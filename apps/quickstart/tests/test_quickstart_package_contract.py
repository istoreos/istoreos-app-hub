import re
import unittest
import json
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]


def make_value(path: Path, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:=(.*)$", path.read_text(), re.MULTILINE)
    if not match:
        raise AssertionError(f"{key} is missing from {path}")
    return match.group(1).strip()


class QuickstartPackageContractTest(unittest.TestCase):
    def test_backend_luci_and_asset_versions_match(self) -> None:
        backend_makefile = APP_ROOT / "quickstart" / "Makefile"
        netpolicy_makefile = APP_ROOT / "quickstart-netpolicy" / "Makefile"
        luci_makefile = APP_ROOT / "luci-app-quickstart" / "Makefile"
        template = (
            APP_ROOT
            / "luci-app-quickstart"
            / "luasrc"
            / "view"
            / "quickstart"
            / "main.htm"
        ).read_text()

        backend_version = make_value(backend_makefile, "PKG_VERSION")
        backend_release = make_value(backend_makefile, "PKG_RELEASE")
        luci_version = make_value(luci_makefile, "PKG_VERSION")
        effective_backend_version = f"{backend_version}-r{backend_release}"

        self.assertEqual(luci_version, effective_backend_version)
        self.assertIn(f'local asset_version = "{luci_version}"', template)
        self.assertEqual(template.count("?v=<%=asset_version%>"), 3)
        self.assertRegex(make_value(backend_makefile, "PKG_HASH"), r"^[0-9a-f]{64}$")
        self.assertEqual(
            make_value(backend_makefile, "PKG_SOURCE_URL"),
            "https://github.com/istoreos/istoreos-app-hub/releases/download/quickstart-runtime-v$(PKG_VERSION)/",
        )
        self.assertEqual(make_value(netpolicy_makefile, "PKG_VERSION"), "0.2.0-test20260928")
        netpolicy_recipe = netpolicy_makefile.read_text()
        self.assertRegex(make_value(netpolicy_makefile, "PKG_HASH_x86_64"), r"^[0-9a-f]{64}$")
        self.assertRegex(make_value(netpolicy_makefile, "PKG_HASH_aarch64"), r"^[0-9a-f]{64}$")
        self.assertEqual(
            make_value(netpolicy_makefile, "PKG_HASH"),
            "$(PKG_HASH_$(ARCH))",
        )
        self.assertIn("NETPOLICY_TARGET_x86_64:=x86_64-unknown-linux-musl", netpolicy_recipe)
        self.assertIn("NETPOLICY_TARGET_aarch64:=aarch64-unknown-linux-musl", netpolicy_recipe)
        self.assertIn("@(x86_64||aarch64)", netpolicy_recipe)
        self.assertIn("/usr/bin/quickstart-netpolicy", netpolicy_recipe)

        self.assertIn(
            "/etc/quickstart/device-classifications.json",
            backend_makefile.read_text(),
        )
        for state_file in (
            "device-profiles.json", "manual-devices.json", "device-groups.json",
            "traffic-insights.json", "device-policy-effects-v1.json",
            "task-transactions-v1.json", "lan-device-model-v1.json", "network-audit.json",
        ):
            self.assertIn(f"/etc/quickstart/{state_file}", backend_makefile.read_text())

        icon_dir = APP_ROOT / "luci-app-quickstart" / "htdocs" / "luci-static" / "quickstart" / "device-icons"
        self.assertEqual(
            sorted(path.name for path in icon_dir.glob("*.webp")),
            sorted([
                "access-point.webp", "air-conditioner.webp", "camera.webp",
                "computer.webp", "desktop.webp", "door-lock.webp", "e-reader.webp",
                "game-console.webp", "gaming.webp", "handheld-game.webp",
                "home-server.webp", "laptop.webp", "network-bridge.webp",
                "network-switch.webp", "network.webp", "phone.webp", "printer.webp",
                "projector.webp", "robot-vacuum.webp", "sensor.webp", "set-top-box.webp",
                "smart-bulb.webp", "smart-home.webp", "smart-speaker.webp", "storage.webp",
                "tablet.webp", "thermostat.webp", "tv.webp", "unknown.webp", "wearable.webp",
            ]),
        )

        manifest = (icon_dir / "manifest.json").read_text()
        self.assertIn('"license": "project-original-ai-assisted"', manifest)
        self.assertIn('"reviewRequiredBeforePublicRelease": true', manifest)

        notice = (
            APP_ROOT
            / "luci-app-quickstart"
            / "root"
            / "usr"
            / "share"
            / "doc"
            / "quickstart"
            / "NOTICE"
        ).read_text()
        self.assertIn("30 WebP device scene icons", notice)
        self.assertIn("product/legal review as required", notice)

        english_catalog = json.loads((
            APP_ROOT / "luci-app-quickstart" / "htdocs" / "luci-static" /
            "quickstart" / "i18n" / "en.json"
        ).read_text())["en"]
        self.assertEqual(english_catalog["上网路线"], "Internet path")
        self.assertEqual(english_catalog["使用管理"], "Usage controls")

    def test_sync_map_publishes_native_policy_package(self) -> None:
        sync_map = (APP_ROOT.parents[1] / "syncapps.yaml").read_text()
        self.assertIn("apps/quickstart/quickstart-netpolicy", sync_map)
        self.assertIn("nas-packages/network/services/quickstart-netpolicy", sync_map)


if __name__ == "__main__":
    unittest.main()
