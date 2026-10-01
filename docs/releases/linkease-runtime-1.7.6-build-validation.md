# LinkEase 1.7.6 Build Validation

Status: accepted for manual release  
Validated: 2026-09-30 UTC

## Scope and Runtime Inputs

The OpenWrt packages were built from the final 1.7.6 migration metadata for all
supported architectures. The LinkEase and LinkEase Full business binaries were
not rebuilt. While the manual GitHub upload is pending, the builds use the
byte-identical 1.7.5 LinkEase runtime archives documented in
`linkease-runtime-1.7.6-migration-baseline.md` under their future 1.7.6 names.

Builder runtime release: `runtime-linkease-176-source-date-fix-20260930`

## Accepted Builds

| Architecture | Build ID | Official OpenWrt 24.10.1 SDK SHA256 |
| --- | --- | --- |
| x86_64 | `linkease-176-x64-source-date-fix-20260930` | `ff013b90ea4912c2c9fd55aef6b399fedf2bb3e1d702a3e62ef17afcafdab221` |
| aarch64_generic | `linkease-176-arm64-source-date-fix-20260930` | `d24322d462c7ab056e06f71642a5a02935be6798d01f71e65f0750556beaf656` |
| arm_cortex-a7_neon-vfpv4 | `linkease-176-arm-source-date-fix-20260930` | `012c2148cc8fe098813f9185be9bae73f91b63f5b4ab6832d02454f81dad076e` |

All builds used these pinned feeds:

| Feed | Commit |
| --- | --- |
| OpenWrt base | `97f7026b3dc97aff135da1ef3575c44cddcf8fb5` |
| LuCI | `2ac26e56cc55102cb10e7b0867c2b78e0f6d5fd8` |
| nas-packages | `ecd9c7ede3a39ae3f2e49716bea1d325585481ac` |
| nas-packages-luci | `29373c7a27a952cd8906e249edc964256db31248` |
| openwrt-app-meta | `6a8627e0e6fa79aaebdfa53fbbb7dc741eec9367` |
| istore | `a97ace34f2da358a015b094d326bba2697697f2e` |

## Final Package Contract

`apps/linkease/tests/check_linkease_ipks.sh` passed against all three artifact
directories. It verified:

- the three runtime Makefiles retain the established `PKG_SOURCE_DATE`-only
  versioning contract and do not assign `PKG_VERSION`;
- `linkease-common-bin` is `1.7.6~<variant>-r1`, has
  `Replaces: linkease (<< 1.7.6~)`, and has no transition-blocking `Conflicts`;
- `linkease` is `1.7.6~<variant>-r1` and requires
  `linkease-common-bin (>=1.7.6~)`;
- `linkeasefull` is `3.0.22~<variant>-r2` and requires
  `linkease-common-bin (>=1.7.6~)` where that product supports the architecture;
- `luci-lib-linkeasefile 2.1.70-r4` replaces
  `luci-app-linkease (<< 2.1.70-r4)`, while `luci-app-linkease 2.1.70-r4`
  requires the new library generation;
- `linkease-runtime-transition 1.7.6-r1` carries the versioned runtime and LuCI
  migration requirements;
- `app-meta-linkease 3.0.0-r3` and `app-meta-linkeasefull 3.0.22-r3` depend on
  the transition package using only unversioned direct dependencies, avoiding
  the `is-opkg` meta-hook parser limitation;
- only `linkease-common-bin` contains `/usr/sbin/heif-converter`,
  `/usr/sbin/linkease-config.sh`, and `/usr/sbin/linkease-media`.

The reproducing device accepted both relevant version comparisons:

```text
1.7.6~8664-r1 >= 1.7.6~
1.7.6~8664-r1 >> 1.7.5-8664-r8
1.7.0~8664-r4 << 1.7.6~
```

## x86_64 Device-Test Artifact Checksums

| Package | SHA256 |
| --- | --- |
| `app-meta-linkease_3.0.0-r3_all.ipk` | `11a523ac378df350875b4e1423d9adb8873fb025533de8cb9d2e2c854cf19719` |
| `app-meta-linkeasefull_3.0.22-r3_all.ipk` | `3a3572a994feffbc7c033f81a1320a28e341bdfcd0fbc9e9cfdf7233934c6490` |
| `linkease-common-bin_1.7.6~8664-r1_all.ipk` | `0e47571a2513e88fbe1bce0e3180271110ea6b704e14cbb2276741ae7f65f92b` |
| `linkease-runtime-transition_1.7.6-r1_all.ipk` | `4dca7d1d7bb773d5b2f73b70745b098b715d9c13be9c674eea04c1fb266ee04c` |
| `linkease_1.7.6~8664-r1_all.ipk` | `3acf913a87328535067e03b4f521f17a218c5a6cc68c4795391758b6a5293ef6` |
| `linkeasefull_3.0.22~8664-r2_all.ipk` | `8729243606c8e6fea725602c3d378dd4c407d99b975f02014132111648e36ac1` |
| `luci-app-linkease_2.1.70-r4_all.ipk` | `2d1930267ea5d233c1f673902cc925b2e5ffaa1464af5010faf29c70c18df2fe` |
| `luci-lib-linkeasefile_2.1.70-r4_all.ipk` | `3bff7bcd1c1c57dd7c1b636ada61691e27c5de80cdbe603e0500f0338d69c633` |

The build artifacts are validation outputs, not published release assets.
Publishing the renamed 1.7.6 runtime archives remains an explicit manual step.
