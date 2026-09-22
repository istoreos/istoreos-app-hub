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

Its LuCI package depends on `luci-lib-linkeaseauth`. App metadata launches:

```text
/cgi-bin/luci/admin/services/linkease_apps/open?id=<app-id>
```

The shared status endpoint is:

```text
/cgi-bin/luci/admin/services/linkease_apps/status?id=<app-id>
```

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
```

Reports must not contain authentication material. Production-like final state
for gateway-only testing is `linkeasefull.enabled=0`, force marker present,
`active=gateway`, and no `linkease-full` process.
