import json
import pathlib
import stat
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HUB = ROOT.parents[1]


class OpenCodeContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text()

    def test_fixed_native_musl_release_uses_safe_baseline(self):
        recipe = self.read("opencode/Makefile")
        runtime = self.read("opencode/files/opencode-runtime.lua")
        package = self.read("opencode/files/opencode-package.lua")
        self.assertIn("PKG_VERSION:=2.4.1", recipe)
        self.assertIn("PKG_RELEASE:=4", recipe)
        self.assertIn("@opencode/cli-linux-x64-baseline-musl", runtime)
        self.assertIn("@opencode/cli-linux-arm64-musl", runtime)
        self.assertIn("candidate.version=='24.22.1'", runtime)
        self.assertIn("'--ignore-scripts'", package)
        self.assertIn("'--omit=optional'", package)
        self.assertIn("'/usr/bin/su'", package)
        self.assertIn("'auth','list','--format','json'", package)
        self.assertNotIn("R.package..'@'..R.version", package)
        self.assertNotIn("@latest", package)
        self.assertIn("function M.orchestrator_home()", runtime)
        self.assertIn("R.orchestrator_home()", package)
        self.assertIn("AGENTFLOW_PROVIDER_MODE", runtime)
        self.assertIn("function M.provider_status(value)", package)
        self.assertIn("action=='provider-status'", self.read("opencode/files/runtime-cli.lua"))

    def test_terminal_and_gateway_are_private_and_authenticated(self):
        init = self.read("opencode/files/opencode.init")
        manifest = json.loads(self.read("opencode/files/opencode-plugin.json"))
        self.assertIn("-i 127.0.0.1", init)
        self.assertIn("procd_set_param user opencode", init)
        self.assertIn("-b /apps/opencode", init)
        self.assertEqual(manifest["auth"]["mode"], "default")
        self.assertEqual(manifest["backend"]["host"], "127.0.0.1")
        for relative in ("opencode/files/opencode", "opencode/files/opencode-runtime", "opencode/files/opencode.init"):
            self.assertTrue((ROOT / relative).stat().st_mode & stat.S_IXUSR, relative)

    def test_luci_is_one_page_and_agentflow_is_optional(self):
        controller = self.read("luci-app-opencode/luasrc/controller/opencode.lua")
        status = self.read("luci-app-opencode/luasrc/view/opencode/status.htm")
        self.assertIn("require_post_csrf", controller)
        self.assertIn('ipairs({ "terminal", "agentflow" })', controller)
        self.assertIn("opencode auth login", status)
        self.assertIn("?id=opencode", status)
        self.assertIn("安装 AgentFlow 后使用", status)
        self.assertNotIn("auth.json", controller)

    def test_missing_runtime_storage_has_an_actionable_luci_path(self):
        runtime = self.read("opencode/files/opencode-runtime.lua")
        package = self.read("opencode/files/opencode-package.lua")
        controller = self.read("luci-app-opencode/luasrc/controller/opencode.lua")
        status = self.read("luci-app-opencode/luasrc/view/opencode/status.htm")
        luci_recipe = self.read("luci-app-opencode/Makefile")
        meta_recipe = self.read("app-meta-opencode/Makefile")

        self.assertIn("storage_configured", package)
        self.assertIn("Configure persistent storage in Runtime Environments", runtime)
        self.assertIn('next = "runtime-storage"', controller)
        self.assertIn("opencode-storage-guide", status)
        self.assertIn("先配置运行时存储", status)
        self.assertIn("前往运行时环境", status)
        self.assertIn("!storageReady", status)
        self.assertIn("PKG_VERSION:=0.1.0-r3", luci_recipe)
        self.assertIn("PKG_RELEASE:=5", meta_recipe)

    def test_registration_and_sync_are_owned_by_plugin(self):
        recipe = self.read("opencode/Makefile")
        agent = json.loads(self.read("opencode/files/opencode-agent.json"))
        sync = (HUB / "syncapps.yaml").read_text()
        self.assertIn("/usr/share/linkease/apps.d/37-opencode.json", recipe)
        self.assertIn("    opencode:\n", sync)
        self.assertIn("apps/opencode/luci-app-opencode", sync)
        self.assertEqual(agent["manageUrl"], "/cgi-bin/luci/admin/services/opencode")


if __name__ == "__main__":
    unittest.main()
