from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class LinkEaseAppsPackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_shared_luci_package_is_versioned_as_apps_integration(self):
        makefile = self.read("linkeaseauth/luci-lib-linkeaseauth/Makefile")
        self.assertIn("LUCI_TITLE:=LuCI shared integration for LinkEase apps", makefile)
        self.assertIn("PKG_VERSION:=1.1.0", makefile)
        self.assertIn("PKG_RELEASE:=2", makefile)

    def test_shared_package_keeps_auth_and_adds_separate_apps_routes(self):
        auth = self.read("linkeaseauth/luci-lib-linkeaseauth/luasrc/controller/linkease_auth.lua")
        apps = self.read("linkeaseauth/luci-lib-linkeaseauth/luasrc/controller/linkease_apps.lua")
        decision = self.read("linkeaseauth/luci-lib-linkeaseauth/luasrc/model/linkease/apps.lua")
        defaults = self.read("linkeaseauth/luci-lib-linkeaseauth/root/etc/uci-defaults/50_luci-linkeaseauth")

        self.assertIn('"linkease_auth", "auth"', auth)
        self.assertIn('"linkease_auth", "auth_finish"', auth)
        self.assertIn('"linkease_apps", "open"', apps)
        self.assertIn('"linkease_apps", "status"', apps)
        auth_begin = auth.split('local auth_finish =', 1)[0]
        apps_open = apps.split('local status =', 1)[0]
        self.assertIn("auth.sysauth = false", auth_begin)
        self.assertNotIn("sysauth_authenticator", auth_begin)
        self.assertIn("open.sysauth = false", apps_open)
        self.assertNotIn("sysauth_authenticator", apps_open)
        self.assertIn("function linkease_auth_finish(state)", auth)
        self.assertIn("bridge():auth_finish(state)", auth)
        self.assertIn('auth_finish.sysauth = "root"', auth)
        self.assertIn('status.sysauth = "root"', apps)
        self.assertNotIn("luci.http", decision)
        self.assertNotIn("uci:set", decision)
        self.assertNotIn("os.execute", decision)
        self.assertIn("rm -f /tmp/luci-indexcache*", defaults)
        self.assertNotIn("uci delete", defaults)

    def test_migrated_apps_have_runtime_and_luci_dependencies(self):
        for app in ("dockermanager", "kaiplus", "baidudrive"):
            runtime = self.read(f"{app}/{app}/Makefile")
            luci = self.read(f"{app}/luci-app-{app}/Makefile")
            self.assertIn("+linkease-app-entry", runtime, app)
            self.assertIn("+luci-lib-linkeaseauth", luci, app)

    def test_migrated_apps_register_neutral_and_legacy_manifests_safely(self):
        for app, prefix in (("dockermanager", "20"), ("kaiplus", "00"), ("baidudrive", "10")):
            makefile = self.read(f"{app}/{app}/Makefile")
            target = f"/usr/share/{app}/{app}-plugin.json"
            neutral = f"/usr/share/linkease/apps.d/{prefix}-{app}-plugin.json"
            legacy = f"/usr/share/linkeasefull/desktop-apps.d/{prefix}-{app}-plugin.json"
            self.assertIn(neutral, makefile)
            self.assertIn(legacy, makefile)
            self.assertIn(f'readlink {neutral}', makefile)
            self.assertIn(f'= "{target}"', makefile)

    def test_app_controllers_delegate_instead_of_implementing_routing(self):
        for app in ("dockermanager", "kaiplus", "baidudrive"):
            controller = self.read(f"{app}/luci-app-{app}/luasrc/controller/{app}.lua")
            self.assertIn(f'compat():open("{app}")', controller)
            self.assertIn(f'compat():legacy_status("{app}"', controller)
            for forbidden in ("uhttpd_apps_proxy", "app_entry_running", "enable_external_port", "uci:set", "uci:commit"):
                self.assertNotIn(forbidden, controller, f"{app}: {forbidden}")


if __name__ == "__main__":
    unittest.main()
