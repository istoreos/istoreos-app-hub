from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FastNetPackageContractTest(unittest.TestCase):
    def test_release_versions_and_binary_contract_are_aligned(self):
        runtime = (ROOT / "fastnet/Makefile").read_text(encoding="utf-8")
        luci = (ROOT / "luci-app-fastnet/Makefile").read_text(encoding="utf-8")
        meta = (ROOT / "app-meta-fastnet/Makefile").read_text(encoding="utf-8")

        source_version = re.search(r"^PKG_VERSION:=(.+)$", runtime, re.MULTILINE)
        luci_version = re.search(r"^PKG_VERSION:=(.+)$", luci, re.MULTILINE)
        meta_version = re.search(r"^PKG_VERSION:=(.+)$", meta, re.MULTILINE)
        source_hash = re.search(r"^PKG_HASH:=([0-9a-f]{64})$", runtime, re.MULTILINE)

        self.assertIsNotNone(source_version)
        self.assertIsNotNone(luci_version)
        self.assertIsNotNone(meta_version)
        self.assertIsNotNone(source_hash)
        self.assertEqual(luci_version.group(1), f"{source_version.group(1)}-r1")
        self.assertEqual(meta_version.group(1), source_version.group(1))
        self.assertIn(
            "istoreos-app-hub/releases/download/fastnet-runtime-v$(PKG_VERSION)/",
            runtime,
        )
        self.assertIn(
            "$(PKG_BUILD_DIR)/FastNet.$(PKG_ARCH_FASTNET)",
            runtime,
        )
        self.assertNotIn("PKGARCH:=all", runtime)

    def test_app_meta_registers_a_standard_lan_web_module(self):
        manifest_path = (
            ROOT
            / "app-meta-fastnet/root/usr/share/linkeasefull/desktop-apps.d/17-fastnet.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["id"], "fastnet")
        self.assertNotIn("staticRoot", manifest)
        self.assertNotIn("backend", manifest)

        desktop = manifest["desktop"]
        self.assertEqual(desktop["mode"], "iframe")
        self.assertEqual(desktop["target"]["hostMode"], "request-host")
        self.assertEqual(desktop["target"]["port"]["default"], 3200)
        self.assertEqual(
            desktop["target"]["port"]["keys"]["uci"],
            "fastnet.@fastnet[0].port",
        )
        self.assertEqual(desktop["access"]["scope"], "lan")
        self.assertTrue(manifest["standalone"]["externalOpen"]["enabled"])
        self.assertNotIn("defaultPort", manifest["standalone"]["externalOpen"])


if __name__ == "__main__":
    unittest.main()
