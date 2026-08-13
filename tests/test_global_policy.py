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

    def test_delegation_receipt_is_evidence_based_and_low_noise(self):
        self.assertIn("## Delegation Receipt", TEMPLATE)
        for outcome in (
            "DELEGATED",
            "TASK_TOO_SMALL",
            "SOL_REASONING_TASK",
            "NO_INDEPENDENT_WORK",
            "LUNA_UNAVAILABLE",
        ):
            self.assertIn(outcome, TEMPLATE)
        for receipt in (
            "Sol/Luna: delegated",
            "Sol/Luna: Sol-only \u00b7 task too small",
            "Sol/Luna: Sol-only \u00b7 reasoning/architecture task",
            "Sol/Luna: Sol-only \u00b7 no independent bounded work",
            "Sol/Luna: Sol-only \u00b7 Luna unavailable",
        ):
            self.assertIn(receipt, TEMPLATE)

        self.assertIn("non-trivial user task", TEMPLATE)
        self.assertIn("Omit it for casual conversation", TEMPLATE)
        self.assertIn("must not lower the delegation threshold", TEMPLATE)
        self.assertIn("must not influence whether Sol delegates", TEMPLATE)
        self.assertIn("actual selected native role", TEMPLATE)
        self.assertIn("actual direct Luna children", TEMPLATE)
        self.assertIn("actually overlapped in execution", TEMPLATE)
        self.assertIn("If overlap cannot be established", TEMPLATE)
        self.assertIn("reasonable delegation opportunity existed", TEMPLATE)
        self.assertIn("Do not invoke the selector", TEMPLATE)
        self.assertIn("spawn or inspect a child", TEMPLATE)
        self.assertIn("read files, call tools or networks", TEMPLATE)
        self.assertIn("write state", TEMPLATE)
        self.assertIn("add telemetry", TEMPLATE)
        self.assertIn("not runtime attestation", TEMPLATE)
        self.assertIn("Never expose hidden chain-of-thought", TEMPLATE)

        self.assertIn("<SELECTOR_COMMAND>", TEMPLATE)
        self.assertIn("Do not substitute a direct model", TEMPLATE)
        self.assertIn("Never select `ultra`", TEMPLATE)

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
