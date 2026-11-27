# OpenClawMgr (openclawmgr)

## 交互/操作设计

目标：所有“长耗时/可失败”的操作都通过 `taskd` 运行，并在 LuCI 中弹出日志窗口（xterm），执行期间禁止并发启动其他任务。

### 操作分层

- **主流程（常用）**
  - `安装`：验证 Node 与 OpenClaw 候选后部署、生成配置；默认不启用服务
  - `升级`：验证候选后切换；保留原运行状态，启动失败恢复旧运行时与数据快照
  - `启动/重启/停止`：服务控制（必要时联动 enabled）
- **高级（危险/低频）**
  - `卸载`：移除运行时（保留数据目录）
  - `清理（含数据）`：移除运行时 + 删除数据目录

### 日志策略

- **任务日志（taskd）**：每次点击操作都创建/复用 `task_id=openclawmgr`，立即弹窗追踪 `/var/log/tasks/openclawmgr.log`。
- **安装器日志（installer.log）**：`${base_dir}/log/installer.log` 持久保存阶段和退出状态；完整命令输出在 taskd 日志中。LuCI 可“一键查看”安装器日志（只读）。

### 并发控制

- LuCI 侧：操作按钮点击后立即禁用，直到 taskd 返回任务结束。
- 系统侧：依赖 `taskd` 自身锁机制（`/etc/init.d/tasks task_add ...` 返回非 0 表示已有任务在跑）。

### Save & Apply（配置应用）

- `Save & Apply` 不直接在 LuCI 进程内执行重启，而是通过 taskd 创建 `task_id=openclawmgr` 任务去执行：
  - `"/usr/libexec/istorec/openclawmgr.sh" restart`
- 页面加载时如检测到 `openclawmgr` 任务在运行，会自动弹出 taskd 日志窗口。

## 依赖

- `luci-lib-taskd`（含 `luci-lib-xterm` 与 `taskd`）、curl/CA、tar/xz、jsonfilter、Git HTTPS、ttyd。
- `ks-cli` 使用现有 OpenWrt 软件包；不运行普通 Linux 的 ks-cli/zsetup 安装器。
- `mise-runtime` 提供持久磁盘中的公共固定 Node/npm、GNU loader/C++ 库及普通 UID 执行入口；`coreutils-timeout`、`coreutils-stat`（读取 inode）及现有 libstdcpp/libatomic；系统 BusyBox 需提供 `setsid`。先在运行时环境页面配置持久存储。新版本不依赖 `openclawmgr-glibc` 包。
- 开启安装加速时需要已启用的 `istoreenhance`；缺少或关闭时明确报错，可关闭安装加速后使用源站。

## 安装事务

实现目标、任务树及最多三轮检查记录见
[`../../docs/plans/openclawmgr-installation.md`](../../docs/plans/openclawmgr-installation.md)。

1. 安装和升级都检查持久目录、架构、libc、空间和 inode。默认预留 2 GiB 工作空间，
   另外计算现有 data 快照所需空间；至少需要 30000 个可用 inode（不报告 inode 总量的文件系统除外）。
2. `runtime-policy.json` 声明固定 Node 24.22.1/npm 11.19.1、GNU ABI 和库修订。
   安装器通过公共 `mise-runtime request ensure` 安装、校验或复用确切实例；SDK 和库只保存在公共存储。
   每个应用 release 的 `runtime.json` 固定存储根、实例、库和清单摘要，Node 目录仅提供小型入口脚本。
   不跟随全局默认，不复制共享 SDK，不原地升级其 npm；engines 不满足时保留原应用并报错。
3. stable 固定为官方 extended-stable `openclaw@2026.10.34`，兼容回退版固定为既有产品兼容基线
   `openclaw@2026.3.28`；latest 只解析一次。三个通道最终都按精确版本安装。校验目标 engines，
   按精确版本 `npm pack`，再独立核对包名、版本及 SHA512，随后安装本地 tarball。
   依赖包仍由 npm 使用其完整性元数据验证；不声称仅锁定顶层版本就锁定了整个依赖树。
