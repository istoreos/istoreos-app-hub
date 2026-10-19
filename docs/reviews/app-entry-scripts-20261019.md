# 18个应用动态入口审查

审查日期2026-10-19，冻结源码6a532f69259fef2227a5b4cab2a03696bc8d3fb1，开始时工作区干净。用户要求检查apps下18份entry.sh是否正确；这是当前文件全量审查，不是某次提交的差异审查。未修改任何应用业务源码、元数据或设备，未执行真实Docker/服务启停/部署。

结论：不能全部判定正确。18份本机`sh -n`均通过，但运行时语义及入口契约有明确缺陷。对入口、实际istorec提供者、元数据生成器、Quickstart解析器和既有产品路由契约进行了交叉读取。[隔离观测JSON](app-entry-scripts-20261019.json)记录18份源码SHA和40次问题观测（同一缺陷多场景，不是40个独立缺陷）；[可复跑探针](check-entry-scripts-20261019.py)仅用临时依赖桩，临时文件已清理，不调用实际设备。未来修复后该诊断记录应重新生成，不把当前问题存在作为正式CI通过条件。

## 优先修复的确定问题

### P1 端口读取到了别的应用，或过滤了错误的容器端口

- `apps/oneapi/luci-app-oneapi/root/usr/libexec/istorec/oneapi.sh:72`：port分支查询`name=^/htreader$`及9060，而安装是oneapi、宿主映射到3000。没有HTReader时读空，entry回退3005丢失自定义端口；有HTReader时会把用户带到HTReader。
- `apps/openwebui/luci-app-openwebui/root/usr/libexec/istorec/openwebui.sh:80`：同样误查HTReader/9060，实际openwebui映射8080；安装默认10086，而entry默认3005，连默认部署都可能打不开。
- `apps/uptimekuma/luci-app-uptimekuma/root/usr/libexec/istorec/uptimekuma.sh:72`：查对容器但grep9060，真实映射3001；自定义43001时仍回退到3001。

探针实际执行上述提供者的port分支，仅Docker被替换为只读桩：OneAPI/OpenWebUI在HTReader存在时输出49060而不是43000/43080；不存在时为空；UptimeKuma始终读不到测试的43001。只改entry.sh默认值不能修好提供者。

### P1 Ubuntu协议不一致

`apps/ubuntu/app-meta-ubuntu/entry.sh:19–20`：href=https，protocol=http。此meta实际依赖`apps/ubuntu2/luci-app-ubuntu2`，不是旧ubuntu实现；ubuntu2提供者映射https_port到3001，LuCI界面也明确使用https。Quickstart优先消费web+protocol，所以被规范化成HTTP，不能用href的HTTPS纠正它。桩实测href为https://router.example:43210/，protocol仍http。

### P1 OpenClaw入口丢失认证信息、写死路径

`apps/openclawmgr/app-meta-openclawmgr/entry.sh:19–24`只把`#token=...`拼进href，web没有；Quickstart优先web，token会丢失。web/href还写死`/openclawmgr/`，而实际控制器`configured_base_path()`从`gateway.controlUi.basePath`读取，缺省返回`/`。本地桩确认href含fixture token但web不含；未读取任何真实token。应让规范入口携带应用必要的路径/临时认证语义，同时避免把token写进布局、收藏或日志；不应让Quickstart忽略所有安全校验而盲信href。

### P1 两项元数据使entry.sh根本不会被调用

`apps/istorepanel/app-meta-istorepanel/Makefile`和`apps/istoredup/app-meta-istoredup/Makefile`没有META_UCI。canonical `openwrt-app-meta/meta.mk:62`只在设置后生成uci；软件中心entrysh要求meta.flags含entrysh且meta.uci存在，Quickstart的launcherMetadata也要求合法uci。因此这些包虽然包含脚本，但动态入口会被跳过；通常表现为只进入静态管理页。应补正确配置身份，而不是只给浏览器硬编码应用例外。istoredup不发布web本身可以是有意设计，其网络地址语义不同，不能强行套成“宿主端口”。

### P2 十份脚本的启停判断缺少空格

涉及oneapi、istorepanel、openwebui、pve、istoredup、ubuntu、jellyfin、uptimekuma、webvirtcloud、dpanel。

形如`[ "$status" = "running"]`和`[ "$status" != "running"]`，末尾`]`没有成为独立参数。`sh -n`发现不了；实际执行报`[: missing ]`。因为后接`||`，start/stop会无条件调用底层动作，而非按状态判断。桩实测每项“已运行时start”和“已停止时stop”均出现错误且仍调用动作。不是声称所有启停完全无法执行。Quickstart当前仅调用status，不会主动触发这组启停问题；软件中心显式启停及其他调用者仍受影响。

### P2 十二份入口吞掉状态读取失败

