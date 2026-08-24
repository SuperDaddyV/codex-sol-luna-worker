import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.install import MANIFEST_RELATIVE, VERSION
from scripts.install_assist import (
    AssistError,
    CommandOutcome,
    PHASES,
    _github_https_check,
    _is_wsl,
    build_recovery_plan,
    check_result,
    classify_installed,
    collect_snapshot,
    execute_recovery,
    install_workflow,
    load_catalog,
    make_support_report,
    main,
    render_card,
    render_support_markdown,
    verify_source_checkout,
)


def make_snapshot(
    blockers=(),
    *,
    platform_name="Windows",
    distro=None,
    package_manager="winget",
    installed_state="ABSENT",
    installed_version=None,
):
    return {
        "schema": 1,
        "target_version": VERSION,
        "platform": platform_name,
        "distro": distro,
        "wsl": False,
        "approval_policy": "on-request",
        "sandbox_mode": "workspace-write",
        "package_manager": package_manager,
        "tools": {
            "codex": {"status": "PASS", "version": "codex-cli 0.143.0"},
            "python": {"status": "PASS", "version": "Python 3.11.9"},
            "git": {"status": "PASS", "version": "git version 2.51.0"},
        },
        "github_https": {"status": "PASS", "attempts": 1},
        "installed": {
            "state": installed_state,
            "version": installed_version,
            "source_commit": None,
        },
        "blockers": list(blockers),
        "ready": not blockers,
    }


def capability_pass():
    return {
        "all_supported": True,
        "results": [
            {
                "effort": effort,
                "supported": True,
                "response_exact": True,
                "exit_code": 0,
            }
            for effort in ("low", "medium", "high", "xhigh", "max")
        ],
    }


class RecoveryCatalogTests(unittest.TestCase):
    def test_catalog_is_valid_and_contains_only_bounded_vectors(self):
        catalog = load_catalog()
        self.assertEqual(catalog["schema"], 1)
        self.assertEqual(catalog["last_verified"], "2026-08-24")
        self.assertGreaterEqual(len(catalog["actions"]), 9)
        self.assertEqual(
            len({action["action_id"] for action in catalog["actions"]}),
            len(catalog["actions"]),
        )
        for action in catalog["actions"]:
            self.assertTrue(action["source"].startswith("https://"))
            self.assertTrue(action["proof"])
            self.assertTrue(action["rollback_instruction"])
            for command in action["commands"] + action["rollback"]:
                self.assertIsInstance(command, list)
                self.assertNotIn("|", command)
                self.assertNotIn("&&", command)
            if action["classification"] == "approval_required":
                self.assertTrue(action["commands"])
                self.assertTrue(action["rollback"])
            else:
                self.assertEqual(action["commands"], [])

    def test_catalog_rejects_non_official_source(self):
        catalog = load_catalog()
        catalog["actions"][0]["source"] = "https://example.invalid/install"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaises(AssistError) as raised:
                load_catalog(path)
        self.assertEqual(raised.exception.reason_code, "RECOVERY_CATALOG_INVALID")

    def test_plan_id_is_deterministic_and_covers_command_drift(self):
        snapshot = make_snapshot(["GIT_MISSING"])
        catalog = load_catalog()
        first = build_recovery_plan(snapshot, catalog)
        second = build_recovery_plan(snapshot, catalog)
        self.assertEqual(first["plan_id"], second["plan_id"])

        changed = copy.deepcopy(catalog)
        action = next(
            item for item in changed["actions"] if item["action_id"] == "windows-winget-git-user"
        )
        action["commands"][0].append("--silent")
        drifted = build_recovery_plan(snapshot, changed)
        self.assertNotEqual(first["plan_id"], drifted["plan_id"])

    def test_windows_plan_combines_approval_and_user_action(self):
        snapshot = make_snapshot(
            [
                "CODEX_CLI_MISSING_OR_UNUSABLE",
                "PYTHON_MISSING_OR_UNSUPPORTED",
                "GIT_MISSING",
            ]
        )
        plan = build_recovery_plan(snapshot, load_catalog())
        self.assertEqual(plan["phase"], "AWAITING_APPROVAL")
        self.assertEqual(plan["administrator_required"], "MAY_PROMPT")
        self.assertEqual(
            {action["action_id"] for action in plan["actions"]},
            {
                "official-codex-cli-guidance",
                "windows-winget-python-3.14-user",
                "windows-winget-git-user",
            },
        )

    def test_linux_python_is_guided_not_executed(self):
        snapshot = make_snapshot(
            ["PYTHON_MISSING_OR_UNSUPPORTED"],
            platform_name="Linux",
            distro="ubuntu",
            package_manager="apt-get",
        )
        plan = build_recovery_plan(snapshot, load_catalog())
        self.assertEqual(plan["phase"], "NEEDS_USER_ACTION")
        self.assertEqual(plan["actions"][0]["classification"], "user_action")
        self.assertEqual(plan["actions"][0]["commands"], [])

    def test_missing_supported_package_manager_is_unresolved(self):
        snapshot = make_snapshot(["GIT_MISSING"], package_manager=None)
        plan = build_recovery_plan(snapshot, load_catalog())
        self.assertEqual(plan["phase"], "NEEDS_USER_ACTION")
        self.assertEqual(plan["actions"], [])
        self.assertEqual(plan["unresolved"], ["GIT_MISSING"])

    def test_platform_recovery_matrix_selects_only_matching_catalog_action(self):
        cases = (
            ("Darwin", None, "brew", "PYTHON_MISSING_OR_UNSUPPORTED", "macos-homebrew-python"),
            ("Darwin", None, "brew", "GIT_MISSING", "macos-homebrew-git"),
            ("Linux", "ubuntu", "apt-get", "GIT_MISSING", "ubuntu-apt-git"),
            ("Linux", "debian", "apt-get", "GIT_MISSING", "debian-apt-git"),
            (
                "Linux",
                "debian",
                "apt-get",
                "PYTHON_MISSING_OR_UNSUPPORTED",
                "debian-python-version-guidance",
            ),
        )
        catalog = load_catalog()
        for platform_name, distro, manager, blocker, expected in cases:
            with self.subTest(platform=platform_name, distro=distro, blocker=blocker):
                plan = build_recovery_plan(
                    make_snapshot(
                        [blocker],
                        platform_name=platform_name,
                        distro=distro,
                        package_manager=manager,
                    ),
                    catalog,
                )
                self.assertEqual(
                    [action["action_id"] for action in plan["actions"]],
                    [expected],
                )

    def test_newer_or_invalid_manifest_is_a_hard_block(self):
        for blocker in ("CURRENT_VERSION_NEWER", "MANIFEST_INVALID"):
            with self.subTest(blocker=blocker):
                plan = build_recovery_plan(make_snapshot([blocker]), load_catalog())
                self.assertEqual(plan["phase"], "BLOCKED")