4. 候选在 `${base_dir}/.install.*/candidate` 安装，使用独立 HOME 做 CLI smoke。
   sharp（目标包声明时）执行基本功能检查；通过已安装 OpenClaw 的 memory-host SDK 加载入口检查 sqlite-vec，实际执行 `vec_version()`、
   建立 vec0 表、插入向量并验证最近邻查询。缺少扩展不再允许降级通过安装。
   node-pty 执行加载检查；已核对的 2026.3.28 仍允许其普通子进程回退，并明确记录 PTY 不可用。
   可选 Matrix 原生集成另外记录真实可用性，不把 Gateway 健康当成频道验收。
   Gateway 健康不等同于 Matrix 频道、PTY 交互或模型推理的端到端验证。
5. 候选验证期间旧服务继续运行。切换前先停止服务并确认停止，完整备份 data 到
   `backups/事务ID/data.tar`。然后切换 `current`，生成配置，检查认证 gateway health。
   默认 disabled 的新安装也会临时在 loopback 启动、关闭频道等集成做健康检查，通过后停止，保持最终未启用状态。
   health CLI 为慢设备冷加载预留每次 60 秒、最多 3 次，失败仍回退。
6. 失败时恢复旧入口和 data 快照，失败候选写入的数据保存在同一备份目录的
   `failed-data`。回退失败保留事务日志和锁；恢复可再次尝试。成功升级保留 `previous`。
   配置写入使用临时文件和 rename；备份目录为 0700，配置文件为 0600。

运行时目录：

```text
OpenClawMgr/
  current -> releases/事务ID
  previous -> releases/上一个事务ID
  node -> current/node
  global -> current/global
  releases/事务ID/{node,global,runtime.json,receipt.json}
  # node/bin/{node,npm,npx,git} 解析该 release 的固定公共实例
  # 共享 SDK 和库位于 mise 的持久 storage_root，应用 release 不持有副本
  data/
  npm-cache/
  backups/事务ID/{data.tar,failed-data/}
```

旧版本的 node/global 实体目录在停服后迁入独立 legacy release，继续通过原路径使用。
记录 `current/receipt.json` 包含精确版本、engines、npm、平台、包完整性、Node 来源/摘要、
原生模块能力及安装时间；`runtime.kind=mise-runtime` 记录确切实例、存储根、实际 glibc 版本和库清单 SHA256。Node 摘要来自实际执行的共享二进制；原始归档校验由公共管理器维护。
历史 releases 和成功备份不自动删除，需运维确认后清理；卸载运行时保留 data 和备份。
“清理（含数据）”会删除这些内容。

### 版本通道与手动回退

- `stable`：推荐稳定版 `2026.10.34`。
- `compat`：兼容回退版 `2026.3.28`，仅用于故障恢复，可能缺少较新的安全更新。
- `latest`：官方 latest，解析一次后固定精确版本完成本次事务。

成功升级后，页面仅在 `previous` release 和与当前 release 对应的升级前 `data.tar`
同时有效时显示“回退到上一可用版本”。回退不联网：先停服务并归档当前数据，再同时恢复
previous 程序和升级前数据，最后执行 Gateway 健康检查。目标启动失败会恢复回退前程序、
数据和服务；异常中断使用：

```sh
/usr/libexec/istorec/openclawmgr.sh recover_rollback
```

当前版本产生的数据保存在 `backups/rollback-*/forward-data.tar`，不会自动合并进旧版本。
跨版本回退必须使用该事务入口，不能手工只切换 `previous`。

## 固定公共运行时与 glibc 启动链路

已有私有/musl 安装更新插件后，执行一次“升级”迁移。旧实体目录迁入 legacy release，旧 Node/库保留以支持失败回退；仅更新插件不搬移 SDK 或改变运行中的应用。

