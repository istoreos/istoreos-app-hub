# LinkEase Apps integration

Routed applications use one LuCI launch contract and one runtime entry. An
application does not depend on LinkEaseFull and does not implement uhttpd,
worker, authentication, or fallback decisions in its own controller.

## Product and package boundaries

The source tree groups the shared Apps capability with the LinkEaseFull
business family, but keeps every reusable capability as an independent IPK:

```text
apps/linkeasefull/
  linkeasefull/                 # full desktop runtime
  linkease-app-entry/           # entry arbiter and fallback gateway IPK
  luci-lib-linkeaseauth/        # shared auth and launch integration IPK
  luci-app-linkeasefull/
  luci-app-linkeasefull-embed/
  app-meta-linkeasefull/
```

Directory ownership does not imply a package dependency. The dependency flow
is one-way: `linkeasefull` depends on `linkease-app-entry`, and
`linkease-app-entry` depends on `luci-lib-linkeaseauth`. Neither shared package
depends on `linkeasefull`, so a standalone app can install and run the fallback
gateway without installing the full desktop.

The entry package also has its own small
`linkease-app-entry-runtime-<version>-<target>.tar.gz` artifact. It must not
reuse the LinkEaseFull runtime archive: standalone apps should not download the
full desktop payload, and entry releases must be independently buildable and
upgradable. The source remains in `linkease-desktop`; its release and verify
scripts produce exactly the two worker binaries consumed by this package.

`app-meta-linkeasefull` is the desktop and storage core product. It includes
the embedded OpenWrt desktop component, but deliberately does not pull in
Docker Manager, KaiPlus, Kai, BaiduDrive, KSpeeder, or other business apps.
`app-meta-istorex` is the complete iStoreNAS product bundle and is the layer
that aggregates `app-meta-linkeasefull` with those app meta packages. New apps
must not be added to the LinkEaseFull core merely to make them part of the
iStoreNAS bundle.

## Package contract

An application runtime package:

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

Its LuCI package directly depends on both `luci-lib-linkeaseauth` and
`linkease-app-entry`. The former provides the Lua launch/auth interface; the
latter provides the selectable gateway worker used when `/apps` proxying is
available. Do not rely only on the runtime package to pull these dependencies
transitively: the LuCI package directly exposes this capability and must retain
a complete dependency closure if runtime packaging changes. App metadata may
depend on the LuCI package rather than repeating both shared dependencies.

### Dependency ownership for new applications

Package dependencies are part of the shared launch interface, not an optional
packaging detail. Use this ownership model:

| Package role | Required dependency | Reason |
| --- | --- | --- |
| application runtime that owns the manifest | `+linkease-app-entry` | installs the small gateway/supervisor needed for `/apps` routing |
| LuCI package that exposes an open button or compatibility route | `+luci-lib-linkeaseauth +linkease-app-entry` | directly consumes the Lua resolver/auth interface and the entry runtime |
| app-meta package | runtime package and LuCI package | receives shared dependencies transitively through the packages whose capabilities it exposes |
| LinkEaseFull-only builtin | `+linkeasefull` | has no independent application entry and is intentionally desktop-only |

The explicit LuCI dependency on `linkease-app-entry` is intentional even when
the application runtime already depends on it. The LuCI package directly owns
the launch button. If the runtime package is later split, replaced, or changes
its dependency list, installing the LuCI package must still produce a working
launch flow. OpenWrt/opkg deduplicates the repeated dependency, so this adds no
second copy of the runtime.

Current applications follow the same interface while retaining different
implementations:

| Application ID | Runtime package | LuCI package | Notes |
| --- | --- | --- | --- |
| `kai` | `kai` | `luci-app-kai` | runtime also directly uses `luci-lib-linkeaseauth` for KAI's LuCI authentication middleware |
| `dockermanager` | `dockermanager` | `luci-app-dockermanager` | Unix-first; direct TCP fallback is user-controlled |
| `fastnet` | `fastnet` | `luci-app-fastnet` | browser-direct target still uses shared launch/auth resolution |
| `kspeeder` | `istoreenhance` | `luci-app-istoreenhance` | package names are historical; manifest application ID remains `kspeeder` |
| `agentflow` | `agentflow` | `luci-app-agentflow` | app-base service using the common launch route |
| `baidudrive` | `baidudrive` | `luci-app-baidudrive` | direct listener root differs from the shared public path |
| `kaiplus` | `kaiplus` | `luci-app-kaiplus` | runtime and LuCI remain, but there is no current `app-meta-kaiplus` |

For example, a new application's packages normally contain:

```makefile
# Runtime package
define Package/example
  DEPENDS:=+linkease-app-entry
endef

# LuCI package
LUCI_DEPENDS:=+example +luci-lib-linkeaseauth +linkease-app-entry

# Software-center metadata
META_DEPENDS:=+example +luci-app-example
```

Avoid these dependency mistakes:

- depending only on `luci-lib-linkeaseauth`: the Lua route exists, but no small
  entry worker is guaranteed to serve the uhttpd `/apps` mapping;
- relying only on `runtime -> linkease-app-entry`: this makes the LuCI launch
  capability depend on an unrelated future runtime packaging decision;
- adding `linkeasefull` to make routing work: independent applications must
  remain installable without the full desktop;
- repeating shared dependencies in app-meta: app-meta should aggregate product
  packages, not become a second owner of runtime capability;
- implementing uhttpd/worker checks in each controller: delegate through
  `luci.model.linkease.apps_compat` and the shared resolver instead.

Any Makefile dependency change must increment that package's `PKG_RELEASE`.
It does not require a runtime binary version change.

App metadata launches:

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
`standalone.externalOpen.path` (preferred) or the legacy backend
`externalBasePath` (for example `/`). The standalone declaration wins when
both exist. External URLs always reuse the current request host and never
accept a host from a manifest.

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

`linkease-app-entry supervisor` owns the stable listener and passes its file
descriptor to exactly one worker. It does not proxy HTTP, so the fallback adds
no extra HTTP hop. When LinkEaseFull is unavailable, it starts the same binary
as `linkease-app-entry gateway`. There is one installed executable but two
separate process roles, preserving lifecycle and failure isolation while
sharing one Go runtime on disk.

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

The application-specific no-proxy matrix and the KAI incident regression are
documented in [the routing test runbook](../operations/linkease-app-routing-test.md).
