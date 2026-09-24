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

        icon_dir = APP_ROOT / "luci-app-quickstart" / "htdocs" / "luci-static" / "quickstart" / "device-icons"
        self.assertEqual(
            sorted(path.name for path in icon_dir.glob("*.webp")),
            sorted([
                "camera.webp", "computer.webp", "gaming.webp", "network.webp",
                "phone.webp", "printer.webp", "smart-home.webp", "storage.webp",
                "tablet.webp", "tv.webp", "unknown.webp", "wearable.webp",
            ]),
        )


if __name__ == "__main__":
    unittest.main()