应用的 `shared-runtime.lua` 验证 release 绑定与公共收据，再使用 `mise-runtime exec`。
公共 GNU Node 以固定库实例的 `ld.so --library-path` 启动，`process.execPath`/fork 仍回到同一入口。
宿主 sh/git/ks-cli 保持原环境；npm 平台选择明确为 glibc。库来源和完整性由公共管理器负责，
不修改系统 `/lib`，不需要设备 apt/Docker 或系统 C 工具链。

procd 必须使用专用非 root 账户，HOME/用户名/缓存明确落在应用持久 data 中。
root 管理命令通过 `exec-user` 清除附加组、设置 UID/GID，再执行同一公共入口。
启动前校验公共库及实际向量查询，Gateway 自身再以服务 UID 校验并保存
`data/.openclaw/runtime-native.json`。读取凭证 env 文件按字面解析，禁止作为 root shell 执行。

SDK 被用户明确删除后显示“固定运行时缺失”并拒绝启动；恢复该实例或执行应用升级重新准备。
卸载应用只删除其 release/wrap，保留公共 SDK、库和其他调用方；保留 data 的原有卸载语义不变。

## 加速与脚本策略

- 公共 Node/库的下载、摘要、缓存和安装任务由 mise-runtime 负责；应用只持有自己提交的计划身份，取消不会删除已成功的共享实例。
- npm 的查询、打包和安装经固定实例适配器调用 `ks-cli npm`，服务 readiness、能力和 TLS 端口由 ks-cli 处理。
  依赖安装使用 prefer-offline 复用持久缓存，缺失内容仍联网获取；版本解析和独立完整性校验照常执行。
- npm 的 Git 子进程通过 `npm-git.sh` 显式调用 `ks-cli git`，关闭加速则调用原生 Git。
  支持的 GitHub HTTPS 读取由 ks-cli 加速；SSH、私有源和其他平台保留 ks-cli 的原生语义，
  不写用户 Git 配置、不擅自改写 SSH 鉴权方式。
- 固定 Matrix 0.4.0 的下载脚本通过标准 npm script-shell 适配：只匹配版本、工作目录、命令和脚本 SHA256，按官方 asset SHA256/大小复验 `npm-cache/native`；缺缓存按选择使用 ks-cli download 或 HTTPS 源站。下载临时文件放事务目录，取消会清理。其他生命周期脚本保留原行为；任意 HTTP 下载不保证加速。
- 依赖安装上限 3600 秒，其他命令一般为 900 秒；具体 health/native 检查有更短时限。均可取消并恢复所属进程。
- 不再因 musl 全局设置 ignore-scripts。npm 11.16+ 对顶层 OpenClaw 显式添加 allow-scripts；
  必要原生模块仍须通过实际检查。缺少平台产物时失败并保留旧服务，不自动在路由器安装编译工具链。
- LuCI 交互终端通过 release npm shim 复用固定实例和进程级策略；由公共适配器选择原生 npm，避免递归包装。
  用户手动升级 OpenClaw 会绕过管理器事务，并可能因收据版本不一致而被启动检查拒绝；
  使用界面“升级”可保持收据一致并获得回退保护。

## 取消与恢复

取消先给安装协调进程发送 TERM。外部命令在 exec 前经过持久进程握手，记录 boot ID/PID/start/session；协调者回收自己及子命令的会话后才回退和清理。SIGKILL 后恢复会先原子关闭登记目录、回收已记录的所属进程，随后恢复应用事务。
LuCI 仅在协调者清理完成后删除 taskd 状态；不强杀协调者，也不提前移除锁。
有异常中断的事务时，后续安装会要求先恢复：

```sh
/usr/libexec/istorec/openclawmgr.sh recover_install
```

恢复失败时保留日志并返回非零，不删除恢复证据；空配置不阻断恢复入口，恢复前先检查备份
归档。缺失/无效归档不会触发停服、指针切换或 data 移动。事务文件不完整、多个中断日志或磁盘故障
需要人工检查；本地 SIGKILL 测试不是断电/文件系统损坏保证。所有外部业务状态、数据目录之外
的文件和远端副作用不在快照范围内。成功提交后的跨版本数据降级也不能仅靠切换 previous。

