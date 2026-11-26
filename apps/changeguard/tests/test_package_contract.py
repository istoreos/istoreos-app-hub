import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import unittest
import urllib.request
from pathlib import Path

H = Path(__file__).resolve().parents[3]
HELPER = H / "apps/changeguard/changeguard/files/usr/libexec/changeguard-package"


class Contract(unittest.TestCase):
    def test_runtime_recipes_use_tabs_and_immutable_release(self):
        for name, version, release in [("changeguard", "0.3.5", "4"), ("linkspace", "0.3.3", "3")]:
            recipe = (H / f"apps/{name}/{name}/Makefile").read_text()
            self.assertRegex(recipe, rf"(?m)^PKG_VERSION:={re.escape(version)}$")
            self.assertRegex(recipe, rf"(?m)^PKG_RELEASE:={release}$")
            self.assertIn(f"releases/download/{name}-runtime-v$(PKG_VERSION)/", recipe)
            match = re.search(rf"^define Package/{name}/install\n(.*?)^endef$", recipe, re.M | re.S)
            self.assertIsNotNone(match)
            for line in match.group(1).splitlines():
                if line.strip():
                    self.assertTrue(line.startswith("\t"), line)

    def test_one_product_identity_and_headless_dependencies(self):
        self.assertFalse(list((H / "apps/changeguard").glob("app-meta-*")))
        meta = (H / "apps/kaiplus/app-meta-kaiplus/Makefile").read_text()
        self.assertIn("+kaiplus", meta)
        mapping = re.split(r"\n    \S", (H / "syncapps.yaml").read_text().split("\n    changeguard:\n", 1)[1], maxsplit=1)[0]
        self.assertNotIn("app-meta-", mapping)
        self.assertIn("meta: []", mapping)
        self.assertFalse((H / "apps/optimemachine").exists())
        self.assertIn("+changeguard", (H / "apps/kaiplus/kaiplus/Makefile").read_text())
        self.assertIn("changeguard (>=0.3.5-$(if $(CONFIG_USE_APK),r)4)", (H / "apps/kaiplus/kaiplus/Makefile").read_text())
        self.assertIn("+linkspace", (H / "apps/changeguard/changeguard/Makefile").read_text())
        self.assertIn("linkspace (>=0.3.3-$(if $(CONFIG_USE_APK),r)3)", (H / "apps/changeguard/changeguard/Makefile").read_text())
        self.assertFalse(list((H / "apps/changeguard/changeguard/files").rglob("*plugin.json")))
        for name in ["changeguard", "linkspace"]:
            self.assertNotIn("optimemachine", (H / f"apps/{name}/{name}/Makefile").read_text())
        self.assertNotIn("optimemachine", HELPER.read_text())
        for obsolete in [
            H / "tools/build-optimemachine-candidate.py",
            H / "tools/build-changeguard-candidate.py",
        ]:
            if obsolete.exists():
                self.assertNotIn("optimemachine", obsolete.read_text())

    def test_offline_hooks_preserve_all_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            keep = root / "configuration"
            keep.write_text("unchanged")
            for phase in ["preinst", "postinst", "prerm"]:
                subprocess.run(["sh", str(HELPER), phase], env={**os.environ, "IPKG_INSTROOT": directory}, check=True)
            self.assertEqual(keep.read_text(), "unchanged")
            self.assertEqual(list(root.iterdir()), [keep])

    def test_native_lifecycle_stops_old_work_and_starts_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.json"
            config.write_text('{\n  "schemaVersion": 1,\n  "http": {\n    "listen": "0.0.0.0:8080"\n  },\n  "stateDir": "/tmp/state"\n}\n')
            log = root / "calls"
            binary = root / "changeguard_bin"
            binary.write_text('#!/bin/sh\nprintf "cli %s\\n" "$1" >> "$CG_TEST_LOG"\n[ "$1" != maintenance-check ]\n')
            binary.chmod(0o755)
            service = root / "service"
            service.write_text('#!/bin/sh\nprintf "service %s\\n" "$1" >> "$CG_TEST_LOG"\n')
            service.chmod(0o755)
            ucode = root / "ucode"
            ucode.write_text("#!/usr/bin/env python3\nimport json, sys\nvalue = json.load(sys.stdin)\nvalue.pop('http', None)\njson.dump(value, sys.stdout)\n")
            ucode.chmod(0o755)
            body = HELPER.read_text().replace("/usr/sbin/changeguard_bin", str(binary)).replace("/etc/init.d/changeguard", str(service)).replace("/etc/changeguard/config.json", str(config)).replace("/usr/bin/ucode", str(ucode))
            env = {**os.environ, "IPKG_INSTROOT": "", "CG_TEST_LOG": str(log)}

            subprocess.run(["sh", "-s", "preinst"], input=body, text=True, env=env, check=True)
            subprocess.run(["sh", "-s", "postinst"], input=body, text=True, env=env, check=True)

            self.assertEqual(log.read_text().splitlines(), [
                "service stop",
                "cli initialize",
                "cli sync-backend",
                "cli refresh-runtime",
                "service enable",
                "service restart",
            ])
            self.assertNotIn('"http"', config.read_text())
            migrated = json.loads(config.read_text())
            self.assertEqual(migrated, {"schemaVersion": 1, "stateDir": "/tmp/state"})
            self.assertNotIn("maintenance-check", HELPER.read_text())
            self.assertNotIn("/var/run/changeguard-package-", HELPER.read_text())

    def test_package_preinstall_does_not_delegate_to_the_old_helper(self):
        recipe = (H / "apps/changeguard/changeguard/Makefile").read_text()
        preinstall = re.search(r"define Package/changeguard/preinst\n(.*?)\nendef", recipe, re.S).group(1)
        self.assertNotIn("changeguard-package", preinstall)
        self.assertIn("ubus call service delete", preinstall)
        self.assertIn("killall changeguard_bin", preinstall)

    def test_service_stop_is_never_blocked_by_protection_state(self):
        init = (H / "apps/changeguard/changeguard/files/etc/init.d/changeguard").read_text()
        self.assertNotIn('case "$action"', init)
        self.assertNotIn("maintenance-check", init)

    def test_changeguard_and_linkspace_hooks_never_fail_package_transactions(self):
        for name in ["changeguard", "linkspace"]:
            recipe = (H / f"apps/{name}/{name}/Makefile").read_text()
            phases = ["postinst", "prerm"] if name == "changeguard" else ["preinst", "postinst", "prerm"]
            for phase in phases:
                with self.subTest(package=name, phase=phase), tempfile.TemporaryDirectory() as directory:
                    failing = Path(directory) / "changeguard-package"
                    failing.write_text("#!/bin/sh\nprintf '%s\\n' 'simulated helper failure' >&2\nexit 1\n")
                    failing.chmod(0o755)
                    body = re.search(rf"define Package/{name}/{phase}\n(.*?)\nendef", recipe, re.S).group(1)
                    body = body.replace("$${", "${").replace("$$?", "$?")
                    body = body.replace("/usr/libexec/changeguard-package", str(failing))
                    result = subprocess.run(
                        ["sh", "-s"],
                        input=body,
                        text=True,
                        env={**os.environ, "IPKG_INSTROOT": ""},
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("simulated helper failure", result.stderr)

    def test_runtime_only_postinst_work_is_best_effort(self):
        for name in ["agentflow", "kaiplus"]:
            recipe = (H / f"apps/{name}/{name}/Makefile").read_text()
            body = re.search(r"define Package/\$\(PKG_NAME\)/postinst\n(.*?)\nendef", recipe, re.S).group(1)
            self.assertNotRegex(body, r"(?:uci|/etc/init\.d/\S+) .*\|\| exit")
            self.assertRegex(body, r"(?m)^exit 0$")

    @unittest.skipUnless(os.environ.get("CG_VERIFY_PUBLIC_RELEASE"), "explicit public release verification required")
    def test_public_assets_match_hashes_and_layout(self):
        for name, version, executable in [("changeguard", "0.3.5", "changeguard_bin"), ("linkspace", "0.3.3", "linkspace")]:
            hashes = (H / f"apps/{name}/{name}/release.mk").read_text()
            for arch in ["x86_64", "aarch64"]:
                expected = re.search(rf"^{name.upper()}_HASH_{arch}:=([0-9a-f]{{64}})$", hashes, re.M).group(1)
                url = f"https://github.com/istoreos/istoreos-app-hub/releases/download/{name}-runtime-v{version}/{name}-{version}-{arch}.tar.gz"
                with urllib.request.urlopen(url, timeout=60) as response:
                    body = response.read()
                self.assertEqual(hashlib.sha256(body).hexdigest(), expected)
                with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as package:
                    names = package.getnames()
                self.assertIn(f"./{name}-{version}/{executable}", names)
                self.assertEqual(f"./{name}-{version}/dependency.json" in names, name == "linkspace")


if __name__ == "__main__":
    unittest.main()
