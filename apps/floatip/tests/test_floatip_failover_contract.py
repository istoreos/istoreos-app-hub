#!/usr/bin/env python3

from pathlib import Path
import unittest


APP = Path(__file__).resolve().parents[1]


class FloatIPFailoverContractTest(unittest.TestCase):
    def test_runtime_depends_on_arping(self):
        makefile = (APP / "floatip/Makefile").read_text()
        self.assertIn("+iputils-arping", makefile)

    def test_takeover_announces_new_mac_to_lan_clients(self):
        script = (APP / "floatip/files/floatip.sh").read_text()
        self.assertIn('arping -q -U -c 3 -w 2 -I "$LAN_IFACE" "$ipaddr"', script)
        self.assertIn('arping -q -A -c 3 -w 2 -I "$LAN_IFACE" "$ipaddr"', script)
        add_position = script.index('ip addr add "$ipaddr" dev "$LAN_IFACE"')
        announce_position = script.index('announce_ip "$ipaddr"', add_position)
        self.assertGreater(announce_position, add_position)

    def test_runtime_and_meta_versions_match(self):
        runtime = (APP / "floatip/Makefile").read_text()
        meta = (APP / "app-meta-floatip/Makefile").read_text()
        self.assertIn("PKG_VERSION:=1.1.1", runtime)
        self.assertIn("PKG_VERSION:=1.1.1", meta)


if __name__ == "__main__":
    unittest.main()
