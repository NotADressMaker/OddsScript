import unittest

from sportsbetlang.lang.sandbox import HostCapabilities, SandboxViolation


class TestSandboxCapabilities(unittest.TestCase):
    def test_default_deny_read(self):
        caps = HostCapabilities(no_io=False)
        with self.assertRaises(SandboxViolation):
            caps.check_read_path("/tmp/test.txt")

    def test_allowlist_read(self):
        caps = HostCapabilities(no_io=False, allow_read_dirs=["/tmp"])
        caps.check_read_path("/tmp/file.txt")

    def test_domain_allowlist(self):
        caps = HostCapabilities(no_io=False, allow_domains=["example.com"])
        caps.check_domain("https://api.example.com/v1")
        with self.assertRaises(SandboxViolation):
            caps.check_domain("https://openai.com")


if __name__ == "__main__":
    unittest.main()
