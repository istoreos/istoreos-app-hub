from pathlib import Path
import json
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class IStoreEnhancePackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_runtime_package_tracks_kspeeder_release_asset(self):
        makefile = self.read("istoreenhance/Makefile")

        self.assertIn("PKG_SOURCE_DATE:=0.9.1", makefile)
        self.assertIn("PKG_RELEASE:=2", makefile)
        self.assertIn("PKG_SOURCE:=iStoreEnhance-binary-$(PKG_SOURCE_DATE).tar.gz", makefile)
        self.assertIn(
            "PKG_SOURCE_URL:=https://github.com/kspeeder/docker_kspeeder/releases/download/v$(PKG_SOURCE_DATE)/",
            makefile,
        )
        self.assertIn(
            "PKG_HASH:=d117d3529ce4ae170f7ba284ce89112535337c97ce86997275b93dcf373b0ce9",
            makefile,
        )
        self.assertIn("PKG_BUILD_DIR:=$(BUILD_DIR)/iStoreEnhance-binary-$(PKG_SOURCE_DATE)", makefile)

    def test_meta_package_shows_runtime_version(self):
        makefile = self.read("app-meta-istoreenhance/Makefile")

        self.assertIn("PKG_VERSION:=0.9.1", makefile)
        self.assertIn("PKG_RELEASE:=12", makefile)
        self.assertIn("META_ARCH:=x86_64 aarch64 arm", makefile)
        self.assertIn(
            "META_DESCRIPTION:=KSpeeder 为 Docker 镜像、软件包/文件下载和 GitHub/GitLab 公开仓库克隆提供网络加速。",
            makefile,
        )
        self.assertIn(
            "META_DESCRIPTION.en:=KSpeeder accelerates Docker images, package/file downloads, and public GitHub/GitLab repository clones.",
            makefile,
        )

    def test_runtime_package_installs_kspeeder_iframe_assets(self):
        makefile = self.read("istoreenhance/Makefile")

        self.assertIn("$(1)/usr/share/kspeeder/www", makefile)
        self.assertNotIn("$(1)/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertIn("./files/kspeeder-plugin.json", makefile)
        self.assertIn("KSPEEDER_WEB_ROOT:=$(PKG_BUILD_DIR)/wwwroot", makefile)
        self.assertIn("$(KSPEEDER_WEB_ROOT)/index.html", makefile)
        self.assertNotIn("$(KSPEEDER_WEB_ROOT)/desktop-entry.js", makefile)
        self.assertIn("$(CP) $(KSPEEDER_WEB_ROOT)/* $(1)/usr/share/kspeeder/www/", makefile)
        self.assertNotIn("./files/www/desktop-entry.js", makefile)
        self.assertIn("$(INSTALL_DATA) ./files/logo.png $(1)/usr/share/kspeeder/www/logo.png", makefile)
        self.assertNotIn("../app-meta-", makefile)
        self.assertIn("/usr/share/linkease/apps.d/20-kspeeder.json", makefile)

    def test_kspeeder_desktop_manifest_uses_iframe_with_uci_admin_port(self):
        manifest = json.loads(self.read("istoreenhance/files/kspeeder-plugin.json"))

        self.assertEqual(manifest["id"], "kspeeder")
        self.assertEqual(manifest["staticRoot"], "/usr/share/kspeeder/www")
        self.assertEqual(manifest["desktop"]["mode"], "iframe")
        self.assertNotIn("entry", manifest["desktop"])
        self.assertNotIn("isolation", manifest["desktop"])
        target = manifest["desktop"]["target"]
        self.assertEqual(target["scheme"], "http")
        self.assertEqual(target["hostMode"], "request-host")
        self.assertEqual(target["port"]["default"], 5003)
        self.assertEqual(
            target["port"]["keys"]["uci"],
            "istoreenhance.@istoreenhance[0].adminport",
        )
        self.assertEqual(target["path"], "/")
        self.assertEqual(manifest["desktop"]["access"]["scope"], "lan")
        self.assertEqual(manifest["config"]["providerOrder"], ["uci"])
        self.assertEqual(manifest["config"]["providers"]["uci"]["type"], "uci")
        self.assertEqual(manifest["standalone"]["basePath"], "/apps/kspeeder/")
        self.assertTrue(manifest["standalone"]["externalOpen"]["enabled"])
        self.assertEqual(manifest["standalone"]["externalOpen"]["defaultPort"], 5003)
        self.assertEqual(manifest["standalone"]["externalOpen"]["path"], "/")
        self.assertEqual(manifest["backend"]["portFromUci"], "istoreenhance.@istoreenhance[0].adminport")
        self.assertEqual(manifest["backend"]["defaultPort"], 5003)
        self.assertEqual(manifest["backend"]["apiPath"], "api/")
        self.assertEqual(manifest["backend"]["upstreamBasePath"], "/")
        self.assertEqual(manifest["backend"]["pathMode"], "strip-public-base")

    def test_runtime_package_does_not_ship_obsolete_desktop_module(self):
        self.assertFalse((ROOT / "istoreenhance/files/www/desktop-entry.js").exists())

    def test_gateway_domains_are_one_typed_authoritative_list(self):
        lines = [
            line.split()
            for line in self.read("istoreenhance/files/gateway-domains.conf").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertTrue(all(len(line) == 2 for line in lines))
        gateway = sorted(domain for kind, domain in lines if kind == "gateway")
        loopback = sorted(domain for kind, domain in lines if kind == "loopback")
        self.assertEqual(len(lines), len(gateway) + len(loopback))
        self.assertEqual(len({domain for _, domain in lines}), len(lines))
        self.assertEqual(
            gateway,
            sorted(
                """
                dl-codeload-github.linkease.net
                dl-conda-community.linkease.net
                dl-conda.linkease.net
                dl-crates-index.linkease.net
                dl-crates-static.linkease.net
                dl-crates.linkease.net
                dl-github-api.linkease.net
                dl-github.linkease.net
                dl-go-sdk.linkease.net
                dl-golang.linkease.net
                dl-gradle-distributions.linkease.net
                dl-gradle-plugins.linkease.net
                dl-homebrew-api.linkease.net
                dl-homebrew-bottles.linkease.net
                dl-maven.linkease.net
                dl-mise-versions.linkease.net
                dl-node-unofficial.linkease.net
                dl-nodejs-org.linkease.net
                dl-npm.linkease.net
                dl-nuget-files.linkease.net
                dl-nuget.linkease.net
                dl-packagist-huawei.linkease.net
                dl-packagist.linkease.net
                dl-playwright.linkease.net
                dl-pypi-files.linkease.net
                dl-pypi.linkease.net
                dl-rubygems.linkease.net
                dl-rustup.linkease.net
                dl-sigstore-tuf.linkease.net
                gh.linkease.net
                ghcr.linkease.net
                registry.linkease.net
                """.split()
            ),
        )
        self.assertEqual(loopback, ["ghcr-relay.linkease.net", "registry-relay.linkease.net"])

    def test_runtime_package_installs_gateway_domain_manifest(self):
        makefile = self.read("istoreenhance/Makefile")
        self.assertIn("./files/gateway-domains.conf", makefile)
        self.assertIn("$(1)/usr/share/kspeeder/gateway-domains.conf", makefile)

    def test_gateway_mode_uses_manifest_and_manages_dnsmasq(self):
        config = self.read("istoreenhance/files/istoreenhance.config")
        init = self.read("istoreenhance/files/istoreenhance.init")

        self.assertIn("option gateway_mode '0'", config)
        self.assertIn("config_get_bool gateway_mode $1 gateway_mode 0", init)
        self.assertIn('GATEWAY_DOMAINS_FILE="/usr/share/kspeeder/gateway-domains.conf"', init)
        self.assertIn('GATEWAY_DNSMASQ_HOSTS="/tmp/kspeeder-gateway.hosts"', init)
        self.assertIn("render_gateway_dns_config", init)
        self.assertIn("apply_gateway_dns", init)
        self.assertIn("remove_gateway_dns", init)
        self.assertIn("register_gateway_hosts", init)
        self.assertIn("unregister_gateway_hosts", init)
        self.assertIn("addnhosts", init)
        self.assertIn("/etc/init.d/dnsmasq reload", init)
        self.assertIn('$1 == "gateway"', init)
        self.assertNotIn('address=/.linkease.net/', init)

    def test_dnsmasq_renderer_maps_gateway_domains_but_not_loopback_domains(self):
        init = ROOT / "istoreenhance/files/istoreenhance.init"
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            manifest = directory / "domains.conf"
            output = directory / "dnsmasq.conf"
            manifest.write_text(
                "gateway registry.linkease.net\n"
                "gateway dl-npm.linkease.net\n"
                "loopback registry-relay.linkease.net\n",
                encoding="utf-8",
            )
            script = f"""
                . {init}
                GATEWAY_DOMAINS_FILE={manifest}
                render_gateway_dns_config 192.168.9.1 {output}
            """
            result = subprocess.run(["sh", "-c", script], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "192.168.9.1 registry.linkease.net\n"
                "192.168.9.1 dl-npm.linkease.net\n",
            )

    def test_chinese_catalog_is_valid_gettext(self):
        msgfmt = shutil.which("msgfmt")
        if not msgfmt:
            self.skipTest("msgfmt is unavailable")
        catalog = ROOT / "luci-app-istoreenhance/po/zh-cn/istoreenhance.po"
        result = subprocess.run(
            [msgfmt, "--check", "-o", "/dev/null", str(catalog)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_luci_exposes_gateway_mode_and_both_domain_groups(self):
        cbi = self.read("luci-app-istoreenhance/luasrc/model/cbi/istoreenhance.lua")
        model = self.read("luci-app-istoreenhance/luasrc/model/istoreenhance.lua")

        self.assertIn('s:option(Flag, "gateway_mode"', cbi)
        self.assertIn("gateway_domains", cbi)
        self.assertIn("loopback_domains", cbi)
        self.assertIn("/usr/share/kspeeder/gateway-domains.conf", model)
        self.assertIn('kind == "gateway"', model)
        self.assertIn('kind == "loopback"', model)

    def test_default_entry_stays_on_luci_while_open_uses_shared_route(self):
        makefile = self.read("luci-app-istoreenhance/Makefile")
        controller = self.read("luci-app-istoreenhance/luasrc/controller/istoreenhance.lua")
        status = self.read("luci-app-istoreenhance/luasrc/view/istoreenhance_status.htm")
        meta_entry = self.read("app-meta-istoreenhance/entry.sh")
        meta_makefile = self.read("app-meta-istoreenhance/Makefile")

        self.assertIn("+luci-lib-linkeaseauth", makefile)
        self.assertIn("+linkease-app-entry", makefile)
        self.assertIn("PKG_VERSION:=0.9.1-r2", makefile)
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
        self.assertIn("PKG_VERSION:=0.9.1", makefile)
        self.assertIn("PKG_RELEASE:=1", makefile)
        self.assertIn("PKG_SOURCE:=ks-cli-binary-$(PKG_VERSION).tar.gz", makefile)
        self.assertIn(
            "PKG_SOURCE_URL:=https://github.com/kspeeder/docker_kspeeder/releases/download/v$(PKG_VERSION)/",
            makefile,
        )
        self.assertIn(
            "PKG_HASH:=1ec1474d59767d2d5feb48c39217b8409fa16831bd87c7c777d5359c2ceb05d6",
            makefile,
        )
        self.assertIn("DEPENDS:=@(arm||x86_64||aarch64)", makefile)
        self.assertNotRegex(makefile, r"PKGARCH\s*:?=\s*all")

    def test_ks_cli_install_selects_the_target_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            sdk = Path(directory)
            (sdk / "rules.mk").touch()
            (sdk / "package.mk").touch()
            build = sdk / "build/ks-cli-binary-0.9.1"
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
