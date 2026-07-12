from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LinkEaseFullContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def procd_open_instance_pattern(self, name):
        escaped = re.escape(name)
        return re.compile(
            r"^[ \t]*procd_open_instance\s+(?:['\"]%s['\"]|%s)(?=\s|$|#)" % (escaped, escaped),
            re.MULTILINE,
        )

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

    def shell_function_block(self, text, name):
        escaped = re.escape(name)
        pattern = re.compile(
            r"^[ \t]*%s\(\)[ \t]*(?:\{[ \t]*(?:#.*)?\n|\n[ \t]*\{[ \t]*(?:#.*)?\n)"
            r".*?^[ \t]*\}[ \t]*(?:#.*)?$"
            % escaped,
            re.DOTALL | re.MULTILINE,
        )
        match = pattern.search(text)
        self.assertIsNotNone(match, "missing shell function block for %s" % name)
        return match.group(0)

    def test_shell_function_block_requires_opening_brace(self):
        text = """valid_same_line() {
    value=1
}
valid_next_line()
{
    value=2
}
invalid()
    value=3
}
"""

        self.assertIn("value=1", self.shell_function_block(text, "valid_same_line"))
        self.assertIn("value=2", self.shell_function_block(text, "valid_next_line"))
        with self.assertRaises(AssertionError):
            self.shell_function_block(text, "invalid")

    def test_package_installs_full_runtime_files(self):
        text = self.read("linkease/Makefile")

        self.assertIn("PKG_NAME:=linkease", text)
        self.assertIn("PKG_SOURCE:=linkease-full-binary-$(PKG_SOURCE_DATE).tar.gz", text)
        self.assertIn("LINKEASE_FULL_ARCH", text)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/linkease-desktop $(1)/usr/bin/linkease-desktop", text)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/apptunnel-client $(1)/usr/bin/apptunnel-client", text)
        self.assertNotIn("$(CP) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/kaiplus $(1)/usr/lib/linkease/", text)
        self.assertNotIn("/usr/lib/linkease/kaiplus", text)

    def test_config_preserves_desktop_base_path_contract(self):
        text = self.read("linkease/files/linkease.config")

        self.assertIn("option enabled '1'", text)
        self.assertIn("option edition 'full'", text)
        self.assertIn("option port '8897'", text)
        self.assertIn("option desktop_port '19290'", text)
        self.assertIn("option desktop_base_path '/apps/'", text)
        self.assertIn("option desktop_enabled '1'", text)
        self.assertIn("option apptunnel_enabled '1'", text)
        self.assertIn("option low_memory_fallback '1'", text)

    def test_init_starts_desktop_and_apptunnel_instances(self):
        text = self.read("linkease/files/linkease.init")

        self.assertIn("PROG_DESKTOP=/usr/bin/linkease-desktop", text)
        self.assertIn("PROG_APPTUNNEL=/usr/bin/apptunnel-client", text)
        self.assertRegex(text, self.procd_open_instance_pattern("desktop"))
        self.assertRegex(text, self.procd_open_instance_pattern("apptunnel"))

        desktop = self.procd_instance_block(text, "desktop")
        self.assertRegex(desktop, re.compile(r"procd_(?:set|append)_param command .*(?:\$PROG_DESKTOP|linkease-desktop)"))
        self.assertIn("SERVER_PORT=$desktop_port", desktop)
        self.assertIn("SERVER_BASE_PATH=$desktop_base_path", desktop)
        self.assertIn("KAIPLUS_ENABLED=0", desktop)
        self.assertNotIn("KAIPLUS_BIN=", desktop)
        self.assertNotIn("KAIPLUS_STATIC_DIR=", desktop)
        self.assertNotIn("KAIPLUS_DEFAULTS_DIR=", desktop)
        self.assertNotIn("KAIPLUS_HOME=", desktop)
        self.assertNotIn("KAIPLUS_ADDR=", desktop)
        self.assertNotIn("KAIPLUS_BASE_PATH=", desktop)
        self.assertRegex(
            desktop,
            re.compile(
                r'if \[ -n "\$KAIPLUS_PROXY_TARGET" \]; then\s*'
                r'procd_set_param env "KAIPLUS_PROXY_TARGET=\$KAIPLUS_PROXY_TARGET"\s*fi'
            ),
        )
        config = self.read("linkease/files/linkease.config")
        self.assertIn("option desktop_base_path '/apps/'", config)
        self.assertIn("SERVER_BASE_PATH=$desktop_base_path", desktop)

        apptunnel = self.procd_instance_block(text, "apptunnel")
        self.assertRegex(apptunnel, re.compile(r"procd_(?:set|append)_param command .*(?:\$PROG_APPTUNNEL|apptunnel-client)"))
        self.assertIn("--deviceAddr", apptunnel)
        self.assertIn(":$port", apptunnel)
        self.assertIn("--localApi", apptunnel)
        self.assertIn("/var/run/linkease.sock", apptunnel)

    def test_init_read_config_resolves_kaiplus_proxy_from_standalone_plugin(self):
        text = self.read("linkease/files/linkease.init")
        resolver = self.shell_function_block(text, "resolve_kaiplus_proxy_target")
        read_config = self.shell_function_block(text, "read_config")

        self.assertIn("resolve_data_root_parent", read_config)
        self.assertIn("data_root=", read_config)
        self.assertIn("recycle_root=", read_config)
        self.assertIn("resolve_kaiplus_proxy_target", read_config)
        self.assertLess(
            read_config.index("data_root="),
            read_config.index("resolve_kaiplus_proxy_target"),
        )
        self.assertLess(
            read_config.index("recycle_root="),
            read_config.index("resolve_kaiplus_proxy_target"),
        )
        self.assertIn("[ -x /etc/init.d/kaiplus ] || return 0", resolver)
        self.assertIn('kaiplus_port="$(uci -q get kaiplus.@kaiplus[0].port || true)"', resolver)
        self.assertIn('[ -n "$kaiplus_port" ] || kaiplus_port=8189', resolver)
        self.assertIn('KAIPLUS_PROXY_TARGET="http://127.0.0.1:$kaiplus_port"', resolver)
        self.assertNotIn("127.0.0.1:19291", text)

    def test_luci_opens_full_ui_and_reports_both_statuses(self):
        controller = self.read("luci-app-linkease/luasrc/controller/linkease.lua")
        status = self.read("luci-app-linkease/luasrc/view/linkease_status.htm")

        self.assertIn("desktop_running", controller)
        self.assertIn("apptunnel_running", controller)
        self.assertIn("desktop_port", controller)
        self.assertIn("desktop_base_path", controller)
        self.assertIn("fullUrl", status)
        self.assertIn("var fullUrl", status)
        self.assertIn("st.desktop_port || 19290", status)
        self.assertIn("desktopBase", status)
        self.assertRegex(status, re.compile(r"fullUrl\s*=.*hostname.*(?:desktop_port|desktopPort).*desktopBase", re.DOTALL))
        self.assertRegex(status, re.compile(r"(window\.open\s*\([^)]*\bfullUrl\b[^)]*\)|location\.href\s*=\s*fullUrl\b)", re.DOTALL))
        self.assertIn("Click to open LinkEase Full", status)

    def test_migration_helper_preserves_legacy_and_removes_betterapps(self):
        text = self.read("linkease/files/linkease-migrate.sh")

        self.assertIn("uci -q get linkease.@linkease[0].local_home", text)
        self.assertIn("data_root_parent", text)
        self.assertRegex(text, re.compile(r"data_root_parent=.*\$\{?local_home\}?", re.IGNORECASE))
        self.assertRegex(text, re.compile(r"uci -q set linkease\.@linkease\[0\]\.data_root_parent=.*\$\{?data_root_parent\}?", re.IGNORECASE))
        self.assertIn("uci -q set linkease.@linkease[0].edition='full'", text)
        self.assertIn("/etc/init.d/betterapps stop", text)
        self.assertIn("rm -f /etc/init.d/betterapps", text)
        self.assertIn("/etc/rc.d/S*betterapps", text)
        self.assertIn("/etc/rc.d/K*betterapps", text)
        self.assertRegex(text, re.compile(r"(?m)(?:^|[;&]\s*)rm\s+-f(?:\s+[^#\n;]*)?['\"]?/etc/rc\.d/S\*betterapps['\"]?(?:\s|$|[;#])"))
        self.assertRegex(text, re.compile(r"(?m)(?:^|[;&]\s*)rm\s+-f(?:\s+[^#\n;]*)?['\"]?/etc/rc\.d/K\*betterapps['\"]?(?:\s|$|[;#])"))
        self.assertNotRegex(text, re.compile(r"rm\s+-rf\s+(?:--\s+)?['\"]?/mnt(?:/|\b)", re.IGNORECASE))
        self.assertNotRegex(text, re.compile(r"rm\s+-rf\s+(?:--\s+)?['\"]?\$\{?data[\w_]*\}?", re.IGNORECASE))
        self.assertNotRegex(text, re.compile(r"rm\s+-rf\s+(?:--\s+)?['\"]?\$\{?[\w_]*mount[\w_]*\}?", re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
