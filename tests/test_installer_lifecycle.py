import hashlib
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.install import (
    AGENTS_BEGIN,
    AGENTS_END,
    CONFIG_BEGIN,
    CONFIG_END,
    InstallerError,
    MANIFEST_RELATIVE,
    STABLE_AGENT_FILES,
    install,
    rollback,
    uninstall,
)


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_ROOT = ROOT / ".tmp" / "installer-validation" / "lifecycle-tests"
FIXED_TIME = datetime(2026, 8, 12, 0, 0, tzinfo=timezone.utc)
LEGACY_FIXTURE = ROOT / "fixtures" / "legacy-v3" / "manifest-3.2.json"


def sandbox():
    VALIDATION_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=VALIDATION_ROOT)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    if not root.exists():
        return digest.hexdigest()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def call_install(target: Path, **kwargs):
    return install(
        target,
        project_root=ROOT,
        generated_at=kwargs.pop("generated_at", FIXED_TIME),
        allow_validation_sandbox=True,
        **kwargs,
    )


def materialize_legacy_fixture(target: Path) -> dict:
    fixture = json.loads(LEGACY_FIXTURE.read_text(encoding="utf-8"))
    fixture["created_files"] = [
        path.replace("<installation>", "fixture")
        for path in fixture["created_files"]
    ]
    target.mkdir(parents=True, exist_ok=True)
    for relative in fixture["created_files"]:
        if relative in {"hooks.json", "sol-luna-router/install-manifest.json"}:
            continue
        write_text(target / relative, "legacy owned fixture\n")

    write_text(
        target / "config.toml",
        'user_model = "preserve"\n'
        "# BEGIN SOL_LUNA_DAILY_BEST_FEATURES\n"
        "legacy_feature = true\n"
        "# END SOL_LUNA_DAILY_BEST_FEATURES\n"
        "# BEGIN SOL_LUNA_DAILY_BEST_AGENTS\n"
        'legacy_worker = "remove"\n'
        "# END SOL_LUNA_DAILY_BEST_AGENTS\n",
    )
    write_text(
        target / "AGENTS.md",
        "User instruction stays.\n"
        "<!-- BEGIN SOL_LUNA_DAILY_BEST -->\n"
        "Legacy owned policy.\n"
        "<!-- END SOL_LUNA_DAILY_BEST -->\n",
    )
    old_group = {
        "hooks": [
            {
                "type": "command",
                "command": "python hooks/sol_luna_router.py",
            }
        ]
    }
    user_group = {
        "hooks": [{"type": "command", "command": "python hooks/user_hook.py"}]
    }
    hooks = {
        "description": "user and legacy hooks",
        "hooks": {
            "PreToolUse": [user_group, old_group],
            "SubagentStart": [old_group],
            "SubagentStop": [old_group],
            "SessionStart": [old_group],
        },
    }
    write_text(target / "hooks.json", json.dumps(hooks, indent=2) + "\n")
    write_text(target / "hooks" / "user_hook.py", "# user hook\n")
    write_text(target / "agents" / "user-agent.toml", 'name = "user_agent"\n')
    write_text(target / "sol-luna-router" / "user-note.txt", "preserve\n")
    write_text(
        target / "sol-luna-router" / "install-manifest.json",
        json.dumps(fixture, indent=2) + "\n",
    )
    return fixture


