import json
import pathlib
import stat
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HUB = ROOT.parents[1]


class KimiCodeContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text()

    def test_fixed_node_release_uses_mise_without_lifecycle_scripts(self):
        recipe = self.read("kimi/Makefile")
        runtime = self.read("kimi/files/kimi-runtime.lua")
        package = self.read("kimi/files/kimi-package.lua")
        self.assertIn("PKG_VERSION:=2.7.3", recipe)
        self.assertIn("PKG_RELEASE:=4", recipe)
        self.assertIn("@moonshot-ai/kimi-code", runtime)
        self.assertIn("candidate.version=='24.22.1'", runtime)
        self.assertIn("'--ignore-scripts'", package)
        self.assertIn("binding.instance,'node',entry", package)
        self.assertIn("/.kimi-code", runtime)
        self.assertNotIn("@latest", package)
        self.assertIn("function M.orchestrator_home()", runtime)
        self.assertIn("R.orchestrator_home()", package)
        self.assertIn("AGENTFLOW_PROVIDER_MODE", runtime)
        self.assertIn("function M.provider_status(value)", package)
        self.assertIn("action=='provider-status'", self.read("kimi/files/runtime-cli.lua"))

    def test_terminal_and_gateway_are_private_and_authenticated(self):
        init = self.read("kimi/files/kimi.init")
        manifest = json.loads(self.read("kimi/files/kimi-plugin.json"))
        self.assertIn("-i 127.0.0.1", init)
        self.assertIn("procd_set_param user kimi", init)
        self.assertIn("-b /apps/kimi", init)
        self.assertEqual(manifest["auth"]["mode"], "default")
        self.assertEqual(manifest["backend"]["host"], "127.0.0.1")
        for relative in ("kimi/files/kimi", "kimi/files/kimi-runtime", "kimi/files/kimi.init"):
            self.assertTrue((ROOT / relative).stat().st_mode & stat.S_IXUSR, relative)

    def test_luci_is_one_page_and_agentflow_is_optional(self):
        controller = self.read("luci-app-kimi/luasrc/controller/kimi.lua")
        status = self.read("luci-app-kimi/luasrc/view/kimi/status.htm")
        self.assertIn("require_post_csrf", controller)
        self.assertIn('ipairs({ "terminal", "agentflow" })', controller)
        self.assertIn("kimi login", status)
        self.assertIn("?id=kimi", status)
        self.assertIn("安装 AgentFlow 后使用", status)
        self.assertNotIn("credentials", controller)

    def test_registration_and_sync_are_owned_by_plugin(self):
        recipe = self.read("kimi/Makefile")
        agent = json.loads(self.read("kimi/files/kimi-agent.json"))
        sync = (HUB / "syncapps.yaml").read_text()
        self.assertIn("/usr/share/linkease/apps.d/38-kimi.json", recipe)
        self.assertIn("    kimi:\n", sync)
        self.assertIn("apps/kimi/luci-app-kimi", sync)
        self.assertEqual(agent["manageUrl"], "/cgi-bin/luci/admin/services/kimi")


if __name__ == "__main__":
    unittest.main()
