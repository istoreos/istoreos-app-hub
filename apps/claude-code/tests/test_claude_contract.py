import json
import pathlib
import stat
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HUB = ROOT.parents[1]


class ClaudeCodeContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text()

    def test_fixed_native_musl_release_uses_mise_only_for_installation(self):
        recipe = self.read("claude-code/Makefile")
        runtime = self.read("claude-code/files/claude-runtime.lua")
        package = self.read("claude-code/files/claude-package.lua")
        self.assertIn("PKG_VERSION:=2.1.326", recipe)
        self.assertIn("PKG_RELEASE:=4", recipe)
        self.assertIn("@anthropic-ai/claude-code-linux-x64-musl", runtime)
        self.assertIn("@anthropic-ai/claude-code-linux-arm64-musl", runtime)
        self.assertIn("candidate.version=='24.22.1'", runtime)
        self.assertIn("'--ignore-scripts'", package)
        self.assertIn("'--omit=optional'", package)
        self.assertIn("'/usr/bin/su'", package)
        self.assertIn("fs.chmod(entry,'755')", package)
        self.assertNotIn("R.package..'@'..R.version", package)
        self.assertNotIn("@latest", package)
        self.assertIn("function M.orchestrator_home()", runtime)
        self.assertIn("R.orchestrator_home()", package)
        self.assertIn("AGENTFLOW_PROVIDER_MODE", runtime)
        self.assertIn("function M.provider_status(value)", package)
        self.assertIn("action=='provider-status'", self.read("claude-code/files/runtime-cli.lua"))

    def test_terminal_and_gateway_are_private_and_authenticated(self):
        init = self.read("claude-code/files/claude.init")
        manifest = json.loads(self.read("claude-code/files/claude-plugin.json"))
        self.assertIn("-i 127.0.0.1", init)
        self.assertIn("procd_set_param user claude", init)
        self.assertIn("-b /apps/claude-code", init)
        self.assertEqual(manifest["id"], "claude-code")
        self.assertEqual(manifest["auth"]["mode"], "default")
        self.assertEqual(manifest["backend"]["host"], "127.0.0.1")
        for relative in ("claude-code/files/claude", "claude-code/files/claude-runtime", "claude-code/files/claude.init"):
            self.assertTrue((ROOT / relative).stat().st_mode & stat.S_IXUSR, relative)

    def test_luci_is_one_page_and_does_not_expose_credentials(self):
        controller = self.read("luci-app-claude-code/luasrc/controller/claude.lua")
        status = self.read("luci-app-claude-code/luasrc/view/claude/status.htm")
        self.assertIn("require_post_csrf", controller)
        self.assertIn('object = "luci-app-claude-code"', controller)
        self.assertIn('ipairs({ "terminal", "agentflow" })', controller)
        self.assertIn('http.status(404, "Not Found")', controller)
        self.assertIn("claude auth login", status)
        self.assertIn("?id=claude-code", status)
        self.assertIn("安装 AgentFlow 后使用", status)
        self.assertNotIn("auth.json", controller)

    def test_registration_and_sync_are_owned_by_plugin(self):
        recipe = self.read("claude-code/Makefile")
        agent = json.loads(self.read("claude-code/files/claude-agent.json"))
        sync = (HUB / "syncapps.yaml").read_text()
        self.assertIn("/usr/share/linkease/apps.d/36-claude-code.json", recipe)
        self.assertEqual(agent["ownerPackage"], "claude-code")
        self.assertEqual(agent["manageUrl"], "/cgi-bin/luci/admin/services/claude")
        self.assertIn("    claude-code:\n", sync)
        self.assertIn("apps/claude-code/luci-app-claude-code", sync)


if __name__ == "__main__":
    unittest.main()
