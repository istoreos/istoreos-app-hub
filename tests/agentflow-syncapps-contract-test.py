#!/usr/bin/env python3

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentFlowSyncAppsContractTest(unittest.TestCase):
    def test_syncapps_includes_all_agentflow_packages(self):
        syncapps = (ROOT / "syncapps.yaml").read_text(encoding="utf-8")
        section = re.search(
            r"(?ms)^    agentflow:\n(?P<body>.*?)(?=^    [a-z0-9][^:\n]*:\n|\Z)",
            syncapps,
        )
        self.assertIsNotNone(section)
        body = section.group("body")

        self.assertIn("local: apps/agentflow/agentflow", body)
        self.assertIn(
            "remote: openwrt-app-actions/applications/agentflow",
            body,
        )
        self.assertIn("local: apps/agentflow/luci-app-agentflow", body)
        self.assertIn(
            "remote: openwrt-app-actions/applications/luci-app-agentflow",
            body,
        )
        self.assertIn("local: apps/agentflow/app-meta-agentflow", body)
        self.assertIn(
            "remote: openwrt-app-meta/applications/app-meta-agentflow",
            body,
        )


if __name__ == "__main__":
    unittest.main()
