# KaiPlus and CLASSIC KAI

KaiPlus is the Reasonix product (`reasonix-kai`). CLASSIC KAI is the existing
OpenCode product (`opencode` + the KAI gateway and embedded Web UI). “Classic”
names the product line; it does not pin an obsolete KAI binary version.

`luci-app-kaiplus` owns both management tabs:

| Tab | Configuration | Service | Default port | Data directory suffix |
| --- | --- | --- | --- | --- |
| KaiPlus | `/etc/config/kaiplus` | `/etc/init.d/kaiplus` | 8189 | `Configs/KAIPlus` |
| CLASSIC KAI | `/etc/config/kai` | `/etc/init.d/kai` | 8197 | `Configs/KAI` |

The tabs are `/admin/services/kaiplus/settings` and
`/admin/services/kaiplus/classic` beneath the LuCI base URL. The existing
`/admin/services/kaiplus` entry opens the KaiPlus settings tab.

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
stops it when disabled. It does not restart KaiPlus or LinkEase. Use distinct
ports and data directories to run both products together. Opening CLASSIC KAI
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

This UI update uses `luci-app-kaiplus 1.0.9-r9` and
`app-meta-kaiplus 1.0.9-r3`. Runtime binaries are unchanged. Existing
`syncapps.yaml` mappings cover both changed packages.

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
