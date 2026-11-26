import json
import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DshContract(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_runtime_profile_is_pinned_and_extensible(self):
        script = self.read("dsh/files/dsh.sh")
        config = self.read("dsh/files/dsh.config")
        cbi = self.read("luci-app-dsh/luasrc/model/cbi/dsh.lua")

        self.assertIn("option image_profile 'standard'", config)
        self.assertIn("option extra_trusted_hosts '*'", config)
        self.assertIn("case \"${1:-standard}\"", script)
        self.assertIn("ghcr.io/omdsh-dev/dsh-container:0.2.1-rc.2@sha256:", script)
        self.assertNotIn(":latest", script)
        self.assertNotIn("runzhliu/deepseek-harness", script)
        self.assertIn('profile:value("standard"', cbi)
        self.assertNotIn('profile:value("advanced"', cbi)

    def test_container_uses_a_dedicated_authenticated_port(self):
        script = self.read("dsh/files/dsh.sh")
        for fragment in (
            '--publish "$port:3080"',
            '--env "DSH_CONTAINER_KEY=$admin_key"',
            "--read-only",
            "--cap-drop ALL",
            "--security-opt no-new-privileges:true",
            "--pids-limit 1024",
            "--tmpfs /tmp:rw,exec,nosuid,nodev,size=512m,mode=1777",
            'src=$workspace_path,dst=/home/node',
            'src=$data_path,dst=/home/node/.dsh',
        ):
            self.assertIn(fragment, script)
        self.assertNotIn("--privileged", script)
        self.assertNotIn("/var/run/docker.sock", script)
        self.assertNotIn("eval ", script)
        self.assertNotIn("docker logs", script)
        self.assertIn("*[!A-Za-z0-9.,:_%_-]*", script)
        self.assertIn('KEY_FILE="$KEY_DIRECTORY/admin.key"', script)
        self.assertIn("ensure_admin_key", script)
        self.assertIn("hexdump -n 32", script)
        self.assertNotIn("od -An", script)
        self.assertIn('chmod 0600 "$KEY_FILE"', script)
        self.assertIn('case "$address" in 0.0.0.0|::)', script)
        self.assertIn('[ "$value" = "*" ] && return 0', script)
        self.assertIn("''|'*')", script)

    def test_replacement_has_health_gate_and_rollback(self):
        script = self.read("dsh/files/dsh.sh")
        self.assertIn('ROLLBACK_NAME="dsh-rollback"', script)
        self.assertIn("docker rename \"$CONTAINER_NAME\" \"$ROLLBACK_NAME\"", script)
        self.assertIn("if ! wait_healthy", script)
        self.assertGreaterEqual(script.count("restore_previous"), 3)

    def test_root_path_is_native_and_has_no_html_rewrite(self):
        script = self.read("dsh/files/dsh.sh")
        acceptance = self.read("tests/device_acceptance.sh")
        self.assertNotIn("prepare_rebased_index", script)
        self.assertNotIn("auth-bootstrap.js", script)
        self.assertNotIn("dsh-index.html.new", script)
        self.assertNotIn("dst=$UPSTREAM_INDEX", script)
        self.assertIn('"$BASE_URL/auth-bootstrap.js"', acceptance)

    def test_manifest_redirects_launcher_to_dedicated_root(self):
        manifest = json.loads(self.read("dsh/files/dsh-plugin.json"))
        self.assertEqual(manifest["id"], "dsh")
        self.assertEqual(manifest["auth"]["mode"], "passthrough")
        self.assertEqual(manifest["standalone"]["basePath"], "/apps/dsh/")
        self.assertEqual(manifest["desktop"]["target"]["path"], "/")
        self.assertNotIn("backend", manifest)
        self.assertEqual(
            manifest["desktop"]["target"]["port"]["keys"]["uci"],
            "dsh.@main[0].port",
        )

    def test_luci_prioritizes_access_storage_and_runtime(self):
        cbi = self.read("luci-app-dsh/luasrc/model/cbi/dsh.lua")
        status = self.read("luci-app-dsh/luasrc/view/dsh/status.htm")

        self.assertIn('section:tab("access"', cbi)
        self.assertIn('section:tab("storage"', cbi)
        self.assertIn('section:tab("runtime"', cbi)
        self.assertIn('trusted_hosts.default = "*"', cbi)
        self.assertIn('value ~= "*"', cbi)
        self.assertIn("dsh-facts", status)
        self.assertIn("Runtime details", status)
        self.assertNotIn("dsh-status-row", status)

    def test_package_ownership_and_dependencies(self):
        runtime = self.read("dsh/Makefile")
        luci = self.read("luci-app-dsh/Makefile")
        meta = self.read("app-meta-dsh/Makefile")

        self.assertIn("+docker +dockerd +ca-bundle +linkease-app-entry", runtime)
        self.assertIn("/usr/share/linkease/apps.d/39-dsh.json", runtime)
        self.assertIn("+luci-lib-linkeaseauth +linkease-app-entry", luci)
        self.assertIn("META_DEPENDS:=+dsh +luci-app-dsh", meta)
        self.assertNotIn("linkease/apps.d", meta)

    def test_shell_is_syntactically_valid(self):
        for relative in ("dsh/files/dsh.sh", "tests/device_acceptance.sh"):
            result = subprocess.run(
                ["sh", "-n", str(ROOT / relative)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, f"{relative}: {result.stderr}")

    def test_device_acceptance_keeps_secrets_out_of_output(self):
        script = self.read("tests/device_acceptance.sh")
        self.assertIn('--data-urlencode "key@$KEY_FILE"', script)
        self.assertIn("dsh_container_session=", script)
        self.assertNotIn("docker logs", script)
        self.assertNotIn('cat "$KEY_FILE"', script)
        self.assertIn("FINAL_DSH_DEVICE_ACCEPTANCE=PASS", script)

    def test_kaiplus_provider_fixture_contains_no_credential(self):
        overlay = self.read("tests/fixtures/kaiplus-provider.patch.yml")
        self.assertIn("apiKeyEnv: KOOLCENTER_API_KEY", overlay)
        self.assertIn("api: openai-completions", overlay)
        self.assertIn("baseURL: https://token.koolcenter.com/v1", overlay)
        self.assertIn("provider: kaiplus", overlay)
        self.assertIn("model: qwen3.8-flash", overlay)
        self.assertNotIn("KOOLCENTER_API_KEY=", overlay)
        self.assertNotRegex(overlay, r"(?i)(api[_-]?key|token):\s+\S")


if __name__ == "__main__":
    unittest.main()
