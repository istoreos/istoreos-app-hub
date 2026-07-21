# LinkEaseLite OpenWrt Design

Date: 2026-07-21
Status: approved for planning
App id: `linkeaselite`

## Context

`apps/linkease` now represents the OpenWrt LinkEase full package. It downloads the full binary bundle, installs `linkease-desktop` and `apptunnel-client`, and starts desktop plus remote-access procd instances. That package is intentionally scoped to larger devices.

The new requirement is an OpenWrt LinkEaseLite package for smaller-memory devices under `istoreos-app-hub/apps`. It should use the new `apptunnel` lite client instead of restoring the old `linkease` 1.7.5 LinuxStorage binary.

The user approved these binary naming contracts:

- Installed runtime path: `/usr/sbin/linkease-lite`
- Release artifact member: `linkease-lite.$(ARCH)`

## Goals

1. Add a new app-hub app with id `linkeaselite`.
2. Package a single lightweight runtime process.
3. Preserve the legacy LinkEaseLite network contract: listen on port `8897`, expose a local Unix API socket, and accept `--allowPublic`.
4. Keep the full `linkease` app isolated from Lite.
5. Keep LuCI and UCI names distinct so support and debugging can identify which edition is installed.
6. Cover the package with contract tests similar to the existing `apps/linkease/tests/test_linkease_full_contract.py`.

## Non-Goals

1. Do not modify `apps/linkease` full behavior.
2. Do not run `linkease-desktop`, `apptunnel-client`, KaiPlus, rclone, Syncthing, mountremote, or full desktop UI from the Lite package.
3. Do not embed the old 1.7.5 LinuxStorage binary.
4. Do not add `linkmount` as a dependency for the new package. The selected runtime is the `apptunnel` lite client, not the old LinuxStorage package.
5. Do not implement a multi-edition selector inside one OpenWrt package.

## Package Layout

The new app directory should be:

```text
apps/linkeaselite/
  app-meta-linkeaselite/
    Makefile
    config.sh
  linkeaselite/
    Makefile
    files/linkeaselite.config
    files/linkeaselite.init
    files/linkeaselite.uci-default
    files/linkeaselite-config.sh
  luci-app-linkeaselite/
    Makefile
    luasrc/controller/linkeaselite.lua
    luasrc/model/cbi/linkeaselite.lua
    luasrc/view/linkeaselite_status.htm
    root/etc/uci-defaults/50_luci-linkeaselite
    po/zh-cn/linkeaselite.po
  tests/test_linkeaselite_contract.py
```

The app id must be `linkeaselite`, matching `apps/linkeaselite` and `app-meta-linkeaselite`.

## Runtime Package

`apps/linkeaselite/linkeaselite/Makefile` should define:

- `PKG_NAME:=linkeaselite`
- `PKG_SOURCE:=linkeaselite-binary-$(PKG_SOURCE_DATE).tar.gz`
- `PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-binary-$(PKG_SOURCE_DATE)`
- `DEPENDS:=@(arm||x86_64||aarch64) +ca-bundle`
- `CONFLICTS:=linkease`
- conffile: `/etc/config/linkeaselite`

The install step should copy:

```make
$(INSTALL_BIN) $(PKG_BUILD_DIR)/linkease-lite.$(ARCH) $(1)/usr/sbin/linkease-lite
```

The first implementation should support `arm`, `x86_64`, and `aarch64`, matching the old OpenWrt LinkEase architecture support surface. `mipsel` can be added later only after a verified `apptunnel` lite binary exists for that target.

The exact `PKG_SOURCE_URL`, `PKG_SOURCE_DATE`, and `PKG_HASH` should be pinned during implementation to the actual published artifact. The design expects a tarball whose top-level files include `linkease-lite.arm`, `linkease-lite.x86_64`, and `linkease-lite.aarch64` for the supported architectures.

## Runtime Process

The init script should start one procd instance:

