#!/usr/bin/env python3

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class IstoreRouterContractTest(unittest.TestCase):
    def read(self, relative_path):
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_luci_app_uses_istorerouter_identity(self):
        app_root = ROOT / "apps/istorerouter/luci-app-istorerouter"
        makefile = self.read("apps/istorerouter/luci-app-istorerouter/Makefile")
        controller = self.read(
            "apps/istorerouter/luci-app-istorerouter/luasrc/controller/istorerouter.lua"
        )
        menu = self.read(
            "apps/istorerouter/luci-app-istorerouter/root/usr/share/luci/menu.d/luci-app-istorerouter.json"
        )
        config = self.read("apps/istorerouter/luci-app-istorerouter/root/etc/config/istorerouter")

        self.assertIn("LUCI_TITLE:=iStoreRouter", makefile)
        self.assertIn("define Package/luci-app-istorerouter/conffiles", makefile)
        self.assertIn("/etc/config/istorerouter", makefile)
        self.assertIn('module("luci.controller.istorerouter", package.seeall)', controller)
        self.assertIn('entry({"admin", "istorerouter"}', controller)
        self.assertIn('entry({"admin", "istorerouter_api","status"}', controller)
        self.assertIn('luci.template.render("istorerouter/main"', controller)
        self.assertIn('"admin/istorerouter"', menu)
        self.assertIn('"path": "istorerouter/index"', menu)
        self.assertIn("config istorerouter", config)
        self.assertIn("option 'model'  'router'", config)
        self.assertTrue((app_root / "htdocs/luci-static/istorerouter/index.js").is_file())
        self.assertTrue((app_root / "htdocs/luci-static/istorerouter/style.css").is_file())

    def test_meta_and_syncapps_use_istorerouter(self):
        meta = self.read("apps/istorerouter/app-meta-istorerouter/Makefile")
        syncapps = self.read("syncapps.yaml")

        self.assertIn("META_TITLE:=iStoreRouter", meta)
        self.assertIn("META_DEPENDS:=+luci-app-istorerouter", meta)
        self.assertIn("META_LUCI_ENTRY:=/cgi-bin/luci/admin/istorerouter", meta)
        self.assertIn("local: apps/istorerouter/luci-app-istorerouter", syncapps)
        self.assertIn("remote: nas-packages-luci/luci/luci-app-istorerouter", syncapps)
        self.assertIn("local: apps/istorerouter/app-meta-istorerouter", syncapps)
        self.assertIn("remote: openwrt-app-meta/applications/app-meta-istorerouter", syncapps)


if __name__ == "__main__":
    unittest.main()
