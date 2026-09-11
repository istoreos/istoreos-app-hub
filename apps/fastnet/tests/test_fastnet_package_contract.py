from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FastNetPackageContractTest(unittest.TestCase):
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
