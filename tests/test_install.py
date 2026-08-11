import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.install import (
    FUTURE_ARTIFACTS,
    STABLE_AGENT_FILES,
    UnsafeTarget,
    build_plan,
    resolve_codex_home,
    validate_target,
)


ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = datetime(2026, 8, 11, tzinfo=timezone.utc)


class InstallPlanTests(unittest.TestCase):
    def test_dry_run_plan_never_mutates_target(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            before = list(Path(directory).rglob("*"))
            plan = build_plan(target, generated_at=FIXED_TIME)
            after = list(Path(directory).rglob("*"))
            self.assertEqual(before, after)
            self.assertEqual(plan["mode"], "dry-run")
            self.assertFalse(plan["will_modify"])
            self.assertFalse(plan["backup_plan"]["will_create"])
            self.assertEqual(
                [Path(action["source"]).name for action in plan["actions"]],
                list(STABLE_AGENT_FILES),
            )

    def test_future_inventory_is_rc1_minimum_and_excludes_legacy_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            plan = build_plan(target, generated_at=FIXED_TIME)

            inventory = plan["future_artifacts"]
            self.assertEqual(len(inventory), 8)
            expected = {
                ".codex/agents/luna-low.toml": (
                    "agents/luna-low.toml",
                    "agent-conflict-check",
                ),
                ".codex/agents/luna-medium.toml": (
                    "agents/luna-medium.toml",
                    "agent-conflict-check",
                ),
                ".codex/agents/luna-high.toml": (
                    "agents/luna-high.toml",
                    "agent-conflict-check",
                ),
                ".codex/agents/luna-xhigh.toml": (
                    "agents/luna-xhigh.toml",
                    "agent-conflict-check",
                ),
                ".codex/agents/luna-max.toml": (
                    "agents/luna-max.toml",
                    "agent-conflict-check",
                ),
                "AGENTS.md": ("AGENTS.md", "merge-policy"),
                "src/selector.py": (
                    "sol-luna-v4/selector.py",
                    "copy-if-absent",
                ),
                ".codex/config.toml": ("config.toml", "merge-agents-config"),
            }
            self.assertEqual(
                {item["source"] for item in inventory}, set(expected)
            )
            for item in inventory:
                destination, strategy = expected[item["source"]]
                self.assertEqual(item["destination"], destination)
                self.assertEqual(item["strategy"], strategy)
                self.assertEqual(
                    Path(item["source_path"]),
                    (ROOT / item["source"]).resolve(),
                )
                self.assertEqual(
                    Path(item["destination_path"]),
                    (target / destination).resolve(),
                )

            rendered = json.dumps(plan).lower()
            for excluded in (
                "luna-leaf-experiment",
                "hook",
                "managed",
                "registry",
                "slr_",
                "v3.2.1",
            ):
                self.assertNotIn(excluded, rendered)
            self.assertEqual(
                {item["source"] for item in FUTURE_ARTIFACTS}, set(expected)
            )

    def test_conflict_detection_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            agents = target / "agents"
            agents.mkdir(parents=True)
            conflict = agents / "luna-low.toml"
            conflict.write_text("user-owned content\n", encoding="utf-8")
            plan = build_plan(target, generated_at=FIXED_TIME)
            self.assertIn(str(conflict.resolve()), plan["conflicts"])
            self.assertEqual(conflict.read_text(encoding="utf-8"), "user-owned content\n")

    def test_path_safety_rejects_root_and_repo_overlap(self):
        with self.assertRaises(UnsafeTarget):
            validate_target(Path(ROOT.anchor), ROOT)
        with self.assertRaises(UnsafeTarget):
            validate_target(ROOT / ".codex-home", ROOT)

    def test_codex_home_resolution_uses_only_named_setting(self):
        with tempfile.TemporaryDirectory() as directory:
            expected = Path(directory) / "codex-home"
            resolved = resolve_codex_home(
                None,
                environ={"CODEX_HOME": str(expected), "API_KEY": "do-not-copy"},
                user_home=Path(directory),
            )
            self.assertEqual(resolved, expected.resolve())

    def test_plan_does_not_leak_unrelated_environment_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = build_plan(Path(directory) / ".codex", generated_at=FIXED_TIME)
            rendered = json.dumps(plan)
            self.assertNotIn("API_KEY", rendered)
            self.assertNotIn("token", rendered.lower())


if __name__ == "__main__":
    unittest.main()
