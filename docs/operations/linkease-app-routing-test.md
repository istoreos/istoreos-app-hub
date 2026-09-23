# LinkEase application routing and test runbook

## Purpose

This runbook records the KAI routing incident as a reusable contract for every
LinkEase application. A plugin's LuCI button must express an application ID;
the shared resolver decides whether to use the uhttpd `/apps` route or a direct
listener. Individual controllers must not duplicate proxy detection, host, or
authentication URL construction.

Every LuCI package that exposes this launch flow directly depends on both
`luci-lib-linkeaseauth` and `linkease-app-entry`. Its runtime package also
depends on `linkease-app-entry` when it owns the application manifest. This
intentional overlap prevents a future runtime-package refactor from silently
breaking the LuCI launch button.

The stable launch API is:

```text
/cgi-bin/luci/admin/services/linkease_apps/open?id=<app-id>
```

The diagnostic API is:

```text
/cgi-bin/luci/admin/services/linkease_apps/status?id=<app-id>
```

Both preserve the browser's current host. This matters for LAN IPs, WAN IPs,
DDNS names, non-default uhttpd ports, and an outer reverse proxy.

## The KAI incident

The router UI was opened through `http://192.168.30.7:10000`, while KAI listened
on port `8197`. An application-specific button built its own authentication URL
and lost uhttpd's `:10000`. A later implementation always selected
`/apps/kai/web/`, even after the uhttpd proxy mapping was removed.

The correct public contract is `/apps/kai/`. KAI itself redirects that root to
`/apps/kai/web/`; callers must not encode that implementation detail.

KAI's manifest therefore declares:

```json
{
  "standalone": {
    "basePath": "/apps/kai/",
    "externalOpen": { "enabled": true }
  },
  "desktop": {
    "mode": "iframe",
    "target": {
      "hostMode": "request-host",
      "path": "/apps/kai/",
      "port": { "keys": { "uci": "kai.@kai[0].port" } }
    }
  }
}
```

Expected resolution:

| uhttpd `/apps` proxy and worker | Result |
| --- | --- |
| available | `http://<current-authority>/apps/kai/` |
| unavailable | `http://<current-host>:<kai-port>/apps/kai/` |

For the test router those are respectively
`http://192.168.30.7:10000/apps/kai/` and
`http://192.168.30.7:8197/apps/kai/`.

## Shared resolution contract

The resolver in `luci.model.linkease.apps_openwrt` uses this order:

1. choose `/apps/<id>/` only when uhttpd proxy support, its `/apps` mapping,
   and an active LinkEase entry worker are all present;
2. otherwise choose a manifest-enabled direct listener;
3. otherwise return `503` without enabling a port or starting a process.

For a direct URL, the path precedence is:

1. `standalone.externalOpen.path`;
2. iframe `desktop.target.path`, or backend `externalBasePath`;
3. the application's public base path.

This distinction prevents the KSpeeder failure mode: its shared route is
`/apps/kspeeder/`, but its direct listener serves `/`, so the fallback URL must
be `http://<host>:5003/`, not `http://<host>:5003/apps/kspeeder/`.

## Application differences

| Pattern | Applications | Direct behavior when shared entry is absent |
| --- | --- | --- |
| app-base service | KAI, AgentFlow | same `/apps/<id>/` path on the app port |
| module with different direct root | KSpeeder | explicit `externalOpen.path`, currently `/` |
| module with matching direct root | BaiduDrive | backend `externalBasePath`, currently `/` |
| Unix-first, optional TCP | Docker Manager, KaiPlus | unavailable unless the user enabled the external port |
| browser-direct iframe | FastNet | redirect to its configured service port; do not proxy measurement traffic |
| LinkEaseFull builtin | OpenWrt embed | no standalone fallback; requires LinkEaseFull |

Do not normalize these applications into one transport model. They share the
launch decision and manifest vocabulary, while each plugin retains its backend
transport and public-path semantics.

## Source-level verification

Before behavioral tests, verify the package dependency closure. Every LuCI
caller must match both shared packages, while runtime packages must retain
`linkease-app-entry` and must not gain `linkeasefull`:

