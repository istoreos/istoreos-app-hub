#!/bin/sh
set -eu

root="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)"
archive="${1:?usage: test-agent-bundle-staging.sh ARCHIVE EXPECTED_SKILLS_COMMIT}"
expected_commit="${2:?expected kai-skills commit is required}"
version="$(sed -n 's/^PKG_VERSION:=//p' "$root/kai-agent/Makefile")"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/kai-agent-staging.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/sdk/include" "$scratch/build" "$scratch/install"
: > "$scratch/sdk/rules.mk"
: > "$scratch/sdk/include/package.mk"
tar -xzf "$archive" -C "$scratch/build"

# Execute the real OpenWrt install recipe with a minimal SDK macro environment.
# This checks the shipped file tree, rather than duplicating its copy commands.
cat > "$scratch/stage.mk" <<'MAKE'
include $(KAI_AGENT_MAKEFILE)
.PHONY: stage
stage:
	$(call Package/kai-agent/install,$(STAGING_ROOT))
MAKE
make --no-print-directory -f "$scratch/stage.mk" stage \
  TOPDIR="$scratch/sdk" INCLUDE_DIR="$scratch/sdk/include" \
  BUILD_DIR="$scratch/build" STAGING_ROOT="$scratch/install" \
  KAI_AGENT_MAKEFILE="$root/kai-agent/Makefile" \
  'INSTALL_DIR=mkdir -p' 'CP=cp -a' 'INSTALL_DATA=install -m 0644' 'LN=ln -sf'

source="$scratch/build/kai-agent-bundle-$version"
installed="$scratch/install/usr/share/kai/agent-bundles/$version"
test "$(readlink "$scratch/install/usr/share/kai/agent")" = "agent-bundles/$version"
diff -ru "$source/skills" "$installed/skills" >/dev/null
diff -ru "$source/agents" "$installed/agents" >/dev/null
for file in manifest.json opencode.json home-prompts.json; do
  cmp "$source/$file" "$installed/$file"
done
jq -e --arg version "$version" --arg commit "$expected_commit" \
  '.version == $version and .sourceCommit == $commit and .consumer == "opencode" and (.skills | length > 0)' \
  "$installed/manifest.json" >/dev/null
jq -e '.skills.paths == ["/usr/share/kai/agent/skills"] and .skills.urls == null' \
  "$installed/opencode.json" >/dev/null
count="$(find -L "$installed/skills" -type f -name SKILL.md | wc -l | tr -d ' ')"
test "$count" -gt 0
printf 'KAI packaged skills staging: PASS (version=%s skills=%s source=%s)\n' "$version" "$count" "$expected_commit"
