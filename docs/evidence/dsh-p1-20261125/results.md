# DSH P1 双架构兼容性 Spike 结果

日期：2026-11-25

结论：**P1 Spike 已完成，原生 OpenWrt 方案为 conditional go；P2 正式插件编码门尚未完全放行。**
DSH 本体、完整依赖闭包、低权限 Web、Workspace 持久化和共享入口在 x86_64 与
aarch64 上均能运行；但 x86_64 缺少可用的进程沙箱，当前共享入口也没有收窄 DSH
Session Cookie 的 Path。这两项必须先形成通用修复并复验，不能在插件里静默降级。

## 固定候选

- DSH：`@deepseek-ai/dsh@0.2.2-rc.5`；许可证 MIT；Engine `>=24.9.0`；
- tarball：`https://registry.npmjs.org/@deepseek-ai/dsh/-/dsh-0.2.2-rc.5.tgz`；
- SHA512 integrity：
  `sha512-cNbp12tLYLUTXaVli7zwwMjzmmEVCD1PRldg4oKtXM4+lFYckcaliMS2PU/FoThB4iAN/fKOSID0nrtRZU4Gjw==`；
- tarball SHA1：`b540ae0577939a34c43fdc6bf44f034b2de040e5`；
- mise：Node.js 24.22.1、npm 11.19.1、私有 glibc 2.39；
- 锁文件：lockfileVersion 3，共 744 个解析记录；实际生产安装 671/673 个包。

锁文件与最小复现清单位于 [`fixture/`](fixture/)。没有解析 `latest`，没有编译 IPK，
也没有从源码构建 DSH monorepo。

## 三轮执行

1. 第 1 轮：aarch64 在设备上 `npm ci` 成功，用时 156 秒；x86_64 经 `ks-cli`
   加速链路 410 秒无进展，终止后只保留诊断日志。
2. 第 2 轮：x86_64 强制 `ISTORE_RUNTIME_ACCELERATION=origin`，604 秒仍停在早期下载/
   缓存阶段；终止时 `node_modules` 仅 3.1 MiB，npm 缓存约 159 MiB。锁文件、空间和
   ABI 均未报错，判断为该设备下载链路问题，而非 DSH 包不兼容。
3. 第 3 轮：在本机 SSD 缓存环境按同一锁文件构建 x86_64 闭包，用时 23 秒；将闭包
   作为发布制品流式部署到测试机后，完成双架构原生、Web、RPC、认证代理、权限、
   持久化和资源回归。这说明正式插件应下载已锁定的架构制品，不应在路由器现场执行
   全量 npm 安装。

第 1、2 轮只删除了 x86_64 可丢弃测试目录中的不完整 `node_modules`；未删除 mise
SDK、既有应用数据或其他测试目录。

## 双架构结果矩阵

| 项目 | x86_64 (`192.168.30.7`) | aarch64 (`192.168.30.93`) |
| --- | --- | --- |
| 非 root 身份 | UID/GID 32760 | UID/GID 32760 |
| Node/DSH | 24.22.1 / 0.2.2-rc.5 | 24.22.1 / 0.2.2-rc.5 |
| PTY、SQLite、Koffi、Sharp、ripgrep | 通过 | 通过 |
| system flock addon、Shell、Git | 通过 | 通过 |
| 工作区写入 / root 私有目录读取 | 通过 / EACCES | 通过 / EACCES |
| `/etc/shadow` 读取 / `/etc` 写入 | EACCES / EACCES | EACCES / EACCES |
| Web 监听 | 仅 `127.0.0.1:13080` | 仅 `127.0.0.1:13080` |
| DSH Token → Cookie | 303 → 200 | 303 → 200 |
| 无 DSH Cookie访问根 | 401 | 401 |
| 静态资源 / WebSocket | 200 / 101 | 200 / 101 |
| Workspace RPC | 创建成功，重启后 ID 不变 | 创建成功，重启后 ID 不变 |
| DSH Cookie 重启后 | 仍为 200 | 仍为 200 |
| 工作目录 | 持久 Workspace | 持久 Workspace |
| `/apps/dsh/` 外层未登录 | 302 到 LuCI 登录 | 302 到 LuCI 登录 |
| 前缀 Token / HTML / 资源 / WS | 303 / 200 / 200 / 101 | 303 / 200 / 200 / 101 |
| `/apps/dsh` 尾斜杠 | 307 | 307 |
| Cookie Path | **仍为 `/`，失败** | **仍为 `/`，失败** |
| Landlock | unusable | unusable |
| bubblewrap | **缺失，整体沙箱不可用** | full probe 通过 |

