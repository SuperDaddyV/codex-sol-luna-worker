import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-CN.md"
SETUP = ROOT / "CODEX_SOL_LUNA_SETUP.md"
PUBLIC_DOCS = (README, README_ZH, SETUP, ROOT / "SECURITY.md")
PLACEHOLDER = "<PINNED_SETUP_URL_PENDING_DOCS_COMMIT>"
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
            self.assertIn("github/license", content)
            self.assertIn(heading, content)

    def test_v41_rc3_source_flow_and_runtime_boundary_are_explicit(self):
        release_docs = (
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
        for path in (
            README,
            README_ZH,
            SETUP,
            ROOT / "ARCHITECTURE.md",
            ROOT / "SECURITY.md",
        ):
            self.assertIn("v4.1.0-rc3", text(path))
        for path in (README, README_ZH, ROOT / "ARCHITECTURE.md"):
            self.assertIn("FRESH_REPO_CONTEXT_DELEGATION_PASS", text(path))
        self.assertIn("v4.1.0-rc1", text(SETUP))
        self.assertIn("https://modeldial.com/api/v1/radar/latest.json", combined)
        self.assertIn(
            "https://modeldial.com/data/reference-snapshots/latest.json", combined
        )
        self.assertIn("Radar HTML runtime fallback is removed", text(README))
        self.assertNotIn("REAL GLOBAL RUNTIME NOT RUN", combined)
        self.assertIn("Global Runtime G1-G7", combined)
        self.assertIn("Receipt runtime acceptance", combined)
        self.assertIn("v4.0.0` remains the stable release", text(README))
        self.assertIn("v4.0.0` 仍是稳定版本", text(README_ZH))
        self.assertNotRegex(combined, r"v4\.1\.0-rc3[^\n]*(?:—|is|是)\s*STABLE")
        self.assertNotIn(
            "RC2 repository-context delegation validation remains pending", combined
        )
        for path in release_docs:
            content = text(path)
            self.assertIn("v4.1.0-rc3", content)
            self.assertNotIn("source candidate", content.lower())
        runtime = text(ROOT / "RUNTIME_TESTS.md")
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
