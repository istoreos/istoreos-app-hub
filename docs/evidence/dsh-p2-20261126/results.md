# DSH P2 x86_64 首轮设备验收

日期：2026-11-26  
设备：iStoreOS `x86_64`，`192.168.30.7`  
结论：**standard 容器的独立根路径端口和 DSH 强制认证已通过 x86_64 验收；P2 尚未完成，不能据此发布。**

## 部署方式

- 直接复制 `apps/dsh` 的运行脚本、UCI、LuCI、应用清单和静态文件到测试机；
- 未编译、安装或缓存 DSH IPK；
- 数据目录：`/mnt/mise-runtime/Configs/DSH`；
- 工作区目录：`/mnt/mise-runtime/Public/DSH`；
- 固定镜像：`ghcr.io/omdsh-dev/dsh-container:0.2.1-rc.2@sha256:a447bbfcafce5d05d1e9cc861c9170bb6907ef1e31ed53a40c588bd6e77d5705`。

测试机的共享应用网关原版本会把 `/plugins/??...` 错误转发为
`/plugins??...`。修复位于相邻 `linkease-desktop` 仓库的
`backend/src/appgateway/handler.go`，并增加真实 DSH 组合资源形式的回归测试。
`go test ./cmd/linkease-app-entry ./src/appgateway` 在 SSD 构建缓存环境通过。

测试候选只构建 `linux-amd64` 的 `linkease-app-entry`，没有构建 IPK：

- 源码基线：`29f5d455ae66f3178b8bdd65c8894b7bce61a907` 加本次未提交修复；
- 测试归档 SHA-256：`3cb7eaa4185c77ef576d58ea254b9de31a740c303d04a8655b88f7c0849b25f3`；
- 当前浏览器认证修复测试二进制 SHA-256：
  `272f30cbc8562f45ad60edf805db4325ee95ab52cbed85bfbecbeae4236a3a07`。

## 通过项

| 范围 | 结果 |
| --- | --- |
| 容器状态 | `running`、`healthy` |
| 身份与隔离 | 用户 `node`、只读 rootfs、`cap-drop ALL`、`no-new-privileges`、非 privileged、无 Docker socket |
| 监听 | Docker 发布 `0.0.0.0/[::]:13080 -> 3080/tcp`；接口范围交给用户防火墙策略 |
| 持久目录 | 两目录均 UID/GID 1000、模式 0750；同版本重建后数据和工作区标记保留 |
| 未登录入口 | 独立端口顶层导航 303 到 DSH 管理密钥登录；子资源返回 401 |
| 已登录入口 | 密钥登录后独立端口根页面 200 |
| 路径规范 | `/apps/dsh/` 返回 307 到 `http://<request-host>:13080/`；子路径资源不代理 |
| 页面资源 | 原生根路径 HTML 引用的 11 项资源全部 200 |
| 浏览器 base path | 保留上游绝对 `/auth-bootstrap.js`，独立端口认证后返回 200；`/apps/dsh/auth-bootstrap.js` 返回 404 |
| 登录缓存 | DSH 登录与未认证响应为 `no-store`，认证 Cookie 由 DSH relay 管理 |
| 未认证子资源 | 独立端口 CSS/JS/Manifest 类请求返回 401，不跳入 LuCI `auth_finish` |
| 未认证顶层导航 | 独立端口返回 303 到 `/_dsh-container/auth/login` |
| WebSocket | 独立端口 `/api/remote.mux` Upgrade 返回 101 |
| 同版本重建 | 新容器 ID 生效，固定 digest 未漂移，两个持久目录内容保留 |
| 失败回滚 | 用占用的候选端口制造 `docker run` 失败；原容器 ID、13080 监听和数据均恢复 |
| taskd | 任务进入 running；同 ID 第二个任务被拒绝；取消在 procd 终止窗口后完成；任务日志删除 |
| 整机重启 | 设备经历离线和重新上线；容器 ID 不变，数据与工作区标记保留，网关和 WebSocket 复测通过 |
| 真实 Provider 只读 | KAI Plus Provider 经 DSH `kaiplus/qwen3.8-flash` 路由返回固定标记；工作区文件数和输入 SHA-256 前后不变 |
| 真实 Provider 写入 | DSH 只新增指定结果文件；内容逐字节匹配预期，原输入 SHA-256 不变 |
| 最终资源快照 | CPU 约 0.08%，内存约 244.2 MiB / 1.916 GiB，25 PIDs |

