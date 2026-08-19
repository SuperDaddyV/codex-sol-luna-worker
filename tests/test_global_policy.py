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
        self.assertIn("<STATUS_COMMAND>", TEMPLATE)
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
        self.assertIn("reasonable delegation opportunity", TEMPLATE)
        self.assertIn("Receipt generation must not invoke the selector", TEMPLATE)
        self.assertIn("probe capabilities", TEMPLATE)
        self.assertIn("spawn or inspect a child", TEMPLATE)
        self.assertIn("read files, call tools or networks", TEMPLATE)
        self.assertIn("access the network", TEMPLATE)
        self.assertIn("write state", TEMPLATE)
        self.assertIn("repository content", TEMPLATE)
        self.assertIn("add telemetry", TEMPLATE)
        self.assertIn("not runtime attestation", TEMPLATE)
        self.assertIn("Never expose hidden chain-of-thought", TEMPLATE)
        self.assertIn("same-batch, same-pricing, same-effort", TEMPLATE)
        for forbidden_claim in (
            "token saved",
            "cost saved",
            "bill saved",
            "quota saved",
            "whole-task saving",
        ):
            self.assertNotIn(forbidden_claim, TEMPLATE.lower())

        self.assertIn("<SELECTOR_COMMAND>", TEMPLATE)
        self.assertIn("Do not substitute a direct model", TEMPLATE)
        self.assertIn("Never select `ultra`", TEMPLATE)

    def test_luna_unavailable_requires_current_task_parent_visible_evidence(self):
        for required in (
            "`LUNA_UNAVAILABLE` is evidence-gated",
            "current task's normal delegation path already naturally produced "
            "parent-visible execution evidence",
            "selector returned no valid Daily role or failed closed",
            "selected native Luna role",
            "agent discovery",
            "required Luna capability",
            "spawn/agent availability failed",
            "availability failure must be an observed execution fact from the current task",
        ):
            with self.subTest(required=required):
                self.assertIn(required, TEMPLATE)

    def test_luna_unavailable_is_not_inferred_or_used_as_fallback(self):
        for insufficient in (
            "selector that was not invoked",
            "no child attempt",
            "Sol retaining or completing the task",
            "docs-only work",
            "sequential dependencies",
            "no independent bounded work",
        ):
            with self.subTest(insufficient=insufficient):
                self.assertIn(insufficient, TEMPLATE)
        self.assertIn("No delegation does not mean Luna unavailable", TEMPLATE)
        self.assertIn(
            "current-task parent-visible availability failure evidence does not exist",
            TEMPLATE,
        )
        self.assertIn("never the default Sol-only fallback", TEMPLATE)
        self.assertIn("most direct high-level non-availability reason", TEMPLATE)
        self.assertIn("clearest parent-visible support", TEMPLATE)

    def test_receipt_regression_matrix_remains_fact_based(self):
        expected_semantics = {
            "reasoning": "core work is architecture",
            "delegated": "requires at least one Luna direct child that actually ran",
            "no-independent-work": "execution exists but cannot be separated safely",
            "real-unavailable-evidence": "selector returned no valid Daily role or failed closed",
        }
        for case, semantic in expected_semantics.items():
            with self.subTest(case=case):
                self.assertIn(semantic, TEMPLATE)
        self.assertIn("actual selected native role", TEMPLATE)
        self.assertIn("actual direct Luna children", TEMPLATE)
        self.assertIn("actually overlapped in execution", TEMPLATE)

    def test_windows_rendering_quotes_paths(self):
        rendered = render_global_policy(
            TEMPLATE, r"C:\Program Data\Codex Home", platform_name="Windows"
        )
        self.assertIn(r'python "C:\Program Data\Codex Home\sol-luna-v4\selector.py"', rendered)
        self.assertIn(r'--state-dir "C:\Program Data\Codex Home\sol-luna-v4\state"', rendered)
        self.assertIn("--ensure-daily --print-selection", rendered)
        self.assertIn("--status-json", rendered)
        self.assertNotIn("<CODEX_HOME>", rendered)
        self.assertNotIn("<STATUS_COMMAND>", rendered)

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

    def test_receipt_suffix_order_and_budget(self):
        order = (
            " · parallel",
            " · Luna ref-cost ↓X.X%",
            " · LKG",
            " · capability <source_effort>→<selected_effort>",
        )
        positions = [TEMPLATE.index(item) for item in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("exact order", TEMPLATE)
        self.assertIn("at most one of each suffix", TEMPLATE)
        self.assertIn("Sol-only receipts never receive", TEMPLATE)
        self.assertIn("Normal healthy/API/full-capability state stays silent", TEMPLATE)

    def test_receipt_requires_zero_extra_work(self):
        self.assertIn("Save that one result for delegation and the final receipt", TEMPLATE)
        for forbidden_extra in (
            "must not invoke the selector",
            "probe capabilities",
            "spawn or inspect a child",
            "read files, call tools or networks",
            "write state",
            "add telemetry",
        ):
            self.assertIn(forbidden_extra, TEMPLATE)

    def test_status_and_diagnostic_share_one_read_only_reader(self):
        self.assertIn("## Natural-language status and diagnostics", TEMPLATE)
        self.assertEqual(TEMPLATE.count("run `<STATUS_COMMAND>` exactly once"), 1)
        self.assertIn("run the same `<STATUS_COMMAND>` exactly once", TEMPLATE)
        for forbidden_action in (
            "fetch ModelDial",
            "create or refresh a profile or LKG",
            "take the selector lock",
            "spawn Luna",
            "write state",
        ):
            self.assertIn(forbidden_action, TEMPLATE)
        self.assertIn("Selection not initialized", TEMPLATE)
        self.assertIn("sanitized whitelist", TEMPLATE)

    def test_latest_stable_and_prerelease_semver_contract(self):
        self.assertIn("including prereleases", TEMPLATE)
        self.assertIn("Do not ask Stable or Preview again", TEMPLATE)
        self.assertIn("strict project SemVer", TEMPLATE)
        self.assertIn("Choose by SemVer precedence", TEMPLATE)
        self.assertIn("never by publication time", TEMPLATE)
        self.assertIn("draft = false", TEMPLATE)
        self.assertIn("non-null `published_at`", TEMPLATE)
        self.assertIn("Reject build metadata", TEMPLATE)
        self.assertIn("malformed leading zeroes", TEMPLATE)
        self.assertIn("duplicate Releases with the same normalized version", TEMPLATE)

    def test_immutable_tag_and_prerelease_risk_contract(self):
        for required in (
            "direct ref",
            "annotated or lightweight tag",
            "exact 40-hex commit",
            "detached checkout",
            "TAG_MOVED",
            "--source-commit <40hex>",
            "never install from `master`",
            "If the installed version is already the target",
            "zero writes and zero backups",
            "never downgrade automatically",
            "渠道：Prerelease / Public Beta",
            "外部真实运行验证少于稳定版",
            "修改托管文件前会创建事务备份",
        ):
            self.assertIn(required, TEMPLATE)

    def test_upgrade_discovery_stays_outside_installer(self):
        installer = (ROOT / "scripts" / "install.py").read_text(encoding="utf-8")
        self.assertIn("Release discovery is a semantic workflow outside the installer", TEMPLATE)
        self.assertNotIn("/repos/SuperDaddyV/codex-sol-luna-worker/releases", installer)
        self.assertNotIn("target_commitish", installer)
        self.assertNotIn("urllib", installer)


if __name__ == "__main__":
    unittest.main()
