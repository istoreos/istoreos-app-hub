#!/usr/bin/env python3
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

# Each entry is the audited source expression and its OpenWrt 21.02 OPKG and
# OpenWrt 25.12 APK expansions. API floors intentionally do not pin a package
# revision; release-coupled runtime floors use the CONFIG_USE_APK selector.
EXPECTED = {
    "apps/agentflow/agentflow/Makefile": (
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/agentflow/luci-app-agentflow/Makefile": (
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/baidudrive/baidudrive/Makefile": (
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/baidudrive/luci-app-baidudrive/Makefile": (
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/changeguard/changeguard/Makefile": (
        "linkspace (>=0.3.3-$(if $(CONFIG_USE_APK),r)2)",
        "linkspace (>=0.3.3-2)",
        "linkspace (>=0.3.3-r2)",
    ),
    "apps/claude-code/claude-code/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-r2), luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/claude-code/luci-app-claude-code/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-r2), luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/codex/codex/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-r2), luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/codex/luci-app-codex/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-r2), luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/dockermanager/luci-app-dockermanager/Makefile": (
        "luci-lib-linkeaseauth (>=1.2.1-r4)",
        "luci-lib-linkeaseauth (>=1.2.1-r4)",
        "luci-lib-linkeaseauth (>=1.2.1-r4)",
    ),
    "apps/fastnet/luci-app-fastnet/Makefile": (
        "fastnet (>=0.8.10-$(if $(CONFIG_USE_APK),r)4)",
        "fastnet (>=0.8.10-4)",
        "fastnet (>=0.8.10-r4)",
    ),
    "apps/istorerouter/luci-app-istorerouter/Makefile": (
        "luci-lib-taskd (>=1.0.15)",
        "luci-lib-taskd (>=1.0.15)",
        "luci-lib-taskd (>=1.0.15)",
    ),
    "apps/istorex/luci-app-istorex/Makefile": (
        "luci-lib-taskd (>=1.0.15)",
        "luci-lib-taskd (>=1.0.15)",
        "luci-lib-taskd (>=1.0.15)",
    ),
    "apps/kaiplus/kaiplus/Makefile": (
        "changeguard (>=0.3.5-$(if $(CONFIG_USE_APK),r)2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "changeguard (>=0.3.5-2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "changeguard (>=0.3.5-r2), luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/kaiplus/luci-app-kaiplus/Makefile": (
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
        "luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/kimi/kimi/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-r2), luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/kimi/luci-app-kimi/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-r2), luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/linkease/linkease-runtime-transition/Makefile": (
        "linkease (>=1.7.6~0), luci-lib-linkeasefile (>=2.1.70-r4)",
        "linkease (>=1.7.6~0), luci-lib-linkeasefile (>=2.1.70-r4)",
        "linkease (>=1.7.6~0), luci-lib-linkeasefile (>=2.1.70-r4)",
    ),
    "apps/linkease/linkease/Makefile": (
        "linkease-common-bin (>=1.7.6~0)",
        "linkease-common-bin (>=1.7.6~0)",
        "linkease-common-bin (>=1.7.6~0)",
    ),
    "apps/linkease/luci-app-linkease/Makefile": (
        "luci-lib-linkeasefile (>=2.1.70-r4)",
        "luci-lib-linkeasefile (>=2.1.70-r4)",
        "luci-lib-linkeasefile (>=2.1.70-r4)",
    ),
    "apps/linkeasefull/linkeasefull/Makefile": (
        "linkease-common-bin (>=1.7.6~0)",
        "linkease-common-bin (>=1.7.6~0)",
        "linkease-common-bin (>=1.7.6~0)",
    ),
    "apps/mise/luci-app-mise/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)1)",
        "mise-runtime (>=0.1.1-1)",
        "mise-runtime (>=0.1.1-r1)",
    ),
    "apps/mise/mise-runtime/Makefile": (
        "mise (>=2026.8.14-$(if $(CONFIG_USE_APK),r)28)",
        "mise (>=2026.8.14-28)",
        "mise (>=2026.8.14-r28)",
    ),
    "apps/openclawmgr/luci-app-openclawmgr/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)2)",
        "mise-runtime (>=0.1.1-2)",
        "mise-runtime (>=0.1.1-r2)",
    ),
    "apps/opencode/luci-app-opencode/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-r2), luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/opencode/opencode/Makefile": (
        "mise-runtime (>=0.1.1-$(if $(CONFIG_USE_APK),r)2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-2), luci-lib-linkeaseauth (>=1.2.1-r5)",
        "mise-runtime (>=0.1.1-r2), luci-lib-linkeaseauth (>=1.2.1-r5)",
    ),
    "apps/runmynas/luci-app-runmynas/Makefile": (
        "luci-lib-iform (>=1.1)",
        "luci-lib-iform (>=1.1)",
        "luci-lib-iform (>=1.1)",
    ),
    "apps/systools/luci-app-systools/Makefile": (
        "luci-lib-iform (>=1.1)",
        "luci-lib-iform (>=1.1)",
        "luci-lib-iform (>=1.1)",
    ),
    "apps/ubuntu/luci-app-ubuntu/Makefile": (
        "luci-lib-iform (>=1.1)",
        "luci-lib-iform (>=1.1)",
        "luci-lib-iform (>=1.1)",
    ),
}


def declarations():
    result = {}
    pattern = re.compile(r"^[ \t]*(?:LUCI_)?EXTRA_DEPENDS[ \t]*:=[ \t]*(.+)$", re.MULTILINE)
    for makefile in ROOT.glob("apps/**/Makefile"):
        matches = pattern.findall(makefile.read_text(encoding="utf-8"))
        if matches:
            result[str(makefile.relative_to(ROOT))] = matches
    return result


class ExtraDependsContractTest(unittest.TestCase):
    def test_every_extra_depends_declaration_is_audited(self):
        actual = declarations()
        self.assertEqual(set(actual), set(EXPECTED))
        for relative, (source, _, _) in EXPECTED.items():
            with self.subTest(package=relative):
                self.assertEqual(actual[relative], [source])

    def test_opkg_and_apk_expansions_are_valid(self):
        dependency = re.compile(r"^[a-zA-Z0-9+_.-]+ \((?:>=|<=|=|>|<)[^ ()]+\)$")
        selector = "$(if $(CONFIG_USE_APK),r)"
        for relative, (source, expected_opkg, expected_apk) in EXPECTED.items():
            with self.subTest(package=relative, package_manager="opkg"):
                expanded = source.replace(selector, "")
                self.assertEqual(expanded, expected_opkg)
                for item in expanded.split(", "):
                    self.assertRegex(item, dependency)
            with self.subTest(package=relative, package_manager="apk"):
                expanded = source.replace(selector, "r")
                self.assertEqual(expanded, expected_apk)
                for item in expanded.split(", "):
                    self.assertRegex(item, dependency)

    def test_mise_runtime_satisfies_every_declared_floor(self):
        runtime_recipe = (ROOT / "apps/mise/mise-runtime/Makefile").read_text(encoding="utf-8")
        runtime_version = re.search(r"^PKG_VERSION:=(.+)$", runtime_recipe, re.MULTILINE).group(1)
        runtime_release = int(
            re.search(r"^PKG_RELEASE:=(\d+)$", runtime_recipe, re.MULTILINE).group(1)
        )
        floor = re.compile(
            r"mise-runtime \(>=(?P<version>[0-9.]+)-"
            r"\$\(if \$\(CONFIG_USE_APK\),r\)(?P<release>\d+)\)"
        )
        for relative, (source, _, _) in EXPECTED.items():
            match = floor.search(source)
            if not match:
                continue
            with self.subTest(package=relative):
                self.assertEqual(match.group("version"), runtime_version)
                self.assertGreaterEqual(runtime_release, int(match.group("release")))


if __name__ == "__main__":
    unittest.main()