`auth-bootstrap.js` 是社区容器在 origin-root 页面注入的管理员密钥辅助脚本。standard
配置现在强制启用 `DSH_CONTAINER_KEY`；密钥位于 `/etc/dsh/admin.key`，root/0600，
不进入 UCI、状态输出或测试日志。

## 端口产品决策

`13080` 是 DSH 的独立用户端口，DSH 始终运行在 origin root。`/apps/dsh/` 仅根据当前
请求主机名跳转，不再承载内容。Docker 与其他 iStoreOS 插件一致监听所有接口；
LAN/WAN 可达性由用户防火墙策略决定，插件不自动开关 WAN 规则。

## KAI Plus Provider 补充验收

用户在 2026-11-26 明确授权复用测试机上已经配置的 KAI Plus Provider。验收只读取
Provider 类型、端点和模型等非秘密字段；API Key 未出现在命令输出、证据文件或仓库。
测试机上的桥接方式如下：

- DSH profile overlay 使用 `kaiplus` 路由、`openai-completions` 协议、KAI Plus 已配置
  的端点和默认模型 `qwen3.8-flash`；无秘密 overlay 固化为
  `apps/dsh/tests/fixtures/kaiplus-provider.patch.yml`；
- KAI Plus 的单项 `KOOLCENTER_API_KEY` 被复制到 DSH 私有 `.env`，所有者为 UID/GID
  1000，模式 0600；这是测试机快照，不是两个产品之间的动态凭据同步；
- `/v1/models` 鉴权探测返回 HTTP 200；DSH 重启后 Web 与 headless profile 均解析为
  `kaiplus/qwen3.8-flash`；
- 只读任务返回 `KAIPLUS_READ_20261126`；输入 SHA-256 前后均为
  `8c14b0a2633f565e1c6f20029bf9163c485f9d32f178290379c7c4bc953f3c90`，文件数保持 1；
- 受控写入任务返回 `WRITE_OK`；结果与测试预期逐字节一致，结果 SHA-256 为
  `15cd95ce5d40ef314df7d181736a304d9e5b9c2b0697dfcf07f61269de134b3e`，原输入未改变；
- 完成独立端口迁移后再次运行 `device_acceptance.sh`，结果为未认证导航 303、密钥登录
  后根页面 200、11 项资源 200、bootstrap 200、WebSocket 101、入口 307，容器 healthy。

该补充验收关闭“DSH 是否能使用真实 Provider 完成只读/写入任务”的阻塞，但不等同于
浏览器审批流程、会话重启续用或正式的 KAI Plus 凭据导入产品能力。

## 浏览器认证与独立端口最终修复

真实浏览器报告证明该社区镜像以 origin root 为稳定部署合同。短期的 bootstrap 相对路径
改写虽然能修复一个入口，却会继续引入 manifest、插件资源、API 和未来上游变更的维护面。
最终方案因此改成独立端口，不再对 DSH 内容做 base-path 兼容。

修复后：

- `dsh.sh` 删除入口 HTML 提取、字符串替换和只读 index bind mount，并在成功重建后
  删除旧的 `.istoreos/dsh-index.html`；
- 清单删除 `backend.proxyMode=app-base`，`desktop.target.path=/`，`auth.mode=passthrough`；
- `/apps/dsh/` 返回 307 到 request-host 的 `13080` 根路径，`/apps/dsh/auth-bootstrap.js`
  返回 404，证明内容不再经过子路径代理；
- Docker 发布 IPv4/IPv6 全接口端口，强制 `DSH_CONTAINER_KEY`；未认证浏览器导航 303
  到 DSH 登录页，静态资源 401，认证后 bootstrap/11 项资源 200、WebSocket 101；
- 密钥文件 root/0600；LuCI 可盲写替换密钥，状态页只报告配置状态；
- 容器重建后 Provider 仍为 `kaiplus/qwen3.8-flash`，真实读写验收文件 SHA-256 未变化。

测试网关使用 `CGO_ENABLED=0` 构建为静态 x86_64 ELF。一次普通宿主 glibc 构建在目标机
预执行检查中暴露 libc 不兼容并立即恢复旧二进制，没有继续用于验收；正式发布仍必须走
OpenWrt 的目标工具链和包发布流程。

## 未完成与发布阻塞