class RecoveryExecutionTests(unittest.TestCase):
    def test_mismatched_approval_executes_nothing(self):
        plan = build_recovery_plan(make_snapshot(["GIT_MISSING"]), load_catalog())
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return CommandOutcome(0)

        result = execute_recovery(plan, "sha256:" + "0" * 64, runner=runner)
        self.assertEqual(result["reason_code"], "RECOVERY_PLAN_CHANGED")
        self.assertEqual(result["writes_performed"], "NO")
        self.assertEqual(calls, [])

    def test_exact_approval_runs_command_once_and_one_proof(self):
        plan = build_recovery_plan(make_snapshot(["GIT_MISSING"]), load_catalog())
        calls = []

        def runner(command, **kwargs):
            calls.append(list(command))
            return CommandOutcome(0)

        result = execute_recovery(plan, plan["plan_id"], runner=runner)
        self.assertEqual(result["phase"], "RECHECKING")
        self.assertEqual(result["attempted_actions"][0]["status"], "PASS")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[-1], ["git", "--version"])

    def test_failed_package_command_is_not_retried(self):
        plan = build_recovery_plan(make_snapshot(["GIT_MISSING"]), load_catalog())
        calls = []

        def runner(command, **kwargs):
            calls.append(list(command))
            return CommandOutcome(1)

        result = execute_recovery(plan, plan["plan_id"], runner=runner)
        self.assertEqual(result["reason_code"], "RECOVERY_COMMAND_FAILED")
        self.assertEqual(len(calls), 1)

    def test_hard_block_prevents_other_approved_recovery_actions(self):
        snapshot = make_snapshot(["GIT_MISSING", "MANIFEST_INVALID"])
        plan = build_recovery_plan(snapshot, load_catalog())
        calls = []

        def runner(command, **kwargs):
            calls.append(list(command))
            return CommandOutcome(0)

        result = execute_recovery(plan, plan["plan_id"], runner=runner)
        self.assertEqual(result["phase"], "BLOCKED")
        self.assertEqual(result["reason_code"], "MANIFEST_INVALID")
        self.assertEqual(calls, [])

    def test_transient_github_check_uses_bounded_attempts(self):
        outcomes = iter((CommandOutcome(1), CommandOutcome(1), CommandOutcome(0)))
        calls = []
        sleeps = []

        def runner(command, **kwargs):
            calls.append(list(command))
            return next(outcomes)

        result = _github_https_check(
            True,
            runner=runner,
            attempts=3,
            sleeper=sleeps.append,
        )
        self.assertEqual(result, {"status": "PASS", "attempts": 3})
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [1.0, 2.0])

    def test_invalid_network_retry_budget_fails_closed(self):
        with self.assertRaises(AssistError) as raised:
            _github_https_check(
                True,
                runner=lambda *args, **kwargs: CommandOutcome(0),
                attempts=4,
                sleeper=lambda _seconds: None,
            )
        self.assertEqual(raised.exception.reason_code, "NETWORK_RETRY_BUDGET_INVALID")


