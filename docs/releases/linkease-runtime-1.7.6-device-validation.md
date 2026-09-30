# LinkEase 1.7.6 Device Migration Validation

Status: migration behavior accepted; final source-date artifact verified offline  
Validated: 2026-09-30 UTC

## Device and Recovery Points

The migration was exercised on `root@192.168.30.244`, an x86_64 iStoreOS
24.10.1 device. Its starting package was the legacy monolithic
`linkease 1.7.0~8664-r4`.

The pre-install state and logs remain available on the device at:

```text
/tmp/linkease176-m7-backup-20260930
/tmp/linkease176-m8-backup-20260930
```

## Direct Runtime Migration

The accepted x86_64 `linkease-common-bin` and `linkease` IPKs were supplied to
one `opkg install` transaction. A preceding `--noaction` transaction succeeded.
Neither transaction used a force option.

The real transaction:

- installed `linkease-common-bin 1.7.6-8664-r1`;
- upgraded `linkease` from `1.7.0~8664-r4` to `1.7.6-8664-r1`;
- emitted no `check_data_file_clashes` or package-install failure;
- removed the now-orphaned legacy `linkmount` dependency.

The complete direct-install log is retained as
`/tmp/linkease176-m7-backup-20260930/install.log`.

This first end-to-end transaction used the earlier hyphenated validation
candidate. After restoring the required source-date-only versioning convention,
the final `1.7.6~8664-r1` packages were checked against the saved legacy package
database with an isolated `opkg --offline-root --noaction` transaction. It
selected the same install/upgrade path and emitted no data-file clash. Evidence
is retained at `/tmp/linkease176-source-date-offline/noaction.log`.

## Actual is-opkg Entry-Point Transactions

A temporary local candidate feed was added to the isolated `/tmp/is-root`
configuration. These real commands both completed successfully:

```text
is-opkg install app-meta-linkease
is-opkg install app-meta-linkeasefull
```

The first command upgraded the previously installed LuCI package and installed
the transition contract. The second installed the Full runtime and its meta
package. Neither log contains `check_data_file_clashes`, `Collected errors`,
`Unknown package`, `Cannot install`, or a force-overwrite path. Logs are kept at:

```text
/tmp/linkease176-m8-backup-20260930/is-opkg-linkease-opt2.log
/tmp/linkease176-m8-backup-20260930/is-opkg-linkeasefull-opt2.log
```

The temporary feed configuration and package-list entry were removed after the
test, while the earlier validation packages were retained. The live device was
not force-downgraded from the hyphenated candidate to the final tilde-form
package solely to refresh evidence.

## Final Installed State

| Package | Installed version |
| --- | --- |
| `app-meta-linkease` | `3.0.0-r3` |
| `app-meta-linkeasefull` | `3.0.22-r3` |
| `linkease-runtime-transition` | `1.7.6-r1` |
| `linkease` | `1.7.6-8664-r1` |
| `linkease-common-bin` | `1.7.6-8664-r1` |
| `linkeasefull` | `3.0.22-8664-r2` |
| `luci-app-linkease` | `2.1.70-r4` |
| `luci-lib-linkeasefile` | `2.1.70-r4` |

`apps/linkease/tests/check_linkease_split_migration.sh` passed. The three
historically conflicting runtime files are owned exclusively by
`linkease-common-bin`; the LinkEase file UI is owned by
`luci-lib-linkeasefile`, with no stale overlap from the upgraded app package.
The transition marker contains `1.7.6`.

The original user-controlled values, `enabled=1` and `port=8897`, were
preserved. The idempotent migration added only the safe `allowPublic=0`
default. At final validation the standard service was running on port 8897,
the Full application entry was listening locally on port 19290, and both init
services remained enabled.
