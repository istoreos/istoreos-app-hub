from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


class LinkEaseLiteContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def read_repo(self, relative):
        return (REPO / relative).read_text(encoding="utf-8")

    def assert_not_contains_full_runtime(self, text):
        forbidden = [
            "linkease-desktop",
            "apptunnel-client",
            "KAIPLUS",
            "kaiplus",
            "linkmount",
            "desktop_port",
            "desktop_base_path",
            "Full UI",
            "edition",
        ]
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, text)

    def procd_instance_block(self, text, name):
        escaped = re.escape(name)
        pattern = re.compile(
            r"^[ \t]*procd_open_instance\s+(?:['\"]%s['\"]|%s)(?=\s|$|#).*?^[ \t]*procd_close_instance\b"
            % (escaped, escaped),
            re.DOTALL | re.MULTILINE,
        )
        match = pattern.search(text)
        self.assertIsNotNone(match, "missing procd instance block for %s" % name)
        return match.group(0)

    def test_runtime_makefile_installs_lite_binary_contract(self):
        text = self.read("linkeaselite/Makefile")

        self.assertIn("PKG_NAME:=linkeaselite", text)
        self.assertIn("PKG_SOURCE:=linkeaselite-binary-$(PKG_SOURCE_DATE).tar.gz", text)
        self.assertIn("TAR_CMD=$(HOST_TAR) -C $(PKG_BUILD_DIR) $(TAR_OPTIONS)", text)
        self.assertIn("CONFLICTS:=linkease", text)
        self.assertIn("DEPENDS:=@(arm||x86_64||aarch64) +ca-bundle", text)
        self.assertIn("/etc/config/linkeaselite", text)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/linkease-lite.$(ARCH) $(1)/usr/sbin/linkease-lite", text)
        self.assertIn("PKG_HASH:=", text)
        self.assertNotIn("PKG_HASH:=skip", text)
        self.assert_not_contains_full_runtime(text)

    def test_runtime_config_defaults(self):
        text = self.read("linkeaselite/files/linkeaselite.config")

        self.assertIn("config linkeaselite", text)
        self.assertIn("option enabled '1'", text)
        self.assertIn("option port '8897'", text)
        self.assertIn("option allowPublic '0'", text)
        self.assert_not_contains_full_runtime(text)

    def test_init_starts_single_lite_process(self):
        text = self.read("linkeaselite/files/linkeaselite.init")

        self.assertIn("PROG=/usr/sbin/linkease-lite", text)
        self.assertIn("LOCAL_API=/var/run/linkeaselite.sock", text)
        self.assertEqual(len(re.findall(r"^[ \t]*procd_open_instance\b", text, re.MULTILINE)), 1)
        block = self.procd_instance_block(text, "linkeaselite")
        self.assertIn('procd_set_param command "$PROG"', block)
        self.assertIn('procd_append_param command --deviceAddr ":$port" --localApi "$LOCAL_API"', block)
        self.assertIn('[ "$allowPublic" = "1" ] && procd_append_param command --allowPublic', block)
        self.assertIn('procd_set_param limits nofile="65535 65535"', block)
        self.assertIn("procd_set_param respawn", block)
        self.assert_not_contains_full_runtime(text)

    def test_init_reconciles_firewall_on_every_restart(self):
        text = self.read("linkeaselite/files/linkeaselite.init")

        self.assertIn("sync_firewall() {", text)
        self.assertIn("uci -q delete firewall.linkeaselite", text)
        self.assertIn("uci -q set firewall.linkeaselite=rule", text)
        self.assertIn('uci -q set firewall.linkeaselite.name="linkeaselite"', text)
        self.assertIn('uci -q set firewall.linkeaselite.dest_port="$port"', text)
        self.assertIn("uci -q commit firewall", text)
        self.assertIn("/etc/init.d/firewall reload", text)
        self.assertIn('sync_firewall\n\t[ "$enabled" = "1" ] || return 1', text)

    def test_runtime_package_removal_deletes_only_its_firewall_rule(self):
        text = self.read("linkeaselite/Makefile")
        postrm = re.search(
            r"define Package/\$\(PKG_NAME\)/postrm\n(.*?)\nendef", text, re.DOTALL
        )

        self.assertIsNotNone(postrm, "missing runtime package postrm hook")
        postrm_text = postrm.group(1)
        self.assertIn("uci -q delete firewall.linkeaselite", postrm_text)
        self.assertIn("uci -q commit firewall", postrm_text)
        self.assertIn("/etc/init.d/firewall reload", postrm_text)
        self.assertNotIn("delete linkeaselite", postrm_text)

    def test_uci_default_preserves_values_and_manages_firewall(self):
        text = self.read("linkeaselite/files/linkeaselite.uci-default")

        self.assertIn('uci -q add linkeaselite linkeaselite', text)
        self.assertIn("set_default enabled 1", text)
        self.assertIn("set_default port 8897", text)
        self.assertIn("set_default allowPublic 0", text)
        self.assertIn("delete ucitrack.@linkeaselite[-1]", text)
        self.assertIn("set ucitrack.@linkeaselite[-1].init=linkeaselite", text)
        self.assertIn("delete firewall.linkeaselite", text)
        self.assertIn('set firewall.linkeaselite.name="linkeaselite"', text)
        self.assertIn("/etc/init.d/linkeaselite enable", text)
        self.assertIn("/etc/init.d/linkeaselite restart", text)
        self.assertNotRegex(text, re.compile(r"rm\s+-rf\s+(?:--\s+)?['\"]?/mnt(?:/|\\b)", re.IGNORECASE))

    def test_config_helper_uses_linkeaselite_namespace(self):
        text = self.read("linkeaselite/files/linkeaselite-config.sh")

        self.assertIn('uci set "linkeaselite.@linkeaselite[0].preconfig=$2"', text)
        self.assertIn('uci -q get linkeaselite.@linkeaselite[0].local_home', text)
        self.assertIn("local_save)", text)
        self.assertIn("local_load)", text)
        self.assertIn("status)", text)
        self.assertNotIn("linkease.@linkease", text)

    def test_luci_package_and_controller_are_lite_only(self):
        makefile = self.read("luci-app-linkeaselite/Makefile")
        controller = self.read("luci-app-linkeaselite/luasrc/controller/linkeaselite.lua")
        cbi = self.read("luci-app-linkeaselite/luasrc/model/cbi/linkeaselite.lua")
        status = self.read("luci-app-linkeaselite/luasrc/view/linkeaselite_status.htm")

        self.assertIn("LUCI_TITLE:=LuCI support for linkeaselite", makefile)
        self.assertIn("LUCI_DEPENDS:=+linkeaselite", makefile)
        self.assertIn('/etc/config/linkeaselite', controller)
        self.assertIn('entry({"admin", "services", "linkeaselite"}, cbi("linkeaselite"), _("LinkEaseLite"), 20)', controller)
        self.assertIn('pidof linkease-lite >/dev/null', controller)
        self.assertIn('port = (port or 8897)', controller)
        self.assertIn('Map("linkeaselite"', cbi)
        self.assertIn('s:option(Flag, "allowPublic"', cbi)
        self.assertIn("linkeaselite_status", status)
        self.assertIn("Click to open LinkEaseLite", status)
        self.assert_not_contains_full_runtime(makefile + controller + cbi + status)

    def test_luci_backend_proxies_to_lite_socket(self):
        backend = self.read("luci-app-linkeaselite/luasrc/controller/linkeaselite_backend.lua")
        file_view = self.read("luci-app-linkeaselite/luasrc/view/linkeaselite/file.htm")
        static_index = ROOT / "luci-app-linkeaselite/htdocs/luci-static/linkeasefile/index.js"
        static = static_index.read_text(encoding="utf-8")

        self.assertIn('local LINKEASELITE_UNIX = "/var/run/linkeaselite.sock"', backend)
        self.assertIn('entry({"linkeaselite"}, call("linkeaselite_backend")).leaf=true', backend)
        self.assertIn("function linkeaselite_backend()", backend)
        self.assertIn('local request_uri = http.getenv("REQUEST_URI") or "/"', backend)
        self.assertIn(
            'request_uri = request_uri:gsub("^/cgi%-bin/luci/linkeaselite", "")', backend
        )
        self.assertIn('.. " " .. request_uri .. " HTTP/1.1"', backend)
        self.assertIn("for k, v in pairs(req.message.env)", backend)
        self.assertNotIn("function get_session()", backend)
        self.assertNotIn("X-Forwarded-Sid", backend)
        self.assertNotIn("X-Forwarded-Token", backend)
        self.assertIn("luci-static/linkeasefile/index.js", file_view)
        self.assertIn(
            'window.LINKEASE_BACKEND_PREFIX = "/cgi-bin/luci/linkeaselite"', file_view
        )
        self.assertTrue(static_index.is_file())
        self.assertNotRegex(static, re.compile(r"(?<!/cgi-bin/luci)/linkeaselite"))
        self.assertEqual(static.count("/cgi-bin/luci/linkeaselite"), 4)
        self.assertNotIn('/var/run/linkease.sock', backend)

    def test_app_meta_declares_linkeaselite(self):
        makefile = self.read("app-meta-linkeaselite/Makefile")
        config = self.read("app-meta-linkeaselite/config.sh")

        self.assertIn("PKG_VERSION:=3.0.0", makefile)
        self.assertIn("META_TITLE:=易有云Lite", makefile)
        self.assertIn("META_TITLE.en:=LinkEaseLite", makefile)
        self.assertIn("META_DEPENDS:=+linkeaselite +luci-app-linkeaselite +luci-i18n-linkeaselite-zh-cn", makefile)
        self.assertIn("META_ARCH:=x86_64 aarch64 arm", makefile)
        self.assertIn("META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/linkeaselite", makefile)
        self.assertIn('set linkeaselite.@linkeaselite[0].enabled="1"', config)
        self.assertIn("/etc/init.d/linkeaselite restart", config)

    def test_syncapps_maps_all_three_linkeaselite_slots(self):
        text = self.read_repo("syncapps.yaml")

        self.assertIn("    linkeaselite:", text)
        self.assertIn("local: apps/linkeaselite/linkeaselite", text)
        self.assertIn("remote: nas-packages/network/services/linkeaselite", text)
        self.assertIn("local: apps/linkeaselite/luci-app-linkeaselite", text)
        self.assertIn("remote: nas-packages-luci/luci/luci-app-linkeaselite", text)
        self.assertIn("local: apps/linkeaselite/app-meta-linkeaselite", text)
        self.assertIn("remote: openwrt-app-meta/applications/app-meta-linkeaselite", text)

    def test_apps_catalog_contains_linkeaselite(self):
        text = self.read_repo("docs/apps-catalog.min.md")
        data = json.loads(self.read_repo("docs/apps-catalog.json"))
        ids = {item["id"] for item in data}

        self.assertIn("- linkeaselite — 易有云Lite —", text)
        self.assertIn("linkeaselite", ids)


if __name__ == "__main__":
    unittest.main()
