import json
import pathlib
import stat
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
HUB = ROOT.parents[1]


class CodexContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text()

    def test_runtime_is_pinned_and_uses_mise(self):
        recipe = self.read("codex/Makefile")
        runtime = self.read("codex/files/codex-runtime.lua")
        package = self.read("codex/files/codex-package.lua")
        self.assertIn("PKG_VERSION:=0.172.0", recipe)
        self.assertIn("PKG_RELEASE:=4", recipe)
        self.assertIn("+mise-runtime", recipe)
        self.assertIn("group_add_next codex", recipe)
        self.assertIn("version='0.172.0'", runtime)
        self.assertIn("candidate.abi=='musl'", runtime)
        self.assertIn("candidate.version=='24.22.1'", runtime)
        self.assertIn("n.getpwnam or n.getpw", runtime)
        self.assertIn("'--ignore-scripts'", package)
        self.assertIn("codex-path/rg", package)
        self.assertIn("fs.chmod(path,'755')", package)
        self.assertIn("define Build/Compile", recipe)
        self.assertNotIn("@latest", package)
        self.assertIn("function M.orchestrator_home()", runtime)
        self.assertIn("R.orchestrator_home()", package)
        self.assertIn("AGENTFLOW_PROVIDER_MODE", runtime)
        self.assertIn("home .. '/.codex'", runtime)
        self.assertIn("function M.provider_status(value)", package)
        self.assertIn("action=='provider-status'", self.read("codex/files/runtime-cli.lua"))

    def test_terminal_is_loopback_and_unprivileged(self):
        init = self.read("codex/files/codex.init")
        self.assertIn("-i 127.0.0.1", init)
        self.assertIn("procd_set_param user codex", init)
        self.assertIn("CODEX_DATA_DIR=", init)
        self.assertIn("CODEX_WORKSPACE_DIR=", init)
        self.assertIn("-b /apps/codex", init)
        self.assertNotIn("kill -9", init)
        manifest = json.loads(self.read("codex/files/codex-plugin.json"))
        self.assertEqual(manifest["backend"]["host"], "127.0.0.1")
        self.assertEqual(manifest["backend"]["proxyMode"], "app-base")
        self.assertEqual(manifest["auth"]["mode"], "default")
        for relative in ("codex/files/codex", "codex/files/codex-runtime", "codex/files/codex.init"):
            self.assertTrue((ROOT / relative).stat().st_mode & stat.S_IXUSR, relative)

    def test_credentials_are_not_exposed_by_luci(self):
        controller = self.read("luci-app-codex/luasrc/controller/codex.lua")
        status = self.read("luci-app-codex/luasrc/view/codex/status.htm")
        self.assertNotIn("auth.json", controller)
        self.assertNotIn("OPENAI_API_KEY", controller)
        self.assertIn("codex login --device-auth", status)
        self.assertIn("require_post_csrf", controller)
        self.assertIn('object = "luci-app-codex"', controller)

    def test_luci_is_a_single_management_page(self):
        controller = self.read("luci-app-codex/luasrc/controller/codex.lua")
        status = self.read("luci-app-codex/luasrc/view/codex/status.htm")
        self.assertNotIn('template("codex/terminal")', controller)
        self.assertNotIn('template("codex/agentflow")', controller)
        self.assertIn('ipairs({ "terminal", "agentflow" })', controller)
        self.assertIn('http.status(404, "Not Found")', controller)
        self.assertFalse((ROOT / "luci-app-codex/luasrc/view/codex/terminal.htm").exists())
        self.assertFalse((ROOT / "luci-app-codex/luasrc/view/codex/agentflow.htm").exists())
        self.assertNotIn("codex-data", status)
        self.assertNotIn("codex-workspace", status)
        self.assertIn("linkease_apps/open", status)
        self.assertIn("?id=codex", status)

    def test_agentflow_is_optional(self):
        meta = self.read("app-meta-codex/Makefile")
        view = self.read("luci-app-codex/luasrc/view/codex/status.htm")
        agent = json.loads(self.read("codex/files/codex-agent.json"))
        self.assertNotIn("agentflow", meta.lower())
        self.assertIn("codexAgentFlow", view)
        self.assertIn("?id=agentflow", view)
        self.assertIn("安装 AgentFlow 后使用", view)
        self.assertEqual(agent["command"], "/usr/bin/codex")
        self.assertEqual(agent["manageUrl"], "/cgi-bin/luci/admin/services/codex")

    def test_registration_is_owned_by_runtime(self):
        recipe = self.read("codex/Makefile")
        self.assertIn("/usr/share/linkease/apps.d/35-codex.json", recipe)
        self.assertIn("/usr/share/codex/codex-plugin.json", recipe)
        self.assertNotIn("linkease/apps.d", self.read("app-meta-codex/Makefile"))

    def test_sync_mapping_exists(self):
        sync = (HUB / "syncapps.yaml").read_text()
        self.assertIn("    codex:\n", sync)
        self.assertIn("apps/codex/codex", sync)
        self.assertIn("apps/codex/luci-app-codex", sync)
        self.assertIn("apps/codex/app-meta-codex", sync)


if __name__ == "__main__":
    unittest.main()
