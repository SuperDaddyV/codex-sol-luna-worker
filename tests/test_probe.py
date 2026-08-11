import subprocess
import unittest
from unittest.mock import patch

from scripts.probe_capabilities import EFFORTS, build_command, run_probe


class CapabilityProbeTests(unittest.TestCase):
    def test_commands_are_ephemeral_and_ignore_user_config(self):
        command = build_command("codex", "max")
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--strict-config", command)
        self.assertIn('model_reasoning_effort="max"', command)

    @patch("scripts.probe_capabilities.subprocess.run")
    def test_successful_client_run_is_supported_even_if_echo_is_not_exact(self, run):
        calls = []
        for effort in EFFORTS:
            marker = f"LUNA_CAPABILITY_{effort.upper()}_OK"
            output = marker if effort != "high" else f"Result: {marker}"
            calls.append(subprocess.CompletedProcess([], 0, output, ""))
        calls.append(subprocess.CompletedProcess([], 0, "codex-cli fixture", ""))
        run.side_effect = calls

        result = run_probe("codex", timeout=1)

        self.assertTrue(result["all_supported"])
        high = next(item for item in result["results"] if item["effort"] == "high")
        self.assertTrue(high["supported"])
        self.assertFalse(high["response_exact"])


if __name__ == "__main__":
    unittest.main()
