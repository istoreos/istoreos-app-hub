from pathlib import Path
import os
import subprocess
import tempfile
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

    def test_embed_uses_private_fallbacks_without_unavailable_protocol_dependency(self):
        makefile = self.read("luci-app-linkeasefull-embed/Makefile")

        self.assertIn("PKG_VERSION:=1.1.0", makefile)
        self.assertIn("PKG_RELEASE:=1", makefile)
        self.assertNotIn("+luci-proto-bonding", makefile)
        self.assertIn("/usr/share/linkeasefull/openwrt-luci/protocol-fallbacks", makefile)
        self.assertIn(
            "./files/openwrt-luci-maintain.sh $(1)/usr/libexec/linkeasefull/openwrt-luci-maintain",
            makefile,
        )
        self.assertIn('"$${maintainer}" install "$${root}"', makefile)
        self.assertIn('"$${maintainer}" remove "$${root}"', makefile)
        self.assertNotIn(
            "$(INSTALL_DATA) ./files/protocol/bonding.js $(1)/www/luci-static/resources/protocol/bonding.js",
            makefile,
        )
        self.assertNotIn(
            "$(INSTALL_DATA) ./files/protocol/directip.js $(1)/www/luci-static/resources/protocol/directip.js",
            makefile,
        )
        self.assertNotIn(
            "$(INSTALL_DATA) ./files/protocol/wwan.js $(1)/www/luci-static/resources/protocol/wwan.js",
            makefile,
        )

    def test_fallback_maintainer_preserves_real_protocol_modules(self):
        maintainer = EMBED / "files/openwrt-luci-maintain.sh"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private = root / "usr/share/linkeasefull/openwrt-luci/protocol-fallbacks"
            public = root / "www/luci-static/resources/protocol"
            private.mkdir(parents=True)
            public.mkdir(parents=True)
            for source in sorted((EMBED / "files/protocol").glob("*.js")):
                (private / source.name).write_bytes(source.read_bytes())

            real_bonding = public / "bonding.js"
            real_bonding.write_text("real bonding module\n", encoding="utf-8")
            subprocess.run(["sh", str(maintainer), "install", str(root)], check=True)

            self.assertFalse(real_bonding.is_symlink())
            self.assertEqual(real_bonding.read_text(encoding="utf-8"), "real bonding module\n")
            for name in ("directip.js", "wwan.js"):
                link = public / name
                self.assertTrue(link.is_symlink())
                self.assertEqual(
                    os.readlink(link),
                    f"/usr/share/linkeasefull/openwrt-luci/protocol-fallbacks/{name}",
                )

            (public / "wwan.js").unlink()
            (public / "wwan.js").write_text("real wwan module\n", encoding="utf-8")
            subprocess.run(["sh", str(maintainer), "remove", str(root)], check=True)

            self.assertEqual(real_bonding.read_text(encoding="utf-8"), "real bonding module\n")
            self.assertFalse((public / "directip.js").exists())
            self.assertEqual(
                (public / "wwan.js").read_text(encoding="utf-8"),
                "real wwan module\n",
            )

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
