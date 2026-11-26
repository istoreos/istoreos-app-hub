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

        self.assertIn("PKG_VERSION:=3.0.32", meta)
        self.assertIn("PKG_RELEASE:=8", meta)
        self.assertIn("PKG_SOURCE_DATE:=3.0.32", runtime)
        self.assertIn(
            "4f917e4e1348ee7a3251830dfb23fbe4a193487ccad5bc71d08479676841f57a",
            runtime,
        )
        self.assertIn(
            "a7133ca2be4f8d9fe10b2d3fe17bfc203cad522d84a7120a7504d20f5537829b",
            runtime,
        )
        self.assertIn("+luci-app-linkeasefull-embed", meta)
        self.assertIn("DEPENDS:=+linkeasefull", embed)
        self.assertNotIn("luci-app-linkeasefull-embed", runtime)

    def test_embed_does_not_own_firmware_protocol_compatibility(self):
        makefile = self.read("luci-app-linkeasefull-embed/Makefile")
        readme = self.read("luci-app-linkeasefull-embed/README.md")

        self.assertIn("PKG_VERSION:=1.2.0-r3", makefile)
        self.assertRegex(makefile, r"(?m)^PKG_RELEASE:=$")
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
