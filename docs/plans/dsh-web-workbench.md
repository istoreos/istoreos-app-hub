# DSH Web 工作台插件实施目标与任务树

状态：P1 原生 compatibility spike complete；P2 已切换为容器方案，并在 2026-11-26
把 DSH 从 `/apps/dsh/` 子路径反代改为“独立根路径端口 + DSH 强制管理密钥认证”。
`/apps/dsh/` 仅保留跳转入口，不再改写上游 HTML。x86_64 源码部署、同版本重建、失败
回滚、taskd 取消、整机重启续用和真实 Provider 任务已通过，真实容器版本升级和
aarch64 仍待验收。容器证据见
[`../evidence/dsh-p2-20261126/results.md`](../evidence/dsh-p2-20261126/results.md)，原生实机证据见
[`../evidence/dsh-p1-20261125/results.md`](../evidence/dsh-p1-20261125/results.md)。产品事实与来源见
[`../product/dsh/research.md`](../product/dsh/research.md)。

## 目标

为 iStoreOS 提供独立的 DSH Web 工作台：设备侧负责固定版本安装、低权限服务、
持久化、独立端口、强制认证、升级回滚和诊断；模型、工作区、会话、工具审批和 DSH
插件继续由上游 Web UI 管理。

首版完成的判断标准不是“能执行 `dsh --version`”，而是用户从软件管理页一键跳转
到 DSH 独立端口，通过 DSH 管理密钥登录，选择受控工作区，完成一次只读任务和一次
需确认的写入任务；服务和设备重启后，会话、凭据与工作区仍然存在。

## 产品关系与边界

| 组件 | 负责 | 不负责 |
| --- | --- | --- |
| Codex / Claude Code / OpenCode / Kimi 插件 | 单个 CLI、浏览器终端、账号与 AgentFlow Provider | DSH 的会话、插件或 Web UI |
| AgentFlow | 项目、任务和多 CLI Provider 编排 | 安装或承载 DSH |
| DSH | Web 工作区、模型、会话、工具、审批、插件与自动化 | AgentFlow 项目控制面 |
| Docker / DSH 镜像预设 | 固定 Linux 用户态、Node/DSH 依赖闭包与容器内工具 | LuCI 产品交互、宿主数据策略或外部端口 |
| mise-runtime | 其他原生 CLI 的固定 Node/npm 与私有运行库 | DSH 容器运行依赖；首版 DSH 不依赖 mise |
| `luci-app-dsh` | 镜像预设、安装状态、服务、存储、安全入口、诊断 | 复制 Models、Workspace、Session、Plugin 页面 |

DSH 不登记到 `/usr/share/coding-agents.d`。将来若 AgentFlow 需要调用 DSH，应另行
设计 ACP/SDK 适配器；不得把 Web 工作台伪装成普通 CLI Provider。

## 用户交互

### 软件管理页

LuCI 只保留一个页面和一个主要操作，按状态改变动作：

| 状态 | 主操作 | 页面反馈 |
| --- | --- | --- |
| 未配置存储 | 选择数据目录 | 说明至少空间、独立用户和默认工作区位置 |
| 未安装 | 安装 DSH | 展示固定 DSH/Node 版本、预计下载与磁盘占用 |
| 安装中 | 查看进度 / 取消 | 展示当前阶段，不用假百分比 |
| 已安装、已停止 | 启动 | 保留数据，不把“已安装”写成“可使用” |
| 正常运行 | 打开 DSH 工作台 | `/apps/dsh/` 跳转到当前主机的 DSH 独立端口 |
| 运行异常 | 诊断 / 重试 | 给出精确失败项和最近日志，不自动关闭安全限制 |
| 有已验证更新 | 复核升级 | 显示版本、数据兼容性和回滚点 |

页面信息架构只有三块：

1. 服务状态：DSH/Node 版本、运行状态、Web 端口、最近错误；
2. 存储与安全：管理密钥状态、数据目录、默认工作区根、低权限身份、备份提示；
3. 主行动：安装、启动、打开、升级或诊断。

不增加“命令行”“模型”“会话”“插件”页签。API Key 只在 DSH 原生设置页输入，
LuCI 不读取、不回显，也不复制保存。

### DSH 原生工作台

首次进入后的引导顺序保持上游语义：配置模型 → 选择工作区 → 选择模型/权限 →
创建会话。页面应完整打开，不嵌入 LuCI iframe；文件预览、下载、剪贴板、焦点、
Cookie、WebSocket 和第三方 Client 插件都留在 DSH 自己的页面上下文中。

