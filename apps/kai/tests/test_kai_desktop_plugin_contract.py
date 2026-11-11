"""KAI keeps its service but retires both desktop registration entries."""
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = runpy.run_path(str(ROOT.parents[1] / "tools/tests/test_app_registration.py"))
DIRECTORIES = ("usr/share/linkease/apps.d", "usr/share/linkeasefull/desktop-apps.d")
MANIFEST = "/usr/share/kai/kai-plugin.json"


class KaiDesktopPluginContractTest(unittest.TestCase):
    def package(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return SUPPORT["PackageStage"]("kai/kai", Path(temporary.name))

    def test_fresh_install_keeps_runtime_without_desktop_assets_or_entries(self):
        package = self.package()
        package.hook("postinst")
        for directory in DIRECTORIES:
            self.assertFalse((package.stage / directory).exists())
        self.assertFalse((package.stage / "usr/share/kai/kai-plugin.json").exists())
        self.assertFalse((package.stage / "usr/share/kai/www/logo.png").exists())
        for relative in ("usr/sbin/kai_bin", "usr/libexec/kai-session-launch", "etc/init.d/kai", "etc/config/kai"):
            self.assertTrue((package.stage / relative).is_file(), relative)
        makefile = (ROOT / "kai/Makefile").read_text()
        self.assertIn("+luci-lib-linkeaseauth", makefile)
        self.assertNotIn("+linkease-app-entry", makefile)

    def test_upgrade_and_uninstall_retire_only_owned_kai_links(self):
        for hook in ("postinst", "prerm"):
            with self.subTest(hook=hook):
                package = self.package()
                for directory in DIRECTORIES:
                    parent = package.stage / directory
                    parent.mkdir(parents=True, exist_ok=True)
                    (parent / "05-kai-plugin.json").symlink_to(MANIFEST)
                    (parent / "00-kaiplus-plugin.json").symlink_to("/usr/share/kaiplus/kaiplus-plugin.json")
                package.hook(hook)
                package.hook(hook)
                for directory in DIRECTORIES:
                    self.assertFalse((package.stage / directory / "05-kai-plugin.json").is_symlink())
                    self.assertEqual(str((package.stage / directory / "00-kaiplus-plugin.json").readlink()),
                                     "/usr/share/kaiplus/kaiplus-plugin.json")

    def test_custom_files_directories_and_foreign_links_survive(self):
        package = self.package()
        for directory in DIRECTORIES:
            path = package.stage / directory / "05-kai-plugin.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"custom":true}')
            package.hook("postinst")
            package.hook("prerm")
            self.assertEqual(path.read_text(), '{"custom":true}')
            path.unlink()
            path.symlink_to("/usr/share/other/custom.json")
            package.hook("postinst")
            package.hook("prerm")
            self.assertEqual(str(path.readlink()), "/usr/share/other/custom.json")
            path.unlink()
            path.mkdir()
            (path / "custom").write_text("keep")
            package.hook("postinst")
            package.hook("prerm")
            self.assertEqual((path / "custom").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