上述11个Docker应用（含空格已正确的codeserver）及openclawmgr：`local status=\`provider status 2>/dev/null\``不检查命令退出码，后续空字符串被写成running=false/deployed=false，最后json_cleanup成功使整个脚本返回0。提供者不存在、Docker daemon不可达、权限失败都可能伪装成“确定未部署”。12个隔离失败用例均复现。应把读取失败、未创建、已停止、正在运行分开；Docker ps成功返回空列表才可表示未创建。OpenClaw的底层do_status自身对部分ubus错误也会降成stopped，需一起检查。

## 18项覆盖矩阵

| 应用ID | 本轮结论与边界 |
|---|---|
| baidudrive | pidof实际进程名与init一致，正常路径可解释；端口直接读UCI、未校验范围，配置未应用/仅loopback绑定、PID归属和安装不完整场景需补。未做运行设备全场景通过声明。 |
| oneapi | 确定问题：提供者查HTReader端口、启停判断、失败伪装未部署。 |
| istorepanel | 确定问题：META_UCI缺失、启停判断、状态错误吞并；entry还未消费已配置的安全入口路径，原LuCI按钮用/entrance，需按运行1Panel入口核对，不能只返回根路径。 |
| openwebui | 确定问题：提供者查HTReader、回退端口3005与安装默认10086不符、启停判断、状态错误吞并。 |
| pve | 确定问题：启停判断、状态错误吞并。当前entry和LuCI按钮都用HTTP；镜像是否另有HTTP代理需要实际监听/镜像证据，不能仅据PVE常识武断改HTTPS。 |
| istoredup | 确定问题：META_UCI缺失、启停判断、状态错误吞并。弃用应用，未发布web未单独认定缺陷。 |
| agentflow | pidof与init原生二进制相符；端口/路径来自UCI，未校验及缺少实际生效监听核对；host支持loopback但entry仍可发布远端入口。正常路径可解释，边界未完备。 |
| openclawmgr | 确定问题：web丢token、固定路径与运行配置不一致、提供者失败吞并；需用应用专有认证/基础路径规则，不能套纯端口模板。 |
| codeserver | 启停方括号空格已正确；仍吞提供者错误，端口grep未指定内部端口，仅认0.0.0.0，多端口/指定IP/IPv6映射需补。 |
| ubuntu | 确定问题：HTTPS/HTTP矛盾、启停判断、状态错误吞并。实际匹配ubuntu2依赖，不误报缺少提供者。 |
| istoreenhance | 已修复“文件存在就认为运行”；但读期望UCI端口而非运行命令的adminAddr，改配置未重载时可跳错。start/stop无论init返回什么都return0，失败被报成功。未重新宣称全场景通过。 |
| dockermanager | 有external_port_enabled/base_path业务分支，应保留；仍使用UCI预期配置和pidof判断，未完整覆盖实际listen_mode=tcp/unix、绑定地址、代理可用性/端口校验。不可把它简化成普通Docker容器。 |
| jellyfin | 确定问题：启停判断、状态错误吞并；提供者8096筛选本身与安装一致，但仅认0.0.0.0及读取失败默认值需补。 |
| uptimekuma | 确定问题：提供者grep9060而不是3001、启停判断、状态错误吞并。 |
| webvirtcloud | 确定问题：启停判断、状态错误吞并；端口查询未限定内部端口，指定IP/IPv6/多映射需补。 |
| dpanel | 确定问题：启停判断、状态错误吞并；提供者8080筛选与安装一致，但仅认0.0.0.0/失败默认值需补。 |
| kai | pidof进程名与init一致，基本状态分离已存在；缺少端口/实际配置及loopback/能力边界核验。manifest要求/apps/kai/，entry给根路径，是否有运行时重定向本轮未证明，暂列待验证，不武断判404。 |
| fastnet | 当前版本有procd真实运行、运行命令实际端口、有效JSON/端口、loopback和歧义保护；此前该同SHA脚本有真实B/14夹具证据，本轮未重新将其当作新设备验收。未发现新的阻断性缺陷；服务未注册、异常结构等长期兼容仍不能凭静态审查宣称全覆盖。 |

## 修复顺序与共用边界

先修OneAPI/OpenWebUI/UptimeKuma提供者、Ubuntu协议、OpenClaw路径/认证、两项META_UCI；再修启停判断和错误分类。统一最小契约：稳定app、docker类型、deployed/running明确语义、管理href、运行时有效web/protocol/port、失败非零且stdout仅JSON。不得将“没有Web”自动等同未安装。

Docker容器采用实际inspect状态/指定内部端口的PortBindings，区分daemon读取失败与容器不存在；原生服务采用procd运行身份及实际参数/环境。认证片段、基础路径、Unix代理、独立网络地址是业务差异，不能全部替换成同一段“端口+根路径”模板。可抽小型读取/校验helper，不建任意执行框架，不在查询时自动安装/启动/修复。

正式修复时各受影响包release及测试需跟进，考虑opkg/APK的包内安装和调用协议；当前审查没有推送、打包、安装或变更18份业务脚本，也不把本机桩当18应用真实安装验收。
