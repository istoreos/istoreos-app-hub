from pathlib import Path
import json
import os
import re
import shlex
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FastNetPackageContractTest(unittest.TestCase):
    def translation_versions(self, apk, sdk_translation=None):
        # Expand the actual recipe; the SDK stub optionally supplies its default.
        with tempfile.TemporaryDirectory() as directory:
            sdk = Path(directory)
            (sdk / "feeds/luci").mkdir(parents=True)
            (sdk / "rules.mk").touch()
            (sdk / "feeds/luci/luci.mk").write_text(
                "PKG_PO_VERSION?=" + sdk_translation + "\n" if sdk_translation else ""
            )
            harness = sdk / "versions.mk"
            harness.write_text(
                f"include {ROOT / 'luci-app-fastnet/Makefile'}\n"
                "versions:\n\t@printf '%s\\n' '$(PKG_VERSION)' '$(PKG_PO_VERSION)'\n"
            )
            return subprocess.check_output(
                ["make", "--no-print-directory", "-f", str(harness), "versions",
                 f"TOPDIR={sdk}", "CONFIG_USE_APK=" + ("y" if apk else "")],
                text=True,
            ).splitlines()

    def test_apk_translation_version_is_owned_by_sdk(self):
        _, translation = self.translation_versions(apk=True)
        self.assertEqual(translation, "", "APK recipe must not override SDK translation versioning")
        command = os.environ.get("APK_VERSION_COMMAND")
        for sdk_version in ("26.315.12345~abcdef0", "0.261112.12345"):
            with self.subTest(sdk_version=sdk_version):
                _, translation = self.translation_versions(apk=True, sdk_translation=sdk_version)
                self.assertEqual(translation, sdk_version)
                if command:
                    result = subprocess.run(shlex.split(command) + [translation],
                                            text=True, capture_output=True, timeout=20)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_opkg_translation_version_is_owned_by_sdk(self):
        _, translation = self.translation_versions(apk=False)
        self.assertEqual(translation, "", "OPKG recipe must not override SDK translation versioning")
        for sdk_version in ("git-26.181.32799-853c877", "26.315.12345~abcdef0"):
            with self.subTest(sdk_version=sdk_version):
                _, translation = self.translation_versions(apk=False, sdk_translation=sdk_version)
                self.assertEqual(translation, sdk_version)

    def test_release_versions_and_binary_contract_are_aligned(self):
        runtime = (ROOT / "fastnet/Makefile").read_text(encoding="utf-8")
        luci = (ROOT / "luci-app-fastnet/Makefile").read_text(encoding="utf-8")
        meta = (ROOT / "app-meta-fastnet/Makefile").read_text(encoding="utf-8")

        source_version = re.search(r"^PKG_VERSION:=(.+)$", runtime, re.MULTILINE)
        source_release = re.search(r"^PKG_RELEASE:=(.+)$", runtime, re.MULTILINE)
        luci_version = re.search(r"^PKG_VERSION:=(.+)$", luci, re.MULTILINE)
        luci_release = re.search(r"^PKG_RELEASE:=([^\r\n]*)$", luci, re.MULTILINE)
        meta_version = re.search(r"^PKG_VERSION:=(.+)$", meta, re.MULTILINE)
        meta_release = re.search(r"^PKG_RELEASE:=(.+)$", meta, re.MULTILINE)
        source_hash = re.search(r"^PKG_HASH:=([0-9a-f]{64})$", runtime, re.MULTILINE)

        self.assertIsNotNone(source_version)
        self.assertIsNotNone(source_release)
        self.assertIsNotNone(luci_version)
        self.assertIsNotNone(luci_release)
        self.assertIsNotNone(meta_version)
        self.assertIsNotNone(meta_release)
        self.assertIsNotNone(source_hash)
        self.assertEqual(luci_version.group(1), f"{source_version.group(1)}-r2")
        self.assertEqual(luci_release.group(1), "")
        self.assertEqual(meta_version.group(1), source_version.group(1))
        self.assertEqual(meta_release.group(1), "21")
        self.assertIn(
            "istoreos-app-hub/releases/download/fastnet-runtime-v$(PKG_VERSION)/",
            runtime,
        )
        self.assertIn(
            "$(PKG_BUILD_DIR)/FastNet.$(PKG_ARCH_FASTNET)",
            runtime,
        )
        self.assertNotIn("PKGARCH:=all", runtime)

    def test_app_meta_keeps_lan_target_and_registers_same_origin_gateway(self):
        manifest_path = ROOT / "fastnet/files/fastnet-plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["id"], "fastnet")
        self.assertNotIn("staticRoot", manifest)
        self.assertEqual(manifest["backend"], {
            "type": "http", "scheme": "http", "host": "127.0.0.1",
            "portFromUci": "fastnet.@fastnet[0].port", "defaultPort": 3200,
            "upstreamBasePath": "/", "pathMode": "strip-public-base",
        })

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
        self.assertEqual(manifest["standalone"]["basePath"], "/apps/fastnet/")
        self.assertNotIn("defaultPort", manifest["standalone"]["externalOpen"])

    def test_luci_open_routes_through_the_shared_auth_entry(self):
        makefile = (ROOT / "luci-app-fastnet/Makefile").read_text(encoding="utf-8")
        meta = (ROOT / "app-meta-fastnet/Makefile").read_text(encoding="utf-8")
        controller = (ROOT / "luci-app-fastnet/luasrc/controller/fastnet.lua").read_text(encoding="utf-8")
        model = (ROOT / "luci-app-fastnet/luasrc/model/cbi/fastnet.lua").read_text(encoding="utf-8")

        self.assertIn("+luci-lib-linkeaseauth", makefile)
        self.assertIn("+linkease-app-entry", makefile)
        self.assertIn("META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/fastnet", meta)
        self.assertNotIn("META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/linkease_apps/open", meta)
        self.assertIn('"fastnet", "embed") .. "?standalone=1"', controller)
        self.assertIn('http = require "luci.http"', controller)
        self.assertIn('resolver = require("luci.model.linkease.apps_openwrt").new()', controller)
        self.assertIn('auth_url = dispatcher.build_url("admin", "services", "linkease_auth", "auth")', controller)
        self.assertIn('dispatcher.build_url("admin", "services", "linkease_apps", "open") .. "?id=fastnet"', model)


if __name__ == "__main__":
    unittest.main()
