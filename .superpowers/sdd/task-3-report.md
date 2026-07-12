# Task 3 Report: LinkEase Decoupling Contract Tests

## Changes

- Updated `apps/linkease/tests/test_linkease_full_contract.py` to reject embedded KaiPlus packaging.
- Added desktop assertions requiring disabled embedded KaiPlus configuration and a standalone-plugin proxy target.
- Added assertions requiring proxy target resolution from `/etc/init.d/kaiplus` and UCI port configuration.

## Verification

Command:

```text
rtk python3 -m unittest discover apps/linkease/tests
```

Result: expected failure, 3 failing tests and 3 passing tests. Failures are caused by the current LinkEase `Makefile` copying KaiPlus, `linkease.init` setting embedded KaiPlus environment variables, and the missing standalone proxy helper. No unrelated production files were changed.

`git show --check` passed for the committed change.

## Commit

`e0d2232 test: define linkease standalone kaiplus proxy contract`

## Concerns

The worktree contains unrelated untracked `apps/kaiplus/tests/__pycache__/` and `apps/linkease/tests/__pycache__/` directories; they were left untouched.

## Review Fixes

- Renamed the proxy test to clarify that startup configuration is covered.
- Added a regex requiring `read_config()` to call `resolve_kaiplus_proxy_target` after deriving `data_root` and `recycle_root`.
- Added explicit assertions preserving `option desktop_base_path '/apps/'`, `SERVER_BASE_PATH=$desktop_base_path`, and rejecting `KAIPLUS_BASE_PATH=` from the desktop procd block.

## Review Fix Verification

Command:

```text
rtk python3 -m unittest discover apps/linkease/tests
```

Result: expected failure, 3 failing tests and 3 passing tests. Failures remain the expected Task 4 production gaps: the Makefile still copies KaiPlus, the desktop procd block still configures embedded KaiPlus, and `read_config()` lacks the standalone proxy resolver call.