class SnapshotAndReportTests(unittest.TestCase):
    @patch(
        "scripts.install_assist._python_check",
        return_value={"status": "UNSUPPORTED", "version": "Python 3.10.9"},
    )
    def test_snapshot_aggregates_independent_prerequisite_failures(self, _python):
        def which(name):
            return "winget" if name == "winget" else None

        snapshot = collect_snapshot(
            Path("unused-codex-home"),
            approval_policy="on-request",
            sandbox_mode="workspace-write",
            platform_name="Windows",
            which=which,
            runner=lambda *args, **kwargs: CommandOutcome(1),
            sleeper=lambda _seconds: None,
        )
        self.assertEqual(
            snapshot["blockers"],
            [
                "CODEX_CLI_MISSING_OR_UNUSABLE",
                "PYTHON_MISSING_OR_UNSUPPORTED",
                "GIT_MISSING",
            ],
        )
        self.assertEqual(snapshot["github_https"]["status"], "NOT_CHECKED")
        self.assertEqual(snapshot["package_manager"], "winget")

    def test_wsl_detection_is_explicit(self):
        with patch(
            "scripts.install_assist.platform.release",
            return_value="5.15.90.1-microsoft-standard-WSL2",
        ), patch.dict("scripts.install_assist.os.environ", {}, clear=True):
            self.assertTrue(_is_wsl("Linux"))
            self.assertFalse(_is_wsl("Windows"))

    def test_manifest_classification_covers_all_version_states(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            manifest_path = home / Path(MANIFEST_RELATIVE.as_posix())
            self.assertEqual(classify_installed(home)["state"], "ABSENT")
            manifest_path.parent.mkdir(parents=True)

            for version, expected in (
                (VERSION, "CURRENT"),
                ("v4.1.0", "OLDER"),
                ("v4.1.2", "NEWER"),
                ("not-semver", "INVALID"),
            ):
                with self.subTest(version=version):
                    manifest_path.write_text(
                        json.dumps({"version": version}), encoding="utf-8"
                    )
                    self.assertEqual(classify_installed(home)["state"], expected)

    def test_support_report_is_whitelist_only_and_sanitized(self):
        snapshot = make_snapshot(["GIT_MISSING"])
        private_posix = "/" + "home/private"
        snapshot["tools"]["codex"]["version"] = "sk-" + "A" * 30
        snapshot["tools"]["git"]["version"] = "C:\\Users\\Private\\git.exe"
        snapshot["tools"]["python"]["version"] = private_posix + "/python"
        snapshot["installed"]["source_commit"] = "a" * 40
        plan = build_recovery_plan(snapshot, load_catalog())
        report = make_support_report(snapshot, plan)
        self.assertEqual(report["schema"], 1)
        rendered = json.dumps(report)
        self.assertNotIn("sk-", rendered)
        self.assertNotIn("C:\\Users", rendered)
        self.assertNotIn(private_posix, rendered)
        self.assertNotIn("commands", rendered)
        self.assertNotIn("https://", rendered)
        self.assertEqual(report["installed"]["location"], "<CODEX_HOME>")
        markdown = render_support_markdown(report)
        self.assertIn("Sol/Luna Installation Support Report", markdown)
        self.assertNotIn("sk-", markdown)

    def test_support_report_normalizes_uppercase_source_commit(self):
        snapshot = make_snapshot()
        snapshot["installed"]["source_commit"] = "A" * 40
        plan = build_recovery_plan(snapshot, load_catalog())
        report = make_support_report(snapshot, plan)
        self.assertEqual(report["installed"]["source_commit"], "a" * 40)

    def test_check_result_can_hide_or_show_exact_actions(self):
        plan = build_recovery_plan(make_snapshot(["GIT_MISSING"]), load_catalog())
        summary = check_result(plan, include_actions=False)
        proposal = check_result(plan, include_actions=True)
        self.assertNotIn("actions", summary)
        self.assertIn("actions", proposal)
        self.assertEqual(summary["plan_id"], proposal["plan_id"])


class SourceAndInstallWorkflowTests(unittest.TestCase):
    def test_source_verification_requires_exact_clean_detached_checkout(self):
        commit = "a" * 40

        def runner(command, **kwargs):
            if command[:3] == ["git", "rev-parse", "HEAD"]:
                return CommandOutcome(0, commit + "\n")
            if command[:3] == ["git", "status", "--short"]:
                return CommandOutcome(0, "")
            if command[:3] == ["git", "symbolic-ref", "-q"]:
                return CommandOutcome(1, "")
            raise AssertionError(command)

        result = verify_source_checkout(commit, runner=runner)
        self.assertTrue(result["ok"])
        self.assertEqual(result["source_commit"], commit)

    def test_attached_source_fails_closed(self):
        commit = "b" * 40

        def runner(command, **kwargs):
            if command[:3] == ["git", "rev-parse", "HEAD"]:
                return CommandOutcome(0, commit)
            if command[:3] == ["git", "status", "--short"]:
                return CommandOutcome(0, "")
            return CommandOutcome(0, "refs/heads/master")

        result = verify_source_checkout(commit, runner=runner)
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason_code"], "SOURCE_NOT_DETACHED")

    def test_capability_failure_stops_before_installer(self):
        called = []

        def dry_runner(*args, **kwargs):
            called.append("dry")
            return {"status": "DRY_RUN_PASS"}

        result = install_workflow(
            make_snapshot(),
            Path("unused"),
            source_commit="c" * 40,
            apply=True,
            migrate_v3=False,
            capability_timeout=1,
            source_verifier=lambda *args, **kwargs: {"ok": True},
            capability_probe=lambda *args: {"all_supported": False, "results": []},
            dry_runner=dry_runner,
        )
        self.assertEqual(result["reason_code"], "LUNA_CAPABILITY_UNAVAILABLE")
        self.assertEqual(result["writes_performed"], "NO")
        self.assertEqual(called, [])

    def test_capability_requires_exact_complete_five_effort_evidence(self):
        for mutate in (
            lambda payload: payload["results"][0].update(response_exact=False),
            lambda payload: payload["results"].pop(),
            lambda payload: payload["results"].append(copy.deepcopy(payload["results"][0])),
        ):
            with self.subTest(mutation=mutate):
                capability = capability_pass()
                mutate(capability)
                result = install_workflow(
                    make_snapshot(),
                    Path("unused"),
                    source_commit="2" * 40,
                    apply=False,
                    migrate_v3=False,
                    capability_timeout=1,
                    source_verifier=lambda *args, **kwargs: {"ok": True},
                    capability_probe=lambda *args, payload=capability: payload,
                    dry_runner=lambda *args, **kwargs: self.fail(
                        "installer dry-run must not run"
                    ),
                )
                self.assertEqual(result["reason_code"], "LUNA_CAPABILITY_UNAVAILABLE")
                self.assertEqual(result["writes_performed"], "NO")

    def test_current_installation_fast_path_has_zero_write_and_backup(self):
        def unexpected_apply(*args, **kwargs):
            raise AssertionError("apply must not run")

        result = install_workflow(
            make_snapshot(installed_state="CURRENT", installed_version=VERSION),
            Path("unused"),
            source_commit="d" * 40,
            apply=True,
            migrate_v3=False,
            capability_timeout=1,
            source_verifier=lambda *args, **kwargs: {"ok": True},
            capability_probe=lambda *args: capability_pass(),
            dry_runner=lambda *args, **kwargs: {
                "status": "IDEMPOTENT_PASS",
                "effective_changes": 0,
            },
            apply_runner=unexpected_apply,
        )
        self.assertEqual(result["phase"], "FRESH_TASK_SMOKE")
        self.assertEqual(result["writes_performed"], "NO")
        self.assertEqual(result["backup"], "NONE")

    def test_dry_run_stops_before_apply(self):
        result = install_workflow(
            make_snapshot(),
            Path("unused"),
            source_commit="e" * 40,
            apply=False,
            migrate_v3=False,
            capability_timeout=1,
            source_verifier=lambda *args, **kwargs: {"ok": True},
            capability_probe=lambda *args: capability_pass(),
            dry_runner=lambda *args, **kwargs: {
                "status": "DRY_RUN_PASS",
                "effective_changes": 9,
            },
        )
        self.assertEqual(result["phase"], "DRY_RUN")
        self.assertEqual(result["effective_changes"], 9)
        self.assertEqual(result["writes_performed"], "NO")

    def test_apply_returns_symbolic_backup_and_reload_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / ".codex"
            backup = home / "sol-luna-v4" / "backups" / "transaction-1"
            observed = {}

            def dry_runner(_home, *, migrate_legacy, **_kwargs):
                observed["dry_migrate_legacy"] = migrate_legacy
                return {"status": "DRY_RUN_PASS", "effective_changes": 9}

            def apply_runner(_home, *, migrate_legacy, **_kwargs):
                observed["apply_migrate_legacy"] = migrate_legacy
                return {
                    "status": "INSTALLED",
                    "effective_changes": 9,
                    "backup": str(backup),
                }

            result = install_workflow(
                make_snapshot(),
                home,
                source_commit="f" * 40,
                apply=True,
                migrate_v3=True,
                capability_timeout=1,
                allow_validation_sandbox=True,
                source_verifier=lambda *args, **kwargs: {"ok": True},
                capability_probe=lambda *args: capability_pass(),
                dry_runner=dry_runner,
                apply_runner=apply_runner,
            )
        self.assertEqual(result["phase"], "RELOAD_REQUIRED")
        self.assertEqual(
            result["backup"],
            "<CODEX_HOME>/sol-luna-v4/backups/transaction-1",
        )
        self.assertIn("FRESH_TASK_SMOKE", result["resume"])
        self.assertEqual(
            observed,
            {"dry_migrate_legacy": True, "apply_migrate_legacy": True},
        )

    def test_capability_exception_becomes_bounded_user_action(self):
        def broken_probe(*args):
            raise RuntimeError("sensitive provider error")

        result = install_workflow(
            make_snapshot(),
            Path("unused"),
            source_commit="1" * 40,
            apply=False,
            migrate_v3=False,
            capability_timeout=1,
            source_verifier=lambda *args, **kwargs: {"ok": True},
            capability_probe=broken_probe,
        )
        rendered = json.dumps(result)
        self.assertEqual(result["reason_code"], "LUNA_CAPABILITY_PRECHECK_FAILED")
        self.assertNotIn("sensitive", rendered)


class ResultCardTests(unittest.TestCase):
    def test_state_machine_phase_set_is_fixed(self):
        self.assertEqual(
            PHASES,
            (
                "CHECKING",
                "SAFE_RECOVERY",
                "AWAITING_APPROVAL",
                "RECHECKING",
                "CAPABILITY_PRECHECK",
                "DRY_RUN",
                "INSTALLING",
                "RELOAD_REQUIRED",
                "FRESH_TASK_SMOKE",
                "COMPLETE",
                "NEEDS_USER_ACTION",
                "BLOCKED",
            ),
        )

    def test_complete_user_action_and_blocked_cards_are_distinct(self):
        complete = render_card(
            {
                "phase": "COMPLETE",
                "target_version": VERSION,
                "source_commit": "a" * 40,
                "backup": "NONE",
            }
        )
        needs = render_card(
            {"phase": "NEEDS_USER_ACTION", "reason_code": "AUTH_REQUIRED"}
        )
        blocked = render_card(
            {"phase": "BLOCKED", "reason_code": "OWNERSHIP_CONFLICT"}
        )
        self.assertTrue(complete.startswith("Installation Complete"))
        self.assertTrue(needs.startswith("Needs User Action"))
        self.assertTrue(blocked.startswith("Blocked"))
        self.assertIn("do not patch managed state", blocked)


class CommandLineContractTests(unittest.TestCase):
    def test_every_command_requires_explicit_codex_home(self):
        for command in ("check", "plan", "recover", "install", "report"):
            arguments = [command]
            if command == "recover":
                arguments.extend(["--approve", "sha256:" + "0" * 64])
            elif command == "install":
                arguments.extend(["--source-commit", "0" * 40])
            with self.subTest(command=command), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    main(arguments)
                self.assertEqual(raised.exception.code, 2)

    def test_migrate_v3_requires_apply_before_environment_checks(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main(
                    [
                        "install",
                        "--codex-home",
                        "unused",
                        "--source-commit",
                        "0" * 40,
                        "--migrate-v3",
                    ]
                )
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
