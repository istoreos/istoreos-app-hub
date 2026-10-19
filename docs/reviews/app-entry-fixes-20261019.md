# 应用入口修复任务与验收

基线：`1fa7ed5`。原始问题及失败证据保留在 [审查记录](app-entry-scripts-20261019.md) 和对应 JSON。本轮用户明确排除 `istorepanel`、`istoredup`，不修改这两个目录。

## 目标与任务树

1. Docker 九项：修复错误容器/内部端口选择；以实际发布端口为准；查询失败不能伪装未部署；启动停止幂等并传播失败；Ubuntu 使用 HTTPS。
2. 原生服务：百度网盘、AgentFlow、KAI、KSpeeder、DockerManager、OpenClawMgr 从 procd 的实际 Web 实例读取入口；不把 SDK/会话进程当成 Web 服务，不用未生效 UCI 端口冒充运行参数。FastNet 保留现有实现并回归。
3. OpenClawMgr：读取实际配置的 basePath，主入口保留 URL 编码后的认证片段；管理地址仍指向 LuCI。只读状态不启动、安装或写配置。
4. 包更新：只提升发生变化的包 release；不修改镜像、安装流程、默认路由和公共构建仓库。
5. 验证与收口：先留下失败回归，再测试候选，最多三轮；保存每轮报告；复核忽略目录未变；本地提交，不推送。

## 可测试验收与边界

- 实际执行 entry/provider 脚本，覆盖运行、停止、未部署、查询失败、非默认端口、IPv6、回环绑定、无发布端口、歧义绑定、动作幂等与动作失败。
- 原生服务用真实 procd JSON 结构，检查运行参数与 UCI 不一致、多实例、错误命令及依赖实例独自运行。
- 目标 `root@192.168.30.244` 仅在专属临时目录使用隔离依赖，执行目标 BusyBox ash、jsonfilter、jshn；不操作真实业务服务。脚本临时文件必须清理。
- 不把隔离回归当成每个真实应用镜像、浏览器、安装包和 APK 固件已验收；需要真实实例才能确认的行为单列。
- 原始诊断不重跑覆盖旧 JSON。新证据放在 `docs/evidence/app-entry-fixes-20261019/`，报告不记录认证 token 或实际服务环境。

## 实施状态

已完成源码修复和隔离验证。自包含 entry 脚本随各 meta 包分发，不引入新的运行时公共包；有限的重复入口逻辑由同一回归矩阵覆盖。未修改镜像安装流程。OpenClaw 的显式启停继续走原 provider，保留启用设置、token 准备、安全端口处理及停止后的禁用行为；其停止状态仍区分安装器存在与运行时已下载。

| 范围 | 最终行为 |
|---|---|
| oneapi、openwebui、uptimekuma | 精确读取自身容器的 3000、8080、3001/tcp 发布端口，消除 HTReader/9060 误选。 |
| pve、codeserver、ubuntu、jellyfin、webvirtcloud、dpanel | 精确读取对应内部 TCP 端口；支持 IPv4/IPv6，同端口双栈去重；仅回环、未发布时不捏造 Web；多端口歧义或查询失败返回非零。 |
| 全部九个 Docker 入口 | 单次读取状态，合法空列表与读取失败分开；启动已运行实例、停止已停止实例不重复操作；显式动作失败向上传递；running/deployed 均明确。 |
| ubuntu | web 与 protocol 统一使用 HTTPS，仍对接 ubuntu2。 |
| baidudrive、kai | 只认实际 Web 实例，辅助 SDK/会话实例不计为 Web 运行；端口、绑定取自运行命令。KAI 使用 manifest 声明的 `/apps/kai/`。 |
| agentflow、istoreenhance | 使用运行实例的 env/命令端口；配置未应用不会造成旧进程跳新端口；KSpeeder 不再把启停失败报成功。 |
| dockermanager | 原生服务标记 docker=false；按运行实例区分 TCP/Unix。TCP 使用生效地址、端口和路径；Unix 委托已有共享 open 路由判断代理和认证能力，管理 href 保留原 LuCI。 |
| openclawmgr | 使用 gateway 实例实际端口/token 与实际配置路径；basePath 缺省 `/`，校验类型和路径；web 保留百分号编码的认证片段；读取错误非零；未知或仅回环绑定保留管理入口。 |
| fastnet | 本轮未发现阻断问题，源码与包版本均未改，纳入当前设备隔离回归。 |
| istorepanel、istoredup | 用户指定忽略，两个目录 28 个跟踪文件与基线逐字节相同，原问题未宣称修复。 |