```sh
PROG=/usr/sbin/linkease-lite
LOCAL_API=/var/run/linkeaselite.sock

procd_open_instance linkeaselite
procd_set_param limits nofile="65535 65535"
procd_set_param command "$PROG"
procd_append_param command --deviceAddr ":$port" --localApi "$LOCAL_API"
[ "$allowPublic" = "1" ] && procd_append_param command --allowPublic
procd_set_param respawn
procd_set_param stdout 1
procd_set_param stderr 1
procd_close_instance
```

Default config:

```text
config linkeaselite
  option enabled '1'
  option port '8897'
  option allowPublic '0'
```

The package is a replacement for the full LinkEase package on small devices, not a same-device co-run service. `CONFLICTS:=linkease` avoids port, socket, and identity confusion.

## LuCI Surface

`luci-app-linkeaselite` should be intentionally small:

- Page title: `LinkEaseLite`
- Config options: enable, port, allowPublic
- Status polling: `pidof linkease-lite`
- Open button: `http://<router-host>:<port>/`
- Optional file-management button through LuCI backend proxy

If the backend proxy is included, it should use `/var/run/linkeaselite.sock` and a LuCI route under `linkeaselite`, not `linkease`.

The Lite LuCI surface should not include Full UI port, desktop base path, desktop status, edition selector, KaiPlus integration, or `apptunnel-client` status.

## Build Artifact Source

The runtime binary should come from `apptunnel/cmd/client/scripts/build-client.sh` with:

```sh
BUILD_MODE=lite
TARGETS="linux/arm/5 linux/amd64 linux/arm64"
```

The artifact packaging step should rename outputs to OpenWrt `ARCH` names:

```text
linux/arm/5 -> linkease-lite.arm
linux/amd64 -> linkease-lite.x86_64
linux/arm64 -> linkease-lite.aarch64
```

The `apptunnel` lite build uses the tags:

```text
vendorLinkease linkease_lite disable_smb disable_sftp disable_s3 no_relay disable_proxy nomsync
```

The build process must continue running `verify-lite-deps.sh` so the binary does not import full dependency families such as rclone, Syncthing, goleveldb, mountremote, mobilebridge, or relay.

## Migration And Coexistence

The package should not migrate or delete full LinkEase state. It should preserve its own `/etc/config/linkeaselite` values on upgrade.

Because `linkeaselite` conflicts with `linkease`, switching editions should be handled by uninstalling one package and installing the other. The implementation should not remove user data directories during install, upgrade, or uninstall.

## Tests

Add `apps/linkeaselite/tests/test_linkeaselite_contract.py` covering:

1. Package name is `linkeaselite`.
2. Makefile installs `$(PKG_BUILD_DIR)/linkease-lite.$(ARCH)` to `/usr/sbin/linkease-lite`.
3. Package declares `/etc/config/linkeaselite` as a conffile.
4. Package declares `CONFLICTS:=linkease`.
5. Package does not install `linkease-desktop`, `apptunnel-client`, KaiPlus, or `linkmount`.
6. Init starts one procd instance using `/usr/sbin/linkease-lite`.
7. Init passes `--deviceAddr ":$port"` and `--localApi /var/run/linkeaselite.sock`.
8. Init appends `--allowPublic` only when enabled.
9. LuCI status checks `pidof linkease-lite`.
10. LuCI does not mention Full UI, desktop port, desktop base path, KaiPlus, or `apptunnel-client`.

After implementation, run the app-specific Python contract test and the repository-level app metadata checks used by app-hub.

## Acceptance Criteria

1. `apps/linkeaselite` exists with runtime, LuCI, meta, and tests.
2. Installing `linkeaselite` provides `/usr/sbin/linkease-lite`.
3. `/etc/init.d/linkeaselite start` runs one `linkease-lite` process.
4. The runtime listens on the configured port, default `8897`.
5. The local API socket is `/var/run/linkeaselite.sock`.
6. LuCI can enable, disable, show status, and open the Lite web entry.
7. `linkease` full package files and behavior remain unchanged.
8. Contract tests pass.
