from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class KaiPlusOpenWrtContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_config_defaults_to_standalone_url_contract(self):
        text = self.read("kaiplus/files/kaiplus.config")

        self.assertIn("option 'enabled' '0'", text)
        self.assertIn("option 'port' '8189'", text)
        self.assertIn("option 'base_path' '/apps/kaiplus/'", text)
        self.assertIn("option 'system_role' 'istoreos'", text)

    def test_init_reads_base_path_and_passes_it_to_kaiplus_web(self):
        text = self.read("kaiplus/files/kaiplus.init")

        self.assertIn('config_get port "$1" port "8189"', text)
        self.assertIn('config_get base_path "$1" base_path "/apps/kaiplus/"', text)
        self.assertIn('procd_append_param command --base-path "$base_path"', text)
        self.assertIn('procd_append_param command --addr "0.0.0.0:$port"', text)
        self.assertNotIn('port "8198"', text)

    def test_app_meta_config_writes_standalone_port_and_base_path(self):
        text = self.read("app-meta-kaiplus/config.sh")

        self.assertIn('set kaiplus.@kaiplus[0].port="8189"', text)
        self.assertIn('set kaiplus.@kaiplus[0].base_path="/apps/kaiplus/"', text)
        self.assertNotIn('port="8198"', text)

    def test_app_meta_entry_reports_base_path_href(self):
        text = self.read("app-meta-kaiplus/entry.sh")

        self.assertIn('base_path="$(uci get kaiplus.@kaiplus[0].base_path 2>/dev/null)"', text)
        self.assertIn('local basepath=${base_path:-/apps/kaiplus/}', text)
        self.assertIn('json_add_string "href" "http://$host:${portsec}${basepath}"', text)
        self.assertNotIn('http://$host:${portsec}/"', text)

    def test_luci_status_exposes_base_path_and_open_button_uses_it(self):
        controller = self.read("luci-app-kaiplus/luasrc/controller/kaiplus.lua")
        status_view = self.read("luci-app-kaiplus/luasrc/view/kaiplus/kaiplus_status.htm")

        self.assertIn('local base_path = uci:get_first("kaiplus", "kaiplus", "base_path", "/apps/kaiplus/")', controller)
        self.assertRegex(controller, re.compile(r"base_path\s*=\s*base_path"))
        self.assertIn('st.base_path || "/apps/kaiplus/"', status_view)
        self.assertIn("window.location.hostname + ':' + st.port + basePath", status_view)


if __name__ == "__main__":
    unittest.main()
