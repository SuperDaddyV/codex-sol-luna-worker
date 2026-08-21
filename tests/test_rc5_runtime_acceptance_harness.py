import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "scripts" / "accept_rc5_runtime_isolation.py"
SPEC = importlib.util.spec_from_file_location("rc5_runtime_harness", HARNESS_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load RC5 runtime acceptance harness")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)
SYNTHETIC_VISUALIZATION_RUN_ID = "-".join(
    ("11111111", "2222", "4333", "8444", "555555555555")
)


class Rc5RuntimeAcceptanceHarnessTests(unittest.TestCase):
    def _make_real_home_fixture(self, root: Path) -> Path:
        real_home = root / "real"
        (real_home / "agents").mkdir(parents=True)
        (real_home / "sol-luna-v4" / "state").mkdir(parents=True)
        (real_home / "backups" / "sol-luna-v4").mkdir(parents=True)
        (real_home / "AGENTS.md").write_bytes(b"protected policy\n")
        (real_home / "config.toml").write_bytes(b"[agents]\n")
        for role in ("low", "medium", "high", "xhigh", "max"):
            (real_home / "agents" / f"luna-{role}.toml").write_bytes(
                b"[agents]\nenabled = false\n"
            )
        (real_home / "sol-luna-v4" / "selector.py").write_bytes(
            b"protected selector\n"
        )
        (real_home / "sol-luna-v4" / "install-manifest.json").write_bytes(
            b"{}\n"
        )
        (real_home / "sol-luna-v4" / "state" / "daily-profile.json").write_bytes(
            b"{}\n"
        )
        (real_home / "sol-luna-v4" / "state" / "last-good-profile.json").write_bytes(
            b"{}\n"
        )
        (real_home / "sol-luna-v4" / "state" / "selector.lock").write_bytes(
            b"lock\n"
        )
        (real_home / "sol-luna-v4" / "state" / "other-state.bin").write_bytes(
            b"other state\n"
        )
        (real_home / "backups" / "sol-luna-v4" / "metadata.json").write_bytes(
            b"{}\n"
        )
        (real_home / "auth.json").write_bytes(b'{"fixture":"auth"}\n')
        return real_home

    def _make_isolated_home_fixture(self, root: Path) -> tuple[Path, Path]:
        real_home = self._make_real_home_fixture(root)
        fake_home = root / "fake"
        shutil.copytree(real_home, fake_home)
        return real_home, fake_home

    def _create_junction(self, link: Path, target: Path) -> None:
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            self.skipTest(f"junction creation is unavailable: {completed.stderr}")

    def test_codex_environment_is_isolated_and_drops_unrelated_secrets(self):
        fake_home = Path("isolated-home")
        environment = HARNESS._codex_environment(
            fake_home,
            {
                "Path": "safe-path",
                "SystemRoot": "safe-system-root",
                "HOME": "private-home",
                "USERPROFILE": "private-profile",
                "XDG_RUNTIME_DIR": "host-runtime-dir",
                "OPENAI_API_KEY": "secret-value",
                "GITHUB_TOKEN": "secret-value",
                "API_KEY": "secret-value",
            },
        )

        self.assertEqual(environment["PATH"], "safe-path")
        self.assertEqual(environment["SYSTEMROOT"], "safe-system-root")
        self.assertEqual(environment["HOME"], str(fake_home))
        self.assertEqual(environment["USERPROFILE"], str(fake_home))
        self.assertEqual(environment["CODEX_HOME"], str(fake_home))
        self.assertEqual(
            environment["TEMP"],
            str(fake_home / "runtime-environment" / "temp"),
        )
        for name in (
            "APPDATA",
            "LOCALAPPDATA",
            "TEMP",
            "TMP",
            "TMPDIR",
            "XDG_CACHE_HOME",
            "XDG_CONFIG_HOME",
            "XDG_DATA_HOME",
            "XDG_RUNTIME_DIR",
            "XDG_STATE_HOME",
        ):
            self.assertTrue(Path(environment[name]).is_relative_to(fake_home))
        for forbidden in ("OPENAI_API_KEY", "GITHUB_TOKEN", "API_KEY"):
            self.assertNotIn(forbidden, environment)

    def test_o4_selector_uses_isolated_env(self):
        isolated_runtime_env = {
            "CODEX_HOME": "isolated-home",
            "HOME": "isolated-home",
            "PATH": "safe-path",
        }
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="{}", stderr=""
        )

        with mock.patch.object(HARNESS, "_run", return_value=completed) as runner:
            HARNESS._ensure_selection(
                "python",
                Path("isolated-home/sol-luna-v4/selector.py"),
                Path("snapshot.json"),
                Path("acceptance-state/o4"),
                isolated_runtime_env=isolated_runtime_env,
                supported="high,medium,low",
            )

        runner.assert_called_once()
        self.assertIs(runner.call_args.kwargs["env"], isolated_runtime_env)

    def test_real_home_identity_excludes_mutable_directory_link_count(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(
                HARNESS, "_file_identity", return_value=(11, 22, 33)
            ):
                identity = HARNESS._plain_real_home_identity(
                    Path(temporary)
                )

        self.assertEqual(identity, (11, 22))

    def test_unknown_snapshot_excludes_mutable_ancestor_link_count(self):
        inventory = {
            "entries": {
                ".": {
                    "type": "directory",
                    "size": 1,
                    "mtime_ns": 2,
                    "device": 3,
                    "file_id": 4,
                    "link_count": 5,
                }
            }
        }
        with mock.patch.object(HARNESS, "_inventory_tree", return_value=inventory):
            snapshot = HARNESS._unexpected_write_snapshot(Path("runtime-home"))

        root = snapshot["entries"]["."]
        self.assertEqual(root["type"], "directory")
        self.assertEqual(root["device"], 3)
        self.assertEqual(root["file_id"], 4)
        self.assertNotIn("size", root)
        self.assertNotIn("mtime_ns", root)
        self.assertNotIn("link_count", root)

    def test_only_macos_var_is_an_allowed_platform_root_alias(self):
        with mock.patch.object(HARNESS.sys, "platform", "darwin"):
            with mock.patch.object(
                Path, "resolve", return_value=Path("/private/var")
            ):
                self.assertTrue(
                    HARNESS._is_allowed_platform_root_alias(Path("/var"))
                )
            with mock.patch.object(
                Path, "resolve", return_value=Path("/unexpected")
            ):
                self.assertFalse(
                    HARNESS._is_allowed_platform_root_alias(Path("/var"))
                )
            self.assertFalse(HARNESS._is_allowed_platform_root_alias(Path("/tmp")))
        with mock.patch.object(HARNESS.sys, "platform", "linux"):
            self.assertFalse(HARNESS._is_allowed_platform_root_alias(Path("/var")))

    def test_evidence_paths_are_symbolized_and_private_homes_are_redacted(self):
        private_fake = (
            "C:\\" + "Users" + r"\Private\AppData\Temp\run\codex-home"
        )
        private_unknown = (
            "C:\\" + "Users" + r"\Another User\secret folder\item.txt"
        )
        symbolic_values = {
            private_fake: "<FAKE_CODEX_HOME>",
            r"D:\private-repository": "<REPOSITORY_ROOT>",
        }
        evidence = {
            "root": private_fake,
            "nested": [r"D:\private-repository\scripts\accept.py"],
            "failure": f"failed beside {private_unknown}",
            "stderr": "Bearer " + "A" * 24 + " api_key=" + "B" * 24,
        }

        sanitized = HARNESS._sanitize_evidence(
            evidence, symbolic_values=symbolic_values
        )
        rendered = repr(sanitized)

        self.assertEqual(sanitized["root"], "<FAKE_CODEX_HOME>")
        self.assertEqual(
            sanitized["nested"], [r"<REPOSITORY_ROOT>\scripts\accept.py"]
        )
        self.assertIn("<PRIVATE_PATH>", sanitized["failure"])
        self.assertEqual(
            sanitized["stderr"], "<REDACTED_SECRET> <REDACTED_SECRET>"
        )
        self.assertNotIn("C:\\" + "Users", rendered)
        self.assertNotIn(r"D:\private-repository", rendered)

    def test_main_evidence_symbol_map_covers_runtime_and_executable_paths(self):
        base = Path.cwd().resolve()
        root = base / "acceptance"
        real_home = base / "real-home"
        repo_root = base / "repository"
        codex_command = base / "bin" / "codex"
        python_command = base / "bin" / "python"
        values = HARNESS._evidence_symbolic_values(
            fake_home=root / "fake-home",
            acceptance_root=root,
            real_home=real_home,
            repo_root=repo_root,
            temp_parent=base,
            codex_command=str(codex_command),
            python_command=str(python_command),
        )

        self.assertEqual(values[str(root / "fake-home")], "<FAKE_CODEX_HOME>")
        self.assertEqual(values[str(root)], "<ACCEPTANCE_ROOT>")
        self.assertEqual(values[str(real_home)], "<REAL_CODEX_HOME>")
        self.assertEqual(values[str(repo_root)], "<REPOSITORY_ROOT>")
        self.assertEqual(values[str(base)], "<TEMP_PARENT>")
        self.assertEqual(values[str(codex_command)], "<CODEX_COMMAND>")
        self.assertEqual(values[str(python_command)], "<PYTHON_COMMAND>")

    def test_source_attribution_requires_fixed_installed_commit(self):
        expected = HARNESS.RC5_SOURCE_COMMIT
        self.assertEqual(
            HARNESS._source_attribution(expected),
            {"installed": expected, "expected": expected, "match": "YES"},
        )
        self.assertEqual(
            HARNESS._source_attribution("0" * 40)["match"],
            "NO",
        )

        with tempfile.TemporaryDirectory() as temporary:
            fake_home = Path(temporary)
            manifest = fake_home / "sol-luna-v4" / "install-manifest.json"
            manifest.parent.mkdir()
            manifest.write_text(
                json.dumps({"source_commit": expected}), encoding="utf-8"
            )
            installed = HARNESS._read_installed_source_commit(fake_home)
            self.assertEqual(installed, expected)
            self.assertEqual(HARNESS._source_attribution(installed)["match"], "YES")

            manifest.write_text(
                json.dumps({"source_commit": "0" * 40}), encoding="utf-8"
            )
            installed = HARNESS._read_installed_source_commit(fake_home)
            self.assertEqual(HARNESS._source_attribution(installed)["match"], "NO")

    def test_auth_runtime_refresh_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            audits = {}
            auth_path = real_home / "auth.json"
            before_identity = HARNESS._file_identity(auth_path)[:2]

            def refresh_auth():
                replacement = real_home / "auth.json.refresh"
                replacement.write_bytes(b'{"fixture":"runtime-refresh"}\n')
                replacement.replace(auth_path)
                return "ok"

            result = HARNESS._run_with_real_home_audit(
                label="AUTH_REFRESH",
                real_home=real_home,
                audits=audits,
                action=refresh_auth,
            )

            self.assertEqual(result, "ok")
            self.assertNotEqual(before_identity, HARNESS._file_identity(auth_path)[:2])
            self.assertTrue(audits["AUTH_REFRESH"]["protected_state_unchanged"])
            self.assertEqual(
                audits["AUTH_REFRESH"]["real_home_runtime_attribution"],
                "NOT_USED",
            )
            self.assertIsNone(audits["AUTH_REFRESH"]["auth_classification"])

    def test_session_jsonl_activity_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            audits = {}

            def write_session_jsonl():
                session_path = real_home / "sessions" / "2026" / "08" / "20.jsonl"
                session_path.parent.mkdir(parents=True)
                session_path.write_text('{"type":"session_meta"}\n', encoding="utf-8")

            HARNESS._run_with_real_home_audit(
                label="SESSION_JSONL",
                real_home=real_home,
                audits=audits,
                action=write_session_jsonl,
            )

            self.assertEqual(
                audits["SESSION_JSONL"]["real_home_runtime_attribution"],
                "NOT_USED",
            )
            self.assertEqual(audits["SESSION_JSONL"]["activity_categories"], [])

    def test_sqlite_wal_activity_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            (real_home / "state_5.sqlite").write_bytes(b"base\n")
            wal_path = real_home / "state_5.sqlite-wal"
            wal_path.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="SQLITE_WAL",
                real_home=real_home,
                audits=audits,
                action=lambda: wal_path.write_bytes(b"after\n"),
            )

            self.assertEqual(
                audits["SQLITE_WAL"]["real_home_runtime_attribution"],
                "NOT_USED",
            )

    def test_sqlite_shm_activity_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            (real_home / "state_5.sqlite").write_bytes(b"base\n")
            shm_path = real_home / "state_5.sqlite-shm"
            shm_path.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="SQLITE_SHM",
                real_home=real_home,
                audits=audits,
                action=lambda: shm_path.write_bytes(b"after\n"),
            )

            self.assertEqual(
                audits["SQLITE_SHM"]["real_home_runtime_attribution"],
                "NOT_USED",
            )

    def test_sqlite_db_activity_is_not_a_real_home_attribution_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            database_path = real_home / "sqlite" / "codex-dev.db"
            database_path.parent.mkdir()
            database_path.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="SQLITE_DB",
                real_home=real_home,
                audits=audits,
                action=lambda: database_path.write_bytes(b"after\n"),
            )

            self.assertEqual(
                audits["SQLITE_DB"]["real_home_runtime_attribution"],
                "NOT_USED",
            )
            self.assertFalse(HARNESS._is_local_storage_path("unexpected.db"))
            self.assertFalse(HARNESS._is_local_storage_path("sqlite/random.db"))
            self.assertFalse(
                HARNESS._is_local_storage_path("sqlite/unexpected.txt")
            )

    def test_new_arbitrary_codex_db_is_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            candidate = real_home / "sqlite" / "codex-evil.db"
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="NEW_ARBITRARY_CODEX_DB",
                real_home=real_home,
                audits=audits,
                action=lambda: (
                    candidate.parent.mkdir(),
                    candidate.write_bytes(b"unexpected\n"),
                ),
            )

            self.assertEqual(
                HARNESS._runtime_path_category("sqlite/codex-evil.db"),
                HARNESS.UNKNOWN,
            )
            self.assertEqual(
                audits["NEW_ARBITRARY_CODEX_DB"]["unexpected_changed_paths"], []
            )

    def test_baseline_existing_codex_db_mutation_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            database_path = real_home / "sqlite" / "codex-existing.db"
            database_path.parent.mkdir()
            database_path.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="BASELINE_CODEX_DB_MUTATION",
                real_home=real_home,
                audits=audits,
                action=lambda: database_path.write_bytes(b"after\n"),
            )

            self.assertEqual(
                audits["BASELINE_CODEX_DB_MUTATION"]["real_home_runtime_attribution"],
                "NOT_USED",
            )

    def test_baseline_codex_db_safe_regular_file_replacement_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            database_path = real_home / "sqlite" / "codex-existing.db"
            database_path.parent.mkdir()
            database_path.write_bytes(b"before\n")
            replacement = root / "replacement.db"
            replacement.write_bytes(b"after replacement\n")
            before_identity = HARNESS._file_identity(database_path)[:2]
            replacement_identity = HARNESS._file_identity(replacement)[:2]
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="BASELINE_CODEX_DB_SAFE_REPLACEMENT",
                real_home=real_home,
                audits=audits,
                action=lambda: os.replace(replacement, database_path),
            )

            self.assertNotEqual(before_identity, replacement_identity)
            self.assertEqual(
                HARNESS._file_identity(database_path)[:2], replacement_identity
            )
            self.assertEqual(
                audits["BASELINE_CODEX_DB_SAFE_REPLACEMENT"][
                    "real_home_runtime_attribution"
                ],
                "NOT_USED",
            )

    def test_observed_runtime_path_classification_contract_is_total(self):
        approved = frozenset()
        observability = HARNESS._runtime_observability_metadata()
        self.assertEqual(
            observability["OBSERVED_RUNTIME_PATH_CLASSIFICATION_TOTAL"], "YES"
        )
        self.assertEqual(
            observability["runtime_path_classification_scope"],
            "OBSERVED_SNAPSHOT_CHANGES_ONLY",
        )
        self.assertEqual(
            observability["unknown_fail_closed_scope"],
            "OBSERVED_UNKNOWN_SNAPSHOT_CHANGES_ONLY",
        )
        self.assertEqual(
            observability["FULL_TRANSIENT_FILESYSTEM_EVENT_CAPTURE"],
            "OUT_OF_SCOPE",
        )
        cases = {
            "sol-luna-v4/state/daily-profile.json": HARNESS.PROTECTED_SOL_LUNA_STATE,
            "sessions/2026/example.jsonl": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "session_index.jsonl": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "cache/codex_apps_tools/tools.json": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "node_repl/active_execs/exec.json": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "browser/sessions/2026/example.jsonl": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "cache/remote_plugin_catalog/catalog.json": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "plugins/cache": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "plugins/cache/marketplace/plugin/1.0.0/state.json": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "tmp/arg0/command.log": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            f"visualizations/2026/08/20/{SYNTHETIC_VISUALIZATION_RUN_ID}/frame.png": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "goals_1.sqlite": HARNESS.CODEX_LOCAL_STORAGE_STATE,
            "logs_2.sqlite": HARNESS.CODEX_LOCAL_STORAGE_STATE,
            "memories_3.sqlite": HARNESS.CODEX_LOCAL_STORAGE_STATE,
            "queue_4.sqlite": HARNESS.CODEX_LOCAL_STORAGE_STATE,
            "state_5.sqlite": HARNESS.CODEX_LOCAL_STORAGE_STATE,
            "sqlite/goals_1.sqlite": HARNESS.CODEX_LOCAL_STORAGE_STATE,
            "plugins/evil/state.json": HARNESS.UNKNOWN,
            "plugins/data/state.json": HARNESS.UNKNOWN,
            "plugins-other/state.json": HARNESS.UNKNOWN,
            "sqlite/codex-evil.db": HARNESS.UNKNOWN,
            "browser/other.json": HARNESS.UNKNOWN,
            "cache/other.json": HARNESS.UNKNOWN,
            "tmp/other.json": HARNESS.UNKNOWN,
            "visualizations/other/frame.png": HARNESS.UNKNOWN,
        }
        valid_categories = {
            HARNESS.PROTECTED_SOL_LUNA_STATE,
            HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            HARNESS.CODEX_LOCAL_STORAGE_STATE,
            HARNESS.UNKNOWN,
        }

        for relative, expected in cases.items():
            with self.subTest(relative=relative):
                category = HARNESS._runtime_path_category(relative, approved)
                self.assertIn(category, valid_categories)
                self.assertEqual(category, expected)

        with mock.patch.object(
            HARNESS, "_is_protected_runtime_path", return_value=True
        ), mock.patch.object(HARNESS, "_is_session_runtime_path", return_value=True):
            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "multiple categories"
            ):
                HARNESS._runtime_path_category("overlapping/path")

    def test_new_codex_db_wal_is_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            candidate = real_home / "sqlite" / "codex-evil.db-wal"
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="NEW_CODEX_DB_WAL",
                real_home=real_home,
                audits=audits,
                action=lambda: (
                    candidate.parent.mkdir(),
                    candidate.write_bytes(b"unexpected wal\n"),
                ),
            )

            self.assertEqual(
                audits["NEW_CODEX_DB_WAL"]["unexpected_changed_paths"], []
            )

    def test_new_codex_db_shm_is_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            candidate = real_home / "sqlite" / "codex-evil.db-shm"
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="NEW_CODEX_DB_SHM",
                real_home=real_home,
                audits=audits,
                action=lambda: (
                    candidate.parent.mkdir(),
                    candidate.write_bytes(b"unexpected shm\n"),
                ),
            )

            self.assertEqual(
                audits["NEW_CODEX_DB_SHM"]["unexpected_changed_paths"], []
            )

    def test_sqlite_sidecars_require_one_of_the_named_root_bases(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            database_path = real_home / "goals-1.sqlite"
            database_path.write_bytes(b"before\n")
            self.assertFalse(HARNESS._is_local_storage_path(database_path.name))
            database_path = real_home / "goals_1.sqlite"
            database_path.write_bytes(b"before\n")
            audits = {}

            def create_sidecars():
                (database_path.with_name("goals_1.sqlite-wal")).write_bytes(
                    b"wal\n"
                )
                (database_path.with_name("goals_1.sqlite-shm")).write_bytes(
                    b"shm\n"
                )

            HARNESS._run_with_real_home_audit(
                label="SQLITE_ROOT_SIDECARS",
                real_home=real_home,
                audits=audits,
                action=create_sidecars,
            )

            approved = frozenset()
            self.assertTrue(
                HARNESS._is_local_storage_path(
                    "goals_1.sqlite-wal", approved
                )
            )
            self.assertFalse(
                HARNESS._is_valid_sqlite_entry(
                    "goals_2.sqlite-wal",
                    {"type": "file", "reparse": False, "link_count": 1},
                    {},
                )
            )
            self.assertEqual(
                HARNESS._runtime_path_category("goals_2.sqlite-wal"),
                HARNESS.CODEX_LOCAL_STORAGE_STATE,
            )
            self.assertEqual(
                audits["SQLITE_ROOT_SIDECARS"]["real_home_runtime_attribution"],
                "NOT_USED",
            )

    def test_baseline_codex_db_replaced_by_directory_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            database_path = fake_home / "goals_1.sqlite"
            database_path.write_bytes(b"before\n")
            audits = {}

            def replace_with_directory():
                database_path.unlink()
                database_path.mkdir()

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "isolated CODEX_HOME runtime state is invalid"
            ):
                HARNESS._run_with_real_home_audit(
                    label="BASELINE_CODEX_DB_DIRECTORY",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=replace_with_directory,
                )

            self.assertIn(
                "goals_1.sqlite",
                audits["BASELINE_CODEX_DB_DIRECTORY"]["isolated_home"][
                    "changed_paths"
                ],
            )

    def test_baseline_codex_db_replaced_by_symlink_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home, fake_home = self._make_isolated_home_fixture(root)
            database_path = fake_home / "goals_1.sqlite"
            database_path.write_bytes(b"before\n")
            external = root / "external.db"
            external.write_bytes(b"external\n")
            probe_target = root / "probe-target"
            probe_link = root / "probe-link"
            probe_target.write_bytes(b"probe\n")
            try:
                probe_link.symlink_to(probe_target)
            except OSError as exc:
                self.skipTest(f"file symlink creation is unavailable: {exc}")
            finally:
                if os.path.lexists(probe_link):
                    probe_link.unlink()
            audits = {}

            def replace_with_symlink():
                database_path.unlink()
                database_path.symlink_to(external)

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "isolated CODEX_HOME runtime state is invalid"
            ):
                HARNESS._run_with_real_home_audit(
                    label="BASELINE_CODEX_DB_SYMLINK",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=replace_with_symlink,
                )

            self.assertIn(
                "goals_1.sqlite",
                audits["BASELINE_CODEX_DB_SYMLINK"]["isolated_home"][
                    "changed_paths"
                ],
            )

    def test_baseline_codex_db_replaced_by_hardlink_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home, fake_home = self._make_isolated_home_fixture(root)
            database_path = fake_home / "goals_1.sqlite"
            database_path.write_bytes(b"before\n")
            external = root / "external.db"
            external.write_bytes(b"external\n")
            probe = root / "probe-hardlink"
            try:
                os.link(external, probe)
            except OSError as exc:
                self.skipTest(f"hardlink creation is unavailable: {exc}")
            finally:
                if os.path.lexists(probe):
                    probe.unlink()
            audits = {}

            def replace_with_hardlink():
                database_path.unlink()
                os.link(external, database_path)

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "isolated CODEX_HOME runtime state is invalid"
            ):
                HARNESS._run_with_real_home_audit(
                    label="BASELINE_CODEX_DB_HARDLINK",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=replace_with_hardlink,
                )

            self.assertIn(
                "goals_1.sqlite",
                audits["BASELINE_CODEX_DB_HARDLINK"]["isolated_home"][
                    "changed_paths"
                ],
            )

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_baseline_codex_db_replaced_by_junction_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home, fake_home = self._make_isolated_home_fixture(root)
            database_path = fake_home / "goals_1.sqlite"
            database_path.write_bytes(b"before\n")
            external = root / "external-directory"
            external.mkdir()
            probe = root / "probe-junction"
            completed = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(probe), str(external)],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                self.skipTest(f"junction creation is unavailable: {completed.stderr}")
            if os.path.lexists(probe):
                os.rmdir(probe)
            audits = {}

            def replace_with_junction():
                database_path.unlink()
                completed = subprocess.run(
                    [
                        "cmd",
                        "/c",
                        "mklink",
                        "/J",
                        str(database_path),
                        str(external),
                    ],
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    check=False,
                )
                if completed.returncode != 0:
                    raise RuntimeError(completed.stderr)

            try:
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure,
                    "isolated CODEX_HOME runtime state is invalid",
                ):
                    HARNESS._run_with_real_home_audit(
                        label="BASELINE_CODEX_DB_JUNCTION",
                        real_home=real_home,
                        audits=audits,
                        isolated_home=fake_home,
                        action=replace_with_junction,
                    )
            finally:
                if os.path.lexists(database_path):
                    os.rmdir(database_path)

            self.assertIn(
                "goals_1.sqlite",
                audits["BASELINE_CODEX_DB_JUNCTION"]["isolated_home"][
                    "changed_paths"
                ],
            )

    def test_valid_state_sqlite_family_activity_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            audits = {}

            def create_sqlite_family():
                root_base = real_home / "state_5.sqlite"
                root_base.write_bytes(b"base\n")
                (real_home / "state_5.sqlite-wal").write_bytes(b"wal\n")
                (real_home / "state_5.sqlite-shm").write_bytes(b"shm\n")

            HARNESS._run_with_real_home_audit(
                label="SQLITE_FAMILY_CREATE",
                real_home=real_home,
                audits=audits,
                action=create_sqlite_family,
            )

            self.assertEqual(
                audits["SQLITE_FAMILY_CREATE"]["real_home_runtime_attribution"],
                "NOT_USED",
            )

    def test_arbitrary_root_sqlite_is_unknown(self):
        for relative in ("evil.sqlite", "random.db"):
            with (
                self.subTest(relative=relative),
                tempfile.TemporaryDirectory() as temporary,
            ):
                real_home = self._make_real_home_fixture(Path(temporary))
                candidate = real_home / relative
                audits = {}

                HARNESS._run_with_real_home_audit(
                    label="ARBITRARY_ROOT_SQLITE",
                    real_home=real_home,
                    audits=audits,
                    action=lambda: candidate.write_bytes(b"unexpected\n"),
                )

                self.assertEqual(
                    audits["ARBITRARY_ROOT_SQLITE"]["unexpected_changed_paths"], []
                )

    def test_arbitrary_sqlite_wal_and_shm_are_unknown(self):
        for relative in ("evil.sqlite-wal", "evil.sqlite-shm"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                real_home = self._make_real_home_fixture(Path(temporary))
                candidate = real_home / relative
                audits = {}

                def create_candidate():
                    candidate.parent.mkdir(parents=True, exist_ok=True)
                    candidate.write_bytes(b"unexpected\n")

                HARNESS._run_with_real_home_audit(
                    label="ARBITRARY_SQLITE_SIDECAR",
                    real_home=real_home,
                    audits=audits,
                    action=create_candidate,
                )
                self.assertEqual(
                    audits["ARBITRARY_SQLITE_SIDECAR"]["unexpected_changed_paths"],
                    [],
                )

    def test_valid_sqlite_validated_family_activity_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            audits = {}
            bases = (
                "goals_1.sqlite",
                "logs_2.sqlite",
                "memories_1.sqlite",
                "queue_4.sqlite",
                "state_5.sqlite",
            )

            def create_sqlite_family():
                for name in bases:
                    (real_home / name).write_bytes(b"base\n")
                    (real_home / f"{name}-wal").write_bytes(b"wal\n")
                    (real_home / f"{name}-shm").write_bytes(b"shm\n")

            HARNESS._run_with_real_home_audit(
                label="SQLITE_VALIDATED_FAMILY",
                real_home=real_home,
                audits=audits,
                action=create_sqlite_family,
            )

            self.assertEqual(
                audits["SQLITE_VALIDATED_FAMILY"]["real_home_runtime_attribution"],
                "NOT_USED",
            )

    def test_allowed_volatile_storage_is_not_content_hashed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            (real_home / "state_5.sqlite").write_bytes(b"base\n")
            database_path = real_home / "state_5.sqlite-wal"
            database_path.write_bytes(b"before\n")
            audits = {}
            real_sha256_file = HARNESS._sha256_file

            def reject_database_hash(path):
                if path == database_path:
                    raise AssertionError("allowed volatile storage was hashed")
                return real_sha256_file(path)

            with mock.patch.object(
                HARNESS, "_sha256_file", side_effect=reject_database_hash
            ):
                HARNESS._run_with_real_home_audit(
                    label="VOLATILE_STORAGE",
                    real_home=real_home,
                    audits=audits,
                    action=lambda: database_path.write_bytes(b"after\n"),
                )

            self.assertEqual(
                audits["VOLATILE_STORAGE"]["real_home_runtime_attribution"],
                "NOT_USED",
            )
            self.assertTrue(
                audits["VOLATILE_STORAGE"]["protected_state_unchanged"]
            )

    def test_codex_platform_runtime_cache_activity_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            cache_path = (
                real_home
                / "cache"
                / "codex_apps_tools"
                / "runtime-cache.json"
            )
            cache_path.parent.mkdir(parents=True)
            cache_path.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="PLATFORM_CACHE",
                real_home=real_home,
                audits=audits,
                action=lambda: cache_path.write_bytes(b"after\n"),
            )

            self.assertEqual(
                audits["PLATFORM_CACHE"]["real_home_runtime_attribution"],
                "NOT_USED",
            )
            self.assertFalse(
                HARNESS._is_session_runtime_path("cache/unexpected.json")
            )

    def test_node_repl_active_exec_activity_allowed_without_allowing_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            active_exec = real_home / "node_repl" / "active_execs" / "one.json"
            active_exec.parent.mkdir(parents=True)
            active_exec.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="NODE_REPL_ACTIVE_EXEC",
                real_home=real_home,
                audits=audits,
                action=lambda: active_exec.write_bytes(b"after\n"),
            )

            self.assertEqual(
                audits["NODE_REPL_ACTIVE_EXEC"]["real_home_runtime_attribution"],
                "NOT_USED",
            )
            self.assertFalse(
                HARNESS._is_session_runtime_path("node_repl/unexpected.json")
            )

    def test_plugin_cache_remote_curated_activity_is_platform_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            plugin_state = (
                real_home
                / "plugins"
                / "cache"
                / "openai-curated-remote"
                / "finances"
                / "0.1.0"
                / "runtime-state.json"
            )
            plugin_state.parent.mkdir(parents=True)
            plugin_state.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="REMOTE_CURATED_PLUGIN_CACHE",
                real_home=real_home,
                audits=audits,
                action=lambda: plugin_state.write_bytes(b"after plugin state\n"),
            )

            self.assertEqual(
                audits["REMOTE_CURATED_PLUGIN_CACHE"][
                    "real_home_runtime_attribution"
                ],
                "NOT_USED",
            )
            self.assertEqual(
                HARNESS._runtime_path_category(
                    "plugins/cache/openai-curated-remote/finances/0.1.0/runtime-state.json"
                ),
                HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            )

    def test_plugin_cache_can_be_created_on_first_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            plugin_state = (
                real_home
                / "plugins"
                / "cache"
                / "community"
                / "sample-plugin"
                / "0.2.0"
                / "runtime-state.json"
            )
            audits = {}

            def create_plugin_cache_state():
                plugin_state.parent.mkdir(parents=True)
                plugin_state.write_bytes(b"created\n")

            HARNESS._run_with_real_home_audit(
                label="PLUGIN_CACHE_FIRST_USE",
                real_home=real_home,
                audits=audits,
                action=create_plugin_cache_state,
            )

            self.assertEqual(
                audits["PLUGIN_CACHE_FIRST_USE"]["real_home_runtime_attribution"],
                "NOT_USED",
            )

    def test_plugin_cache_observed_create_and_delete_are_classified(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            plugin_state = (
                real_home
                / "plugins"
                / "cache"
                / "community"
                / "sample-plugin"
                / "0.2.0"
                / "observed.json"
            )
            audits = {}
            observed_path = plugin_state.relative_to(real_home).as_posix()

            def create_plugin_cache_state():
                plugin_state.parent.mkdir(parents=True)
                plugin_state.write_bytes(b"created\n")

            HARNESS._run_with_real_home_audit(
                label="PLUGIN_CACHE_OBSERVED_CREATE",
                real_home=real_home,
                audits=audits,
                action=create_plugin_cache_state,
            )

            self.assertEqual(
                audits["PLUGIN_CACHE_OBSERVED_CREATE"][
                    "real_home_runtime_attribution"
                ],
                "NOT_USED",
            )
            self.assertEqual(
                HARNESS._runtime_path_category(observed_path),
                HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            )
            self.assertEqual(
                audits["PLUGIN_CACHE_OBSERVED_CREATE"]["observability"][
                    "activity_observation_scope"
                ],
                HARNESS.OBSERVED_RUNTIME_ACTIVITY,
            )

            def delete_plugin_cache_state():
                plugin_state.unlink()
                current = plugin_state.parent
                while current != real_home:
                    current.rmdir()
                    current = current.parent

            HARNESS._run_with_real_home_audit(
                label="PLUGIN_CACHE_OBSERVED_DELETE",
                real_home=real_home,
                audits=audits,
                action=delete_plugin_cache_state,
            )
            self.assertEqual(
                audits["PLUGIN_CACHE_OBSERVED_DELETE"][
                    "real_home_runtime_attribution"
                ],
                "NOT_USED",
            )
            self.assertEqual(
                audits["PLUGIN_CACHE_OBSERVED_DELETE"]["activity_categories"], []
            )
            self.assertEqual(
                HARNESS._runtime_path_category(observed_path),
                HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            )

    def test_fully_ephemeral_plugin_cache_activity_is_not_claimed_as_observed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            plugin_state = (
                real_home
                / "plugins"
                / "cache"
                / "example"
                / "plugin"
                / "1.0"
                / "file"
            )
            audits = {}
            before_runtime = HARNESS._session_runtime_snapshot(real_home)

            def create_delete_and_cleanup():
                plugin_state.parent.mkdir(parents=True)
                plugin_state.write_bytes(b"transient\n")
                plugin_state.unlink()
                current = plugin_state.parent
                while current != real_home:
                    current.rmdir()
                    current = current.parent

            HARNESS._run_with_real_home_audit(
                label="FULLY_EPHEMERAL_PLUGIN_CACHE",
                real_home=real_home,
                audits=audits,
                action=create_delete_and_cleanup,
            )
            after_runtime = HARNESS._session_runtime_snapshot(real_home)
            changed_runtime_paths = HARNESS._changed_entry_paths(
                before_runtime, after_runtime
            )

            audit = audits["FULLY_EPHEMERAL_PLUGIN_CACHE"]
            self.assertIsNone(audit["activity_category"])
            self.assertEqual(audit["activity_categories"], [])
            self.assertFalse(audit["session_runtime_activity"])
            self.assertEqual(changed_runtime_paths, [])
            self.assertEqual(audit["before"], audit["after"])
            self.assertNotIn(HARNESS.SESSION_RUNTIME_ACTIVITY, repr(audit))
            self.assertNotIn(HARNESS.CODEX_PLATFORM_RUNTIME_STATE, repr(audit))
            self.assertEqual(
                audit["observability"]["UNOBSERVED_TRANSIENT_ACTIVITY_CLAIM"],
                "NO",
            )

    def test_other_marketplace_plugin_cache_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            plugin_state = (
                real_home
                / "plugins"
                / "cache"
                / "another-marketplace"
                / "another-plugin"
                / "9.9.9"
                / "state.bin"
            )
            plugin_state.parent.mkdir(parents=True)
            plugin_state.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="ANOTHER_MARKETPLACE_PLUGIN_CACHE",
                real_home=real_home,
                audits=audits,
                action=lambda: plugin_state.write_bytes(b"after plugin state\n"),
            )

            self.assertEqual(
                audits["ANOTHER_MARKETPLACE_PLUGIN_CACHE"][
                    "real_home_runtime_attribution"
                ],
                "NOT_USED",
            )

    def _assert_unknown_plugin_path_fails_closed(self, relative, label):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            candidate = fake_home / relative
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "isolated CODEX_HOME runtime state is invalid"
            ):
                def write_candidate():
                    candidate.parent.mkdir(parents=True, exist_ok=True)
                    candidate.write_bytes(b"after plugin state\n")

                HARNESS._run_with_real_home_audit(
                    label=label,
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=write_candidate,
                )

            self.assertEqual(
                audits[label]["isolated_home"]["runtime_state_valid"], False
            )
            self.assertEqual(
                HARNESS._runtime_path_category(relative), HARNESS.UNKNOWN
            )
            self.assertIn(relative, audits[label]["isolated_home"]["changed_paths"])

    def test_plugins_unknown_child_fails_closed(self):
        self._assert_unknown_plugin_path_fails_closed(
            "plugins/evil/state.json", "UNKNOWN_PLUGIN_CHILD"
        )

    def test_plugins_data_is_not_implicitly_allowed(self):
        self._assert_unknown_plugin_path_fails_closed(
            "plugins/data/state.json", "UNKNOWN_PLUGIN_DATA"
        )

    def test_plugins_other_root_is_not_plugin_cache(self):
        self._assert_unknown_plugin_path_fails_closed(
            "plugins-other/state.json", "UNKNOWN_PLUGINS_OTHER"
        )

    def test_plugin_cache_root_as_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            (real_home / "plugins").mkdir()
            (real_home / "plugins" / "cache").write_bytes(b"not a directory\n")

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "not an expected safe entry"
            ):
                HARNESS._session_runtime_snapshot(real_home)

    def test_plugins_root_as_symlink_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            external = root / "external-plugins"
            external.mkdir()
            try:
                (real_home / "plugins").symlink_to(external, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory symlink creation is unavailable: {exc}")

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unsafe object type or identity"
            ):
                HARNESS._session_runtime_snapshot(real_home)

    def test_plugin_cache_reparse_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            (real_home / "plugins").mkdir()
            external = root / "external-cache"
            external.mkdir()
            try:
                (real_home / "plugins" / "cache").symlink_to(
                    external, target_is_directory=True
                )
            except OSError as exc:
                self.skipTest(f"directory symlink creation is unavailable: {exc}")

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unsafe object type or identity"
            ):
                HARNESS._session_runtime_snapshot(real_home)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_plugin_cache_internal_junction_allowed(self):
        scenarios = (
            (
                "plugins/cache/example/plugin/version",
                "plugins/cache/target",
            ),
            (
                "plugins/cache/openai-bundled/chrome/latest",
                "plugins/cache/openai-bundled/chrome/1.0.0",
            ),
        )
        for relative, target_relative in scenarios:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    real_home = self._make_real_home_fixture(Path(temporary))
                    target = real_home / target_relative
                    target.mkdir(parents=True)
                    (target / "runtime-state.json").write_bytes(
                        b"internal target\n"
                    )
                    junction = real_home / relative
                    junction.parent.mkdir(parents=True, exist_ok=True)
                    self._create_junction(junction, target)
                    try:
                        snapshot = HARNESS._session_runtime_snapshot(real_home)
                        entry = snapshot["entries"][relative]
                        self.assertEqual(entry["type"], "reparse")
                        self.assertEqual(
                            HARNESS._runtime_path_category(relative),
                            HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
                        )
                        self.assertNotIn(
                            relative,
                            HARNESS._unexpected_write_snapshot(real_home)["entries"],
                        )
                    finally:
                        if os.path.lexists(junction):
                            os.rmdir(junction)

    def test_plugin_cache_internal_reparse_allowed_if_safe(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            target = (
                real_home
                / "plugins"
                / "cache"
                / "openai-bundled"
                / "chrome"
                / "1.0.0"
            )
            target.mkdir(parents=True)
            (target / "runtime-state.json").write_bytes(b"internal target\n")
            reparse = target.parent / "latest"
            try:
                reparse.symlink_to(target, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory reparse creation is unavailable: {exc}")
            try:
                snapshot = HARNESS._session_runtime_snapshot(real_home)
                entry = snapshot["entries"][
                    "plugins/cache/openai-bundled/chrome/latest"
                ]
                self.assertEqual(entry["type"], "reparse")
            finally:
                if os.path.lexists(reparse):
                    reparse.unlink()

    def test_plugin_cache_external_symlink_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            external = root / "random-external-folder"
            external.mkdir()
            reparse = real_home / "plugins" / "cache" / "evil"
            reparse.parent.mkdir(parents=True)
            try:
                reparse.symlink_to(external, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory reparse creation is unavailable: {exc}")
            try:
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "unsafe object type or identity"
                ):
                    HARNESS._session_runtime_snapshot(real_home)
            finally:
                if os.path.lexists(reparse):
                    reparse.unlink()

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_plugin_cache_junction_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            (real_home / "plugins").mkdir()
            external = root / "external-cache"
            external.mkdir()
            cache = real_home / "plugins" / "cache"
            completed = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(cache), str(external)],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            try:
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "unsafe object type or identity"
                ):
                    HARNESS._session_runtime_snapshot(real_home)
            finally:
                if os.path.lexists(cache):
                    os.rmdir(cache)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_plugin_cache_junction_to_protected_file_fails_closed(self):
        for protected_relative in ("AGENTS.md", "config.toml"):
            with self.subTest(protected_relative=protected_relative):
                with tempfile.TemporaryDirectory() as temporary:
                    real_home = self._make_real_home_fixture(Path(temporary))
                    protected_path = real_home / protected_relative
                    junction = real_home / "plugins" / "cache" / "evil"
                    junction.parent.mkdir(parents=True)
                    self._create_junction(junction, protected_path)
                    try:
                        with self.assertRaisesRegex(
                            HARNESS.HarnessFailure, "unsafe object type or identity"
                        ):
                            HARNESS._session_runtime_snapshot(real_home)
                    finally:
                        if os.path.lexists(junction):
                            os.rmdir(junction)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_plugin_cache_junction_inside_home_but_outside_cache_fails_closed(self):
        scenarios = ("sessions", "sol-luna-v4/state")
        for target_relative in scenarios:
            with self.subTest(target_relative=target_relative):
                with tempfile.TemporaryDirectory() as temporary:
                    real_home = self._make_real_home_fixture(Path(temporary))
                    target = real_home / target_relative
                    target.mkdir(parents=True, exist_ok=True)
                    junction = real_home / "plugins" / "cache" / "evil"
                    junction.parent.mkdir(parents=True)
                    self._create_junction(junction, target)
                    try:
                        with self.assertRaisesRegex(
                            HARNESS.HarnessFailure, "unsafe object type or identity"
                        ):
                            HARNESS._session_runtime_snapshot(real_home)
                    finally:
                        if os.path.lexists(junction):
                            os.rmdir(junction)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_plugin_cache_junction_outside_codex_home_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            external = root / "outside-codex-home"
            external.mkdir()
            junction = real_home / "plugins" / "cache" / "evil"
            junction.parent.mkdir(parents=True)
            self._create_junction(junction, external)
            try:
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "unsafe object type or identity"
                ):
                    HARNESS._session_runtime_snapshot(real_home)
            finally:
                if os.path.lexists(junction):
                    os.rmdir(junction)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_plugin_cache_junction_loop_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            loop_a = real_home / "plugins" / "cache" / "evil"
            loop_b = real_home / "plugins" / "cache" / "loop-b"
            loop_a.parent.mkdir(parents=True)
            try:
                self._create_junction(loop_a, loop_b)
                self._create_junction(loop_b, loop_a)
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "unsafe object type or identity"
                ):
                    HARNESS._session_runtime_snapshot(real_home)
            finally:
                for loop in (loop_a, loop_b):
                    if os.path.lexists(loop):
                        os.rmdir(loop)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_plugin_cache_junction_to_ancestor_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            cache = real_home / "plugins" / "cache"
            cache.mkdir(parents=True)
            loop = cache / "loop"
            self._create_junction(loop, cache)
            try:
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "unsafe object type or identity"
                ):
                    HARNESS._session_runtime_snapshot(real_home)
            finally:
                if os.path.lexists(loop):
                    os.rmdir(loop)

    def test_plugin_cache_path_escape_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            cache_root = fake_home / "plugins" / "cache"
            cache_root.mkdir(parents=True)
            escaped_path = cache_root / ".." / "evil" / "state.json"
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "isolated CODEX_HOME runtime state is invalid"
            ):
                def write_escape():
                    escaped_path.parent.mkdir(parents=True, exist_ok=True)
                    escaped_path.write_bytes(b"after\n")

                HARNESS._run_with_real_home_audit(
                    label="PLUGIN_CACHE_PATH_ESCAPE",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=write_escape,
                )

            normalized_relative = "plugins/evil/state.json"
            self.assertEqual(
                HARNESS._runtime_path_category(normalized_relative),
                HARNESS.UNKNOWN,
            )
            self.assertEqual(
                audits["PLUGIN_CACHE_PATH_ESCAPE"]["isolated_home"][
                    "runtime_state_valid"
                ],
                False,
            )

    def test_plugin_cache_external_hardlink_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            external = root / "external-plugin-state.json"
            external.write_bytes(b"external state\n")
            plugin_state = (
                real_home
                / "plugins"
                / "cache"
                / "community"
                / "sample-plugin"
                / "0.2.0"
                / "state.json"
            )
            plugin_state.parent.mkdir(parents=True)
            os.link(external, plugin_state)

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unsafe object type or identity"
            ):
                HARNESS._session_runtime_snapshot(real_home)

    def test_explicit_computer_use_local_storage_activity_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            config_path = real_home / "computer-use" / "config.json"
            config_path.parent.mkdir()
            config_path.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="COMPUTER_USE_CONFIG",
                real_home=real_home,
                audits=audits,
                action=lambda: config_path.write_bytes(b"after\n"),
            )

            self.assertEqual(
                audits["COMPUTER_USE_CONFIG"]["real_home_runtime_attribution"],
                "NOT_USED",
            )
            self.assertFalse(
                HARNESS._is_local_storage_path("computer-use/unexpected.json")
            )

    def test_valid_computer_use_config_initial_creation_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            config_path = real_home / "computer-use" / "config.json"
            audits = {}

            def create_config():
                config_path.parent.mkdir()
                config_path.write_bytes(b"created\n")

            HARNESS._run_with_real_home_audit(
                label="COMPUTER_USE_CONFIG_CREATE",
                real_home=real_home,
                audits=audits,
                action=create_config,
            )

            self.assertEqual(
                audits["COMPUTER_USE_CONFIG_CREATE"][
                    "real_home_runtime_attribution"
                ],
                "NOT_USED",
            )

    def test_unexpected_computer_use_child_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            child = fake_home / "computer-use" / "unexpected.json"
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "isolated CODEX_HOME runtime state is invalid"
            ):
                def write_child():
                    child.parent.mkdir(parents=True, exist_ok=True)
                    child.write_bytes(b"unexpected\n")

                HARNESS._run_with_real_home_audit(
                    label="COMPUTER_USE_CHILD",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=write_child,
                )

            self.assertIn(
                "computer-use/unexpected.json",
                audits["COMPUTER_USE_CHILD"]["isolated_home"]["changed_paths"],
            )

    def test_expected_runtime_file_replaced_by_directory_fails_closed(self):
        cases = (
            ("computer-use/config.json", HARNESS._local_storage_snapshot),
        )
        for relative, snapshotter in cases:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                real_home = self._make_real_home_fixture(Path(temporary))
                target = real_home / relative
                target.mkdir(parents=True)

                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "not an expected safe entry"
                ):
                    snapshotter(real_home)

    def test_expected_runtime_file_directory_children_are_not_hidden(self):
        cases = (
            "computer-use/config.json",
        )
        for relative in cases:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                real_home = self._make_real_home_fixture(Path(temporary))
                target = real_home / relative
                target.mkdir(parents=True)
                child = target / "arbitrary-child.json"
                child.write_bytes(b"hidden-child\n")

                unknown = HARNESS._unexpected_write_snapshot(real_home)
                self.assertIn(
                    f"{relative}/arbitrary-child.json",
                    unknown["entries"],
                )

    def test_memories_content_tree_activity_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            memory_path = real_home / "memories" / "entries" / "one.md"
            memory_path.parent.mkdir(parents=True)
            memory_path.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="MEMORIES_TREE",
                real_home=real_home,
                audits=audits,
                action=lambda: memory_path.write_bytes(b"after\n"),
            )

            self.assertEqual(
                audits["MEMORIES_TREE"]["real_home_runtime_attribution"],
                "NOT_USED",
            )
            self.assertFalse(
                HARNESS._is_local_storage_path("unlisted-memories/one.md")
            )

    def test_auth_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home, fake_home = self._make_isolated_home_fixture(root)
            external = root / "external-auth.json"
            external.write_bytes(b"external auth target")
            audits = {}

            def redirect_auth():
                (fake_home / "auth.json").unlink()
                (fake_home / "auth.json").symlink_to(external)

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "isolated CODEX_HOME runtime state is invalid"
            ):
                HARNESS._run_with_real_home_audit(
                    label="AUTH_SYMLINK",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=redirect_auth,
                )

            self.assertEqual(
                audits["AUTH_SYMLINK"]["isolated_home"]["runtime_state_valid"],
                False,
            )

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_auth_junction_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home, fake_home = self._make_isolated_home_fixture(root)
            external = root / "external-auth-directory"
            external.mkdir()
            audits = {}
            auth_path = fake_home / "auth.json"

            def redirect_auth():
                auth_path.unlink()
                completed = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(auth_path), str(external)],
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    check=False,
                )
                if completed.returncode != 0:
                    raise RuntimeError(completed.stderr)

            try:
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure,
                    "isolated CODEX_HOME runtime state is invalid",
                ):
                    HARNESS._run_with_real_home_audit(
                        label="AUTH_JUNCTION",
                        real_home=real_home,
                        audits=audits,
                        isolated_home=fake_home,
                        action=redirect_auth,
                    )
                self.assertEqual(
                    audits["AUTH_JUNCTION"]["isolated_home"][
                        "runtime_state_valid"
                    ],
                    False,
                )
            finally:
                if os.path.lexists(auth_path):
                    os.rmdir(auth_path)

    def test_protected_state_new_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            target = fake_home / "sol-luna-v4/state/new-state.bin"
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure,
                "isolated CODEX_HOME protected state changed",
            ):
                HARNESS._run_with_real_home_audit(
                    label="PROTECTED_NEW_FILE",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=lambda: target.write_bytes(b"new state\n"),
                )

            self.assertFalse(
                audits["PROTECTED_NEW_FILE"]["isolated_home"][
                    "protected_state_unchanged"
                ]
            )
            self.assertIn(
                "sol-luna-v4/state/new-state.bin",
                audits["PROTECTED_NEW_FILE"]["isolated_home"][
                    "protected_changed_paths"
                ],
            )

    def test_protected_state_modified_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            target = fake_home / "sol-luna-v4/state/daily-profile.json"
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure,
                "isolated CODEX_HOME protected state changed",
            ):
                HARNESS._run_with_real_home_audit(
                    label="PROTECTED_MODIFIED_FILE",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=lambda: target.write_bytes(b"modified state\n"),
                )

            self.assertFalse(
                audits["PROTECTED_MODIFIED_FILE"]["isolated_home"][
                    "protected_state_unchanged"
                ]
            )
            self.assertIn(
                "sol-luna-v4/state/daily-profile.json",
                audits["PROTECTED_MODIFIED_FILE"]["isolated_home"][
                    "protected_changed_paths"
                ],
            )

    def test_protected_state_deleted_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            target = fake_home / "sol-luna-v4/state/other-state.bin"
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure,
                "isolated CODEX_HOME protected state changed",
            ):
                HARNESS._run_with_real_home_audit(
                    label="PROTECTED_DELETED_FILE",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=target.unlink,
                )

            self.assertFalse(
                audits["PROTECTED_DELETED_FILE"]["isolated_home"][
                    "protected_state_unchanged"
                ]
            )
            self.assertIn(
                "sol-luna-v4/state/other-state.bin",
                audits["PROTECTED_DELETED_FILE"]["isolated_home"][
                    "protected_changed_paths"
                ],
            )

    def test_protected_state_change_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            audits = {}

            def change_protected_state():
                (real_home / "AGENTS.md").write_bytes(b"unexpected write\n")

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "protected state changed"
            ):
                HARNESS._run_with_real_home_audit(
                    label="PROTECTED_CHANGE",
                    real_home=real_home,
                    audits=audits,
                    action=change_protected_state,
                )

            self.assertFalse(
                audits["PROTECTED_CHANGE"]["protected_state_unchanged"]
            )
            self.assertEqual(
                audits["PROTECTED_CHANGE"]["real_home_runtime_attribution"],
                "NOT_USED",
            )

    def test_daily_profile_and_lkg_changes_fail_real_home_integrity(self):
        for relative in (
            "sol-luna-v4/state/daily-profile.json",
            "sol-luna-v4/state/last-good-profile.json",
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                real_home = self._make_real_home_fixture(Path(temporary))
                protected = real_home / relative
                audits = {}

                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "protected state changed"
                ):
                    HARNESS._run_with_real_home_audit(
                        label="PROFILE_OR_LKG_CHANGE",
                        real_home=real_home,
                        audits=audits,
                        action=lambda: protected.write_bytes(b"changed\n"),
                    )

                self.assertFalse(
                    audits["PROFILE_OR_LKG_CHANGE"]["protected_state_unchanged"]
                )

    def test_real_state_tree_immutable(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            snapshot = HARNESS._protected_state_snapshot(real_home)
            protected_relatives = (
                "sol-luna-v4/state",
                "sol-luna-v4/state/daily-profile.json",
                "sol-luna-v4/state/last-good-profile.json",
                "sol-luna-v4/state/selector.lock",
                "sol-luna-v4/state/other-state.bin",
            )

            for relative in protected_relatives:
                self.assertIn(relative, snapshot["entries"])
                entry = snapshot["entries"][relative]
                for field in (
                    "type",
                    "device",
                    "file_id",
                    "link_count",
                    "reparse",
                ):
                    self.assertIn(field, entry)
            for relative in protected_relatives[1:]:
                self.assertIsNotNone(snapshot["entries"][relative]["sha256"])

            audits = {}
            HARNESS._run_with_real_home_audit(
                label="REAL_STATE_UNCHANGED",
                real_home=real_home,
                audits=audits,
                action=lambda: None,
            )
            self.assertTrue(
                audits["REAL_STATE_UNCHANGED"]["protected_state_unchanged"]
            )

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "protected state changed"
            ):
                HARNESS._run_with_real_home_audit(
                    label="OTHER_STATE_CHANGE",
                    real_home=real_home,
                    audits={},
                    action=lambda: (
                        real_home / "sol-luna-v4/state/other-state.bin"
                    ).write_bytes(b"changed\n"),
                )

    def test_selector_lock_change_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            selector_lock = real_home / "sol-luna-v4/state/selector.lock"

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "protected state changed"
            ):
                HARNESS._run_with_real_home_audit(
                    label="SELECTOR_LOCK_CHANGE",
                    real_home=real_home,
                    audits={},
                    action=lambda: selector_lock.write_bytes(b"changed lock\n"),
                )

    def test_protected_state_dominates_plugin_cache_activity(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            plugin_state = (
                real_home
                / "plugins"
                / "cache"
                / "community"
                / "sample-plugin"
                / "0.2.0"
                / "state.json"
            )
            plugin_state.parent.mkdir(parents=True)
            plugin_state.write_bytes(b"before\n")
            audits = {}

            def change_plugin_and_protected_state():
                plugin_state.write_bytes(b"after plugin state\n")
                (real_home / "AGENTS.md").write_bytes(b"unexpected write\n")

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "protected state changed"
            ):
                HARNESS._run_with_real_home_audit(
                    label="PROTECTED_PLUGIN_DOMINANCE",
                    real_home=real_home,
                    audits=audits,
                    action=change_plugin_and_protected_state,
                )

            self.assertEqual(
                audits["PROTECTED_PLUGIN_DOMINANCE"][
                    "real_home_runtime_attribution"
                ],
                "NOT_USED",
            )
            self.assertFalse(
                audits["PROTECTED_PLUGIN_DOMINANCE"]["protected_state_unchanged"]
            )

    def test_unknown_path_change_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            mutable_candidate = fake_home / "unlisted-runtime.json"
            audits = {}

            def change_unlisted_state():
                mutable_candidate.write_bytes(b"before\n")
                mutable_candidate.write_bytes(b"after\n")

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "isolated CODEX_HOME runtime state is invalid"
            ):
                HARNESS._run_with_real_home_audit(
                    label="UNEXPECTED_WRITE",
                    real_home=real_home,
                    audits=audits,
                    isolated_home=fake_home,
                    action=change_unlisted_state,
                )

            self.assertTrue(
                audits["UNEXPECTED_WRITE"]["protected_state_unchanged"]
            )
            self.assertIn(
                "unlisted-runtime.json",
                audits["UNEXPECTED_WRITE"]["isolated_home"]["changed_paths"],
            )

    def test_copied_auth_has_distinct_file_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_auth = root / "real" / "auth.json"
            fake_auth = root / "fake" / "auth.json"
            real_auth.parent.mkdir()
            fake_auth.parent.mkdir()
            real_auth.write_bytes(b'{"fixture":"auth"}\n')

            shutil.copy2(real_auth, fake_auth, follow_symlinks=False)

            HARNESS._assert_independent_auth(real_auth, fake_auth)
            self.assertNotEqual(
                HARNESS._file_identity(real_auth)[:2],
                HARNESS._file_identity(fake_auth)[:2],
            )
            self.assertEqual(HARNESS._file_identity(fake_auth)[2], 1)

    def test_hardlink_to_real_home_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = root / "real"
            fake_home = root / "fake"
            real_home.mkdir()
            fake_home.mkdir()
            real_file = real_home / "auth.json"
            real_file.write_bytes(b"fixture")
            os.link(real_file, fake_home / "auth.json")

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "hardlink to real CODEX_HOME"
            ):
                HARNESS._assert_no_redirection(fake_home, real_home)

    def test_auth_symlink_write_through_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = root / "real"
            temp_parent = root / "temp"
            acceptance_root = temp_parent / (
                f"{HARNESS.HARNESS_ROOT_PREFIX}auth-symlink-test"
            )
            source_root = acceptance_root / "source"
            fake_home = acceptance_root / "codex-home"
            real_home.mkdir()
            temp_parent.mkdir()
            real_auth = real_home / "auth.json"
            real_auth.write_bytes(b"real auth must remain unchanged")
            artifacts = {}

            with HARNESS._owned_acceptance_directory(
                temp_parent=temp_parent,
                acceptance_root=acceptance_root,
                fake_home=fake_home,
                real_home=real_home,
                artifacts=artifacts,
            ):
                source_root.mkdir()
                fake_home.mkdir()
                fake_auth = fake_home / "auth.json"
                try:
                    fake_auth.symlink_to(real_auth)
                except OSError as exc:
                    self.skipTest(f"file symlink creation is unavailable: {exc}")

                with mock.patch.object(HARNESS, "_run") as runner:
                    with self.assertRaisesRegex(
                        HARNESS.HarnessFailure, "reparse point"
                    ):
                        HARNESS._apply_isolated_runtime(
                            python_command="python",
                            source_root=source_root,
                            source_commit="0" * 40,
                            acceptance_root=acceptance_root,
                            fake_home=fake_home,
                            real_home=real_home,
                            isolated_runtime_env={
                                "PATH": os.environ.get("PATH", "")
                            },
                        )

            runner.assert_not_called()
            self.assertEqual(real_auth.read_bytes(), b"real auth must remain unchanged")
            self.assertFalse(os.path.lexists(acceptance_root))

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_junction_to_real_codex_home_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = root / "real"
            temp_parent = root / "temp"
            junction = temp_parent / "link"
            real_home.mkdir()
            temp_parent.mkdir()
            completed = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(real_home)],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            try:
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "reparse point"
                ):
                    HARNESS._validate_temp_parent(junction, real_home)
            finally:
                if os.path.lexists(junction):
                    os.rmdir(junction)

    def test_mount_temp_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = root / "real"
            temp_parent = root / "temp"
            real_home.mkdir()
            temp_parent.mkdir()
            resolved_temp_parent = temp_parent.resolve(strict=True)
            real_ismount = os.path.ismount

            def simulated_mount(candidate):
                path = Path(candidate)
                if path.resolve(strict=False) == resolved_temp_parent:
                    return True
                return real_ismount(candidate)

            with mock.patch.object(
                HARNESS.os.path, "ismount", side_effect=simulated_mount
            ):
                with self.assertRaisesRegex(HARNESS.HarnessFailure, "mount point"):
                    HARNESS._validate_temp_parent(temp_parent, real_home)

    def test_temp_artifacts_cleanup_after_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = root / "real"
            temp_parent = root / "temp"
            acceptance_root = temp_parent / (
                f"{HARNESS.HARNESS_ROOT_PREFIX}cleanup-success"
            )
            fake_home = acceptance_root / "codex-home"
            real_home.mkdir()
            temp_parent.mkdir()
            artifacts = {}
            external = root / "external-auth.json"
            external.write_bytes(b"external")

            with HARNESS._owned_acceptance_directory(
                temp_parent=temp_parent,
                acceptance_root=acceptance_root,
                fake_home=fake_home,
                real_home=real_home,
                artifacts=artifacts,
            ):
                fake_home.mkdir()
                HARNESS._track_artifact(artifacts, fake_home)
                fake_auth = fake_home / "auth.json"
                fake_auth.write_bytes(b"fake")
                HARNESS._track_artifact(artifacts, fake_auth)
                hardlink = fake_home / "test-hardlink"
                os.link(external, hardlink)
                HARNESS._track_artifact(artifacts, hardlink)
                if os.name == "nt":
                    external_directory = root / "external-directory"
                    external_directory.mkdir()
                    junction = fake_home / "test-junction"
                    completed = subprocess.run(
                        [
                            "cmd",
                            "/c",
                            "mklink",
                            "/J",
                            str(junction),
                            str(external_directory),
                        ],
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    HARNESS._track_artifact(artifacts, junction)

            self.assertFalse(os.path.lexists(acceptance_root))
            self.assertEqual(artifacts["residual"], [])
            self.assertEqual(external.read_bytes(), b"external")
            if os.name == "nt":
                self.assertTrue(external_directory.is_dir())

    def test_temp_artifacts_cleanup_after_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = root / "real"
            temp_parent = root / "temp"
            acceptance_root = temp_parent / (
                f"{HARNESS.HARNESS_ROOT_PREFIX}cleanup-failure"
            )
            fake_home = acceptance_root / "codex-home"
            real_home.mkdir()
            temp_parent.mkdir()
            artifacts = {}

            with self.assertRaisesRegex(RuntimeError, "forced acceptance failure"):
                with HARNESS._owned_acceptance_directory(
                    temp_parent=temp_parent,
                    acceptance_root=acceptance_root,
                    fake_home=fake_home,
                    real_home=real_home,
                    artifacts=artifacts,
                ):
                    fake_home.mkdir()
                    HARNESS._track_artifact(artifacts, fake_home)
                    fake_auth = fake_home / "auth.json"
                    fake_auth.write_bytes(b"fake")
                    HARNESS._track_artifact(artifacts, fake_auth)
                    raise RuntimeError("forced acceptance failure")

            self.assertFalse(os.path.lexists(acceptance_root))
            self.assertEqual(artifacts["residual"], [])

    def test_temp_parent_identity_change_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = root / "real"
            temp_parent = root / "temp"
            acceptance_root = temp_parent / (
                f"{HARNESS.HARNESS_ROOT_PREFIX}cleanup-parent-identity"
            )
            fake_home = acceptance_root / "codex-home"
            real_home.mkdir()
            temp_parent.mkdir()
            artifacts = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "cleanup parent identity changed"
            ):
                with HARNESS._owned_acceptance_directory(
                    temp_parent=temp_parent,
                    acceptance_root=acceptance_root,
                    fake_home=fake_home,
                    real_home=real_home,
                    artifacts=artifacts,
                ):
                    moved_parent = root / "moved-temp"
                    temp_parent.rename(moved_parent)
                    temp_parent.mkdir()

            self.assertTrue(moved_parent.is_dir())
            self.assertTrue(temp_parent.is_dir())

    def test_protected_fingerprint_includes_mtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / "auth.json"
            auth.write_bytes(b"same bytes")
            before = HARNESS._fingerprint_paths(root, ("auth.json",))
            details = auth.stat()
            os.utime(auth, ns=(details.st_atime_ns, details.st_mtime_ns + 1_000_000_000))
            after = HARNESS._fingerprint_paths(root, ("auth.json",))

            self.assertNotEqual(before, after)

    def test_full_inventory_records_hash_mtime_and_link_count(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / "auth.json"
            auth.write_bytes(b"inventory fixture")

            inventory = HARNESS._inventory_tree(root)
            record = inventory["entries"]["auth.json"]

            self.assertEqual(record["type"], "file")
            self.assertEqual(record["sha256"], HARNESS._sha256_file(auth))
            self.assertEqual(record["mtime_ns"], auth.stat().st_mtime_ns)
            self.assertEqual(record["link_count"], 1)
            self.assertEqual(inventory["file_count"], 1)

    def test_environment_roots_can_be_siblings_inside_owned_acceptance_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            acceptance_root = root / "acceptance"
            fake_home = acceptance_root / "codex-home"
            environment_root = acceptance_root / "runtime-environment"
            environment = HARNESS._codex_environment(
                fake_home,
                {"HOME": "real-home", "OPENAI_API_KEY": "must-drop"},
                environment_root=environment_root,
            )

            self.assertEqual(environment["CODEX_HOME"], str(fake_home))
            self.assertEqual(environment["HOME"], str(fake_home))
            self.assertEqual(environment["USERPROFILE"], str(fake_home))
            for name in (
                "APPDATA",
                "LOCALAPPDATA",
                "TEMP",
                "TMP",
                "TMPDIR",
                "XDG_CACHE_HOME",
                "XDG_CONFIG_HOME",
                "XDG_DATA_HOME",
                "XDG_RUNTIME_DIR",
                "XDG_STATE_HOME",
            ):
                self.assertTrue(
                    Path(environment[name]).is_relative_to(environment_root)
                )
            self.assertNotIn("OPENAI_API_KEY", environment)
            real_home = root / "real"
            real_home.mkdir()
            fake_home.mkdir(parents=True)
            environment_root.mkdir()
            HARNESS._assert_isolated_environment_root(
                environment_root,
                acceptance_root,
                fake_home,
                real_home,
                environment,
            )

    def test_isolated_environment_root_rejects_external_hardlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            acceptance_root = root / "acceptance"
            fake_home = acceptance_root / "codex-home"
            environment_root = acceptance_root / "runtime-environment"
            real_home = root / "real"
            fake_home.mkdir(parents=True)
            environment_root.mkdir()
            real_home.mkdir()
            external = real_home / "external.bin"
            external.write_bytes(b"external")
            os.link(external, environment_root / "linked.bin")

            with self.assertRaisesRegex(HARNESS.HarnessFailure, "hardlink"):
                HARNESS._assert_isolated_environment_root(
                    environment_root,
                    acceptance_root,
                    fake_home,
                    real_home,
                )

    def test_owned_marker_and_fake_auth_are_preserved_during_case(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            temp_parent = root / "temp"
            temp_parent.mkdir()
            acceptance_root = temp_parent / (
                f"{HARNESS.HARNESS_ROOT_PREFIX}marker-test"
            )
            fake_home = acceptance_root / "codex-home"
            artifacts = {}

            with HARNESS._owned_acceptance_directory(
                temp_parent=temp_parent,
                acceptance_root=acceptance_root,
                fake_home=fake_home,
                real_home=real_home,
                artifacts=artifacts,
            ):
                marker = acceptance_root / HARNESS.OWNERSHIP_MARKER
                payload = json.loads(marker.read_text(encoding="utf-8"))
                self.assertEqual(payload["schema"], HARNESS.OWNERSHIP_SCHEMA)
                self.assertEqual(payload["root"], str(acceptance_root))
                fake_home.mkdir()
                fake_auth = fake_home / "auth.json"
                HARNESS._copy_auth_exclusive(real_home / "auth.json", fake_auth)
                HARNESS._assert_independent_auth(real_home / "auth.json", fake_auth)
                self.assertTrue(marker.is_file())
                self.assertTrue(fake_auth.is_file())

    def test_real_home_unrelated_runtime_activity_is_tolerated(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            unrelated = real_home / "sessions/host-runtime.jsonl"
            audits = {}

            def write_unrelated_runtime():
                unrelated.parent.mkdir()
                unrelated.write_bytes(b"host activity")

            HARNESS._run_with_real_home_audit(
                label="REAL_HOME_UNRELATED",
                real_home=real_home,
                audits=audits,
                action=write_unrelated_runtime,
            )

            self.assertTrue(audits["REAL_HOME_UNRELATED"]["protected_state_unchanged"])
            self.assertTrue(audits["REAL_HOME_UNRELATED"]["real_home_identity_unchanged"])
            self.assertEqual(
                audits["REAL_HOME_UNRELATED"]["real_home_runtime_attribution"],
                "NOT_USED",
            )
            self.assertNotIn("auth_before", audits["REAL_HOME_UNRELATED"])

    def test_exact_platform_namespaces_and_visualization_validation(self):
        allowed = (
            "sessions/2026/08/20/session.jsonl",
            "archived_sessions/2026/session.jsonl",
            "session-cache/index.json",
            "session_cache/index.json",
            "thread-writer-locks/thread.lock",
            "session_index.jsonl",
            "cache/codex_apps_tools/tools.json",
            "cache/codex_apps_server_info/server.json",
            "node_repl/active_execs/exec.json",
            "browser/sessions/2026/08/20/session.jsonl",
            "cache/remote_plugin_catalog/catalog.json",
            "plugins/cache/openai/plugin/1.0/state.json",
            "tmp/arg0/stdout.txt",
            f"visualizations/2026/08/20/{SYNTHETIC_VISUALIZATION_RUN_ID}/frame.png",
        )
        for relative in allowed:
            with self.subTest(relative=relative):
                self.assertEqual(
                    HARNESS._runtime_path_category(relative),
                    HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
                )
        rejected = (
            "auth.json",
            "browser/sessions/../other.json",
            "browser/other.json",
            "cache/other.json",
            "node_repl/other.json",
            "plugins/other/state.json",
            "tmp/other.txt",
            "visualizations/other/frame.png",
            f"visualizations/2026/13/20/{SYNTHETIC_VISUALIZATION_RUN_ID}/frame.png",
            "visualizations/2026/08/20/not-a-uuid/frame.png",
            f"visualizations/2026/08/20/{SYNTHETIC_VISUALIZATION_RUN_ID}/../frame.png",
        )
        for relative in rejected:
            with self.subTest(relative=relative):
                self.assertEqual(HARNESS._runtime_path_category(relative), HARNESS.UNKNOWN)

    def test_sandbox_migration_exact_regular_file_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            target = fake_home / ".sandbox_migration"
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="SANDBOX_MIGRATION_VALID",
                real_home=real_home,
                audits=audits,
                isolated_home=fake_home,
                action=lambda: target.write_bytes(b"abc"),
            )

            self.assertTrue(
                audits["SANDBOX_MIGRATION_VALID"]["isolated_home"][
                    "runtime_state_valid"
                ]
            )
            entry = HARNESS._isolated_home_snapshot(fake_home)["entries"][
                ".sandbox_migration"
            ]
            self.assertEqual(
                HARNESS._runtime_path_category(".sandbox_migration"),
                HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            )
            self.assertEqual(entry["type"], "file")
            self.assertEqual(entry["link_count"], 1)
            self.assertFalse(entry["reparse"])

    def test_sandbox_migration_wrong_type_and_reparse_are_rejected(self):
        for scenario in ("directory", "reparse"):
            with self.subTest(scenario=scenario):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    real_home, fake_home = self._make_isolated_home_fixture(root)
                    target = fake_home / ".sandbox_migration"
                    audits = {}

                    if scenario == "directory":
                        action = lambda: target.mkdir()
                    else:
                        external = root / "external-sandbox"
                        external.mkdir()

                        def create_reparse():
                            try:
                                target.symlink_to(external, target_is_directory=True)
                            except OSError as exc:
                                self.skipTest(
                                    f"reparse creation is unavailable: {exc}"
                                )

                        action = create_reparse

                    with self.assertRaisesRegex(
                        HARNESS.HarnessFailure,
                        "isolated CODEX_HOME runtime state is invalid",
                    ):
                        HARNESS._run_with_real_home_audit(
                            label=f"SANDBOX_MIGRATION_{scenario.upper()}",
                            real_home=real_home,
                            audits=audits,
                            isolated_home=fake_home,
                            action=action,
                        )

    def test_skills_observed_safe_structure_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            skills = fake_home / "skills"
            audits = {}

            def create_observed_structure():
                for index in range(28):
                    (skills / f"directory-{index}").mkdir(parents=True)
                for index in range(28):
                    (skills / f"directory-{index}" / "skill.txt").write_bytes(
                        b"skill\n"
                    )
                for index in range(26):
                    (skills / f"root-skill-{index}.txt").write_bytes(b"skill\n")

            HARNESS._run_with_real_home_audit(
                label="SKILLS_OBSERVED_STRUCTURE",
                real_home=real_home,
                audits=audits,
                isolated_home=fake_home,
                action=create_observed_structure,
            )

            self.assertTrue(
                audits["SKILLS_OBSERVED_STRUCTURE"]["isolated_home"][
                    "runtime_state_valid"
                ]
            )
            snapshot = HARNESS._isolated_home_snapshot(fake_home)
            descendants = {
                relative: entry
                for relative, entry in snapshot["entries"].items()
                if relative.startswith("skills/")
            }
            self.assertEqual(
                HARNESS._runtime_path_category("skills"),
                HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            )
            self.assertEqual(
                sum(entry["type"] == "directory" for entry in descendants.values()),
                28,
            )
            self.assertEqual(
                sum(entry["type"] == "file" for entry in descendants.values()),
                54,
            )
            self.assertTrue(all(not entry["reparse"] for entry in descendants.values()))
            self.assertTrue(
                all(
                    entry["type"] != "file" or entry["link_count"] == 1
                    for entry in descendants.values()
                )
            )

    def test_skills_and_staging_root_file_replacements_are_rejected(self):
        for relative, label in (
            ("skills", "SKILLS_ROOT_FILE"),
            (
                "plugins/.remote-plugin-install-staging",
                "STAGING_ROOT_FILE",
            ),
        ):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    real_home, fake_home = self._make_isolated_home_fixture(
                        Path(temporary)
                    )
                    target = fake_home / relative
                    audits = {}

                    with self.assertRaisesRegex(
                        HARNESS.HarnessFailure,
                        "isolated CODEX_HOME runtime state is invalid",
                    ):
                        def replace_root_with_file():
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(b"must be a directory\n")

                        HARNESS._run_with_real_home_audit(
                            label=label,
                            real_home=real_home,
                            audits=audits,
                            isolated_home=fake_home,
                            action=replace_root_with_file,
                        )

    def test_staging_safe_structure_and_persistent_empty_root_are_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            staging = fake_home / "plugins/.remote-plugin-install-staging"
            audits = {}

            def create_bundle_structure():
                bundle = staging / "remote-plugin-bundle"
                (bundle / "nested").mkdir(parents=True)
                (bundle / "manifest.json").write_bytes(b"{}\n")
                (bundle / "nested" / "payload.bin").write_bytes(b"payload\n")

            HARNESS._run_with_real_home_audit(
                label="STAGING_SAFE_STRUCTURE",
                real_home=real_home,
                audits=audits,
                isolated_home=fake_home,
                action=create_bundle_structure,
            )
            self.assertTrue(
                audits["STAGING_SAFE_STRUCTURE"]["isolated_home"][
                    "runtime_state_valid"
                ]
            )

        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            staging = fake_home / "plugins/.remote-plugin-install-staging"
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="STAGING_PERSISTENT_EMPTY_ROOT",
                real_home=real_home,
                audits=audits,
                isolated_home=fake_home,
                action=lambda: staging.mkdir(parents=True),
            )
            self.assertTrue(staging.is_dir())
            self.assertEqual(list(staging.iterdir()), [])
            self.assertTrue(
                audits["STAGING_PERSISTENT_EMPTY_ROOT"]["isolated_home"][
                    "runtime_state_valid"
                ]
            )

    def test_skills_and_staging_external_reparse_escapes_are_rejected(self):
        for relative, label in (
            ("skills", "SKILLS_EXTERNAL_REPARSE"),
            (
                "plugins/.remote-plugin-install-staging",
                "STAGING_EXTERNAL_REPARSE",
            ),
        ):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    real_home, fake_home = self._make_isolated_home_fixture(root)
                    external = root / "external-runtime"
                    external.mkdir()
                    target = fake_home / relative
                    audits = {}

                    def create_external_reparse():
                        try:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.symlink_to(external, target_is_directory=True)
                        except OSError as exc:
                            self.skipTest(
                                f"reparse creation is unavailable: {exc}"
                            )

                    with self.assertRaisesRegex(
                        HARNESS.HarnessFailure,
                        "isolated CODEX_HOME runtime state is invalid",
                    ):
                        HARNESS._run_with_real_home_audit(
                            label=label,
                            real_home=real_home,
                            audits=audits,
                            isolated_home=fake_home,
                            action=create_external_reparse,
                        )

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_skills_and_staging_external_junction_descendants_are_rejected(self):
        for relative, label in (
            ("skills/external", "SKILLS_EXTERNAL_JUNCTION"),
            (
                "plugins/.remote-plugin-install-staging/external",
                "STAGING_EXTERNAL_JUNCTION",
            ),
        ):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    real_home, fake_home = self._make_isolated_home_fixture(root)
                    external = root / "external-runtime"
                    external.mkdir()
                    target = fake_home / relative
                    audits = {}

                    def create_external_junction():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        self._create_junction(target, external)

                    try:
                        with self.assertRaisesRegex(
                            HARNESS.HarnessFailure,
                            "isolated CODEX_HOME runtime state is invalid",
                        ):
                            HARNESS._run_with_real_home_audit(
                                label=label,
                                real_home=real_home,
                                audits=audits,
                                isolated_home=fake_home,
                                action=create_external_junction,
                            )
                    finally:
                        if os.path.lexists(target):
                            target.unlink()

    def test_new_runtime_files_and_trees_unsafe_hardlinks_are_rejected(self):
        for relative, label in (
            (".sandbox_migration", "SANDBOX_MIGRATION_UNSAFE_HARDLINK"),
            ("skills/unsafe.txt", "SKILLS_UNSAFE_HARDLINK"),
            (
                "plugins/.remote-plugin-install-staging/unsafe.bin",
                "STAGING_UNSAFE_HARDLINK",
            ),
        ):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    real_home, fake_home = self._make_isolated_home_fixture(root)
                    external = root / "external-runtime-file"
                    external.write_bytes(b"external\n")
                    target = fake_home / relative
                    audits = {}

                    def create_unsafe_hardlink():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            os.link(external, target)
                        except OSError as exc:
                            self.skipTest(
                                f"hardlink creation is unavailable: {exc}"
                            )

                    with self.assertRaisesRegex(
                        HARNESS.HarnessFailure,
                        "isolated CODEX_HOME runtime state is invalid",
                    ):
                        HARNESS._run_with_real_home_audit(
                            label=label,
                            real_home=real_home,
                            audits=audits,
                            isolated_home=fake_home,
                            action=create_unsafe_hardlink,
                        )

    def test_new_runtime_namespace_names_remain_exact_and_fail_closed(self):
        rejected = (
            ".sandbox_migration.bak",
            ".sandbox_other",
            "skills-extra/file.txt",
            "skills/../outside.txt",
            "plugins/.remote-plugin-install-staging-extra/file.txt",
            "plugins/.remote-plugin-install-staging/../outside.txt",
            "plugins/other/state.json",
        )
        for relative in rejected:
            with self.subTest(relative=relative):
                self.assertEqual(
                    HARNESS._runtime_path_category(relative), HARNESS.UNKNOWN
                )

    def test_namespace_root_replaced_by_file_fails(self):
        for relative in HARNESS.EXPECTED_RUNTIME_DIRECTORY_ROOTS:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
                HARNESS._isolated_home_snapshot(fake_home)
                target = fake_home / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"runtime namespace must be a directory\n")

                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure,
                    "runtime namespace root is not an expected safe directory",
                ):
                    HARNESS._isolated_home_snapshot(fake_home)

    def test_visualization_runtime_file_is_not_a_directory_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, fake_home = self._make_isolated_home_fixture(Path(temporary))
            run_root = (
                fake_home
                / "visualizations/2026/08/20"
                / SYNTHETIC_VISUALIZATION_RUN_ID
            )
            run_root.mkdir(parents=True)
            (run_root / "frame.png").write_bytes(b"frame\n")

            snapshot = HARNESS._isolated_home_snapshot(fake_home)

            self.assertEqual(
                snapshot["entries"][
                    f"visualizations/2026/08/20/"
                    f"{SYNTHETIC_VISUALIZATION_RUN_ID}/frame.png"
                ]["type"],
                "file",
            )

    def test_invalid_visualization_structural_directory_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            audits = {}

            def create_invalid_date_directory():
                (fake_home / "visualizations/2026/13").mkdir(parents=True)

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure,
                "isolated CODEX_HOME could not be validated",
            ):
                HARNESS._run_with_isolated_home_audit(
                    label="INVALID_VISUALIZATION_STRUCTURE",
                    fake_home=fake_home,
                    real_home=real_home,
                    audits=audits,
                    action=create_invalid_date_directory,
                )
            self.assertIn(
                "visualizations/2026/13",
                audits["INVALID_VISUALIZATION_STRUCTURE"]["changed_paths"],
            )

    def test_isolated_home_all_five_sqlite_families_and_coupled_sidecars(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            names = (
                "goals_1.sqlite",
                "logs_2.sqlite",
                "memories_3.sqlite",
                "queue_4.sqlite",
                "state_5.sqlite",
            )
            audits = {}

            def create_sqlite_families():
                for name in names:
                    (fake_home / name).write_bytes(b"base")
                    (fake_home / f"{name}-wal").write_bytes(b"wal")
                    (fake_home / f"{name}-shm").write_bytes(b"shm")

            HARNESS._run_with_isolated_home_audit(
                label="ISOLATED_SQLITE_FAMILIES",
                fake_home=fake_home,
                real_home=real_home,
                audits=audits,
                action=create_sqlite_families,
            )
            self.assertTrue(audits["ISOLATED_SQLITE_FAMILIES"]["runtime_state_valid"])

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "isolated CODEX_HOME could not be validated"
            ):
                HARNESS._run_with_isolated_home_audit(
                    label="ORPHAN_SQLITE_SIDECAR",
                    fake_home=fake_home,
                    real_home=real_home,
                    action=lambda: (fake_home / "queue_99.sqlite-wal").write_bytes(
                        b"orphan"
                    ),
                )

    def test_thread_history_sqlite_family_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            base_relative = "thread_history_123.sqlite"
            audits = {}

            def create_thread_history_sqlite_family():
                for relative, content in (
                    (base_relative, b"base"),
                    (f"{base_relative}-wal", b"wal"),
                    (f"{base_relative}-shm", b"shm"),
                ):
                    (fake_home / relative).write_bytes(content)

            HARNESS._run_with_isolated_home_audit(
                label="THREAD_HISTORY_SQLITE_FAMILY",
                fake_home=fake_home,
                real_home=real_home,
                audits=audits,
                action=create_thread_history_sqlite_family,
            )

            self.assertTrue(
                audits["THREAD_HISTORY_SQLITE_FAMILY"]["runtime_state_valid"]
            )
            for relative in (
                base_relative,
                f"{base_relative}-wal",
                f"{base_relative}-shm",
            ):
                self.assertEqual(
                    HARNESS._runtime_path_category(relative),
                    HARNESS.CODEX_LOCAL_STORAGE_STATE,
                )

    def test_thread_history_orphan_sidecar_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            orphan_relative = "thread_history_123.sqlite-wal"
            audits = {}

            self.assertEqual(
                HARNESS._runtime_path_category(orphan_relative),
                HARNESS.CODEX_LOCAL_STORAGE_STATE,
            )
            with self.assertRaisesRegex(
                HARNESS.HarnessFailure,
                "isolated CODEX_HOME could not be validated",
            ):
                HARNESS._run_with_isolated_home_audit(
                    label="THREAD_HISTORY_ORPHAN_SIDECAR",
                    fake_home=fake_home,
                    real_home=real_home,
                    audits=audits,
                    action=lambda: (fake_home / orphan_relative).write_bytes(b"orphan"),
                )

            self.assertIn(
                orphan_relative,
                audits["THREAD_HISTORY_ORPHAN_SIDECAR"]["changed_paths"],
            )

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_isolated_plugin_cache_internal_junction_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            target = (
                fake_home
                / "plugins"
                / "cache"
                / "openai-bundled"
                / "chrome"
                / "1.0.0"
            )
            junction = target.parent / "latest"
            relative = junction.relative_to(fake_home).as_posix()
            audits = {}

            def create_internal_junction():
                target.mkdir(parents=True)
                (target / "runtime-state.json").write_bytes(b"internal target\n")
                self._create_junction(junction, target)

            try:
                HARNESS._run_with_isolated_home_audit(
                    label="ISOLATED_PLUGIN_CACHE_INTERNAL_JUNCTION",
                    fake_home=fake_home,
                    real_home=real_home,
                    audits=audits,
                    action=create_internal_junction,
                )
                self.assertTrue(
                    audits["ISOLATED_PLUGIN_CACHE_INTERNAL_JUNCTION"][
                        "runtime_state_valid"
                    ]
                )
                snapshot = HARNESS._isolated_home_snapshot(fake_home)
                self.assertEqual(
                    snapshot["entries"][relative]["type"],
                    "reparse",
                )
            finally:
                if os.path.lexists(junction):
                    os.rmdir(junction)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_isolated_plugin_cache_external_junction_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home, fake_home = self._make_isolated_home_fixture(root)
            external = root / "external-plugin-cache"
            external.mkdir()
            junction = fake_home / "plugins" / "cache" / "external"
            audits = {}

            def create_external_junction():
                junction.parent.mkdir(parents=True)
                self._create_junction(junction, external)

            try:
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure,
                    "isolated CODEX_HOME could not be validated",
                ):
                    HARNESS._run_with_isolated_home_audit(
                        label="ISOLATED_PLUGIN_CACHE_EXTERNAL_JUNCTION",
                        fake_home=fake_home,
                        real_home=real_home,
                        audits=audits,
                        action=create_external_junction,
                    )
                self.assertFalse(
                    audits["ISOLATED_PLUGIN_CACHE_EXTERNAL_JUNCTION"][
                        "runtime_state_valid"
                    ]
                )
            finally:
                if os.path.lexists(junction):
                    os.rmdir(junction)

    def test_o4_case_uses_isolated_home_and_exact_session_namespace(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home, fake_home = self._make_isolated_home_fixture(Path(temporary))
            environment_root = Path(temporary) / "acceptance" / "runtime"
            audits = {}
            observed: dict[str, str] = {}

            def run_o4_like_case():
                environment = HARNESS._codex_environment(
                    fake_home, environment_root=environment_root
                )
                observed.update(environment)
                for relative in (
                    "sessions/2026/08/20/o4.jsonl",
                    "browser/sessions/2026/08/20/o4.jsonl",
                ):
                    session = fake_home / relative
                    session.parent.mkdir(parents=True)
                    session.write_text("{}\n", encoding="utf-8")
                return "O4-ISOLATED"

            result = HARNESS._run_with_real_home_audit(
                label="O4_ISOLATED",
                real_home=real_home,
                audits=audits,
                isolated_home=fake_home,
                action=run_o4_like_case,
            )

            self.assertEqual(result, "O4-ISOLATED")
            self.assertEqual(observed["CODEX_HOME"], str(fake_home))
            self.assertEqual(observed["HOME"], str(fake_home))
            self.assertTrue(
                Path(observed["TEMP"]).is_relative_to(environment_root)
            )
            self.assertTrue(audits["O4_ISOLATED"]["isolated_home"]["runtime_state_valid"])

    def test_o9_selector_loader_does_not_create_pycache(self):
        with tempfile.TemporaryDirectory() as temporary:
            fake_home = Path(temporary) / "fake-home"
            selector_path = fake_home / "sol-luna-v4" / "selector.py"
            selector_path.parent.mkdir(parents=True)
            selector_path.write_text("SELECTOR_MARKER = 'loaded'\n", encoding="utf-8")
            original_dont_write_bytecode = sys.dont_write_bytecode

            module = HARNESS._load_selector(selector_path)

            self.assertEqual(module.SELECTOR_MARKER, "loaded")
            self.assertEqual(sys.dont_write_bytecode, original_dont_write_bytecode)
            self.assertFalse((selector_path.parent / "__pycache__").exists())

            failing_selector = selector_path.parent / "failing_selector.py"
            failing_selector.write_text(
                "raise RuntimeError('loader failure')\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "loader failure"):
                HARNESS._load_selector(failing_selector)
            self.assertEqual(sys.dont_write_bytecode, original_dont_write_bytecode)

    def test_o9_failsoft_uses_isolated_env(self):
        class FakeSelector:
            def __init__(self):
                self._read_daily_profile = lambda _: ("OK", {})
                self.observed_environments = []

            def _record_environment(self):
                self.observed_environments.append(dict(os.environ))

            def adapt_modeldial_api(self, payload, *, source_url):
                self._record_environment()
                return payload

            def ensure_daily_profile(self, adapted, *, state_dir):
                self._record_environment()
                return {"selected_role": "luna_max", "selected_effort": "max"}

            def read_status(self, *, codex_home, state_dir):
                self._record_environment()
                if state_dir.name == "o9-read-failure":
                    return {
                        "health": "Misconfigured",
                        "reason_codes": ["DAILY_PROFILE_READ_FAILED"],
                    }
                return {
                    "health": "Healthy",
                    "reference_cost_metadata_available": False,
                }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home, fake_home = self._make_isolated_home_fixture(root)
            snapshot = root / "snapshot.json"
            snapshot.write_text(
                json.dumps({"rankings": [{"model": "gpt-5.6-luna", "reasoningEffort": "max"}]}),
                encoding="utf-8",
            )
            selector = FakeSelector()
            state_root = root / "acceptance-state"
            isolated_runtime_env = HARNESS._codex_environment(
                fake_home,
                {
                    "PATH": "safe-path",
                    "SYSTEMROOT": "safe-system-root",
                    "HOST_ONLY_SECRET": "must-not-leak",
                },
                environment_root=root / "runtime-environment",
            )
            with mock.patch.dict(
                os.environ, {"HOST_ONLY_SECRET": "host-value"}, clear=False
            ), mock.patch.object(HARNESS, "_load_selector", return_value=selector):
                results, profile = HARNESS._run_o9_fail_soft(
                    selector_path=fake_home / "sol-luna-v4/selector.py",
                    fake_home=fake_home,
                    snapshot_path=snapshot,
                    isolated_runtime_env=isolated_runtime_env,
                    state_root=state_root,
                )
                self.assertEqual(os.environ["HOST_ONLY_SECRET"], "host-value")

            self.assertEqual(profile["selected_role"], "luna_max")
            self.assertEqual(results["missing"]["health"], "Healthy")
            self.assertEqual(results["invalid"]["health"], "Healthy")
            self.assertEqual(results["read_failure"]["health"], "Misconfigured")
            self.assertEqual(results["read_failure"]["state_created"], False)
            self.assertFalse((fake_home / "upgrade").exists())
            self.assertGreaterEqual(len(selector.observed_environments), 7)
            for observed in selector.observed_environments:
                self.assertEqual(observed, isolated_runtime_env)
                self.assertNotIn("HOST_ONLY_SECRET", observed)


if __name__ == "__main__":
    unittest.main()
