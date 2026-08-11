import unittest
from pathlib import Path


POLICY = (Path(__file__).resolve().parents[1] / "AGENTS.md").read_text(
    encoding="utf-8"
)


class PolicyTests(unittest.TestCase):
    def test_sol_responsibilities(self):
        for responsibility in (
            "planner",
            "architect",
            "orchestrator",
            "ambiguity resolver",
            "final reviewer",
        ):
            self.assertIn(responsibility, POLICY)

    def test_daily_role_mapping(self):
        for role in (
            "luna_low",
            "luna_medium",
            "luna_high",
            "luna_xhigh",
            "luna_max",
        ):
            self.assertIn(role, POLICY)
        self.assertIn(".var/daily-profile.json", POLICY)

    def test_luna_scope_and_context_firewall(self):
        self.assertIn("bounded execution workers", POLICY)
        self.assertIn("Task Contract", POLICY)
        self.assertIn("context firewall", POLICY)
        self.assertIn("must not spawn", POLICY)

    def test_acceptance_gate_and_parallel_limit(self):
        self.assertIn("Sol alone declares", POLICY)
        self.assertIn("at most three spawned threads", POLICY)

    def test_no_hook_enforcement_requirement(self):
        self.assertIn("Do not add Hook routing", POLICY)
        self.assertNotIn("PreToolUse", POLICY)
        self.assertNotIn("SubagentStart", POLICY)
        self.assertNotIn("SubagentStop", POLICY)


if __name__ == "__main__":
    unittest.main()
