#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
LUCI = APP / "luci-app-hermes"
SHARE = LUCI / "root/usr/share/hermes"
POLICY = SHARE / "runtime-policy.json"
CATALOG = ROOT / "mise/mise-runtime/files/catalog.json"


def canonical_digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class NativeRuntimeContract(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(POLICY.read_text())
        self.catalog = json.loads(CATALOG.read_text())

    def test_policy_is_fully_pinned(self):
        self.assertEqual(self.policy["schema_version"], 1)
        self.assertRegex(self.policy["python"]["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(self.policy["python"]["abi"], "musl")
        for product in ("agent", "webui"):
            item = self.policy[product]
            self.assertRegex(item["commit"], r"^[a-f0-9]{40}$")
            self.assertRegex(item["sha256"], r"^[a-f0-9]{64}$")
            self.assertNotIn("latest", item["url"])
            self.assertNotRegex(item["url"], r"/(main|master)(/|\.)")
        self.assertRegex(self.policy["uv"]["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(set(self.policy["uv"]["artifacts"]), {"aarch64", "x86_64"})
        for artifact in self.policy["uv"]["artifacts"].values():
            self.assertRegex(artifact["sha256"], r"^[a-f0-9]{64}$")
        pyyaml = self.policy["webui"]["pyyaml"]
        self.assertRegex(pyyaml["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(set(pyyaml["artifacts"]), {"aarch64", "x86_64"})
        for artifact in pyyaml["artifacts"].values():
            self.assertRegex(artifact["sha256"], r"^[a-f0-9]{64}$")
            self.assertTrue(artifact["url"].endswith(".whl"))
            self.assertEqual(artifact["filename"], artifact["url"].rsplit("/", 1)[-1])

    def test_python_policy_has_both_architectures(self):
        policy = self.policy["python"]
        selected = [
            entry
            for entry in self.catalog["entries"]
            if entry["tool"] == "python"
            and entry["version"] == policy["version"]
            and entry["build"] == policy["build"]
            and entry["abi"] == policy["abi"]
        ]
        self.assertEqual({entry["arch"] for entry in selected}, {"x86_64", "aarch64"})
        for entry in selected:
            self.assertEqual(entry["availability"], "available")
            self.assertEqual(entry["layout"], "python")
            self.assertEqual(entry["artifact_set"], canonical_digest(entry["artifacts"]))

    def test_catalog_revision_covers_new_entries(self):
        value = dict(self.catalog)
        revision = value.pop("revision")
        self.assertEqual(revision, canonical_digest(value))

    def test_native_implementation_has_no_docker_or_floating_sources(self):
        implementation = "\n".join(
            path.read_text()
            for path in (
                SHARE / "shared-runtime.lua",
                LUCI / "root/usr/libexec/istorec/hermes-native.sh",
            )
        )
        self.assertNotRegex(implementation, r"\bdocker\b")
        self.assertNotRegex(implementation, r"linkease/hermes:latest")
        self.assertIn("--frozen --all-packages --no-dev", implementation)
        self.assertIn("UV_PYTHON_DOWNLOADS=never", implementation)
        self.assertIn('CANDIDATE="$base/releases/$RELEASE"', implementation)
        self.assertNotIn('mv "$txn/candidate"', implementation)
        for required in (
            "dependency-client",
            "exec-user",
            "receipt_sha256",
            "--create-venv",
            "--venv",
            "HERMES_HOME",
            "HERMES_DISABLE_LAZY_INSTALLS=1",
            "candidate health port $port is already in use",
            "venv-runtime.json",
            "inspect \"$binding\"",
            "chown -R root:root",
        ):
            self.assertIn(required, implementation)

    def test_native_lifecycle_is_transactional_and_supervised(self):
        script = (
            LUCI / "root/usr/libexec/istorec/hermes-native.sh"
        ).read_text()
        init = (LUCI / "root/etc/init.d/hermes-native").read_text()
        for action in (
            "install",
            "upgrade",
            "start",
            "stop",
            "restart",
            "status",
            "health",
            "logs",
            "cancel",
            "recover",
            "remove",
            "purge",
        ):
            self.assertRegex(script, rf"\b{action}\)")
        for guard in (
            '"$RUNTIME" cancel "$TXN"',
            "Installation phase:",
            "restore_pointers",
            "prune_previous",
            "managed-by=hermes-native",
            "removed-runtime-data-preserved",
            "Refusing to purge an unmanaged directory",
        ):
            self.assertIn(guard, script)
        self.assertIn("procd_open_instance gateway", init)
        self.assertIn("procd_open_instance webui", init)
        self.assertIn("as-app", init)
        self.assertIn("HERMES_DISABLE_LAZY_INSTALLS=1", init)
        self.assertNotIn("procd_set_param user root", init)

    def test_downloads_survive_reboot_and_resume(self):
        implementation = (
            LUCI / "root/usr/libexec/istorec/hermes-native.sh"
        ).read_text()
        self.assertIn('curl --disable -fL -C -', implementation)
        self.assertIn('[ -f "$output.part" ]', implementation)
        self.assertIn('mv "$output.part" "$output"', implementation)
        self.assertNotIn('rm -f "$archive" "$archive.part"', implementation)
        self.assertNotIn('rm -f "$artifact" "$artifact.part"', implementation)

    def test_shell_and_lua_parse(self):
        subprocess.run(
            ["sh", "-n", str(LUCI / "root/usr/libexec/istorec/hermes-native.sh")],
            check=True,
        )
        subprocess.run(
            ["sh", "-n", str(LUCI / "root/etc/uci-defaults/99-hermes")],
            check=True,
        )
        subprocess.run(
            ["sh", "-n", str(LUCI / "root/etc/init.d/hermes-native")],
            check=True,
        )
        subprocess.run(["luac", "-p", str(SHARE / "shared-runtime.lua")], check=True)

    def test_runtime_rejects_unsafe_inputs_in_interface(self):
        source = (SHARE / "shared-runtime.lua").read_text()
        for guard in (
            "path:sub(1,5)=='/mnt/'",
            "part~='.'and part~='..'",
            "Hermes and shared runtime directories must not contain each other",
            "r.verified",
            "r.entry.arch==n.uname().machine",
            "Fixed Python receipt changed",
            "ref.state=='ready'",
        ):
            self.assertIn(guard, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
