# LinkEase Apps 3.0.21 version ledger

> Frozen release record. For the current integration contract, use
> `docs/architecture/linkease-apps-integration.md`. Later package versions are
> intentionally not backported into this ledger.

This ledger is the release baseline for the shared LinkEase application-entry
architecture. Runtime payload or public integration API changes receive a new
version and reset release to `1`. Packaging, dependency, manifest, LuCI, and
metadata-only changes retain their upstream version and increment release.

## Core packages

| Package | Baseline | Target | Change class |
| --- | --- | --- | --- |
| `linkeasefull` | `3.0.20-r2` | `3.0.21-r1` | runtime payload |
| `app-meta-linkeasefull` | `3.0.20-r2` | `3.0.21-r1` | product version alignment |
| `linkease-app-entry` | `3.0.20-r4` | `3.0.21-r1` | runtime payload |
| `luci-lib-linkeaseauth` | `1.1.0-r3` | `1.2.0-r1` | public integration API |
| `luci-app-linkeasefull-embed` | `1.0.0-r3` | `1.1.0-r1` | embedded LuCI capability |
| `luci-app-linkeasefull` | `1.0.0-r2` | `1.0.0-r3` | LuCI packaging |

`linkeasefull` intentionally uses `PKG_SOURCE_DATE` as its package version for
compatibility. It must not introduce a second `PKG_VERSION` declaration.

## KAI packages

| Package | Baseline | Target | Change class |
| --- | --- | --- | --- |
| `kai` | `0.0.23-r1` | `0.0.23-r1` | already released runtime |
| `kai-agent` | `0.0.23-r1` | `0.0.23-r1` | already released runtime |
| `kai_session` | `0.0.23-r1` | `0.0.23-r1` | already released runtime |
| `luci-app-kai` | `1.0.2-r1` | `1.0.2-r2` | LuCI packaging |
| `app-meta-kai` | `1.0.2-r2` | `1.0.2-r3` | expose the complete KAI runtime dependency set |

## Routed application packages

| Package | Baseline | Target |
| --- | --- | --- |
| `dockermanager` | `0.1.1-r1` | `0.1.1-r2` |
| `luci-app-dockermanager` | `0.1.1-r1` | `0.1.1-r2` |
| `app-meta-dockermanager` | `0.1.1-r2` | `0.1.1-r3` |
| `baidudrive` | `1.0.6-r1` | `1.0.6-r2` |
| `luci-app-baidudrive` | `1.0.2-r1` | `1.0.2-r2` |
| `app-meta-baidudrive` | `1.0.6-r1` | `1.0.6-r2` |
| `kaiplus` | `1.0.9-r1` | `1.0.9-r2` |
| `luci-app-kaiplus` | `1.0.9-r1` | `1.0.9-r2` |
| `agentflow` | `0.3.0-r10` | `0.3.0-r11` |
| `luci-app-agentflow` | `1.0.0-r7` | `1.0.0-r8` |
| `app-meta-agentflow` | `0.3.0-r1` | `0.3.0-r2` |
| `fastnet` | `0.7.7-r2` | `0.7.7-r3` |
| `luci-app-fastnet` | `0.7.7-r2` | `0.7.7-r3` |
| `app-meta-fastnet` | `0.7.7-r2` | `0.7.7-r3` |
| `istoreenhance` | `0.8.0-r2` | `0.8.0-r3` |
| `luci-app-istoreenhance` | `0.8.0-r1` | `0.8.0-r2` |
| `app-meta-istoreenhance` | `0.8.0-r3` | `0.8.0-r4` |

KSpeeder is delivered by the `istoreenhance` package family and has no
independent OpenWrt package in this repository.

## Product composition invariants

- `app-meta-linkeasefull` does not depend on business application meta packages.
- `app-meta-istorex` remains the iStoreNAS aggregate and depends on KAI, not
  KaiPlus metadata.
- Routed applications depend on `linkease-app-entry` and can run without
  LinkEaseFull.
- `linkease-app-entry` depends on `luci-lib-linkeaseauth`; the authentication
  library does not depend back on the entry runtime or LinkEaseFull.
- `app-meta-kaiplus` and the legacy `apps/linkeaseauth` package stay removed.

## Manual OpenWrt build gate

The OpenWrt App Actions build is intentionally operated by the maintainer. Run
the `Build IPKs` workflow for both `x64` and `arm64` with these application
directories after the App Hub commit is available remotely:

```text
linkeasefull kai dockermanager baidudrive kaiplus agentflow fastnet istoreenhance istorex
```

The build is accepted when dependency resolution succeeds for both targets and
all produced package versions match this ledger. Do not substitute a successful
runtime-tarball build for this IPK build gate.
