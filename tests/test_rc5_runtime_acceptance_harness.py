import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
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


class Rc5RuntimeAcceptanceHarnessTests(unittest.TestCase):
    def _make_real_home_fixture(self, root: Path) -> Path:
        real_home = root / "real"
        (real_home / "agents").mkdir(parents=True)
        (real_home / "sol-luna-v4" / "state").mkdir(parents=True)
        (real_home / "backups" / "sol-luna-v4").mkdir(parents=True)
        (real_home / "AGENTS.md").write_bytes(b"protected policy\n")
        (real_home / "config.toml").write_bytes(b"[agents]\n")
        (real_home / "agents" / "luna-low.toml").write_bytes(
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
        (real_home / "backups" / "sol-luna-v4" / "metadata.json").write_bytes(
            b"{}\n"
        )
        (real_home / "auth.json").write_bytes(b'{"fixture":"auth"}\n')
        return real_home

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
            "XDG_STATE_HOME",
        ):
            self.assertTrue(Path(environment[name]).is_relative_to(fake_home))
        for forbidden in ("OPENAI_API_KEY", "GITHUB_TOKEN", "API_KEY"):
            self.assertNotIn(forbidden, environment)

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
                audits["AUTH_REFRESH"]["auth_classification"],
                HARNESS.AUTH_RUNTIME_REFRESH_OBSERVED,
            )
            self.assertEqual(
                audits["AUTH_REFRESH"]["activity_category"],
                HARNESS.AUTH_RUNTIME_ACTIVITY,
            )

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
                audits["SESSION_JSONL"]["activity_category"],
                HARNESS.SESSION_RUNTIME_ACTIVITY,
            )
            self.assertEqual(
                audits["SESSION_JSONL"]["activity_categories"],
                [HARNESS.SESSION_RUNTIME_ACTIVITY],
            )

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
                audits["SQLITE_WAL"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
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
                audits["SQLITE_SHM"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
            )

    def test_sqlite_db_activity_allowed_only_in_expected_runtime_path(self):
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
                audits["SQLITE_DB"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
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

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unexpected write outside"
            ):
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
            self.assertIn(
                "sqlite/codex-evil.db",
                audits["NEW_ARBITRARY_CODEX_DB"]["unexpected_changed_paths"],
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
                audits["BASELINE_CODEX_DB_MUTATION"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
            )
            self.assertTrue(
                audits["BASELINE_CODEX_DB_MUTATION"]["unexpected_write_absent"]
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
                audits["BASELINE_CODEX_DB_SAFE_REPLACEMENT"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
            )
            self.assertTrue(
                audits["BASELINE_CODEX_DB_SAFE_REPLACEMENT"][
                    "unexpected_write_absent"
                ]
            )

    def test_observed_runtime_path_classification_contract_is_total(self):
        approved = frozenset({"sqlite/codex-existing.db"})
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
            "plugins": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "plugins/cache": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "plugins/cache/marketplace/plugin/1.0.0/state.json": HARNESS.CODEX_PLATFORM_RUNTIME_STATE,
            "plugins/evil/state.json": HARNESS.UNKNOWN,
            "plugins/data/state.json": HARNESS.UNKNOWN,
            "plugins-other/state.json": HARNESS.UNKNOWN,
            "sqlite/goals_1.sqlite": HARNESS.CODEX_LOCAL_STORAGE_STATE,
            "sqlite/codex-existing.db": HARNESS.CODEX_LOCAL_STORAGE_STATE,
            "sqlite/codex-evil.db": HARNESS.UNKNOWN,
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

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unexpected write outside"
            ):
                HARNESS._run_with_real_home_audit(
                    label="NEW_CODEX_DB_WAL",
                    real_home=real_home,
                    audits=audits,
                    action=lambda: (
                        candidate.parent.mkdir(),
                        candidate.write_bytes(b"unexpected wal\n"),
                    ),
                )

            self.assertIn(
                "sqlite/codex-evil.db-wal",
                audits["NEW_CODEX_DB_WAL"]["unexpected_changed_paths"],
            )

    def test_new_codex_db_shm_is_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            candidate = real_home / "sqlite" / "codex-evil.db-shm"
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unexpected write outside"
            ):
                HARNESS._run_with_real_home_audit(
                    label="NEW_CODEX_DB_SHM",
                    real_home=real_home,
                    audits=audits,
                    action=lambda: (
                        candidate.parent.mkdir(),
                        candidate.write_bytes(b"unexpected shm\n"),
                    ),
                )

            self.assertIn(
                "sqlite/codex-evil.db-shm",
                audits["NEW_CODEX_DB_SHM"]["unexpected_changed_paths"],
            )

    def test_baseline_codex_db_sidecars_are_allowed_only_with_approved_base(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            database_path = real_home / "sqlite" / "codex-approved.db"
            database_path.parent.mkdir()
            database_path.write_bytes(b"before\n")
            audits = {}

            def create_sidecars():
                (database_path.with_name("codex-approved.db-wal")).write_bytes(
                    b"wal\n"
                )
                (database_path.with_name("codex-approved.db-shm")).write_bytes(
                    b"shm\n"
                )

            HARNESS._run_with_real_home_audit(
                label="BASELINE_CODEX_DB_SIDECARS",
                real_home=real_home,
                audits=audits,
                action=create_sidecars,
            )

            approved = frozenset(
                HARNESS._local_storage_snapshot(real_home)[
                    "approved_codex_db_paths"
                ]
            )
            self.assertIn("sqlite/codex-approved.db", approved)
            self.assertTrue(
                HARNESS._is_local_storage_path(
                    "sqlite/codex-approved.db-wal", approved
                )
            )
            self.assertFalse(
                HARNESS._is_local_storage_path(
                    "sqlite/codex-other.db-wal", approved
                )
            )
            self.assertEqual(
                audits["BASELINE_CODEX_DB_SIDECARS"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
            )

    def test_baseline_codex_db_replaced_by_directory_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            database_path = real_home / "sqlite" / "codex-approved.db"
            database_path.parent.mkdir()
            database_path.write_bytes(b"before\n")
            audits = {}

            def replace_with_directory():
                database_path.unlink()
                database_path.mkdir()

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unexpected write outside"
            ):
                HARNESS._run_with_real_home_audit(
                    label="BASELINE_CODEX_DB_DIRECTORY",
                    real_home=real_home,
                    audits=audits,
                    action=replace_with_directory,
                )

            self.assertIn(
                "sqlite/codex-approved.db",
                audits["BASELINE_CODEX_DB_DIRECTORY"]["unexpected_changed_paths"],
            )

    def test_baseline_codex_db_replaced_by_symlink_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            database_path = real_home / "sqlite" / "codex-approved.db"
            database_path.parent.mkdir()
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
                HARNESS.HarnessFailure, "unexpected write outside"
            ):
                HARNESS._run_with_real_home_audit(
                    label="BASELINE_CODEX_DB_SYMLINK",
                    real_home=real_home,
                    audits=audits,
                    action=replace_with_symlink,
                )

            self.assertIn(
                "sqlite/codex-approved.db",
                audits["BASELINE_CODEX_DB_SYMLINK"]["unexpected_changed_paths"],
            )

    def test_baseline_codex_db_replaced_by_hardlink_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            database_path = real_home / "sqlite" / "codex-approved.db"
            database_path.parent.mkdir()
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
                HARNESS.HarnessFailure, "unexpected write outside"
            ):
                HARNESS._run_with_real_home_audit(
                    label="BASELINE_CODEX_DB_HARDLINK",
                    real_home=real_home,
                    audits=audits,
                    action=replace_with_hardlink,
                )

            self.assertIn(
                "sqlite/codex-approved.db",
                audits["BASELINE_CODEX_DB_HARDLINK"]["unexpected_changed_paths"],
            )

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_baseline_codex_db_replaced_by_junction_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            database_path = real_home / "sqlite" / "codex-approved.db"
            database_path.parent.mkdir()
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
                    HARNESS.HarnessFailure, "unexpected write outside"
                ):
                    HARNESS._run_with_real_home_audit(
                        label="BASELINE_CODEX_DB_JUNCTION",
                        real_home=real_home,
                        audits=audits,
                        action=replace_with_junction,
                    )
            finally:
                if os.path.lexists(database_path):
                    os.rmdir(database_path)

            self.assertIn(
                "sqlite/codex-approved.db",
                audits["BASELINE_CODEX_DB_JUNCTION"]["unexpected_changed_paths"],
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
                audits["SQLITE_FAMILY_CREATE"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
            )
            self.assertTrue(
                audits["SQLITE_FAMILY_CREATE"]["unexpected_write_absent"]
            )

    def test_arbitrary_root_sqlite_is_unknown(self):
        for relative in ("evil.sqlite", "goals_1.sqlite", "random.db"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                real_home = self._make_real_home_fixture(Path(temporary))
                candidate = real_home / relative
                audits = {}

                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "unexpected write outside"
                ):
                    HARNESS._run_with_real_home_audit(
                        label="ARBITRARY_ROOT_SQLITE",
                        real_home=real_home,
                        audits=audits,
                        action=lambda: candidate.write_bytes(b"unexpected\n"),
                    )

                self.assertIn(
                    relative,
                    audits["ARBITRARY_ROOT_SQLITE"]["unexpected_changed_paths"],
                )

    def test_arbitrary_sqlite_wal_and_shm_are_unknown(self):
        for relative in (
            "evil.sqlite-wal",
            "evil.sqlite-shm",
            "sqlite/codex-dev.db-wal",
            "sqlite/codex-dev.db-shm",
            "state_5.sqlite-wal",
            "state_5.sqlite-shm",
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                real_home = self._make_real_home_fixture(Path(temporary))
                candidate = real_home / relative
                audits = {}

                def create_candidate():
                    candidate.parent.mkdir(parents=True, exist_ok=True)
                    candidate.write_bytes(b"unexpected\n")

                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "unexpected write outside"
                ):
                    HARNESS._run_with_real_home_audit(
                        label="ARBITRARY_SQLITE_SIDECAR",
                        real_home=real_home,
                        audits=audits,
                        action=create_candidate,
                    )
                self.assertIn(
                    relative,
                    audits["ARBITRARY_SQLITE_SIDECAR"]["unexpected_changed_paths"],
                )

    def test_valid_sqlite_validated_family_activity_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            sqlite_dir = real_home / "sqlite"
            sqlite_dir.mkdir()
            codex_base = sqlite_dir / "codex-history-snapshots-dev.db"
            codex_base.write_bytes(b"before\n")
            audits = {}
            bases = (
                "goals_1.sqlite",
                "logs_2.sqlite",
                "memories_1.sqlite",
                "state_5.sqlite",
            )

            def create_sqlite_family():
                codex_base.write_bytes(b"after\n")
                for name in bases:
                    (sqlite_dir / name).write_bytes(b"base\n")
                    (sqlite_dir / f"{name}-wal").write_bytes(b"wal\n")
                    (sqlite_dir / f"{name}-shm").write_bytes(b"shm\n")

            HARNESS._run_with_real_home_audit(
                label="SQLITE_VALIDATED_FAMILY",
                real_home=real_home,
                audits=audits,
                action=create_sqlite_family,
            )

            self.assertEqual(
                audits["SQLITE_VALIDATED_FAMILY"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
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
                audits["VOLATILE_STORAGE"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
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
                audits["PLATFORM_CACHE"]["activity_category"],
                HARNESS.SESSION_RUNTIME_ACTIVITY,
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
                audits["NODE_REPL_ACTIVE_EXEC"]["activity_category"],
                HARNESS.SESSION_RUNTIME_ACTIVITY,
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
                audits["REMOTE_CURATED_PLUGIN_CACHE"]["activity_category"],
                HARNESS.SESSION_RUNTIME_ACTIVITY,
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
                audits["PLUGIN_CACHE_FIRST_USE"]["activity_category"],
                HARNESS.SESSION_RUNTIME_ACTIVITY,
            )
            self.assertTrue(
                audits["PLUGIN_CACHE_FIRST_USE"]["unexpected_write_absent"]
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
                audits["PLUGIN_CACHE_OBSERVED_CREATE"]["activity_category"],
                HARNESS.SESSION_RUNTIME_ACTIVITY,
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
                audits["PLUGIN_CACHE_OBSERVED_DELETE"]["activity_category"],
                HARNESS.SESSION_RUNTIME_ACTIVITY,
            )
            self.assertEqual(
                audits["PLUGIN_CACHE_OBSERVED_DELETE"]["activity_categories"],
                [HARNESS.SESSION_RUNTIME_ACTIVITY],
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
                audits["ANOTHER_MARKETPLACE_PLUGIN_CACHE"]["activity_category"],
                HARNESS.SESSION_RUNTIME_ACTIVITY,
            )

    def _assert_unknown_plugin_path_fails_closed(self, relative, label):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            candidate = real_home / relative
            candidate.parent.mkdir(parents=True)
            candidate.write_bytes(b"before\n")
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unexpected write outside"
            ):
                HARNESS._run_with_real_home_audit(
                    label=label,
                    real_home=real_home,
                    audits=audits,
                    action=lambda: candidate.write_bytes(b"after plugin state\n"),
                )

            self.assertEqual(
                audits[label]["activity_category"], HARNESS.UNEXPECTED_WRITE
            )
            self.assertEqual(
                HARNESS._runtime_path_category(relative), HARNESS.UNKNOWN
            )
            self.assertIn(relative, audits[label]["unexpected_changed_paths"])

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
            real_home = self._make_real_home_fixture(Path(temporary))
            cache_root = real_home / "plugins" / "cache"
            cache_root.mkdir(parents=True)
            escaped_path = cache_root / ".." / "evil" / "state.json"
            escaped_path.parent.mkdir(parents=True)
            escaped_path.write_bytes(b"before\n")
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unexpected write outside"
            ):
                HARNESS._run_with_real_home_audit(
                    label="PLUGIN_CACHE_PATH_ESCAPE",
                    real_home=real_home,
                    audits=audits,
                    action=lambda: escaped_path.write_bytes(b"after\n"),
                )

            normalized_relative = "plugins/evil/state.json"
            self.assertEqual(
                HARNESS._runtime_path_category(normalized_relative),
                HARNESS.UNKNOWN,
            )
            self.assertEqual(
                audits["PLUGIN_CACHE_PATH_ESCAPE"]["activity_category"],
                HARNESS.UNEXPECTED_WRITE,
            )
            self.assertEqual(
                audits["PLUGIN_CACHE_PATH_ESCAPE"]["unexpected_changed_paths"],
                [normalized_relative],
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
                audits["COMPUTER_USE_CONFIG"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
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
                audits["COMPUTER_USE_CONFIG_CREATE"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
            )
            self.assertTrue(
                audits["COMPUTER_USE_CONFIG_CREATE"]["unexpected_write_absent"]
            )

    def test_unexpected_computer_use_child_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            child = real_home / "computer-use" / "unexpected.json"
            audits = {}

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unexpected write outside"
            ):
                HARNESS._run_with_real_home_audit(
                    label="COMPUTER_USE_CHILD",
                    real_home=real_home,
                    audits=audits,
                    action=lambda: (
                        child.parent.mkdir(),
                        child.write_bytes(b"unexpected\n"),
                    ),
                )

            self.assertIn(
                "computer-use/unexpected.json",
                audits["COMPUTER_USE_CHILD"]["unexpected_changed_paths"],
            )

    def test_expected_runtime_file_replaced_by_directory_fails_closed(self):
        cases = (
            ("session_index.jsonl", HARNESS._session_runtime_snapshot),
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
            "session_index.jsonl",
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
                audits["MEMORIES_TREE"]["activity_category"],
                HARNESS.LOCAL_STORAGE_ACTIVITY,
            )
            self.assertFalse(
                HARNESS._is_local_storage_path("unlisted-memories/one.md")
            )

    def test_auth_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            external = root / "external-auth.json"
            external.write_bytes(b"external auth target")
            audits = {}

            def redirect_auth():
                (real_home / "auth.json").unlink()
                (real_home / "auth.json").symlink_to(external)

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "auth.json runtime state is invalid"
            ):
                HARNESS._run_with_real_home_audit(
                    label="AUTH_SYMLINK",
                    real_home=real_home,
                    audits=audits,
                    action=redirect_auth,
                )

            self.assertEqual(
                audits["AUTH_SYMLINK"]["auth_classification"],
                HARNESS.AUTH_RUNTIME_STATE_INVALID,
            )

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_auth_junction_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_home = self._make_real_home_fixture(root)
            external = root / "external-auth-directory"
            external.mkdir()
            audits = {}
            auth_path = real_home / "auth.json"
            auth_path.unlink()
            completed = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(auth_path), str(external)],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            try:
                with self.assertRaisesRegex(
                    HARNESS.HarnessFailure, "auth.json runtime state is invalid"
                ):
                    HARNESS._run_with_real_home_audit(
                        label="AUTH_JUNCTION",
                        real_home=real_home,
                        audits=audits,
                        action=lambda: None,
                    )
                self.assertEqual(
                    audits["AUTH_JUNCTION"]["auth_classification"],
                    HARNESS.AUTH_RUNTIME_STATE_INVALID,
                )
            finally:
                if os.path.lexists(auth_path):
                    os.rmdir(auth_path)

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
                audits["PROTECTED_CHANGE"]["auth_classification"],
                HARNESS.UNEXPECTED_WRITE,
            )
            self.assertEqual(
                audits["PROTECTED_CHANGE"]["activity_category"],
                HARNESS.UNEXPECTED_WRITE,
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
                audits["PROTECTED_PLUGIN_DOMINANCE"]["activity_category"],
                HARNESS.UNEXPECTED_WRITE,
            )
            self.assertFalse(
                audits["PROTECTED_PLUGIN_DOMINANCE"]["protected_state_unchanged"]
            )

    def test_unknown_path_change_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            mutable_candidate = real_home / "unlisted-runtime.json"
            mutable_candidate.write_bytes(b"before\n")
            audits = {}

            def change_unlisted_state():
                mutable_candidate.write_bytes(b"after\n")

            with self.assertRaisesRegex(
                HARNESS.HarnessFailure, "unexpected write outside the runtime allowlist"
            ):
                HARNESS._run_with_real_home_audit(
                    label="UNEXPECTED_WRITE",
                    real_home=real_home,
                    audits=audits,
                    action=change_unlisted_state,
                )

            self.assertTrue(
                audits["UNEXPECTED_WRITE"]["protected_state_unchanged"]
            )
            self.assertFalse(audits["UNEXPECTED_WRITE"]["unexpected_write_absent"])
            self.assertEqual(
                audits["UNEXPECTED_WRITE"]["auth_classification"],
                HARNESS.UNEXPECTED_WRITE,
            )
            self.assertEqual(
                audits["UNEXPECTED_WRITE"]["activity_category"],
                HARNESS.UNEXPECTED_WRITE,
            )
            self.assertEqual(
                audits["UNEXPECTED_WRITE"]["unexpected_changed_paths"],
                ["unlisted-runtime.json"],
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


if __name__ == "__main__":
    unittest.main()