```sh
for file in \
  apps/kai/luci-app-kai/Makefile \
  apps/dockermanager/luci-app-dockermanager/Makefile \
  apps/fastnet/luci-app-fastnet/Makefile \
  apps/istoreenhance/luci-app-istoreenhance/Makefile \
  apps/agentflow/luci-app-agentflow/Makefile \
  apps/baidudrive/luci-app-baidudrive/Makefile \
  apps/kaiplus/luci-app-kaiplus/Makefile
do
  grep -Eq '^LUCI_DEPENDS:=.*\+luci-lib-linkeaseauth.*\+linkease-app-entry' "$file" || exit 1
done

for file in \
  apps/kai/kai/Makefile \
  apps/dockermanager/dockermanager/Makefile \
  apps/fastnet/fastnet/Makefile \
  apps/istoreenhance/istoreenhance/Makefile \
  apps/agentflow/agentflow/Makefile \
  apps/baidudrive/baidudrive/Makefile \
  apps/kaiplus/kaiplus/Makefile
do
  grep -Eq '^([[:space:]]*)DEPENDS:=.*\+linkease-app-entry' "$file" || exit 1
done

if grep -R '^\(LUCI_\)\?DEPENDS:=.*+linkeasefull' \
  apps/{kai,dockermanager,fastnet,istoreenhance,agentflow,baidudrive,kaiplus}/*/Makefile
then
  exit 1
fi
```

The OpenWrt embed is deliberately excluded because it is a LinkEaseFull-only
builtin rather than an independent application.

Run the package contracts from the repository root:

```sh
python3 -m unittest \
  apps/kai/tests/test_kai_desktop_plugin_contract.py \
  apps/istoreenhance/tests/test_istoreenhance_package_contract.py \
  apps/dockermanager/tests/test_dockermanager_package_contract.py \
  apps/fastnet/tests/test_fastnet_package_contract.py \
  apps/baidudrive/tests/test_baidudrive_openwrt_contract.py \
  apps/kaiplus/tests/test_kaiplus_openwrt_contract.py \
  apps/agentflow/luci-app-agentflow/tests/test_agentflow_luci_open_contract.py \
  apps/linkeasefull/tests/test_linkease_apps_package_contract.py

sh apps/kai/tests/test-local-agent-contract.sh
```

The Lua resolver test needs OpenWrt's Lua/LuCI modules. It can be staged on a
test router without installing a package:

```sh
ssh root@192.168.30.7 'mkdir -p /tmp/linkease-apps-lua-test/luci/model/linkease'
scp apps/linkeasefull/luci-lib-linkeaseauth/luasrc/model/linkease/apps.lua \
  apps/linkeasefull/luci-lib-linkeaseauth/luasrc/model/linkease/apps_openwrt.lua \
  root@192.168.30.7:/tmp/linkease-apps-lua-test/luci/model/linkease/
scp apps/linkeasefull/luci-lib-linkeaseauth/tests/test_linkease_apps_openwrt.lua \
  root@192.168.30.7:/tmp/linkease-apps-lua-test/test.lua
ssh root@192.168.30.7 \
  'LINKEASE_APPS_SOURCE_ROOT=/tmp/linkease-apps-lua-test lua /tmp/linkease-apps-lua-test/test.lua'
```

The test covers KAI's app-base path, KSpeeder's `/` direct root, Docker
Manager's disabled/enabled external port, FastNet's browser-direct target, and
the unsupported standalone behavior of the OpenWrt builtin.

## Router acceptance on a non-default uhttpd port

Back up configuration before changing proxy state:

```sh
ssh root@192.168.30.7 \
  'cp /etc/config/uhttpd /root/uhttpd.before-app-routing-test.conf'
```

With the proxy enabled, launching KAI through the shared `open` endpoint must
eventually reach:

```text
http://192.168.30.7:10000/apps/kai/
```

With the `/apps` uhttpd proxy mapping removed and uhttpd reloaded, the same
launch endpoint must eventually reach:

```text
http://192.168.30.7:8197/apps/kai/
```

Repeat the no-proxy test for each installed application using the table above.
Docker Manager and KaiPlus must return unavailable while their external ports
are disabled. Restore the saved uhttpd configuration after the test if the
router is expected to return to proxy mode.

Never store LuCI cookies, passwords, auth state, or session-bearing URLs in
test logs or this repository.
