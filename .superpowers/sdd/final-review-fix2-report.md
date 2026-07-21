# LinkEaseLite Tarball Unpack Layout Fix

## RED

Added a contract assertion requiring:

`TAR_CMD=$(HOST_TAR) -C $(PKG_BUILD_DIR) $(TAR_OPTIONS)`

Before the Makefile change, the focused test failed with:

`AssertionError: 'TAR_CMD=$(HOST_TAR) -C $(PKG_BUILD_DIR) $(TAR_OPTIONS)' not found`

Command:

`rtk python3 -m unittest apps.linkeaselite.tests.test_linkeaselite_contract.LinkEaseLiteContractTest.test_runtime_makefile_installs_lite_binary_contract`

## GREEN

Added the `TAR_CMD` assignment near the package build settings, matching the existing `webdav2` pattern.

Focused contract test: 1 test passed.

Full suite command:

`rtk python3 -m unittest discover apps/linkeaselite/tests`

Result: 12 tests passed.

## Artifact Verification

The local tarball contains the expected root-level members:

- `./linkease-lite.arm`
- `./linkease-lite.x86_64`
- `./linkease-lite.aarch64`

These match the Makefile install source `$(PKG_BUILD_DIR)/linkease-lite.$(ARCH)` after extraction into `$(PKG_BUILD_DIR)`.

SHA-256 remains:

`db0811ee189f859b4c8a434338697a57cd2d40d6162b955d3acd3f6b8aee442c`

The GitHub release publication/URL availability remains an external concern; `PKG_SOURCE_URL` was not changed.
