import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / ".codex" / "agents"
EXPECTED = {
    "luna-low.toml": ("luna_low", "low"),
    "luna-medium.toml": ("luna_medium", "medium"),
    "luna-high.toml": ("luna_high", "high"),
    "luna-xhigh.toml": ("luna_xhigh", "xhigh"),
    "luna-max.toml": ("luna_max", "max"),
}


class AgentConfigTests(unittest.TestCase):
    def test_five_formal_agent_files(self):
        self.assertEqual({path.name for path in AGENT_DIR.glob("*.toml")}, set(EXPECTED))

    def test_agent_schema_and_efforts(self):
        names = set()
        for filename, (expected_name, expected_effort) in EXPECTED.items():
            with (AGENT_DIR / filename).open("rb") as handle:
                config = tomllib.load(handle)
            self.assertEqual(config["name"], expected_name)
            self.assertNotIn(config["name"], names)
            names.add(config["name"])
            self.assertEqual(config["model"], "gpt-5.6-luna")
            self.assertEqual(config["model_reasoning_effort"], expected_effort)
            self.assertNotEqual(config["model_reasoning_effort"], "ultra")
            self.assertTrue(config["description"].strip())
            instructions = config["developer_instructions"]
            self.assertTrue(instructions.strip())
            self.assertFalse(config["agents"]["enabled"])
            self.assertIn("Complete only the bounded task assigned by the parent Sol agent.", instructions)
            self.assertIn("Do not expand scope, redefine architecture, or make the final acceptance decision.", instructions)
            self.assertIn("Do not spawn, organize, or delegate to other agents.", instructions)

    def test_project_agent_limits(self):
        with (ROOT / ".codex" / "config.toml").open("rb") as handle:
            config = tomllib.load(handle)
        self.assertTrue(config["agents"]["enabled"])
        self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 3)
        self.assertNotIn("default_subagent_model", config["agents"])
        self.assertNotIn("default_subagent_reasoning_effort", config["agents"])

if __name__ == "__main__":
    unittest.main()
