import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


APPS = {
    "codex": {
        "service": "codex",
        "runtime": "codex-runtime",
        "controller": "codex.lua",
        "view": "codex/status.htm",
        "prefix": "codex",
    },
    "claude-code": {
        "service": "claude",
        "runtime": "claude-runtime",
        "controller": "claude.lua",
        "view": "claude/status.htm",
        "prefix": "claude",
    },
    "kimi": {
        "service": "kimi",
        "runtime": "kimi-runtime",
        "controller": "kimi.lua",
        "view": "kimi/status.htm",
        "prefix": "kimi",
    },
    "opencode": {
        "service": "opencode",
        "runtime": "opencode-runtime",
        "controller": "opencode.lua",
        "view": "opencode/status.htm",
        "prefix": "opencode",
    },
}


class CodingAgentRuntimeGuidanceTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text()

    def test_missing_runtime_storage_does_not_fail_meta_configuration(self):
        for app, values in APPS.items():
            with self.subTest(app=app):
                config = self.read(f"apps/{app}/app-meta-{app}/config.sh")
                guard = 'if [ -z "$runtime_root" ]; then'
                prepare = f'/usr/libexec/{values["runtime"]} prepare "$data_dir"'
                self.assertIn('uci -q get mise.main.storage_root', config)
                self.assertIn(guard, config)
                self.assertIn(f'/etc/init.d/{values["service"]} stop || true', config)
                self.assertIn('exit 0', config)
                self.assertLess(config.index(guard), config.index(prepare))

    def test_every_management_page_guides_runtime_storage_setup(self):
        for app, values in APPS.items():
            with self.subTest(app=app):
                base = f"apps/{app}"
                package = self.read(f'{base}/{app}/files/{values["prefix"]}-package.lua')
                runtime = self.read(f'{base}/{app}/files/{values["prefix"]}-runtime.lua')
                controller = self.read(
                    f'{base}/luci-app-{app}/luasrc/controller/{values["controller"]}'
                )
                status = self.read(
                    f'{base}/luci-app-{app}/luasrc/view/{values["view"]}'
                )
                self.assertIn("storage_configured", package)
                self.assertIn(
                    "Configure persistent storage in Runtime Environments", runtime
                )
                self.assertIn('next = "runtime-storage"', controller)
                self.assertIn(f'{values["prefix"]}-storage-guide', status)
                self.assertIn("先配置运行时存储", status)
                self.assertIn("前往运行时环境", status)
                self.assertIn("!storageReady", status)


if __name__ == "__main__":
    unittest.main()
