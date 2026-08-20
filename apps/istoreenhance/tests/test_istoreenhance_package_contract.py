from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class IStoreEnhancePackageContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_runtime_package_tracks_kspeeder_release_asset(self):
        makefile = self.read("istoreenhance/Makefile")

        self.assertIn("PKG_SOURCE_DATE:=0.7.15", makefile)
        self.assertIn("PKG_SOURCE:=iStoreEnhance-binary-$(PKG_SOURCE_DATE).tar.gz", makefile)
        self.assertIn(
            "PKG_SOURCE_URL:=https://github.com/kspeeder/docker_kspeeder/releases/download/v$(PKG_SOURCE_DATE)/",
            makefile,
        )
        self.assertIn(
            "PKG_HASH:=1957ff2f4957e655b7c6eb9db227abbdd3b2da6d0cb623978c7da18b61035494",
            makefile,
        )
        self.assertIn("PKG_BUILD_DIR:=$(BUILD_DIR)/iStoreEnhance-binary-$(PKG_SOURCE_DATE)", makefile)

    def test_meta_package_shows_runtime_version(self):
        makefile = self.read("app-meta-istoreenhance/Makefile")

        self.assertIn("PKG_VERSION:=0.7.15", makefile)


if __name__ == "__main__":
    unittest.main()
