# KAI OpenWrt packaging notes

## `kai_session` must bundle ripgrep

OpenCode's native `skill` tool invokes ripgrep while enumerating files next to
`SKILL.md`. When `rg` is missing, OpenCode tries to download it from GitHub at
runtime. An iStoreOS router may not have GitHub connectivity, in which case
skill loading fails with:

```text
ripgrep execution failed
```

`kai_session` therefore has an offline runtime contract:

- The prebuilt `kai_session-binary-<version>.tar.gz` contains both
  `kai_session.<arch>` and the static `rg.<arch>` binary.
- `kai_session/Makefile` installs the matching binary as `/usr/sbin/rg`.
- Runtime archives are published under the matching
  `kai-runtime-v<version>` release in `istoreos/istoreos-app-hub`.
- A package update must publish the new prebuilt archives first, then update
  `PKG_VERSION` and `PKG_HASH` together for `kai`, `kai_session`, and
  `kai-agent`.
- Run `./tests/test-local-agent-contract.sh` before committing the plugin.
- On a target device, verify both `/usr/sbin/rg --version` and a real skill
  directory scan. Merely listing available skills does not exercise ripgrep.

Keep this dependency in the release artifact and OpenWrt package. Installation
is intentionally unconditional so a missing architecture-specific `rg` fails
the package build instead of falling back to a first-run network download.

## HTTP mount contract

The LuCI entry opens the stable `/apps/kai/` root, which KAI redirects to
`/apps/kai/web/`. Browser traffic stays below `/apps/kai/`, including
`/apps/kai/event`, `/apps/kai/session/*` and product
APIs. Keep the plugin entry path aligned with the server mount when either side
changes.
