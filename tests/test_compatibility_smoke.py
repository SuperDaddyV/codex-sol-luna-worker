import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import compatibility_smoke as smoke


ROOT = Path(__file__).resolve().parents[1]


def protected_snapshot(marker="same"):
    return {
        "entries": {
            "AGENTS.md": {
                "type": "file",
                "sha256": marker,
            }
        }
    }


def runtime_snapshot(entries=None):
    return smoke.RuntimeObservation(
        {"entries": entries or {}},
        frozenset(),
    )


HEALTHY_SELECTOR = {
    "selection_initialized": True,
    "selected_role": "luna_max",
    "selected_effort": "max",
}


class CompatibilitySmokeTests(unittest.TestCase):
    def run_report(
        self,
        *,
        cli=None,
        capability=None,
        selector=None,
        delegation=None,
        protected_before=None,
        protected_after=None,
        runtime_before=None,
        runtime_after=None,
    ):
        cli = cli or (smoke.CheckResult(smoke.PASS), "codex-cli fixture")
        capability = capability or smoke.CheckResult(smoke.PASS)
        selector = selector or smoke.SelectorObservation(
            smoke.CheckResult(smoke.PASS), HEALTHY_SELECTOR
        )
        delegation = delegation or smoke.CheckResult(smoke.PASS)
        protected_before = protected_before or protected_snapshot()
        protected_after = protected_after or protected_snapshot()
        runtime_before = runtime_before or runtime_snapshot()
        runtime_after = runtime_after or runtime_snapshot()
        with (
            patch.object(
                smoke,
                "_protected_state_snapshot",
                side_effect=[protected_before, protected_after],
            ),
            patch.object(smoke, "_validate_protected_state_snapshot"),
            patch.object(
                smoke,
                "_capture_runtime",
                side_effect=[runtime_before, runtime_after],
            ),
            patch.object(smoke, "_check_cli", return_value=cli),
            patch.object(smoke, "_check_capability", return_value=capability),
            patch.object(smoke, "_check_selector", return_value=selector),
            patch.object(smoke, "_check_delegation", return_value=delegation),
        ):
            return smoke.run_smoke(
                codex_home=Path("fixture-codex-home"),
                codex_command="codex",
                python_command="python",
                desktop_version="desktop fixture",
                timeout=1,
            )

    def test_all_checks_pass_and_do_not_change_repository(self):
        before = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout

        report = self.run_report()

        after = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        self.assertEqual(report.compatibility, smoke.PASS)
        self.assertEqual(report.protected.status, smoke.PASS)
        self.assertEqual(report.runtime.status, smoke.PASS)
        self.assertEqual(before, after)
        self.assertNotIn("reason:", report.render())

    def test_missing_cli_is_blocked(self):
        report = self.run_report(
            cli=(
                smoke.CheckResult(
                    smoke.BLOCKED, reason="Codex CLI is missing or unusable"
                ),
                "unknown",
            )
        )

        self.assertEqual(report.compatibility, smoke.BLOCKED)
        self.assertEqual(report.cli.status, smoke.BLOCKED)
        self.assertIn("Compatibility:\nBLOCKED", report.render())

    def test_capability_mismatch_requires_review(self):
        report = self.run_report(
            capability=smoke.CheckResult(
                smoke.REVIEW,
                reason="Luna capability mismatch",
                evidence=("unsupported efforts: xhigh",),
                targeted_review="Luna capability",
            )
        )

        self.assertEqual(report.compatibility, smoke.REVIEW)
        self.assertEqual(report.capability.status, smoke.REVIEW)
        self.assertIn("unsupported efforts: xhigh", report.render())

    def test_selector_failure_requires_review(self):
        report = self.run_report(
            selector=smoke.SelectorObservation(
                smoke.CheckResult(
                    smoke.REVIEW,
                    reason="Selector status path failed",
                    evidence=("read-only status did not complete",),
                    targeted_review="selector status",
                )
            )
        )

        self.assertEqual(report.compatibility, smoke.REVIEW)
        self.assertEqual(report.selector.status, smoke.REVIEW)

    def test_delegation_failure_requires_review(self):
        report = self.run_report(
            delegation=smoke.CheckResult(
                smoke.REVIEW,
                reason="Delegation smoke failed",
                evidence=("one-child delegation did not complete",),
                targeted_review="native delegation",
            )
        )

        self.assertEqual(report.compatibility, smoke.REVIEW)
        self.assertEqual(report.delegation.status, smoke.REVIEW)

    def test_protected_state_change_is_fail_and_requires_review(self):
        report = self.run_report(
            protected_before=protected_snapshot("before"),
            protected_after=protected_snapshot("after"),
        )

        self.assertEqual(report.compatibility, smoke.REVIEW)
        self.assertEqual(report.protected.status, smoke.FAIL)
        self.assertIn("changed protected paths: AGENTS.md", report.render())

    def test_new_runtime_unknown_requires_review_with_relative_path(self):
        report = self.run_report(
            runtime_after=runtime_snapshot(
                {"new-runtime/state.json": {"type": "file", "sha256": "new"}}
            )
        )

        self.assertEqual(report.compatibility, smoke.REVIEW)
        self.assertEqual(report.runtime.status, smoke.REVIEW)
        self.assertIn("UNKNOWN path fingerprints: sha256:", report.render())
        self.assertNotIn("new-runtime/state.json", report.render())

    def test_changed_invalid_known_runtime_path_requires_review(self):
        report = self.run_report(
            runtime_after=runtime_snapshot(
                {"queue_99.sqlite-wal": {"type": "file", "sha256": "new"}}
            )
        )

        self.assertEqual(report.compatibility, smoke.REVIEW)
        self.assertEqual(report.runtime.status, smoke.REVIEW)
        self.assertIn("contract-invalid path fingerprints: sha256:", report.render())
        self.assertNotIn("queue_99.sqlite-wal", report.render())

    def test_runtime_evidence_does_not_expose_private_relative_paths(self):
        report = self.run_report(
            runtime_after=runtime_snapshot(
                {
                    "profiles/alice@example.com/secrets.txt": {
                        "type": "file",
                        "sha256": "new",
                    }
                }
            )
        )

        rendered = report.render()
        self.assertIn("UNKNOWN path fingerprints: sha256:", rendered)
        self.assertNotIn("alice@example.com", rendered)
        self.assertNotIn("secrets.txt", rendered)

    def test_capability_probe_uses_explicit_codex_home(self):
        observed = []

        def probe(_command, _timeout, *, codex_home):
            observed.append(codex_home)
            return {
                "all_supported": True,
                "results": [
                    {"effort": effort, "supported": True}
                    for effort in smoke.EFFORTS
                ],
            }

        with patch.object(smoke, "run_probe", side_effect=probe):
            result = smoke._check_capability(
                "codex", Path("explicit-codex-home"), 1
            )

        self.assertEqual(result.status, smoke.PASS)
        self.assertEqual(observed, [Path("explicit-codex-home")])

    def test_cli_version_uses_explicit_codex_home(self):
        completed = subprocess.CompletedProcess([], 0, "codex-cli fixture", "")
        with (
            patch.dict(
                os.environ,
                {
                    "PATH": "fixture-path",
                    "CODEX_HOME": "ambient-codex-home",
                    "CODEX_API_KEY": "fixture-codex-key",
                    "HTTP_PROXY": "http://fixture-proxy",
                    "UNRELATED_SENTINEL_SECRET": "must-not-cross",
                },
                clear=True,
            ),
            patch.object(smoke.subprocess, "run", return_value=completed) as run,
        ):
            result, version = smoke._check_cli(
                "codex", Path("explicit-codex-home"), 1
            )

        self.assertEqual(result.status, smoke.PASS)
        self.assertEqual(version, "codex-cli fixture")
        self.assertEqual(
            run.call_args.kwargs["env"]["CODEX_HOME"],
            str(Path("explicit-codex-home")),
        )
        self.assertEqual(run.call_args.kwargs["env"]["PATH"], "fixture-path")
        self.assertNotIn("CODEX_API_KEY", run.call_args.kwargs["env"])
        self.assertNotIn("HTTP_PROXY", run.call_args.kwargs["env"])
        self.assertNotIn(
            "UNRELATED_SENTINEL_SECRET", run.call_args.kwargs["env"]
        )

    def selector_observation(self, payload):
        completed = subprocess.CompletedProcess(
            [], 0, json.dumps(payload), ""
        )
        with (
            patch.object(smoke, "_fingerprint_tree", return_value="same"),
            patch.object(smoke.subprocess, "run", return_value=completed),
        ):
            return smoke._check_selector(
                python_command="python",
                codex_home=Path("codex-home"),
                timeout=1,
            )

    def test_selector_valid_misconfigured_status_still_passes_execution_check(self):
        payload = {
            "diagnostic_schema_version": 1,
            "health": "Misconfigured",
            "reason_codes": ["PROJECT_OVERRIDE_PRESENT"],
            "selection_initialized": True,
            "selected_role": "luna_max",
            "selected_effort": "max",
        }
        observation = self.selector_observation(payload)

        self.assertEqual(observation.result.status, smoke.PASS)
        self.assertEqual(observation.payload, payload)

    def test_selector_process_uses_minimal_local_environment(self):
        payload = {
            "diagnostic_schema_version": 1,
            "health": "Healthy",
            "reason_codes": ["OK"],
            "selection_initialized": True,
            "selected_role": "luna_max",
            "selected_effort": "max",
        }
        completed = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
        with (
            patch.dict(
                os.environ,
                {
                    "PATH": "fixture-path",
                    "CODEX_API_KEY": "fixture-codex-key",
                    "UNRELATED_SENTINEL_SECRET": "must-not-cross",
                },
                clear=True,
            ),
            patch.object(smoke, "_fingerprint_tree", return_value="same"),
            patch.object(
                smoke.subprocess, "run", return_value=completed
            ) as run,
        ):
            observation = smoke._check_selector(
                python_command="python",
                codex_home=Path("explicit-codex-home"),
                timeout=1,
            )

        environment = run.call_args.kwargs["env"]
        self.assertEqual(observation.result.status, smoke.PASS)
        self.assertEqual(environment["PATH"], "fixture-path")
        self.assertEqual(environment["CODEX_HOME"], "explicit-codex-home")
        self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertNotIn("CODEX_API_KEY", environment)
        self.assertNotIn("UNRELATED_SENTINEL_SECRET", environment)

    def test_selector_expected_override_with_degradation_still_passes(self):
        payload = {
            "diagnostic_schema_version": 1,
            "health": "Misconfigured",
            "reason_codes": ["PROJECT_OVERRIDE_PRESENT", "LKG_FALLBACK_ACTIVE"],
            "selection_initialized": True,
            "selected_role": "luna_max",
            "selected_effort": "max",
        }

        self.assertEqual(self.selector_observation(payload).result.status, smoke.PASS)

    def test_selector_integrity_misconfiguration_requires_review(self):
        for codes in (
            ["MANIFEST_MISSING"],
            ["PROJECT_OVERRIDE_PRESENT", "SELECTOR_OWNERSHIP_MISMATCH"],
            ["PROJECT_OVERRIDE_PRESENT", "AGENT_SET_INCOMPLETE"],
        ):
            with self.subTest(codes=codes):
                payload = {
                    "diagnostic_schema_version": 1,
                    "health": "Misconfigured",
                    "reason_codes": codes,
                    "selection_initialized": True,
                    "selected_role": "luna_max",
                    "selected_effort": "max",
                }
                observation = self.selector_observation(payload)
                self.assertEqual(observation.result.status, smoke.REVIEW)

    def test_selector_unavailable_status_requires_review(self):
        payload = {
            "diagnostic_schema_version": 1,
            "health": "Unavailable",
            "reason_codes": ["DAILY_ROLE_UNAVAILABLE"],
            "selection_initialized": True,
            "selected_role": "luna_max",
            "selected_effort": "max",
        }

        self.assertEqual(self.selector_observation(payload).result.status, smoke.REVIEW)

    def test_delegation_process_uses_explicit_codex_home(self):
        observed = []

        def run(*_args, **kwargs):
            observed.append(kwargs["env"])
            return subprocess.CompletedProcess([], 0, "", "")

        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            (codex_home / "config.toml").write_text(
                'model_provider = "fixture"\n'
                '[model_providers.fixture]\n'
                'env_key = "FIXTURE_PROVIDER_TOKEN"\n'
                'env_http_headers = { "X-Tenant" = "FIXTURE_TENANT" }\n'
                '[mcp_servers.fixture]\n'
                'bearer_token_env_var = "FIXTURE_MCP_BEARER"\n'
                'env_http_headers = { "X-MCP" = "FIXTURE_MCP_HEADER" }\n'
                'env_vars = ["FIXTURE_MCP_LOCAL"]\n',
                encoding="utf-8",
            )
            with (
                patch.dict(
                    os.environ,
                    {
                        "PATH": "fixture-path",
                        "CODEX_HOME": "ambient-codex-home",
                        "CODEX_API_KEY": "fixture-codex-key",
                        "CODEX_ACCESS_TOKEN": "fixture-access-token",
                        "OPENAI_FEDERATION_RULE_ID": "fixture-rule",
                        "OPENAI_IDENTITY_TOKEN_FILE": "/fixture/identity-token",
                        "OPENAI_WORKLOAD_IDENTITY_CONTEXT": '{"fixture":"context"}',
                        "HTTP_PROXY": "http://fixture-proxy",
                        "https_proxy": "http://fixture-lower-proxy",
                        "CODEX_CA_CERTIFICATE": "/fixture/codex-ca.pem",
                        "SSL_CERT_FILE": "/fixture/ssl-ca.pem",
                        "FIXTURE_PROVIDER_TOKEN": "fixture-provider-token",
                        "FIXTURE_TENANT": "fixture-tenant",
                        "FIXTURE_MCP_BEARER": "fixture-mcp-bearer",
                        "FIXTURE_MCP_HEADER": "fixture-mcp-header",
                        "FIXTURE_MCP_LOCAL": "fixture-mcp-local",
                        "UNRELATED_SENTINEL_SECRET": "must-not-cross",
                    },
                    clear=True,
                ),
                patch.object(
                    smoke, "_rollout_files", side_effect=[set(), {Path("parent")}]
                ),
                patch.object(smoke, "_fingerprint_tree", return_value="same"),
                patch.object(smoke.subprocess, "run", side_effect=run),
                patch.object(
                    smoke,
                    "_delegation_rollout_scope",
                    return_value={Path("parent")},
                ),
                patch.object(smoke, "_validate_runtime_case"),
            ):
                result = smoke._check_delegation(
                    codex_command="codex",
                    codex_home=codex_home,
                    selector_payload=HEALTHY_SELECTOR,
                    timeout=1,
                )

        self.assertEqual(result.status, smoke.PASS)
        self.assertEqual(len(observed), 1)
        environment = observed[0]
        self.assertEqual(environment["CODEX_HOME"], str(codex_home))
        self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")
        for name in (
            "CODEX_API_KEY",
            "CODEX_ACCESS_TOKEN",
            "OPENAI_FEDERATION_RULE_ID",
            "OPENAI_IDENTITY_TOKEN_FILE",
            "OPENAI_WORKLOAD_IDENTITY_CONTEXT",
            "HTTP_PROXY",
            "CODEX_CA_CERTIFICATE",
            "SSL_CERT_FILE",
            "FIXTURE_PROVIDER_TOKEN",
            "FIXTURE_TENANT",
            "FIXTURE_MCP_BEARER",
            "FIXTURE_MCP_HEADER",
            "FIXTURE_MCP_LOCAL",
        ):
            self.assertIn(name, environment)
        self.assertTrue(
            "https_proxy" in environment or "HTTPS_PROXY" in environment
        )
        self.assertNotIn("UNRELATED_SENTINEL_SECRET", environment)

    def test_delegation_invalid_child_configuration_requires_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            (codex_home / "config.toml").write_text(
                '[model_providers.fixture\n',
                encoding="utf-8",
            )
            with (
                patch.object(smoke, "_rollout_files", return_value=set()),
                patch.object(smoke, "_fingerprint_tree", return_value="same"),
                patch.object(smoke.subprocess, "run") as run,
            ):
                result = smoke._check_delegation(
                    codex_command="codex",
                    codex_home=codex_home,
                    selector_payload=HEALTHY_SELECTOR,
                    timeout=1,
                )

        self.assertEqual(result.status, smoke.REVIEW)
        self.assertEqual(
            result.reason, "Child environment configuration is invalid"
        )
        self.assertEqual(
            result.evidence, ("child environment could not be resolved",)
        )
        run.assert_not_called()

    def test_delegation_auth_command_or_external_sqlite_home_requires_review(self):
        fixtures = (
            (
                'model_provider = "fixture"\n'
                '[model_providers.fixture.auth]\n'
                'command = "fixture-auth-helper"\n',
                {},
            ),
            ("", {"CODEX_SQLITE_HOME": "external-sqlite-home"}),
        )
        for config, environment in fixtures:
            with self.subTest(config=config), tempfile.TemporaryDirectory() as temporary:
                codex_home = Path(temporary)
                (codex_home / "config.toml").write_text(config, encoding="utf-8")
                with (
                    patch.dict(
                        os.environ,
                        {"PATH": "fixture-path", **environment},
                        clear=True,
                    ),
                    patch.object(smoke, "_rollout_files", return_value=set()),
                    patch.object(smoke, "_fingerprint_tree", return_value="same"),
                    patch.object(smoke.subprocess, "run") as run,
                ):
                    result = smoke._check_delegation(
                        codex_command="codex",
                        codex_home=codex_home,
                        selector_payload=HEALTHY_SELECTOR,
                        timeout=1,
                    )

            self.assertEqual(result.status, smoke.REVIEW)
            self.assertEqual(
                result.reason,
                "Child environment configuration is invalid",
            )
            run.assert_not_called()

    def test_delegation_evidence_retries_until_rollout_writer_settles(self):
        with (
            patch.object(smoke.time, "monotonic", side_effect=[0, 0]),
            patch.object(smoke.time, "sleep"),
            patch.object(smoke, "_rollout_files", return_value={Path("parent")}),
            patch.object(
                smoke,
                "_delegation_rollout_scope",
                side_effect=[
                    smoke.HarnessFailure("child rollout incomplete"),
                    {Path("parent"), Path("child")},
                ],
            ) as scope,
            patch.object(smoke, "_validate_runtime_case") as validate,
        ):
            smoke._wait_for_delegation_evidence(
                codex_home=Path("codex-home"),
                before_rollouts=set(),
                expected_role="luna_max",
                expected_effort="max",
                expected_receipt="Sol/Luna: delegated · luna_max ×1",
                timeout=20,
            )

        self.assertEqual(scope.call_count, 2)
        validate.assert_called_once()

    def test_malformed_rollout_requires_review_instead_of_raising(self):
        completed = subprocess.CompletedProcess([], 0, "", "")
        with (
            patch.object(smoke, "_compatibility_rollout_files", side_effect=[set(), {Path("parent")}]),
            patch.object(smoke, "_fingerprint_tree", return_value="same"),
            patch.object(smoke.subprocess, "run", return_value=completed),
            patch.object(smoke, "_load_json_lines", return_value=[{"type": "session_meta"}]),
            patch.object(smoke.time, "monotonic", side_effect=[0, 6]),
        ):
            result = smoke._check_delegation(
                codex_command="codex",
                codex_home=Path("explicit-codex-home"),
                selector_payload=HEALTHY_SELECTOR,
                timeout=5,
            )

        self.assertEqual(result.status, smoke.REVIEW)
        self.assertEqual(result.reason, "Delegation evidence is incompatible")
        self.assertEqual(result.evidence, ("rollout evidence is malformed",))

    def test_compatibility_rollouts_cover_cli_and_desktop_session_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            cli_rollout = codex_home / "sessions" / "cli.jsonl"
            desktop_rollout = (
                codex_home / "browser" / "sessions" / "desktop.jsonl"
            )
            cli_rollout.parent.mkdir(parents=True)
            desktop_rollout.parent.mkdir(parents=True)
            cli_rollout.write_text("{}\n", encoding="utf-8")
            desktop_rollout.write_text("{}\n", encoding="utf-8")

            observed = smoke._compatibility_rollout_files(codex_home)

        self.assertEqual(observed, {cli_rollout, desktop_rollout})

    def test_render_uses_requested_field_contract(self):
        lines = self.run_report().render().splitlines()

        self.assertEqual(
            lines,
            [
                "Sol/Luna Compatibility Smoke",
                "Codex Desktop: desktop fixture",
                "Codex CLI: codex-cli fixture",
                "CLI: PASS",
                "Luna capability: PASS",
                "Selector: PASS",
                "Delegation: PASS",
                "Protected state: PASS",
                "Runtime contract: PASS",
                "Compatibility:",
                "PASS",
            ],
        )

    def test_display_value_rejects_private_or_secret_shaped_output(self):
        self.assertEqual(smoke._display_value(r"C:\private\codex.exe"), "unknown")
        self.assertEqual(smoke._display_value("token=secretvalue"), "unknown")

    def test_selector_command_is_status_only(self):
        command = smoke._selector_command(
            python_command="python",
            selector_path=Path("selector.py"),
            codex_home=Path("codex-home"),
        )

        self.assertIn("--status-json", command)
        self.assertNotIn("--ensure-daily", command)
        self.assertIn("--codex-home", command)
        self.assertIn("--state-dir", command)

    def test_documentation_prioritizes_smoke_after_codex_update(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

        for content in (english, chinese):
            self.assertIn("Codex Compatibility Smoke", content)
            self.assertIn("scripts/compatibility_smoke.py", content)
            self.assertIn("REVIEW REQUIRED", content)
            self.assertIn("O1–O10", content)
        self.assertIn("no project change", english)
        self.assertIn("无需修改项目", chinese)


if __name__ == "__main__":
    unittest.main()
