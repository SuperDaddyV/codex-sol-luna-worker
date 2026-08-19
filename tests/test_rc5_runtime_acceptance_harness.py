import importlib.util
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
            self.assertFalse(
                HARNESS._is_local_storage_path("sqlite/unexpected.txt")
            )

    def test_allowed_volatile_storage_is_not_content_hashed(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
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

    def test_plugin_install_marker_activity_allowed_without_allowing_cache_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_home = self._make_real_home_fixture(Path(temporary))
            marker_path = (
                real_home
                / "plugins"
                / "cache"
                / "openai-curated-remote"
                / "github"
                / ".codex-remote-plugin-install.json"
            )
            marker_path.parent.mkdir(parents=True)
            marker_path.write_bytes(b"before\n")
            audits = {}

            HARNESS._run_with_real_home_audit(
                label="PLUGIN_INSTALL_MARKER",
                real_home=real_home,
                audits=audits,
                action=lambda: marker_path.write_bytes(b"after\n"),
            )

            self.assertEqual(
                audits["PLUGIN_INSTALL_MARKER"]["activity_category"],
                HARNESS.SESSION_RUNTIME_ACTIVITY,
            )
            self.assertFalse(
                HARNESS._is_session_runtime_path(
                    "plugins/cache/openai-curated-remote/github/unexpected.json"
                )
            )

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
