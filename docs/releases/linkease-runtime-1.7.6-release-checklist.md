# LinkEase 1.7.6 Manual Release Checklist

Status: ready for operator execution  
Prepared: 2026-09-30 UTC

This checklist deliberately does not upload or publish anything. Runtime asset
upload is the manual boundary requested for this release.

## 1. Upload the Renamed Runtime Assets

Create or update GitHub release `linkease-runtime-v1.7.6` in
`istoreos/istoreos-app-hub`, then upload these six files:

```text
linkease-bin-1.7.6-linux-x86_64.tar.gz
linkease-bin-1.7.6-linux-aarch64.tar.gz
linkease-bin-1.7.6-linux-arm.tar.gz
linkease-common-bin-1.7.6-linux-x86_64.tar.gz
linkease-common-bin-1.7.6-linux-aarch64.tar.gz
linkease-common-bin-1.7.6-linux-arm.tar.gz
```

Each archive must contain the unchanged business binaries from its 1.7.5
counterpart under a sole top-level directory that exactly matches the 1.7.6
archive basename. Verify its size, SHA256, layout, and required files with:

```sh
apps/linkease/tests/check_linkease_runtime_archives.sh \
  tmp/linkease-runtime-v1.7.6/upload 1.7.6
```

Do not rebuild the business binaries. Repacking the archives to update the
top-level directory is required.

## 2. Verify the Release Before Building IPKs

- Confirm all six asset names exactly match the package Makefiles.
- Download each asset from the public release URL and verify SHA256 again.
- Confirm the existing `linkeasefull-runtime-v3.0.22` assets remain available;
  LinkEase Full runtime binaries are unchanged.

Do not publish the new IPKs or feed index until these checks pass. The OpenWrt
build must be able to fetch all referenced runtime inputs.

## 3. Build and Stage Packages

Build from the reviewed package sources. The final expected revisions are:

```text
linkease-common-bin         1.7.6~<variant>-r1
linkease                    1.7.6~<variant>-r1
linkeasefull                3.0.22~<variant>-r2
luci-lib-linkeasefile       2.1.70-r4
luci-app-linkease           2.1.70-r4
linkease-runtime-transition 1.7.6-r1
app-meta-linkease           3.0.0-r3
app-meta-linkeasefull       3.0.22-r3
```

Run `apps/linkease/tests/check_linkease_ipks.sh` against every architecture's
staging directory before indexing the packages.

## 4. Publish in Dependency-Safe Order

Publish and index the leaf packages first:

1. `linkease-common-bin`, `linkease`, and `linkeasefull`;
2. `luci-lib-linkeasefile` and `luci-app-linkease`;
3. `linkease-runtime-transition`;
4. only after all prior packages are downloadable and indexed,
   `app-meta-linkease` and `app-meta-linkeasefull`.

This order prevents a visible meta package from resolving against the legacy
runtime or LuCI generation. Do not expose revision-3 meta packages early.

## 5. Post-Publish Smoke Test

On a device that still has a legacy monolithic LinkEase package, run without
force options:

```text
is-opkg update
is-opkg install app-meta-linkease
is-opkg install app-meta-linkeasefull
```

Accept only if both commands return success, the logs contain no data-file
clash or unknown-package errors, the installed versions match this checklist,
and `check_linkease_split_migration.sh` passes.

If a rollback is required, withdraw the revision-3 meta packages first so new
installations cannot enter a partially published dependency graph. Preserve
the runtime and LuCI packages while diagnosing; they contain the compatibility
handoff needed by already-upgraded devices.
