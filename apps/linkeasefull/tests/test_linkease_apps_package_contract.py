from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class LinkEaseAppsPackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_shared_luci_package_is_versioned_as_apps_integration(self):
        makefile = self.read("linkeasefull/luci-lib-linkeaseauth/Makefile")
        self.assertIn("LUCI_TITLE:=LuCI shared integration for LinkEase apps", makefile)
        self.assertIn("PKG_VERSION:=1.1.0", makefile)
        self.assertIn("PKG_RELEASE:=3", makefile)

    def test_shared_package_keeps_auth_and_adds_separate_apps_routes(self):
        auth = self.read("linkeasefull/luci-lib-linkeaseauth/luasrc/controller/linkease_auth.lua")
        apps = self.read("linkeasefull/luci-lib-linkeaseauth/luasrc/controller/linkease_apps.lua")
        decision = self.read("linkeasefull/luci-lib-linkeaseauth/luasrc/model/linkease/apps.lua")
        defaults = self.read("linkeasefull/luci-lib-linkeaseauth/root/etc/uci-defaults/50_luci-linkeaseauth")

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
            self.assertNotIn("+linkeasefull", runtime, app)
            self.assertNotIn("+linkeasefull", luci, app)

    def test_migrated_apps_register_neutral_and_legacy_manifests_safely(self):
        cases = (
            ("dockermanager", "dockermanager/dockermanager/Makefile", "20", "/usr/share/dockermanager/dockermanager-plugin.json"),
            ("kaiplus", "kaiplus/kaiplus/Makefile", "00", "/usr/share/kaiplus/kaiplus-plugin.json"),
            ("baidudrive", "baidudrive/baidudrive/Makefile", "10", "/usr/share/baidudrive/baidudrive-plugin.json"),
            ("agentflow", "agentflow/agentflow/Makefile", "30", "/usr/share/agentflow/agentflow-plugin.json"),
            ("fastnet", "fastnet/fastnet/Makefile", "17", "/usr/share/fastnet/fastnet-plugin.json"),
            ("kspeeder", "istoreenhance/istoreenhance/Makefile", "20", "/usr/share/kspeeder/kspeeder-plugin.json"),
        )
        for app, makefile_path, prefix, target in cases:
            makefile = self.read(makefile_path)
            neutral = f"/usr/share/linkease/apps.d/{prefix}-{app}-plugin.json"
            legacy = f"/usr/share/linkeasefull/desktop-apps.d/{prefix}-{app}-plugin.json"
            if app in ("agentflow", "fastnet", "kspeeder"):
                neutral = f"/usr/share/linkease/apps.d/{prefix}-{app}.json"
                legacy = f"/usr/share/linkeasefull/desktop-apps.d/{prefix}-{app}.json"
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

    def test_additional_apps_use_the_shared_entry_contract(self):
        cases = {
            "agentflow": (
                "agentflow/agentflow/Makefile",
                "agentflow/luci-app-agentflow/Makefile",
                "agentflow/app-meta-agentflow/Makefile",
                "agentflow/luci-app-agentflow/luasrc/controller/agentflow.lua",
            ),
            "fastnet": (
                "fastnet/fastnet/Makefile",
                "fastnet/luci-app-fastnet/Makefile",
                "fastnet/app-meta-fastnet/Makefile",
                "fastnet/luci-app-fastnet/luasrc/controller/fastnet.lua",
            ),
            "kspeeder": (
                "istoreenhance/istoreenhance/Makefile",
                "istoreenhance/luci-app-istoreenhance/Makefile",
                "istoreenhance/app-meta-istoreenhance/Makefile",
                "istoreenhance/luci-app-istoreenhance/luasrc/controller/istoreenhance.lua",
            ),
        }
        for app, (runtime_path, luci_path, meta_path, controller_path) in cases.items():
            runtime = self.read(runtime_path)
            luci = self.read(luci_path)
            meta = self.read(meta_path)
            controller = self.read(controller_path)
            self.assertIn("+linkease-app-entry", runtime, app)
            self.assertIn("/usr/share/linkease/apps.d", runtime, app)
            self.assertIn("+luci-lib-linkeaseauth", luci, app)
            self.assertNotIn("+linkeasefull", runtime, app)
            self.assertNotIn("+linkeasefull", luci, app)
            self.assertIn(
                f"META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/linkease_apps/open?id={app}",
                meta,
                app,
            )
            self.assertIn(f'compat():open("{app}")', controller, app)
            for forbidden in (
                "uhttpd_apps_proxy_available",
                "linkeasefull_running",
                "uci:set",
                "uci:commit",
            ):
                self.assertNotIn(forbidden, controller, f"{app}: {forbidden}")

    def test_openwrt_embed_remains_a_linkeasefull_only_builtin(self):
        makefile = self.read("linkeasefull/luci-app-linkeasefull-embed/Makefile")
        manifest = self.read(
            "linkeasefull/luci-app-linkeasefull-embed/files/openwrt-luci/openwrt-luci.json"
        )
        self.assertIn("DEPENDS:=+linkeasefull", makefile)
        self.assertIn("/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertNotIn("/usr/share/linkease/apps.d", makefile)
        self.assertIn('"mode": "builtin"', manifest)
        self.assertIn('"component": "LuciContainer"', manifest)


if __name__ == "__main__":
    unittest.main()
