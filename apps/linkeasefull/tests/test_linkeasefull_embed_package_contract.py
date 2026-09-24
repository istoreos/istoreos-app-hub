from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
EMBED = ROOT / "luci-app-linkeasefull-embed"


class LinkEaseFullEmbedPackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_full_product_meta_installs_embed_without_coupling_core_runtime(self):
        meta = self.read("app-meta-linkeasefull/Makefile")
        runtime = self.read("linkeasefull/Makefile")
        embed = self.read("luci-app-linkeasefull-embed/Makefile")

        self.assertIn("PKG_VERSION:=3.0.22", meta)
        self.assertIn("PKG_RELEASE:=1", meta)
        self.assertIn("PKG_SOURCE_DATE:=3.0.22", runtime)
        self.assertIn(
            "462f7d4b9500725094d2cacc388a109201f4b6b8eec5f90de68f756447644c70",
            runtime,
        )
        self.assertIn(
            "4dc7c1b4861115042141b02a5822994ede6fb6e2686f1e1dd6f1c213ec44c00c",
            runtime,
        )
        self.assertIn("+luci-app-linkeasefull-embed", meta)
        self.assertIn("DEPENDS:=+linkeasefull", embed)
        self.assertNotIn("luci-app-linkeasefull-embed", runtime)

    def test_embed_does_not_own_firmware_protocol_compatibility(self):
        makefile = self.read("luci-app-linkeasefull-embed/Makefile")
        readme = self.read("luci-app-linkeasefull-embed/README.md")

        self.assertIn("PKG_VERSION:=1.2.0", makefile)
        self.assertIn("PKG_RELEASE:=1", makefile)
        self.assertNotIn("+luci-proto-bonding", makefile)
        self.assertNotIn("protocol-fallbacks", makefile)
        self.assertNotIn("openwrt-luci-maintain", makefile)
        self.assertNotIn("files/protocol", makefile)
        self.assertEqual(list((EMBED / "files/protocol").glob("*.js")), [])
        self.assertFalse((EMBED / "files/openwrt-luci-maintain.sh").exists())
        self.assertIn("does not install LuCI network protocol handlers", readme)

    def test_embed_is_in_the_downstream_sync_map(self):
        syncapps = (REPO / "syncapps.yaml").read_text(encoding="utf-8")
        self.assertIn(
            "local: apps/linkeasefull/luci-app-linkeasefull-embed", syncapps
        )
        self.assertIn(
            "remote: nas-packages-luci/luci/luci-app-linkeasefull-embed", syncapps
        )


if __name__ == "__main__":
    unittest.main()
