#!/bin/sh
set -eu

root="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)"
hub_root="$(CDPATH= cd -- "$root/../.." && pwd -P)"
init="$root/kai/files/kai.init"
launcher="$root/kai/files/kai-session-launch"
status_view="$root/luci-app-kai/luasrc/view/kai/kai_status.htm"
status_controller="$root/luci-app-kai/luasrc/controller/kai.lua"
luci_makefile="$root/luci-app-kai/Makefile"
meta_makefile="$root/app-meta-kai/Makefile"
meta_entry="$root/app-meta-kai/entry.sh"

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
if grep -E '^[[:space:]]*sleep[[:space:]]' "$init" >/dev/null; then
	fail "init uses a fixed sleep instead of runtime readiness"
fi
respawn_policy_count="$(grep -F -c 'procd_set_param respawn 3600 5 5' "$init" || true)"
[ "$respawn_policy_count" -eq 2 ] ||
	fail "init does not explicitly apply the bounded 3600/5/5 respawn policy to both processes"
session_start_line="$(grep -n '^[[:space:]]*start_kai_session || return 1' "$init" | cut -d: -f1)"
gateway_start_line="$(grep -n '^[[:space:]]*start_kai_bin$' "$init" | cut -d: -f1)"
cwd_create_line="$(grep -n '^[[:space:]]*mkdir_cwd "${data_dir}/cwd"' "$init" | cut -d: -f1)"
[ -n "$session_start_line" ] && [ -n "$gateway_start_line" ] && [ "$session_start_line" -lt "$gateway_start_line" ] ||
	fail "init does not start kai_session before kai_bin"
[ -n "$cwd_create_line" ] && [ "$cwd_create_line" -lt "$session_start_line" ] ||
	fail "init does not create runtime directories before starting processes"
grep -F 'cd "$1"' "$launcher" >/dev/null || fail "launcher does not set the process cwd"
grep -F 'exec /usr/sbin/kai_session serve --port 8196 --hostname 127.0.0.1' "$launcher" >/dev/null ||
	fail "launcher command differs from the runtime contract"
grep -F 'DEPENDS:=+kai_session +kai-agent' "$root/kai/Makefile" >/dev/null ||
	fail "kai does not depend on its runtime artifacts"
test -f "$root/kai-agent/Makefile" ||
	fail "kai-agent package directory does not match its package name"
grep -F 'META_DEPENDS:=+luci-app-kai +kai +kai_session +kai-agent' "$meta_makefile" >/dev/null ||
	fail "app-meta-kai does not expose the complete runtime dependency set"
grep -F 'json_add_string "href" "/cgi-bin/luci/admin/services/kai"' "$meta_entry" >/dev/null ||
	fail "app-meta-kai does not enter KAI through its LuCI page"
if grep -F 'json_add_string "href" "http://$host:' "$meta_entry" >/dev/null; then
	fail "app-meta-kai bypasses the LuCI authentication entry"
fi
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
	grep -F 'PKG_VERSION:=0.0.25' "$makefile" >/dev/null ||
		fail "$package does not use the unified KAI runtime version"
	grep -F 'https://github.com/istoreos/istoreos-app-hub/releases/download/kai-runtime-v$(PKG_VERSION)/' "$makefile" >/dev/null ||
		fail "$package does not use the iStoreOS KAI runtime release"
done
grep -F 'url("admin/services/linkease_apps/open")' "$status_view" >/dev/null ||
	fail "LuCI KAI launcher does not use the shared apps entry"
grep -F '?id=kai' "$status_view" >/dev/null ||
	fail "LuCI KAI launcher does not select the KAI app"
if grep -E 'linkease_auth/auth|openKai|/apps/kai/web/' "$status_view" >/dev/null; then
	fail "LuCI KAI launcher bypasses shared route resolution"
fi
grep -F 'uci:get_first("kai", "kai", "port")' "$status_controller" >/dev/null ||
	fail "LuCI KAI status does not report the configured KAI port"
grep -F '+luci-lib-linkeaseauth' "$luci_makefile" >/dev/null ||
	fail "luci-app-kai does not directly depend on its auth bridge"
grep -F '+linkease-app-entry' "$luci_makefile" >/dev/null ||
	fail "luci-app-kai does not directly depend on the shared app entry"

echo "KAI local Agent runtime contract: PASS"
