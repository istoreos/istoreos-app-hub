from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LinkEaseAuthOpenWrtContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_package_is_independent_luci_auth_bridge(self):
        makefile = self.read("luci-lib-linkeaseauth/Makefile")
        controller = self.read("luci-lib-linkeaseauth/luasrc/controller/linkease_auth.lua")

        self.assertIn("LUCI_TITLE:=LuCI shared OpenWrt auth bridge for LinkEase apps", makefile)
        self.assertNotIn("+linkeasefull", makefile)
        self.assertNotIn("+luci-app-linkeasefull", makefile)
        self.assertIn('entry({"admin", "services", "linkease_auth", "auth"}, call("linkease_auth"))', controller)
        self.assertIn('entry({"admin", "services", "linkease_auth", "auth_finish"}, call("linkease_auth_finish"))', controller)

    def test_auth_bridge_defers_missing_luci_session_to_finish_route(self):
        controller = self.read("luci-lib-linkeaseauth/luasrc/controller/linkease_auth.lua")

        self.assertIn('auth_finish.sysauth = "root"', controller)
        self.assertIn('auth_finish.sysauth_authenticator = "htmlauth"', controller)
        self.assertIn('set_pending_return_cookie(target)', controller)
        self.assertIn('http.redirect(auth_finish_url())', controller)

        auth_start = controller.index("function linkease_auth()")
        auth_finish = controller.index("function linkease_auth_finish()")
        self.assertNotIn('http.status(403, "Forbidden")', controller[auth_start:auth_finish])

    def test_pending_return_cookie_preserves_hash_route_across_luci_login(self):
        controller = self.read("luci-lib-linkeaseauth/luasrc/controller/linkease_auth.lua")

        self.assertIn('local pending_return_cookie = "linkease_openwrt_pending_return"', controller)
        self.assertIn('local pending_return_cookie_path = "/cgi-bin/luci/admin/services/linkease_auth"', controller)
        self.assertIn('Max-Age=300; HttpOnly; SameSite=Lax', controller)
        self.assertIn('function cookie_encode(value)', controller)
        self.assertIn('function cookie_decode(value)', controller)
        self.assertIn('return safe_return_target(cookie_decode(http.getcookie(pending_return_cookie)))', controller)

    def test_finish_route_sets_apps_cookie_and_redirects_sanitized_return(self):
        controller = self.read("luci-lib-linkeaseauth/luasrc/controller/linkease_auth.lua")

        finish = controller[controller.index("function linkease_auth_finish()") :]
        self.assertIn('local sid = retrieve_luci_session()', finish)
        self.assertIn('if not valid_cookie_value(sid) then', finish)
        self.assertIn('local target = pending_return_target()', finish)
        self.assertIn('clear_pending_return_cookie()', finish)
        self.assertIn('"linkease_openwrt_sid=" .. sid .. "; Path=/apps; HttpOnly; SameSite=Lax"', finish)
        self.assertIn('http.redirect(target)', finish)

    def test_return_validation_stays_limited_to_apps_paths_and_same_host(self):
        controller = self.read("luci-lib-linkeaseauth/luasrc/controller/linkease_auth.lua")

        self.assertIn("valid_apps_return(value)", controller)
        self.assertIn('path == "/apps"', controller)
        self.assertIn('prefix == "/apps/" or prefix == "/apps?" or prefix == "/apps#"', controller)
        self.assertIn('value:match("^(https?://)([^/]+)(/.*)$")', controller)
        self.assertIn("request_host", controller)
        self.assertIn('request_host .. ":19290"', controller)
        self.assertIn("lan_host", controller)
        self.assertIn('lan_host .. ":19290"', controller)


if __name__ == "__main__":
    unittest.main()
