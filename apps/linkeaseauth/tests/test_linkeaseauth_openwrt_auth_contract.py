from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LinkEaseAuthOpenWrtContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_package_is_independent_luci_auth_bridge(self):
        makefile = self.read("luci-lib-linkeaseauth/Makefile")
        controller = self.read("luci-lib-linkeaseauth/luasrc/controller/linkease_auth.lua")

        self.assertIn("LUCI_TITLE:=LuCI shared integration for LinkEase apps", makefile)
        self.assertNotIn("luci-lib-openwrtauth", makefile)
        self.assertNotIn("+linkeasefull", makefile)
        self.assertNotIn("+luci-app-linkeasefull", makefile)
        self.assertIn('entry({"admin", "services", "linkease_auth", "auth"}, call("linkease_auth"))', controller)
        self.assertIn('entry({"admin", "services", "linkease_auth", "auth_finish"}, call("linkease_auth_finish"))', controller)

    def test_auth_begin_is_public_and_finish_is_protected(self):
        controller = self.read("luci-lib-linkeaseauth/luasrc/controller/linkease_auth.lua")

        auth_start = controller.index('local auth = entry({"admin", "services", "linkease_auth", "auth"}')
        auth_finish = controller.index('local auth_finish = entry({"admin", "services", "linkease_auth", "auth_finish"}')
        self.assertIn("auth.sysauth = false", controller[auth_start:auth_finish])
        self.assertNotIn("sysauth_authenticator", controller[auth_start:auth_finish])
        self.assertIn('auth_finish.sysauth = "root"', controller)
        self.assertIn('auth_finish.sysauth_authenticator = "htmlauth"', controller)
        self.assertIn("function linkease_auth_finish(state)", controller)
        self.assertIn("bridge():auth_finish(state)", controller)

    def test_path_state_preserves_return_and_cookie_remains_compatibility_fallback(self):
        model = self.read("luci-lib-linkeaseauth/luasrc/model/linkease/auth.lua")

        self.assertIn('local pending_return_cookie = "linkease_openwrt_pending_return"', model)
        self.assertIn('local bridge_return_cookie = "linkease_openwrt_return"', model)
        self.assertIn('Max-Age=300; HttpOnly; SameSite=Lax', model)
        self.assertIn("local function encode_state(value)", model)
        self.assertIn("local function decode_state(value)", model)
        self.assertIn('build_url("admin", "services", "linkease_auth", "auth_finish", state)', model)
        self.assertIn("function Bridge:auth_finish(state)", model)
        self.assertIn("target = self:safe_return_target(decoded)", model)
        self.assertIn("target = self:pending_return_target()", model)

    def test_finish_route_sets_apps_cookie_and_redirects_sanitized_return(self):
        model = self.read("luci-lib-linkeaseauth/luasrc/model/linkease/auth.lua")

        finish = model[model.index("function Bridge:auth_finish(state)") :]
        self.assertIn('local sid = self:retrieve_luci_session()', finish)
        self.assertIn('if not valid_cookie_value(sid) then', finish)
        self.assertIn('target = self:pending_return_target()', finish)
        self.assertIn('Max-Age=0; HttpOnly; SameSite=Lax', finish)
        self.assertIn('"linkease_openwrt_sid=" .. sid .. "; Path=/apps; HttpOnly; SameSite=Lax"', finish)
        self.assertIn('http.redirect(target)', finish)

    def test_return_validation_stays_limited_to_apps_paths_and_same_host(self):
        model = self.read("luci-lib-linkeaseauth/luasrc/model/linkease/auth.lua")

        self.assertIn("function Bridge:valid_apps_return(value)", model)
        self.assertIn('path == "/apps"', model)
        self.assertIn('prefix == "/apps/" or prefix == "/apps?" or prefix == "/apps#"', model)
        self.assertIn('value:match("^(https?://)([^/]+)(/.*)$")', model)
        self.assertIn('http.getenv("HTTP_X_FORWARDED_HOST")', model)
        self.assertIn('http.getenv("HTTP_X_FORWARDED_PROTO")', model)
        self.assertIn("authority_host(self:request_authority())", model)
        self.assertIn("authority_host(self.dependencies.lan_ip())", model)
        self.assertIn('value:find("[%z\\1-\\31\\127]")', model)
        self.assertNotIn('request_host .. ":19290"', model)

    def test_absolute_apps_return_allows_same_device_dynamic_port(self):
        model = self.read("luci-lib-linkeaseauth/luasrc/model/linkease/auth.lua")

        self.assertIn('local candidate = authority_host(authority)', model)
        self.assertIn('candidate == authority_host(self:request_authority())', model)
        self.assertIn('candidate == authority_host(self.dependencies.lan_ip())', model)
        self.assertNotIn('authority == self:request_authority()', model)


if __name__ == "__main__":
    unittest.main()
