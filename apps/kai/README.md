# KAI OpenWrt packaging notes

## Classic KAI package roles

The classic management page is built into `luci-app-kaiplus`, at
`/cgi-bin/luci/admin/services/kaiplus/classic`. The standalone `luci-app-kai`
source recipe and its LuCI sync mapping have been retired. All three runtime
packages remain:

| Package | Source | Installed contents and responsibility |
| --- | --- | --- |
| `kai` | `istore-ai-helper/server` and `web` | `/usr/sbin/kai_bin`: gateway, embedded Web UI, authentication and API forwarding; also owns `/etc/init.d/kai`, `/etc/config/kai`, the session launcher and desktop registration. Default public port: 8197. |
| `kai_session` | `istore-ai-helper/opencode` | `/usr/sbin/kai_session`: AI runtime for model requests, sessions and tools. The launcher binds it to `127.0.0.1:8196`. Also includes `/usr/sbin/rg` for offline file and skill scans. |
| `kai-agent` | `kai-skills` bundle | Local skills, instructions, prompts, `opencode.json` and the provenance manifest under `/usr/share/kai/agent-bundles/<version>/`, selected by `/usr/share/kai/agent`. This is a resource package, not a separate process. |

`kai` requires both `kai_session` and `kai-agent`. `/etc/init.d/kai` launches
the engine and gateway together, using the selected local agent bundle and
the configured writable data directory. KaiPlus (`reasonix-kai`) is a separate
runtime and is not required to execute these classic binaries.

The classic Update button explicitly runs `is-opkg upgrade kai kai_session`
after refreshing the iStore feed. It never installs or updates the retired
`luci-app-kai`. A newer `kai` package can still pull in a newer `kai-agent`
through its minimum-version dependency. Releasing only a new skill bundle
does not force an independent skills update through this two-package button.

## `kai_session` must bundle ripgrep

OpenCode's native `skill` tool invokes ripgrep while enumerating files next to
`SKILL.md`. When `rg` is missing, OpenCode tries to download it from GitHub at
runtime. An iStoreOS router may not have GitHub connectivity, in which case
skill loading fails with:

```text
ripgrep execution failed
```

`kai_session` therefore has an offline runtime contract:

- The prebuilt `kai_session-binary-<version>.tar.gz` contains both
  `kai_session.<arch>` and the static `rg.<arch>` binary.
- `kai_session/Makefile` installs the matching binary as `/usr/sbin/rg`.
- Runtime archives are published under the matching
  `kai-runtime-v<version>` release in `istoreos/istoreos-app-hub`.
- Each changed package must update `PKG_VERSION` and `PKG_HASH` together,
  using its corresponding prebuilt archive. Publish the archives before
  committing or distributing the package update.
- Skills-only updates can release `kai-agent` independently. Keep `kai` and
  `kai_session` at their existing tested runtime version when their code and
  runtime dependencies have not changed.
- Run `./tests/test-local-agent-contract.sh` before committing the plugin.
- On a target device, verify both `/usr/sbin/rg --version` and a real skill
  directory scan. Merely listing available skills does not exercise ripgrep.

Keep this dependency in the release artifact and OpenWrt package. Installation
is intentionally unconditional so a missing architecture-specific `rg` fails
the package build instead of falling back to a first-run network download.

## KAI 0.0.27: packaged skills and LuCI port fixes

