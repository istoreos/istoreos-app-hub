# DSH P1 双架构兼容性 Spike 执行计划

日期：2026-11-25

状态：执行中。P0 已复核通过；本目录只记录 P1 实际证据，不代表正式插件或发布包。

## 目标

以固定 `@deepseek-ai/dsh@0.2.2-rc.5` 和 mise-runtime 已验证的
Node.js 24.22.1 / npm 11.19.1 / 私有 glibc 2.39 为候选，在 iStoreOS
x86_64 与 aarch64 上证明或否定原生 Web 工作台方案。结论必须覆盖完整生产依赖、
低权限执行、原生能力、Web/认证代理、持久化、权限与资源，不以版本命令代替。

## 测试对象

| 架构 | 设备 | 可丢弃数据根 | 既有固定 Node |
| --- | --- | --- | --- |
| x86_64 | `192.168.30.7` | `/mnt/mise-runtime/Configs/DSH-P1-20261125` | 24.22.1 / glibc / npm 11.19.1 |
| aarch64 | `192.168.30.93` | `/mnt/nvme0n1-1/Configs/DSH-P1-20261125` | 24.22.1 / glibc / npm 11.19.1 |

不修改系统 mise 默认值，不编译或安装 IPK，不使用 `/root` 保存 DSH 数据。测试目录
可在证据收集结束后删除；既有 mise SDK、应用数据和其他测试目录不得清理。

## 任务树与通过标准

### T1 版本、完整性与可复现安装

- 锁定 npm 版本、tarball、SHA512 integrity、Engine、许可证与顶层依赖；
- 生成并保存 package-lock，使用生产依赖安装，不解析 `latest`；
- 两架构记录下载时间、安装时间、文件数、磁盘占用和平台原生包清单；
- 禁止从源码构建整个 DSH monorepo；发生原生现场编译必须记录并判定发布风险。

### T2 低权限运行与原生能力

- 创建临时非 root `dshp1` 身份和私有 HOME/DSH_HOME/Workspace；
- 通过 mise 固定 wrap 启动 Node/npm/dsh，不继承系统 Node 或 `/root`；
- 实际加载或执行 DSH 闭包中的 system addon、PTY、SQLite、Koffi、Sharp、ripgrep、
  Shell/Git，以及启动路径实际需要的其他平台组件；
- 失败必须明确到包、ELF/ABI、缺少系统能力或资源，不用 root 或跳过安全功能掩盖。

### T3 Web、认证和路径代理

- 以非 root 身份启动 `dsh web --no-open`，仅监听 `127.0.0.1`；
- 验证启动令牌交换、签名 Cookie、静态页面、RPC 和 WebSocket；
- 用可丢弃的前缀代理验证 `/apps/dsh/` 前缀剥离、尾斜杠、Host/Origin、Cookie Path、
  WebSocket Upgrade 和下载；不得把 3080 暴露到 LAN；
- 检查现有 linkease-app-entry 能力缺口，不能把临时代理结果写成正式网关已通过。

### T4 持久化、权限与资源

- 无模型费用地完成 Workspace 注册、会话/配置持久化所需的本地操作；
- 服务重启后 HOME、Profile、Cookie signing state 与工作区仍存在；
- 工作区可写，其他测试身份的 `0700` 私有目录不可读；确认 DSH 沙箱不能替代 Unix 权限；
- 记录空闲/启动/页面请求期间 RSS、CPU、启动耗时、安装体积和临时峰值；
- 真实付费模型任务不在自动 Spike 中执行，单独列为人工验收项。

### T5 三轮判定

- 第 1 轮：完成安装与最小启动，收集所有硬失败；
- 第 2 轮：只修复可归属于 iStoreOS 适配层的问题，复验原生、代理和权限；
- 第 3 轮：完整回归并给出 go/no-go；不降低安全、架构或双平台标准；
- 清理临时服务、进程、账号和运行目录前先保存不含秘密的证据；报告保留物与恢复方式。

## 判定规则

- `go`：两架构所有 T1–T4 硬门通过，可进入 P2 原生 OpenWrt 插件开发；
- `conditional go`：只有明确可在通用入口或适配包中修复的问题，且不改变安全边界；
- `no-go`：任一架构的完整闭包、低权限 Web、认证代理或权限隔离不能可靠成立；转为
  Linux 容器/远端 DSH 后端方案，不以 root、公开端口或禁用认证继续。
