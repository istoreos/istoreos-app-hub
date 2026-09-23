from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LinkEaseAppEntryContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_package_owns_both_workers_and_single_init(self):
        makefile = self.read("linkease-app-entry/Makefile")
        full_makefile = self.read("linkeasefull/Makefile")
        entry_init = self.read("linkease-app-entry/files/linkease-app-entry.init")
        compatibility_init = self.read("linkeasefull/files/linkeasefull.init")

        self.assertIn("PKG_NAME:=linkease-app-entry", makefile)
        self.assertIn("define Package/$(PKG_NAME)", makefile)
        self.assertIn("linkease-app-entryd", makefile)
        self.assertIn("linkease-app-gateway", makefile)
        self.assertIn("+luci-lib-linkeaseauth", makefile)
        self.assertNotIn("+linkeasefull", makefile)
        self.assertIn("+linkease-app-entry", full_makefile)
        self.assertNotIn("define Package/linkease-app-entry", full_makefile)
        self.assertNotIn("linkease-app-entryd", full_makefile)
        self.assertNotIn("linkease-app-gateway", full_makefile)
        self.assertIn("PKG_VERSION:=3.0.20", makefile)
        self.assertIn("PKG_RELEASE:=3", makefile)
        self.assertIn(
            "PKG_SOURCE:=linkease-app-entry-runtime-$(PKG_VERSION)-linux-$(LINKEASE_RUNTIME_ARCH).tar.gz",
            makefile,
        )
        self.assertIn(
            "PKG_BUILD_DIR:=$(BUILD_DIR)/linkease-app-entry-runtime-$(PKG_VERSION)-linux-$(LINKEASE_RUNTIME_ARCH)",
            makefile,
        )
        self.assertIn(
            "ecaee4b875f07c22622044cac7eb39ebf0738c910d21211ca63d36eeaa7cb6e6",
            makefile,
        )
        self.assertIn(
            "b04ac3b15bcd12bb99800ebb7d15e98d8f8c4ca73f2b422153acabd170c9fea4",
            makefile,
        )
        self.assertNotIn(
            "PKG_BUILD_DIR:=$(BUILD_DIR)/linkease-app-entry-runtime-$(PKG_VERSION)-linux-$(LINKEASE_RUNTIME_ARCH)",
            full_makefile,
        )
        self.assertIn('procd_set_param command "$ENTRYD"', entry_init)
        self.assertIn('--primary-enabled="$primary"', entry_init)
        self.assertIn("LINKEASE_AUTH_PROVIDER=openwrt", entry_init)
        self.assertNotIn("procd_open_instance", compatibility_init)
        self.assertIn('"$ENTRY_INIT" restart', compatibility_init)

    def test_luci_enable_reconciles_the_selected_worker(self):
        compatibility_init = self.read("linkeasefull/files/linkeasefull.init")
        defaults = self.read("linkeasefull/files/linkeasefull.uci-default")
        luci_model = self.read(
            "luci-app-linkeasefull/luasrc/model/cbi/linkeasefull.lua"
        )

        self.assertIn("sync_force_gateway", compatibility_init)
        self.assertIn('uci -q get linkeasefull.@linkeasefull[0].enabled', compatibility_init)
        self.assertIn('rm -f "$FORCE_GATEWAY"', compatibility_init)
        self.assertIn(': > "$FORCE_GATEWAY"', compatibility_init)
        self.assertIn("add ucitrack linkeasefull", defaults)
        self.assertIn("set ucitrack.@linkeasefull[-1].init=linkeasefull", defaults)
        self.assertIn("function enabled.write", luci_model)
        self.assertIn("/var/run/linkease-app-entry/force-gateway", luci_model)
        self.assertIn("fs.remove(force_gateway)", luci_model)
        self.assertIn("fs.writefile(force_gateway", luci_model)

    def test_uhttpd_mapping_is_stable_and_idempotent(self):
        defaults = self.read("linkease-app-entry/files/linkease-app-entry.uci-default")
        self.assertIn("/apps=http://127.0.0.1:19290", defaults)
        self.assertIn("add_list", defaults)
        self.assertIn("found", defaults)

    def test_product_meta_packages_keep_core_and_bundle_boundaries(self):
        apps_root = ROOT.parent
        core = self.read("app-meta-linkeasefull/Makefile")
        bundle = (apps_root / "istorex/app-meta-istorex/Makefile").read_text(
            encoding="utf-8"
        )

        self.assertIn("+linkeasefull", core)
        self.assertIn("+luci-app-linkeasefull-embed", core)
        for package in (
            "app-meta-dockermanager",
            "app-meta-kaiplus",
            "app-meta-kai",
            "app-meta-baidudrive",
            "app-meta-istoreenhance",
        ):
            self.assertNotIn("+" + package, core, package)
            self.assertIn("+" + package, bundle, package)
        self.assertIn("+app-meta-linkeasefull", bundle)


if __name__ == "__main__":
    unittest.main()