DSH 的 Linux 沙箱选择顺序是 bubblewrap → Landlock，并在两者都不可用时 fail-closed。
因此 x86_64 虽能启动 Web 与执行不经沙箱的原生探针，但受限 Shell/终端不能作为已通过
功能发布；aarch64 可选择 bubblewrap。x86_64 软件源当时也没有列出 bubblewrap 包。

## 共享入口

使用可丢弃清单验证了 `auth.mode=default`、`upstreamBasePath=/`、
`pathMode=strip-public-base` 与 `proxyMode=app-base`。当前 `linkease-app-entry 3.0.23`
能完成外层 LuCI 认证、前缀剥离、Host 信任、尾斜杠、静态资源与 WebSocket Upgrade；
若缺少 `proxyMode=app-base`，入口会 307 到后端外部端口，因此正式清单必须显式设置。

唯一硬缺口是响应中的 `Set-Cookie` 仍带 `Path=/`，共享入口没有改写为
`Path=/apps/dsh/`。这不会阻止页面工作，但扩大了 DSH Cookie 在同一设备域名下的发送
范围，不符合既定认证契约。修复应落在共享网关的通用 Cookie Path 改写能力，不应在
DSH LuCI 页面制作专用代理。

## 资源基线

| 指标 | x86_64 | aarch64 |
| --- | ---: | ---: |
| `node_modules` | 1,268,252 KiB | 1,264,548 KiB |
| 普通文件 / 符号链接 | 94,524 / 13 | 94,500 / 13 |
| 启动到监听 | 9 秒 | 28 秒 |
| Web RSS（空闲） | 375,172 KiB | 473,928 KiB |
| Web RSS（10 次页面请求后） | 375,644 KiB | 473,956 KiB |
| Web 峰值 RSS | 399,468 KiB | 473,956 KiB |
| 线程数 | 11 | 11 |

x86_64 测试机只有约 2 GiB RAM、无 swap；采样时系统可用内存约 445 MiB。aarch64
约 4 GiB RAM、无 swap，可用约 2.2 GiB。首版必须把 **至少 2 GiB RAM、约 1.5 GiB
安装空间** 写成前置检查，并在 2 GiB 设备上给出明显资源风险提示；正式制品还应剔除
不适用平台的可选包并重新测量，不能直接接受当前 1.27 GiB 闭包。

## 未自动执行的验收

- 没有配置真实模型 Provider、保存真实 API Key 或产生模型费用；
- 没有执行一次真实模型驱动的只读任务、审批后写入任务和 Session 恢复；
- 没有进行整机重启，只完成服务重启后的 Profile、Workspace、存储和 Cookie 验证；
- 没有覆盖文件下载响应、升级切换与回滚。

这些不是兼容性假通过项：它们作为有凭据的人工验收保留，P2/P3 不能据此宣称产品
闭环已完成。

## P2 放行条件

1. 为 x86_64 提供并固定可功能探测通过的 bubblewrap，或给出等价、由 DSH 实际使用
   且 fail-closed 的进程沙箱；两种 runner 都不可用时服务状态必须明确阻塞受限任务。
2. 在 `linkease-app-entry` 增加通用 Cookie Path 改写，并回归现有应用；DSH 清单必须
   显式使用 `proxyMode=app-base`。
3. 决定架构制品的构建、SHA256/SRI、许可证/SBOM和裁剪策略；设备只做校验、解包、
   原生探针和原子切换，不做 1.3 GiB 全量 npm 现场安装。
4. 用用户提供的测试 Provider 完成一次有费用提示的 Session/审批/文件任务，以及整机
   重启、下载和回滚验收。

在 1–3 完成前，结论保持 conditional go，不开始完整 `apps/dsh/` 三包实现；若 x86_64
无法获得可靠沙箱，则原生方案为 no-go，改评估容器或远端 DSH 后端。
