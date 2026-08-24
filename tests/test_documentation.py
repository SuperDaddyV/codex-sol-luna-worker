import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-CN.md"
ASSIST = ROOT / "CODEX_SOL_LUNA_INSTALL_ASSIST.md"
ASSIST_ZH = ROOT / "CODEX_SOL_LUNA_INSTALL_ASSIST.zh-CN.md"
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
PUBLIC_DOCS = (
    README,
    README_ZH,
    ASSIST,
    ASSIST_ZH,
    SETUP,
    ROOT / "ARCHITECTURE.md",
    ROOT / "RUNTIME_TESTS.md",
    ROOT / "SECURITY.md",
    ROOT / "CHANGELOG.md",
)
LEGACY_DEFAULT_SETUP_COMMIT = "e1967f8fc957904e3f90b0dd6140430f792d9956"
PREVIOUS_STABLE_ASSIST_COMMIT = "39594139eaeeda705528733fc383333504546fb6"
PREVIOUS_STABLE_SETUP_COMMIT = "2c912b1e1a0fdbd115eb605517fde9385b633745"
PREVIOUS_STABLE_RUNTIME_SOURCE_COMMIT = "67a72f8accc5d53ef04ff8d64d8838e397ceecda"
V411_ASSIST_CONTRACT_COMMIT = "17eb1d370929e884f91c5f1920a2e0868ce4a421"
V411_SETUP_CONTRACT_COMMIT = "d4a044a04df509285ef38c6afc28b5a68a48a0f9"
PINNED_ASSIST_COMMIT = "a130c676fa5924e44034dc8c27f3dc0abfc3bcad"
PINNED_SETUP_COMMIT = "4b2a6004fb92b6661166cb73e656cc2888b0a2ef"
V412_SETUP_CONTRACT_COMMIT = PINNED_SETUP_COMMIT
PINNED_ASSIST_BLOB_URL = (
    "https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/"
    f"{PINNED_ASSIST_COMMIT}/CODEX_SOL_LUNA_INSTALL_ASSIST.md"
)
PINNED_SETUP_BLOB_URL = (
    "https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/"
    f"{PINNED_SETUP_COMMIT}/CODEX_SOL_LUNA_SETUP.md"
)
RC5_RUNTIME_SOURCE_COMMIT = "5ae88ff9190b31174c55a6136c0c8c8611d0b34c"
RC5_SETUP_CONTRACT_COMMIT = "ccd9d84da2f74df9ca2d919729b75eebf2dac27a"
RC5_STALE_SETUP_CONTRACT_COMMIT = "7affbcda6f68cd125aaf6eec3c0e3ff04ebd60d9"
RC6_RUNTIME_SOURCE_COMMIT = "50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49"
RC6_SETUP_CONTRACT_COMMIT = "3e19e2f547c6fca2a888a176767e8dc69240acbc"
RC6_STALE_SETUP_CONTRACT_COMMIT = "86424ea4d6f6630a34b6e4daa22d2d93a5576ddf"
V411_RUNTIME_SOURCE_COMMIT = "ca8e9e4caf5564ffe8d0a11fe376047594f8a748"
V412_RUNTIME_SOURCE_COMMIT = "551520c2435aca94d60132f292edbd53cc975cbe"
V412_EXACT_CI_RUN = "32717295801"
V412_MASTER_EVIDENCE_COMMIT = "fac118ac5ca096aaf1ef8d68b79bfc1372998a5a"
V412_MASTER_CI_RUN = "32717520585"
V412_BASELINE_RUNTIME_SOURCE_COMMIT = (
    "50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49"
)
ASSIST_RAW_PATTERN = re.compile(
    r"https://raw\.githubusercontent\.com/"
    r"SuperDaddyV/codex-sol-luna-worker/([0-9a-f]{40})/"
    r"CODEX_SOL_LUNA_INSTALL_ASSIST\.md"
)
SETUP_RAW_PATTERN = re.compile(
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
        self.assertTrue(ASSIST.is_file())
        self.assertTrue(ASSIST_ZH.is_file())
        self.assertTrue(SETUP.is_file())
        self.assertIn("[简体中文](README.zh-CN.md)", text(README))
        self.assertIn("[English](README.md)", text(README_ZH))
        self.assertIn(
            "[review-only Chinese translation](CODEX_SOL_LUNA_INSTALL_ASSIST.zh-CN.md)",
            text(README),
        )
        self.assertIn(
            "[安装协助合同中文审阅版](CODEX_SOL_LUNA_INSTALL_ASSIST.zh-CN.md)",
            text(README_ZH),
        )

    def test_required_badges_and_homepage_sections(self):
        for path, headings in (
            (
                README,
                (
                    "What it is",
                    "Core value",
                    "Requirements",
                    "Install with Codex",
                    "Daily use",
                    "Confirm it is working",
                    "Upgrade, rollback, and uninstall",
                    "Technical documentation",
                    "Feedback",
                    "License",
                ),
            ),
            (
                README_ZH,
                (
                    "这是什么",
                    "核心价值",
                    "系统要求",
                    "使用 Codex 安装",
                    "日常使用",
                    "如何确认生效",
                    "升级、回滚与卸载",
                    "技术文档",
                    "反馈",
                    "License",
                ),
            ),
        ):
            content = text(path)
            self.assertIn("actions/workflows/validate.yml/badge.svg", content)
            self.assertIn("releases/tag/v4.1.2", content)
            self.assertIn("img.shields.io/badge/stable-v4.1.2", content)
            self.assertIn("github/license", content)
            self.assertEqual(
                re.findall(r"(?m)^## (.+)$", content),
                list(headings),
            )
            self.assertGreaterEqual(len(content.splitlines()), 120)
            self.assertLessEqual(len(content.splitlines()), 180)
            self.assertNotIn("historical_preview", content)

    def test_stable_installation_entry_declares_hard_prerequisites(self):
        english = text(README)
        chinese = text(README_ZH)
        assist = text(ASSIST)
        for phrase in (
            "Sol/Luna Assisted Installation",
            "Codex CLI: PASS <version> / MISSING_OR_UNUSABLE",
            "Python: PASS <version> / MISSING_OR_UNSUPPORTED",
            "Git: PASS <version> / MISSING",
            "GitHub HTTPS: PASS / BLOCKED / NOT_CHECKED (Git required)",
            "Recovery: NONE / SAFE / AWAITING_APPROVAL / NEEDS_USER_ACTION",
            "Ready: YES / NO",
            "codex --version",
            "git --version",
            "git ls-remote",
        ):
            self.assertIn(phrase, assist)
        for content in (english, chinese):
            self.assertIn(PINNED_ASSIST_COMMIT, content)
            self.assertIn(PINNED_SETUP_COMMIT, content)

        self.assertIn("Codex Desktop alone is not sufficient", english)
        self.assertIn("Git for the required immutable exact-commit checkout", english)
        self.assertIn("仅安装 Codex Desktop 还不够", chinese)
        self.assertIn("用于不可变精确 commit checkout 的 Git", chinese)

    def test_readme_uses_single_v412_immutable_installation_entry(self):
        english = text(README)
        chinese = text(README_ZH)
        for content in (english, chinese):
            assist_url = (
                "https://raw.githubusercontent.com/SuperDaddyV/"
                f"codex-sol-luna-worker/{PINNED_ASSIST_COMMIT}/"
                "CODEX_SOL_LUNA_INSTALL_ASSIST.md"
            )
            self.assertEqual(content.count(assist_url), 1)
            self.assertEqual(content.count(PINNED_ASSIST_BLOB_URL), 1)
            self.assertEqual(content.count(PINNED_SETUP_BLOB_URL), 3)
            self.assertNotIn("](CODEX_SOL_LUNA_INSTALL_ASSIST.md)", content)
            self.assertNotIn("](CODEX_SOL_LUNA_SETUP.md)", content)
            self.assertNotIn(LEGACY_DEFAULT_SETUP_COMMIT, content)
            self.assertIn(PINNED_ASSIST_COMMIT, content)
            self.assertIn(PINNED_SETUP_COMMIT, content)
            self.assertIn(V412_RUNTIME_SOURCE_COMMIT, content)
            for historical in ("RC3", "RC4", "RC5", "RC6"):
                self.assertNotIn(historical, content)
        assist = text(ASSIST)
        self.assertIn(V412_RUNTIME_SOURCE_COMMIT, assist)
        self.assertEqual(
            SETUP_RAW_PATTERN.findall(assist),
            [PINNED_SETUP_COMMIT],
        )
        self.assertIn(V412_RUNTIME_SOURCE_COMMIT, text(SETUP))
        self.assertIn("single prompt", english)
        self.assertIn("只粘贴下面这一个提示词", chinese)
        for stale in (
            PREVIOUS_STABLE_ASSIST_COMMIT,
            PREVIOUS_STABLE_SETUP_COMMIT,
            PREVIOUS_STABLE_RUNTIME_SOURCE_COMMIT,
            "unreleased candidate",
            "未发布候选",
        ):
            self.assertNotIn(stale, english + chinese)

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

    def test_assisted_installation_recovery_is_bounded_and_preserves_setup_gates(self):
        content = text(ASSIST)
        setup_url = (
            "https://raw.githubusercontent.com/SuperDaddyV/"
            f"codex-sol-luna-worker/{V412_SETUP_CONTRACT_COMMIT}/"
            "CODEX_SOL_LUNA_SETUP.md"
        )

        for identity in (
            "Stable release: `v4.1.2`",
            V412_RUNTIME_SOURCE_COMMIT,
            V412_SETUP_CONTRACT_COMMIT,
            setup_url,
            "`v4.1.0-rc6` remains an immutable historical",
        ):
            self.assertIn(identity, content)

        for boundary in (
            "Do not stop at the first missing",
            "Safe automatic recovery",
            "Approval-required recovery",
            "request to install Sol/Luna is not approval",
            "Persistent `PATH` changes require separate inclusion",
            "Guided user action",
            "SOL_LUNA_ASSIST_RESUME",
            "Run a deterministic remediation command at most once",
            "at most three total attempts for a transient GitHub HTTPS check",
            "No output for 30 seconds is not by itself a product failure",
            "Any setup result containing",
            "fresh-task smoke",
            "--dangerously-bypass-approvals-and-sandbox",
        ):
            self.assertIn(boundary, content)

        for protected in (
            "authentication",
            "proxy",
            "certificate trust",
            "sandbox",
            "organization policy",
            "ownership",
            "transaction",
        ):
            self.assertIn(protected, content.lower())

        self.assertNotIn(
            "raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/master/",
            content,
        )

    def test_v412_stable_assistance_is_deterministic_and_bounded(self):
        content = text(ASSIST)
        stable = content.index("## 11. v4.1.2 deterministic Stable assistance")
        capability = content.index("### 11.6 Early capability and installer handoff")
        dry_run = content.index("installer's non-mutating dry-run", capability)
        self.assertLess(stable, capability)
        self.assertLess(capability, dry_run)
        for phrase in (
            "P3 standalone bootstrap is explicitly out of scope",
            "scripts/install_assist.py check",
            "scripts/install_assist.py plan",
            "scripts/install_assist.py recover",
            "scripts/install_assist.py install",
            "scripts/install_assist.py report",
            "RECOVERY_PLAN_CHANGED",
            "scripts/install_recovery_catalog.json",
            "approval_required",
            "user_action",
            "IDEMPOTENT_PASS",
            "run the five Luna efforts through ephemeral",
            "Codex executions with user config ignored",
            "whitelist-only",
            "Installation Complete",
            "Reload Required",
            "Selector Initialization Required",
            "Needs User Action",
            "Blocked",
        ):
            self.assertIn(phrase, content)
        for phase in (
            "CHECKING",
            "SAFE_RECOVERY",
            "AWAITING_APPROVAL",
            "RECHECKING",
            "CAPABILITY_PRECHECK",
            "DRY_RUN",
            "INSTALLING",
            "RELOAD_REQUIRED",
            "SELECTOR_INITIALIZATION",
            "FRESH_TASK_SMOKE",
            "COMPLETE",
            "NEEDS_USER_ACTION",
            "BLOCKED",
        ):
            self.assertIn(phase, content)
        self.assertIn("This section specifies the deterministic installation experience", content)
        self.assertIn("exact immutable documentation commit", content)
        self.assertIn("No preflight state file is created", content)
        self.assertIn("DAILY_SELECTION_PROOF_REQUIRED", content)
        self.assertIn("--ensure-daily --print-selection", content)
        self.assertIn("The smoke remains status-only", content)
        self.assertNotIn("unreleased `v4.1.2`", content)
        self.assertNotIn("assistance candidate", content)
        self.assertNotIn(PREVIOUS_STABLE_RUNTIME_SOURCE_COMMIT, content)
        self.assertNotIn(PREVIOUS_STABLE_SETUP_COMMIT, content)
        self.assertEqual(
            content.count(f"--source-commit {V412_RUNTIME_SOURCE_COMMIT}"), 2
        )

    def test_chinese_assistance_document_is_review_only_and_covers_same_boundaries(self):
        content = text(ASSIST_ZH)
        self.assertIn("本文件只用于中文审阅，不是可执行安装权威", content)
        self.assertIn("英文 `CODEX_SOL_LUNA_INSTALL_ASSIST.md`", content)
        self.assertIn("不能执行可变 `master` 上的中文译文", content)
        self.assertIn(V412_RUNTIME_SOURCE_COMMIT, content)
        self.assertIn(V412_SETUP_CONTRACT_COMMIT, content)
        for phrase in (
            "`v4.1.0-rc6` 继续作为",
            "不可变的历史 Prerelease",
            "P3 排除边界",
            "scripts/install_assist.py check",
            "RECOVERY_PLAN_CHANGED",
            "scripts/install_recovery_catalog.json",
            "IDEMPOTENT_PASS",
            "Capability 前置门禁",
            "Installer 唯一写入权威",
            "脱敏支持报告",
            "Installation Complete",
            "Reload Required",
            "Selector Initialization Required",
            "Needs User Action",
            "Blocked",
            "SELECTOR_INITIALIZATION",
            "DAILY_SELECTION_PROOF_REQUIRED",
            "--ensure-daily --print-selection",
            "--dangerously-bypass-approvals-and-sandbox",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn(
            "raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/master/",
            content,
        )
        self.assertNotIn("安装助手候选", content)
        self.assertNotIn(PREVIOUS_STABLE_RUNTIME_SOURCE_COMMIT, content)
        self.assertNotIn(PREVIOUS_STABLE_SETUP_COMMIT, content)

    def test_setup_records_v412_stable_evidence_and_handoff(self):
        content = text(SETUP)
        architecture = text(ROOT / "ARCHITECTURE.md")
        security = text(ROOT / "SECURITY.md")
        handoff = content.index("## 22. v4.1.2 Stable assisted installation handoff")
        self.assertGreater(handoff, content.index("## 21. Final Report"))
        for phrase in (
            "Sections 0–21 are the reviewed `v4.1.2` Stable transactional setup contract",
            "scripts/install_assist.py",
            "scripts/install_recovery_catalog.json",
            "clean detached Stable Source Commit A checkout",
            "runs the five",
            "ephemeral read-only Luna capability checks",
            "Without `--apply`, it stops at `DRY_RUN`",
            "zero-write, zero-backup fast path",
            "`SELECTOR_INITIALIZATION` gate",
            "--ensure-daily --print-selection",
            "must not initialize Daily selection",
            "P3 standalone bootstrap remains out of scope",
        ):
            self.assertIn(phrase, content)
        self.assertIn(V412_RUNTIME_SOURCE_COMMIT, content[:handoff])
        self.assertNotIn("<V4_1_2_SOURCE_COMMIT>", content)
        self.assertIn("pins this Setup contract", content)
        self.assertIn("The public README pins this contract", content)
        for phrase in (
            "v4.1.2",
            "exact recovery plan + SHA-256 Plan ID",
            "scripts/install_recovery_catalog.json",
            "explicit Daily selector initialization and proof",
            "compatibility smoke remains read-only and status-only",
        ):
            self.assertIn(phrase, architecture + content)
        for phrase in (
            "v4.1.2 Stable boundary",
            "executes approved recovery as argument vectors without a",
            "five-effort Luna probe is ephemeral",
            "P3",
            "standalone bootstrap is excluded",
            "controls do not change the installed selector",
            "Stable assistant adds an explicit post-reload `SELECTOR_INITIALIZATION` handoff",
            "cannot initialize Daily selection itself",
        ):
            self.assertIn(phrase, security)
        for value in (
            V412_RUNTIME_SOURCE_COMMIT,
            V412_EXACT_CI_RUN,
            V412_MASTER_EVIDENCE_COMMIT,
            V412_MASTER_CI_RUN,
            V412_BASELINE_RUNTIME_SOURCE_COMMIT,
            "DRY_RUN_PASS",
            "UPGRADED",
            "CURRENT_INSTALLATION_PASS",
            "169.4",
            "0.146.0",
        ):
            self.assertIn(value, content)

    def test_stable_feedback_forms_and_guidance(self):
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
                self.assertIn("current Stable release", content)
                self.assertNotIn("public beta", content.lower())
                self.assertNotIn("public-beta", content.lower())
                self.assertNotIn("v4.1.0-rc4", content)

        bug = text(ISSUE_TEMPLATE_DIR / "bug-report.yml")
        for phrase in (
            "API keys", "access tokens", "cookies", "passwords",
            "private repository credentials", "personal email", "home-directory",
            "proprietary source/code", "minimum relevant logs",
            "unless specifically requested during later troubleshooting",
        ):
            self.assertIn(phrase, bug)
        self.assertIn("placeholder: v4.1.1", bug)
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
            (english, "## Feedback", "the entire `CODEX_HOME`"),
            (chinese, "## 反馈", "整个 `CODEX_HOME`"),
        ):
            self.assertIn(feedback_heading, content)
            self.assertGreater(
                content.index(feedback_heading), content.index("GitHub Releases")
            )
            for filename in templates:
                self.assertIn(
                    "https://github.com/SuperDaddyV/codex-sol-luna-worker/"
                    f"issues/new?template={filename}",
                    content,
                )
            self.assertIn("CODEX_HOME", content)
            self.assertIn(whole_warning, content)
        self.assertIn("v4.1.2", english)
        self.assertIn("v4.1.2", chinese)
        self.assertIn("[Bug Report]", english)
        self.assertIn("[Compatibility Report]", chinese)

    def test_stable_contract_and_specialized_history_docs_are_explicit(self):
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
                ASSIST,
                SETUP,
                ROOT / "ARCHITECTURE.md",
                ROOT / "SECURITY.md",
            )
        )
        default_assist_url = (
            "https://raw.githubusercontent.com/SuperDaddyV/"
            f"codex-sol-luna-worker/{PINNED_ASSIST_COMMIT}/"
            "CODEX_SOL_LUNA_INSTALL_ASSIST.md"
        )
        for path in (README, README_ZH):
            content = text(path)
            self.assertEqual(content.count(default_assist_url), 1)
            self.assertIn(PINNED_ASSIST_COMMIT, content)
            self.assertIn(PINNED_SETUP_COMMIT, content)
            self.assertIn("releases/tag/v4.1.2", content)
            self.assertIn("img.shields.io/badge/stable-v4.1.2", content)
            self.assertNotIn("historical_preview", content)
            self.assertNotIn(LEGACY_DEFAULT_SETUP_COMMIT, content)
            self.assertNotRegex(content, r"\bRC[3-6]\b")
            for removed in (
                "O4/O9",
                "Runtime Cases",
                "No confirmed product-runtime regression",
                "Luna ref-cost",
                "ModelDial API",
                "LKG fallback",
                "Advanced / Manual",
                "Optional parallel self-test",
                "## FAQ",
            ):
                self.assertNotIn(removed, content)
            self.assertEqual(content.count("O1–O10"), 1)
            for link in (
                "CODEX_SOL_LUNA_SETUP.md",
                "ARCHITECTURE.md",
                "RUNTIME_TESTS.md",
                "SECURITY.md",
                "CHANGELOG.md",
                "codex-sol-luna-worker/releases",
            ):
                self.assertIn(link, content)
            for placeholder in ("<APPROVED_40_HEX_COMMIT>", "<TBD>", "pending"):
                self.assertNotIn(placeholder, content)

        setup = text(SETUP)
        self.assertIn("Contract version: `v4.1.2`", setup)
        self.assertIn(
            "`v4.1.2` is the Stable release target and default installation target",
            setup,
        )
        self.assertIn(V412_RUNTIME_SOURCE_COMMIT, setup)
        self.assertIn("`v4.1.1` remains the previous immutable Stable release", setup)
        self.assertIn("`v4.1.0` remains an older immutable Stable release", setup)
        self.assertIn("`v4.1.0-rc6` remains an immutable historical Prerelease", setup)
        self.assertIn("`v4.1.0-rc5` is an older historical Preview", setup)
        for path in source_docs:
            content = text(path)
            self.assertIn("RC4", content)
            self.assertIn("v4.1.0-rc5", content)
            self.assertIn(V411_RUNTIME_SOURCE_COMMIT, content)
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

        historical_evidence = text(ROOT / "RUNTIME_TESTS.md") + text(
            ROOT / "CHANGELOG.md"
        )
        self.assertIn(RC5_RUNTIME_SOURCE_COMMIT, historical_evidence)
        self.assertIn(RC5_SETUP_CONTRACT_COMMIT, historical_evidence)

        self.assertIn("v4.1.0-rc3", text(ROOT / "CHANGELOG.md"))
        self.assertIn(
            "FRESH_REPO_CONTEXT_DELEGATION_PASS",
            text(ROOT / "ARCHITECTURE.md"),
        )
        self.assertIn(
            "For v4.1.2 Stable, the recorded real Global baseline was `v4.1.0-rc6`",
            setup,
        )
        self.assertNotIn("REAL GLOBAL RUNTIME NOT RUN", combined)
        self.assertIn("Global Runtime G1-G7", combined)
        self.assertIn("v4.1.2 Stable", text(README))
        self.assertIn("v4.1.2 Stable", text(README_ZH))
        self.assertNotRegex(combined, r"v4\.1\.0-rc3[^\n]*(?:—|is|是)\s*STABLE")
        self.assertNotIn(
            "RC2 repository-context delegation validation remains pending", combined
        )
        self.assertNotIn("RC3 Receipt runtime acceptance has not run", combined)
        runtime = text(ROOT / "RUNTIME_TESTS.md")
        self.assertIn(
            "v4.1.2 — CURRENT STABLE RELEASE / DEFAULT INSTALLATION TARGET",
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
        self.assertIn(V411_RUNTIME_SOURCE_COMMIT, runtime)
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

    def test_v412_stable_publication_uses_v412_immutable_installation_chain(self):
        changelog = text(ROOT / "CHANGELOG.md")
        security = text(ROOT / "SECURITY.md")
        public_installation = "\n".join(
            text(path)
            for path in (
                README,
                README_ZH,
                SETUP,
                ASSIST,
                ASSIST_ZH,
            )
        )

        self.assertIn("## v4.1.2 (published Stable release)", changelog)
        self.assertIn("## v4.1.2 Stable boundary", security)
        stable_docs = (
            changelog,
            security,
            text(ROOT / "ARCHITECTURE.md"),
            text(ROOT / "RUNTIME_TESTS.md"),
        )
        stable_evidence = "\n".join(stable_docs)
        for value in (
            V412_RUNTIME_SOURCE_COMMIT,
            V412_EXACT_CI_RUN,
            V412_MASTER_EVIDENCE_COMMIT,
            V412_MASTER_CI_RUN,
            V412_BASELINE_RUNTIME_SOURCE_COMMIT,
            "357",
            "DRY_RUN_PASS",
            "UPGRADED",
            "CURRENT_INSTALLATION_PASS",
            "configuration_preserved true",
            "effective_changes 2",
            "effective_changes 0",
            "backup NONE",
            "169.4",
            "codex-cli 0.146.0",
            "V412_PUBLIC_RELEASE = STABLE",
            PINNED_SETUP_COMMIT,
            PINNED_ASSIST_COMMIT,
        ):
            self.assertIn(value, stable_evidence)
        self.assertIn(
            "`v4.1.2` is the current Stable release and default installation target.",
            security,
        )
        self.assertIn("releases/tag/v4.1.2", public_installation)
        self.assertIn("img.shields.io/badge/stable-v4.1.2", public_installation)
        self.assertIn("Stable release: `v4.1.2`", text(ASSIST))
        self.assertNotIn("releases/tag/v4.1.1", text(README) + text(README_ZH))
        self.assertNotIn("img.shields.io/badge/stable-v4.1.1", public_installation)
        for content in stable_docs + (text(README), text(README_ZH)):
            for unresolved in ("unreleased", "candidate", "not_established"):
                self.assertNotIn(unresolved, content.lower())

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
        self.assertIn("v4.1.2 (published Stable release)", changelog)
        self.assertIn("Source Commit A", changelog)
        for content in (architecture, security):
            self.assertIn(
                "`v4.1.2` is the current Stable release and default installation target.",
                content,
            )
        self.assertIn(
            "v4.1.2 — CURRENT STABLE RELEASE / DEFAULT INSTALLATION TARGET",
            architecture,
        )
        self.assertIn("Contract version: `v4.1.2`", setup)
        self.assertGreaterEqual(setup.count(V412_RUNTIME_SOURCE_COMMIT), 7)
        self.assertNotIn(RC6_SETUP_CONTRACT_COMMIT, setup)
        self.assertIn("`v4.1.1` remains the previous immutable Stable release", setup)
        self.assertIn("`v4.1.0` remains an older immutable Stable release", setup)
        self.assertIn("`v4.1.0-rc6` remains an immutable historical Prerelease", setup)
        self.assertIn("`v4.1.0-rc5` is an older historical Preview", setup)
        self.assertIn(
            "`v4.1.2` is the Stable release target and default installation target",
            setup,
        )
        self.assertNotIn("RC6 is not tagged", setup)
        self.assertNotIn("RC6 is not published", setup)
        self.assertIn("recorded real Global baseline was `v4.1.0-rc6`", setup)
        self.assertIn("Final O4/O9 re-certification", setup)
        self.assertIn(
            "only `sol-luna-v4/selector.py`",
            setup,
        )
        self.assertNotRegex(readmes, r"\bRC[3-6]\b")
        self.assertIn(
            "Install the pinned v4.1.2 Stable target",
            text(README),
        )
        self.assertIn(
            "安装固定的 v4.1.2 Stable 目标",
            text(README_ZH),
        )
        self.assertIn(f"checkout --detach {V412_RUNTIME_SOURCE_COMMIT}", setup)
        self.assertIn(
            f"Require `git rev-parse HEAD` to equal `{V412_RUNTIME_SOURCE_COMMIT}` exactly",
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
            self.assertIn(f"--source-commit {V412_RUNTIME_SOURCE_COMMIT}", command)

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
        self.assertIn("not the runtime payload source", setup)
        self.assertIn("SETUP_CONTRACT_SELF_REFERENCE_REQUIRED = NO", setup)
        for placeholder in ("<source-sha>", "TBD", "TODO-for-release"):
            self.assertNotIn(placeholder, "\n".join((architecture, security, runtime, changelog)))

    def test_readme_status_guidance_is_bilingual_and_bounded(self):
        english = text(README)
        chinese = text(README_ZH)
        architecture = text(ROOT / "ARCHITECTURE.md")
        security = text(ROOT / "SECURITY.md")

        self.assertIn("## Confirm it is working", english)
        self.assertIn("## 如何确认生效", chinese)
        self.assertEqual(english.count("Check Sol/Luna status."), 1)
        self.assertEqual(chinese.count("检查 Sol/Luna 状态"), 1)
        for content in (english, chinese):
            self.assertIn("Status Healthy", content)
            self.assertIn("Agents 5/5 Ready", content)
            self.assertIn("Native leaf Ready", content)
            self.assertIn("RUNTIME_TESTS.md", content)
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
        self.assertNotIn(
            "raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/master/"
            "CODEX_SOL_LUNA_INSTALL_ASSIST.md",
            combined,
        )

        english_shas = ASSIST_RAW_PATTERN.findall(english)
        chinese_shas = ASSIST_RAW_PATTERN.findall(chinese)
        self.assertEqual(len(english_shas), 1)
        self.assertEqual(len(chinese_shas), 1)
        self.assertEqual(english_shas, chinese_shas)
        self.assertNotIn(LEGACY_DEFAULT_SETUP_COMMIT, combined)
        self.assertEqual(
            english_shas,
            [PINNED_ASSIST_COMMIT],
        )
        self.assertNotIn(RC6_SETUP_CONTRACT_COMMIT, english_shas)
        for sha in english_shas:
            self.assertRegex(sha, r"^[0-9a-f]{40}$")

        self.assertEqual(SETUP_RAW_PATTERN.findall(english), [])
        self.assertEqual(SETUP_RAW_PATTERN.findall(chinese), [])
        self.assertEqual(
            SETUP_RAW_PATTERN.findall(text(ASSIST)),
            [V412_SETUP_CONTRACT_COMMIT],
        )

    def test_all_local_documentation_links_exist(self):
        for document in (README, README_ZH, ASSIST, SETUP, ROOT / "SECURITY.md"):
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
        self.assertIn("without a Hook Router", text(README))
        self.assertIn("Do not install or introduce", text(SETUP))

    def test_setup_contract_orchestrates_real_cli(self):
        content = text(SETUP)
        for command in (
            "scripts/install.py --dry-run --codex-home <CODEX_HOME> "
            f"--source-commit {V412_RUNTIME_SOURCE_COMMIT}",
            "scripts/install.py --apply --codex-home <CODEX_HOME> "
            f"--source-commit {V412_RUNTIME_SOURCE_COMMIT}",
            "scripts/install.py --apply --migrate-v3 --codex-home <CODEX_HOME> "
            f"--source-commit {V412_RUNTIME_SOURCE_COMMIT}",
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
