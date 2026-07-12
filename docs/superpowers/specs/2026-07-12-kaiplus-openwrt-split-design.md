# KaiPlus OpenWrt Split Design

## Goal

Split KaiPlus out of the OpenWrt `linkease` full package and make it an
independent OpenWrt/iStore plugin while preserving the existing LinkEase
Desktop user experience.

The independent KaiPlus plugin must expose:

```text
http://<router-ip>:8189/apps/kaiplus/
```

When LinkEase Desktop is installed, the desktop must expose the same app path
through its own port:

```text
http://<router-ip>:<linkease-desktop-port>/apps/kaiplus/
```

The two packages must remain installable independently.

## Current State

`apps/linkease/linkease` currently packages the LinkEase full tarball and
installs:

- `/usr/bin/linkease-desktop`
- `/usr/bin/apptunnel-client`
- `/usr/lib/linkease/kaiplus`

`linkease.init` starts LinkEase Desktop and injects `KAIPLUS_*` variables that
make the desktop process start an embedded KaiPlus runtime on
`127.0.0.1:19291`, then proxy `/apps/kaiplus/` to that embedded runtime.

`apps/kaiplus` already has the right high-level shape for an independent app:

- `kaiplus`: binary package
- `luci-app-kaiplus`: LuCI page
- `app-meta-kaiplus`: iStore metadata and entry script

The standalone KaiPlus package still needs to align its runtime contract with
the target URL:

- default port must be `8189`
- default base path must be `/apps/kaiplus/`
- init must pass `--base-path` to `kaiplus_bin kaiplus-web`

## Architecture

KaiPlus becomes the owner of the KaiPlus process, files, data directory, LuCI
page, iStore metadata, and public standalone URL. LinkEase Desktop becomes only
a reverse proxy and launcher when it detects that the independent KaiPlus plugin
is installed.

The coupling is intentionally narrow:

- KaiPlus publishes its runtime through UCI and `/etc/init.d/kaiplus`.
- LinkEase reads `kaiplus.@kaiplus[0].port` and proxies to
  `http://127.0.0.1:<port>`.
- Both products use the same path contract: `/apps/kaiplus/`.

No package-level dependency is introduced in either direction. Installing
`linkease` must not install `kaiplus`, and installing `kaiplus` must not install
`linkease`.

## KaiPlus Plugin Changes

Update `apps/kaiplus/kaiplus/files/kaiplus.config`:

- default `port` to `8189`
- add `base_path` with `/apps/kaiplus/`
- keep `system_role` as `istoreos`

Update `apps/kaiplus/kaiplus/files/kaiplus.init`:

- read `base_path` from UCI, defaulting to `/apps/kaiplus/`
- pass `--base-path "$base_path"` to `kaiplus_bin kaiplus-web`
- keep serving static files from `/usr/share/kaiplus/www`
- keep data under the configured `data_dir`

Update `apps/kaiplus/app-meta-kaiplus/config.sh`:

- write `port=8189`
- write `base_path=/apps/kaiplus/`

Update `apps/kaiplus/app-meta-kaiplus/entry.sh`:

- report `href` as `http://$host:${port}/apps/kaiplus/`
- keep `status`, `start`, and `stop` actions independent of LinkEase

Update `luci-app-kaiplus` status/open logic:

- read `base_path`
- open `http://<current-host>:<port><base_path>` instead of hardcoding `/`

## LinkEase Plugin Changes

Update `apps/linkease/linkease/Makefile`:

- stop copying `$(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/kaiplus` into
  `/usr/lib/linkease/`
- keep installing `linkease-desktop` and `apptunnel-client`

Update `apps/linkease/linkease/files/linkease.init`:

- stop creating `$data_root/kaiplus`
- always set `KAIPLUS_ENABLED=0` so LinkEase Desktop does not start an embedded
  KaiPlus runtime
- remove embedded KaiPlus runtime variables:
  - `KAIPLUS_ENABLED=1`
  - `KAIPLUS_BIN=...`
  - `KAIPLUS_STATIC_DIR=...`
  - `KAIPLUS_DEFAULTS_DIR=...`
  - `KAIPLUS_HOME=...`
  - `KAIPLUS_SYSTEM_ROLE=...`
  - `KAIPLUS_ADDR=...`
- if `/etc/init.d/kaiplus` exists, read the KaiPlus port from UCI with fallback
  `8189`, and set `KAIPLUS_PROXY_TARGET=http://127.0.0.1:<port>`
- if `/etc/init.d/kaiplus` does not exist, do not set `KAIPLUS_PROXY_TARGET`

Keep `SERVER_BASE_PATH=/apps/` as the desktop base path. The desktop route
remains `/apps/kaiplus/`.

## Desktop Contract

This OpenWrt phase assumes the existing desktop reverse proxy remains available:

- LinkEase Desktop serves `/apps/kaiplus/`
- if `KAIPLUS_PROXY_TARGET` is set, `/apps/kaiplus/api/...` proxies to the
  target
- the browser-facing URL remains under the LinkEase Desktop host and port

If the current desktop only shows the KaiPlus icon when embedded assets are
enabled, a follow-up desktop change will make the icon appear when
`KAIPLUS_PROXY_TARGET` is configured or when a future app descriptor is present.
If the current desktop still advertises KaiPlus only because embedded assets are
compiled into the binary, that behavior is a known transitional limitation of
the OpenWrt-only phase; the package split still disables the embedded runtime.
The desktop registry follow-up is outside this OpenWrt package phase.

## Migration And Compatibility

Existing `linkease` upgrades must stop installing new embedded KaiPlus files.
This design does not remove user data directories. The existing
`linkease-migrate.sh` must continue to avoid destructive data deletion.

If a previous full package left `/usr/lib/linkease/kaiplus` on disk, the new
package no longer depends on it. Cleanup can be added as a conservative file
removal step only for the known package-owned runtime directory, not for data
directories.

KaiPlus standalone data should continue to default under iStore config storage,
currently `ISTORE_CONF_DIR/KAIPlus` during app-meta configuration.

## Error Handling

If LinkEase starts without KaiPlus installed:

- LinkEase Desktop must still start normally
- no KaiPlus process is started by `linkease.init`
- `/apps/kaiplus/` should not be advertised as an installed app

If KaiPlus is installed but stopped:

- standalone status reports `running=false`
- LinkEase may still set the proxy target, but the desktop icon should either
  show a stopped state or fail cleanly when opened
- starting KaiPlus remains the responsibility of `/etc/init.d/kaiplus`

If the KaiPlus port is invalid or missing:

- fallback to `8189`
- avoid failing LinkEase startup

## Tests

Update or add OpenWrt package contract tests for:

- `kaiplus.config` defaults to port `8189` and base path `/apps/kaiplus/`
- `kaiplus.init` passes `--base-path "$base_path"`
- `app-meta-kaiplus/config.sh` writes port `8189` and base path
- `app-meta-kaiplus/entry.sh` returns `/apps/kaiplus/` in `href`
- `linkease/Makefile` no longer copies `kaiplus` into `/usr/lib/linkease/`
- `linkease.init` no longer sets embedded KaiPlus paths
- `linkease.init` sets `KAIPLUS_ENABLED=0`
- `linkease.init` configures `KAIPLUS_PROXY_TARGET` only from the standalone
  KaiPlus plugin

Run the focused package tests after implementation:

```sh
python3 -m unittest discover apps/linkease/tests
python3 -m unittest discover apps/kaiplus/tests
```