## 包和目录设计

首版使用仓库现有的三包结构，不额外创建只有转发作用的 companion 包：

```text
apps/dsh/
  dsh/             # 服务、安装器、固定策略、清单、注册和诊断
  luci-app-dsh/    # 管理页与受保护操作 API
  app-meta-dsh/    # 软件中心元数据、图标和依赖
```

职责约定：

- `dsh` 依赖 Docker、CA 与 `linkease-app-entry`，拥有 `/etc/config/dsh`、固定镜像
  预设、容器事务脚本、应用清单和注册链接；
- `luci-app-dsh` 直接依赖 `dsh`、`luci-lib-linkeaseauth` 和
  `linkease-app-entry`，只暴露管理页与严格参数化的操作；
- `app-meta-dsh` 依赖前两者，只拥有软件中心信息，不重复注册应用；
- 运行包发布代码发生变化时，同一候选中的 `app-meta-dsh` 发布号必须增加。

首版容器持久目录模型：

```text
<data_path>/            # -> /home/node/.dsh：凭据、Profile、插件和会话
<workspace_path>/       # -> /home/node：Agent 唯一宿主工作区
```

镜像以 UID/GID 1000 非 root 用户运行。插件只为新建的专用目录设置属主和权限；已有
目录必须已经由 UID 1000 持有，安装器不得递归 `chown`、`chmod` 或接管用户仓库。
卸载默认保留两个目录，清理数据必须是单独、明确、可复核的破坏性操作。

## 运行与安装契约

- UCI 保存受控 `image_profile`，不接受任意镜像名。`standard` 固定为
  `ghcr.io/omdsh-dev/dsh-container:0.2.1-rc.2` 及已核验的多架构 manifest digest；
  禁止解析 `latest`。
- `advanced` 预设保留给 `runzhliu/deepseek-harness:0.2.3-alpha.2-r1`，在完成
  Chromium/noVNC 端口、共享内存、资源门槛和安全验收前不得出现在可选项中。
- 安装事务为：配置与路径预检查 → 拉取固定 digest → 停止并重命名旧容器 → 创建
  候选容器 → 镜像健康检查 → 提交；创建或健康失败时删除候选并恢复旧容器。
- standard 容器必须非 root、只读根文件系统、`cap-drop ALL`、
  `no-new-privileges`，不得挂载 Docker socket；仅挂载数据与工作区。
- 容器内 DSH 可使用 `danger-full-access`，但它的“全访问”边界只到容器及两个明确
  挂载；这是替代不可靠 OpenWrt 原生进程沙箱的宿主隔离边界。
- Docker 按其他 iStoreOS Docker 插件的惯例发布 `0.0.0.0:<port>`；插件不替用户
  决定 LAN/WAN 策略，接口可达性由用户现有防火墙和端口规则控制。
- `DSH_CONTAINER_KEY` 必须启用。初始密钥自动生成到 `/etc/dsh/admin.key`，root/0600；
  LuCI 只允许覆盖，不读取或回显。容器启动、重启、升级都从该文件注入密钥。
- DSH 原生应用始终位于独立 origin 的 `/`；禁止修改 `index.html`、替换
  `/auth-bootstrap.js`、添加兼容 bind mount 或把根路径资源转写到 `/apps/dsh/`。

## `/apps/dsh/` 与认证契约

应用清单使用 `desktop.mode=iframe` 的现有浏览器直连解析能力，但入口行为是 307 跳转，
不是 iframe 嵌入。`desktop.target` 使用 request-host、UCI 端口和根路径 `/`；
`auth.mode=passthrough` 避免 iStoreOS 与 DSH 双重登录。`/apps/dsh/` 之外的子路径不代理，
例如 `/apps/dsh/auth-bootstrap.js` 应返回 404，而浏览器从独立端口请求
`/auth-bootstrap.js`。

独立端口的未认证顶层导航由 DSH relay 303 到 `/_dsh-container/auth/login`；静态资源
返回 401。密钥登录成功后 relay 发放 HttpOnly 会话 Cookie，并继续完成 DSH 内部
launch token → owner Cookie 交换。测试和诊断只能报告“密钥已配置”，不得输出密钥、
登录 Cookie、启动令牌或带秘密的容器日志。

## 任务树

### P0：产品与证据基线（已完成）

