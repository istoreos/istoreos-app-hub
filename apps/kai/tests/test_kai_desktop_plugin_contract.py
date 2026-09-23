from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class KaiDesktopPluginContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_manifest_registers_kai_as_a_lan_iframe_app(self):
        manifest = json.loads(self.read("kai/files/kai-plugin.json"))

        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["id"], "kai")
        self.assertEqual(manifest["name"], "KAI")
        self.assertEqual(manifest["icon"], "logo.png")
        self.assertEqual(manifest["staticRoot"], "/usr/share/kai/www")
        self.assertEqual(manifest["desktop"]["mode"], "iframe")
        self.assertEqual(manifest["desktop"]["target"]["scheme"], "http")
        self.assertEqual(manifest["desktop"]["target"]["hostMode"], "request-host")
        self.assertEqual(manifest["desktop"]["target"]["port"]["default"], 8197)
        self.assertEqual(
            manifest["desktop"]["target"]["port"]["keys"]["uci"],
            "kai.@kai[0].port",
        )
        self.assertEqual(manifest["desktop"]["target"]["path"], "/apps/kai/web/")
        self.assertEqual(manifest["desktop"]["access"]["scope"], "lan")
        self.assertEqual(manifest["standalone"]["basePath"], "/apps/kai/")
        self.assertNotIn("url", manifest["standalone"])
        self.assertTrue(manifest["standalone"]["externalOpen"]["enabled"])

        backend = manifest["backend"]
        self.assertEqual(backend["type"], "http")
        self.assertEqual(backend["transport"], "tcp")
        self.assertEqual(backend["scheme"], "http")
        self.assertEqual(backend["host"], "127.0.0.1")
        self.assertEqual(backend["portFromUci"], "kai.@kai[0].port")
        self.assertEqual(backend["defaultPort"], 8197)
        self.assertEqual(backend["upstreamBasePath"], "/apps/kai/")
        self.assertEqual(backend["pathMode"], "preserve")
        self.assertEqual(backend["proxyMode"], "app-base")

    def test_runtime_package_owns_desktop_registration(self):
        makefile = self.read("kai/Makefile")

        self.assertIn("+linkease-app-entry", makefile)
        self.assertIn("$(1)/usr/share/kai/www", makefile)
        self.assertIn("$(1)/usr/share/linkease/apps.d", makefile)
        self.assertIn("$(1)/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertIn(
            "$(INSTALL_DATA) ./files/kai-plugin.json $(1)/usr/share/kai/kai-plugin.json",
            makefile,
        )
        self.assertIn(
            "$(INSTALL_DATA) ./files/logo.png $(1)/usr/share/kai/www/logo.png",
            makefile,
        )
        self.assertIn(
            "ln -sf /usr/share/kai/kai-plugin.json $(1)/usr/share/linkease/apps.d/05-kai-plugin.json",
            makefile,
        )
        self.assertIn(
            "ln -sf /usr/share/kai/kai-plugin.json $(1)/usr/share/linkeasefull/desktop-apps.d/05-kai-plugin.json",
            makefile,
        )

    def test_runtime_package_unregisters_only_its_own_links(self):
        makefile = self.read("kai/Makefile")

        self.assertIn("define Package/$(PKG_NAME)/prerm", makefile)
        self.assertIn("readlink /usr/share/linkease/apps.d/05-kai-plugin.json", makefile)
        self.assertIn("readlink /usr/share/linkeasefull/desktop-apps.d/05-kai-plugin.json", makefile)
        self.assertIn('= "/usr/share/kai/kai-plugin.json"', makefile)


if __name__ == "__main__":
    unittest.main()
