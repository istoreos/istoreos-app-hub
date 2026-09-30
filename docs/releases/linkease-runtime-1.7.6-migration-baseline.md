# LinkEase 1.7.6 Package-Split Migration Baseline

Status: baseline frozen  
Captured: 2026-09-30 UTC

## Scope

This release changes package metadata and runtime asset names without rebuilding
the LinkEase business binaries. It migrates ownership of the shared binaries
from legacy `linkease` packages to `linkease-common-bin` and makes both LinkEase
app meta packages require the split-safe LinkEase generation.

Baseline repositories:

- `istoreos-app-hub`: `9aab90a165d1fe1d9cb95ebbd333a19267dd7af6`
- `linkease-desktop`: `26784981953a0cf394b4e26aebf3e19e1aebe40c`

## Standard Runtime Baseline

Release: `linkease-runtime-v1.7.5`

| Asset | Size | SHA256 |
| --- | ---: | --- |
| `linkease-bin-1.7.5-linux-x86_64.tar.gz` | 14386683 | `634d3e1a807119badf98ae58f3e6e9815dacc22a5be31080228998ee0de6addd` |
| `linkease-bin-1.7.5-linux-aarch64.tar.gz` | 13350769 | `92d0c6f9d05a0ba283d03fef2b7f4675eee032c303e959b1e4198e12806510f9` |
| `linkease-bin-1.7.5-linux-arm.tar.gz` | 12466766 | `2a91f404c3eb190a8a828b5e41913595901de54664de518f0430c5544d71a914` |
| `linkease-common-bin-1.7.5-linux-x86_64.tar.gz` | 2901917 | `fffcabac6072feeb460aef0a31d395acf245b78ae2f5af6abd59411a1757935a` |
| `linkease-common-bin-1.7.5-linux-aarch64.tar.gz` | 2811998 | `1646db48f5a512b96a34971e5af82eacd5a51f32abab2c5e84f277c408a72eb8` |
| `linkease-common-bin-1.7.5-linux-arm.tar.gz` | 2808134 | `61f970245e1ae9783bc58280929e134fb0c94f5fc4e0e9a3deea117846b81e40` |

The business binaries in the 1.7.6 assets must be byte-for-byte copies of the
files in these archives. The archives themselves are repacked so their sole
top-level directories match the 1.7.6 source names expected by OpenWrt.

## Repacked 1.7.6 Runtime Assets

Release: `linkease-runtime-v1.7.6`

| Asset | Size | SHA256 |
| --- | ---: | --- |
| `linkease-bin-1.7.6-linux-x86_64.tar.gz` | 14386683 | `2beab45ffd519f19e7dce62bbb06a4ddf63919e2ed69b1f8b4333134efbab03c` |
| `linkease-bin-1.7.6-linux-aarch64.tar.gz` | 13350771 | `129bd623e2eac350365d3687011221bef0d3d6ab0471f9355b050edd07f4eee8` |
| `linkease-bin-1.7.6-linux-arm.tar.gz` | 12466766 | `28016a6d7d600dd98f6ca784591f1acf4cbac015bcbc8038cd75c4195f70c30a` |
| `linkease-common-bin-1.7.6-linux-x86_64.tar.gz` | 2901906 | `608806ab0b2983c3abb9c55783673d74533fd56783327354faa246192909a78c` |
| `linkease-common-bin-1.7.6-linux-aarch64.tar.gz` | 2812006 | `90cc7b43ca881dd6938892b1bb95f8ea55f2b221a44693cdf5875075c0e540c5` |
| `linkease-common-bin-1.7.6-linux-arm.tar.gz` | 2808133 | `58ef68817e34365f749b8e0a684baaffdab80fc8e7ae7293a052a0f0c0715903` |

## LinkEase Full Runtime Baseline

Release: `linkeasefull-runtime-v3.0.22`

| Asset | Size | SHA256 |
| --- | ---: | --- |
| `linkease-runtime-3.0.22-linux-amd64.tar.gz` | 87202796 | `462f7d4b9500725094d2cacc388a109201f4b6b8eec5f90de68f756447644c70` |
| `linkease-runtime-3.0.22-linux-arm64.tar.gz` | 83568633 | `4dc7c1b4861115042141b02a5822994ede6fb6e2686f1e1dd6f1c213ec44c00c` |

The Full runtime remains 3.0.22. Only its OpenWrt package release and dependency
metadata may change.

## Reproducing Device

Device: `root@192.168.30.244`  
Distribution: iStoreOS 24.10.1

Installed package:

```text
Package: linkease
Version: 1.7.0~8664-r4
Depends: libc, linkmount
Status: install ok installed
Architecture: all
```

Available split packages before this migration:

```text
linkease             1.7.5-8664-8
linkease-common-bin  1.7.5-8664-5
```

The installed legacy `linkease` package owns all three paths that the current
`linkease-common-bin` package tries to install:

```text
/usr/sbin/heif-converter
/usr/sbin/linkease-config.sh
/usr/sbin/linkease-media
```

Neither available meta package forces a minimum LinkEase version, and the
available common package has no `Replaces` field. Installing either app meta
package therefore reaches `check_data_file_clashes` before the legacy package
has relinquished those paths.

## Red/Green Feedback Loop

Run:

```sh
apps/linkease/tests/check_linkease_split_migration.sh root@192.168.30.244
```

Baseline verdict: **RED**.

The check becomes green only after the device has all of the following:

- installed `linkease >= 1.7.6~`;
- installed `linkease-common-bin >= 1.7.6~`;
- `Replaces: linkease (<< 1.7.6~)` in the installed common package control;
- exclusive `linkease-common-bin` ownership of the three shared paths.