- [x] 区分官方 DSH、独立社区站点和社区插件证据；
- [x] 归纳用户旅程、插件开发模型、安全说明和代理契约；
- [x] 确定 DSH 为独立 Web 工作台，不是 CLI Provider；
- [x] 形成产品边界、交互结构和实施前门槛。

### P1：原生双架构兼容性 Spike（历史决策门）

- [x] 锁定一个 DSH/npm tarball、Node/npm 实例、完整 integrity 与许可证清单；
- [x] 在可丢弃目录安装生产依赖，记录实际安装路径、安装后大小、内存和启动时间；
- [x] x86_64 与 aarch64 分别探测 CLI、PTY、SQLite、Koffi、平台加载器、Shell、
  Git、文件工具及 DSH 实际装载的其他原生依赖；
- [x] 以非 root 用户、持久 HOME 启动 Web，完成 Workspace RPC 与服务重启持久化；
- [ ] 使用有费用提示的测试 Provider 完成 Web Session、交互审批和整机重启续用；
- [x] 复用 KAI Plus 的 OpenAI-compatible Provider，以 DSH headless 完成真实只读和
  受控写入任务，并用文件数量、SHA-256 与逐字节比较验证结果；
- [x] 验证 `/apps/dsh/` 的静态资源、API、WebSocket 和令牌交换；
- [ ] 把 DSH Cookie Path 从 `/` 收窄到 `/apps/dsh/`，并验证实际下载响应；
- [x] 验证 `dsh` 用户无法读取 `/etc/shadow`、root 私有目录或写入 `/etc`；
- [ ] 为 x86_64 提供可用的 fail-closed 进程沙箱；aarch64 bubblewrap 已通过；
- [x] 记录不兼容项并给出 conditional go，明确 P2 放行条件和 no-go 回退线。

这份原生 Spike 仍为 conditional go，不作为首版发布路径。x86_64 进程沙箱、共享入口
Cookie Path、真实模型任务与整机/下载/回滚验收没有被伪装成通过；用户已选择这里预设的
容器回退线，由独立 Linux 容器承载 DSH，iStoreOS 只做生命周期、持久化和认证代理。
因此未完成的原生项不再阻塞容器 P2，但容器自己的隔离、代理与双架构验收仍必须通过。

### P2：插件骨架与安装事务

- [x] 创建 `dsh`、`luci-app-dsh`、`app-meta-dsh` 及 README；
- [x] 实现 UCI 镜像预设、持久目录、容器状态和健康状态；
- [x] 在 x86_64 完成固定版本安装、同版本重建、候选创建失败回滚和两类持久目录保留；
- [x] 完成 taskd 同 ID 并发拒绝、任务取消和 x86_64 整机重启续用验收；
- [ ] 完成真实容器版本升级和 aarch64 设备验收；
- [x] 注册 `/apps/dsh/` 与旧桌面兼容链接，遵循应用注册唯一归属；
- [x] 复用 LuCI CBI/taskd 实现参数化操作、CSRF、并发锁、任务状态和无秘密诊断；
- [x] 为包归属、路径、权限、失败回滚和 manifest 增加契约测试。

### P2 后续实施目标与三轮任务树（2026-11-26）

目标：在不编译 IPK、不默认调用付费模型的前提下，完成现有
x86_64 测试机可执行的 P2 闭环，并把不能在当前环境完成的门槛转换为明确、可复核的
阻塞项。最多执行三轮；每轮只修复上一轮发现的问题，不降低验收标准。

#### 第 1 轮：功能与生命周期

- [x] 增加可重复运行、不会输出认证 Cookie 或 DSH 秘密的设备验收脚本；
- [x] 验证 taskd 的同 ID 并发拒绝、运行状态和取消后退出；
- [x] 在两个持久目录写入专用标记，整机重启后验证容器、网关和标记；
- [x] 重跑认证、资源、组合插件资源、WebSocket 和 LAN 端口隔离。

#### 第 2 轮：安全、升级与产品边界

- [x] 复核容器身份、只读 rootfs、capabilities、security-opt、挂载和资源占用；
- [x] 复核同版本重建与候选失败回滚证据，区分“同版本修复”和“真实版本升级”；
- [x] 检查 Provider 调用授权；未获明确费用授权，因此没有调用模型；
- [x] 检查 aarch64 实机或等价执行环境；当前不存在，保持双架构门槛未通过。

