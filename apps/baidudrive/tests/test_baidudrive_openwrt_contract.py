from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BaiduDriveOpenWrtContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_linkeasefull_desktop_plugin_manifest_contract(self):
        manifest = json.loads(self.read("baidudrive/files/baidudrive-plugin.json"))

        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["id"], "baidudrive")
        self.assertEqual(manifest["name"], "BaiduDrive")
        self.assertEqual(manifest["icon"], "baidu-drive.png")
        self.assertEqual(manifest["staticRoot"], "/usr/share/baidudrive/www")
        self.assertEqual(manifest["desktop"]["mode"], "module")
        self.assertEqual(manifest["desktop"]["entry"], "desktop-entry.js")
        self.assertEqual(manifest["desktop"]["isolation"], "shadow-dom")
        self.assertEqual(manifest["standalone"]["basePath"], "/apps/baidudrive/")
        self.assertEqual(manifest["backend"]["portFromUci"], "baidudrive.@baidudrive[0].port")
        self.assertEqual(manifest["backend"]["defaultPort"], 10780)
        self.assertEqual(manifest["backend"]["upstreamBasePath"], "/apps/baidudrive/")
        self.assertEqual(manifest["backend"]["apiPath"], "api/")
        self.assertEqual(manifest["backend"]["pathMode"], "preserve")
        self.assertTrue(manifest["window"]["singleton"])
        self.assertNotIn("desktopPriority", manifest)

    def test_baidudrive_package_install_registers_linkeasefull_desktop_plugin(self):
        makefile = self.read("baidudrive/Makefile")

        self.assertIn("$(1)/usr/share/baidudrive/www", makefile)
        self.assertIn("$(1)/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertIn("$(CP) $(PKG_BUILD_DIR)/web/dist/. $(1)/usr/share/baidudrive/www/", makefile)
        self.assertIn(
            "$(INSTALL_DATA) ./files/baidudrive-plugin.json $(1)/usr/share/baidudrive/baidudrive-plugin.json",
            makefile,
        )
        self.assertIn(
            "ln -sf /usr/share/baidudrive/baidudrive-plugin.json $(1)/usr/share/linkeasefull/desktop-apps.d/10-baidudrive-plugin.json",
            makefile,
        )

    def test_baidudrive_package_unregisters_linkeasefull_desktop_plugin_on_remove(self):
        makefile = self.read("baidudrive/Makefile")

        self.assertIn("define Package/$(PKG_NAME)/prerm", makefile)
        self.assertIn("readlink /usr/share/linkeasefull/desktop-apps.d/10-baidudrive-plugin.json", makefile)
        self.assertIn('= "/usr/share/baidudrive/baidudrive-plugin.json"', makefile)
        self.assertIn("rm -f /usr/share/linkeasefull/desktop-apps.d/10-baidudrive-plugin.json", makefile)


if __name__ == "__main__":
    unittest.main()
