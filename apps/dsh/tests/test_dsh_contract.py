import json
import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DshContract(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_runtime_profiles_are_pinned_and_explicit(self):
        script = self.read("dsh/files/dsh.sh")
        config = self.read("dsh/files/dsh.config")
        cbi = self.read("luci-app-dsh/luasrc/model/cbi/dsh.lua")

        self.assertIn("option image_profile 'standard'", config)
        self.assertIn("option extra_trusted_hosts '*'", config)
        self.assertIn("case \"${1:-standard}\"", script)
        self.assertIn("ghcr.io/omdsh-dev/dsh-container:0.2.1-rc.2@sha256:", script)
        self.assertIn("ghcr.io/runzhliu/deepseek-harness:0.2.3-alpha.2-r1@sha256:", script)
        self.assertNotIn(":latest", script)
        self.assertIn('profile:value("standard"', cbi)
        self.assertIn('profile:value("advanced"', cbi)

    def test_advanced_profile_protects_the_browser_desktop(self):
        script = self.read("dsh/files/dsh.sh")
        caddy = self.read("dsh/files/advanced.Caddyfile")

        self.assertIn('GATEWAY_NAME="dsh-gateway"', script)
        self.assertIn('ADVANCED_NETWORK="dsh-internal"', script)
        self.assertIn('--shm-size 1g', script)
        self.assertIn('--publish "$port:13080"', script)
        self.assertIn('--cap-add NET_BIND_SERVICE', script)
        self.assertEqual(script.count('--cap-add NET_BIND_SERVICE'), 1)
        self.assertNotIn('--publish "$port:6080"', script)
        self.assertNotIn('--publish "$port:9222"', script)
        self.assertIn('advanced_data_path="${data_path}-advanced"', script)
        self.assertIn("forward_auth dsh:3080", caddy)
        self.assertIn("header_up -Upgrade", caddy)
        self.assertIn("header_up -Origin", caddy)
        self.assertIn('basic_auth bcrypt "DSH administrator"', caddy)
        self.assertIn("dsh {$DSH_PASSWORD_HASH}", caddy)
        self.assertIn("/?token={$DSH_LAUNCH_TOKEN}", caddy)
        self.assertGreaterEqual(caddy.count("header_up Host {http.request.hostport}"), 5)
        self.assertNotIn("/cgi-bin/luci/admin/services/dsh/open", caddy)
        self.assertIn("reverse_proxy dsh:6080", caddy)
        self.assertIn("reverse_proxy dsh:3080", caddy)
        self.assertIn("@desktop path /novnc-*", caddy)

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
        self.assertIn("do_launch_token", script)
        self.assertIn('docker logs --tail 300 "$CONTAINER_NAME"', script)
        self.assertIn("*[!A-Za-z0-9.,:_%_-]*", script)
        self.assertIn('KEY_FILE="$KEY_DIRECTORY/admin.key"', script)
        self.assertIn("ensure_admin_key", script)
        self.assertIn("hexdump -n 32", script)
        self.assertNotIn("od -An", script)
        self.assertIn('chmod 0600 "$KEY_FILE"', script)
        self.assertIn('--env "DSH_PASSWORD_HASH=$password_hash"', script)
        self.assertIn('--env "DSH_LAUNCH_TOKEN=$launch_token"', script)
        self.assertIn("hash-password --algorithm bcrypt", script)
        self.assertIn("do_refresh_gateway", script)
        self.assertIn("do_boot", script)
        self.assertIn('case "$address" in 0.0.0.0|::)', script)
        self.assertIn('[ "$value" = "*" ] && return 0', script)
        self.assertIn("''|'*')", script)
        self.assertLess(
            script.index('trusted_hosts_value="$(trusted_hosts "$extra_hosts")"'),
            script.index("IFS=,"),
        )

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
        self.assertIn('translate("Administrator username")', cbi)
        self.assertIn('return "dsh"', cbi)
        self.assertIn('administrator_username:depends("image_profile", "advanced")', cbi)
        self.assertIn("dsh-facts", status)
        self.assertIn("Runtime details", status)
        self.assertNotIn("dsh-status-row", status)

    def test_package_ownership_and_dependencies(self):
        runtime = self.read("dsh/Makefile")
        luci = self.read("luci-app-dsh/Makefile")
        meta = self.read("app-meta-dsh/Makefile")
        autoconf_path = ROOT / "app-meta-dsh/config.sh"

        self.assertIn("+docker +dockerd +ca-bundle +linkease-app-entry", runtime)
        self.assertIn("./files/advanced.Caddyfile", runtime)
        self.assertIn("./files/dsh.init", runtime)
        self.assertIn("/usr/share/linkease/apps.d/39-dsh.json", runtime)
        self.assertIn("+luci-lib-linkeaseauth +linkease-app-entry", luci)
        self.assertIn("META_DEPENDS:=+dsh +luci-app-dsh", meta)
        self.assertIn("META_AUTOCONF:=path enable", meta)
        self.assertTrue(autoconf_path.is_file())
        autoconf = autoconf_path.read_text(encoding="utf-8")
        self.assertTrue(autoconf.startswith("#!/bin/sh\n"))
        self.assertIn('data_path="$ISTORE_CONF_DIR/DSH"', autoconf)
        self.assertIn('workspace_path="$ISTORE_PUBLIC_DIR/DSH"', autoconf)
        self.assertIn("/usr/libexec/istorec/dsh.sh", autoconf)
        self.assertNotIn("linkease/apps.d", meta)

    def test_shell_is_syntactically_valid(self):
        for relative in (
            "dsh/files/dsh.sh",
            "dsh/files/dsh.init",
            "app-meta-dsh/config.sh",
            "tests/device_acceptance.sh",
            "tests/device_acceptance_advanced.sh",
        ):
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

        advanced = self.read("tests/device_acceptance_advanced.sh")
        self.assertIn("FINAL_DSH_ADVANCED_ACCEPTANCE=PASS", advanced)
        self.assertIn("novnc_unauth", advanced)
        self.assertIn("authenticated asset returned", advanced)
        self.assertIn("DSH administrator key", advanced)
        self.assertNotIn("docker logs", advanced)

        browser = self.read("tests/browser_acceptance_advanced.mjs")
        self.assertIn("FINAL_DSH_ADVANCED_BROWSER", browser)
        self.assertIn("Network.setExtraHTTPHeaders", browser)
        self.assertNotIn("launch-token", browser)

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
