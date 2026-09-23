#!/usr/bin/env python3
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


EXPECTED = {
    "apps/linkeasefull/linkeasefull/Makefile": ("PKG_SOURCE_DATE", "3.0.21", "1"),
    "apps/linkeasefull/app-meta-linkeasefull/Makefile": ("PKG_VERSION", "3.0.21", "1"),
    "apps/linkeasefull/linkease-app-entry/Makefile": ("PKG_VERSION", "3.0.21", "1"),
    "apps/linkeasefull/luci-lib-linkeaseauth/Makefile": ("PKG_VERSION", "1.2.0", "1"),
    "apps/linkeasefull/luci-app-linkeasefull-embed/Makefile": ("PKG_VERSION", "1.1.0", "1"),
    "apps/linkeasefull/luci-app-linkeasefull/Makefile": ("PKG_VERSION", "1.0.0", "3"),
    "apps/kai/kai/Makefile": ("PKG_VERSION", "0.0.23", "1"),
    "apps/kai/kai_agent/Makefile": ("PKG_VERSION", "0.0.23", "1"),
    "apps/kai/kai_session/Makefile": ("PKG_VERSION", "0.0.23", "1"),
    "apps/kai/luci-app-kai/Makefile": ("PKG_VERSION", "1.0.2", "2"),
    "apps/kai/app-meta-kai/Makefile": ("PKG_VERSION", "1.0.2", "2"),
    "apps/dockermanager/dockermanager/Makefile": ("PKG_VERSION", "0.1.1", "2"),
    "apps/dockermanager/luci-app-dockermanager/Makefile": ("PKG_VERSION", "0.1.1", "2"),
    "apps/dockermanager/app-meta-dockermanager/Makefile": ("PKG_VERSION", "0.1.1", "3"),
    "apps/baidudrive/baidudrive/Makefile": ("PKG_VERSION", "1.0.6", "2"),
    "apps/baidudrive/luci-app-baidudrive/Makefile": ("PKG_VERSION", "1.0.2", "2"),
    "apps/baidudrive/app-meta-baidudrive/Makefile": ("PKG_VERSION", "1.0.6", "2"),
    "apps/kaiplus/kaiplus/Makefile": ("PKG_VERSION", "1.0.9", "2"),
    "apps/kaiplus/luci-app-kaiplus/Makefile": ("PKG_VERSION", "1.0.9", "2"),
    "apps/agentflow/agentflow/Makefile": ("PKG_VERSION", "0.3.0", "11"),
    "apps/agentflow/luci-app-agentflow/Makefile": ("PKG_VERSION", "1.0.0", "8"),
    "apps/agentflow/app-meta-agentflow/Makefile": ("PKG_VERSION", "0.3.0", "2"),
    "apps/fastnet/fastnet/Makefile": ("PKG_VERSION", "0.7.7", "3"),
    "apps/fastnet/luci-app-fastnet/Makefile": ("PKG_VERSION", "0.7.7", "3"),
    "apps/fastnet/app-meta-fastnet/Makefile": ("PKG_VERSION", "0.7.7", "3"),
    "apps/istoreenhance/istoreenhance/Makefile": ("PKG_SOURCE_DATE", "0.8.0", "3"),
    "apps/istoreenhance/luci-app-istoreenhance/Makefile": ("PKG_VERSION", "0.8.0", "2"),
    "apps/istoreenhance/app-meta-istoreenhance/Makefile": ("PKG_VERSION", "0.8.0", "4"),
}


def assignment(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}\s*:?=\s*(.*?)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


class LinkEaseAppsVersionContractTest(unittest.TestCase):
    def test_version_matrix(self):
        for relative, (version_key, version, release) in EXPECTED.items():
            with self.subTest(package=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertEqual(assignment(text, version_key), version)
                self.assertEqual(assignment(text, "PKG_RELEASE"), release)
                if relative.endswith("linkeasefull/linkeasefull/Makefile"):
                    self.assertIsNone(assignment(text, "PKG_VERSION"))

    def test_version_and_release_are_not_combined(self):
        for relative, (version_key, _, _) in EXPECTED.items():
            with self.subTest(package=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                value = assignment(text, version_key)
                self.assertIsNotNone(value)
                self.assertNotRegex(value, r"-r\d+$")

    def test_product_composition_and_dependency_direction(self):
        full_meta = (ROOT / "apps/linkeasefull/app-meta-linkeasefull/Makefile").read_text(encoding="utf-8")
        for forbidden in ("app-meta-dockermanager", "app-meta-kai", "app-meta-baidudrive", "app-meta-istoreenhance", "app-meta-kaiplus"):
            self.assertNotIn(forbidden, full_meta)

        istorex = (ROOT / "apps/istorex/app-meta-istorex/Makefile").read_text(encoding="utf-8")
        self.assertIn("+app-meta-kai", istorex)
        self.assertNotIn("app-meta-kaiplus", istorex)

        auth = (ROOT / "apps/linkeasefull/luci-lib-linkeaseauth/Makefile").read_text(encoding="utf-8")
        self.assertNotIn("linkease-app-entry", auth)
        self.assertNotIn("linkeasefull", auth)

        for relative in (
            "apps/dockermanager/dockermanager/Makefile",
            "apps/baidudrive/baidudrive/Makefile",
            "apps/kaiplus/kaiplus/Makefile",
            "apps/agentflow/agentflow/Makefile",
            "apps/fastnet/fastnet/Makefile",
            "apps/istoreenhance/istoreenhance/Makefile",
            "apps/kai/kai/Makefile",
        ):
            self.assertIn("+linkease-app-entry", (ROOT / relative).read_text(encoding="utf-8"), relative)

    def test_retired_packages_remain_absent(self):
        self.assertFalse((ROOT / "apps/kaiplus/app-meta-kaiplus").exists())
        self.assertFalse((ROOT / "apps/linkeaseauth/luci-lib-linkeaseauth/Makefile").exists())


if __name__ == "__main__":
    unittest.main()
