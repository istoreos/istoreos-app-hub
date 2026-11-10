# 应用注册目录与包归属统一：源码验收通过

2026-11-10。用户要求统一 `/usr/share/linkease/apps.d`，撤掉旧桌面注册目录，并移除 app-meta 对实际插件清单的重复持有。

## 完成范围

- 聚合仓库 7 个运行包和 2 个 LuCI 入口只安装一个新目录登记。DDNSTO 清单/独立图标迁入现有 luci-app-ddnsto，不增加 companion 包；FastNet 继续由运行包持有完整应用清单，Quickstart 卡片 ABI 注册保留原职责。
- 两个目标仓库的 app-meta-fastnet、app-meta-ddnsto 旧清单均删除，旧 DDNSTO 应用图标软链接也删除；软件中心原 logo.png 保留。
- 升级清理只删除自己旧软链接或 SHA256 匹配的两份已知旧普通清单；保留自定义文件和其他链接，只 rmdir 空目录。卸载钩子仅解除仍指向自己的新登记；原 FastNet 停止行为保留。DDNSTO 保留 LuCI 缓存失效处理。
- 桌面、独立网关、Lua 解析器默认只读新目录。builtin 仍由桌面处理，网关按能力过滤，缺少注册目录时仍返回空数组。Docker 打包同目录、同登记文件名。
- FastNet、DDNSTO、LinkEaseFull 元包仅保留原有 META_DEPENDS 普通依赖，不新增最低版本约束。共享 meta.mk 保持原样，相关插件分别更新后执行注册迁移。
- 统一规范及三处 AGENTS.md 已更新。旧 app-meta 图标文档只保留跳转，不再提供第二套规则。聚合仓库复用已有 CI 门禁；元数据测试手动执行，元数据共享构建与 CI 均保持原样。

唯一规范：../../architecture/linkease-app-registration.md 。

## 同步与已有修改保护

除用户指定的聚合和元数据仓库，还按现有 syncapps.yaml 映射同步了本任务涉及的 nas-packages、nas-packages-luci、openwrt-app-actions 文件，并同步宿主源码的消费者与 Docker 打包。

没有全仓同步或 rsync --delete。25 个显式映射文件经过预演和审计，另同步本轮追加的 DDNSTO 缓存处理、embed README 与 Lua 测试。legacy 中较新的 Kai/KaiPlus 发布号、KaiPlus 二进制哈希以及 DDNSTO/KaiPlus 元数据版本均保留；不同仓库的发布号各在原值上增加一次，不用聚合仓库旧业务版本覆盖构建仓库。详见 sync-result.json。

初始 FastNet 用户改动保存在 bin/registration-unification-20261110/*.before.patch；非本任务 Makefile 的既有差异逐段核对不变。Go 检查产生的无关 go.work.sum 变动已清除。

## 验收证据

- 7 组新规范测试通过，执行 9 个入口的真实运行包 Makefile 安装配方或标准 LuCI root overlay，使用惰性测试产物，不下载/执行应用二进制。覆盖新装、升级、重复清理、自定义文件保护、两份旧普通清单和卸载钩子保护。DDNSTO 除 staticRoot 归属外，原启动清单逐字段保持一致，图标字节与原图标一致。
- 实际 legacy 构建目录复用上述 5 组安装/迁移测试通过。它们是包布局测试，不冒充完整 OpenWrt SDK/IPK 发布构建。
- 相关应用包契约 47 项通过；元数据仓库 1 项登记归属检查通过。取消最低版本策略后，相关依赖展开测试一并移除。
- LuCI 5 组纯 fixture 测试在 192.168.30.7 自带 Lua 下通过，临时源码按实际 luci/... 层级隔离加载，确保不是测试设备已安装旧模块；没有写系统配置、替换运行模块或重启服务，测试临时目录已删除。
- Go desktopplugins/appgateway 单测、race 和 vet 通过。首次缓存路径过长触发 Unix socket 长度限制，改用同一 SSD 的短 TMPDIR 后通过，没有放宽断言。
- 66 应用诊断索引门禁通过，Docker bash -n 通过，工作流 YAML 解析通过，六个仓库 git diff --check 通过。
- 当前生产安装配方中的旧路径只出现在精确升级清理里；宿主生产发现代码和 Docker 中没有旧目录引用。LinkEaseFull 自有静态资源目录不属于退役对象。

基线检查已有 4 个过期断言失败（已发布 3.0.23 仍断言 3.0.22、旧双目录规则、旧业务组合）。相应测试按当前已存在版本和本次新规则对齐；没有改动这些业务包的原二进制哈希或产品组合。

## 当前状态与后续上线顺序

按用户最终确定的发布策略，两个仓库中 FastNet、DDNSTO、LinkEaseFull 元包新增的最低版本声明全部删除；不使用 META_EXTRA_DEPENDS 或包内 override 替代。取消对应的依赖展开测试，保留登记归属测试。

改动范围收敛：共享 meta.mk、.github/workflows/ci.yml 均与 HEAD 逐字节一致；本任务新增的 .github/workflows/application-registration.yml 已删除。不增包、不改 iStore。早先 sync-plan / affected-files 等快照是初次迁移的历史记录，当前范围以本记录和实际 git diff 为准。

APK 测试环境为 root@192.168.3.164，已确认 iStoreOS 25.12.5 / APK 3.0.5，当前未安装 FastNet。此前仅执行只读版本查询和 APK 模拟求解，没有修改已安装包、WORLD 或注册目录。当前取消元包版本约束后，不再需要针对元包依赖兼容 OPKG/APK 的版本后缀。尚未进行新版本 APK 制包、实际安装或整机升级验收。

最终自检：两个仓库的三个元包均无新增 EXTRA_DEPENDS，普通依赖逐项一致，共享构建及 CI 无差异，见 unversioned-meta-dependencies.json。在 .164 对三个已有 LuCI 包执行无版本条件的 APK 模拟安装通过，前后已安装包列表、WORLD 和注册目录摘要一致，见 apk-unversioned-dependencies.json。47 项包契约、7 项安装迁移检查、1 项元数据归属检查通过。

本轮源码迁移及验收随本记录进行本地提交，未推送、发布或部署。运行程序仍使用原已发布版本，宿主严格单目录策略需随后续运行版本重新构建发布。

提交前核对发现：FastNet 确实使用 iframe，但 Quickstart／桌面当前通过同源应用网关加载，LAN 请求也会加 `/apps/fastnet` 前缀，尚未满足浏览器直连的性能要求。本次目录迁移不改动这条传输路径，详见 fastnet-iframe-path-audit.md。

上线时先构建并发布实际所属插件包（含新的 LuCI/builtin 包），用户更新相关运行包、LuCI 包及元包后检查新目录登记，最后切换为只读新目录的宿主运行程序。旧目录清理随实际所属包升级执行，不能把只升级元包描述为全设备完成迁移。用户修改过的旧文件保留待人工确认，不会递归删除共享目录。
