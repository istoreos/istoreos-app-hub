#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]
APPS = APP.parent
LUCI = APP / "luci-app-hermes"
SCRIPTS = LUCI / "root/usr/libexec/istorec"


class DualBackendContract(unittest.TestCase):
    def read(self, path):
        return (APP / path).read_text()

    def test_docker_supply_chain_is_immutable_and_multi_arch(self):
        dockerfile = self.read("docker/Dockerfile")
        adapter = (SCRIPTS / "hermes-docker.sh").read_text()
        self.assertRegex(dockerfile.splitlines()[0], r"@sha256:[a-f0-9]{64}$")
        self.assertIn("ARG TARGETARCH", dockerfile)
        self.assertIn("amd64)", dockerfile)
        self.assertIn("arm64)", dockerfile)
        self.assertRegex(dockerfile, r"HERMES_AGENT_COMMIT=[a-f0-9]{40}")
        self.assertRegex(dockerfile, r"HERMES_WEBUI_COMMIT=[a-f0-9]{40}")
        self.assertNotIn("git clone", dockerfile)
        self.assertNotRegex(dockerfile + adapter, r"linkease/hermes:latest")
        self.assertNotRegex(adapter, r"\beval\b")
        self.assertNotIn("mise-runtime", adapter)
        self.assertRegex(adapter, r"IMAGE='linkease/hermes@sha256:[a-f0-9]{64}'")
        self.assertIn('docker rename "$CONTAINER" "$backup"', adapter)
        self.assertIn("restoring the previous container", adapter)

    def test_adapters_share_the_lifecycle_contract(self):
        native = (SCRIPTS / "hermes-native.sh").read_text()
        docker = (SCRIPTS / "hermes-docker.sh").read_text()
        for action in (
            "install",
            "upgrade",
            "start",
            "stop",
            "restart",
            "status",
            "health",
            "port",
            "remove",
            "rm",
        ):
            self.assertRegex(native, rf"(?:^|[|\t ]){action}(?:[|)])", action)
            self.assertRegex(docker, rf"(?:^|[|\t ]){action}(?:[|)])", action)
        for state in ("uninstalled", "running", "stopped", "degraded"):
            self.assertIn(state, native)
            self.assertIn(state, docker)

    def test_orchestrator_enforces_single_active_backend_and_rollback(self):
        source = (SCRIPTS / "hermes.sh").read_text()
        self.assertIn("target_backend", source)
        self.assertIn('"$(adapter "$other")" stop', source)
        self.assertIn("restore_backend", source)
        self.assertIn("restoring the previous backend", source)
        self.assertIn('"$DOCKER" pull', source)
        self.assertLess(source.index('"$DOCKER" pull'), source.index('"$NATIVE" stop'))
        self.assertIn("HERMES_NATIVE_ADAPTER", source)
        self.assertIn("HERMES_DOCKER_ADAPTER", source)

    def test_luci_exposes_native_and_docker_tabs(self):
        cbi = self.read("luci-app-hermes/luasrc/model/cbi/hermes.lua")
        view = self.read("luci-app-hermes/luasrc/view/hermes/status.htm")
        self.assertIn('s:tab("native"', cbi)
        self.assertIn('s:tab("docker"', cbi)
        self.assertIn('"target_backend"', cbi)
        self.assertIn('"native_base_dir"', cbi)
        self.assertIn('"data_path"', cbi)
        self.assertIn('"workspace_path"', cbi)
        self.assertIn("status-native", view)
        self.assertIn("status-docker", view)
        self.assertIn("Active backend", view)

    def test_fresh_install_defaults_to_native_without_docker_dependency(self):
        config = self.read("luci-app-hermes/root/etc/config/hermes")
        defaults = self.read("luci-app-hermes/root/etc/uci-defaults/99-hermes")
        recipe = self.read("luci-app-hermes/Makefile")
        self.assertIn("option 'backend' 'native'", config)
        self.assertIn("option 'target_backend' 'native'", config)
        self.assertIn("HermesNative", defaults)
        self.assertIn("HermesDocker/data", defaults)
        self.assertIn("HermesDocker/workspace", defaults)
        self.assertIn("pre-dual-backend conffile", defaults)
        self.assertIn("hermes.@main[0].backend=docker", defaults)
        self.assertIn("+mise-runtime", recipe)
        self.assertIn("mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)4)", recipe)
        self.assertNotRegex(recipe, r"(?:^|\s)\+docker(?:\s|$)")
        self.assertIn("PKG_VERSION:=1.0.1", recipe)
        self.assertIn("PKG_RELEASE:=1", recipe)

        runtime_recipe = (APPS / "mise/mise-runtime/Makefile").read_text()
        runtime_release = int(re.search(r"PKG_RELEASE:=(\d+)", runtime_recipe).group(1))
        self.assertGreaterEqual(runtime_release, 4)

    def test_shell_files_parse(self):
        for path in (
            SCRIPTS / "hermes.sh",
            SCRIPTS / "hermes-native.sh",
            SCRIPTS / "hermes-docker.sh",
            LUCI / "root/etc/uci-defaults/99-hermes",
            APP / "docker/entrypoint.sh",
        ):
            subprocess.run(["sh", "-n", str(path)], check=True)

    def test_installed_entrypoints_are_executable(self):
        for path in (
            SCRIPTS / "hermes.sh",
            SCRIPTS / "hermes-native.sh",
            SCRIPTS / "hermes-docker.sh",
            LUCI / "root/etc/init.d/hermes-native",
            LUCI / "root/etc/uci-defaults/99-hermes",
        ):
            self.assertTrue(path.stat().st_mode & 0o111, str(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
