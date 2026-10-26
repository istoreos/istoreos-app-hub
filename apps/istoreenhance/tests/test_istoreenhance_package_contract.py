from pathlib import Path
import json
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class IStoreEnhancePackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_runtime_package_tracks_kspeeder_release_asset(self):
        makefile = self.read("istoreenhance/Makefile")

        self.assertIn("PKG_SOURCE_DATE:=0.8.5", makefile)
        self.assertIn("PKG_RELEASE:=1", makefile)
        self.assertIn("PKG_SOURCE:=iStoreEnhance-binary-$(PKG_SOURCE_DATE).tar.gz", makefile)
        self.assertIn(
            "PKG_SOURCE_URL:=https://github.com/kspeeder/docker_kspeeder/releases/download/v$(PKG_SOURCE_DATE)/",
            makefile,
        )
        self.assertIn(
            "PKG_HASH:=9bd2fb08b6c2cc950c7c436abd7e04fbd11496105998303ae3da9dc28e63c0d3",
            makefile,
        )
        self.assertIn("PKG_BUILD_DIR:=$(BUILD_DIR)/iStoreEnhance-binary-$(PKG_SOURCE_DATE)", makefile)

    def test_meta_package_shows_runtime_version(self):
        makefile = self.read("app-meta-istoreenhance/Makefile")

        self.assertIn("PKG_VERSION:=0.8.5", makefile)
        self.assertIn("PKG_RELEASE:=4", makefile)
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

    def test_default_entry_stays_on_luci_while_open_uses_shared_route(self):
        makefile = self.read("luci-app-istoreenhance/Makefile")
        controller = self.read("luci-app-istoreenhance/luasrc/controller/istoreenhance.lua")
        status = self.read("luci-app-istoreenhance/luasrc/view/istoreenhance_status.htm")
        meta_entry = self.read("app-meta-istoreenhance/entry.sh")
        meta_makefile = self.read("app-meta-istoreenhance/Makefile")

        self.assertIn("+luci-lib-linkeaseauth", makefile)
        self.assertIn("+linkease-app-entry", makefile)
        self.assertIn("PKG_VERSION:=0.8.5-r1", makefile)
        self.assertRegex(makefile, r"(?m)^PKG_RELEASE:=$")
        self.assertIn('http = require "luci.http"', controller)
        self.assertIn('resolver = require("luci.model.linkease.apps_openwrt").new()', controller)
        self.assertIn('auth_url = dispatcher.build_url("admin", "services", "linkease_auth", "auth")', controller)
        self.assertIn('url("admin/services/linkease_apps/open")', status)
        self.assertIn('?id=kspeeder', status)
        self.assertNotIn('url("admin/services/istoreenhance/open")', status)
        self.assertNotIn("st.entry_url", status)
        self.assertIn('compat():legacy_status("kspeeder"', controller)
        self.assertNotIn('"istoreenhance", "open"', controller)
        self.assertNotIn('function istoreenhance_open()', controller)
        self.assertNotIn('direct_url', controller)
        self.assertIn('META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/istoreenhance', meta_makefile)
        self.assertNotIn('META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/istoreenhance/open', meta_makefile)
        self.assertIn('json_add_string "href" "/cgi-bin/luci/admin/services/istoreenhance"', meta_entry)
        self.assertNotIn('json_add_string "href" "http://$host:', meta_entry)
        self.assertNotIn('linkease_apps/open?id=kspeeder', meta_entry)

    def test_runtime_depends_on_ks_cli(self):
        makefile = self.read("istoreenhance/Makefile")
        depends = re.search(r"^\s*DEPENDS:=(.+)$", makefile, re.MULTILINE)

        self.assertIsNotNone(depends)
        self.assertIn("+ks-cli", depends.group(1).split())

    def test_ks_cli_tracks_release_archive_and_supported_architectures(self):
        makefile = self.read("ks-cli/Makefile")

        self.assertIn("PKG_NAME:=ks-cli", makefile)
        self.assertIn("PKG_VERSION:=0.8.5", makefile)
        self.assertIn("PKG_RELEASE:=1", makefile)
        self.assertIn("PKG_SOURCE:=ks-cli-binary-$(PKG_VERSION).tar.gz", makefile)
        self.assertIn(
            "PKG_SOURCE_URL:=https://github.com/kspeeder/docker_kspeeder/releases/download/v$(PKG_VERSION)/",
            makefile,
        )
        self.assertIn(
            "PKG_HASH:=e5d40b84d5ff927b313a23f2715801a400adbcd127191e47fb986ed633764a35",
            makefile,
        )
        self.assertIn("DEPENDS:=@(arm||x86_64||aarch64)", makefile)
        self.assertNotRegex(makefile, r"PKGARCH\s*:?=\s*all")

    def test_ks_cli_install_selects_the_target_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            sdk = Path(directory)
            (sdk / "rules.mk").touch()
            (sdk / "package.mk").touch()
            build = sdk / "build/ks-cli-binary-0.8.5"
            build.mkdir(parents=True)
            for arch in ("x86_64", "aarch64", "arm"):
                (build / f"ks-cli.{arch}").write_bytes(f"binary for {arch}".encode())
            harness = sdk / "install.mk"
            harness.write_text(
                "include " + str(ROOT / "ks-cli/Makefile") + "\n"
                "install:\n\t$(call Package/ks-cli/install,$(DESTDIR))\n",
                encoding="utf-8",
            )

            for arch in ("x86_64", "aarch64", "arm"):
                with self.subTest(arch=arch):
                    destination = sdk / arch
                    result = subprocess.run(
                        [
                            "make", "--no-print-directory", "-f", str(harness), "install",
                            f"TOPDIR={sdk}", f"INCLUDE_DIR={sdk}", f"BUILD_DIR={sdk / 'build'}",
                            f"ARCH={arch}", f"DESTDIR={destination}",
                            "INSTALL_DIR=install -d -m0755", "INSTALL_BIN=install -m0755",
                        ],
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    binary = destination / "usr/bin/ks-cli"
                    self.assertEqual(binary.read_bytes(), f"binary for {arch}".encode())
                    self.assertEqual(binary.stat().st_mode & 0o777, 0o755)
                    files = [p for p in destination.rglob("*") if p.is_file()]
                    self.assertEqual(files, [binary])

    def test_syncapps_exports_ks_cli_with_istoreenhance(self):
        syncapps = (ROOT.parents[1] / "syncapps.yaml").read_text(encoding="utf-8")
        section = re.search(
            r"(?ms)^    istoreenhance:\n(?P<body>.*?)(?=^    [a-z0-9][^:\n]*:\n|\Z)",
            syncapps,
        )

        self.assertIsNotNone(section)
        self.assertIn("local: apps/istoreenhance/ks-cli", section.group("body"))
        self.assertIn("remote: nas-packages/network/services/ks-cli", section.group("body"))


if __name__ == "__main__":
    unittest.main()