发生变化的 15 个 meta 包提升 release；9 个 LuCI provider 包将已有日期修订更新为 `r20261019`，保持空 PKG_RELEASE 的 LuCI 构建约定，避免 release 被构建规则清掉而不能升级。syncapps 已有目录映射，无需新增映射。

## 三轮检查与证据

证据目录：[app-entry-fixes-20261019](../evidence/app-entry-fixes-20261019/)。原审查 MD/JSON 未覆盖。

| 检查 | 结果与处理 |
|---|---|
| Docker 修改前 | `baseline-docker.json`：154 场景，101 失败。 |
| 原生服务修改前（已含 Docker 候选） | `baseline-native.json`：224 场景，40 失败。 |
| 候选 1 | `candidate-1-docker.json`：154 场景，4 失败，均是测试未计入 PVE/WebVirtCloud 原有 vmease 启动；修正断言，保留依赖启动业务。自检另纠正 Go 模板换行转义，并新增真实模板引擎检查。 |
| 候选 2 | `candidate-2.json`：224 场景，5 失败。定位 jshn 实例键的标点转下划线和 BusyBox hexdump 编码格式不兼容，随后修复。 |
| 候选 3 | `candidate-3.json`：235/235 通过。最终业务对照发现 OpenClaw 动作应保留 provider，新增回归先复现 4 处失败（`candidate-3-claw-action-review.json`），修正后专项 18/18 通过（`candidate-3-claw-final.json`）。其余脚本未再修改。 |

最终源码对应的覆盖为其余 15 项 219 场景通过，加 OpenClaw 最终 18 场景通过，共 237 个去重场景；并非声称同一命令重新执行了 237 项。报告分别记录运行源码 SHA。所有目标机临时目录已清理。

补充检查：

- 9 个实际 Docker inspect Go 模板由标准模板引擎执行，已发布/未发布两种输入共 18 项通过，防止隔离 Docker 桩掩盖转义错误。Go 使用 SSD wrapper，临时输出和 GOCACHE 位于 `/var/cache/build-cache`，未产生仓库二进制。
- 相关既有包契约：DockerManager 3、KSpeeder 10、百度网盘 4、KAI 4、FastNet 3，共 24 项通过。只更新随此次变化的包 release 和被明确替代的 Unix open 断言，管理入口保护仍保留。
- 24 份修改过的 shell 源码语法通过；`git diff --check` 通过。
- 扩展读取 LinkEase 契约时，23 项中 3 项因旧 `3.0.22` 和旧 FastNet legacy manifest 断言失败。相关被测文件与 HEAD 相同，属本轮前已有失配；未修改其代码或删断言，也不宣称全仓测试通过。

可复跑入口（输出文件必须不存在）：

```sh
rtk proxy python3 docs/reviews/test-entry-fixes.py --target root@192.168.30.244 --output /新的证据目录/entry.json
rtk proxy /var/cache/build-cache/run.sh -- go run docs/reviews/check-docker-entry-templates.go
```

## 验证边界与后续

目标重新读取为 iStoreOS 24.10.1、revision 2025052311、x86/64。执行使用该设备的 ash/jshn/jsonfilter，依赖和业务数据均为隔离夹具；没有安装/停止/启动实际插件，没有替换 `/usr` 或 `/etc`，没有推送、发布或同步 canonical feed。

这些结果证明入口脚本契约与已列异常分支，不能证明 16 个真实应用全部可打开，也不代表 IPK/APK 包安装验收。实际镜像、认证回跳、监听就绪仍需在应用已安装的环境验证。PVE 保留仓库既有 HTTP 约定，不能仅按通用 PVE 知识改为 HTTPS；KAI 按 manifest 路径对齐，尚无真实实例的浏览器证据。Jellyfin host 网络保留默认 HTTP 8096，应用内另改监听端口的情况尚不自动探测。OpenClaw auto/custom/tailnet 绑定不推断为 LAN 直连，仍可进入管理页。这些限制没有伪装成已完成的真实业务验收。
