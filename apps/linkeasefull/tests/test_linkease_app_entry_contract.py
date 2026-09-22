from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LinkEaseAppEntryContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_package_owns_both_workers_and_single_init(self):
        makefile = self.read("linkeasefull/Makefile")
        entry_init = self.read("linkeasefull/files/linkease-app-entry.init")
        compatibility_init = self.read("linkeasefull/files/linkeasefull.init")

        self.assertIn("define Package/linkease-app-entry", makefile)
        self.assertIn("+linkease-app-entry", makefile)
        self.assertIn("linkease-app-entryd", makefile)
        self.assertIn("linkease-app-gateway", makefile)
        self.assertIn('procd_set_param command "$ENTRYD"', entry_init)
        self.assertIn('--primary-enabled="$primary"', entry_init)
        self.assertIn("LINKEASE_AUTH_PROVIDER=openwrt", entry_init)
        self.assertNotIn("procd_open_instance", compatibility_init)
        self.assertIn('"$ENTRY_INIT" restart', compatibility_init)

    def test_luci_enable_reconciles_the_selected_worker(self):
        compatibility_init = self.read("linkeasefull/files/linkeasefull.init")
        defaults = self.read("linkeasefull/files/linkeasefull.uci-default")
        luci_model = self.read(
            "luci-app-linkeasefull/luasrc/model/cbi/linkeasefull.lua"
        )

        self.assertIn("sync_force_gateway", compatibility_init)
        self.assertIn('uci -q get linkeasefull.@linkeasefull[0].enabled', compatibility_init)
        self.assertIn('rm -f "$FORCE_GATEWAY"', compatibility_init)
        self.assertIn(': > "$FORCE_GATEWAY"', compatibility_init)
        self.assertIn("add ucitrack linkeasefull", defaults)
        self.assertIn("set ucitrack.@linkeasefull[-1].init=linkeasefull", defaults)
        self.assertIn("function enabled.write", luci_model)
        self.assertIn("/var/run/linkease-app-entry/force-gateway", luci_model)
        self.assertIn("fs.remove(force_gateway)", luci_model)
        self.assertIn("fs.writefile(force_gateway", luci_model)

    def test_uhttpd_mapping_is_stable_and_idempotent(self):
        defaults = self.read("linkeasefull/files/linkease-app-entry.uci-default")
        self.assertIn("/apps=http://127.0.0.1:19290", defaults)
        self.assertIn("add_list", defaults)
        self.assertIn("found", defaults)


if __name__ == "__main__":
    unittest.main()
