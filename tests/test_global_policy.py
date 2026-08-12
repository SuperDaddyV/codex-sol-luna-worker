import unittest
from pathlib import Path

from scripts.install import render_global_policy


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates" / "AGENTS.global.md").read_text(encoding="utf-8")


class GlobalPolicyTests(unittest.TestCase):
    def test_template_is_global_safe(self):
        for forbidden in (
            ".var",
            "RUNTIME_TESTS.md",
            "GitHub",
            "tests/",
            "tests\\",
        ):
            self.assertNotIn(forbidden, TEMPLATE)
        self.assertIn("<CODEX_HOME>", TEMPLATE)
        self.assertIn("<SELECTOR_COMMAND>", TEMPLATE)
        self.assertIn("[agents] enabled = false", TEMPLATE)

    def test_windows_rendering_quotes_paths(self):
        rendered = render_global_policy(
            TEMPLATE, r"C:\Program Data\Codex Home", platform_name="Windows"
        )
        self.assertIn(r'python "C:\Program Data\Codex Home\sol-luna-v4\selector.py"', rendered)
        self.assertIn(r'--state-dir "C:\Program Data\Codex Home\sol-luna-v4\state"', rendered)
        self.assertIn("--ensure-daily --print-role", rendered)
        self.assertNotIn("<CODEX_HOME>", rendered)

    def test_linux_rendering_quotes_paths(self):
        rendered = render_global_policy(
            TEMPLATE, "/opt/Codex Home", platform_name="Linux"
        )
        self.assertIn("python '/opt/Codex Home/sol-luna-v4/selector.py'", rendered)
        self.assertIn("--state-dir '/opt/Codex Home/sol-luna-v4/state'", rendered)

    def test_macos_rendering_quotes_paths(self):
        rendered = render_global_policy(
            TEMPLATE, "/Volumes/Codex Home", platform_name="Darwin"
        )
        self.assertIn("python '/Volumes/Codex Home/sol-luna-v4/selector.py'", rendered)
        self.assertIn("--state-dir '/Volumes/Codex Home/sol-luna-v4/state'", rendered)


if __name__ == "__main__":
    unittest.main()
