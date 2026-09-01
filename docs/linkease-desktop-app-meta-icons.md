# LinkEase Desktop Icons from app-meta Packages

This note is for future AI agents and maintainers adding LinkEase Desktop icons
for OpenWrt/iStoreOS apps in this repository.

## Goal

Some apps should appear as LinkEase Desktop icons as soon as their OpenWrt
package is installed. For simple LuCI-only apps, do this in the `app-meta-*`
package without changing the shared `meta.mk`.

Use the package's existing `root/` directory support:

```makefile
if [ -d ./root ]; then \
  cp -pR ./root/* $(1)/; \
else true; fi
```

Files placed under `apps/<id>/app-meta-<id>/root/` are installed verbatim into
the target filesystem.

## Recommended Pattern

For a LuCI-only app such as DDNSTO, place the desktop manifest here:

```text
apps/<id>/app-meta-<id>/root/usr/share/linkeasefull/desktop-apps.d/16-<id>.json
```

Place the app icon under the app-specific LinkEase static root:

```text
apps/<id>/app-meta-<id>/root/usr/share/linkeasefull/app-meta/<id>/logo.png
```

Prefer a symlink to the runtime app-meta icon installed by `meta.mk`:

```text
/usr/share/linkeasefull/app-meta/<id>/logo.png
-> /www/luci-static/resources/app-icons/<id>.png
```

Do not symlink from `root/usr/share/.../logo.png` back to the source tree
`app-meta-<id>/logo.png`. OpenWrt packaging preserves symlinks, so such a link
would be broken on the target device.

## DDNSTO Example

Current DDNSTO layout:

```text
apps/ddnsto/app-meta-ddnsto/
  logo.png
  root/
    usr/share/linkeasefull/
      desktop-apps.d/16-ddnsto.json
      app-meta/ddnsto/logo.png -> /www/luci-static/resources/app-icons/ddnsto.png
```

The manifest uses LinkEase Desktop's builtin LuCI container:

```json
{
  "schemaVersion": 1,
  "id": "ddnsto",
  "name": "DDNSTO",
  "icon": "logo.png",
  "staticRoot": "/usr/share/linkeasefull/app-meta/ddnsto",
  "desktop": {
    "mode": "builtin",
    "component": "LuciContainer",
    "props": {
      "initialPath": "/cgi-bin/luci/admin/services/ddnsto",
      "contentOnly": true,
      "isolation": "scoped-dom-css",
      "mountIds": ["root", "app"],
      "hideChrome": true,
      "preloadScripts": ["/luci-static/linkeasefull-embed/embed-prelude.js"],
      "preloadStyles": ["/luci-static/linkeasefull-embed/embed.css"]
    }
  },
  "standalone": {
    "url": "/cgi-bin/luci/admin/services/ddnsto"
  },
  "window": {
    "width": 980,
    "height": 700,
    "singleton": true
  }
}
```

## Meaning of `staticRoot`

`staticRoot` tells LinkEase Desktop where package-owned static assets live.

When the manifest contains:

```json
"icon": "logo.png",
"staticRoot": "/usr/share/linkeasefull/app-meta/ddnsto"
```

LinkEase serves the icon from:

```text
/usr/share/linkeasefull/app-meta/ddnsto/logo.png
```

and exposes it to the frontend as a desktop icon URL.

For builtin LuCI apps, `staticRoot` is mainly used for the icon. For full desktop
modules, it can also host `desktop-entry.js`, `index.html`, CSS, and other
assets.

## When to Use This Pattern

Use this app-meta `root/` pattern when:

- the app is a simple LuCI-only app;
- the app already has `META_LUCI_ENTRY`;
- the app already has `logo.png`;
- changing the source LuCI app package is inconvenient;
- only one desktop icon manifest is needed.

Examples include simple service configuration pages such as DDNSTO.

For apps with their own web UI and dynamic ports, such as Jellyfin, do not model
them as LuCI-only. They need a service launch strategy: running opens the
external service URL, stopped opens the LuCI settings page.

For apps with existing desktop module assets, such as:

```text
istoreenhance/files/www/desktop-entry.js
istoreenhance/files/www/index.html
istoreenhance/files/istoreenhance.config
istoreenhance/Makefile
```

the app-meta package can still ship the LinkEase Desktop manifest if modifying
the app source package is not desirable. In that case the manifest should point
to the already installed module assets instead of `LuciContainer`.

## Avoid Duplicate Packages

Do not keep a separate companion package such as
`luci-app-linkeasefull-<id>` if the same desktop manifest has been moved into
`app-meta-<id>`. Two packages owning the same
`/usr/share/linkeasefull/desktop-apps.d/*.json` path can create install/remove
conflicts.

## Self-Check

For a new app-meta desktop icon, verify:

```bash
jq -e . apps/<id>/app-meta-<id>/root/usr/share/linkeasefull/desktop-apps.d/*.json
test -L apps/<id>/app-meta-<id>/root/usr/share/linkeasefull/app-meta/<id>/logo.png
readlink apps/<id>/app-meta-<id>/root/usr/share/linkeasefull/app-meta/<id>/logo.png
```

On a target device with LinkEaseFull installed, verify:

```bash
curl -fsS http://<router>/apps/api/v1/contracts/apps |
  jq '.data.apps[]? | select(.id=="<id>")'
```

The returned app should have:

- `launchMode="component"` for builtin LuCI apps;
- `component="LuciContainer"`;
- `props.initialPath` under `/cgi-bin/luci/...`;
- `props.contentOnly=true` for plugin content pages that should hide LuCI menu
  chrome.
