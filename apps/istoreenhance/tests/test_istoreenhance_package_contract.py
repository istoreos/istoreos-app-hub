from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class IStoreEnhancePackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_runtime_package_tracks_kspeeder_release_asset(self):
        makefile = self.read("istoreenhance/Makefile")

        self.assertIn("PKG_SOURCE_DATE:=0.8.0", makefile)
        self.assertIn("PKG_SOURCE:=iStoreEnhance-binary-$(PKG_SOURCE_DATE).tar.gz", makefile)
        self.assertIn(
            "PKG_SOURCE_URL:=https://github.com/kspeeder/docker_kspeeder/releases/download/v$(PKG_SOURCE_DATE)/",
            makefile,
        )
        self.assertIn(
            "PKG_HASH:=926d24994b4fa4d7ffcad1a1f546e05a1ea46b056a01f94bb4e88512866722b7",
            makefile,
        )
        self.assertIn("PKG_BUILD_DIR:=$(BUILD_DIR)/iStoreEnhance-binary-$(PKG_SOURCE_DATE)", makefile)

    def test_meta_package_shows_runtime_version(self):
        makefile = self.read("app-meta-istoreenhance/Makefile")

        self.assertIn("PKG_VERSION:=0.8.0", makefile)
        self.assertIn("PKG_RELEASE:=6", makefile)
        self.assertIn("META_ARCH:=x86_64 aarch64 arm", makefile)
        self.assertIn(
            "META_DESCRIPTION:=KSpeeder 为 Docker 镜像、软件包/文件下载和 GitHub/GitLab 公开仓库克隆提供网络加速。",
            makefile,
        )
        self.assertIn(
            "META_DESCRIPTION.en:=KSpeeder accelerates Docker images, package/file downloads, and public GitHub/GitLab repository clones.",
            makefile,
        )

    def test_runtime_package_installs_kspeeder_desktop_module(self):
        makefile = self.read("istoreenhance/Makefile")

        self.assertIn("$(1)/usr/share/kspeeder/www", makefile)
        self.assertIn("$(1)/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertIn("./files/kspeeder-plugin.json", makefile)
        self.assertIn("KSPEEDER_WEB_ROOT:=$(PKG_BUILD_DIR)/wwwroot", makefile)
        self.assertIn("$(KSPEEDER_WEB_ROOT)/desktop-entry.js", makefile)
        self.assertIn("$(CP) $(KSPEEDER_WEB_ROOT)/* $(1)/usr/share/kspeeder/www/", makefile)
        self.assertIn("./files/www/desktop-entry.js", makefile)
        self.assertIn("$(INSTALL_DATA) ./files/logo.png $(1)/usr/share/kspeeder/www/logo.png", makefile)
        self.assertNotIn("../app-meta-", makefile)
        self.assertIn("/usr/share/linkeasefull/desktop-apps.d/20-kspeeder.json", makefile)

    def test_kspeeder_desktop_manifest_uses_linkease_runtime_proxy(self):
        manifest = json.loads(self.read("istoreenhance/files/kspeeder-plugin.json"))

        self.assertEqual(manifest["id"], "kspeeder")
        self.assertEqual(manifest["staticRoot"], "/usr/share/kspeeder/www")
        self.assertEqual(manifest["desktop"]["entry"], "desktop-entry.js")
        self.assertEqual(manifest["standalone"]["basePath"], "/apps/kspeeder/")
        self.assertTrue(manifest["standalone"]["externalOpen"]["enabled"])
        self.assertEqual(manifest["standalone"]["externalOpen"]["defaultPort"], 5003)
        self.assertEqual(manifest["standalone"]["externalOpen"]["path"], "/")
        self.assertEqual(manifest["backend"]["portFromUci"], "istoreenhance.@istoreenhance[0].adminport")
        self.assertEqual(manifest["backend"]["defaultPort"], 5003)
        self.assertEqual(manifest["backend"]["apiPath"], "api/")
        self.assertEqual(manifest["backend"]["upstreamBasePath"], "/")
        self.assertEqual(manifest["backend"]["pathMode"], "strip-public-base")

    def test_kspeeder_desktop_entry_is_browser_safe_single_spa_module(self):
        entry = self.read("istoreenhance/files/www/desktop-entry.js")

        self.assertIn("export async function bootstrap", entry)
        self.assertIn("export async function mount", entry)
        self.assertIn("export async function unmount", entry)
        self.assertIn("context.apiBase", entry)
        self.assertIn("normalizeAPIBase(context)", entry)
        self.assertNotIn("process.", entry)
        self.assertNotIn("require(", entry)

    def test_luci_open_routes_through_the_shared_auth_entry(self):
        makefile = self.read("luci-app-istoreenhance/Makefile")
        controller = self.read("luci-app-istoreenhance/luasrc/controller/istoreenhance.lua")
        status = self.read("luci-app-istoreenhance/luasrc/view/istoreenhance_status.htm")
        meta_entry = self.read("app-meta-istoreenhance/entry.sh")
        meta_makefile = self.read("app-meta-istoreenhance/Makefile")

        self.assertIn("+luci-lib-linkeaseauth", makefile)
        self.assertIn("+linkease-app-entry", makefile)
        self.assertIn('compat():open("kspeeder")', controller)
        self.assertIn('http = require "luci.http"', controller)
        self.assertIn('resolver = require("luci.model.linkease.apps_openwrt").new()', controller)
        self.assertIn('auth_url = dispatcher.build_url("admin", "services", "linkease_auth", "auth")', controller)
        self.assertIn('url("admin/services/istoreenhance/open")', status)
        self.assertNotIn("st.entry_url", status)
        self.assertIn('META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/istoreenhance', meta_makefile)
        self.assertIn('/cgi-bin/luci/admin/services/istoreenhance', meta_entry)
        self.assertNotIn('linkease_apps/open?id=kspeeder', meta_entry)
        self.assertNotIn('json_add_string "href" "http://$host:', meta_entry)


if __name__ == "__main__":
    unittest.main()