class InstallerLifecycleTests(unittest.TestCase):
    def test_clean_install_installs_only_native_v4_artifacts(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            result = call_install(target)

            self.assertEqual(result["status"], "INSTALLED")
            self.assertGreater(result["effective_changes"], 0)
            self.assertEqual(
                {path.name for path in (target / "agents").glob("*.toml")},
                set(STABLE_AGENT_FILES),
            )
            for path in (target / "agents").glob("*.toml"):
                with path.open("rb") as handle:
                    agent = tomllib.load(handle)
                self.assertEqual(agent["model"], "gpt-5.6-luna")
                self.assertFalse(agent["agents"]["enabled"])
            installed_policy = (target / "AGENTS.md").read_text()
            self.assertIn(AGENTS_BEGIN, installed_policy)
            self.assertIn(str(target.resolve()), installed_policy)
            self.assertIn("--ensure-daily --print-role", installed_policy)
            self.assertNotIn("<CODEX_HOME>", installed_policy)
            self.assertNotIn(".var", installed_policy)
            self.assertIn(CONFIG_BEGIN, (target / "config.toml").read_text())
            self.assertTrue((target / "sol-luna-v4" / "selector.py").is_file())
            self.assertTrue((target / MANIFEST_RELATIVE).is_file())
            manifest = json.loads((target / MANIFEST_RELATIVE).read_text())
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["version"], "v4.0.0-rc1")
            self.assertEqual(len(manifest["owned_files"]), 6)
            self.assertEqual(set(manifest["owned_blocks"]), {"AGENTS.md", "config.toml"})
            self.assertNotIn("installation_id", manifest)
            self.assertTrue(Path(result["backup"]).is_dir())
            self.assertFalse((target / "hooks.json").exists())
            self.assertFalse((target / "hooks").exists())
            self.assertFalse((target / ".var").exists())
            self.assertFalse((target / "daily-profile.json").exists())

    def test_merge_preserves_config_agents_policy_hooks_and_user_agents(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            original_agents = "User policy remains.\n"
            original_hook = b'{"hooks":{"UserEvent":[{"command":"user"}]}}\n'
            write_text(
                target / "config.toml",
                'model = "user-model"\n'
                "[mcp_servers.user]\n"
                'command = "user-tool"\n'
                "[agents]\n"
                'user_option = "keep"\n',
            )
            write_text(target / "AGENTS.md", original_agents)
            write_text(target / "agents" / "user-agent.toml", 'name = "user_agent"\n')
            (target / "hooks.json").write_bytes(original_hook)

            call_install(target)
            config = tomllib.loads((target / "config.toml").read_text())
            self.assertEqual(config["model"], "user-model")
            self.assertEqual(config["mcp_servers"]["user"]["command"], "user-tool")
            self.assertEqual(config["agents"]["user_option"], "keep")
            self.assertTrue(config["agents"]["enabled"])
            self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 3)
            self.assertTrue((target / "AGENTS.md").read_text().startswith(original_agents))
            self.assertEqual(
                (target / "agents" / "user-agent.toml").read_text(),
                'name = "user_agent"\n',
            )
            self.assertEqual((target / "hooks.json").read_bytes(), original_hook)

    def test_nonempty_agents_override_fails_closed_without_changes(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            write_text(target / "AGENTS.override.md", "User override takes priority.\n")
            before = tree_hash(target)
            with self.assertRaises(InstallerError) as raised:
                call_install(target)
            self.assertEqual(raised.exception.reason_code, "AGENTS_OVERRIDE_PRESENT")
            self.assertEqual(tree_hash(target), before)

    def test_second_install_is_idempotent(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)
            before = tree_hash(target)
            backups_before = list((target / "backups" / "sol-luna-v4").iterdir())
            second = call_install(target)
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)
            self.assertEqual(second["backup"], None)
            self.assertEqual(tree_hash(target), before)
            self.assertEqual(
                len(list((target / "backups" / "sol-luna-v4").iterdir())),
                len(backups_before),
            )

    def test_existing_agents_table_is_idempotent_and_uninstalls_exactly(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            original_config = (
                'model = "user-model"\n'
                "[agents]\n"
                'user_option = "keep"\n'
                "[mcp_servers.user]\n"
                'command = "user-tool"\n'
            )
            write_text(target / "config.toml", original_config)

            call_install(target)
            second = call_install(target)
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)

            result = uninstall(
                target,
                project_root=ROOT,
                generated_at=FIXED_TIME + timedelta(days=1),
                allow_validation_sandbox=True,
            )
            self.assertEqual(result["status"], "UNINSTALLED")
            self.assertEqual((target / "config.toml").read_text(), original_config)

    def test_upgrade_restores_leaf_removes_owned_experiment_and_rolls_back(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)
            manifest_path = target / MANIFEST_RELATIVE
            manifest = json.loads(manifest_path.read_text())
            for filename in STABLE_AGENT_FILES:
                path = target / "agents" / filename
                prototype = path.read_text().replace("\n[agents]\nenabled = false\n", "\n")
                self.assertNotIn("enabled = false", prototype)
                write_text(path, prototype)
                manifest["owned_files"][f"agents/{filename}"] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
            experiment_relative = "agents/luna-leaf-experiment.toml"
            experiment = b'name = "luna_leaf_experiment"\n'
            (target / experiment_relative).write_bytes(experiment)
            manifest["owned_files"][experiment_relative] = hashlib.sha256(
                experiment
            ).hexdigest()
            manifest["version"] = "v4.0.0-prototype"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            write_text(target / "agents" / "user-agent.toml", 'name = "user_agent"\n')
            before = tree_hash(target)

            upgraded = call_install(target, generated_at=FIXED_TIME + timedelta(days=1))
            self.assertEqual(upgraded["status"], "UPGRADED")
            self.assertFalse((target / experiment_relative).exists())
            for filename in STABLE_AGENT_FILES:
                with (target / "agents" / filename).open("rb") as handle:
                    self.assertFalse(tomllib.load(handle)["agents"]["enabled"])
            self.assertEqual(
                (target / "agents" / "user-agent.toml").read_text(),
                'name = "user_agent"\n',
            )
            self.assertTrue(Path(upgraded["backup"]).is_dir())

            rolled_back = rollback(
                target,
                Path(upgraded["backup"]),
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(rolled_back["status"], "ROLLBACK_EXACT_PASS")
            self.assertEqual(tree_hash(target), before)

    def test_sanitized_legacy_migration_removes_only_manifest_owned_content(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            fixture = materialize_legacy_fixture(target)
            before = tree_hash(target)
            result = call_install(target, migrate_legacy=True)

            self.assertEqual(result["migration"]["source_version"], fixture["version"])
            for relative in fixture["created_files"]:
                relative = relative.replace("<installation>", "fixture")
                if relative == "hooks.json":
                    continue
                self.assertFalse((target / relative).exists(), relative)
            self.assertTrue((target / "agents" / "user-agent.toml").is_file())
            self.assertTrue((target / "hooks" / "user_hook.py").is_file())
            self.assertTrue((target / "sol-luna-router" / "user-note.txt").is_file())
            hooks = json.loads((target / "hooks.json").read_text())
            self.assertEqual(len(hooks["hooks"]["PreToolUse"]), 1)
            self.assertNotIn("SubagentStart", hooks["hooks"])
            self.assertIn("User instruction stays.", (target / "AGENTS.md").read_text())
            self.assertNotIn("SOL_LUNA_DAILY_BEST", (target / "AGENTS.md").read_text())
            self.assertEqual(tomllib.loads((target / "config.toml").read_text())["user_model"], "preserve")
            self.assertFalse((target / "sol-luna-v4" / "state").exists())

            rollback(
                target,
                Path(result["backup"]),
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(tree_hash(target), before)

    def test_empty_legacy_created_hooks_file_is_removed(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            materialize_legacy_fixture(target)
            old_group = {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python hooks/sol_luna_router.py",
                    }
                ]
            }
            write_text(
                target / "hooks.json",
                json.dumps(
                    {
                        "description": "Sol Luna managed hooks",
                        "hooks": {
                            "PreToolUse": [old_group],
                            "SubagentStart": [old_group],
                            "SubagentStop": [old_group],
                            "SessionStart": [old_group],
                        },
                    },
                    indent=2,
                )
                + "\n",
            )
            call_install(target, migrate_legacy=True)
            self.assertFalse((target / "hooks.json").exists())

    def test_audit_bundles_are_untouched_and_backup_covers_commit_markers(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            materialize_legacy_fixture(target)
            audit = target / "sol-luna-router" / "audit-bundles" / "evidence.json"
            write_text(audit, '{"preserve": true}\n')
            audit_before = audit.read_bytes()

            result = call_install(target, migrate_legacy=True)

            self.assertEqual(audit.read_bytes(), audit_before)
            snapshot = json.loads(
                (Path(result["backup"]) / "snapshot.json").read_text(encoding="utf-8")
            )
            backed = {entry["path"] for entry in snapshot["entries"]}
            self.assertIn(MANIFEST_RELATIVE.as_posix(), backed)
            self.assertIn("sol-luna-router/install-manifest.json", backed)
            self.assertIn("agents/luna-low.toml", backed)
            self.assertIn("AGENTS.md", backed)
            self.assertIn("config.toml", backed)
            self.assertNotIn("sol-luna-router/audit-bundles/evidence.json", backed)

    def test_precommit_failpoints_restore_exact_tree(self):
        points = (
            "after_agent_install",
            "after_config_merge",
            "after_hook_removal",
            "after_old_file_deletion",
            "before_v4_manifest_write",
        )
        for point in points:
            with self.subTest(point=point), sandbox() as directory:
                target = Path(directory) / ".codex"
                materialize_legacy_fixture(target)
                write_text(
                    target / "sol-luna-router" / "audit-bundles" / "evidence.txt",
                    "preserve\n",
                )
                before = tree_hash(target)

                def failpoint(name, expected=point):
                    if name == expected:
                        self.assertFalse((target / MANIFEST_RELATIVE).exists())
                        raise OSError(f"fixture failure at {name}")

                with self.assertRaises(InstallerError) as raised:
                    call_install(target, migrate_legacy=True, failpoint=failpoint)
                self.assertEqual(raised.exception.reason_code, "APPLY_FAILED")
                self.assertEqual(tree_hash(target), before)

    def test_manifest_is_last_then_legacy_cleanup_is_postcommit(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            materialize_legacy_fixture(target)
            observed = []

            def observe(name):
                observed.append(name)
                if name != "legacy_manifest_cleanup":
                    self.assertFalse((target / MANIFEST_RELATIVE).exists())
                else:
                    self.assertTrue((target / MANIFEST_RELATIVE).is_file())
                    self.assertTrue(
                        (target / "sol-luna-router" / "install-manifest.json").is_file()
                    )

            result = call_install(target, migrate_legacy=True, failpoint=observe)
            self.assertEqual(result["status"], "INSTALLED")
            self.assertEqual(
                observed,
                [
                    "after_agent_install",
                    "after_config_merge",
                    "after_hook_removal",
                    "after_old_file_deletion",
                    "before_v4_manifest_write",
                    "legacy_manifest_cleanup",
                ],
            )
            manifest = json.loads((target / MANIFEST_RELATIVE).read_text())
            self.assertEqual(manifest["legacy_cleanup"]["status"], "complete")

    def test_postcommit_legacy_manifest_cleanup_failure_is_retryable(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            materialize_legacy_fixture(target)

            def fail_cleanup(name):
                if name == "legacy_manifest_cleanup":
                    raise OSError("fixture cleanup failure")

            result = call_install(
                target, migrate_legacy=True, failpoint=fail_cleanup
            )
            self.assertEqual(result["status"], "LEGACY_MANIFEST_CLEANUP_PENDING")
            self.assertTrue((target / MANIFEST_RELATIVE).is_file())
            self.assertTrue(
                (target / "sol-luna-router" / "install-manifest.json").is_file()
            )
            manifest = json.loads((target / MANIFEST_RELATIVE).read_text())
            self.assertEqual(manifest["legacy_cleanup"]["status"], "pending")
            self.assertTrue((target / "agents" / "luna-low.toml").is_file())

            retried = call_install(
                target,
                migrate_legacy=True,
                generated_at=FIXED_TIME + timedelta(days=1),
            )
            self.assertEqual(retried["status"], "LEGACY_CLEANUP_COMPLETED")
            self.assertFalse(
                (target / "sol-luna-router" / "install-manifest.json").exists()
            )
            manifest = json.loads((target / MANIFEST_RELATIVE).read_text())
            self.assertEqual(manifest["legacy_cleanup"]["status"], "complete")

    def test_foreign_luna_agent_is_ownership_conflict(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            write_text(target / "agents" / "luna-low.toml", "user-owned\n")
            before = tree_hash(target)
            with self.assertRaises(InstallerError) as raised:
                call_install(target)
            self.assertEqual(raised.exception.reason_code, "OWNERSHIP_CONFLICT")
            self.assertEqual(tree_hash(target), before)

    def test_corrupt_agents_marker_fails_closed(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            write_text(target / "AGENTS.md", f"user\n{AGENTS_BEGIN}\nbroken\n")
            before = tree_hash(target)
            with self.assertRaises(InstallerError) as raised:
                call_install(target)
            self.assertEqual(raised.exception.reason_code, "AGENTS_MARKER_CORRUPT")
            self.assertEqual(tree_hash(target), before)

    def test_invalid_config_fails_closed(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            write_text(target / "config.toml", "[broken\n")
            before = tree_hash(target)
            with self.assertRaises(InstallerError) as raised:
                call_install(target)
            self.assertEqual(raised.exception.reason_code, "CONFIG_MERGE_UNSAFE")
            self.assertEqual(tree_hash(target), before)

    def test_missing_manifest_blocks_uninstall(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            with self.assertRaises(InstallerError) as raised:
                uninstall(target, project_root=ROOT, allow_validation_sandbox=True)
            self.assertEqual(raised.exception.reason_code, "MANIFEST_MISSING")

    def test_backup_failure_is_reported_without_partial_install(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            write_text(target / "backups", "user file blocks backup root\n")
            before = tree_hash(target)
            with self.assertRaises(InstallerError) as raised:
                call_install(target)
            self.assertEqual(raised.exception.reason_code, "BACKUP_FAILED")
            self.assertEqual(tree_hash(target), before)

    def test_non_directory_target_is_not_writable(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            write_text(target, "not a directory\n")
            with self.assertRaises(InstallerError) as raised:
                call_install(target)
            self.assertEqual(raised.exception.reason_code, "TARGET_NOT_WRITABLE")

    def test_rollback_restores_exact_preinstall_tree(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            write_text(target / "user" / "state.txt", "preserve exactly\n")
            before = tree_hash(target)
            installed = call_install(target)
            restored = rollback(
                target,
                Path(installed["backup"]),
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(restored["status"], "ROLLBACK_EXACT_PASS")
            self.assertEqual(tree_hash(target), before)

    def test_uninstall_removes_owned_content_and_preserves_user_content(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            original_config = 'user_model = "keep"\n'
            original_agents = "User policy remains.\n"
            write_text(target / "config.toml", original_config)
            write_text(target / "AGENTS.md", original_agents)
            write_text(target / "agents" / "user-agent.toml", 'name = "user_agent"\n')
            write_text(target / "runtime" / "user-state.json", "{}\n")
            call_install(target)

            result = uninstall(
                target,
                project_root=ROOT,
                generated_at=FIXED_TIME + timedelta(days=1),
                allow_validation_sandbox=True,
            )
            self.assertEqual(result["status"], "UNINSTALLED")
            for filename in STABLE_AGENT_FILES:
                self.assertFalse((target / "agents" / filename).exists())
            self.assertFalse((target / "sol-luna-v4" / "selector.py").exists())
            self.assertFalse((target / MANIFEST_RELATIVE).exists())
            self.assertEqual((target / "config.toml").read_text(), original_config)
            self.assertEqual((target / "AGENTS.md").read_text(), original_agents)
            self.assertTrue((target / "agents" / "user-agent.toml").is_file())
            self.assertTrue((target / "runtime" / "user-state.json").is_file())

    def test_uninstall_preserves_modified_owned_file_by_failing_closed(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)
            write_text(target / "agents" / "luna-low.toml", "user changed owned file\n")
            with self.assertRaises(InstallerError) as raised:
                uninstall(target, project_root=ROOT, allow_validation_sandbox=True)
            self.assertEqual(raised.exception.reason_code, "OWNERSHIP_CONFLICT")
            self.assertTrue((target / "agents" / "luna-low.toml").is_file())

    def test_cli_apply_and_second_run_use_validation_sandbox_only(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            command = [
                sys.executable,
                str(ROOT / "scripts" / "install.py"),
                "--apply",
                "--codex-home",
                str(target),
                "--validation-sandbox",
            ]
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(first.stdout)["status"], "INSTALLED")
            second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            second_result = json.loads(second.stdout)
            self.assertEqual(second_result["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second_result["effective_changes"], 0)

    def test_cli_migrates_fake_legacy_32_without_creating_state(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            materialize_legacy_fixture(target)
            command = [
                sys.executable,
                str(ROOT / "scripts" / "install.py"),
                "--apply",
                "--migrate-v3",
                "--codex-home",
                str(target),
                "--validation-sandbox",
            ]
            completed = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "INSTALLED")
            self.assertEqual(result["migration"]["source_version"], "3.2")
            self.assertEqual(result["migration"]["cleanup_status"], "complete")
            self.assertFalse((target / "sol-luna-v4" / "state").exists())


if __name__ == "__main__":
    unittest.main()