KAI is the OpenCode product: `opencode/` builds `kai_session`, `server/`
builds `kai_bin`, and `web/` is embedded in the gateway. KaiPlus is the
separate Reasonix product in `reasonix-kai/`; this release does not update it.
The canonical skills repository is [kai-skills](https://github.com/linkease/kai-skills).

The version set is `kai 0.0.27-r1`, `kai_session 0.0.27-r1`, and
`kai-agent 0.0.27-r1`. OpenCode remains the device-validated `1.18.32` engine
from runtime release `0.0.25`; the release manifest records its actual source
commit rather than the newer source checkout. Classic management now lives in
the `luci-app-kaiplus` classic tab described above.

`kai-skills` is included in the KAI installation through the mandatory
`kai-agent` package. `kai` additionally requires `kai-agent >= 0.0.27~0`, so
upgrading the gateway cannot silently retain an older skills bundle. The
package installs all 20 iStoreOS/OpenCode skills, instructions, the local
OpenCode configuration, and the source manifest under:

```text
/usr/share/kai/agent-bundles/0.0.27/
/usr/share/kai/agent -> agent-bundles/0.0.27
```

These are packaged files, not first-run downloads or external skills URLs.
User configuration remains in the device's writable KAI data directory.
The bundle pins `kai-skills` commit
`a7c5b1e7a855edcbac21ed25e46515e540fc4fae`.

The gateway now discovers LuCI's actual HTTP/HTTPS listeners, preserving the
browser hostname and KAI return port. API, runtime-status, and event-stream
login expiration share a dedicated reauthentication state. This fixes LuCI
ports such as 88 or 10000 being replaced by the HTTP default port 80.

Release assets are under
[kai-runtime-v0.0.27](https://github.com/istoreos/istoreos-app-hub/releases/tag/kai-runtime-v0.0.27).
Each package Makefile pins its own archive SHA-256. The retired `app-meta-kai`
package is intentionally not restored; the current KAI mapping has no meta
package. Do not bump `app-meta-kaiplus` for a KAI release.

From `istore-ai-helper`, reproduce the release with:

```sh
KAI_RUNTIME_BASE_RELEASE=0.0.25 VERSION=0.0.27 make release
```

Verify package installation staging with the actual archive and expected
source commit, in addition to the regular plugin contract checks:

```sh
sh apps/kai/tests/test-local-agent-contract.sh
python3 apps/kai/tests/test_kai_desktop_plugin_contract.py
sh apps/kai/tests/test-agent-bundle-staging.sh \
  /path/to/kai-agent-bundle-0.0.27.tar.gz \
  a7c5b1e7a855edcbac21ed25e46515e540fc4fae
```

## Previous skills update: kai-agent 0.0.26

The released version combination is `kai-agent 0.0.26`, `kai 0.0.25`,
`kai_session 0.0.25` (OpenCode 1.18.32), and `app-meta-kai 1.0.2-r8`.
The Agent bundle uses kai-skills commit
`a7c5b1e7a855edcbac21ed25e46515e540fc4fae`, replacing the
`e5ba9ec05cc6c1160242084e65277a2723a8539c` skills bundled in 0.0.25.

This update adds scoped mise SDK probes and installation receipts, isolated
pip/npm/Go dependency acceptance, and current-run gateway evidence checks.
Client success without gateway evidence is reported as partial/pending. It
also fixes runtime environment and opkg query guidance. The existing local
instructions glob loads the updated routing reminder without a config change.

In the `istore-ai-helper` source checkout, prepare the release with:

```sh
make test-agent-bundle
VERSION=0.0.26 ./scripts/build-agent-bundle.sh
sha256sum build/kai-agent-bundle-0.0.26.tar.gz
```

Expected archive SHA-256:
`04ac5286b45e0e88e9d197992041299250a30d83151f59008fc035b1a0a62ac4`.
The expected value identifies the prepared artifact; changing the product or
skills commit changes the bundle manifest and requires a new checksum.
`kai-agent-bundle-0.0.26.tar.gz`, `agent-manifest.json`, and `SHA256SUMS`
are published in [kai-runtime-v0.0.26](https://github.com/istoreos/istoreos-app-hub/releases/tag/kai-runtime-v0.0.26).
This is an Agent-only release; binaries remain available under
`kai-runtime-v0.0.25`.

Run `sh apps/kai/tests/test-local-agent-contract.sh`, then build and
distribute the updated `kai-agent` and `app-meta-kai` packages. On an
opkg-based device with the updated package feed, apply the update with:

```sh
opkg update
opkg install kai-agent app-meta-kai
/etc/init.d/kai restart
readlink /usr/share/kai/agent
cat /usr/share/kai/agent/manifest.json
(cd /usr/share/kai/agent/skills/istoreos-mise-runtime && \
  OPENCODE_CONFIG=/usr/share/kai/agent/opencode.json \
  /usr/sbin/kai_session debug rg files --glob '**/*' --limit 10)
```

The active link should resolve to `agent-bundles/0.0.26`; use a fresh session
to check the updated skills. User settings remain in the writable data
directory. The upstream skills verification report records x86_64/musl
device acceptance; this package preparation does not establish new ARM,
glibc, apk-device, or cold Node/Go install acceptance.

## HTTP mount contract

The LuCI entry opens the stable `/apps/kai/` root, which KAI redirects to
`/apps/kai/web/`. Browser traffic stays below `/apps/kai/`, including
`/apps/kai/event`, `/apps/kai/session/*` and product
APIs. Keep the plugin entry path aligned with the server mount when either side
changes.
