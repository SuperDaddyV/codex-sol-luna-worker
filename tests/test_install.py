import json
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.install import (
    FUTURE_ARTIFACTS,
    InstallerError,
    MANIFEST_RELATIVE,
    STABLE_AGENT_FILES,
    UnsafeTarget,
    VERSION,
    _compare_project_semver,
    build_plan,
    dry_run_install,
    install,
    resolve_codex_home,
    validate_target,
)


ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = datetime(2026, 8, 11, tzinfo=timezone.utc)
VALIDATION_ROOT = ROOT / ".tmp" / "installer-validation" / "plan-tests"


def validation_directory():
    VALIDATION_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=VALIDATION_ROOT)


def tree_hash(root):
    digest = hashlib.sha256()
    if root.exists():
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


class InstallPlanTests(unittest.TestCase):
    def test_dry_run_plan_never_mutates_target(self):
        with validation_directory() as directory:
            target = Path(directory) / ".codex"
            before = list(Path(directory).rglob("*"))
            plan = build_plan(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            after = list(Path(directory).rglob("*"))
            self.assertEqual(before, after)
            self.assertEqual(plan["mode"], "dry-run")
            self.assertFalse(plan["will_modify"])
            self.assertFalse(plan["backup_plan"]["will_create"])
            self.assertEqual(
                [Path(action["source"]).name for action in plan["actions"]],
                list(STABLE_AGENT_FILES),
            )

    def test_future_inventory_is_stable_minimum_and_excludes_legacy_layers(self):
        with validation_directory() as directory:
            target = Path(directory) / ".codex"
            plan = build_plan(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )

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
                "templates/AGENTS.global.md": ("AGENTS.md", "merge-policy"),
                "src/selector.py": (
                    "sol-luna-v4/selector.py",
                    "copy-if-owned",
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
        with validation_directory() as directory:
            target = Path(directory) / ".codex"
            agents = target / "agents"
            agents.mkdir(parents=True)
            conflict = agents / "luna-low.toml"
            conflict.write_text("user-owned content\n", encoding="utf-8")
            plan = build_plan(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            self.assertIn(str(conflict.resolve()), plan["conflicts"])
            self.assertEqual(conflict.read_text(encoding="utf-8"), "user-owned content\n")

    def test_path_safety_rejects_root_and_repo_overlap(self):
        with self.assertRaises(UnsafeTarget):
            validate_target(Path(ROOT.anchor), ROOT)
        with self.assertRaises(UnsafeTarget):
            validate_target(ROOT / ".codex-home", ROOT)

    def test_codex_home_resolution_uses_only_named_setting(self):
        with validation_directory() as directory:
            expected = Path(directory) / "codex-home"
            resolved = resolve_codex_home(
                None,
                environ={"CODEX_HOME": str(expected), "API_KEY": "do-not-copy"},
                user_home=Path(directory),
            )
            self.assertEqual(resolved, expected.resolve())

    def test_plan_does_not_leak_unrelated_environment_secrets(self):
        with validation_directory() as directory:
            plan = build_plan(
                Path(directory) / ".codex",
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            rendered = json.dumps(plan)
            self.assertNotIn("API_KEY", rendered)
            self.assertNotIn("token", rendered.lower())

    def test_plan_uses_cross_platform_path_abstraction(self):
        with validation_directory() as directory:
            target = Path(directory) / ".codex"
            for platform_name in ("Windows", "Linux", "Darwin"):
                with self.subTest(platform_name=platform_name):
                    plan = build_plan(
                        target,
                        platform_name=platform_name,
                        generated_at=FIXED_TIME,
                        allow_validation_sandbox=True,
                    )
                    self.assertTrue(plan["platform_supported"])
                    self.assertEqual(plan["platform"], platform_name)

    def test_dry_run_uses_transaction_ownership_preflight(self):
        with validation_directory() as directory:
            target = Path(directory) / ".codex"
            before = tree_hash(Path(directory))
            result = dry_run_install(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            self.assertEqual(result["status"], "DRY_RUN_PASS")
            self.assertEqual(result["effective_changes"], 9)
            self.assertFalse(result["will_modify"])
            self.assertIsNone(result["backup"])
            self.assertFalse(target.exists())
            self.assertEqual(tree_hash(Path(directory)), before)

            install(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            selector = target / "sol-luna-v4" / "selector.py"
            selector.write_bytes(selector.read_bytes() + b"\n# user change\n")
            changed = tree_hash(target)
            with self.assertRaises(InstallerError) as raised:
                dry_run_install(
                    target,
                    generated_at=FIXED_TIME,
                    allow_validation_sandbox=True,
                )
            self.assertEqual(raised.exception.reason_code, "OWNERSHIP_CONFLICT")
            self.assertEqual(tree_hash(target), changed)

    def test_source_commit_is_strict_and_preserved_correctly(self):
        with validation_directory() as directory:
            target = Path(directory) / ".codex"
            with patch(
                "scripts.install._ensure_target_writable",
                side_effect=AssertionError("write probe must not run"),
            ):
                with self.assertRaises(InstallerError) as raised:
                    install(
                        target,
                        generated_at=FIXED_TIME,
                        allow_validation_sandbox=True,
                        source_commit="not-a-sha",
                    )
            self.assertEqual(raised.exception.reason_code, "SOURCE_COMMIT_INVALID")
            self.assertFalse(target.exists())

            commit = "A" * 40
            install(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
                source_commit=commit,
            )
            manifest_path = target / MANIFEST_RELATIVE
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_commit"], commit.lower())

            second = install(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(
                json.loads(manifest_path.read_text(encoding="utf-8"))["source_commit"],
                commit.lower(),
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "v4.1.0-rc4"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            upgraded = install(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            self.assertEqual(upgraded["status"], "UPGRADED")
            self.assertNotIn(
                "source_commit",
                json.loads(manifest_path.read_text(encoding="utf-8")),
            )

    def test_already_latest_has_zero_write_and_zero_backup(self):
        with validation_directory() as directory:
            target = Path(directory) / ".codex"
            install(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            before = tree_hash(target)
            dry = dry_run_install(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            self.assertEqual(dry["status"], "IDEMPOTENT_PASS")
            self.assertEqual(dry["effective_changes"], 0)
            self.assertIsNone(dry["backup"])
            second = install(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)
            self.assertIsNone(second["backup"])
            self.assertEqual(tree_hash(target), before)

    def test_current_newer_never_downgrades(self):
        with validation_directory() as directory:
            target = Path(directory) / ".codex"
            install(
                target,
                generated_at=FIXED_TIME,
                allow_validation_sandbox=True,
            )
            manifest_path = target / MANIFEST_RELATIVE
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "v4.1.2"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            before = tree_hash(target)
            for action in (dry_run_install, install):
                with self.subTest(action=action.__name__):
                    with self.assertRaises(InstallerError) as raised:
                        action(
                            target,
                            generated_at=FIXED_TIME,
                            allow_validation_sandbox=True,
                        )
                    self.assertEqual(
                        raised.exception.reason_code, "CURRENT_VERSION_NEWER"
                    )
                    self.assertEqual(tree_hash(target), before)

    def test_v411_candidate_and_historical_semver_contract(self):
        self.assertEqual(VERSION, "v4.1.1")
        self.assertGreater(_compare_project_semver(VERSION, "v4.1.0"), 0)
        self.assertGreater(_compare_project_semver(VERSION, "v4.1.0-rc6"), 0)
        self.assertGreater(_compare_project_semver("v4.1.0-rc6", "v4.1.0-rc5"), 0)
        self.assertGreater(_compare_project_semver("v4.1.0-rc5", "v4.1.0-rc4"), 0)
        self.assertLess(_compare_project_semver("v4.1.0-rc6.1", "v4.1.0-rc6.beta"), 0)
        for invalid in ("v4.01.0", "v4.1.0+build", "4.1.0", "v4.1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(InstallerError):
                    _compare_project_semver(invalid, VERSION)


if __name__ == "__main__":
    unittest.main()
