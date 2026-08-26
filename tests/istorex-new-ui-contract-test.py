#!/usr/bin/env python3

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class IstorexNewUiContractTest(unittest.TestCase):
    def read(self, relative_path):
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_istorex_meta_is_new_ui_bundle(self):
        makefile = self.read("apps/istorex/app-meta-istorex/Makefile")

        self.assertIn("PKG_VERSION:=1.0.0", makefile)
        self.assertIn(
            "META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/linkeasefull/open",
            makefile,
        )
        for package in (
            "app-meta-linkeasefull",
            "app-meta-dockermanager",
            "app-meta-kaiplus",
            "app-meta-kai",
            "app-meta-baidudrive",
            "app-meta-istoreenhance",
            "luci-theme-istorenas",
        ):
            self.assertIn(f"+{package}", makefile)
        self.assertNotIn("+luci-app-istorex", makefile)

    def test_istorex_meta_configures_istorenas_login_landing_page(self):
        config = self.read("apps/istorex/app-meta-istorex/config.sh")

        self.assertIn('[ -z "$ISTORE_CONF_DIR" ] && exit 1', config)
        self.assertIn('LANDING_PAGE="/cgi-bin/luci/admin/services/linkeasefull/open"', config)
        self.assertIn("[ -e /etc/config/luci ] || touch /etc/config/luci", config)
        self.assertIn("[ -e /etc/config/istorenas ] || touch /etc/config/istorenas", config)
        self.assertIn("uci -q show luci.main", config)
        self.assertIn("uci -q set luci.main=core", config)
        self.assertIn("uci -q show luci.themes", config)
        self.assertIn("uci -q set luci.themes=internal", config)
        self.assertIn("uci -q show istorenas.@login[0]", config)
        self.assertIn("uci -q add istorenas login", config)
        self.assertIn('set luci.themes.iStoreNAS="/luci-static/istorenas"', config)
        self.assertIn('set luci.main.mediaurlbase="/luci-static/istorenas"', config)
        self.assertIn('set istorenas.@login[0].landing_page="$LANDING_PAGE"', config)
        self.assertIn("commit luci", config)
        self.assertIn("commit istorenas", config)

    def test_syncapps_maps_theme_and_dockermanager_meta(self):
        syncapps = self.read("syncapps.yaml")

        self.assertIn("local: apps/istorex/luci-theme-istorenas", syncapps)
        self.assertIn("remote: nas-packages-luci/luci/luci-theme-istorenas", syncapps)
        self.assertIn("local: apps/dockermanager/app-meta-dockermanager", syncapps)
        self.assertIn(
            "remote: openwrt-app-meta/applications/app-meta-dockermanager",
            syncapps,
        )

    def test_luci_app_istorex_remains_unmodified_and_not_depended_on(self):
        controller = self.read("apps/istorex/luci-app-istorex/luasrc/controller/istorex.lua")
        makefile = self.read("apps/istorex/luci-app-istorex/Makefile")

        self.assertIn("LUCI_TITLE:=IstoreX", makefile)
        self.assertIn("PKG_VERSION:=0.6.6", makefile)
        self.assertIn("LUCI_DEPENDS:=+luci-app-quickstart +luci-app-store +luci-lib-taskd", makefile)
        self.assertIn("function istorex_template()", controller)
        self.assertIn("function istorex_api_update()", controller)
        self.assertTrue((ROOT / "apps/istorex/luci-app-istorex/htdocs").exists())

    def test_linkeasefull_has_dynamic_open_entry(self):
        controller = self.read(
            "apps/linkeasefull/luci-app-linkeasefull/luasrc/controller/linkeasefull.lua"
        )

        self.assertIn('entry({"admin", "services", "linkeasefull", "open"}', controller)
        self.assertIn("function linkeasefull_open()", controller)
        self.assertIn('return "/apps/"', controller)
        self.assertIn('url_authority(request_or_lan_host(), 19290)', controller)
        self.assertIn('linkease_auth_url("auth")', controller)
        self.assertIn("function uhttpd_supports_proxy_prefix()", controller)
        self.assertIn("function uhttpd_apps_proxy_available()", controller)
        self.assertIn("proxy_prefix_supported = uhttpd_supports_proxy_prefix()", controller)
        self.assertIn("proxy_prefix_enabled = uhttpd_apps_proxy_available()", controller)

    def test_linkeasefull_package_does_not_modify_uhttpd(self):
        defaults = self.read("apps/linkeasefull/linkeasefull/files/linkeasefull.uci-default")

        self.assertNotIn("proxy_prefix", defaults)
        self.assertNotIn("add_list uhttpd", defaults)
        self.assertNotIn("commit uhttpd", defaults)
        self.assertNotIn("/etc/init.d/uhttpd", defaults)

    def test_theme_package_was_imported(self):
        theme_root = ROOT / "apps/istorex/luci-theme-istorenas"

        self.assertTrue((theme_root / "Makefile").is_file())
        self.assertTrue(
            (theme_root / "luasrc/view/themes/istorenas/sysauth.htm").is_file()
        )
        self.assertTrue(
            (theme_root / "htdocs/luci-static/istorenas-login/style.css").is_file()
        )


if __name__ == "__main__":
    unittest.main()
