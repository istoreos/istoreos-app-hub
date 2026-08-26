from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class IStoreEnhancePackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_runtime_package_tracks_kspeeder_release_asset(self):
        makefile = self.read("istoreenhance/Makefile")

        self.assertIn("PKG_SOURCE_DATE:=0.7.16", makefile)
        self.assertIn("PKG_SOURCE:=iStoreEnhance-binary-$(PKG_SOURCE_DATE).tar.gz", makefile)
        self.assertIn(
            "PKG_SOURCE_URL:=https://github.com/kspeeder/docker_kspeeder/releases/download/v$(PKG_SOURCE_DATE)/",
            makefile,
        )
        self.assertIn(
            "PKG_HASH:=d6fffad59a2a496e64cfe4d883ec042daccb0a4b123c964cc3084860e98bf179",
            makefile,
        )
        self.assertIn("PKG_BUILD_DIR:=$(BUILD_DIR)/iStoreEnhance-binary-$(PKG_SOURCE_DATE)", makefile)

    def test_meta_package_shows_runtime_version(self):
        makefile = self.read("app-meta-istoreenhance/Makefile")

        self.assertIn("PKG_VERSION:=0.7.16", makefile)

    def test_runtime_package_installs_kspeeder_desktop_module(self):
        makefile = self.read("istoreenhance/Makefile")

        self.assertIn("$(1)/usr/share/kspeeder/www", makefile)
        self.assertIn("$(1)/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertIn("./files/kspeeder-plugin.json", makefile)
        self.assertIn("KSPEEDER_WEB_ROOT:=$(PKG_BUILD_DIR)/wwwroot", makefile)
        self.assertIn("$(KSPEEDER_WEB_ROOT)/desktop-entry.js", makefile)
        self.assertIn("$(CP) $(KSPEEDER_WEB_ROOT)/* $(1)/usr/share/kspeeder/www/", makefile)
        self.assertIn("./files/www/desktop-entry.js", makefile)
        self.assertIn("ISTOREENHANCE_LOGO:=./files/logo.png", makefile)
        self.assertIn("ISTOREENHANCE_LOGO:=../app-meta-istoreenhance/logo.png", makefile)
        self.assertIn("$(INSTALL_DATA) $(ISTOREENHANCE_LOGO) $(1)/usr/share/kspeeder/www/logo.png", makefile)
        self.assertIn("/usr/share/linkeasefull/desktop-apps.d/20-kspeeder.json", makefile)

    def test_kspeeder_desktop_manifest_uses_linkease_runtime_proxy(self):
        manifest = json.loads(self.read("istoreenhance/files/kspeeder-plugin.json"))

        self.assertEqual(manifest["id"], "kspeeder")
        self.assertEqual(manifest["staticRoot"], "/usr/share/kspeeder/www")
        self.assertEqual(manifest["desktop"]["entry"], "desktop-entry.js")
        self.assertEqual(manifest["standalone"]["basePath"], "/apps/kspeeder/")
        self.assertTrue(manifest["standalone"]["externalOpen"]["enabled"])
        self.assertEqual(manifest["standalone"]["externalOpen"]["defaultPort"], 5003)
        self.assertEqual(manifest["backend"]["portFromUci"], "istoreenhance.@istoreenhance[0].adminport")
        self.assertEqual(manifest["backend"]["defaultPort"], 5003)
        self.assertEqual(manifest["backend"]["apiPath"], "api/")
        self.assertEqual(manifest["backend"]["upstreamBasePath"], "/apps/kspeeder/")
        self.assertEqual(manifest["backend"]["pathMode"], "preserve")

    def test_kspeeder_desktop_entry_is_browser_safe_single_spa_module(self):
        entry = self.read("istoreenhance/files/www/desktop-entry.js")

        self.assertIn("export async function bootstrap", entry)
        self.assertIn("export async function mount", entry)
        self.assertIn("export async function unmount", entry)
        self.assertIn("context.apiBase", entry)
        self.assertIn("normalizeAPIBase(context)", entry)
        self.assertNotIn("process.", entry)
        self.assertNotIn("require(", entry)


if __name__ == "__main__":
    unittest.main()
