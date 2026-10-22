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
        self.assertEqual(manifest["staticRoot"], "/usr/share/kaiplus")
        self.assertEqual(manifest["desktop"]["mode"], "module")
        self.assertEqual(manifest["desktop"]["entry"], "desktop-entry.js")
        self.assertEqual(manifest["desktop"]["isolation"], "shadow-dom")
        self.assertFalse(
            (ROOT / "kaiplus/files/desktop-entry.js").exists(),
            "desktop-entry.js must be served by the KaiPlus backend",
        )
        self.assertEqual(manifest["standalone"]["basePath"], "/apps/kaiplus/")
        self.assertEqual(manifest["standalone"]["url"], "/apps/kaiplus/")
        self.assertTrue(manifest["standalone"]["externalOpen"]["enabled"])
        self.assertEqual(manifest["config"]["providerOrder"], ["uci"])
        self.assertEqual(manifest["config"]["providers"]["uci"]["type"], "uci")
        self.assertEqual(manifest["backend"]["host"], "127.0.0.1")
        self.assertEqual(manifest["backend"]["portFromUci"], "kaiplus.@kaiplus[0].port")
        self.assertEqual(manifest["backend"]["defaultPort"], 8189)
        self.assertEqual(manifest["backend"]["upstreamBasePath"], "/apps/kaiplus/")
        self.assertEqual(manifest["backend"]["apiPath"], "api/")
        self.assertEqual(manifest["backend"]["pathMode"], "preserve")
        self.assertEqual(manifest["backend"]["proxyMode"], "app-base")
        self.assertNotIn("transport", manifest["backend"])
        self.assertNotIn("values", manifest["backend"])
        self.assertNotIn("fallback", manifest["backend"])
        self.assertTrue(manifest["window"]["singleton"])
        self.assertNotIn("desktopPriority", manifest)

    def test_kaiplus_package_install_registers_linkeasefull_desktop_plugin(self):
        makefile = self.read("kaiplus/Makefile")

        self.assertIn("$(1)/usr/share/linkeasefull/desktop-apps.d", makefile)
        self.assertIn("$(1)/usr/share/linkease/apps.d", makefile)
        self.assertIn("DEPENDS:=@(x86_64||aarch64) +linkease-app-entry", makefile)
        self.assertIn("$(INSTALL_DATA) ./files/kaiplus-plugin.json $(1)/usr/share/kaiplus/kaiplus-plugin.json", makefile)
        self.assertIn("$(INSTALL_DATA) ./files/logo.png $(1)/usr/share/kaiplus/logo.png", makefile)
        self.assertNotIn("$(PKG_BUILD_DIR)/www", makefile)
        self.assertNotIn("$(PKG_BUILD_DIR)/defaults", makefile)
        self.assertNotIn("$(PKG_BUILD_DIR)/helpers", makefile)
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
        self.assertIn('KAIPLUS_AUTH_MODE="openwrt_luci"', text)
        self.assertIn('LINKEASE_AUTH_PROVIDER="openwrt_luci"', text)
        self.assertIn('KAIPLUS_LISTEN_MODE="tcp"', text)
        self.assertIn('procd_append_param command --listen-mode tcp', text)
        self.assertIn('procd_append_param command --addr "0.0.0.0:$port"', text)
        self.assertIn('procd_append_param command --base-path /apps/kaiplus/', text)
        self.assertIn('procd_append_param command --release-channel stable', text)
        self.assertIn('procd_open_instance kaiplus', text)
        self.assertIn('procd_set_param command /usr/sbin/kaiplus kaiplus-web', text)
        self.assertNotIn("kaiplus_bin", text)
        self.assertNotIn("--listen-mode unix", text)
        self.assertNotIn("--socket-path", text)
        self.assertNotIn("--static-dir", text)
        self.assertNotIn("--defaults-dir", text)
        self.assertNotIn("KAIPLUS_WORKSPACE_HELPER_DIR", text)
        self.assertNotIn("KAIPLUS_WORKSPACE_TOOL_INSTALL_DIR", text)
        self.assertNotIn("KAIPLUS_SSH_HELPER_TOKEN", text)
        self.assertNotIn("ssh-helper.token", text)
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
        self.assertIn("PKG_RELEASE:=8", runtime_makefile)
        self.assertIn("PKG_RELEASE:=7", luci_makefile)
        self.assertIn("KAIPLUS_ARCH_x86_64:=amd64", runtime_makefile)
        self.assertIn("KAIPLUS_ARCH_aarch64:=arm64", runtime_makefile)
        self.assertIn(
            "KAIPLUS_HASH_x86_64:=5588a5e1b7874bc5e631ab8ff1288226f567a84d3115808f22352d142c40f5d6",
            runtime_makefile,
        )
        self.assertIn(
            "KAIPLUS_HASH_aarch64:=5be29e4715a1181937c0156a6954738ce96fde2f338a1b03cd32c68b00e61524",
            runtime_makefile,
        )
        self.assertIn(
            "URL:=https://fw.koolcenter.com/binary/kai/releases/build/",
            runtime_makefile,
        )
        self.assertIn("URL_FILE:=$(KAIPLUS_URL_FILE)", runtime_makefile)
        self.assertIn("FILE:=$(KAIPLUS_DOWNLOAD)", runtime_makefile)
        self.assertIn("HASH:=$(KAIPLUS_HASH_$(ARCH))", runtime_makefile)
        self.assertIn("$(eval $(call Download,kaiplus))", runtime_makefile)
        self.assertIn(
            "$(CP) $(DL_DIR)/$(KAIPLUS_DOWNLOAD) $(PKG_BUILD_DIR)/kaiplus",
            runtime_makefile,
        )
        self.assertIn(
            "$(INSTALL_BIN) $(PKG_BUILD_DIR)/kaiplus $(1)/usr/sbin/kaiplus",
            runtime_makefile,
        )
        self.assertNotIn("kaiplus_bin", runtime_makefile)
        self.assertNotIn("github.com/istoreos/istoreos-app-hub/releases", runtime_makefile)

    def test_luci_menu_has_simplified_chinese_translation(self):
        text = self.read("luci-app-kaiplus/po/zh-cn/kaiplus.po")

        translations = {
            "KaiPlus": "酷友社AI",
            "KaiPlus is an AI workspace and session service.": "酷友社AI 是一款 AI 工作区与会话服务。",
            "Global settings": "全局设置",
            "Enable": "启用",
            "Data directory": "数据目录",
            "Required. KaiPlus stores workspace, cache, config, and state under this directory.": "必填。酷友社AI 会在此目录中保存工作区、缓存、配置和状态数据。",
            "Access port": "访问端口",
            "KaiPlus is available at http://router-address:port/apps/kaiplus/.": "可通过 http://路由器地址:端口/apps/kaiplus/ 访问酷友社AI。",
            "The KaiPlus service is running.": "酷友社AI 服务正在运行。",
            "The KaiPlus service is not running.": "酷友社AI 服务未运行。",
            "Access mode: LinkEase Desktop proxy.": "访问模式：LinkEase Desktop 代理。",
            "Access mode: external port.": "访问模式：外部端口。",
            "External port access is disabled.": "外部端口访问已禁用。",
            "Click to open KaiPlus": "点击打开酷友社AI",
            "Status": "状态",
            "Collecting data...": "正在获取数据……",
        }

        for source, translated in translations.items():
            self.assertIn(
                'msgid "{}"\nmsgstr "{}"'.format(source, translated),
                text,
            )

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
        self.assertIn('pidof kaiplus >/dev/null', controller)
        self.assertNotIn("kaiplus_bin", controller)
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
