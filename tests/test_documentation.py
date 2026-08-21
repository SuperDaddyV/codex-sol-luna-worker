import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-CN.md"
SETUP = ROOT / "CODEX_SOL_LUNA_SETUP.md"
ISSUE_TEMPLATE_DIR = ROOT / ".github" / "ISSUE_TEMPLATE"
ISSUE_FORMS = {
    "bug-report.yml": {
        "summary", "expected", "os", "codex_client_version", "python_version",
        "install_type", "version", "receipt", "luna_run", "minimal_logs",
        "reproduction", "context", "privacy_confirmation",
    },
    "compatibility-report.yml": {
        "os", "codex_client_version", "python_version", "install_type",
        "from_version", "installed_version", "installation_result", "daily_role",
        "sol_only_receipt", "delegated_receipt", "luna_delegation",
        "parallel_delegation", "usage_duration", "problems_found",
        "overall_result", "privacy_confirmation",
    },
    "feature-feedback.yml": {
        "type", "improvement", "reason", "suggested_behavior", "context",
        "privacy_confirmation",
    },
}
PUBLIC_DOCS = (README, README_ZH, SETUP, ROOT / "SECURITY.md")
PLACEHOLDER = "<PINNED_SETUP_URL_PENDING_DOCS_COMMIT>"
LEGACY_DEFAULT_SETUP_COMMIT = "e1967f8fc957904e3f90b0dd6140430f792d9956"
PINNED_SETUP_COMMIT = "3e19e2f547c6fca2a888a176767e8dc69240acbc"
RC5_RUNTIME_SOURCE_COMMIT = "5ae88ff9190b31174c55a6136c0c8c8611d0b34c"
RC5_SETUP_CONTRACT_COMMIT = "ccd9d84da2f74df9ca2d919729b75eebf2dac27a"
RC5_STALE_SETUP_CONTRACT_COMMIT = "7affbcda6f68cd125aaf6eec3c0e3ff04ebd60d9"
RC6_RUNTIME_SOURCE_COMMIT = "50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49"
RC6_SETUP_CONTRACT_COMMIT = "3e19e2f547c6fca2a888a176767e8dc69240acbc"
RC6_STALE_SETUP_CONTRACT_COMMIT = "86424ea4d6f6630a34b6e4daa22d2d93a5576ddf"
STABLE_RUNTIME_SOURCE_COMMIT = "67a72f8accc5d53ef04ff8d64d8838e397ceecda"
RAW_PATTERN = re.compile(
    r"https://raw\.githubusercontent\.com/"
    r"SuperDaddyV/codex-sol-luna-worker/([0-9a-f]{40})/"
    r"CODEX_SOL_LUNA_SETUP\.md"
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def local_markdown_targets(content: str):
    for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", content):
        target = match.group(1).split("#", 1)[0]
        if not target or "://" in target or target.startswith(("#", "mailto:")):
            continue
        yield target


class DocumentationTests(unittest.TestCase):
    def test_bilingual_navigation_and_setup_contract(self):
        self.assertTrue(SETUP.is_file())
        self.assertIn("[简体中文](README.zh-CN.md)", text(README))
        self.assertIn("[English](README.md)", text(README_ZH))

    def test_required_badges_and_install_sections(self):
        for path, heading in (
            (README, "## Install with Codex"),
            (README_ZH, "## 使用 Codex 安装"),
        ):
            content = text(path)
            self.assertIn("actions/workflows/validate.yml/badge.svg", content)
            self.assertIn("releases/tag/v4.0.0", content)
            self.assertIn("img.shields.io/badge/stable-v4.0.0", content)
            self.assertIn("releases/tag/v4.1.0-rc6", content)
            self.assertIn("img.shields.io/badge/preview-v4.1.0--rc6", content)
            self.assertIn("github/license", content)
            self.assertIn(heading, content)

    def test_rc6_installation_entry_declares_hard_prerequisites(self):
        english = text(README)
        chinese = text(README_ZH)
        for content in (english, chinese):
            for phrase in (
                "Sol/Luna Installation Preflight",
                "Codex CLI: PASS <version> / MISSING_OR_UNUSABLE",
                "Python: PASS <version> / MISSING_OR_UNSUPPORTED",
                "Git: PASS <version> / MISSING",
                "GitHub HTTPS: PASS / BLOCKED",
                "Ready: YES / NO",
                "codex --version",
                "git --version",
                "git ls-remote",
            ):
                self.assertIn(phrase, content)
            self.assertIn(RC6_SETUP_CONTRACT_COMMIT, content)

        self.assertIn("Codex Desktop alone is not sufficient", english)
        self.assertIn("Git for the required immutable exact-commit checkout", english)
        self.assertIn("仅安装 Codex Desktop 还不够", chinese)
        self.assertIn("必须使用 Git 获取并校验不可变的精确 commit", chinese)

    def test_rc6_release_replaces_rc5_default_installation_entry(self):
        english = text(README)
        chinese = text(README_ZH)
        for content in (english, chinese):
            setup_url = (
                "https://raw.githubusercontent.com/SuperDaddyV/"
                f"codex-sol-luna-worker/{RC6_SETUP_CONTRACT_COMMIT}/"
                "CODEX_SOL_LUNA_SETUP.md"
            )
            self.assertEqual(content.count(setup_url), 2)
            self.assertNotIn(LEGACY_DEFAULT_SETUP_COMMIT, content)
            self.assertIn(RC6_RUNTIME_SOURCE_COMMIT, content)
            self.assertIn(RC6_SETUP_CONTRACT_COMMIT, content)
        self.assertIn(
            "The default installation path is the immutable RC6 Setup contract",
            english,
        )
        self.assertIn(
            "the installer runtime source remains separately fixed at",
            english,
        )
        self.assertIn(
            "RC6 Final O4/O9 re-certification | `PASS`",
            english,
        )
        self.assertIn(
            "默认安装路径使用当前 Preview／Public Beta 的 immutable RC6 Setup contract",
            chinese,
        )
        self.assertIn(
            "installer runtime source 则单独固定为",
            chinese,
        )
        self.assertIn("RC6 最终 O4/O9 再认证 | 通过 isolated acceptance harness 获得 `PASS`", chinese)

    def test_setup_preflight_stops_missing_dependencies_before_writes(self):
        content = text(SETUP)
        preflight = content.index("## 0A. Installation Preflight")
        source = content.index("## 5. Source Acquisition")
        capability = content.index("## 6. Codex Capability")
        dry_run = content.index("## 8. Dry Run")
        self.assertLess(preflight, source)
        self.assertLess(source, capability)
        self.assertLess(capability, dry_run)
        self.assertLess(preflight, dry_run)
        for phrase in (
            "Before cloning or downloading source",
            "before any filesystem write",
            "`Ready: YES` requires every hard prerequisite above to pass",
            "do not create or modify files",
            "BLOCKED: CODEX_CLI_REQUIRED",
            "BLOCKED: PYTHON_3_11_WITH_TOMLLIB_REQUIRED",
            "BLOCKED: GIT_REQUIRED_FOR_IMMUTABLE_SOURCE",
            "BLOCKED: GITHUB_HTTPS_REQUIRED",
            "Do not install system dependencies, modify `PATH`",
            "`curl` and other download tools are not required",
        ):
            self.assertIn(phrase, content)

    def test_public_beta_feedback_forms_and_guidance(self):
        self.assertEqual(
            text(ISSUE_TEMPLATE_DIR / "config.yml").strip(),
            "blank_issues_enabled: false",
        )
        for filename, expected_ids in ISSUE_FORMS.items():
            path = ISSUE_TEMPLATE_DIR / filename
            with self.subTest(form=filename):
                self.assertTrue(path.is_file())
                content = text(path)
                ids = re.findall(r"(?m)^\s+id:\s+([A-Za-z0-9_-]+)\s*$", content)
                field_ids = set(ids)
                self.assertEqual(field_ids, expected_ids)
                self.assertEqual(len(ids), len(field_ids))
                for key in ("name:", "description:", "title:", "body:"):
                    self.assertIn(key, content)
                self.assertIn("validations:", content)
                self.assertIn("type: dropdown", content)
                self.assertIn("options:", content)
                labels = re.findall(r"(?m)^      label: (.+)$", content)
                self.assertEqual(len(labels), len(set(labels)))
                self.assertNotIn("labels:", content)
                self.assertNotIn("contact_links:", content)

        bug = text(ISSUE_TEMPLATE_DIR / "bug-report.yml")
        for phrase in (
            "API keys", "access tokens", "cookies", "passwords",
            "private repository credentials", "personal email", "home-directory",
            "proprietary source/code", "minimum relevant logs",
            "unless specifically requested during later troubleshooting",
        ):
            self.assertIn(phrase, bug)
        self.assertIn("placeholder: v4.1.0-rc4", bug)
        self.assertIn("`Sol/Luna: Sol-only · no independent bounded work`", bug)
        self.assertIn("`Sol/Luna: delegated · luna_max ×2 · parallel`", bug)
        self.assertIn("`No Receipt`", bug)
        self.assertIn('- "Yes"\n        - "No"\n        - "Not sure"', bug)

        compatibility = text(ISSUE_TEMPLATE_DIR / "compatibility-report.yml")
        for phrase in (
            "Success reports are welcome", "OS compatibility", "fresh installs",
            "upgrades", "Luna delegation", "Delegation Receipt behavior",
            "public GitHub Issues only", "write None if no problems were found",
            "placeholder: luna_max / Unknown",
            "placeholder: Works normally on my environment",
        ):
            self.assertIn(phrase, compatibility)
        for option in (
            "PASS", "PASS with minor issue", "FAIL", "Not tested",
            "Just installed", "Less than 1 day", "1–3 days", "4–7 days",
            "More than 1 week",
        ):
            self.assertIn(option, compatibility)

        feature = text(ISSUE_TEMPLATE_DIR / "feature-feedback.yml")
        self.assertIn("name: Feature request / feedback", feature)
        self.assertIn("Non-guarantee notice", feature)
        for option in (
            "Feature request", "Documentation", "UX / usability",
            "Installation experience", "Delegation behavior", "Other",
        ):
            self.assertIn(f"- {option}", feature)

        english = text(README)
        chinese = text(README_ZH)
        templates = (
            "bug-report.yml",
            "compatibility-report.yml",
            "feature-feedback.yml",
        )
        for content, feedback_heading, whole_warning in (
            (english, "## Public Beta Feedback", "the whole `CODEX_HOME`"),
            (chinese, "## Public Beta 反馈", "整个 `CODEX_HOME`"),
        ):
            self.assertIn(feedback_heading, content)
            self.assertLess(content.index(feedback_heading), content.index("Basic"))
            for filename in templates:
                self.assertIn(
                    "https://github.com/SuperDaddyV/codex-sol-luna-worker/"
                    f"issues/new?template={filename}",
                    content,
                )
            self.assertIn("CODEX_HOME", content)
            self.assertIn(whole_warning, content)
        self.assertIn("`v4.0.0` remains the Stable release", english)
        self.assertIn("`v4.1.0-rc6` is the current Preview prerelease", english)
        self.assertIn("`v4.0.0` 仍是 Stable 稳定版本", chinese)
        self.assertIn("`v4.1.0-rc6` 是当前 Preview prerelease", chinese)
        self.assertIn("欢迎提交 Bug 报告", chinese)
        self.assertIn("欢迎提交成功的兼容性报告", chinese)

    def test_stable_contract_and_historical_preview_status_are_explicit(self):
        source_docs = (
            ROOT / "RUNTIME_TESTS.md",
            ROOT / "ARCHITECTURE.md",
            ROOT / "SECURITY.md",
            ROOT / "CHANGELOG.md",
        )
        combined = "\n".join(
            text(path)
            for path in (
                README,
                README_ZH,
                SETUP,
                ROOT / "ARCHITECTURE.md",
                ROOT / "SECURITY.md",
            )
        )
        default_setup_url = (
            "https://raw.githubusercontent.com/SuperDaddyV/"
            f"codex-sol-luna-worker/{PINNED_SETUP_COMMIT}/CODEX_SOL_LUNA_SETUP.md"
        )
        for path, preview_heading, publication_row, runtime_row in (
            (
                README,
                "## Current Preview",
                "| Publication | `PUBLISHED — GitHub Prerelease / Public Beta` |",
                "| RC6 O1–O10 and Runtime Cases A/B/C/D | "
                "`PASS` in the documented environment; bounded evidence |",
            ),
            (
                README_ZH,
                "## 当前 Preview",
                "| 发布状态 | `已发布 — GitHub Prerelease／Public Beta` |",
                "| RC6 O1–O10 和 Runtime Cases A/B/C/D | "
                "在 documented environment `PASS`；仍是有边界的证据 |",
            ),
        ):
            content = text(path)
            self.assertIn("RC4", content)
            self.assertIn("v4.1.0-rc5", content)
            self.assertIn("RC6", content)
            self.assertIn(RC6_RUNTIME_SOURCE_COMMIT, content)
            self.assertIn(RC5_RUNTIME_SOURCE_COMMIT, content)
            self.assertIn(RC5_SETUP_CONTRACT_COMMIT, content)
            self.assertIn(preview_heading, content)
            self.assertIn(publication_row, content)
            self.assertIn(runtime_row, content)
            if path == README:
                self.assertIn(
                    "The documented-environment RC5 O1–O10 record remains bounded historical evidence",
                    content,
                )
            else:
                self.assertIn(
                    "documented-environment 的 RC5 O1–O10 记录仍是有边界的历史证据",
                    content,
                )
            if path == README:
                self.assertIn("Final O4/O9 re-certification", content)
            else:
                self.assertIn("最终 O4/O9 再认证", content)
            self.assertIn("`CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`", content)
            for number in range(1, 11):
                self.assertEqual(
                    sum(line.startswith(f"- O{number} ") for line in content.splitlines()),
                    0,
                )
            for feature in (
                "Observability metadata",
                "Sol/Luna Status",
                "Diagnostic report",
                "Degraded indicators",
                "Luna ref-cost Receipt",
                "Upgrade-to-latest UX",
            ):
                self.assertIn(feature, content)
            self.assertEqual(content.count(default_setup_url), 2)
            self.assertNotIn(LEGACY_DEFAULT_SETUP_COMMIT, content)
            self.assertLess(content.index(default_setup_url), content.index(preview_heading))
            self.assertGreater(content.rfind(default_setup_url), content.index(preview_heading))
            preview_start = content.index(preview_heading)
            preview_end = content.index("\n## ", preview_start + len(preview_heading))
            preview_section = content[preview_start:preview_end]
            self.assertNotIn("NOT RUN", preview_section)
            for placeholder in ("<APPROVED_40_HEX_COMMIT>", "<TBD>", "pending"):
                self.assertNotIn(placeholder, preview_section)
            self.assertIn("releases/tag/v4.1.0-rc6", content)
            self.assertIn("img.shields.io/badge/preview-v4.1.0--rc6", content)
            self.assertNotIn("NOT PUBLISHED", content)
            self.assertNotIn("尚未发布", content)
        setup = text(SETUP)
        self.assertIn("Contract version: `v4.1.0`", setup)
        self.assertIn(
            "`v4.1.0` is the Stable release target and current default installation target",
            setup,
        )
        self.assertIn("`v4.1.0-rc6` remains an immutable historical Prerelease", setup)
        self.assertIn("`v4.1.0-rc5` is an older historical Preview", setup)
        for path in source_docs:
            content = text(path)
            self.assertIn("RC4", content)
            self.assertIn("v4.1.0-rc5", content)
            self.assertIn(STABLE_RUNTIME_SOURCE_COMMIT, content)
            self.assertIn("stable", content.lower())
            self.assertIn("prerelease", content.lower())
            for stale in (
                "RC6 is not tagged",
                "RC6 is an unpublished",
                "RC6 remains the unpublished",
                "Published/default Preview remains `v4.1.0-rc5`",
                "release pending",
            ):
                self.assertNotIn(stale, content)
        self.assertIn(
            "is the default installation target/path through the immutable RC6 entry above",
            text(README),
        )
        self.assertIn(
            "并通过上方 immutable RC6 entry 成为默认安装目标／路径",
            text(README_ZH),
        )
        self.assertIn("v4.1.0-rc3", text(ROOT / "CHANGELOG.md"))
        for path in (README, README_ZH, ROOT / "ARCHITECTURE.md"):
            self.assertIn("FRESH_REPO_CONTEXT_DELEGATION_PASS", text(path))
        self.assertIn(
            "existing valid `v4.1.0-rc6` installation is an existing v4 upgrade to Stable",
            text(SETUP),
        )
        self.assertIn("https://modeldial.com/api/v1/radar/latest.json", combined)
        self.assertIn(
            "https://modeldial.com/data/reference-snapshots/latest.json", combined
        )
        self.assertIn("Radar HTML runtime fallback is removed", text(README))
        self.assertNotIn("REAL GLOBAL RUNTIME NOT RUN", combined)
        self.assertIn("Global Runtime G1-G7", combined)
        self.assertIn("current published GitHub Prerelease / Preview", text(README))
        self.assertIn("当前已发布的 GitHub Prerelease／Preview", text(README_ZH))
        self.assertIn("public beta", text(README))
        self.assertIn("公开测试版本", text(README_ZH))
        self.assertIn("no selector, no delegation, and no availability evidence", text(README))
        self.assertIn("没有 selector、没有 delegation、没有 availability evidence", text(README_ZH))
        self.assertIn("v4.0.0` remains Stable", text(README))
        self.assertIn("v4.0.0` 仍是 Stable 稳定版本", text(README_ZH))
        self.assertNotRegex(combined, r"v4\.1\.0-rc3[^\n]*(?:—|is|是)\s*STABLE")
        self.assertNotIn(
            "RC2 repository-context delegation validation remains pending", combined
        )
        self.assertNotIn("RC3 Receipt runtime acceptance has not run", combined)
        for content in (text(README), text(README_ZH)):
            self.assertIn("| RC4 real Global upgrade | `PASS` |", content)
            self.assertIn("| RC4 Case A | `PASS` |", content)
            self.assertIn("| RC4 Case B | `PASS` |", content)
            self.assertIn("| RC4 Case C | `PASS` |", content)
            self.assertIn("| RC4 controlled Case D | `PASS` |", content)
            self.assertIn("| RC3 real Global upgrade | `PASS` |", content)
            self.assertIn("| RC3 Sol-only Receipt | `PASS` |", content)
            self.assertIn("| RC3 delegated Receipt | `PASS` |", content)
        runtime = text(ROOT / "RUNTIME_TESTS.md")
        self.assertIn(
            "v4.1.0 — STABLE RELEASE TARGET / DEFAULT INSTALLATION TARGET",
            runtime,
        )
        self.assertIn(
            "They do not imply runtime validation across every operating system, "
            "Codex client, account, or user environment.",
            runtime,
        )
        self.assertNotIn("CURRENT PREVIEW / RUNTIME ACCEPTANCE PASS", runtime)
        self.assertIn(
            "v4.1.0-rc6 historical Preview — recorded fresh-task runtime acceptance",
            runtime,
        )
        self.assertIn(STABLE_RUNTIME_SOURCE_COMMIT, runtime)
        self.assertIn(RC6_RUNTIME_SOURCE_COMMIT, runtime)
        self.assertIn(
            "Compatibility smoke, O1-O10 acceptance, Final O4/O9 re-certification",
            runtime,
        )
        self.assertIn("are recorded `PASS`", runtime)
        self.assertIn("`RC6_RUNTIME_ACCEPTANCE_COMPLETED = YES`", runtime)
        self.assertIn("`RC6_FINAL_O4_O9_RECERTIFICATION = PASS`", runtime)
        self.assertIn("Real RC3 → RC4 Global upgrade — `PASS`", runtime)
        self.assertIn("Result: `UPGRADED`; effective changes: `2`", runtime)
        for case in ("Runtime Case A", "Runtime Case B", "Runtime Case C", "Runtime Case D"):
            self.assertIn(case, runtime)
        self.assertIn("Sol/Luna: Sol-only · reasoning/architecture task", runtime)
        self.assertIn("Sol/Luna: delegated · luna_max ×3 · parallel", runtime)
        self.assertIn("Sol/Luna: Sol-only · no independent bounded work", runtime)
        self.assertIn("Selector result: `NO_LUNA_PROFILE_AVAILABLE`", runtime)
        self.assertIn("availability evidence `NONE`; `Luna unavailable` is forbidden", runtime)
        self.assertIn("RC1 → RC3 Global upgrade — `PASS`", runtime)
        self.assertIn("Sol-only Receipt — `PASS`", runtime)
        self.assertIn("Delegated Receipt — `PASS`", runtime)
        self.assertNotIn("planned Receipt acceptance — `NOT RUN`", runtime)
        for status in (
            "DAY_2_CROSS_DAY_END_TO_END_PASS",
            "DAY_2_SAME_DAY_NEW_SESSION_PERSISTENCE_PASS",
            "SELECTOR_URL_EXCEPTION_HARDENING = DEFERRED_TO_PRE_STABLE",
        ):
            self.assertIn(status, runtime)
            self.assertIn(status, text(ROOT / "CHANGELOG.md"))
        self.assertIn(
            "CURRENT_TEST_OBSERVED_REFRESH_EVENT_DIRECTLY = NO", runtime
        )
        self.assertIn("CURRENT_TEST_VERIFIED_REFRESH_RESULT = YES", runtime)

        security = text(ROOT / "SECURITY.md")
        self.assertIn("For this public repository", security)
        self.assertNotIn("For a future public repository", security)

    def test_stable_setup_contract_pins_runtime_source_without_self_reference(self):
        architecture = text(ROOT / "ARCHITECTURE.md")
        security = text(ROOT / "SECURITY.md")
        runtime = text(ROOT / "RUNTIME_TESTS.md")
        changelog = text(ROOT / "CHANGELOG.md")
        setup = text(SETUP)
        readmes = text(README) + "\n" + text(README_ZH)

        for required in (
            "structured selection metadata boundary",
            "read-only health reader",
            "fail-soft",
            "single state authority",
        ):
            self.assertIn(required, architecture)
        for required in (
            "exact whitelist",
            "symbolic locations",
            "immutable commit",
            "no auto-updater",
        ):
            self.assertIn(required, security)
        for number in range(1, 11):
            self.assertRegex(setup, rf"(?m)^- O{number} .* — `PASS`[;.]$")
        self.assertIn("v4.1.0 (Stable release target)", changelog)
        self.assertIn("Stable Source Commit A", changelog)
        self.assertIn("Contract version: `v4.1.0`", setup)
        self.assertGreaterEqual(setup.count(STABLE_RUNTIME_SOURCE_COMMIT), 7)
        self.assertNotIn(RC6_SETUP_CONTRACT_COMMIT, setup)
        self.assertIn("`v4.1.0-rc6` remains an immutable historical Prerelease", setup)
        self.assertIn("`v4.1.0-rc5` is an older historical Preview", setup)
        self.assertIn(
            "`v4.1.0` is the Stable release target and current default installation target",
            setup,
        )
        self.assertNotIn("RC6 is not tagged", setup)
        self.assertNotIn("RC6 is not published", setup)
        self.assertIn("RC6 real Global upgrade, O1–O10 runtime acceptance", setup)
        self.assertIn("Final O4/O9 re-certification", setup)
        self.assertIn(
            "The only expected effective installed change is:\n\n"
            "1. `sol-luna-v4/install-manifest.json`.",
            setup,
        )
        self.assertIn("v4.1.0-rc5", readmes)
        self.assertIn(
            "current published GitHub Prerelease / Preview and Public Beta",
            text(README),
        )
        self.assertIn(
            "当前已发布、面向高级用户使用的 GitHub Prerelease／Preview／Public Beta",
            text(README_ZH),
        )
        self.assertIn(f"checkout --detach {STABLE_RUNTIME_SOURCE_COMMIT}", setup)
        self.assertIn(
            f"Require `git rev-parse HEAD` to equal `{STABLE_RUNTIME_SOURCE_COMMIT}` exactly",
            setup,
        )
        installer_commands = [
            line
            for line in setup.splitlines()
            if "scripts/install.py" in line
            and ("--dry-run" in line or "--apply" in line)
        ]
        self.assertEqual(len(installer_commands), 4)
        for command in installer_commands:
            self.assertIn(f"--source-commit {STABLE_RUNTIME_SOURCE_COMMIT}", command)

        for placeholder in (
            "<APPROVED_40_HEX_COMMIT>",
            "<RC6_SOURCE_SHA>",
            "<STABLE_SOURCE_SHA>",
            "<TBD_SHA>",
            "PIN_PENDING",
            "<SETUP_COMMIT>",
            "<SETUP_COMMIT_SHA>",
            "SELF_SHA",
            "CURRENT_DOC_SHA",
        ):
            self.assertNotIn(placeholder, setup)
        self.assertNotRegex(
            setup,
            r"(?m)^(?:git|<PYTHON>)[^\n]*(?:\bmaster\b|\bmain\b|"
            r"origin/master|target_commitish)",
        )
        self.assertNotIn(
            "raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/master/",
            setup,
        )
        self.assertIn("a separate documentation anchor", setup)
        self.assertIn("is not the runtime payload source", setup)
        self.assertIn("SETUP_CONTRACT_SELF_REFERENCE_REQUIRED = NO", setup)
        for placeholder in ("<source-sha>", "TBD", "TODO-for-release"):
            self.assertNotIn(placeholder, "\n".join((architecture, security, runtime, changelog)))

    def test_delegation_receipt_user_guidance_is_bilingual_and_bounded(self):
        english = text(README)
        chinese = text(README_ZH)
        architecture = text(ROOT / "ARCHITECTURE.md")
        security = text(ROOT / "SECURITY.md")

        self.assertIn("## How do I know Sol + Luna is working?", english)
        self.assertIn("## 怎么判断 Sol + Luna 是否已经生效？", chinese)
        self.assertIn("### Basic read-only self-test", english)
        self.assertIn("### Basic 只读自测", chinese)
        self.assertIn("### Optional parallel self-test", english)
        self.assertIn("### 可选并行自测", chinese)
        for content in (english, chinese):
            self.assertIn(
                "Sol/Luna: delegated · <role> ×<direct_child_count>", content
            )
            self.assertIn("0 Luna", content)
            self.assertIn("Receipt", content)
        self.assertIn("not runtime attestation", english)
        self.assertIn("Receipt text is not runtime attestation", architecture)
        self.assertIn("adds no selector or network call", security)

    def test_setup_execution_urls_are_coordinated_and_immutable_when_pinned(self):
        english = text(README)
        chinese = text(README_ZH)
        combined = english + "\n" + chinese
        for content in (english, chinese):
            self.assertNotIn(RC5_STALE_SETUP_CONTRACT_COMMIT, content)
            self.assertNotIn(RC6_STALE_SETUP_CONTRACT_COMMIT, content)
        self.assertNotIn(
            "raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/master/"
            "CODEX_SOL_LUNA_SETUP.md",
            combined,
        )

        if PLACEHOLDER in combined:
            self.assertEqual(english.count(PLACEHOLDER), 1)
            self.assertEqual(chinese.count(PLACEHOLDER), 1)
            self.assertEqual(RAW_PATTERN.findall(combined), [])
            self.assertIn("deliberate for RC3 source Commit A", english)
            self.assertIn("RC3 source Commit A 的有意占位", chinese)
            self.assertNotIn("During RC assembly, the placeholder above", english)
            self.assertNotIn("RC 组装阶段，上面的 placeholder", chinese)
            return

        english_shas = RAW_PATTERN.findall(english)
        chinese_shas = RAW_PATTERN.findall(chinese)
        self.assertEqual(len(english_shas), 2)
        self.assertEqual(len(chinese_shas), 2)
        self.assertEqual(english_shas, chinese_shas)
        self.assertNotIn(LEGACY_DEFAULT_SETUP_COMMIT, combined)
        self.assertEqual(
            english_shas,
            [PINNED_SETUP_COMMIT, RC6_SETUP_CONTRACT_COMMIT],
        )
        for sha in english_shas:
            self.assertRegex(sha, r"^[0-9a-f]{40}$")

    def test_all_local_documentation_links_exist(self):
        for document in (README, README_ZH, SETUP, ROOT / "SECURITY.md"):
            for target in local_markdown_targets(text(document)):
                with self.subTest(document=document.name, target=target):
                    self.assertTrue((document.parent / target).exists())

    def test_public_docs_contain_no_private_paths_runtime_ids_or_secrets(self):
        private_path = re.compile(
            r"(?:\b[A-Z]:\\" + "Users" + r"\\[^\s\\/:]+|"
            r"(?<![A-Za-z0-9_])/" + "Users" + r"/[^\s/]+|"
            r"(?<![A-Za-z0-9_])/" + "home" + r"/[^\s/]+)",
            re.I,
        )
        uuid_value = re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
            r"[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.I,
        )
        labelled_runtime_id = re.compile(
            r"\b(?:session|child|installation|rollout)[_-]?id\b\s*[:=]\s*"
            r"[A-Za-z0-9][A-Za-z0-9._-]{7,}",
            re.I,
        )
        secrets = (
            re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
            re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
            re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
            re.compile(r"AKIA[0-9A-Z]{16}"),
            re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
        )
        for path in PUBLIC_DOCS:
            content = text(path)
            self.assertIsNone(private_path.search(content), path)
            self.assertIsNone(uuid_value.search(content), path)
            self.assertIsNone(labelled_runtime_id.search(content), path)
            for pattern in secrets:
                self.assertIsNone(pattern.search(content), path)

    def test_hooks_are_not_a_current_install_requirement(self):
        content = "\n".join(text(path) for path in (README, README_ZH, SETUP))
        stale_requirements = (
            re.compile(
                r"(?im)^(?![^\n]*\b(?:no|not|do not|does not|without)\b)"
                r"[^\n]*must install[^\n]*(?:Hook Router|PreToolUse)"
            ),
            re.compile(
                r"(?im)^(?![^\n]*\b(?:no|not|do not|does not|without)\b)"
                r"[^\n]*requires?[^\n]*(?:Hook Router|PreToolUse)"
            ),
            re.compile(
                r"(?im)^(?![^\n]*\b(?:no|not|do not|does not|without)\b)"
                r"[^\n]*(?:Hook Router|PreToolUse)[^\n]*is required"
            ),
        )
        for pattern in stale_requirements:
            self.assertIsNone(pattern.search(content))
        self.assertIn("No Hook Router is required", text(README))
        self.assertIn("Do not install or introduce", text(SETUP))

    def test_setup_contract_orchestrates_real_cli(self):
        content = text(SETUP)
        for command in (
            "scripts/install.py --dry-run --codex-home <CODEX_HOME> "
            f"--source-commit {STABLE_RUNTIME_SOURCE_COMMIT}",
            "scripts/install.py --apply --codex-home <CODEX_HOME> "
            f"--source-commit {STABLE_RUNTIME_SOURCE_COMMIT}",
            "scripts/install.py --apply --migrate-v3 --codex-home <CODEX_HOME> "
            f"--source-commit {STABLE_RUNTIME_SOURCE_COMMIT}",
            "scripts/install.py --rollback <BACKUP_PATH> --codex-home <CODEX_HOME>",
            "scripts/install.py --uninstall --codex-home <CODEX_HOME>",
        ):
            self.assertIn(command, content)
        self.assertIn("Python 3.11 or newer", content)
        self.assertIn("INSTALL_RUNTIME_PASS", content)
        self.assertIn("Fresh Session Requirement", content)
        for required in (
            "--print-selection",
            "--status-json",
            "Luna ref-cost ↓X.X%",
            "LKG",
            "capability <source_effort>→<selected_effort>",
            "STATUS_NETWORK = 0",
            "STATUS_SELECTOR_LOCK = 0",
            "STATUS_STATE_WRITES = 0",
            "STATUS_LUNA_SPAWN = 0",
            "Healthy / TODAY_SELECTION_NOT_INITIALIZED",
            "Unavailable / DAILY_PROFILE_INVALID",
            "Misconfigured / DAILY_PROFILE_READ_FAILED",
            "OLD_SAME_DAY_PROFILE_FORCE_REFRESH = NO",
            "STATE_MIGRATION_REQUIRED = NO",
            "Upgrade to the Latest Published Version",
        ):
            self.assertIn(required, content)
        self.assertNotIn("--validation-sandbox --codex-home <CODEX_HOME>", content)


if __name__ == "__main__":
    unittest.main()