#### 第 3 轮：完整回归与交付判定

- [x] 运行本地合同测试、Shell/Lua/JSON/PO 检查和共享网关 Go 回归；
- [x] 重跑设备验收脚本并核对测试机无临时冲突容器、回滚容器或秘密日志；
- [x] 更新证据矩阵，明确通过项、阻塞项、测试二进制和正式发布边界；
- [x] 因仍缺 Provider 费用授权、真实升级候选和 aarch64 设备，保持 P2/P3 未完成并停止发布。

#### Provider 补充验收（2026-11-26）

- [x] 用户明确授权后，从测试机 KAI Plus 配置识别出 OpenAI-compatible Provider，
  不输出或提交 API Key；
- [x] 在 DSH profile 中新增 `kaiplus` 路由并设为默认模型，凭据副本使用 UID 1000、
  模式 0600 保存，容器重启后 profile 装载和健康检查通过；
- [x] 只读任务正确读取固定标记，工作区文件数量和输入 SHA-256 前后相同；
- [x] 受控写入任务只新增指定文件，内容与预期逐字节相同，原输入 SHA-256 不变；
- [x] 真实调用后重跑设备验收：入口 200、11 项资源 200、WebSocket 101、LAN 直连阻断；
- [x] 修复真实浏览器暴露的 bootstrap base-path 和认证页面缓存问题；顶层未登录导航
  保持 302 登录桥，子资源返回无 `Location` 的 401；
- [x] 后续架构决策改为独立根路径端口：删除 bootstrap 改写与子路径代理，强制启用
  DSH 管理密钥，`/apps/dsh/` 只做 request-host-aware 跳转；
- [ ] 浏览器 Web Session 的审批交互和整机重启后的会话续用仍需单独验证。

### P3：产品闭环与三轮验收

- [ ] 完成七种页面状态及手机/桌面、深浅主题、键盘焦点和错误恢复；
- [ ] 打通首次安装 → 启动 → 打开 → 配置模型 → 选择工作区 → 只读任务 →
  受控写入 → 重启续用；
- [ ] 覆盖未登录、错误/缺少 CSRF、非法路径、端口冲突、磁盘离线/只读/空间不足、
  下载/摘要/npm/原生探测失败、取消、升级启动失败和回滚；
- [ ] 第 1 轮验证功能闭环，第 2 轮审查安全/升级/交互，第 3 轮完整回归；若第三轮
  仍有硬门失败，停止发布并列明阻塞，不修改通过标准；
- [x] 首轮直接复制源码到 x86_64 测试设备，不以预编译 IPK 代替开发测试；
- [ ] 正式发布前完成包文件归属、干净安装、真实版本升级和双架构验收。

### P4：发布治理

- [ ] 固定版本、SHA/SRI、依赖锁、LICENSE、THIRD_PARTY_NOTICES 和 SBOM；
- [ ] 软件中心文案明确 developer preview、资源要求、API 费用和风险；
- [ ] 定义上游破坏性变更的兼容矩阵、更新节奏和撤回策略；
- [ ] 两架构发布候选完成安装、升级、回滚、重启与资源门槛复测。

## 首版验收门槛

以下各项必须同时成立：

1. DSH 始终以非 root 用户运行，Docker 发布独立端口且不使用 host network；
2. 独立端口未认证时只能进入 DSH 登录页，密钥文件为 root/0600；
3. origin root 下静态资源、RPC、WebSocket、Cookie、下载均可用，`/apps/dsh/` 只跳转；
4. 默认工作区可读写，系统敏感文件与其他应用私有目录不可读；
5. 固定版本完整原生依赖在 x86_64/aarch64 都通过实际装载与功能探测；
6. 安装/升级失败保留旧服务，卸载/升级不删除会话、凭据或 Workspace；
7. 页面不复制上游产品设置，不暴露 API Key、启动令牌或完整敏感日志；
8. 真实模型任务产生的费用由用户明确配置并知情，自动测试不默认调用付费模型。

## 非目标

- 不把 DSH 做成 ttyd 终端插件；
- 不把 DSH 加入 AgentFlow CLI Provider 列表；
- 不修改 DSH 上游界面品牌或复制其设置页；
- 不自动修改用户 LAN/WAN 防火墙，不提供多人账号或租户隔离；
- 不承诺第三方 DSH 插件在 OpenWrt 上都可安装；
- 不在兼容性 Spike 前编译 IPK、发布包或写入正式设备。
