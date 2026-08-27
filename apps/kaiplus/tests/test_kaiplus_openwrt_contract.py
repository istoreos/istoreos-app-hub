from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LEGACY_PORT = str(8200 - 2)


class KaiPlusOpenWrtContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_linkeasefull_desktop_plugin_manifest_contract(self):
        manifest = json.loads(self.read("kaiplus/files/kaiplus-plugin.json"))

        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["id"], "kaiplus")
        self.assertEqual(manifest["name"], "KaiPlus")
        self.assertEqual(manifest["icon"], "logo.png")
        self.assertEqual(manifest["staticRoot"], "/usr/share/kaiplus/www")
        self.assertEqual(manifest["desktop"]["mode"], "module")
        self.assertEqual(manifest["desktop"]["entry"], "desktop-entry.js")
        self.assertEqual(manifest["desktop"]["isolation"], "shadow-dom")
        self.assertEqual(manifest["standalone"]["basePath"], "/apps/kaiplus/")
        self.assertEqual(manifest["config"]["providerOrder"], ["uci"])
        self.assertEqual(manifest["config"]["providers"]["uci"]["type"], "uci")
        self.assertEqual(manifest["backend"]["transport"], "unix")
        self.assertEqual(
            manifest["backend"]["values"]["socketPath"]["keys"]["uci"],
            "kaiplus.@kaiplus[0].socket_path",
        )
        self.assertEqual(manifest["backend"]["values"]["socketPath"]["default"], "/var/run/kaiplus.sock")
        self.assertEqual(
            manifest["backend"]["values"]["listenMode"]["keys"]["uci"],
            "kaiplus.@kaiplus[0].listen_mode",
        )
        self.assertEqual(manifest["backend"]["values"]["listenMode"]["default"], "auto")
        self.assertEqual(
            manifest["backend"]["values"]["externalPortEnabled"]["keys"]["uci"],
            "kaiplus.@kaiplus[0].external_port_enabled",
        )
        self.assertFalse(manifest["backend"]["values"]["externalPortEnabled"]["default"])
        self.assertEqual(manifest["backend"]["values"]["port"]["keys"]["uci"], "kaiplus.@kaiplus[0].port")
        self.assertEqual(manifest["backend"]["values"]["port"]["default"], 8189)
        self.assertEqual(manifest["backend"]["upstreamBasePath"], "/apps/kaiplus/")
        self.assertEqual(manifest["backend"]["apiPath"], "api/")
        self.assertEqual(manifest["backend"]["pathMode"], "preserve")
        self.assertEqual(manifest["backend"]["fallback"]["transport"], "tcp")
        self.assertEqual(manifest["backend"]["fallback"]["host"], "127.0.0.1")
        self.assertTrue(manifest["window"]["singleton"])
        self.assertNotIn("desktopPriority", manifest)

    def test_kaiplus_package_install_registers_linkeasefull_desktop_plugin(self):
        makefile = self.read("kaiplus/Makefile")

        self.assertIn("$(1)/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertIn("$(INSTALL_DATA) ./files/kaiplus-plugin.json $(1)/usr/share/kaiplus/kaiplus-plugin.json", makefile)
        self.assertIn("$(INSTALL_DATA) ./files/logo.png $(1)/usr/share/kaiplus/www/logo.png", makefile)
        self.assertNotIn("../app-meta-", makefile)
        self.assertIn(
            "ln -sf /usr/share/kaiplus/kaiplus-plugin.json $(1)/usr/share/linkeasefull/desktop-apps.d/00-kaiplus-plugin.json",
            makefile,
        )

    def test_kaiplus_package_unregisters_linkeasefull_desktop_plugin_on_remove(self):
        makefile = self.read("kaiplus/Makefile")

        self.assertIn("define Package/$(PKG_NAME)/prerm", makefile)
        self.assertIn("readlink /usr/share/linkeasefull/desktop-apps.d/00-kaiplus-plugin.json", makefile)
        self.assertIn('= "/usr/share/kaiplus/kaiplus-plugin.json"', makefile)
        self.assertIn("rm -f /usr/share/linkeasefull/desktop-apps.d/00-kaiplus-plugin.json", makefile)

    def test_config_defaults_to_standalone_url_contract(self):
        text = self.read("kaiplus/files/kaiplus.config")

        self.assertIn("option 'enabled' '0'", text)
        self.assertIn("option 'listen_mode' 'auto'", text)
        self.assertIn("option 'external_port_enabled' '0'", text)
        self.assertIn("option 'socket_path' '/var/run/kaiplus.sock'", text)
        self.assertIn("option 'port' '8189'", text)
        self.assertIn("option 'bind_addr' '0.0.0.0'", text)
        self.assertIn("option 'base_path' '/apps/kaiplus/'", text)
        self.assertIn("option 'system_role' 'istoreos'", text)

    def test_init_reads_listen_config_and_passes_it_to_kaiplus_web(self):
        text = self.read("kaiplus/files/kaiplus.init")

        self.assertIn('config_get_bool enabled "$1" enabled 0', text)
        self.assertIn('config_get listen_mode "$1" listen_mode "auto"', text)
        self.assertIn('config_get_bool external_port_enabled "$1" external_port_enabled 0', text)
        self.assertIn('config_get socket_path "$1" socket_path "/var/run/kaiplus.sock"', text)
        self.assertIn('config_get port "$1" port "8189"', text)
        self.assertIn('config_get bind_addr "$1" bind_addr "0.0.0.0"', text)
        self.assertIn('config_get base_path "$1" base_path "/apps/kaiplus/"', text)
        self.assertIn('KAIPLUS_LISTEN_MODE="unix"', text)
        self.assertIn('KAIPLUS_SOCKET_PATH="$socket_path"', text)
        self.assertIn('KAIPLUS_LISTEN_MODE="tcp"', text)
        self.assertIn('procd_append_param command --listen-mode unix', text)
        self.assertIn('procd_append_param command --socket-path "$socket_path"', text)
        self.assertIn('procd_append_param command --listen-mode tcp', text)
        self.assertIn('procd_append_param command --addr "$bind_addr:$port"', text)
        self.assertIn('procd_append_param command --base-path "$base_path"', text)
        self.assertNotIn('port "{}"'.format(LEGACY_PORT), text)

    def test_app_meta_config_writes_listen_defaults_and_base_path(self):
        text = self.read("app-meta-kaiplus/config.sh")

        self.assertIn('set kaiplus.@kaiplus[0].listen_mode="auto"', text)
        self.assertIn('set kaiplus.@kaiplus[0].external_port_enabled="0"', text)
        self.assertIn('set kaiplus.@kaiplus[0].socket_path="/var/run/kaiplus.sock"', text)
        self.assertIn('set kaiplus.@kaiplus[0].port="8189"', text)
        self.assertIn('set kaiplus.@kaiplus[0].bind_addr="0.0.0.0"', text)
        self.assertIn('set kaiplus.@kaiplus[0].base_path="/apps/kaiplus/"', text)
        self.assertNotIn('port="{}"'.format(LEGACY_PORT), text)

    def test_kaiplus_package_contains_no_legacy_port_value(self):
        for path in ROOT.rglob("*"):
            if path.is_file() and "tests" not in path.parts:
                self.assertNotIn(LEGACY_PORT.encode(), path.read_bytes(), str(path))

    def test_restart_paths_refresh_linkease_when_present(self):
        app_meta = self.read("app-meta-kaiplus/config.sh")
        cbi = self.read("luci-app-kaiplus/luasrc/model/cbi/kaiplus.lua")

        self.assertIn('[ -x /etc/init.d/linkease ] && /etc/init.d/linkease restart >/dev/null 2>&1 &', app_meta)
        self.assertIn('if sys.call("[ -x /etc/init.d/linkease ]") == 0 then', cbi)
        self.assertIn('sys.call("/etc/init.d/linkease restart >/dev/null 2>&1 &")', cbi)

    def test_app_meta_entry_uses_luci_open_unless_external_port_enabled(self):
        text = self.read("app-meta-kaiplus/entry.sh")

        self.assertIn('base_path="$(uci get kaiplus.@kaiplus[0].base_path 2>/dev/null)"', text)
        self.assertIn('local basepath=${base_path:-/apps/kaiplus/}', text)
        self.assertIn('external_port_enabled="$(uci get kaiplus.@kaiplus[0].external_port_enabled 2>/dev/null)"', text)
        self.assertIn('if [ "$external_port_enabled" = "1" ]; then', text)
        self.assertIn('json_add_string "href" "http://$host:${portsec}${basepath}"', text)
        self.assertIn('json_add_string "href" "/cgi-bin/luci/admin/services/kaiplus/open"', text)
        self.assertNotIn('http://$host:${portsec}/"', text)

    def test_luci_status_exposes_entry_state_and_open_button_uses_luci_open(self):
        controller = self.read("luci-app-kaiplus/luasrc/controller/kaiplus.lua")
        status_view = self.read("luci-app-kaiplus/luasrc/view/kaiplus/kaiplus_status.htm")

        self.assertIn('local APPS_PROXY_PREFIX = "/apps=http://127.0.0.1:19290"', controller)
        self.assertIn('local open = entry({"admin", "services", "kaiplus", "open"}, call("kaiplus_open"))', controller)
        self.assertIn('function kaiplus_open()', controller)
        self.assertIn('uci:set("kaiplus", section, "external_port_enabled", "1")', controller)
        self.assertIn('uci:set("kaiplus", section, "listen_mode", "tcp")', controller)
        self.assertRegex(controller, re.compile(r"base_path\s*=\s*base_path"))
        self.assertIn('external_port_enabled = external_port_enabled', controller)
        self.assertIn('proxy_prefix_enabled = uhttpd_apps_proxy_available()', controller)
        self.assertIn('linkeasefull_running = linkeasefull_running()', controller)
        self.assertIn('st.proxy_prefix_enabled && st.linkeasefull_running', status_view)
        self.assertIn('st.external_port_enabled', status_view)
        self.assertIn('<%=url("admin/services/kaiplus/open")%>', status_view)
        self.assertNotIn("window.location.hostname + ':' + st.port", status_view)

    def test_luci_cbi_marks_socket_and_base_path_readonly(self):
        text = self.read("luci-app-kaiplus/luasrc/model/cbi/kaiplus.lua")

        self.assertIn('s:option(ListValue, "listen_mode", translate("Listen mode"))', text)
        self.assertIn('s:option(Flag, "external_port_enabled", translate("Enable external port access"))', text)
        self.assertIn('s:option(Value, "socket_path", translate("Unix socket path"))', text)
        self.assertIn('socket_path.readonly = true', text)
        self.assertIn('s:option(Value, "base_path", translate("Base path"))', text)
        self.assertIn('base_path.readonly = true', text)


if __name__ == "__main__":
    unittest.main()
