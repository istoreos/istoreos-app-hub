# luci-app-linkeasefull-ddnsto

Registers the DDNSTO LuCI page as a standalone LinkEaseFull desktop icon.

The package depends on `luci-app-linkeasefull-embed` and uses the shared
`LuciContainer` builtin component. Its manifest sets:

- `initialPath=/cgi-bin/luci/admin/services/ddnsto/page`
- `contentOnly=true`
- `isolation=scoped-dom-css`
- `mountIds=["root","app"]`
- `hideChrome=true`

This keeps DDNSTO independent as a desktop entry while still running inside the
OpenWrt LuCI runtime.
