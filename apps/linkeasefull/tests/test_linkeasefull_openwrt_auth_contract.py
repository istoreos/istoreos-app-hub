from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LinkEaseFullOpenWrtAuthShimContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_legacy_auth_paths_redirect_to_shared_auth_bridge(self):
        controller = self.read("luci-app-linkeasefull/luasrc/controller/linkeasefull.lua")
        makefile = self.read("luci-app-linkeasefull/Makefile")

        self.assertIn('entry({"admin", "services", "linkeasefull", "auth"}, call("linkeasefull_auth")).leaf = true', controller)
        self.assertIn('entry({"admin", "services", "linkeasefull", "auth_finish"}, call("linkeasefull_auth_finish"))', controller)
        self.assertIn('auth_finish.sysauth = "root"', controller)
        self.assertIn('auth_finish.sysauth_authenticator = "htmlauth"', controller)
        self.assertIn('function cookie_encode(value)', controller)
        self.assertIn('return dispatcher.build_url("admin", "services", "linkease_auth", name)', controller)
        self.assertIn('http.redirect(linkease_auth_url("auth") .. "?return=" .. cookie_encode(target))', controller)
        self.assertIn('http.redirect(linkease_auth_url("auth_finish"))', controller)
        self.assertIn("LUCI_DEPENDS:=+linkeasefull +luci-lib-linkeaseauth +luci-lib-linkeasefile", makefile)
        self.assertNotIn('util.ubus("session", "get", { ubus_rpc_session = sid })', controller)
        self.assertNotIn('local pending_return_cookie = "linkease_openwrt_pending_return"', controller)


if __name__ == "__main__":
    unittest.main()
