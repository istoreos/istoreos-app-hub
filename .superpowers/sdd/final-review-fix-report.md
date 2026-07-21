# LinkEaseLite Final Review Fix Report

## Scope

- Rebased file-manager browser requests on `/cgi-bin/luci/linkeaselite`.
- Stripped the LuCI prefix before forwarding requests to the Lite Unix socket.
- Preserved browser-provided proxy headers and removed LuCI sysauth-derived forwarding headers.
- Reconciled `firewall.linkeaselite` on every service restart and removed only that rule on package removal.

## RED Evidence

```text
rtk python3 -m unittest \
  apps.linkeaselite.tests.test_linkeaselite_contract.LinkEaseLiteContractTest.test_init_reconciles_firewall_on_every_restart \
  apps.linkeaselite.tests.test_linkeaselite_contract.LinkEaseLiteContractTest.test_runtime_package_removal_deletes_only_its_firewall_rule \
  apps.linkeaselite.tests.test_linkeaselite_contract.LinkEaseLiteContractTest.test_luci_backend_proxies_to_lite_socket
```

The focused contract run failed with three expected failures: no restart-time firewall reconciliation, no package removal hook, and no LuCI-prefix stripping/static route update.

## GREEN Evidence

- The same focused command passed: `Ran 3 tests ... OK`.
- `rtk python3 -m unittest discover apps/linkeaselite/tests` passed: `Ran 12 tests ... OK`.
- `rtk sh -n apps/linkeaselite/linkeaselite/files/linkeaselite.init` passed.
- `rtk git diff --check` passed with no whitespace errors.
- The forbidden full-runtime reference scan produced no matches.
- The required-reference scan found the expected Lite binary, socket, conflict, architecture artifact, and port references.
- The hash-pinned check printed `db0811ee189f859b4c8a434338697a57cd2d40d6162b955d3acd3f6b8aee442c`.
- `rtk git diff --exit-code 941f6b4 -- apps/linkease` passed with no output.

## External Artifact Note

The GitHub release artifact for `linkeaselite-v3.0.0` currently returns 404. The controller confirmed that `gh` is unavailable and this repository remote is `istoreos/istoreos-app-hub`; publishing `linkeaselite-v3.0.0` to `linkease/istore-packages` remains an external release step. `PKG_SOURCE_URL` was not changed.
