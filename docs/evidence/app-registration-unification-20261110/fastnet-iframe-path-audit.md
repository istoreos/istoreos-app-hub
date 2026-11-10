# FastNet iframe 与 LAN 数据路径核对

2026-11-10。结论：页面使用 iframe，但当前从 Quickstart 卡片及 LinkEase 桌面打开的 LAN 测速仍经过应用网关；不能视为浏览器直连测速。

## 源码调用链

- FastNet `quickstart-card/src/WebDialog.vue` 创建 iframe，入口为 `/cgi-bin/luci/admin/services/fastnet/embed`。
- `apps/fastnet/luci-app-fastnet/luasrc/controller/fastnet.lua` 的 action_embed 解析同源应用网关入口，再通过认证跳转打开页面。
- FastNet 清单同时声明 desktop.mode=iframe 和 backend.proxyMode=app-base。桌面 `backend/src/common/apps/registry.go` 因 app-base 将 iframeUrl 设置为 `/apps/fastnet/`，而非设备的 3200 端口。
- FastNet `cmd/fastnet/webui-src/src/composables/useFastnet.js` 将 LAN transport 注入为 `fetch(publicPath(path), options)`。当页面位于 `/apps/fastnet/` 时，publicPath 同样给 `/ping`、`/download`、`/upload` 加该前缀。
- 桌面 `backend/src/appgateway/handler.go` 和 `backend/src/routes/routes.go` 将这些请求反向代理到 FastNet 服务。

实际路径为浏览器 → 应用网关 → FastNet。直接打开 `http://设备局域网地址:3200/` 时，LAN 相对路径请求才直接抵达 FastNet（端口以设备 UCI 配置为准）。

## 范围与后续

本次应用登记目录迁移没有修改上述传输路径，也没有解决代理对 LAN 测速性能的影响。未运行带宽测试，不据此声称具体损耗比例。

满足用户要求应让测速 iframe 使用设备实际 FastNet 地址，使 LAN 数据不经过 Quickstart、LuCI 或桌面网关。实现时还需一并处理 HTTPS 页面嵌入 HTTP 服务、主题跨源消息、访问凭据与共享历史；这些属于独立的传输路径修复，不应以改一个 iframe 标签代替完整处理。
