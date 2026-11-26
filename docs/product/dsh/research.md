# DSH 产品、使用与开发调研

> 调研日期：2026-11-25
>
> 对象：DeepSeek Harness（`dsh`）及其社区生态
>
> 用途：为 iStoreOS 的“Web 工作台型 DSH 插件”确定产品边界与实施前置条件

## 结论摘要

1. **DSH 不是另一个 Codex/Claude Code 风格的终端 CLI。** 官方把它定义为开源 Agent Harness，主入口是浏览器工作台：工作区、会话、模型、工具调用、审批、插件和自动化任务都在同一个 Web 产品中完成。[官方仓库](https://github.com/deepseek-ai/deepseek-harness) · [官方产品页](https://deepseek.com/harness/)
2. **`deepseekdsh.com` 不是 DeepSeek 官方网站。** 站点自己声明由 Linkong 维护、与 DeepSeek 无隶属或背书关系；它适合作为操作案例和问题索引，产品与安全结论仍应以官方仓库和官方文档为准。[站点声明](https://deepseekdsh.com/about)
3. **社区真实扩展方向验证了“Web 工作台”定位。** 代表性需求包括：文件树与差异审阅、项目/会话控制台、多目录或 SSH 工作区、手机/另一台设备继续会话、办公文档产出及人工审核，而不是再增加一个独立终端壳。
4. **iStoreOS 版应是独立的 `luci-app-dsh` / DSH 服务应用。** LuCI 只负责安装、生命周期、存储、反向代理和安全入口；工作区、模型、会话、插件、审批等交互由 DSH 原生 Web UI 负责，避免复制一套很快会过时的 UI。
5. **不能直接照搬普通 Linux 的 `npx` 启动方式。** 当前源码要求 Node.js `^24.22.3 || >=26.13.1`，依赖中包含 PTY 与平台原生组件；OpenWrt/musl、x86_64/aarch64、内存、磁盘和进程沙箱均需先做兼容性验证。[根 `package.json`](https://github.com/deepseek-ai/deepseek-harness/blob/master/package.json) · [CLI `package.json`](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/package.json)
6. **安全边界必须高于普通 CLI 插件。** DSH 能执行模型生成的命令、加载第三方插件并访问文件、网络、进程和凭据；官方明确表示它未经安全审计、不是生产就绪软件，沙箱与审批也不保证隔离。[官方安全说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md)

## 1. DSH 是什么

### 官方事实

- DeepSeek Harness 是 DeepSeek AI 开发的开源 Agent Harness，采用 Cordis 驱动的“一切皆插件”架构，MIT 许可证；目前仍处在 developer preview，官方明确提示会有破坏兼容性的变更。[官方 README](https://github.com/deepseek-ai/deepseek-harness/blob/master/README.md) · [LICENSE](https://github.com/deepseek-ai/deepseek-harness/blob/master/LICENSE)
- 模型适配器、工具注册、会话日志、Agent Loop、Web UI 本身都由插件组成；运行实例是按顺序叠加的 Profile 与 Bundle 树，而不是一个不可替换的核心。[官方架构](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)
- 官方提供 `web`、`headless`、`sdk`、`sdk-minimal`、`acp` 等 Profile；`dsh web` 只是选择 Web Profile 的入口，`dsh plugin --profile <name> ...` 则在对应 Profile 中管理插件。[CLI 参考](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/README.md)
- 官方产品页展示的使用范围同时包括日常办公、代码仓库、资料查证、后台任务、定时任务与插件开发，并提供工具调用轨迹和结果预览。[官方产品页](https://deepseek.com/harness/)

### 产品判断

DSH 更接近“本地优先、可扩展的 Agent 操作系统/工作台”，而不是某个模型厂商的聊天窗口，也不是只能在终端运行的 Coding Agent。模型只是可替换的一层，工作区、会话、工具、权限与插件组合才是核心产品资产。

因此，在 iStoreOS 产品矩阵中应作如下区分：

| 产品 | 主要形态 | iStoreOS 插件职责 |
| --- | --- | --- |
| Codex / Claude Code / OpenCode / Kimi CLI | 终端型单 Agent 工具 | 安装 CLI、账号/凭据状态、浏览器终端、可选 AgentFlow Provider |
| AgentFlow | 多 Agent 编排与任务控制面 | 使用已安装 Provider 执行任务，不再安装这些 CLI |
| **DSH** | **浏览器优先的 Agent 工作台与插件平台** | **运行原生 DSH Web、提供受认证入口、持久化和安全边界** |

## 2. 别人如何使用 DSH

### 2.1 官方的基本用户旅程

官方 Web 指南给出的最短闭环是：

1. 安装 Node.js，运行 `npx @deepseek-ai/dsh web`；默认监听 `127.0.0.1:3080`。
2. 打开 Settings → Models，保存模型 Provider 的 API Key。
3. 选择工作区；未选工作区前，输入框不可用。
4. 创建会话，用自然语言让 Agent 读取/修改工作区文件、运行命令、委派子任务或维护计划。
5. 对需要批准的操作查看路径、命令和范围，再决定允许或拒绝。
6. 在文件系统和测试结果中独立核验产物。

来源：[官方 Web UI 指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/index.md)；独立社区指南提供了一套“先只读浏览、再做小修改、阅读审批、最后离开聊天界面核验文件”的完整示例，但其身份不是官方：[DeepSeekDSH Web UI 实操](https://deepseekdsh.com/guides/web-ui)。

### 2.2 模型与凭据交互

- DSH 原生支持 DeepSeek，也能添加 Anthropic、OpenAI、Moonshot/Kimi、Z.AI/GLM 等第三方 Provider，以及 OpenAI-compatible 自定义端点。
- 保存的 API Key 是只写凭据：设置接口返回脱敏描述，不把明文 Key 送回浏览器；凭据存放于 `$DSH_HOME/.credentials.yaml`，普通设置只保存引用。
- Provider 与模型变更在下一次请求生效，不要求重启服务。

来源：[官方模型配置指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.md)。

### 2.3 社区实际在补什么

下列样本是各社区项目维护者对自己产品的第一方说明，不代表 DeepSeek 官方背书；它们用于识别重复出现的产品需求，而不是证明市场规模。

| 社区行为 | 代表样本 | 暴露的真实需求 |
| --- | --- | --- |
| 在聊天旁查看文件、跳转工具引用、审阅逐文件/逐 hunk 差异 | [`dsh-workbench`](https://github.com/lee259/dsh-workbench) | 用户不希望为查看 Agent 正在改什么而离开浏览器；“对话 + 文件 + Diff”是核心工作台布局 |
| 把本地目录、远端 SSH 目录和多工作区放进同一会话 | [`dsh-workspace-enhancement`](https://github.com/DobyChao/dsh-workspace-enhancement) | DSH 常驻在控制端，计算和文件可在另一台机器；工作区是可替换执行面 |
| 离开电脑后用手机、平板或另一台电脑继续原会话并处理审批 | [DeepSeek Harness Remote 讨论](https://github.com/deepseek-ai/deepseek-harness/discussions/3778) | 长任务需要“查看进度、补充指令、回答问题、处理权限请求”，而不是始终守着终端 |
| 把项目资料变成可编辑、可追溯、需人工批准的 DOCX/XLSX/PPTX/PDF | [`DSH Work`](https://github.com/HuangYuChuh/dsh-work) | 非编码用户把 Workspace 当项目/客户资料夹，把 Session 当工作线程，把 Approval 当交付闸门 |
| 在一个面板观察 Agent、子 Agent、工具调用、Token 与待审批状态 | [`dsh-plugin-mission-control`](https://github.com/Jian-Sparrow/dsh-plugin-mission-control) · [`dsh-mission-control`](https://github.com/fuxiaoji/dsh-mission-control) | 多任务并行以后，用户需要状态汇总与“等待我处理”的收件箱 |
| 让人与 Agent 共享一个可接管的持久 PTY | [Agent Interactive Terminal](https://github.com/deepseek-ai/deepseek-harness/discussions/12370) | 终端是工作台中的一个协作组件，而不是整个产品外壳 |

### 交互模式归纳

社区实践呈现出五个稳定模式：

1. **Workspace-first**：先选项目目录，再创建会话；会话天然属于项目上下文。
2. **Conversation-centered**：需求、澄清、审批与结果说明仍在对话中完成。
3. **Artifact-aware**：文件树、预览、Diff、Office 产物和来源证据与对话并列展示。
4. **Long-running and resumable**：用户会离开页面，之后回来查看进度、回答问题或继续同一会话。
5. **Extensible UI**：插件不只增加模型工具，也会增加侧栏、设置页、面板、终端或完整业务界面。

## 3. 别人如何开发 DSH

### 3.1 修改 DSH 本体

官方源码是 TypeScript/pnpm monorepo。当前开发基线要求 Node.js 24.22.3+ 的 24.x 或 Node.js 26.13.1+、Corepack 管理的 pnpm 11.28.5、Git 2.26+；首次安装依赖后，`pnpm run typecheck` 是最小环境验收，完整产物使用 `pnpm run build`。Web 开发用 `pnpm run dev:web`，它会构建并监听 Client Bundle。[官方开发指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/development.md)

源码运行路径是：

```sh
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
pnpm install
pnpm run build
pnpm dsh web
```

这条路径适合上游贡献和源码调试，不适合 iStoreOS 设备安装：构建需要大型 TypeScript 工程和较高内存，官方开发文档中 Host/Client 聚合类型检查使用 8 GiB V8 old-space 上限。[官方开发指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/development.md)

### 3.2 开发外部插件

官方插件教程定义的最小插件是一个导出 `apply(ctx)` 的 TypeScript 模块。插件通过 `ctx` 注册工具、服务、事件或 UI；所依赖的服务写入 `inject`，Cordis 会等待依赖就绪后再加载；通过 `ctx` 注册的效果会在卸载时自动回收，需要手动释放的资源使用 `ctx.effect()` 返回 disposer。[官方插件教程](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/index.md)

实际开发通常分为：

- **Host 插件**：注册服务、工具、事件、远程 API 或业务状态。
- **Client 插件**：在 Web UI 中增加设置项、侧栏、面板、渲染器或完整交互。
- **Bundle**：把若干 Host/Client 插件和 Cordis 配置打包成可安装层。
- **Profile/Patch**：决定一个 DSH 实例最终装载哪些 Bundle，以及覆盖哪些默认配置。

开发者通过本地绝对路径或 npm/Git 包安装到 Profile；发布后的常见安装形式是：

```sh
dsh plugin --profile web add <package-or-path>
dsh web
```

官方架构强调“没有需要打补丁的特权核心”：新能力应挂在已有 Service/Capability/Event/UI 扩展点上；模型 Provider、工具、Shell、PTY、文件系统、子 Agent、Webhook 和 Client UI 都有独立扩展缝。[官方架构](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)

### 3.3 社区开发的现实约束

- DSH 仍在快速迭代，社区插件经常需要按 DSH 发行线维护兼容矩阵。[`dsh-workspace-enhancement` 兼容说明](https://github.com/DobyChao/dsh-workspace-enhancement)
- Web 插件通常要同时处理 Host 与 Client 入口、DSH 注入的 React 运行时、样式隔离、国际化和 DSH 原生状态 API。[`dsh-workbench` 开发说明](https://github.com/lee259/dsh-workbench)
- Profile 插件安装由 pnpm 驱动；含 `node-pty` 等原生依赖时，构建脚本和目标平台 ABI 是真实交付约束，而不是纯 JavaScript 包的简单复制。[官方 `pnpm-workspace.yaml`](https://github.com/deepseek-ai/deepseek-harness/blob/master/pnpm-workspace.yaml)

## 4. 技术架构与发行事实

### 4.1 运行时结构

```text
dsh CLI launcher
└── Profile（web / headless / sdk / acp / custom）
    ├── ordered Bundles
    ├── profile cordis.patch.yml
    ├── DSH_HOME patch / credentials / sessions / profile packages
    └── optional external plugins
        ├── Host services/tools/events
        └── Client UI extensions
```

Session Event Log 是模型上下文和回放的事实来源；Web UI 的实时增量来自 Agent 事件流。Workspace Registry 则保存项目目录、顺序与会话分组，删除 Workspace 注册不会删除目录、文件或历史会话。[官方架构](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md) · [Workspace 包参考](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/workspace/workspace/README.md)

### 4.2 当前发行与平台约束

- 2026-11-25 的官方 `master` 源码版本字段为 `0.2.3-alpha.2`，Node Engine 为 `^24.22.3 || >=26.13.1`；版本处于预览期，不能把 `latest` 当成稳定兼容契约。[根 `package.json`](https://github.com/deepseek-ai/deepseek-harness/blob/master/package.json)
- 官方桌面下载页只直接提供 Windows x64 与 Apple Silicon macOS；Linux 的官方使用路径是 Node CLI 启动 Web UI。[官方产品页](https://deepseek.com/harness/) · [官方 README](https://github.com/deepseek-ai/deepseek-harness/blob/master/README.md)
- 依赖/构建清单明确包含 `node-pty`、Koffi、平台原生加载器和 Linux musl 变体，但这并不等于已支持 OpenWrt；OpenWrt 的 libc、内核能力、交叉架构与安装脚本仍需在目标机实测。[官方 `pnpm-workspace.yaml`](https://github.com/deepseek-ai/deepseek-harness/blob/master/pnpm-workspace.yaml)
- 官方许可证为 MIT，第三方依赖另有 NOTICE；iStoreOS 打包时应保留上游 LICENSE 与第三方许可证清单。[官方 README](https://github.com/deepseek-ai/deepseek-harness/blob/master/README.md) · [THIRD_PARTY_NOTICES](https://github.com/deepseek-ai/deepseek-harness/blob/master/THIRD_PARTY_NOTICES.md)

## 5. iStoreOS Web 工作台插件的产品启示

### 5.1 推荐边界

`luci-app-dsh` 应提供一个很薄的“设备侧产品壳”：

- 安装/升级固定版本的 DSH Runtime；
- 配置持久化数据目录、工作区根目录、监听端口与服务开关；
- 显示运行状态、版本、存储占用、上游兼容状态和最近错误；
- 提供唯一主入口“打开 DSH 工作台”；
- 通过 iStoreOS 已登录会话保护 `/apps/dsh/`；
- 在网关内把 `/apps/dsh/` 反代到仅监听 loopback 的 DSH Web 服务；
- 提供备份/恢复路径说明与故障诊断，不在 LuCI 中复制 DSH 的 Models、Workspace、Session 或 Plugin 页面。

DSH 原生 Web UI 继续负责：

- 首次引导、模型 Provider 与凭据；
- Workspace 和 Session；
- Agent 模式、工具与审批；
- 文件/产物/轨迹展示；
- DSH 自身插件的安装与配置。

### 5.2 推荐入口交互

LuCI 页面只保留三块：

1. **服务状态**：运行/停止、当前版本、监听状态、更新时间。
2. **存储与安全**：数据目录、受控工作区根目录、仅本机监听、备份提示。
3. **主行动**：`打开 DSH 工作台`；未安装时显示 `安装运行时`，依赖不兼容时显示明确原因，不出现空白 iframe。

点击主入口后使用完整页面打开 `/apps/dsh/`。不建议嵌入 LuCI iframe：DSH 有自己的全屏侧栏、WebSocket、会话 Cookie、文件预览与插件 UI，iframe 会带来高度、焦点、剪贴板、下载和 Cookie 边界问题。

### 5.3 反向代理契约

官方明确支持带路径前缀的反向代理，但外层代理必须：

- 保留浏览器看到的 `Host`；
- 把 `/apps/dsh/` 前缀剥离后再转发给 DSH；
- 转发 WebSocket Upgrade；
- 把后端 Cookie 的 `Path=/` 重写到 `/apps/dsh/`；
- 把 `/apps/dsh` 重定向到带尾斜杠的 `/apps/dsh/`；
- 启动时配置 `--public-url` 与 `--trusted-host`；
- 后端端口只允许网关访问。

DSH 自身还使用启动 Token 与签名 Session Cookie；iStoreOS 认证是更外层的设备访问控制，两者不应互相替代。[官方反向代理指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/public-deployments.md)

### 5.4 必须优先解决的安全问题

1. **不得以 root 运行 DSH。** 官方要求最小权限；而 DSH 的文件沙箱明确只限制写入，读取、列目录和元数据仍不受限制。应创建独立 `dsh` 用户，并依赖 Unix 文件权限阻止其读取 `/etc/shadow`、路由器密钥和其他应用数据。[官方安全说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md) · [`fs-sandbox` 参考](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/fs/fs-sandbox/README.md)
2. **工作区必须落在显式根目录。** 推荐默认 `/mnt/.../DSH/workspaces`，由 `dsh` 用户拥有；不要把 `/`、`/etc`、整个 `/mnt` 或其他应用数据目录作为 Workspace。
3. **服务只监听 loopback。** LAN 访问只走受 iStoreOS 登录保护的 `/apps/dsh/`，不得直接暴露 3080。
4. **默认 `workspace-write`，禁用无提示的 `danger-full-access`。** OpenWrt 上若 bwrap/Landlock 不可用，应失败并清晰提示；不能静默退化为无限制 root shell。[官方 Sandbox 参考](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/sandbox/sandbox/README.md)
5. **插件安装属于高风险操作。** DSH 官方明确说明第三方插件可访问网络、进程、凭据和文件；MVP 应至少提示来源、版本和风险，后续再考虑允许列表或锁定版本。

## 6. 实施前验证清单

在创建正式插件代码前先做一次可丢弃的兼容性 Spike，验收条件如下：

- [ ] mise 能在目标 iStoreOS x86_64 与 aarch64 上安装满足 Engine 的 Node 24/26；
- [ ] 固定 DSH 版本可以离线/可重复安装，不依赖设备现场编译整个上游仓库；
- [ ] `node-pty`、SQLite、Koffi/平台加载器等原生依赖在 musl 上可加载；
- [ ] 普通 `dsh` 用户能启动 `dsh web --no-open`，且 HOME、DSH_HOME、缓存都写入持久盘；
- [ ] DSH 仅监听 `127.0.0.1`；
- [ ] `/apps/dsh/` 在已登录状态可访问，未登录状态被 iStoreOS 拦截；
- [ ] 页面静态资源、API、SSE/WebSocket、下载与 Session Cookie 在路径前缀下正常；
- [ ] 重启服务和设备后，Workspace、Session、Provider 配置仍存在；
- [ ] `workspace-write` 下可在指定工作区读写、无法写出工作区；
- [ ] `dsh` 用户无法读取系统敏感文件和其他应用私有目录；
- [ ] 内存、磁盘、启动时间和一次真实任务的资源峰值可接受；
- [ ] 升级与回滚不会删除 `$DSH_HOME`、Workspace 或凭据。

若 Node/原生依赖或沙箱在 OpenWrt 上不可稳定运行，应停止正式打包，改评估“DSH 运行在独立 Linux 主机/iStoreOS Docker，LuCI 仅提供受认证反向代理与生命周期入口”的部署模型，不应通过 root、关闭沙箱或在线编译来掩盖不兼容。

## 7. 建议的下一阶段目标

> 交付一个以 DSH 原生 Web UI 为中心、由 iStoreOS 提供认证入口和安全运行边界的独立工作台插件；先证明 OpenWrt 运行时与代理契约，再开发完整安装、升级和诊断体验。

具体包拆分、交互状态、认证交接和逐阶段验收见
[`../../plans/dsh-web-workbench.md`](../../plans/dsh-web-workbench.md)。

建议任务树：

1. **P0 兼容性 Spike**
   - 固定 DSH 与 Node 版本；
   - x86_64/aarch64 安装与启动；
   - 原生依赖、沙箱、资源基线；
   - 路径前缀/WebSocket/Cookie 代理验证。
2. **P1 插件骨架**
   - `dsh-runtime`、`luci-app-dsh`、`app-meta-dsh`；
   - 独立用户、procd 服务、UCI 配置、持久目录；
   - `/apps/dsh/` 认证反代与状态页。
3. **P2 产品闭环**
   - 首次启动/未安装/升级/故障状态；
   - Workspace 根目录与备份提示；
   - Provider 设置、首个只读任务、受控写入任务的端到端验收。
4. **P3 发布治理**
   - 版本锁定、校验和、许可证与 SBOM；
   - 升级/回滚/数据迁移；
   - 两架构设备回归与资源门槛。

## 8. 证据边界

- 官方来源用于说明产品定位、架构、运行方式、许可证和安全边界。
- 社区仓库与官方 Discussions 中的插件说明用于归纳“维护者声称解决的场景”；本次没有统计活跃用户数，也没有把 Star、视频播放量或搜索排名当作采用率证据。
- 2026-11-25 已在 iStoreOS x86_64 与 aarch64 完成固定版本 P1 Spike；结果为
  conditional go，而不是“OpenWrt 已支持”。双架构原生与 Web 能运行，但 x86_64
  进程沙箱和共享入口 Cookie Path 仍是正式编码门，详见
  [`../../evidence/dsh-p1-20261125/results.md`](../../evidence/dsh-p1-20261125/results.md)。
- DSH 处于快速迭代期，Node Engine、Profile、插件 API 和代理参数应在实现时锁定到具体版本重新核验。
