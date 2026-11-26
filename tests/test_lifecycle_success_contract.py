import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


TARGET_HOOKS = [
    ("apps/ddnsto/ddnsto/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/fail2banop/fail2banop/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/kai/kai_session/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/linkease/linkease/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/linkeasefull/linkeasefull/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/mise/mise/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/quickstart/quickstart/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/sunpanel/sunpanel/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/vmease/vmease/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/fastnet/fastnet/Makefile", "$(PKG_NAME)", "postinst"),
    ("apps/fastnet/luci-app-fastnet/Makefile", "luci-app-fastnet", "postinst"),
    ("apps/fastnet/luci-app-fastnet/Makefile", "luci-app-fastnet", "prerm"),
    ("apps/fastnet/app-meta-fastnet/Makefile", "app-meta-fastnet", "postinst"),
]


def hook_body(relative_path, package, phase):
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    match = re.search(
        rf"^define Package/{re.escape(package)}/{phase}\n(.*?)^endef$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise AssertionError(f"missing {package}/{phase} in {relative_path}")
    return match.group(1)


class LifecycleSuccessContract(unittest.TestCase):
    def test_target_hooks_end_with_explicit_success(self):
        for relative_path, package, phase in TARGET_HOOKS:
            with self.subTest(path=relative_path, package=package, phase=phase):
                body = hook_body(relative_path, package, phase)
                statements = [
                    line.strip()
                    for line in body.splitlines()
                    if line.strip()
                    and line.strip() != "#!/bin/sh"
                    and not line.lstrip().startswith("#")
                ]
                self.assertTrue(statements)
                self.assertEqual(statements[-1], "exit 0")

    def test_fastnet_hooks_cannot_abort_package_transactions(self):
        for relative_path, package, phase in TARGET_HOOKS[-4:]:
            with self.subTest(path=relative_path, phase=phase):
                body = hook_body(relative_path, package, phase)
                self.assertNotRegex(body, r"(?m)^\s*set\s+-[^\n]*e")
                self.assertNotRegex(body, r"\|\|\s*exit\b")
                self.assertNotRegex(body, r"(?m)^\s*exec\s+")

    def test_fastnet_hooks_swallow_failing_helpers(self):
        cases = [
            ("apps/fastnet/fastnet/Makefile", "$(PKG_NAME)", "postinst", "usr/share/fastnet/register-desktop.sh"),
            ("apps/fastnet/luci-app-fastnet/Makefile", "luci-app-fastnet", "postinst", "usr/libexec/fastnet-card-register"),
            ("apps/fastnet/luci-app-fastnet/Makefile", "luci-app-fastnet", "prerm", "usr/libexec/fastnet-card-register"),
            ("apps/fastnet/app-meta-fastnet/Makefile", "app-meta-fastnet", "postinst", "usr/share/fastnet/register-desktop.sh"),
        ]
        for relative_path, package, phase, helper_path in cases:
            with self.subTest(path=relative_path, phase=phase), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                helper = root / helper_path
                helper.parent.mkdir(parents=True)
                helper.write_text("#!/bin/sh\nprintf '%s\\n' 'simulated helper failure' >&2\nexit 7\n")
                helper.chmod(0o755)
                body = hook_body(relative_path, package, phase).replace("$$", "$")
                result = subprocess.run(
                    ["sh", "-s"],
                    input=body,
                    text=True,
                    env={**os.environ, "IPKG_INSTROOT": directory},
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("simulated helper failure", result.stderr)

    def test_fastnet_build_sources_live_in_openwrt_app_actions(self):
        mapping = (ROOT / "syncapps.yaml").read_text(encoding="utf-8")
        block = mapping.split("\n    fastnet:\n", 1)[1].split("\n    feishuvpn:\n", 1)[0]
        self.assertIn("remote: openwrt-app-actions/applications/fastnet", block)
        self.assertIn("remote: openwrt-app-actions/applications/luci-app-fastnet", block)
        self.assertNotIn("remote: nas-packages/network/services/fastnet", block)
        self.assertNotIn("remote: nas-packages-luci/luci/luci-app-fastnet", block)


if __name__ == "__main__":
    unittest.main()
