import re
import unittest
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


if __name__ == "__main__":
    unittest.main()
