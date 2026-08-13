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
PINNED_SETUP_COMMIT = "e1967f8fc957904e3f90b0dd6140430f792d9956"
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
            self.assertIn("releases/tag/v4.1.0-rc4", content)
            self.assertIn("img.shields.io/badge/preview-v4.1.0--rc4", content)
            self.assertIn("github/license", content)
            self.assertIn(heading, content)

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
        self.assertIn("`v4.1.0-rc4` is the current Preview prerelease", english)
        self.assertIn("`v4.0.0` 仍是 Stable 稳定版本", chinese)
        self.assertIn("`v4.1.0-rc4` 是当前 Preview prerelease", chinese)
        self.assertIn("欢迎提交 Bug 报告", chinese)
        self.assertIn("欢迎提交成功的兼容性报告", chinese)

    def test_v41_rc4_published_flow_and_runtime_acceptance_are_explicit(self):
        aligned_docs = (
            SETUP,
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
        for path in aligned_docs:
            self.assertIn("v4.1.0-rc4", text(path))
            self.assertIn("published prerelease", text(path).lower())
            self.assertNotIn("source candidate", text(path).lower())
        for path in (README, README_ZH):
            self.assertIn("v4.1.0-rc4", text(path))
            self.assertNotIn("source candidate", text(path).lower())
        self.assertIn("v4.1.0-rc3", text(ROOT / "CHANGELOG.md"))
        for path in (README, README_ZH, ROOT / "ARCHITECTURE.md"):
            self.assertIn("FRESH_REPO_CONTEXT_DELEGATION_PASS", text(path))
        self.assertIn(
            "existing valid `v4.1.0-rc3` installation is an existing v4 upgrade for RC4",
            text(SETUP),
        )
        self.assertIn("https://modeldial.com/api/v1/radar/latest.json", combined)
        self.assertIn(
            "https://modeldial.com/data/reference-snapshots/latest.json", combined
        )
        self.assertIn("Radar HTML runtime fallback is removed", text(README))
        self.assertNotIn("REAL GLOBAL RUNTIME NOT RUN", combined)
        self.assertIn("Global Runtime G1-G7", combined)
        self.assertIn("current published preview prerelease", text(README))
        self.assertIn("当前已发布的 Preview prerelease", text(README_ZH))
        self.assertIn("public beta", text(README))
        self.assertIn("公开测试版本", text(README_ZH))
        self.assertIn("no selector, no delegation, and no availability evidence", text(README))
        self.assertIn("没有 selector、没有 delegation、没有 availability evidence", text(README_ZH))
        self.assertIn("v4.0.0` remains stable", text(README))
        self.assertIn("v4.0.0` 仍是稳定版本", text(README_ZH))
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
            "v4.1.0-rc4 — PUBLISHED PRERELEASE / CURRENT PREVIEW / "
            "RUNTIME ACCEPTANCE PASS",
            runtime,
        )
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
        self.assertEqual(len(english_shas), 1)
        self.assertEqual(len(chinese_shas), 1)
        self.assertEqual(english_shas, chinese_shas)
        self.assertEqual(english_shas, [PINNED_SETUP_COMMIT])
        self.assertRegex(english_shas[0], r"^[0-9a-f]{40}$")

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
            "scripts/install.py --dry-run --codex-home <CODEX_HOME>",
            "scripts/install.py --apply --codex-home <CODEX_HOME>",
            "scripts/install.py --apply --migrate-v3 --codex-home <CODEX_HOME>",
            "scripts/install.py --rollback <BACKUP_PATH> --codex-home <CODEX_HOME>",
            "scripts/install.py --uninstall --codex-home <CODEX_HOME>",
        ):
            self.assertIn(command, content)
        self.assertIn("Python 3.11 or newer", content)
        self.assertIn("INSTALL_RUNTIME_PASS", content)
        self.assertIn("Fresh Session Requirement", content)
        self.assertNotIn("--validation-sandbox --codex-home <CODEX_HOME>", content)


if __name__ == "__main__":
    unittest.main()
