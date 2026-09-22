#!/bin/sh
set -eu

root="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)"
init="$root/kai/files/kai.init"
launcher="$root/kai/files/kai-session-launch"
status_view="$root/luci-app-kai/luasrc/view/kai/kai_status.htm"

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
grep -F '$(PKG_BUILD_DIR)/rg.$(PKG_ARCH_kai_session)' "$root/kai_session/Makefile" >/dev/null ||
	fail "kai_session does not install its bundled ripgrep runtime"
grep -F '/apps/kai/web/' "$status_view" >/dev/null ||
	fail "LuCI does not open the mounted KAI web path"

echo "KAI local Agent runtime contract: PASS"
