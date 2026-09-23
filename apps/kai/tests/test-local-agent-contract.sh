#!/bin/sh
set -eu

root="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)"
hub_root="$(CDPATH= cd -- "$root/../.." && pwd -P)"
init="$root/kai/files/kai.init"
launcher="$root/kai/files/kai-session-launch"
status_view="$root/luci-app-kai/luasrc/view/kai/kai_status.htm"
meta_makefile="$root/app-meta-kai/Makefile"

fail() {
	echo "failed: $*" >&2
	exit 1
}

grep -F 'OPENCODE_CONFIG="${agent_root}/opencode.json"' "$init" >/dev/null ||
	fail "init does not use local OPENCODE_CONFIG"
grep -F 'KAIPLUS_SKILLS_DIR="${agent_root}/skills"' "$init" >/dev/null ||
	fail "init does not expose the local skills root"
grep -F 'KAI_AUTH_MODE="$auth_mode"' "$init" >/dev/null ||
	fail "init does not enable the OpenWrt auth middleware"
grep -F "option 'auth_mode' 'openwrt_luci'" "$root/kai/files/kai.config" >/dev/null ||
	fail "kai does not default to LuCI authentication"
grep -F '+luci-lib-linkeaseauth' "$root/kai/Makefile" >/dev/null ||
	fail "kai does not depend on the shared auth bridge"
if grep -E 'OPENCODE_CWD|/agentconf/(opencode|skills)' "$init" >/dev/null; then
	fail "init still depends on the legacy HTTP/cwd contract"
fi
grep -F 'cd "$1"' "$launcher" >/dev/null || fail "launcher does not set the process cwd"
grep -F 'exec /usr/sbin/kai_session serve --port 8196 --hostname 127.0.0.1' "$launcher" >/dev/null ||
	fail "launcher command differs from the runtime contract"
grep -F 'DEPENDS:=+kai_session +kai-agent' "$root/kai/Makefile" >/dev/null ||
	fail "kai does not depend on its runtime artifacts"
test -f "$root/kai-agent/Makefile" ||
	fail "kai-agent package directory does not match its package name"
grep -F 'META_DEPENDS:=+luci-app-kai +kai +kai_session +kai-agent' "$meta_makefile" >/dev/null ||
	fail "app-meta-kai does not expose the complete runtime dependency set"
grep -F 'local: apps/kai/kai-agent' "$hub_root/syncapps.yaml" >/dev/null ||
	fail "syncapps does not publish kai-agent to the package feed"
if grep -F '$(CP) $(PKG_BUILD_DIR)/*' "$root/kai-agent/Makefile" >/dev/null; then
	fail "kai-agent recursively copies OpenWrt package staging directories"
fi
grep -F '$(CP) $(PKG_BUILD_DIR)/agents' "$root/kai-agent/Makefile" >/dev/null ||
	fail "kai-agent does not explicitly install its agents directory"
grep -F '$(CP) $(PKG_BUILD_DIR)/skills' "$root/kai-agent/Makefile" >/dev/null ||
	fail "kai-agent does not explicitly install its skills directory"
grep -F '$(PKG_BUILD_DIR)/rg.$(PKG_ARCH_kai_session)' "$root/kai_session/Makefile" >/dev/null ||
	fail "kai_session does not install its bundled ripgrep runtime"
if grep -F 'if [ -f "$(PKG_BUILD_DIR)/rg.' "$root/kai_session/Makefile" >/dev/null; then
	fail "kai_session still treats ripgrep as optional"
fi
for package in kai kai_session kai-agent; do
	makefile="$root/$package/Makefile"
	grep -F 'PKG_VERSION:=0.0.23' "$makefile" >/dev/null ||
		fail "$package does not use the unified KAI runtime version"
	grep -F 'https://github.com/istoreos/istoreos-app-hub/releases/download/kai-runtime-v$(PKG_VERSION)/' "$makefile" >/dev/null ||
		fail "$package does not use the iStoreOS KAI runtime release"
done
grep -F '/apps/kai/web/' "$status_view" >/dev/null ||
	fail "LuCI does not open the mounted KAI web path"

echo "KAI local Agent runtime contract: PASS"
