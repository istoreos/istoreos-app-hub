# Hermes Native / Docker 双后端实施计划

状态：M1～M3 已完成；M4 源码已直接部署到测试机，等待人工验收。IPK/APK 编译由人工后续执行。

## 范围约束

- 同一时间只激活一个后端。
- Native 与 Docker 不自动共享或迁移 Hermes HOME。
- Python 版本由应用 policy 固定，不提供用户版本/ABI 选择。
- 首版 Native 不安装 Chromium、browser 或 computer-use。
- Hermes Agent、WebUI、Python 和 Docker 镜像都必须固定版本及摘要，不跟随 `latest` 或默认分支。
- Native 使用 `mise-runtime` 的固定 Python；应用自己持有 venv、release、数据和服务生命周期。

## M1：固定 Python 的原生闭环

状态：已完成（2026-11-26）。

任务：补充 Python 3.14 catalog；固定上游版本；实现 runtime binding、私有 venv、专用 UID 执行、候选 release 和 CLI/WebUI 健康探测；完成本地及 x86_64 设备验证。

通过条件：verified Python receipt；运行版本与 policy 一致；应用依赖仅在私有 venv；CLI 和 `/health` 以 `hermes` UID 运行；不使用 Docker；失败候选不切换 `current`。

设备证据：在 `192.168.30.7` 从空应用缓存下载并校验 Agent、WebUI、uv、PyYAML，安装 Python 3.14.9 musl 私有 venv；中途设备重启后旧 release 仍为 `current`，修复并实测 `.part` 从字节 4104046 续传；最终 release `20261126135901-28610` 的 receipt、Hermes UID 32776、CLI、五项依赖导入、WebUI HTTP 200 及进程/端口释放全部通过，未创建 Docker Hermes 容器。

## M2：可维护的 Native 后端

状态：已完成（2026-11-26）。

任务：补齐 install/upgrade/start/stop/restart/status/health/logs/cancel/recover/remove，procd 管理 Gateway/WebUI，升级事务、回退、重启、runtime 仓库切换和资源约束。

通过条件：完整生命周期、失败回退、中断恢复、重启恢复、专用 UID、端口/空间/权限保护在测试机通过。

设备证据：Gateway/WebUI 两个 procd 实例均以 UID 32776 运行；start/stop/restart/status/health/logs 幂等测试通过；运行中 upgrade 成功且提交后回收旧 release；激活后 cancel 返回 143 并恢复旧 release/服务；preparing journal 可 recover；设备重启后自动恢复 healthy；remove 后用户数据与校验缓存摘要保持不变并可重新安装；未受管目录的 purge 被拒绝。

## M3：Docker 修复与双后端页面

状态：已完成（2026-11-26）。

任务：固定 Docker 构建和镜像；定义两个 Adapter 的共同 Interface；增加 Native/Docker 页签、单一激活选择、安全切换、独立数据目录和旧 Docker 配置迁移；移除通用 LuCI 包的 Docker 硬依赖。

通过条件：两个 Adapter 通过同一契约测试；Native 不安装 Docker；双向切换和失败恢复通过；老用户配置与容器不丢失。

设备证据：Docker 使用固定多架构索引 `sha256:6958262de9d71633b81866e2b17f35c8662e2aaa9a91b0444d29d795b3b08763`，在 Native 保持在线时完成冷拉取；统一入口完成 Native → Docker → Native → Docker → Native 双向切换，每次仅一个后端运行；两套数据目录的保留标记均未变化；注入非法 Native 端口后切换失败并自动恢复原 Docker 后端及健康状态。最终测试机恢复 Native healthy、Docker stopped。14 项本地契约测试、Shell/Lua 语法与 LuCI 双页签文件加载通过。

## M4：正式包与设备验收

状态：代码已提交并直接部署，等待人工验收（2026-11-26）。

任务：补齐同步映射、依赖版本、元数据与 release；提交源码；将开发代码直接部署到 `192.168.30.7`，完成运行状态、双后端页面、切换、重启、异常恢复和数据保留检查。IPK/APK 编译与正式包安装不属于本轮自动验收，由人工后续执行。

通过条件：测试机运行文件与提交一致；Native healthy、Docker stopped；双后端页面可供人工检查；本地契约测试和代码审查完成；源码、聚合仓库和 legacy 工作树内容一致。完全空白机器若没有 QuickStart 的持久目录配置，必须先在页面选择一个 `/mnt` 下的路径，禁止静默回退到系统闪存。

部署证据：聚合仓库提交 `1b8abab` 后，将控制脚本、procd init、LuCI 页面、固定 runtime policy 和 mise catalog 直接复制到测试机；未覆盖 `/etc/config/hermes` 或用户数据。部署后统一入口 restart 成功，`backend=native`、Native `running/healthy`、Docker `stopped`、端口 `18787`；设备 policy SHA256 为 `9c9dd22dce8cfa3a5e994022517efeed836a20e226eece4ca5521935d1792d2e`，catalog SHA256 为 `b1e4fea2d29b2d5fc9def3464daf128f5fbc792419937fe6f2a73e31d2e74c2`，均与源码一致。
