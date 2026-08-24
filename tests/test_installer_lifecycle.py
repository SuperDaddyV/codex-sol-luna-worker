import hashlib
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.install import (
    AGENTS_BEGIN,
    AGENTS_END,
    CONFIG_BEGIN,
    CONFIG_END,
    InstallerError,
    MANIFEST_RELATIVE,
    STABLE_AGENT_FILES,
    VERSION,
    dry_run_install,
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


def simulate_rc1_managed_policy(target: Path) -> None:
    agents_path = target / "AGENTS.md"
    policy = agents_path.read_text(encoding="utf-8")
    receipt_start = policy.index("## Delegation Receipt")
    luna_start = policy.index("## Luna", receipt_start)
    rc1_policy = policy[:receipt_start] + policy[luna_start:]
    rc1_policy = rc1_policy.replace("- Never select `ultra` for Luna.\n", "")
    agents_path.write_bytes(rc1_policy.encode("utf-8"))

    block_start = rc1_policy.index(AGENTS_BEGIN)
    block_finish = rc1_policy.index(AGENTS_END, block_start) + len(AGENTS_END)
    if block_finish < len(rc1_policy) and rc1_policy[block_finish] == "\r":
        block_finish += 1
    if block_finish < len(rc1_policy) and rc1_policy[block_finish] == "\n":
        block_finish += 1

    manifest_path = target / MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = "v4.1.0-rc1"
    manifest["owned_blocks"]["AGENTS.md"]["sha256"] = hashlib.sha256(
        rc1_policy[block_start:block_finish].encode("utf-8")
    ).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def simulate_rc3_managed_policy(target: Path) -> None:
    agents_path = target / "AGENTS.md"
    policy = agents_path.read_text(encoding="utf-8")
    evidence_start = policy.index("- `LUNA_UNAVAILABLE` is evidence-gated.")
    summary_start = policy.index(
        "- The receipt is a user-facing execution summary", evidence_start
    )
    rc3_policy = (
        policy[:evidence_start]
        + "- Use `Sol/Luna: Sol-only · Luna unavailable` only when a reasonable "
        "delegation opportunity existed but no valid selector role, required Luna "
        "capability, discovered agent, or other fail-closed prerequisite was available.\n"
        "- Generate the receipt only from facts already obtained during the task. "
        "Do not invoke the selector, spawn or inspect a child, read files, call tools "
        "or networks, write state, or add telemetry solely to produce it.\n"
        + policy[summary_start:]
    )
    agents_path.write_bytes(rc3_policy.encode("utf-8"))

    block_start = rc3_policy.index(AGENTS_BEGIN)
    block_finish = rc3_policy.index(AGENTS_END, block_start) + len(AGENTS_END)
    if block_finish < len(rc3_policy) and rc3_policy[block_finish] == "\r":
        block_finish += 1
    if block_finish < len(rc3_policy) and rc3_policy[block_finish] == "\n":
        block_finish += 1

    manifest_path = target / MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = "v4.1.0-rc3"
    manifest["owned_blocks"]["AGENTS.md"]["sha256"] = hashlib.sha256(
        rc3_policy[block_start:block_finish].encode("utf-8")
    ).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def simulate_rc4_managed_install(target: Path) -> None:
    agents_path = target / "AGENTS.md"
    policy = agents_path.read_text(encoding="utf-8")
    policy = "\n".join(
        line for line in policy.splitlines() if not line.startswith("- Status command:")
    ) + "\n"
    policy = policy.replace(
        "- The selector returns receipt-safe selection JSON. Save that one result for "
        "delegation and the final receipt; do not select again for reporting.\n",
        "",
    )
    policy = policy.replace(
        "- When `selected_role` is valid, delegate through that native custom agent type.\n",
        "- When the selector returns a valid role, delegate through that native custom "
        "agent type.\n",
    )
    suffix_start = policy.index("- A delegated receipt may append only")
    suffix_end = policy.index(
        "- If any Luna child actually ran", suffix_start
    )
    policy = policy[:suffix_start] + policy[suffix_end:]
    status_start = policy.index("## Natural-language status and diagnostics")
    luna_start = policy.index("## Luna", status_start)
    policy = policy[:status_start] + policy[luna_start:]
    policy = policy.replace("--print-selection", "--print-role")
    agents_path.write_bytes(policy.encode("utf-8"))

    block_start = policy.index(AGENTS_BEGIN)
    block_finish = policy.index(AGENTS_END, block_start) + len(AGENTS_END)
    if block_finish < len(policy) and policy[block_finish] == "\r":
        block_finish += 1
    if block_finish < len(policy) and policy[block_finish] == "\n":
        block_finish += 1

    selector_relative = "sol-luna-v4/selector.py"
    selector_path = target / selector_relative
    selector = b"# simulated manifest-owned RC4 selector\n" + selector_path.read_bytes()
    selector_path.write_bytes(selector)
    manifest_path = target / MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = "v4.1.0-rc4"
    manifest.pop("source_commit", None)
    manifest["owned_files"][selector_relative] = hashlib.sha256(selector).hexdigest()
    manifest["owned_blocks"]["AGENTS.md"]["sha256"] = hashlib.sha256(
        policy[block_start:block_finish].encode("utf-8")
    ).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


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
            installed_policy = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(AGENTS_BEGIN, installed_policy)
            self.assertIn(str(target.resolve()), installed_policy)
            self.assertIn("--ensure-daily --print-selection", installed_policy)
            self.assertIn("--status-json", installed_policy)
            self.assertNotIn("<CODEX_HOME>", installed_policy)
            self.assertNotIn(".var", installed_policy)
            self.assertIn(
                CONFIG_BEGIN, (target / "config.toml").read_text(encoding="utf-8")
            )
            self.assertTrue((target / "sol-luna-v4" / "selector.py").is_file())
            self.assertTrue((target / MANIFEST_RELATIVE).is_file())
            manifest = json.loads(
                (target / MANIFEST_RELATIVE).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["version"], VERSION)
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
            config = tomllib.loads(
                (target / "config.toml").read_text(encoding="utf-8")
            )
            self.assertEqual(config["model"], "user-model")
            self.assertEqual(config["mcp_servers"]["user"]["command"], "user-tool")
            self.assertEqual(config["agents"]["user_option"], "keep")
            self.assertTrue(config["agents"]["enabled"])
            self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 3)
            self.assertTrue(
                (target / "AGENTS.md")
                .read_text(encoding="utf-8")
                .startswith(original_agents)
            )
            self.assertEqual(
                (target / "agents" / "user-agent.toml").read_text(encoding="utf-8"),
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
            self.assertEqual(
                (target / "config.toml").read_text(encoding="utf-8"), original_config
            )

    def test_upgrade_restores_leaf_removes_owned_experiment_and_rolls_back(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)
            manifest_path = target / MANIFEST_RELATIVE
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for filename in STABLE_AGENT_FILES:
                path = target / "agents" / filename
                prototype = path.read_text(encoding="utf-8").replace(
                    "\n[agents]\nenabled = false\n", "\n"
                )
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
                (target / "agents" / "user-agent.toml").read_text(encoding="utf-8"),
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

    def test_v40_manifest_owned_selector_upgrades_to_stable_and_rolls_back(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            write_text(target / "config.toml", 'user_setting = "preserve"\n')
            write_text(target / "AGENTS.md", "User policy remains.\n")
            call_install(target)

            manifest_path = target / MANIFEST_RELATIVE
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            selector_relative = "sol-luna-v4/selector.py"
            selector_path = target / selector_relative
            v40_selector = (
                b"# simulated manifest-owned v4.0.0 payload\n"
                + selector_path.read_bytes()
            )
            selector_path.write_bytes(v40_selector)
            manifest["version"] = "v4.0.0"
            manifest["owned_files"][selector_relative] = hashlib.sha256(
                v40_selector
            ).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            state = target / "sol-luna-v4" / "state"
            write_text(state / "daily-profile.json", '{"legacy":"daily"}\n')
            write_text(state / "last-good-profile.json", '{"legacy":"lkg"}\n')
            state_before = {
                path.name: path.read_bytes() for path in state.iterdir() if path.is_file()
            }
            agents_before = {
                filename: (target / "agents" / filename).read_bytes()
                for filename in STABLE_AGENT_FILES
            }
            config_before = (target / "config.toml").read_bytes()
            agents_policy_before = (target / "AGENTS.md").read_bytes()
            before = tree_hash(target)

            upgraded = call_install(target, generated_at=FIXED_TIME + timedelta(days=1))
            self.assertEqual(upgraded["status"], "UPGRADED")
            self.assertTrue(Path(upgraded["backup"]).is_dir())
            self.assertEqual(
                selector_path.read_bytes(), (ROOT / "src/selector.py").read_bytes()
            )
            self.assertEqual(
                json.loads(manifest_path.read_text(encoding="utf-8"))["version"],
                VERSION,
            )
            self.assertEqual(
                {
                    filename: (target / "agents" / filename).read_bytes()
                    for filename in STABLE_AGENT_FILES
                },
                agents_before,
            )
            self.assertEqual((target / "config.toml").read_bytes(), config_before)
            self.assertEqual((target / "AGENTS.md").read_bytes(), agents_policy_before)
            self.assertEqual(
                {
                    path.name: path.read_bytes()
                    for path in state.iterdir()
                    if path.is_file()
                },
                state_before,
            )

            second = call_install(target, generated_at=FIXED_TIME + timedelta(days=2))
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)

            rolled_back = rollback(
                target,
                Path(upgraded["backup"]),
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(rolled_back["status"], "ROLLBACK_EXACT_PASS")
            self.assertEqual(tree_hash(target), before)

    def test_rc4_to_stable_upgrade_changes_exactly_three_paths(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            write_text(target / "config.toml", 'user_setting = "preserve"\n')
            write_text(target / "AGENTS.md", "User policy remains.\n")
            call_install(target)
            simulate_rc4_managed_install(target)

            state = target / "sol-luna-v4" / "state"
            write_text(state / "daily-profile.json", '{"preserve":"daily"}\n')
            write_text(state / "last-good-profile.json", '{"preserve":"lkg"}\n')
            agents_before = {
                filename: (target / "agents" / filename).read_bytes()
                for filename in STABLE_AGENT_FILES
            }
            config_before = (target / "config.toml").read_bytes()
            state_before = {
                path.name: path.read_bytes() for path in state.iterdir() if path.is_file()
            }
            before = tree_hash(target)
            expected = {
                "AGENTS.md",
                "sol-luna-v4/selector.py",
                MANIFEST_RELATIVE.as_posix(),
            }

            dry = dry_run_install(
                target,
                project_root=ROOT,
                generated_at=FIXED_TIME + timedelta(days=1),
                allow_validation_sandbox=True,
                source_commit="b" * 40,
            )
            self.assertEqual(dry["status"], "DRY_RUN_PASS")
            self.assertEqual(dry["effective_changes"], 3)
            self.assertEqual(set(dry["modified"]), expected)
            self.assertEqual(tree_hash(target), before)

            upgraded = call_install(
                target,
                generated_at=FIXED_TIME + timedelta(days=1),
                source_commit="b" * 40,
            )
            self.assertEqual(upgraded["status"], "UPGRADED")
            self.assertEqual(upgraded["effective_changes"], 3)
            self.assertEqual(set(upgraded["modified"]), expected)
            backup = Path(upgraded["backup"])
            backup_entries = json.loads(
                (backup / "snapshot.json").read_text(encoding="utf-8")
            )["entries"]
            self.assertEqual({entry["path"] for entry in backup_entries}, expected)
            manifest = json.loads(
                (target / MANIFEST_RELATIVE).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["version"], VERSION)
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["source_commit"], "b" * 40)
            self.assertEqual(
                {
                    filename: (target / "agents" / filename).read_bytes()
                    for filename in STABLE_AGENT_FILES
                },
                agents_before,
            )
            self.assertEqual((target / "config.toml").read_bytes(), config_before)
            self.assertEqual(
                {
                    path.name: path.read_bytes()
                    for path in state.iterdir()
                    if path.is_file()
                },
                state_before,
            )

            second = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=2)
            )
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)
            self.assertIsNone(second["backup"])
            self.assertEqual(
                json.loads(
                    (target / MANIFEST_RELATIVE).read_text(encoding="utf-8")
                )["source_commit"],
                "b" * 40,
            )

            rolled_back = rollback(
                target,
                backup,
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(rolled_back["status"], "ROLLBACK_EXACT_PASS")
            self.assertEqual(tree_hash(target), before)

    def test_rc5_to_rc6_upgrade_is_idempotent_and_rolls_back_exactly(self):
        version_patch = patch("scripts.install.VERSION", "v4.1.0-rc6")
        version_patch.start()
        self.addCleanup(version_patch.stop)
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)

            manifest_path = target / MANIFEST_RELATIVE
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            selector_relative = "sol-luna-v4/selector.py"
            selector_path = target / selector_relative
            rc5_selector = (
                b"# simulated manifest-owned RC5 selector\n"
                + selector_path.read_bytes()
            )
            selector_path.write_bytes(rc5_selector)
            manifest["version"] = "v4.1.0-rc5"
            manifest["owned_files"][selector_relative] = hashlib.sha256(
                rc5_selector
            ).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rc5_before = tree_hash(target)

            dry = dry_run_install(
                target,
                project_root=ROOT,
                generated_at=FIXED_TIME + timedelta(days=1),
                allow_validation_sandbox=True,
            )
            self.assertEqual(dry["status"], "DRY_RUN_PASS")
            self.assertEqual(dry["effective_changes"], 2)
            self.assertEqual(
                set(dry["modified"]),
                {MANIFEST_RELATIVE.as_posix(), selector_relative},
            )
            self.assertIsNone(dry["backup"])
            self.assertEqual(tree_hash(target), rc5_before)

            upgraded = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=1)
            )
            self.assertEqual(upgraded["status"], "UPGRADED")
            self.assertEqual(upgraded["effective_changes"], 2)
            self.assertEqual(
                set(upgraded["modified"]),
                {MANIFEST_RELATIVE.as_posix(), selector_relative},
            )
            backup = Path(upgraded["backup"])
            self.assertTrue(backup.is_dir())
            self.assertEqual(
                {
                    entry["path"]
                    for entry in json.loads(
                        (backup / "snapshot.json").read_text(encoding="utf-8")
                    )["entries"]
                },
                {MANIFEST_RELATIVE.as_posix(), selector_relative},
            )
            self.assertEqual(
                json.loads(manifest_path.read_text(encoding="utf-8"))["version"],
                "v4.1.0-rc6",
            )
            self.assertEqual(
                selector_path.read_bytes(), (ROOT / "src/selector.py").read_bytes()
            )
            upgraded_tree = tree_hash(target)

            second = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=2)
            )
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)
            self.assertIsNone(second["backup"])
            self.assertEqual(tree_hash(target), upgraded_tree)

            rolled_back = rollback(
                target,
                backup,
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(rolled_back["status"], "ROLLBACK_EXACT_PASS")
            self.assertEqual(tree_hash(target), rc5_before)
            self.assertEqual(
                json.loads(manifest_path.read_text(encoding="utf-8"))["version"],
                "v4.1.0-rc5",
            )

    def test_rc6_to_stable_upgrade_changes_only_manifest(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            with patch("scripts.install.VERSION", "v4.1.0-rc6"):
                call_install(target)

            manifest_path = target / MANIFEST_RELATIVE
            rc6_manifest_before = manifest_path.read_bytes()
            before = tree_hash(target)

            dry = dry_run_install(
                target,
                project_root=ROOT,
                generated_at=FIXED_TIME + timedelta(days=1),
                allow_validation_sandbox=True,
            )
            self.assertEqual(dry["status"], "DRY_RUN_PASS")
            self.assertEqual(dry["effective_changes"], 1)
            self.assertEqual(dry["created"], [])
            self.assertEqual(dry["modified"], [MANIFEST_RELATIVE.as_posix()])
            self.assertEqual(dry["removed"], [])
            self.assertIsNone(dry["backup"])
            self.assertEqual(tree_hash(target), before)

            upgraded = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=1)
            )
            self.assertEqual(upgraded["status"], "UPGRADED")
            self.assertEqual(upgraded["effective_changes"], 1)
            self.assertEqual(upgraded["created"], [])
            self.assertEqual(upgraded["modified"], [MANIFEST_RELATIVE.as_posix()])
            self.assertEqual(upgraded["removed"], [])
            backup = Path(upgraded["backup"])
            self.assertTrue(backup.is_dir())
            self.assertEqual(
                {
                    entry["path"]
                    for entry in json.loads(
                        (backup / "snapshot.json").read_text(encoding="utf-8")
                    )["entries"]
                },
                {MANIFEST_RELATIVE.as_posix()},
            )
            self.assertEqual(
                json.loads(manifest_path.read_text(encoding="utf-8"))["version"],
                VERSION,
            )

            upgraded_tree = tree_hash(target)
            second = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=2)
            )
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)
            self.assertIsNone(second["backup"])
            self.assertEqual(tree_hash(target), upgraded_tree)

            rolled_back = rollback(
                target,
                backup,
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(rolled_back["status"], "ROLLBACK_EXACT_PASS")
            self.assertEqual(tree_hash(target), before)
            self.assertEqual(manifest_path.read_bytes(), rc6_manifest_before)

    def test_v410_to_v411_candidate_upgrade_changes_only_manifest(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)

            manifest_path = target / MANIFEST_RELATIVE
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "v4.1.0"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            v410_manifest_before = manifest_path.read_bytes()
            before = tree_hash(target)

            dry = dry_run_install(
                target,
                project_root=ROOT,
                generated_at=FIXED_TIME + timedelta(days=1),
                allow_validation_sandbox=True,
                source_commit="1" * 40,
            )
            self.assertEqual(dry["status"], "DRY_RUN_PASS")
            self.assertEqual(dry["effective_changes"], 1)
            self.assertEqual(dry["created"], [])
            self.assertEqual(dry["modified"], [MANIFEST_RELATIVE.as_posix()])
            self.assertEqual(dry["removed"], [])
            self.assertIsNone(dry["backup"])
            self.assertEqual(tree_hash(target), before)

            upgraded = call_install(
                target,
                generated_at=FIXED_TIME + timedelta(days=1),
                source_commit="1" * 40,
            )
            self.assertEqual(upgraded["status"], "UPGRADED")
            self.assertEqual(upgraded["effective_changes"], 1)
            self.assertEqual(upgraded["created"], [])
            self.assertEqual(upgraded["modified"], [MANIFEST_RELATIVE.as_posix()])
            self.assertEqual(upgraded["removed"], [])
            backup = Path(upgraded["backup"])
            self.assertEqual(
                {
                    entry["path"]
                    for entry in json.loads(
                        (backup / "snapshot.json").read_text(encoding="utf-8")
                    )["entries"]
                },
                {MANIFEST_RELATIVE.as_posix()},
            )
            installed = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(installed["version"], VERSION)
            self.assertEqual(installed["source_commit"], "1" * 40)

            second = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=2)
            )
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)
            self.assertIsNone(second["backup"])

            rolled_back = rollback(
                target,
                backup,
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(rolled_back["status"], "ROLLBACK_EXACT_PASS")
            self.assertEqual(tree_hash(target), before)
            self.assertEqual(manifest_path.read_bytes(), v410_manifest_before)

    def test_rc6_modified_owned_file_blocks_stable_upgrade_without_changes(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            with patch("scripts.install.VERSION", "v4.1.0-rc6"):
                call_install(target)

            selector_path = target / "sol-luna-v4" / "selector.py"
            selector_path.write_bytes(selector_path.read_bytes() + b"\n# user change\n")
            before = tree_hash(target)

            with self.assertRaises(InstallerError) as raised:
                dry_run_install(
                    target,
                    project_root=ROOT,
                    generated_at=FIXED_TIME + timedelta(days=1),
                    allow_validation_sandbox=True,
                )
            self.assertEqual(raised.exception.reason_code, "OWNERSHIP_CONFLICT")
            self.assertEqual(tree_hash(target), before)

            with self.assertRaises(InstallerError) as raised:
                call_install(target, generated_at=FIXED_TIME + timedelta(days=1))
            self.assertEqual(raised.exception.reason_code, "OWNERSHIP_CONFLICT")
            self.assertEqual(tree_hash(target), before)

    def test_rc5_modified_owned_file_blocks_rc6_upgrade_without_changes(self):
        version_patch = patch("scripts.install.VERSION", "v4.1.0-rc6")
        version_patch.start()
        self.addCleanup(version_patch.stop)
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)

            manifest_path = target / MANIFEST_RELATIVE
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "v4.1.0-rc5"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            selector_path = target / "sol-luna-v4" / "selector.py"
            selector_path.write_bytes(selector_path.read_bytes() + b"\n# user change\n")
            before = tree_hash(target)

            with self.assertRaises(InstallerError) as raised:
                call_install(
                    target, generated_at=FIXED_TIME + timedelta(days=1)
                )

            self.assertEqual(raised.exception.reason_code, "OWNERSHIP_CONFLICT")
            self.assertEqual(tree_hash(target), before)

    def test_rc4_modified_owned_content_blocks_upgrade(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)
            simulate_rc4_managed_install(target)
            policy = target / "AGENTS.md"
            policy.write_text(
                policy.read_text(encoding="utf-8").replace(
                    "Sol is the sole planner", "User changed the owned policy"
                ),
                encoding="utf-8",
            )
            before = tree_hash(target)
            with self.assertRaises(InstallerError) as raised:
                call_install(target, generated_at=FIXED_TIME + timedelta(days=1))
            self.assertEqual(raised.exception.reason_code, "OWNERSHIP_CONFLICT")
            self.assertEqual(tree_hash(target), before)

    def test_rc1_global_policy_upgrades_to_stable_receipt_and_rolls_back(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            write_text(target / "config.toml", 'user_setting = "preserve"\n')
            write_text(target / "AGENTS.md", "User policy remains.\n")
            call_install(target)
            simulate_rc1_managed_policy(target)

            state = target / "sol-luna-v4" / "state"
            write_text(state / "daily-profile.json", '{"preserve":"daily"}\n')
            write_text(state / "last-good-profile.json", '{"preserve":"lkg"}\n')
            state_before = {
                path.name: path.read_bytes() for path in state.iterdir() if path.is_file()
            }
            selector_before = (target / "sol-luna-v4" / "selector.py").read_bytes()
            agents_before = {
                filename: (target / "agents" / filename).read_bytes()
                for filename in STABLE_AGENT_FILES
            }
            config_before = (target / "config.toml").read_bytes()
            rc1_agents_before = (target / "AGENTS.md").read_bytes()
            rc1_manifest_before = (target / MANIFEST_RELATIVE).read_bytes()
            before = tree_hash(target)

            upgraded = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=1)
            )

            self.assertEqual(upgraded["status"], "UPGRADED")
            self.assertEqual(upgraded["effective_changes"], 2)
            self.assertEqual(
                set(upgraded["modified"]),
                {"AGENTS.md", MANIFEST_RELATIVE.as_posix()},
            )
            backup = Path(upgraded["backup"])
            self.assertTrue(backup.is_dir())
            snapshot = json.loads(
                (backup / "snapshot.json").read_text(encoding="utf-8")
            )
            backed = {entry["path"] for entry in snapshot["entries"]}
            self.assertIn("AGENTS.md", backed)
            self.assertIn(MANIFEST_RELATIVE.as_posix(), backed)

            upgraded_policy = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertTrue(upgraded_policy.startswith("User policy remains.\n"))
            self.assertIn("## Delegation Receipt", upgraded_policy)
            self.assertEqual(
                json.loads(
                    (target / MANIFEST_RELATIVE).read_text(encoding="utf-8")
                )["version"],
                VERSION,
            )
            self.assertEqual(
                (target / "sol-luna-v4" / "selector.py").read_bytes(),
                selector_before,
            )
            self.assertEqual(
                {
                    filename: (target / "agents" / filename).read_bytes()
                    for filename in STABLE_AGENT_FILES
                },
                agents_before,
            )
            self.assertEqual((target / "config.toml").read_bytes(), config_before)
            self.assertEqual(
                {
                    path.name: path.read_bytes()
                    for path in state.iterdir()
                    if path.is_file()
                },
                state_before,
            )

            second = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=2)
            )
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)

            rolled_back = rollback(
                target,
                backup,
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(rolled_back["status"], "ROLLBACK_EXACT_PASS")
            self.assertEqual(tree_hash(target), before)
            self.assertEqual((target / "AGENTS.md").read_bytes(), rc1_agents_before)
            self.assertEqual(
                (target / MANIFEST_RELATIVE).read_bytes(), rc1_manifest_before
            )

    def test_rc1_modified_owned_policy_blocks_stable_upgrade(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)
            simulate_rc1_managed_policy(target)
            agents_path = target / "AGENTS.md"
            agents_path.write_text(
                agents_path.read_text(encoding="utf-8").replace(
                    "Sol is the sole planner",
                    "User changed the owned policy; Sol is the sole planner",
                ),
                encoding="utf-8",
            )
            before = tree_hash(target)

            with self.assertRaises(InstallerError) as raised:
                call_install(target, generated_at=FIXED_TIME + timedelta(days=1))

            self.assertEqual(raised.exception.reason_code, "OWNERSHIP_CONFLICT")
            self.assertEqual(tree_hash(target), before)

    def test_rc3_global_policy_upgrades_to_stable_evidence_gate_and_rolls_back(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            write_text(target / "config.toml", 'user_setting = "preserve"\n')
            write_text(target / "AGENTS.md", "User policy remains.\n")
            call_install(target)
            simulate_rc3_managed_policy(target)

            state = target / "sol-luna-v4" / "state"
            write_text(state / "daily-profile.json", '{"preserve":"daily"}\n')
            write_text(state / "last-good-profile.json", '{"preserve":"lkg"}\n')
            selector_before = (target / "sol-luna-v4" / "selector.py").read_bytes()
            agents_before = {
                filename: (target / "agents" / filename).read_bytes()
                for filename in STABLE_AGENT_FILES
            }
            config_before = (target / "config.toml").read_bytes()
            state_before = {
                path.name: path.read_bytes() for path in state.iterdir() if path.is_file()
            }
            rc3_policy_before = (target / "AGENTS.md").read_bytes()
            rc3_manifest_before = (target / MANIFEST_RELATIVE).read_bytes()
            before = tree_hash(target)

            upgraded = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=1)
            )

            self.assertEqual(upgraded["status"], "UPGRADED")
            self.assertEqual(upgraded["effective_changes"], 2)
            self.assertEqual(
                set(upgraded["modified"]),
                {"AGENTS.md", MANIFEST_RELATIVE.as_posix()},
            )
            backup = Path(upgraded["backup"])
            self.assertTrue(backup.is_dir())
            snapshot = json.loads(
                (backup / "snapshot.json").read_text(encoding="utf-8")
            )
            backed = {entry["path"] for entry in snapshot["entries"]}
            self.assertIn("AGENTS.md", backed)
            self.assertIn(MANIFEST_RELATIVE.as_posix(), backed)

            upgraded_policy = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("`LUNA_UNAVAILABLE` is evidence-gated", upgraded_policy)
            self.assertIn(
                "current-task parent-visible availability failure evidence",
                upgraded_policy,
            )
            manifest = json.loads(
                (target / MANIFEST_RELATIVE).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["version"], VERSION)
            self.assertEqual(
                (target / "sol-luna-v4" / "selector.py").read_bytes(),
                selector_before,
            )
            self.assertEqual(
                {
                    filename: (target / "agents" / filename).read_bytes()
                    for filename in STABLE_AGENT_FILES
                },
                agents_before,
            )
            self.assertEqual((target / "config.toml").read_bytes(), config_before)
            self.assertEqual(
                {
                    path.name: path.read_bytes()
                    for path in state.iterdir()
                    if path.is_file()
                },
                state_before,
            )

            second = call_install(
                target, generated_at=FIXED_TIME + timedelta(days=2)
            )
            self.assertEqual(second["status"], "IDEMPOTENT_PASS")
            self.assertEqual(second["effective_changes"], 0)

            rolled_back = rollback(
                target,
                backup,
                project_root=ROOT,
                allow_validation_sandbox=True,
            )
            self.assertEqual(rolled_back["status"], "ROLLBACK_EXACT_PASS")
            self.assertEqual(tree_hash(target), before)
            self.assertEqual((target / "AGENTS.md").read_bytes(), rc3_policy_before)
            self.assertEqual(
                (target / MANIFEST_RELATIVE).read_bytes(), rc3_manifest_before
            )

    def test_rc3_modified_owned_policy_blocks_stable_upgrade(self):
        with sandbox() as directory:
            target = Path(directory) / ".codex"
            target.mkdir()
            call_install(target)
            simulate_rc3_managed_policy(target)
            agents_path = target / "AGENTS.md"
            agents_path.write_text(
                agents_path.read_text(encoding="utf-8").replace(
                    "Sol is the sole planner",
                    "User changed the owned policy; Sol is the sole planner",
                ),
                encoding="utf-8",
            )
            before = tree_hash(target)

            with self.assertRaises(InstallerError) as raised:
                call_install(target, generated_at=FIXED_TIME + timedelta(days=1))

            self.assertEqual(raised.exception.reason_code, "OWNERSHIP_CONFLICT")
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
            hooks = json.loads((target / "hooks.json").read_text(encoding="utf-8"))
            self.assertEqual(len(hooks["hooks"]["PreToolUse"]), 1)
            self.assertNotIn("SubagentStart", hooks["hooks"])
            self.assertIn(
                "User instruction stays.",
                (target / "AGENTS.md").read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                "SOL_LUNA_DAILY_BEST",
                (target / "AGENTS.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                tomllib.loads(
                    (target / "config.toml").read_text(encoding="utf-8")
                )["user_model"],
                "preserve",
            )
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
            manifest = json.loads(
                (target / MANIFEST_RELATIVE).read_text(encoding="utf-8")
            )
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
            manifest = json.loads(
                (target / MANIFEST_RELATIVE).read_text(encoding="utf-8")
            )
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
            manifest = json.loads(
                (target / MANIFEST_RELATIVE).read_text(encoding="utf-8")
            )
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
            self.assertEqual(
                (target / "config.toml").read_text(encoding="utf-8"), original_config
            )
            self.assertEqual(
                (target / "AGENTS.md").read_text(encoding="utf-8"), original_agents
            )
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
