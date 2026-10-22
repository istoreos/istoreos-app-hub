from pathlib import Path
import json
import re
import subprocess
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
        self.assertEqual(manifest["standalone"]["url"], "/apps/kaiplus/")
        self.assertEqual(manifest["config"]["providerOrder"], ["uci"])
        self.assertEqual(manifest["config"]["providers"]["uci"]["type"], "uci")
        self.assertEqual(manifest["backend"]["host"], "127.0.0.1")
        self.assertEqual(manifest["backend"]["portFromUci"], "kaiplus.@kaiplus[0].port")
        self.assertEqual(manifest["backend"]["defaultPort"], 8189)
        self.assertEqual(manifest["backend"]["upstreamBasePath"], "/apps/kaiplus/")
        self.assertEqual(manifest["backend"]["apiPath"], "api/")
        self.assertEqual(manifest["backend"]["pathMode"], "preserve")
        self.assertNotIn("transport", manifest["backend"])
        self.assertNotIn("values", manifest["backend"])
        self.assertNotIn("fallback", manifest["backend"])
        self.assertTrue(manifest["window"]["singleton"])
        self.assertNotIn("desktopPriority", manifest)

    def test_kaiplus_package_install_registers_linkeasefull_desktop_plugin(self):
        makefile = self.read("kaiplus/Makefile")

        self.assertIn("$(1)/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertIn("$(1)/usr/share/linkease/apps.d", makefile)
        self.assertIn("DEPENDS:=+linkease-app-entry", makefile)
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

    def test_config_contains_only_user_facing_runtime_options(self):
        text = self.read("kaiplus/files/kaiplus.config")

        self.assertEqual(
            re.findall(r"option '([^']+)'", text),
            ["enabled", "data_dir", "port"],
        )

    def test_init_uses_fixed_tcp_runtime_contract(self):
        text = self.read("kaiplus/files/kaiplus.init")

        self.assertIn('config_get_bool enabled "$1" enabled 0', text)
        self.assertIn('config_get data_dir "$1" data_dir ""', text)
        self.assertIn('config_get port "$1" port "8189"', text)
        self.assertNotIn("config_get listen_mode", text)
        self.assertNotIn("config_get_bool external_port_enabled", text)
        self.assertNotIn("config_get socket_path", text)
        self.assertNotIn("config_get release_channel", text)
        self.assertIn('KAIPLUS_RELEASE_CHANNEL="stable"', text)
        self.assertIn('KAIPLUS_AUTH_MODE="disabled"', text)
        self.assertIn('LINKEASE_AUTH_PROVIDER="disabled"', text)
        self.assertIn('KAIPLUS_LISTEN_MODE="tcp"', text)
        self.assertIn('procd_append_param command --listen-mode tcp', text)
        self.assertIn('procd_append_param command --addr "0.0.0.0:$port"', text)
        self.assertIn('procd_append_param command --base-path /apps/kaiplus/', text)
        self.assertIn('procd_append_param command --release-channel stable', text)
        self.assertNotIn("--listen-mode unix", text)
        self.assertNotIn("--socket-path", text)
        self.assertNotIn('port "{}"'.format(LEGACY_PORT), text)

    def test_router_runtime_directories_are_private_and_init_is_ash_compatible(self):
        text = self.read("kaiplus/files/kaiplus.init")
        self.assertIn("umask 077", text)
        self.assertIn('chmod 0700 "$data_dir/config" "$data_dir/state"', text)
        self.assertIn('procd_append_param command --system-role istoreos', text)
        subprocess.run(["sh", "-n", str(ROOT / "kaiplus/files/kaiplus.init")], check=True)

    def test_bubblewrap_is_not_a_current_runtime_dependency(self):
        makefile = self.read("kaiplus/Makefile")
        package_block = makefile.split("define Package/$(PKG_NAME)", 1)[1].split("endef", 1)[0]
        self.assertNotIn("bubblewrap", package_block.lower())
        self.assertNotIn("bwrap", package_block.lower())

    def test_kaiplus_runtime_and_luci_remain_without_software_center_meta(self):
        self.assertTrue((ROOT / "kaiplus/Makefile").is_file())
        self.assertTrue((ROOT / "luci-app-kaiplus/Makefile").is_file())
        self.assertFalse((ROOT / "app-meta-kaiplus").exists())

    def test_openwrt_auth_bridge_is_declared_as_package_dependency(self):
        runtime_makefile = self.read("kaiplus/Makefile")
        luci_makefile = self.read("luci-app-kaiplus/Makefile")

        self.assertIn("+luci-lib-linkeaseauth", luci_makefile)
        self.assertIn("+linkease-app-entry", luci_makefile)
        self.assertNotIn("luci-lib-openwrtauth", luci_makefile)
        self.assertNotIn("+luci-lib-linkeaseauth", runtime_makefile)

    def test_runtime_and_plugin_versions_are_pinned_for_release_traceability(self):
        runtime_makefile = self.read("kaiplus/Makefile")
        luci_makefile = self.read("luci-app-kaiplus/Makefile")

        for text in (runtime_makefile, luci_makefile):
            self.assertIn("PKG_VERSION:=1.0.9", text)
        self.assertIn("PKG_RELEASE:=3", runtime_makefile)
        self.assertIn("PKG_RELEASE:=4", luci_makefile)
        self.assertIn("kaiplus-runtime-v$(PKG_VERSION)", runtime_makefile)
        self.assertIn("$(PKG_NAME)-binary-$(PKG_VERSION).tar.gz", runtime_makefile)

    def test_kaiplus_package_contains_no_legacy_port_value(self):
        for path in ROOT.rglob("*"):
            if path.is_file() and "tests" not in path.parts:
                self.assertNotIn(LEGACY_PORT.encode(), path.read_bytes(), str(path))

    def test_restart_paths_refresh_linkease_when_present(self):
        cbi = self.read("luci-app-kaiplus/luasrc/model/cbi/kaiplus.lua")

        self.assertIn('if sys.call("[ -x /etc/init.d/linkease ]") == 0 then', cbi)
        self.assertIn('sys.call("/etc/init.d/linkease restart >/dev/null 2>&1 &")', cbi)

    def test_luci_status_exposes_entry_state_and_open_button_uses_luci_open(self):
        controller = self.read("luci-app-kaiplus/luasrc/controller/kaiplus.lua")
        status_view = self.read("luci-app-kaiplus/luasrc/view/kaiplus/kaiplus_status.htm")

        self.assertIn('local open = entry({"admin", "services", "kaiplus", "open"}, call("kaiplus_open"))', controller)
        self.assertIn('function kaiplus_open()', controller)
        self.assertIn('compat():open("kaiplus")', controller)
        self.assertIn('compat():legacy_status("kaiplus"', controller)
        self.assertNotIn("uhttpd_apps_proxy_available", controller)
        self.assertNotIn("app_entry_running", controller)
        self.assertNotIn("enable_port", controller)
        self.assertNotIn("uci:set", controller)
        self.assertNotIn("uci:commit", controller)
        self.assertNotIn("restart", controller)
        self.assertIn('external_port_enabled = true', controller)
        self.assertIn('st.proxy_prefix_enabled && st.app_entry_running', status_view)
        self.assertIn('st.external_port_enabled', status_view)
        self.assertIn('<%=url("admin/services/kaiplus/open")%>', status_view)
        self.assertNotIn("window.location.hostname + ':' + st.port", status_view)

    def test_luci_cbi_exposes_only_enable_data_directory_and_port(self):
        text = self.read("luci-app-kaiplus/luasrc/model/cbi/kaiplus.lua")

        self.assertEqual(
            re.findall(r's:option\([^,]+, "([^"]+)"', text),
            ["enabled", "data_dir", "port"],
        )
        self.assertIn('translate("Access port")', text)


if __name__ == "__main__":
    unittest.main()