## 本地验证与设备验收

安装及升级会在下载前检查 Gateway 端口；只允许当前数据目录对应的受托管 Gateway 占用该端口。旧目录中的残留 Gateway 或其他服务占用时返回 `PORT_IN_USE`，先停止旧实例或在配置页选择其他端口。服务停止后、候选版本激活前还会再检查一次，不把其他实例的响应当作新版本健康状态。

```sh
/var/cache/build-cache/run.sh -- env OPENCLAWMGR_TEST_NODE=/path/to/node-24.22.1/bin/node \
  python3 -B apps/openclawmgr/tests/test_installation.py
```

在仓库根执行。测试用 fake UCI/procd/网络/npm，只有 runtime-check 与微型 CLI 使用真实 Node，
不安装宿主服务、不运行真实 OpenWrt 包。可用 `OPENCLAWMGR_TEST_SHELL='busybox ash'` 和
`OPENCLAWMGR_TEST_BUSYBOX=/absolute/path/to/busybox` 验证 BusyBox applets。
历史本地验证见 `docs/evidence/openclawmgr-installation-20261123/`；后续 x86_64 与 arm64
设备验收证据见 `docs/evidence/openclawmgr-devices-20261123/`，以其中的最终验收报告为准。
glibc 改造与后续设备结果见 `docs/evidence/openclawmgr-glibc-20261123/`，任务树见
`docs/plans/openclawmgr-glibc.md`。旧证据中的向量降级结果不代表当前策略。
设备测试部署后端候选文件，不等同于 SDK 构建的 ipk 安装或浏览器端完整验收。

## 配置来源

- `UCI` 仅保留 `enabled`、`base_dir`、`install_accelerated` 这类外层管理配置。
- OpenClaw 运行配置统一以 `${base_dir}/data/.openclaw/openclaw.json` 为准，包括 `port`、`bind`、`token` 以及模型/鉴权相关设置；LuCI、安装脚本与 init 脚本均优先读取该文件。
- 数据目录用下拉框列出各挂载盘的 `Configs/OpenClawMgr` 候选，同时保留当前目录及自定义路径输入。选择其他目录只编辑表单，保存前不会修改配置；更换目录不会自动迁移已有安装和数据。
- 服务状态同时展示 Node 版本、绑定的 libc/版本及 mise 来源；点击运行时标签进入公共运行时页面，标签提示显示固定实例。ABI 信息来自验证后的 SDK/库收据，未能验证绑定时显示未知，不从 Node 版本号推断 glibc。


## 当前开发测试方式

M5 起按用户要求直接同步脚本、必要二进制与正式前端到 x86_64/ARM64 测试机，逐批保存文件摘要与回滚备份。
入口及使用方法见 [直接部署说明](../mise/tools/README.md)。同一设备的完整 M5 场景使用
`tests/with-device-lease.lua` 串行运行，防止多个场景在各自的服务操作之间互相干扰。

当前逐项结果以 [M5 执行记录](../../docs/evidence/mise-runtime-execution-20261123/M5/progress.json) 为准。
源码直部署的功能通过不代表包依赖、包归属或安装/升级钩子通过；IPK/APK 编译和包验收留待人工确认后人工进行。

## 仓库切换与启动恢复

切换公共 Runtime 目录不搬迁应用包或业务数据。重启时 procd 先运行 root 准备入口，在新仓库按当前 release 的准确 Node/npm/库修订准备依赖，校验成功后原子更新 runtime.json，再清空附加组并切换专用非 root UID 执行 Gateway。Gateway 启动仍执行 sqlite-vec 实际查询。

准备在受监管的后台进程执行，init 不等待网络下载。手动启动/重启提交后台启动，界面显示准备状态、失败原因和运行时任务入口。同一次启动的准备失败不会被 procd 重复触发下载，显式重启可重试。旧仓库保留；依赖准备失败不回退旧仓库。配置 UCI 保持私有，非 root 入口仅读取 /var/run/mise-runtime-root.json 中的当前仓库路径。
