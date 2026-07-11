from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LinkEaseFullContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_package_installs_full_runtime_files(self):
        text = self.read("linkease/Makefile")

        self.assertIn("PKG_NAME:=linkease", text)
        self.assertIn("PKG_SOURCE:=linkease-full-binary-$(PKG_SOURCE_DATE).tar.gz", text)
        self.assertIn("LINKEASE_FULL_ARCH", text)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/linkease-desktop $(1)/usr/bin/linkease-desktop", text)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/apptunnel-client $(1)/usr/bin/apptunnel-client", text)
        self.assertIn("$(CP) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/kaiplus $(1)/usr/lib/linkease/", text)

    def test_config_has_full_runtime_defaults(self):
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
        self.assertRegex(text, r"procd_open_instance ['\"]?desktop['\"]?")
        self.assertRegex(text, r"procd_open_instance ['\"]?apptunnel['\"]?")
        self.assertIn("SERVER_PORT=$desktop_port", text)
        self.assertIn("SERVER_BASE_PATH=$desktop_base_path", text)
        self.assertIn("--deviceAddr", text)
        self.assertIn(":$port", text)
        self.assertIn("--localApi", text)
        self.assertIn("/var/run/linkease.sock", text)

    def test_luci_opens_full_ui_and_reports_both_statuses(self):
        controller = self.read("luci-app-linkease/luasrc/controller/linkease.lua")
        status = self.read("luci-app-linkease/luasrc/view/linkease_status.htm")

        self.assertIn("desktop_running", controller)
        self.assertIn("apptunnel_running", controller)
        self.assertIn("desktop_port", controller)
        self.assertIn("desktop_base_path", controller)
        self.assertIn("fullUrl", status)
        self.assertIn("desktop_port", status)
        self.assertIn("desktopBase", status)
        self.assertRegex(status, re.compile(r"fullUrl\s*=.*desktop_port.*\+.*desktopBase", re.DOTALL))
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
        self.assertNotIn("rm -rf /mnt", text)
        self.assertNotRegex(text, re.compile(r"rm -rf\s+\$\{?data", re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
