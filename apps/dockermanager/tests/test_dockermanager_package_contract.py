from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DockerManagerPackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_package_depends_on_shared_linkease_openwrt_auth_bridge(self):
        makefile = self.read("dockermanager/Makefile")
        meta = self.read("app-meta-dockermanager/Makefile")

        self.assertIn("DEPENDS:=+docker +dockerd +ca-bundle +luci-lib-linkeaseauth", makefile)
        self.assertIn("META_DEPENDS:=+dockermanager +luci-lib-linkeaseauth", meta)
        self.assertNotIn("+luci-app-linkeasefull", makefile)
        self.assertNotIn("+luci-app-linkeasefull", meta)

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
