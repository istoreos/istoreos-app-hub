# LinkEase Apps integration

Routed applications use one LuCI launch contract and one runtime entry. An
application does not depend on LinkEaseFull and does not implement uhttpd,
worker, authentication, or fallback decisions in its own controller.

## Package contract

An application package:

1. depends on `linkease-app-entry`;
2. installs its manifest at an application-owned stable path;
3. creates a symlink in `/usr/share/linkease/apps.d`;
4. may also create the legacy `/usr/share/linkeasefull/desktop-apps.d` symlink
   during the compatibility window;
5. removes a symlink in `prerm` only when `readlink` still points to its own
   manifest.

The OpenWrt LuCI embed is an intentional exception: its manifest declares
`desktop.mode=builtin` and names the LinkEaseFull-only `LuciContainer`
component. It remains owned by `luci-app-linkeasefull-embed`, depends on
`linkeasefull`, and registers only in the LinkEaseFull desktop directory. The
fallback gateway must ignore builtin manifests rather than pretending they are
standalone `/apps` applications.

Its LuCI package depends on `luci-lib-linkeaseauth`. App metadata launches:

```text
/cgi-bin/luci/admin/services/linkease_apps/open?id=<app-id>
```

The shared status endpoint is:

```text
/cgi-bin/luci/admin/services/linkease_apps/status?id=<app-id>
```

`open` is a public, read-only intent-capture endpoint so LuCI cannot discard
its `id` query before authentication. `status` remains protected by LuCI.
Authentication is split into two routes:

```text
/cgi-bin/luci/admin/services/linkease_auth/auth?return=<apps-url>
/cgi-bin/luci/admin/services/linkease_auth/auth_finish/<base64url-state>
```

Auth Begin is public and only validates and encodes an `/apps` return target.
Auth Finish is protected by LuCI and performs the session handoff. Putting the
validated return intent in the path lets LuCI preserve it through its login
redirect, supports independent browser tabs, and avoids relying on one shared
pending-return cookie. The cookie flow remains as a compatibility fallback for
old callers. The state is routing data, not a credential, and Finish validates
it again before redirecting.

Existing application-specific routes may delegate through
`luci.model.linkease.apps_compat` while old UI clients are supported.

## Manifest contract

IDs are lower-case letters, digits, `_`, or `-`, begin with a letter or digit,
and are at most 64 characters. The manifest supplies the standalone `/apps`
path and backend transport data. No central controller switch is required.

For Unix-first applications with an optional TCP fallback, declare UCI-backed
values:

```json
{
  "schemaVersion": 1,
  "id": "example",
  "standalone": { "basePath": "/apps/example/" },
  "backend": {
    "transport": "unix",
    "values": {
      "externalPortEnabled": {
        "default": false,
        "keys": { "uci": "example.@example[0].external_port_enabled" }
      },
      "port": {
        "default": 8080,
        "keys": { "uci": "example.@example[0].port" }
      }
    }
  }
}
```

Legacy TCP applications may use `portFromUci` and `defaultPort`. If their
direct listener serves a different path from the `/apps` route, they declare
`externalBasePath` (for example `/`). External URLs always reuse the current
request host and never accept a host from a manifest.

Browser-direct `iframe` applications, such as FastNet, use a generic
`desktop.target` with a UCI-backed port. `/apps/<id>/` authenticates through the
shared entry and then redirects to that same-device port; if the shared entry
is unavailable, the Apps LuCI Entry resolves the same target as the external
fallback. LinkEaseFull and the gateway implement the same redirect-only
behavior and never proxy the measurement traffic.

## Runtime and security behavior

The decision order is fixed:

1. use `/apps/<id>/` when uhttpd proxy support, its mapping, and the active
   entry worker are available;
2. otherwise use an explicitly enabled external port;
3. otherwise report the registered application as unavailable.

`open` and `status` are read-only. A GET never changes UCI, enables a port,
starts an application, or switches a worker. Browser launch passes through the
existing Auth Bridge. API requests without an application session receive 401,
invalid IDs receive 400, unknown IDs receive 404, and registered unavailable
applications receive 503.

An authenticated browser request for `/apps/` (`Accept: text/html`) receives a
small application launcher. Explicit JSON clients continue to receive the
manifest index (`Accept: application/json`), so the existing API contract is
unchanged.

`linkease-app-entryd` owns the stable listener and passes its file descriptor
to exactly one worker. It does not proxy HTTP, so the gateway fallback adds no
extra entryd HTTP hop. The executable names remain stable for upgrade safety;
“Apps Gateway” is the role, while `linkease-app-gateway` remains the installed
binary name.

## Verification

The router acceptance base URL is intentionally non-default:

```sh
cd /config/playwright-runner
BASE_URL=http://192.168.30.7:10000 npm run linkease-apps:preflight
BASE_URL=http://192.168.30.7:10000 npm run linkease-apps:gate
EXPECTED_WORKER=gateway BASE_URL=http://192.168.30.7:10000 npm run linkease-apps:worker-smoke
EXPECTED_WORKER=linkeasefull BASE_URL=http://192.168.30.7:10000 npm run linkease-apps:worker-smoke
```

Reports must not contain authentication material. Production-like final state
for gateway-only testing is `linkeasefull.enabled=0`, force marker present,
`active=gateway`, and no `linkease-full` process.