- 尚未完成浏览器 Web Session 的交互审批、下载和整机重启后的会话续用；
- 尚未验证真实容器版本升级和干净包安装；GHCR 在检查时只有
  `0.2.1-rc.2` 这一项 0.2.x 容器标签，不能用 `latest` 或跨大版本旧镜像代替升级候选；
- 尚未完成 aarch64 同等容器、代理和回滚验收；
- DSH 管理密钥已强制启用；仍需正式包安装验证 LuCI 首次设置密钥的完整交互；
- 共享 `linkease-app-entry` 修复仍是测试二进制，需要独立提交、版本化和正式发布；
- 测试机上的共享 Lua resolver 也是源码部署状态，正式包升级路径仍需验证。

因此本轮只把 x86_64 standard 的核心部署和安全代理标记为通过，不把 P2/P3 或正式
发布门槛标记为完成。

## LuCI 信息架构与可信主机优化

- 状态区改为紧凑摘要：就绪状态、Web 端口、密钥状态、网络范围和打开按钮；完整镜像
  digest 收进默认折叠的“运行详情”；
- 部署表单改为“访问与安全 / 存储 / 运行环境”三个页签，缩短首屏说明；
- `extra_trusted_hosts` 默认值改为 `*`。这是 iStoreOS 的自动模式标记，运行时展开为设备
  当前 IPv4 地址、路由器 hostname 和 `.lan` 名称，不把上游不支持的原始通配符传给 DSH；
- 自定义 DNS 访问时可把 `*` 替换为精确的逗号分隔 authority；页面同时提示该设置不会
  关闭管理员密钥认证；
- 测试机已安装本轮中文 LMO，重建后自动模式展开为当前设备地址，完整设备验收仍通过。

## 早期子路径方案复验记录（已被独立端口方案取代）

### 第 1 轮：功能与生命周期

- 新增 `apps/dsh/tests/device_acceptance.sh`，临时创建并销毁 ubus Session，不输出
  Cookie、Provider 配置或容器日志；
- 设备脚本通过：认证后根页面 200、11 项资源 200、WebSocket 101、LAN 直连阻断；
- taskd 的运行状态、同 ID 并发拒绝和异步取消通过；
- 整机重启后 Docker 与 app-entry 自动恢复，两个持久目录标记保留并已清理。

### 第 2 轮：安全与边界

- 再次确认 non-root、只读 rootfs、`cap-drop ALL`、`no-new-privileges`、无 Docker
  socket 和 loopback-only；
- manifest 可解析出 `linux/amd64` 与 `linux/arm64`，但测试机为 x86_64 且没有
  `qemu-aarch64` binfmt，因此 aarch64 仍是运行阻塞，不以 manifest 代替实测；
- [DSH 官方发布页](https://github.com/deepseek-ai/deepseek-harness/releases)已有更新版本，
  但选择的社区容器仓库没有相应固定镜像；上游 npm/桌面版本不等于可直接升级的容器；
- 没有用户确认的 Provider 费用授权，本轮没有发起模型请求。

### 第 3 轮：完整回归

- DSH 本地合同测试 7 项通过，Shell、Lua、JSON、PO 和 diff 检查通过；
- SSD 缓存环境执行 `GOWORK=off go test ./cmd/linkease-app-entry ./src/appgateway` 通过；
- 首次 Go 回归因 Unix socket 测试路径超过 Linux 长度限制失败，改用仍指向 NVMe 的
  `/tmp/d3` 短软链接后通过；没有修改测试标准或回退到机械盘；
- 重跑设备脚本通过，确认无 `dsh-rollback`、`dsh-port-conflict`、taskd `dsh` 任务、
  临时标记或任务日志残留。

## 独立端口迁移验收记录

1. 第 1 轮在停止旧容器前发现目标 BusyBox 没有 `od`，密钥生成 fail closed；旧容器
   保持 healthy。改用目标已提供且实测通过的 `hexdump`。
2. 第 2 轮容器成功重建；端口解析器最初只接受 IPv4 映射，随后修正为同时接受 Docker
   返回的 `0.0.0.0` 与 `::` 同端口映射。浏览器探针补齐 `Accept: text/html` 与
   `Sec-Fetch-Mode: navigate` 后，最终设备脚本通过。
3. 第 3 轮执行完整回归和残留清理；不再需要兼容性 index、回滚容器或部署暂存目录。

最终设备摘要：`health=healthy port=13080 auth=303 root=200 bootstrap=200 assets=11
websocket=101 launcher=307 legacy_subpath=404`。Provider 输入/输出 SHA-256 与迁移前一致。
