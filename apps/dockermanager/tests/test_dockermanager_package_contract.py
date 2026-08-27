from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DockerManagerPackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_package_depends_on_shared_linkease_openwrt_auth_bridge(self):
        makefile = self.read("dockermanager/Makefile")
        meta = self.read("app-meta-dockermanager/Makefile")
        luci_makefile = self.read("luci-app-dockermanager/Makefile")
        controller = self.read("luci-app-dockermanager/luasrc/controller/dockermanager.lua")
        cbi = self.read("luci-app-dockermanager/luasrc/model/cbi/dockermanager.lua")
        status = self.read("luci-app-dockermanager/luasrc/view/dockermanager_status.htm")

        self.assertIn("PKG_VERSION:=0.1.1", makefile)
        self.assertIn(
            "PKG_SOURCE_URL:=https://github.com/istoreos/istoreos-app-hub/releases/download/dockermanager-runtime-v$(PKG_VERSION)/",
            makefile,
        )
        self.assertIn("PKG_HASH:=6bd0a5b91d32125879fa5ae54ca3a00df1a3b37bffadda8f986fbf1c4a3e0919", makefile)
        self.assertIn("$(INSTALL_DATA) ./files/logo.svg $(1)/usr/share/dockermanager/www/logo.svg", makefile)
        self.assertNotIn("../app-meta-", makefile)
        self.assertIn("PKG_VERSION:=0.1.1", meta)
        self.assertIn("DEPENDS:=+docker +dockerd +ca-bundle", makefile)
        self.assertNotIn("+luci-lib-linkeaseauth", makefile)
        self.assertIn("LUCI_DEPENDS:=+dockermanager +luci-lib-linkeaseauth", luci_makefile)
        self.assertIn("META_DEPENDS:=+dockermanager +luci-app-dockermanager", meta)
        self.assertNotIn("+luci-lib-linkeaseauth", meta)
        self.assertIn("META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/dockermanager/open", meta)
        self.assertNotIn("+luci-app-linkeasefull", makefile)
        self.assertNotIn("+luci-app-linkeasefull", meta)
        self.assertIn('entry({"admin", "services", "dockermanager", "open"}', controller)
        self.assertIn("function dockermanager_open()", controller)
        self.assertIn("uhttpd_apps_proxy_available()", controller)
        self.assertIn("return base_path", controller)
        self.assertIn("url_authority(request_or_lan_host(), port)", controller)
        self.assertIn('linkease_auth_url("auth")', controller)
        self.assertIn('Map("dockermanager"', cbi)
        self.assertIn('"data_dir"', cbi)
        self.assertIn('"port"', cbi)
        self.assertIn('url("admin/services/dockermanager/open")', status)

    def test_package_registers_desktop_plugin_without_owning_auth_bridge(self):
        makefile = self.read("dockermanager/Makefile")

        self.assertIn("$(1)/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertIn(
            "ln -sf /usr/share/dockermanager/dockermanager-plugin.json $(1)/usr/share/linkeasefull/desktop-apps.d/20-dockermanager-plugin.json",
            makefile,
        )
        self.assertNotIn("/cgi-bin/luci/admin/services/linkeasefull/auth", makefile)
        self.assertNotIn("/cgi-bin/luci/admin/services/linkease_auth/auth", makefile)


if __name__ == "__main__":
    unittest.main()
