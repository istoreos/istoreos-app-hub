import unittest

from verify_quickstart_runtime import version_is_safe


class QuickstartRuntimeVerifierTest(unittest.TestCase):
    def test_go_security_floors_are_branch_aware(self) -> None:
        self.assertFalse(version_is_safe("1.25.12"))
        self.assertFalse(version_is_safe("1.26.10"))
        self.assertTrue(version_is_safe("1.26.11"))
        self.assertFalse(version_is_safe("1.27.3"))
        self.assertTrue(version_is_safe("1.27.4"))
        self.assertTrue(version_is_safe("1.28.0"))


if __name__ == "__main__":
    unittest.main()
