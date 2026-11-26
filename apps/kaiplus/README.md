# KaiPlus and CLASSIC KAI

KaiPlus is the Reasonix product (`reasonix-kai`). CLASSIC KAI is the existing
OpenCode product (`opencode` + the KAI gateway and embedded Web UI). “Classic”
names the product line; it does not pin an obsolete KAI binary version.

`luci-app-kaiplus` owns both management tabs:

| Tab | Configuration | Service | Internal listener | Data directory suffix |
| --- | --- | --- | --- | --- |
| KaiPlus | `/etc/config/kaiplus` | `/etc/init.d/kaiplus` | Unix `/var/run/kaiplus.sock` | `Configs/KAIPlus` |
| CLASSIC KAI | `/etc/config/kai` | `/etc/init.d/kai` | 8197 | `Configs/KAI` |

The tabs are `/admin/services/kaiplus/settings` and
`/admin/services/kaiplus/classic` beneath the LuCI base URL. The existing
`/admin/services/kaiplus` entry opens the KaiPlus settings tab.

## Shared application entry

KaiPlus's OpenWrt profile is Unix-only. The pinned 1.0.25 source already supports
`--listen-mode unix --socket-path /var/run/kaiplus.sock`; the package and manifest
select that path and LuCI probes it for readiness. The Open action is
`linkease_apps/open?id=kaiplus`, selecting the uhttpd proxy or shared LAN port
19290. KaiPlus has no public Web port or TCP fallback. Backend auth, recovery
points and changeguard setup retain their existing owners. A package upgrade
removes the obsolete KaiPlus port setting and restarts only an active service.
The optional classic runtime below retains its separate TCP contract.
The Reasonix source archive's `packaging/openwrt/kaiplus.init` follows the same
Unix-only profile. Its OpenWrt deployment script uses the current app-hub init,
manifest and complete LuCI sources, registers both directories, and does not
restore obsolete public-port settings. The deployment task displays the socket
path rather than a browser port.

## Optional classic runtime

Installing `luci-app-kaiplus` does not install `kai`, `kai_session`, `kai-agent`,
or `luci-app-kai`. The CLASSIC KAI tab remains available when KAI is absent and
offers installation through a POST/CSRF-protected taskd job:

```sh
/bin/is-opkg install kai
```

The `kai` package pulls in `kai_session` and the mandatory `kai-agent` bundle,
including the local `kai-skills` files. The classic tab implements its own
configuration and status view, so it does not need the standalone
`luci-app-kai` page. Its standalone source recipe and `syncapps.yaml` LuCI
mapping have been removed. Existing KAI runtime configuration and data are
reused; `kai`, `kai_session`, and `kai-agent` remain packaged separately.
Do not restore `app-meta-kai` or `luci-app-kai`.

After installation, the classic tab reloads to show Enable, Data directory,
and Access port. Save & Apply restarts `/etc/init.d/kai` when enabled and
stops it when disabled. It does not restart KaiPlus or LinkEase. The classic service retains its configured TCP port; use distinct
data directories to run both products together. Opening CLASSIC KAI
uses the shared `linkease_apps/open?id=kai` entry resolver, including the
configured authentication and access URL behavior.

The installed classic tab also provides **Update CLASSIC KAI**. The task
refreshes the iStore package index and runs:

```sh
/bin/is-opkg update
/bin/is-opkg upgrade kai kai_session
```

This explicitly upgrades only the classic gateway and runtime engine. It does
not upgrade `luci-app-kai` or the KaiPlus runtime. `kai-agent` remains a mandatory
dependency of `kai`, with a minimum-version requirement; the package manager
can upgrade it when required by a new KAI package. Skills-only updates can
still release `kai-agent` independently.
Updates come from the published iStore package feed; publishing only GitHub
binary archives does not make a version available here. Build and publish the
corresponding IPK/APK packages to the feed first. Normal package upgrades
preserve `/etc/config/kai` and the external KAI data directory. A previously
running, enabled classic service is restarted after the update; otherwise it
is stopped to preserve its prior inactive state. KaiPlus is not restarted.
An update failure remains a failed task with its log and does not report
success. Installation and updating share the same task ID to prevent overlap.

## Package versions and checks

