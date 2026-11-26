import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class MiseLuciGuidanceTest(unittest.TestCase):
    def test_unavailable_kspeeder_has_install_and_origin_paths(self):
        source = (ROOT / "web/src/live/ProductionApp.vue").read_text()
        asset = (ROOT / "luci-app-mise/htdocs/luci-static/resources/mise/app.js").read_text()

        for text in (
            "安装 KSpeeder 可加速下载",
            "前往 iStore 安装 KSpeeder",
            "暂不安装也可以使用源站继续",
        ):
            self.assertIn(text, source)
            self.assertIn(text, asset)
        self.assertIn('href="/cgi-bin/luci/admin/store"', source)

    def test_package_revisions_expose_the_luci_update(self):
        luci_recipe = (ROOT / "luci-app-mise/Makefile").read_text()
        meta_recipe = (ROOT / "app-meta-mise/Makefile").read_text()
        self.assertIn("PKG_RELEASE:=2", luci_recipe)
        self.assertIn("PKG_RELEASE:=7", meta_recipe)


if __name__ == "__main__":
    unittest.main()
