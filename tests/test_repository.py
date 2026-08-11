import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".var", "__pycache__", ".pytest_cache"}
TEXT_SUFFIXES = {".md", ".py", ".toml", ".json", ".yml", ".yaml", ".txt"}
EXECUTABLE_SUFFIXES = {".py", ".toml", ".json", ".yml", ".yaml", ".ps1", ".sh"}


def repository_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or (
            path.suffix.lower() not in TEXT_SUFFIXES
            and path.name not in {"LICENSE", ".gitignore", ".gitattributes"}
        ):
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        yield path


def executable_repository_text_files():
    """Yield implementation/configuration files, excluding historical prose."""

    roots = (ROOT / "src", ROOT / "scripts", ROOT / ".codex", ROOT / ".github")
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in EXECUTABLE_SUFFIXES:
                yield path


class RepositorySafetyTests(unittest.TestCase):
    def test_no_private_paths_installation_ids_or_secret_material(self):
        private_user_path = re.compile(
            r"(?:\b[A-Z]:\\" + "Users" + r"\\[^\s\\/:]+(?:\\[^\s]+)*|"
            r"(?<![A-Za-z0-9_])/" + "Users" + r"/[^\s/]+(?:/[^\s]+)*|"
            r"(?<![A-Za-z0-9_])/" + "home" + r"/[^\s/]+(?:/[^\s]+)*)",
            re.I,
        )
        installation_role = re.compile(
            r"\bslr_[A-Za-z0-9][A-Za-z0-9-]*_(?:low|medium|high|xhigh|max)\b",
            re.I,
        )
        labelled_installation_id = re.compile(
            r"\b(?:installation|install)[_-]?id\b\s*[:=]\s*[\"']?"
            r"[A-Za-z0-9][A-Za-z0-9._-]{2,}",
            re.I,
        )
        labelled_rollout_id = re.compile(
            r"\brollout[_ -]?id\b\s*[:=]\s*[\"']?"
            r"[A-Za-z0-9][A-Za-z0-9._-]{2,}",
            re.I,
        )
        install_marker = re.compile(
            r"\b(?:inst|installation)[_-][A-Za-z0-9][A-Za-z0-9-]{7,}\b",
            re.I,
        )
        rollout_marker = re.compile(
            r"\brollout[_-][A-Za-z0-9][A-Za-z0-9-]{7,}\b", re.I
        )
        rollout_uuid = re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f][0-9a-f]{3}-"
            r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
            re.I,
        )
        secret_patterns = (
            re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
            re.compile(r"ghp_[A-Za-z0-9]{20,}"),
            re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
            re.compile(r"AKIA[0-9A-Z]{16}"),
            re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
            re.compile(
                r"\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*"
                r"[\"'][A-Za-z0-9][A-Za-z0-9._-]{15,}[\"']",
                re.I,
            ),
            re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.I),
        )
        for path in repository_text_files():
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(private_user_path.search(text), path)
            self.assertIsNone(installation_role.search(text), path)
            self.assertIsNone(labelled_installation_id.search(text), path)
            self.assertIsNone(labelled_rollout_id.search(text), path)
            self.assertIsNone(install_marker.search(text), path)
            self.assertIsNone(rollout_marker.search(text), path)
            self.assertIsNone(rollout_uuid.search(text), path)
            for pattern in secret_patterns:
                self.assertIsNone(pattern.search(text), path)

    def test_no_stale_hook_architecture_in_executable_layers(self):
        forbidden = (
            re.compile(r"\bPreToolUse\b", re.I),
            re.compile(r"\bSubagent(?:Start|Stop)\b", re.I),
            re.compile(r"managed[-_ ]?(?:child(?:ren)?|registry)", re.I),
            re.compile(r"\bhooks?\.json\b", re.I),
            re.compile(r"\bHook[_ -]?Router\b", re.I),
            re.compile(r"\bHook[_ -]?Trust\b", re.I),
            re.compile(r"\bspawn[_ -]?model(?:[_ -]?rewrite)?\b", re.I),
            re.compile(r"\bmodel[_ -]?rewrite\b", re.I),
            re.compile(
                r"\bdefault_subagent_(?:model|reasoning_effort)\b", re.I
            ),
            re.compile(
                r"\bslr_[A-Za-z0-9][A-Za-z0-9-]*_"
                r"(?:low|medium|high|xhigh|max)\b",
                re.I,
            ),
            re.compile(r"\bv3\.2\.1\b[^\n]*(?:hook|enforcement)", re.I),
            re.compile(r"\b(?:hook|enforcement)[^\n]*\bv3\.2\.1\b", re.I),
        )
        for path in executable_repository_text_files():
            text = path.read_text(encoding="utf-8")
            for pattern in forbidden:
                self.assertIsNone(pattern.search(text), path)

    def test_historical_architecture_mentions_are_not_treated_as_current_code(self):
        historical_docs = {
            ROOT / "ARCHITECTURE.md",
            ROOT / "CHANGELOG.md",
            ROOT / "README.md",
            ROOT / "README.zh-CN.md",
            ROOT / "RUNTIME_TESTS.md",
        }
        self.assertTrue(any("Hook" in path.read_text(encoding="utf-8") for path in historical_docs))
        self.assertFalse(
            any(path in set(executable_repository_text_files()) for path in historical_docs)
        )

    def test_runtime_state_and_core_codex_files_have_correct_gitignore_boundary(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".var/", ignore)
        self.assertNotIn(".codex/\n", ignore)
        self.assertNotIn(".codex/agents/", ignore)


if __name__ == "__main__":
    unittest.main()