The pending package set uses `kaiplus 1.0.25-r4`,
`luci-app-kaiplus 1.0.11-r5`, and `app-meta-kaiplus 1.0.25-r14`. The runtime
recipe consumes `kaiplus-binary-1.0.25.tar.gz` from the
`kaiplus-runtime-v1.0.25` GitHub release, built from Reasonix commit
`f6913b1fb322b8b6f8e3d9795580510cb703e30d`. Its SHA-256 is
`13d31810ca6dd861515a683a1c7710868cba2895c515295eb064753eada1c628`.
If the candidate is rebuilt, refresh `KAIPLUS_HASH` from the new tarball.
OpenWrt IPK/APK compilation and feed publication remain separate steps. Device
protection uses `changeguard 0.3.5-r4` and `linkspace 0.3.3-r3` from their
matching runtime releases.
Existing `syncapps.yaml` mappings cover all changed packages.

The runtime owns `kaiplus-plugin.json` and the canonical and compatibility
registration links, following the FastNet registration layout. KaiPlus keeps
its desktop module entry and backend authentication settings. Its `logo.png`
is a symlink to `/www/luci-static/resources/app-icons/kaiplus.png`, installed
from `app-meta-kaiplus/logo.png`. The metadata package is the only icon owner;
updating it updates the desktop icon without rebuilding the runtime. A runtime
installed without its metadata package may have no custom icon. The runtime
does not depend on its metadata package, avoiding a circular package dependency.

The runtime tarball carries `kaiplus.x86_64`, `kaiplus.aarch64`, and `kaiplus-web.zip`.
The package installs only the matching binary and the single web archive at
`/usr/share/kaiplus/kaiplus-web.zip`; it does not unpack a `www` directory or duplicate
the web assets inside the binary. The init script passes `--web-zip` explicitly.
The server uses zipserve to send individually precompressed Brotli entries to
clients accepting `br`, with streaming identity fallback for other clients.
HTML stays uncompressed for runtime base-path injection and SPA routing.
Publish the tarball, `kaiplus-web.zip`, and `release.json` together from the
same Reasonix release build. Standalone binaries continue to embed the ZIP.

The KaiPlus runtime requires ChangeGuard >= 0.3.5-r4, and ChangeGuard requires
Linkspace >= 0.3.3-r3 (OPKG uses the equivalent release suffixes). These minimum
versions belong to runtime package dependencies so an installation cannot
silently reuse incompatible protection components.
The market `config.sh` saves the KaiPlus data and backup directories and starts
the service. The default backup directory is the disk-root `TimeMachine`
folder beside `Configs`; KaiPlus applies that global value to ChangeGuard. A
service-start failure is returned to the installer. The focused first-install check is
`python3 apps/kaiplus/tests/test_fresh_install.py`.

Verify the published runtime archive against the recipe (checks both architectures,
checks the hashes and ELF targets, and runs the matching native version command):

```sh
KAI_VERIFY_PUBLIC_RELEASE=1 python3 apps/kaiplus/tests/test_fresh_install.py
CG_VERIFY_PUBLIC_RELEASE=1 python3 apps/changeguard/tests/test_package_contract.py
```

Before upload, verify the exact local candidate instead:

```sh
KAI_RUNTIME_RELEASE_DIR=/absolute/path/to/reasonix-kai/releases/build \
  python3 apps/kaiplus/tests/test_fresh_install.py -v
```

Run the focused checks without downloading an OpenWrt SDK:

```sh
python3 apps/kaiplus/luci-app-kaiplus/tests/test_classic_kai_entry_contract.py -v
python3 tests/istorex-new-ui-contract-test.py
```

The behavior checks require Node.js and Lua 5.1. If Lua is unavailable locally,
the test supports an SSH interpreter:

```sh
LUA_COMMAND='ssh -o BatchMode=yes root@192.168.30.7 lua -' \
  python3 apps/kaiplus/luci-app-kaiplus/tests/test_classic_kai_entry_contract.py -v
```

The Lua harness runs the real source with filesystem, shell, taskd and UCI
stubs entirely in memory. It does not install packages, write configuration,
or change device services. These checks cover optional installation,
incomplete runtime files, authentication/CSRF rejection, duplicate and failed
tasks, independent service control, browser retries and the post-install
reload. They do not replace browser acceptance of compiled IPK/APK packages.
