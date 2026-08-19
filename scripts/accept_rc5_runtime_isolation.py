#!/usr/bin/env python3
"""Run the RC5 O2/O4/O9 acceptance cases in an isolated fake CODEX_HOME."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any, Callable, Iterable, Iterator, Mapping
import uuid


RC5_SOURCE_COMMIT = "5ae88ff9190b31174c55a6136c0c8c8611d0b34c"

# The real CODEX_HOME boundary is intentionally split into the managed Sol/Luna
# state and the runtime state that Codex is allowed to refresh while acceptance
# is running.  Keep these path lists explicit: a broad ``**/*.sqlite`` or
# ``**/*`` allowlist would hide an unexpected write.
PROTECTED_SOL_LUNA_STATE = "PROTECTED_SOL_LUNA_STATE"
CODEX_PLATFORM_RUNTIME_STATE = "CODEX_PLATFORM_RUNTIME_STATE"
CODEX_LOCAL_STORAGE_STATE = "CODEX_LOCAL_STORAGE_STATE"

PROTECTED_REAL_PATHS = (
    "AGENTS.md",
    "config.toml",
    "agents/luna-low.toml",
    "agents/luna-medium.toml",
    "agents/luna-high.toml",
    "agents/luna-xhigh.toml",
    "agents/luna-max.toml",
    "sol-luna-v4/selector.py",
    "sol-luna-v4/install-manifest.json",
    "sol-luna-v4/state",
    "backups/sol-luna-v4",
)
PROTECTED_REAL_TREE_PATHS = {
    "sol-luna-v4/state",
    "backups/sol-luna-v4",
}
AUTH_RUNTIME_RELATIVE = "auth.json"
SESSION_RUNTIME_TREE_PATHS: tuple[str, ...] = (
    "sessions",
    "archived_sessions",
    "session-cache",
    "session_cache",
    "thread-writer-locks",
    "cache/codex_apps_tools",
    "cache/codex_apps_server_info",
    "node_repl/active_execs",
)
SESSION_RUNTIME_FILE_PATHS: tuple[str, ...] = ("session_index.jsonl",)
SESSION_RUNTIME_DISCOVERY_ROOTS: tuple[str, ...] = ("plugins/cache",)
SESSION_RUNTIME_DISCOVERED_FILE_NAMES = {".codex-remote-plugin-install.json"}
EXPLICIT_SESSION_RUNTIME_PATHS: tuple[str, ...] = (
    *SESSION_RUNTIME_TREE_PATHS,
    *SESSION_RUNTIME_FILE_PATHS,
)
EXPLICIT_LOCAL_STORAGE_FILE_PATHS: tuple[str, ...] = (
    ".codex-global-state.json",
    ".codex-global-state.json.bak",
    "history.jsonl",
    "models_cache.json",
    "installation_id",
    "computer-use/config.json",
)
EXPLICIT_LOCAL_STORAGE_TREE_PATHS: tuple[str, ...] = ("sqlite",)
EXPLICIT_LOCAL_STORAGE_CONTENT_TREE_PATHS: tuple[str, ...] = ("memories",)
ALL_LOCAL_STORAGE_TREE_PATHS = (
    *EXPLICIT_LOCAL_STORAGE_TREE_PATHS,
    *EXPLICIT_LOCAL_STORAGE_CONTENT_TREE_PATHS,
)
MUTABLE_REAL_PATHS = (
    AUTH_RUNTIME_RELATIVE,
    *EXPLICIT_SESSION_RUNTIME_PATHS,
    *EXPLICIT_LOCAL_STORAGE_FILE_PATHS,
    *EXPLICIT_LOCAL_STORAGE_CONTENT_TREE_PATHS,
)
LOCAL_STORAGE_ANCESTOR_PATHS = (
    *ALL_LOCAL_STORAGE_TREE_PATHS,
)
AUTH_UNCHANGED = "AUTH_UNCHANGED"
AUTH_RUNTIME_REFRESH_OBSERVED = "AUTH_RUNTIME_REFRESH_OBSERVED"
AUTH_RUNTIME_STATE_INVALID = "AUTH_RUNTIME_STATE_INVALID"

AUTH_RUNTIME_ACTIVITY = "AUTH_RUNTIME_ACTIVITY"
SESSION_RUNTIME_ACTIVITY = "SESSION_RUNTIME_ACTIVITY"
LOCAL_STORAGE_ACTIVITY = "LOCAL_STORAGE_ACTIVITY"
UNEXPECTED_WRITE = "UNEXPECTED_WRITE"

# Keep the old auth-specific constants above for the existing diagnostics and
# tests.  New audit consumers should use the category fields below.
RUNTIME_ACTIVITY_CATEGORIES = {
    AUTH_RUNTIME_ACTIVITY,
    SESSION_RUNTIME_ACTIVITY,
    LOCAL_STORAGE_ACTIVITY,
    UNEXPECTED_WRITE,
}
ALLOWED_RECEIPT_TOOLS = {"spawn_agent", "wait_agent"}
HARNESS_ROOT_PREFIX = "rc5-runtime-auth-isolated-"
OWNERSHIP_MARKER = ".rc5-runtime-acceptance-owner.json"
OWNERSHIP_SCHEMA = 1
INHERITED_CODEX_ENVIRONMENT_NAMES = {
    "COMSPEC",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "NO_COLOR",
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "TERM",
    "WINDIR",
}
PRIVATE_HOME_PATH_PATTERNS = (
    re.compile(
        r"\b[A-Z]:[\\/]Users[\\/][^\\/\r\n\"']+(?:[\\/][^\r\n\"']*)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<![A-Za-z0-9_])/(?:Users|home)/[^/\r\n\"']+(?:/[^\r\n\"']*)?",
        re.IGNORECASE,
    ),
)
EVIDENCE_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
    re.compile(
        r"\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*"
        r"[\"']?[A-Za-z0-9][A-Za-z0-9._-]{14,}[\"']?",
        re.IGNORECASE,
    ),
)


class HarnessFailure(RuntimeError):
    """Raised when an acceptance or isolation invariant is not satisfied."""


def _codex_environment(
    fake_home: Path, source: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Build an isolated child environment without unrelated user secrets."""

    inherited = os.environ if source is None else source
    environment = {
        name.upper(): value
        for name, value in inherited.items()
        if name.upper() in INHERITED_CODEX_ENVIRONMENT_NAMES
    }
    runtime_environment = fake_home / "runtime-environment"
    isolated_paths = {
        "APPDATA": runtime_environment / "appdata",
        "HOME": fake_home,
        "LOCALAPPDATA": runtime_environment / "local-appdata",
        "TEMP": runtime_environment / "temp",
        "TMP": runtime_environment / "temp",
        "TMPDIR": runtime_environment / "temp",
        "USERPROFILE": fake_home,
        "XDG_CACHE_HOME": runtime_environment / "xdg-cache",
        "XDG_CONFIG_HOME": runtime_environment / "xdg-config",
        "XDG_DATA_HOME": runtime_environment / "xdg-data",
        "XDG_STATE_HOME": runtime_environment / "xdg-state",
    }
    environment.update({name: str(path) for name, path in isolated_paths.items()})
    if fake_home.drive:
        environment["HOMEDRIVE"] = fake_home.drive
        environment["HOMEPATH"] = str(fake_home)[len(fake_home.drive) :]
    environment["CODEX_HOME"] = str(fake_home)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _sanitize_evidence(
    value: Any, *, symbolic_values: Mapping[str, str]
) -> Any:
    """Replace runtime locations before JSON evidence leaves the harness."""

    if isinstance(value, Mapping):
        return {
            key: _sanitize_evidence(item, symbolic_values=symbolic_values)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _sanitize_evidence(item, symbolic_values=symbolic_values)
            for item in value
        ]
    if isinstance(value, tuple):
        return tuple(
            _sanitize_evidence(item, symbolic_values=symbolic_values)
            for item in value
        )
    if not isinstance(value, str):
        return value

    sanitized = value
    replacements: dict[str, str] = {}
    for raw, symbol in symbolic_values.items():
        if not raw:
            continue
        replacements[raw] = symbol
        replacements[raw.replace("\\", "/")] = symbol
    flags = re.IGNORECASE if os.name == "nt" else 0
    for raw in sorted(replacements, key=len, reverse=True):
        sanitized = re.sub(
            re.escape(raw), replacements[raw], sanitized, flags=flags
        )
    for pattern in PRIVATE_HOME_PATH_PATTERNS:
        sanitized = pattern.sub("<PRIVATE_PATH>", sanitized)
    for pattern in EVIDENCE_SECRET_PATTERNS:
        sanitized = pattern.sub("<REDACTED_SECRET>", sanitized)
    return sanitized


def _evidence_symbolic_values(
    *,
    fake_home: Path,
    acceptance_root: Path,
    real_home: Path,
    repo_root: Path,
    temp_parent: Path,
    codex_command: str,
    python_command: str,
) -> dict[str, str]:
    values = {
        str(fake_home): "<FAKE_CODEX_HOME>",
        str(acceptance_root): "<ACCEPTANCE_ROOT>",
        str(real_home): "<REAL_CODEX_HOME>",
        str(repo_root): "<REPOSITORY_ROOT>",
        str(temp_parent): "<TEMP_PARENT>",
    }
    for command, symbol in (
        (codex_command, "<CODEX_COMMAND>"),
        (python_command, "<PYTHON_COMMAND>"),
    ):
        if Path(command).is_absolute():
            values[str(Path(command))] = symbol
    return values


def _run(
    args: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    input_text: str | None = None,
    timeout: int = 900,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        args,
        cwd=cwd,
        env=dict(env) if env is not None else None,
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise HarnessFailure(
            f"command failed ({completed.returncode}): {args[0]} {stderr}"
        )
    return completed


def _sha256_file(path: Path) -> str:
    before = path.stat(follow_symlinks=False)
    if before.st_size == 0:
        after = path.stat(follow_symlinks=False)
        if (
            after.st_size == 0
            and (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
            and before.st_mtime_ns == after.st_mtime_ns
        ):
            return hashlib.sha256(b"").hexdigest().upper()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _is_reparse_point(path: Path) -> bool:
    details = path.lstat()
    attributes = getattr(details, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    is_junction = getattr(os.path, "isjunction", lambda _: False)
    return path.is_symlink() or is_junction(path) or bool(attributes & reparse_flag)


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _paths_overlap(left: Path, right: Path) -> bool:
    return (
        left == right
        or left.is_relative_to(right)
        or right.is_relative_to(left)
    )


def _is_allowed_platform_root_alias(path: Path) -> bool:
    # macOS exposes /var as the platform-owned /private/var alias. Temporary
    # directories live below it, so rejecting this fixed root alias would make
    # otherwise plain system temp directories unusable.
    if sys.platform != "darwin" or path.as_posix() != "/var":
        return False
    try:
        return path.resolve(strict=True).as_posix() == "/private/var"
    except (OSError, RuntimeError):
        return False


def _assert_plain_ancestor_chain(path: Path) -> None:
    absolute = _absolute(path)
    chain = list(reversed((absolute, *absolute.parents)))
    anchor = Path(absolute.anchor)
    for candidate in chain:
        if not _lexists(candidate):
            continue
        if _is_reparse_point(candidate) and not _is_allowed_platform_root_alias(
            candidate
        ):
            raise HarnessFailure(f"reparse point found in path chain: {candidate}")
        if candidate != anchor and os.path.ismount(candidate):
            raise HarnessFailure(f"mount point found in path chain: {candidate}")


def _validate_temp_parent(temp_parent: Path, real_home: Path) -> Path:
    candidate = _absolute(temp_parent)
    if not _lexists(candidate):
        raise HarnessFailure("temp parent must be an existing directory")
    _assert_plain_ancestor_chain(candidate)
    if not candidate.is_dir():
        raise HarnessFailure("temp parent must be an existing directory")
    resolved = candidate.resolve(strict=True)
    real_resolved = real_home.resolve(strict=True)
    if _paths_overlap(resolved, real_resolved):
        raise HarnessFailure("temp parent overlaps real CODEX_HOME")
    return resolved


def _validate_planned_isolation_root(
    temp_parent: Path,
    acceptance_root: Path,
    fake_home: Path,
    real_home: Path,
) -> None:
    safe_parent = _validate_temp_parent(temp_parent, real_home)
    planned_root = _absolute(acceptance_root)
    planned_fake_home = _absolute(fake_home)
    if planned_root.parent.resolve(strict=True) != safe_parent:
        raise HarnessFailure("acceptance root is not a direct temp-parent child")
    if not planned_root.name.startswith(HARNESS_ROOT_PREFIX):
        raise HarnessFailure("acceptance root does not have the harness prefix")
    if _lexists(planned_root):
        raise HarnessFailure("acceptance root already exists")
    if planned_fake_home.parent != planned_root:
        raise HarnessFailure("fake CODEX_HOME is not inside the acceptance root")
    real_resolved = real_home.resolve(strict=True)
    for candidate in (planned_root, planned_fake_home):
        resolved = candidate.resolve(strict=False)
        if _paths_overlap(resolved, real_resolved):
            raise HarnessFailure("planned isolation path overlaps real CODEX_HOME")


def _walk_without_reparse(root: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        retained: list[str] = []
        for name in directories:
            candidate = current_path / name
            yield candidate
            if not _is_reparse_point(candidate):
                retained.append(name)
        directories[:] = retained
        for name in files:
            yield current_path / name


def _file_identity(path: Path) -> tuple[int, int, int]:
    details = path.stat(follow_symlinks=False)
    return details.st_dev, details.st_ino, details.st_nlink


def _missing_entry() -> dict[str, Any]:
    return {
        "type": "missing",
        "size": None,
        "mtime_ns": None,
        "device": None,
        "file_id": None,
        "link_count": None,
        "sha256": None,
        "reparse": False,
    }


def _snapshot_entry(path: Path) -> dict[str, Any]:
    """Capture one path without following links or exposing file contents."""

    if not _lexists(path):
        return _missing_entry()
    details = path.stat(follow_symlinks=False)
    reparse = _is_reparse_point(path)
    if reparse:
        kind = "reparse"
    elif stat.S_ISDIR(details.st_mode):
        kind = "directory"
    elif stat.S_ISREG(details.st_mode):
        kind = "file"
    else:
        kind = "other"
    entry: dict[str, Any] = {
        "type": kind,
        "size": details.st_size,
        "mtime_ns": details.st_mtime_ns,
        "device": details.st_dev,
        "file_id": details.st_ino,
        "link_count": details.st_nlink,
        "sha256": None,
        "reparse": reparse,
    }
    if kind == "file":
        for _ in range(3):
            before = path.stat(follow_symlinks=False)
            digest = _sha256_file(path)
            after = path.stat(follow_symlinks=False)
            before_identity = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_nlink,
            )
            after_identity = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_nlink,
            )
            if before_identity == after_identity:
                entry.update(
                    {
                        "size": after.st_size,
                        "mtime_ns": after.st_mtime_ns,
                        "device": after.st_dev,
                        "file_id": after.st_ino,
                        "link_count": after.st_nlink,
                        "sha256": digest,
                    }
                )
                return entry
        raise HarnessFailure(f"file changed while snapshotting: {path}")
    return entry


def _snapshot_file(path: Path) -> dict[str, Any]:
    _assert_plain_ancestor_chain(path.parent)
    return _snapshot_entry(path)


def _snapshot_runtime_entry(path: Path) -> dict[str, Any]:
    """Capture volatile allowed runtime metadata without requiring stable bytes."""

    for _ in range(3):
        try:
            if not _lexists(path):
                return _missing_entry()
            details = path.stat(follow_symlinks=False)
            reparse = _is_reparse_point(path)
            if reparse:
                kind = "reparse"
            elif stat.S_ISDIR(details.st_mode):
                kind = "directory"
            elif stat.S_ISREG(details.st_mode):
                kind = "file"
            else:
                kind = "other"
            return {
                "type": kind,
                "size": details.st_size,
                "mtime_ns": details.st_mtime_ns,
                "device": details.st_dev,
                "file_id": details.st_ino,
                "link_count": details.st_nlink,
                "sha256": None,
                "reparse": reparse,
            }
        except FileNotFoundError:
            continue
    return _missing_entry()


def _fingerprint_paths(root: Path, relatives: Iterable[str]) -> str:
    records: list[str] = []
    for relative in relatives:
        target = root / relative
        if not target.exists():
            records.append(f"MISSING|{relative}")
            continue
        candidates = [target]
        if target.is_dir():
            candidates.extend(_walk_without_reparse(target))
        for candidate in candidates:
            rendered = candidate.relative_to(root).as_posix()
            details = candidate.lstat()
            if _is_reparse_point(candidate):
                records.append(
                    f"REPARSE|{rendered}|{details.st_mtime_ns}|{details.st_size}"
                )
            elif candidate.is_dir():
                records.append(f"DIR|{rendered}")
            elif candidate.is_file():
                records.append(
                    "|".join(
                        (
                            "FILE",
                            rendered,
                            str(details.st_size),
                            str(details.st_mtime_ns),
                            _sha256_file(candidate),
                        )
                    )
                )
    payload = "\n".join(sorted(records)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _fingerprint_tree(root: Path) -> str:
    if not root.exists():
        return hashlib.sha256(b"MISSING").hexdigest().upper()
    return _fingerprint_paths(root, (".",))


def _inventory_tree(
    root: Path,
    *,
    excluded_relatives: Iterable[str] = (),
    hash_file: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    if not _lexists(root):
        raise HarnessFailure(f"inventory root does not exist: {root}")
    exclusions = tuple(excluded_relatives)
    records: dict[str, dict[str, Any]] = {}
    files_to_hash: list[tuple[Path, str]] = []
    candidates = [root, *_walk_without_reparse(root)]
    for candidate in candidates:
        relative = "." if candidate == root else candidate.relative_to(root).as_posix()
        if any(
            relative == excluded or relative.startswith(f"{excluded}/")
            for excluded in exclusions
        ):
            continue
        details = candidate.stat(follow_symlinks=False)
        reparse = _is_reparse_point(candidate)
        if reparse:
            kind = "reparse"
        elif candidate.is_dir():
            kind = "directory"
        elif candidate.is_file():
            kind = "file"
        else:
            kind = "other"
        record: dict[str, Any] = {
            "type": kind,
            "size": details.st_size,
            "mtime_ns": details.st_mtime_ns,
            "device": details.st_dev,
            "file_id": details.st_ino,
            "link_count": details.st_nlink,
        }
        if kind == "reparse":
            try:
                record["target"] = os.readlink(candidate)
            except OSError:
                record["target"] = None
        if kind == "file" and (hash_file is None or hash_file(relative)):
            files_to_hash.append((candidate, relative))
        records[relative] = record

    def hash_stable_file(
        item: tuple[Path, str],
    ) -> tuple[str, str, os.stat_result]:
        candidate, relative = item
        for _ in range(3):
            before = candidate.stat(follow_symlinks=False)
            digest = _sha256_file(candidate)
            after = candidate.stat(follow_symlinks=False)
            before_identity = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_nlink,
            )
            after_identity = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_nlink,
            )
            if before_identity == after_identity:
                return relative, digest, after
        raise HarnessFailure(
            f"file changed while building real CODEX_HOME inventory: {relative}"
        )

    workers = min(16, max(4, (os.cpu_count() or 2) * 2))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for relative, digest, details in executor.map(
            hash_stable_file, files_to_hash
        ):
            records[relative].update(
                {
                    "size": details.st_size,
                    "mtime_ns": details.st_mtime_ns,
                    "device": details.st_dev,
                    "file_id": details.st_ino,
                    "link_count": details.st_nlink,
                    "sha256": digest,
                }
            )
    payload = json.dumps(
        records, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "hash": hashlib.sha256(payload).hexdigest().upper(),
        "entries": records,
        "entry_count": len(records),
        "file_count": sum(row["type"] == "file" for row in records.values()),
    }


def _inventory_summary(inventory: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "hash": inventory["hash"],
        "entry_count": inventory["entry_count"],
        "file_count": inventory["file_count"],
    }


def _changed_entry_paths(
    before: Mapping[str, Any], after: Mapping[str, Any] | None
) -> list[str]:
    if after is None:
        return ["<snapshot unavailable>"]
    before_entries = before["entries"]
    after_entries = after["entries"]
    return sorted(
        relative
        for relative in before_entries.keys() | after_entries.keys()
        if before_entries.get(relative) != after_entries.get(relative)
    )


def _is_under_relative_path(relative: str, root: str) -> bool:
    return relative == root or relative.startswith(f"{root}/")


def _is_sqlite_filename(relative: str) -> bool:
    name = relative.rsplit("/", 1)[-1].lower()
    return name.endswith((".sqlite", ".sqlite-wal", ".sqlite-shm"))


def _is_expected_sqlite_storage_filename(relative: str) -> bool:
    name = relative.rsplit("/", 1)[-1].lower()
    return name.endswith(
        (
            ".sqlite",
            ".sqlite-wal",
            ".sqlite-shm",
            ".sqlite-journal",
            ".db",
            ".db-wal",
            ".db-shm",
            ".db-journal",
        )
    )


def _is_protected_runtime_path(relative: str) -> bool:
    return any(
        _is_under_relative_path(relative, protected)
        for protected in PROTECTED_REAL_PATHS
        if protected in PROTECTED_REAL_TREE_PATHS
    ) or relative in {
        protected
        for protected in PROTECTED_REAL_PATHS
        if protected not in PROTECTED_REAL_TREE_PATHS
    }


def _is_session_runtime_path(relative: str) -> bool:
    explicit_path = any(
        _is_under_relative_path(relative, root)
        for root in SESSION_RUNTIME_TREE_PATHS
    ) or relative in SESSION_RUNTIME_FILE_PATHS
    if explicit_path:
        return True
    name = relative.rsplit("/", 1)[-1]
    return name in SESSION_RUNTIME_DISCOVERED_FILE_NAMES and any(
        relative.startswith(f"{root}/")
        for root in SESSION_RUNTIME_DISCOVERY_ROOTS
    )


def _is_session_runtime_metadata_directory(relative: str) -> bool:
    return any(
        relative == root
        or relative.startswith(f"{root}/")
        or root.startswith(f"{relative}/")
        for root in SESSION_RUNTIME_DISCOVERY_ROOTS
    )


def _is_local_storage_path(relative: str) -> bool:
    if relative in EXPLICIT_LOCAL_STORAGE_FILE_PATHS:
        return True
    if relative in ALL_LOCAL_STORAGE_TREE_PATHS:
        return True
    if any(
        _is_under_relative_path(relative, root)
        for root in EXPLICIT_LOCAL_STORAGE_CONTENT_TREE_PATHS
    ):
        return True
    if "/" not in relative and _is_sqlite_filename(relative):
        return True
    return any(
        _is_under_relative_path(relative, root)
        and _is_expected_sqlite_storage_filename(relative)
        for root in EXPLICIT_LOCAL_STORAGE_TREE_PATHS
    )


def _runtime_path_category(relative: str) -> str | None:
    if _is_protected_runtime_path(relative):
        return PROTECTED_SOL_LUNA_STATE
    if relative == AUTH_RUNTIME_RELATIVE or _is_session_runtime_path(relative):
        return CODEX_PLATFORM_RUNTIME_STATE
    if _is_local_storage_path(relative):
        return CODEX_LOCAL_STORAGE_STATE
    return None


def _snapshot_from_entries(records: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    normalized = {relative: dict(entry) for relative, entry in records.items()}
    payload = json.dumps(
        normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "hash": hashlib.sha256(payload).hexdigest().upper(),
        "entries": normalized,
        "entry_count": len(normalized),
        "file_count": sum(row["type"] == "file" for row in normalized.values()),
    }


def _snapshot_runtime_tree(
    real_home: Path,
    relative: str,
    *,
    include: Callable[[str], bool] | None = None,
) -> dict[str, dict[str, Any]]:
    target = real_home / relative
    if not _lexists(target):
        if include is None or include(relative):
            return {relative: _missing_entry()}
        return {}
    inventory = _inventory_tree(target, hash_file=lambda _: False)
    records: dict[str, dict[str, Any]] = {}
    for nested, entry in inventory["entries"].items():
        rendered = relative if nested == "." else f"{relative}/{nested}"
        if include is None or include(rendered):
            records[rendered] = dict(entry)
    return records


def _validate_runtime_entries(
    real_home: Path,
    entries: Mapping[str, Mapping[str, Any]],
    category: str,
) -> None:
    real_resolved = real_home.resolve(strict=True)
    for relative, entry in entries.items():
        if entry["type"] == "missing":
            continue
        if entry["type"] not in {"directory", "file"}:
            raise HarnessFailure(
                f"{category} runtime path has unsupported type: {relative}"
            )
        if (
            category == CODEX_PLATFORM_RUNTIME_STATE
            and relative in SESSION_RUNTIME_TREE_PATHS
            and entry["type"] != "directory"
        ) or (
            category == CODEX_LOCAL_STORAGE_STATE
            and relative in ALL_LOCAL_STORAGE_TREE_PATHS
            and entry["type"] != "directory"
        ):
            raise HarnessFailure(
                f"{category} runtime root is not a directory: {relative}"
            )
        target = real_home / relative
        try:
            _assert_plain_ancestor_chain(target)
            resolved = target.resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as exc:
            raise HarnessFailure(
                f"{category} path cannot be validated inside real CODEX_HOME: {relative}"
            ) from exc
        if entry["type"] == "reparse" or not resolved.is_relative_to(real_resolved):
            raise HarnessFailure(
                f"{category} path escapes real CODEX_HOME: {relative}"
            )
        if entry["type"] == "file" and entry["link_count"] != 1:
            raise HarnessFailure(
                f"{category} runtime file has unexpected hardlinks: {relative}"
            )


def _session_runtime_snapshot(real_home: Path) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    for relative in SESSION_RUNTIME_TREE_PATHS:
        records.update(_snapshot_runtime_tree(real_home, relative))
    for relative in SESSION_RUNTIME_FILE_PATHS:
        records[relative] = _snapshot_runtime_entry(real_home / relative)
    for relative in SESSION_RUNTIME_DISCOVERY_ROOTS:
        records.update(
            _snapshot_runtime_tree(
                real_home,
                relative,
                include=_is_session_runtime_path,
            )
        )
    snapshot = _snapshot_from_entries(records)
    _validate_runtime_entries(
        real_home, snapshot["entries"], CODEX_PLATFORM_RUNTIME_STATE
    )
    return snapshot


def _local_storage_snapshot(real_home: Path) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    for relative in EXPLICIT_LOCAL_STORAGE_FILE_PATHS:
        records[relative] = _snapshot_runtime_entry(real_home / relative)
    for relative in EXPLICIT_LOCAL_STORAGE_TREE_PATHS:
        records.update(
            _snapshot_runtime_tree(
                real_home,
                relative,
                include=_is_local_storage_path,
            )
        )
    for relative in EXPLICIT_LOCAL_STORAGE_CONTENT_TREE_PATHS:
        records.update(_snapshot_runtime_tree(real_home, relative))

    inventory = _inventory_tree(
        real_home,
        excluded_relatives=(
            AUTH_RUNTIME_RELATIVE,
            *EXPLICIT_SESSION_RUNTIME_PATHS,
            *EXPLICIT_LOCAL_STORAGE_CONTENT_TREE_PATHS,
        ),
        hash_file=lambda _: False,
    )
    for relative, entry in inventory["entries"].items():
        if _is_local_storage_path(relative):
            records[relative] = dict(entry)
    snapshot = _snapshot_from_entries(records)
    _validate_runtime_entries(
        real_home, snapshot["entries"], CODEX_LOCAL_STORAGE_STATE
    )
    return snapshot


def _unexpected_write_snapshot(real_home: Path) -> dict[str, Any]:
    """Snapshot unknown state without reading mutable auth content."""

    inventory = _inventory_tree(
        real_home,
        excluded_relatives=MUTABLE_REAL_PATHS,
        hash_file=lambda relative: not (
            _is_session_runtime_path(relative)
            or _is_local_storage_path(relative)
        ),
    )
    mutable_ancestors = {"."}
    for relative in (*MUTABLE_REAL_PATHS, *LOCAL_STORAGE_ANCESTOR_PATHS):
        parts = relative.split("/")
        mutable_ancestors.update(
            "/".join(parts[:index]) for index in range(1, len(parts))
        )
    records: dict[str, dict[str, Any]] = {}
    for relative, entry in inventory["entries"].items():
        if _is_session_runtime_path(relative):
            continue
        if _is_local_storage_path(relative):
            if relative in ALL_LOCAL_STORAGE_TREE_PATHS:
                records[relative] = {"type": "runtime-root"}
            continue
        sanitized = dict(entry)
        if sanitized["type"] == "directory" and (
            relative in mutable_ancestors
            or _is_session_runtime_metadata_directory(relative)
        ):
            sanitized.pop("size", None)
            sanitized.pop("mtime_ns", None)
            sanitized.pop("link_count", None)
        records[relative] = sanitized
    for relative in LOCAL_STORAGE_ANCESTOR_PATHS:
        if relative not in records:
            records[relative] = {"type": "runtime-root"}
    payload = json.dumps(
        records, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "hash": hashlib.sha256(payload).hexdigest().upper(),
        "entries": records,
        "entry_count": len(records),
        "file_count": sum(row["type"] == "file" for row in records.values()),
    }


def _protected_state_snapshot(real_home: Path) -> dict[str, Any]:
    """Snapshot only managed runtime state, excluding the auth allowlist."""

    records: dict[str, dict[str, Any]] = {}

    def add_entry(relative: str, target: Path) -> None:
        _assert_plain_ancestor_chain(target)
        entry = _snapshot_entry(target)
        records[relative] = entry

    def add_tree(relative: str, target: Path) -> None:
        _assert_plain_ancestor_chain(target)
        if not _lexists(target):
            records[relative] = _missing_entry()
            return
        inventory = _inventory_tree(target)
        for nested, entry in inventory["entries"].items():
            rendered = relative if nested == "." else f"{relative}/{nested}"
            sanitized = dict(entry)
            sanitized.pop("target", None)
            records[rendered] = sanitized

    for relative in PROTECTED_REAL_PATHS:
        target = real_home / relative
        if relative in PROTECTED_REAL_TREE_PATHS:
            add_tree(relative, target)
        else:
            add_entry(relative, target)

    payload = json.dumps(
        records, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "hash": hashlib.sha256(payload).hexdigest().upper(),
        "entries": records,
        "entry_count": len(records),
        "file_count": sum(row["type"] == "file" for row in records.values()),
    }


def _validate_protected_state_snapshot(snapshot: Mapping[str, Any]) -> None:
    for relative, entry in snapshot["entries"].items():
        if entry["type"] == "reparse":
            raise HarnessFailure(
                f"protected runtime path is a reparse point: {relative}"
            )
        if entry["type"] == "file" and entry["link_count"] != 1:
            raise HarnessFailure(
                f"protected runtime file has unexpected hardlinks: {relative}"
            )


def _auth_runtime_state_is_valid(
    auth_path: Path,
    real_home: Path,
    snapshot: Mapping[str, Any],
) -> bool:
    if snapshot.get("type") != "file" or snapshot.get("reparse"):
        return False
    try:
        _assert_plain_ancestor_chain(auth_path)
        if os.path.ismount(auth_path):
            return False
        details = auth_path.stat(follow_symlinks=False)
        if not stat.S_ISREG(details.st_mode):
            return False
        if _is_reparse_point(auth_path) or details.st_nlink != 1:
            return False
        real_resolved = real_home.resolve(strict=True)
        auth_resolved = auth_path.resolve(strict=True)
        if auth_resolved.parent != real_resolved:
            return False
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def _classify_auth_runtime_change(
    *,
    auth_path: Path,
    real_home: Path,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> str:
    if not _auth_runtime_state_is_valid(auth_path, real_home, before):
        return AUTH_RUNTIME_STATE_INVALID
    if not _auth_runtime_state_is_valid(auth_path, real_home, after):
        return AUTH_RUNTIME_STATE_INVALID
    if dict(before) == dict(after):
        return AUTH_UNCHANGED
    return AUTH_RUNTIME_REFRESH_OBSERVED


def _plain_real_home_identity(real_home: Path) -> tuple[int, int]:
    _assert_plain_ancestor_chain(real_home)
    if not _lexists(real_home) or _is_reparse_point(real_home):
        raise HarnessFailure("real CODEX_HOME must remain a plain directory")
    if os.path.ismount(real_home) or not real_home.is_dir():
        raise HarnessFailure("real CODEX_HOME must remain a plain directory")
    return _file_identity(real_home)[:2]


def _assert_independent_auth(real_auth: Path, fake_auth: Path) -> None:
    if _is_reparse_point(fake_auth):
        raise HarnessFailure("fake auth.json is a reparse point")
    real_device, real_file_id, _ = _file_identity(real_auth)
    fake_device, fake_file_id, fake_links = _file_identity(fake_auth)
    if fake_links != 1:
        raise HarnessFailure("fake auth.json has more than one hardlink")
    if (real_device, real_file_id) == (fake_device, fake_file_id):
        raise HarnessFailure("fake auth.json shares the real auth.json file ID")
    if _sha256_file(real_auth) != _sha256_file(fake_auth):
        raise HarnessFailure("fake auth.json copy is not byte-identical at creation")


def _file_ids(root: Path) -> set[tuple[int, int]]:
    identities: set[tuple[int, int]] = set()
    for candidate in _walk_without_reparse(root):
        if _is_reparse_point(candidate) or not candidate.is_file():
            continue
        details = candidate.stat(follow_symlinks=False)
        identities.add((details.st_dev, details.st_ino))
    return identities


def _assert_no_redirection(fake_home: Path, real_home: Path) -> None:
    if not _lexists(fake_home):
        raise HarnessFailure(f"isolation path does not exist: {fake_home}")
    _assert_plain_ancestor_chain(fake_home)
    if _is_reparse_point(fake_home):
        raise HarnessFailure(f"reparse point found in isolation path: {fake_home}")
    if os.path.ismount(fake_home):
        raise HarnessFailure(f"mount point found in isolation path: {fake_home}")
    fake_resolved = fake_home.resolve(strict=True)
    real_resolved = real_home.resolve(strict=True)
    if _paths_overlap(fake_resolved, real_resolved):
        raise HarnessFailure("isolation path resolves into or contains real CODEX_HOME")
    candidates = list(_walk_without_reparse(fake_home))
    hardlinked: list[Path] = []
    for candidate in candidates:
        if _is_reparse_point(candidate):
            raise HarnessFailure(f"reparse point found in isolation path: {candidate}")
        if os.path.ismount(candidate):
            raise HarnessFailure(f"mount point found in isolation path: {candidate}")
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(fake_resolved):
            raise HarnessFailure(f"isolated path resolves outside its root: {candidate}")
        if candidate.is_file() and candidate.stat(follow_symlinks=False).st_nlink != 1:
            hardlinked.append(candidate)
    overlap = _file_ids(fake_home) & _file_ids(real_home)
    if overlap:
        raise HarnessFailure("fake CODEX_HOME contains a hardlink to real CODEX_HOME")
    if hardlinked:
        raise HarnessFailure(f"hardlink found in isolation path: {hardlinked[0]}")


def _copy_auth_exclusive(real_auth: Path, fake_auth: Path) -> None:
    real_snapshot = _snapshot_file(real_auth)
    if not _auth_runtime_state_is_valid(
        real_auth, real_auth.parent, real_snapshot
    ):
        raise HarnessFailure("real auth.json runtime state is invalid before copy")
    if _lexists(fake_auth):
        raise HarnessFailure("fake auth.json already exists before isolated copy")
    try:
        with real_auth.open("rb") as source, fake_auth.open("xb") as destination:
            shutil.copyfileobj(source, destination)
    except FileExistsError as exc:
        raise HarnessFailure(
            "fake auth.json appeared before isolated copy"
        ) from exc


def _assert_safe_apply_target(
    acceptance_root: Path, fake_home: Path, real_home: Path
) -> None:
    _assert_no_redirection(acceptance_root, real_home)
    root_resolved = acceptance_root.resolve(strict=True)
    if _lexists(fake_home):
        _assert_no_redirection(fake_home, real_home)
        return
    _assert_plain_ancestor_chain(fake_home.parent)
    planned = fake_home.resolve(strict=False)
    if planned.parent != root_resolved:
        raise HarnessFailure("planned fake CODEX_HOME escapes the acceptance root")
    if _paths_overlap(planned, real_home.resolve(strict=True)):
        raise HarnessFailure("planned fake CODEX_HOME overlaps real CODEX_HOME")


def _apply_isolated_runtime(
    *,
    python_command: str,
    source_root: Path,
    source_commit: str,
    acceptance_root: Path,
    fake_home: Path,
    real_home: Path,
) -> subprocess.CompletedProcess[str]:
    _assert_safe_apply_target(acceptance_root, fake_home, real_home)
    return _run(
        [
            python_command,
            "scripts/install.py",
            "--apply",
            "--codex-home",
            str(fake_home),
            "--source-commit",
            source_commit,
        ],
        cwd=source_root,
    )


def _track_artifact(artifacts: dict[str, Any], path: Path) -> None:
    rendered = str(path)
    if rendered not in artifacts["created"]:
        artifacts["created"].append(rendered)


def _remove_reparse_entry(path: Path) -> None:
    is_junction = getattr(os.path, "isjunction", lambda _: False)
    if path.is_symlink():
        path.unlink()
    elif is_junction(path) or path.is_dir():
        os.rmdir(path)
    else:
        path.unlink()


def _remove_owned_tree(path: Path) -> None:
    if _is_reparse_point(path):
        _remove_reparse_entry(path)
        return
    if os.path.ismount(path):
        raise HarnessFailure(f"refusing to traverse mounted cleanup path: {path}")
    if not path.is_dir():
        path.unlink()
        return
    with os.scandir(path) as entries:
        children = [Path(entry.path) for entry in entries]
    for child in children:
        if _is_reparse_point(child):
            _remove_reparse_entry(child)
        elif os.path.ismount(child):
            raise HarnessFailure(f"refusing to traverse mounted cleanup path: {child}")
        elif child.is_dir():
            _remove_owned_tree(child)
        else:
            child.unlink()
    path.rmdir()


def _cleanup_owned_acceptance_root(
    artifacts: dict[str, Any], ownership_token: str, root_identity: tuple[int, int]
) -> None:
    acceptance_root = Path(artifacts["harness_root"])
    temp_parent = Path(artifacts["temp_parent"])
    if acceptance_root.parent != temp_parent:
        raise HarnessFailure("cleanup target is not a direct temp-parent child")
    if not acceptance_root.name.startswith(HARNESS_ROOT_PREFIX):
        raise HarnessFailure("cleanup target does not have the harness prefix")
    if not _lexists(acceptance_root):
        artifacts["removed"] = list(artifacts["created"])
        artifacts["residual"] = []
        return
    if _is_reparse_point(acceptance_root) or os.path.ismount(acceptance_root):
        raise HarnessFailure("cleanup root identity is unsafe")
    current_identity = _file_identity(acceptance_root)[:2]
    if current_identity != root_identity:
        raise HarnessFailure("cleanup root identity changed")
    marker = acceptance_root / OWNERSHIP_MARKER
    if not marker.is_file() or _is_reparse_point(marker):
        raise HarnessFailure("cleanup ownership marker is missing or unsafe")
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    if (
        marker_payload.get("schema") != OWNERSHIP_SCHEMA
        or marker_payload.get("token") != ownership_token
        or marker_payload.get("root") != str(acceptance_root)
    ):
        raise HarnessFailure("cleanup ownership marker does not match this run")
    _remove_owned_tree(acceptance_root)
    artifacts["removed"] = [
        item for item in artifacts["created"] if not _lexists(Path(item))
    ]
    artifacts["residual"] = [
        item for item in artifacts["created"] if _lexists(Path(item))
    ]
    if _lexists(acceptance_root) or artifacts["residual"]:
        raise HarnessFailure("acceptance artifacts remain after cleanup")


@contextmanager
def _owned_acceptance_directory(
    *,
    temp_parent: Path,
    acceptance_root: Path,
    fake_home: Path,
    real_home: Path,
    artifacts: dict[str, Any],
) -> Iterator[dict[str, Any]]:
    _validate_planned_isolation_root(
        temp_parent, acceptance_root, fake_home, real_home
    )
    acceptance_root.mkdir(parents=False, exist_ok=False)
    marker = acceptance_root / OWNERSHIP_MARKER
    try:
        if _is_reparse_point(acceptance_root) or os.path.ismount(acceptance_root):
            raise HarnessFailure("new acceptance root is not a plain directory")
        if (
            acceptance_root.resolve(strict=True).parent
            != temp_parent.resolve(strict=True)
        ):
            raise HarnessFailure("new acceptance root escaped temp parent")
        root_identity = _file_identity(acceptance_root)[:2]
        ownership_token = uuid.uuid4().hex
        marker.write_text(
            json.dumps(
                {
                    "schema": OWNERSHIP_SCHEMA,
                    "token": ownership_token,
                    "root": str(acceptance_root),
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    except Exception:
        if _lexists(marker) and not _is_reparse_point(marker):
            marker.unlink()
        if _lexists(acceptance_root) and not any(acceptance_root.iterdir()):
            acceptance_root.rmdir()
        raise
    artifacts.update(
        {
            "harness_root": str(acceptance_root),
            "temp_parent": str(temp_parent),
            "created": [],
            "removed": [],
            "residual": [],
        }
    )
    _track_artifact(artifacts, acceptance_root)
    _track_artifact(artifacts, marker)
    try:
        yield artifacts
    finally:
        _cleanup_owned_acceptance_root(artifacts, ownership_token, root_identity)


def _run_with_real_home_audit(
    *,
    label: str,
    real_home: Path,
    audits: dict[str, Any],
    action: Callable[[], Any],
    expected_home_identity: tuple[int, int] | None = None,
) -> Any:
    before = _protected_state_snapshot(real_home)
    before_auth = _snapshot_file(real_home / AUTH_RUNTIME_RELATIVE)
    before_sessions = _session_runtime_snapshot(real_home)
    before_local_storage = _local_storage_snapshot(real_home)
    before_unexpected = _unexpected_write_snapshot(real_home)
    before_home_identity = (
        expected_home_identity
        if expected_home_identity is not None
        else _plain_real_home_identity(real_home)
    )
    action_error: BaseException | None = None
    outcome: Any = None
    try:
        outcome = action()
    except BaseException as exc:
        action_error = exc
    after: dict[str, Any] | None = None
    after_protected_error: BaseException | None = None
    after_auth: dict[str, Any] | None = None
    after_auth_error: BaseException | None = None
    after_sessions: dict[str, Any] | None = None
    after_sessions_error: BaseException | None = None
    after_local_storage: dict[str, Any] | None = None
    after_local_storage_error: BaseException | None = None
    after_unexpected: dict[str, Any] | None = None
    after_unexpected_error: BaseException | None = None
    after_home_identity: tuple[int, int] | None = None
    after_home_error: BaseException | None = None
    try:
        after = _protected_state_snapshot(real_home)
    except BaseException as exc:
        after_protected_error = exc
    try:
        after_auth = _snapshot_file(real_home / AUTH_RUNTIME_RELATIVE)
    except BaseException as exc:
        after_auth_error = exc
    try:
        after_sessions = _session_runtime_snapshot(real_home)
    except BaseException as exc:
        after_sessions_error = exc
    try:
        after_local_storage = _local_storage_snapshot(real_home)
    except BaseException as exc:
        after_local_storage_error = exc
    try:
        after_unexpected = _unexpected_write_snapshot(real_home)
    except BaseException as exc:
        after_unexpected_error = exc
    try:
        after_home_identity = _plain_real_home_identity(real_home)
    except BaseException as exc:
        after_home_error = exc
    protected_unchanged = (
        after_protected_error is None
        and after is not None
        and before["entries"] == after["entries"]
    )
    home_identity_unchanged = (
        after_home_error is None
        and after_home_identity is not None
        and after_home_identity == before_home_identity
    )
    unexpected_write_absent = (
        after_unexpected_error is None
        and after_unexpected is not None
        and before_unexpected["entries"] == after_unexpected["entries"]
    )
    unexpected_changed_paths = _changed_entry_paths(
        before_unexpected, after_unexpected
    )
    session_runtime_state_valid = (
        after_sessions_error is None and after_sessions is not None
    )
    local_storage_state_valid = (
        after_local_storage_error is None and after_local_storage is not None
    )
    session_runtime_activity = (
        after_sessions is not None
        and before_sessions["entries"] != after_sessions["entries"]
    )
    local_storage_activity = (
        after_local_storage is not None
        and before_local_storage["entries"] != after_local_storage["entries"]
    )
    if (
        after_protected_error is not None
        or after_unexpected_error is not None
        or after_home_error is not None
        or not home_identity_unchanged
    ):
        auth_classification = UNEXPECTED_WRITE
    elif not protected_unchanged or not unexpected_write_absent:
        auth_classification = UNEXPECTED_WRITE
    elif after_auth_error is not None or after_auth is None:
        auth_classification = AUTH_RUNTIME_STATE_INVALID
    else:
        auth_classification = _classify_auth_runtime_change(
            auth_path=real_home / "auth.json",
            real_home=real_home,
            before=before_auth,
            after=after_auth,
        )
    activity_categories: list[str] = []
    if auth_classification == AUTH_RUNTIME_REFRESH_OBSERVED:
        activity_categories.append(AUTH_RUNTIME_ACTIVITY)
    if session_runtime_activity:
        activity_categories.append(SESSION_RUNTIME_ACTIVITY)
    if local_storage_activity:
        activity_categories.append(LOCAL_STORAGE_ACTIVITY)
    activity_category: str | list[str] | None
    if (
        after_protected_error is not None
        or after_unexpected_error is not None
        or after_home_error is not None
        or not home_identity_unchanged
        or not protected_unchanged
        or not unexpected_write_absent
        or auth_classification == AUTH_RUNTIME_STATE_INVALID
        or not session_runtime_state_valid
        or not local_storage_state_valid
    ):
        activity_category = UNEXPECTED_WRITE
    elif len(activity_categories) == 1:
        activity_category = activity_categories[0]
    elif activity_categories:
        activity_category = activity_categories
    else:
        activity_category = None
    audits[label] = {
        "before": _inventory_summary(before),
        "after": _inventory_summary(after) if after is not None else None,
        "byte_identical": protected_unchanged,
        "protected_state_unchanged": protected_unchanged,
        "auth_classification": auth_classification,
        "activity_category": activity_category,
        "activity_categories": activity_categories,
        "classification": activity_category,
        "session_runtime_activity": session_runtime_activity,
        "local_storage_activity": local_storage_activity,
        "session_runtime_state_valid": session_runtime_state_valid,
        "local_storage_state_valid": local_storage_state_valid,
        "real_home_identity_unchanged": home_identity_unchanged,
        "unexpected_write_absent": unexpected_write_absent,
        "unexpected_changed_paths": unexpected_changed_paths,
    }
    if (
        after_protected_error is not None
        or after_home_error is not None
        or not home_identity_unchanged
    ):
        raise HarnessFailure(
            f"real CODEX_HOME protected state could not be validated during {label}"
        ) from after_protected_error or after_home_error or action_error
    if not protected_unchanged:
        raise HarnessFailure(
            f"real CODEX_HOME protected state changed during {label}"
        ) from action_error
    if after_unexpected_error is not None:
        raise HarnessFailure(
            f"real CODEX_HOME unknown state could not be validated during {label}"
        ) from after_unexpected_error
    if not unexpected_write_absent:
        raise HarnessFailure(
            f"unexpected write outside the runtime allowlist during {label}"
        ) from action_error
    if auth_classification == AUTH_RUNTIME_STATE_INVALID:
        raise HarnessFailure(
            f"real auth.json runtime state is invalid during {label}"
        ) from action_error
    if not session_runtime_state_valid or not local_storage_state_valid:
        raise HarnessFailure(
            f"real CODEX_HOME runtime state is invalid during {label}"
        ) from action_error
    if action_error is not None:
        raise action_error
    return outcome


def _load_json_lines(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records


def _session_metadata(records: list[dict[str, Any]]) -> dict[str, Any]:
    for record in records:
        if record.get("type") == "session_meta":
            return record["payload"]
    raise HarnessFailure("rollout is missing session_meta")


def _turn_context(records: list[dict[str, Any]]) -> dict[str, Any]:
    for record in records:
        if record.get("type") == "turn_context":
            return record["payload"]
    raise HarnessFailure("rollout is missing turn_context")


def _final_assistant_text(records: list[dict[str, Any]]) -> str:
    final = ""
    for record in records:
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload", {})
        if payload.get("type") != "message" or payload.get("role") != "assistant":
            continue
        text = "".join(
            block.get("text", "")
            for block in payload.get("content", [])
            if isinstance(block, dict)
        )
        if text:
            final = text
    return final.strip()


def _tool_calls(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for record in records:
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload", {})
        if payload.get("type") in {"function_call", "custom_tool_call"}:
            calls.append(payload)
    return calls


def _rollout_files(fake_home: Path) -> set[Path]:
    return set((fake_home / "sessions").glob("**/*.jsonl"))


def _validate_runtime_case(
    rollout_paths: set[Path],
    *,
    expected_role: str,
    expected_effort: str,
    expected_literal: str,
    expected_receipt: str,
) -> dict[str, Any]:
    rollouts = {path: _load_json_lines(path) for path in rollout_paths}
    metadata = {path: _session_metadata(records) for path, records in rollouts.items()}
    parent_candidates = [
        path
        for path, meta in metadata.items()
        if not meta.get("parent_thread_id") and not meta.get("agent_role")
    ]
    if len(parent_candidates) != 1:
        raise HarnessFailure(
            f"expected one parent rollout, found {len(parent_candidates)}"
        )
    parent_path = parent_candidates[0]
    parent_meta = metadata[parent_path]
    parent_id = parent_meta.get("id")
    children = [
        path
        for path, meta in metadata.items()
        if meta.get("parent_thread_id") == parent_id
    ]
    if len(children) != 1:
        raise HarnessFailure(f"expected one direct child, found {len(children)}")
    child_path = children[0]
    child_meta = metadata[child_path]
    child_id = child_meta.get("id")
    grandchildren = [
        path
        for path, meta in metadata.items()
        if meta.get("parent_thread_id") == child_id
    ]
    if grandchildren:
        raise HarnessFailure("child spawned a descendant")

    parent_calls = _tool_calls(rollouts[parent_path])
    parent_names = [call.get("name") for call in parent_calls]
    if set(parent_names) - ALLOWED_RECEIPT_TOOLS:
        raise HarnessFailure(f"unexpected parent tool calls: {parent_names}")
    spawn_calls = [call for call in parent_calls if call.get("name") == "spawn_agent"]
    if len(spawn_calls) != 1:
        raise HarnessFailure(f"expected one spawn_agent call, found {len(spawn_calls)}")
    spawn_arguments = json.loads(spawn_calls[0].get("arguments", "{}"))
    if spawn_arguments.get("agent_type") != expected_role:
        raise HarnessFailure("spawned child role does not match saved selection")
    if _tool_calls(rollouts[child_path]):
        raise HarnessFailure("bounded child unexpectedly used a tool")

    source = child_meta.get("source", {}).get("subagent", {}).get("thread_spawn", {})
    context = _turn_context(rollouts[child_path])
    if child_meta.get("agent_role") != expected_role:
        raise HarnessFailure("child session role mismatch")
    if source.get("depth") != 1:
        raise HarnessFailure("child depth is not 1")
    if context.get("model") != "gpt-5.6-luna":
        raise HarnessFailure("child model is not gpt-5.6-luna")
    if context.get("effort") != expected_effort:
        raise HarnessFailure("child effort mismatch")
    if child_meta.get("multi_agent_version") != "disabled":
        raise HarnessFailure("child native-leaf multi-agent setting is not disabled")
    if _final_assistant_text(rollouts[child_path]) != expected_literal:
        raise HarnessFailure("child did not return the exact acceptance literal")

    parent_final = _final_assistant_text(rollouts[parent_path])
    lines = [line.strip() for line in parent_final.splitlines() if line.strip()]
    if not lines or lines[-1] != expected_receipt:
        raise HarnessFailure("parent Receipt does not match the saved selection")
    return {
        "result": "PASS",
        "child": {
            "role": expected_role,
            "model": context["model"],
            "effort": context["effort"],
            "depth": source["depth"],
            "direct_child_count": 1,
            "grandchild_count": 0,
        },
        "receipt": expected_receipt,
        "extra_selector": 0,
        "extra_network": 0,
        "extra_state": 0,
        "parent_tool_calls": parent_names,
    }


def _run_codex_case(
    *,
    codex_command: str,
    fake_home: Path,
    workspace: Path,
    evidence_dir: Path,
    case_name: str,
    prompt: str,
    state_dir: Path,
    expected_role: str,
    expected_effort: str,
    expected_literal: str,
    expected_receipt: str,
) -> dict[str, Any]:
    before_rollouts = _rollout_files(fake_home)
    state_before = _fingerprint_tree(state_dir)
    environment = _codex_environment(fake_home)
    for name in (
        "APPDATA",
        "LOCALAPPDATA",
        "TEMP",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
    ):
        Path(environment[name]).mkdir(parents=True, exist_ok=True)
    completed = _run(
        [
            codex_command,
            "exec",
            "--json",
            "--skip-git-repo-check",
            "-s",
            "read-only",
            "-C",
            str(workspace),
            "-",
        ],
        cwd=workspace,
        env=environment,
        input_text=prompt,
    )
    (evidence_dir / f"{case_name}.stdout.jsonl").write_text(
        completed.stdout, encoding="utf-8"
    )
    (evidence_dir / f"{case_name}.stderr.txt").write_text(
        completed.stderr, encoding="utf-8"
    )
    state_after = _fingerprint_tree(state_dir)
    if state_before != state_after:
        raise HarnessFailure(f"{case_name} Receipt work changed selector state")
    new_rollouts = _rollout_files(fake_home) - before_rollouts
    result = _validate_runtime_case(
        new_rollouts,
        expected_role=expected_role,
        expected_effort=expected_effort,
        expected_literal=expected_literal,
        expected_receipt=expected_receipt,
    )
    result["state_hash_before"] = state_before
    result["state_hash_after"] = state_after
    return result


def _load_selector(selector_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("rc5_acceptance_selector", selector_path)
    if spec is None or spec.loader is None:
        raise HarnessFailure("could not load isolated selector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ensure_selection(
    python_command: str,
    selector_path: Path,
    snapshot_path: Path,
    state_dir: Path,
    *,
    supported: str | None = None,
) -> dict[str, Any]:
    args = [
        python_command,
        str(selector_path),
        "--snapshot",
        str(snapshot_path),
        "--state-dir",
        str(state_dir),
        "--ensure-daily",
    ]
    if supported is not None:
        args.extend(("--supported", supported))
    args.append("--print-selection")
    completed = _run(args, cwd=selector_path.parent)
    return json.loads(completed.stdout)


def _selection_prompt(
    *,
    case_name: str,
    selection: Mapping[str, Any],
    role: str,
    literal: str,
    receipt: str,
) -> str:
    saved_selection = json.dumps(selection, sort_keys=True, separators=(",", ":"))
    return f"""Controlled RC5 {case_name} runtime acceptance.
The process CODEX_HOME, authentication, config, agents, manifest, state, sessions,
workspace, and evidence are all inside one independent fake CODEX_HOME. Do not
inspect or modify any path outside the current workspace. Do not run selector,
status, diagnostics, installer, release discovery, shell, file, or web/network
tools.

Saved single-call selection JSON:
{saved_selection}

Spawn exactly one direct native custom-agent child with agent_type {role} and
fork_turns \"none\". The child task is to return exactly {literal}, use no tools,
and spawn no descendants. Explicitly wait until the child is completed. If it is
interrupted or failed, say FAIL and do not emit a delegated Receipt. Do not spawn
another child.

If and only if the child completed with the exact literal, state that fact and
make the final line exactly:
{receipt}

Generate the Receipt solely from the saved selection and observed child result.
Receipt generation must perform zero selector calls, zero extra network/probe
calls, zero selector-state reads/writes, and zero extra child work.
"""


def _run_o9_fail_soft(
    *, selector_path: Path, fake_home: Path, snapshot_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    selector = _load_selector(selector_path)
    source_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    results: dict[str, Any] = {}
    selected_profile: dict[str, Any] | None = None
    for mode in ("missing", "invalid"):
        payload = copy.deepcopy(source_payload)
        for row in payload["rankings"]:
            if mode == "missing":
                row.pop("estimatedReferenceCostUsd", None)
            elif (
                row.get("model") == "gpt-5.6-luna"
                and row.get("reasoningEffort") == "max"
            ):
                row["estimatedReferenceCostUsd"] = "invalid-cost"
        adapted = selector.adapt_modeldial_api(
            payload, source_url=f"controlled-{mode}-cost"
        )
        state_dir = fake_home / "sol-luna-v4" / "acceptance-state" / f"o9-{mode}"
        profile = selector.ensure_daily_profile(adapted, state_dir=state_dir)
        status = selector.read_status(codex_home=fake_home, state_dir=state_dir)
        if profile.get("selected_role") != "luna_max":
            raise HarnessFailure(f"O9 {mode} cost changed selection")
        if "reference_cost_comparison" in profile:
            raise HarnessFailure(f"O9 {mode} cost did not omit ref-cost metadata")
        if status.get("health") != "Healthy":
            raise HarnessFailure(f"O9 {mode} cost status is not Healthy")
        if status.get("reference_cost_metadata_available") is not False:
            raise HarnessFailure(f"O9 {mode} cost status exposed ref-cost metadata")
        results[mode] = {
            "selection": "OK",
            "role": profile["selected_role"],
            "effort": profile["selected_effort"],
            "reference_cost": "omitted",
            "health": status["health"],
        }
        if mode == "missing":
            selected_profile = profile

    read_failure_state = (
        fake_home / "sol-luna-v4" / "acceptance-state" / "o9-read-failure"
    )
    state_existed_before = read_failure_state.exists()
    original_reader = selector._read_daily_profile
    selector._read_daily_profile = lambda _: ("READ_FAILED", None)
    try:
        read_failure = selector.read_status(
            codex_home=fake_home, state_dir=read_failure_state
        )
    finally:
        selector._read_daily_profile = original_reader
    if read_failure.get("health") != "Misconfigured":
        raise HarnessFailure("O9 read failure did not become Misconfigured")
    if "DAILY_PROFILE_READ_FAILED" not in read_failure.get("reason_codes", []):
        raise HarnessFailure("O9 read failure reason code is missing")
    if read_failure_state.exists() != state_existed_before:
        raise HarnessFailure("O9 read failure created selector state")
    results["read_failure"] = {
        "health": read_failure["health"],
        "reason_codes": read_failure["reason_codes"],
        "state_created": False,
    }
    if selected_profile is None:
        raise HarnessFailure("O9 missing-cost selection was not captured")
    return results, selected_profile


def _git_state(repo_root: Path) -> dict[str, str]:
    status = _run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo_root
    ).stdout
    head = _run(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()
    return {"head": head, "status": status}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--real-codex-home",
        required=True,
        type=Path,
        help="Real CODEX_HOME to protect and audit read-only",
    )
    parser.add_argument(
        "--source-commit",
        default=RC5_SOURCE_COMMIT,
        help="Immutable RC5 source commit used only to build the fake runtime",
    )
    parser.add_argument("--codex-command", default=shutil.which("codex") or "codex")
    parser.add_argument("--python-command", default=sys.executable)
    parser.add_argument("--temp-parent", type=Path, default=Path(tempfile.gettempdir()))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    real_home = args.real_codex_home.resolve(strict=True)
    real_home_identity = _plain_real_home_identity(real_home)
    real_auth = real_home / "auth.json"
    if not real_auth.is_file() or _is_reparse_point(real_auth):
        raise HarnessFailure("real auth.json must be an existing regular file")
    if _file_identity(real_auth)[2] != 1:
        raise HarnessFailure("real auth.json must not be hardlinked")
    temp_parent = _validate_temp_parent(args.temp_parent, real_home)

    protected_state = _protected_state_snapshot(real_home)
    _validate_protected_state_snapshot(protected_state)
    session_runtime = _session_runtime_snapshot(real_home)
    local_storage = _local_storage_snapshot(real_home)
    baseline = {
        "auth": _snapshot_file(real_auth),
        "protected": protected_state,
        "sessions": session_runtime,
        "local_storage": local_storage,
        "unexpected": _unexpected_write_snapshot(real_home),
        "repo": _git_state(repo_root),
    }
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    acceptance_root = temp_parent / (
        f"{HARNESS_ROOT_PREFIX}{stamp}-{os.getpid()}"
    )
    fake_home = acceptance_root / "codex-home"
    source_root = acceptance_root / "source"
    archive_path = acceptance_root / "source.tar"
    artifacts: dict[str, Any] = {
        "harness_root": str(acceptance_root),
        "temp_parent": str(temp_parent),
        "created": [],
        "removed": [],
        "residual": [],
    }

    result: dict[str, Any] = {
        "decision": "RC5_ACCEPTANCE_HARNESS_SECURITY_FAILED",
        "harness_root": str(acceptance_root),
        "real_codex_home": {
            "before_hash": baseline["protected"]["hash"],
            "after_hash": None,
            "before_inventory": _inventory_summary(baseline["protected"]),
            "before_protected_state": _inventory_summary(baseline["protected"]),
            "after_inventory": None,
            "after_protected_state": None,
            "auth_before": baseline["auth"],
            "auth_after": None,
            "auth_classification": None,
            "activity_category": None,
            "activity_categories": [],
            "classification": None,
            "session_runtime_before": _inventory_summary(baseline["sessions"]),
            "session_runtime_after": None,
            "local_storage_before": _inventory_summary(baseline["local_storage"]),
            "local_storage_after": None,
            "changed": None,
        },
        "product_runtime": {"rc5_code_modified": "NO"},
        "acceptance_audits": {},
        "artifacts": artifacts,
    }
    failure: str | None = None
    try:
        with _owned_acceptance_directory(
            temp_parent=temp_parent,
            acceptance_root=acceptance_root,
            fake_home=fake_home,
            real_home=real_home,
            artifacts=artifacts,
        ):
            source_root.mkdir()
            _track_artifact(artifacts, source_root)
            _run(
                [
                    "git",
                    "archive",
                    "--format=tar",
                    f"--output={archive_path}",
                    args.source_commit,
                ],
                cwd=repo_root,
            )
            _track_artifact(artifacts, archive_path)
            with tarfile.open(archive_path, "r") as archive:
                archive.extractall(source_root, filter="data")

            install = _apply_isolated_runtime(
                python_command=args.python_command,
                source_root=source_root,
                source_commit=args.source_commit,
                acceptance_root=acceptance_root,
                fake_home=fake_home,
                real_home=real_home,
            )
            install_result = json.loads(install.stdout)
            if install_result.get("status") not in {"INSTALLED", "UPGRADED"}:
                raise HarnessFailure("isolated RC5 install did not complete")
            _track_artifact(artifacts, fake_home)

            _assert_no_redirection(fake_home, real_home)
            fake_auth = fake_home / "auth.json"
            _copy_auth_exclusive(real_auth, fake_auth)
            _track_artifact(artifacts, fake_auth)
            _assert_independent_auth(real_auth, fake_auth)
            _assert_no_redirection(fake_home, real_home)

            selector_path = fake_home / "sol-luna-v4/selector.py"
            snapshot_path = source_root / "fixtures/modeldial/api-complete.json"
            workspace = fake_home / "acceptance-workspace"
            evidence_dir = fake_home / "acceptance-evidence"
            workspace.mkdir()
            evidence_dir.mkdir()

            o2_state = fake_home / "sol-luna-v4/acceptance-state/o2"
            o2_selection = _ensure_selection(
                args.python_command, selector_path, snapshot_path, o2_state
            )
            if (
                o2_selection.get("selected_role") != "luna_max"
                or o2_selection.get("selected_effort") != "max"
                or not o2_selection.get("reference_cost_comparison")
            ):
                raise HarnessFailure("O2 selection is not luna_max/max with ref-cost")
            o2_reduction = o2_selection["reference_cost_comparison"]["reduction_pct"]
            o2_receipt = (
                "Sol/Luna: delegated · luna_max ×1 · "
                f"Luna ref-cost ↓{o2_reduction:.1f}%"
            )
            o2_literal = "RC5-O2-LUNA-MAX-OK"
            result["o2"] = _run_with_real_home_audit(
                label="O2",
                real_home=real_home,
                audits=result["acceptance_audits"],
                expected_home_identity=real_home_identity,
                action=lambda: _run_codex_case(
                    codex_command=args.codex_command,
                    fake_home=fake_home,
                    workspace=workspace,
                    evidence_dir=evidence_dir,
                    case_name="O2",
                    prompt=_selection_prompt(
                        case_name="O2",
                        selection=o2_selection,
                        role="luna_max",
                        literal=o2_literal,
                        receipt=o2_receipt,
                    ),
                    state_dir=o2_state,
                    expected_role="luna_max",
                    expected_effort="max",
                    expected_literal=o2_literal,
                    expected_receipt=o2_receipt,
                ),
            )

            o4_state = fake_home / "sol-luna-v4/acceptance-state/o4"
            o4_selection = _ensure_selection(
                args.python_command,
                selector_path,
                snapshot_path,
                o4_state,
                supported="high,medium,low",
            )
            if (
                o4_selection.get("source_winner_effort") != "max"
                or o4_selection.get("selected_role") != "luna_high"
                or o4_selection.get("selected_effort") != "high"
                or o4_selection.get("capability_degraded") is not True
            ):
                raise HarnessFailure("O4 selection is not capability max to high")
            o4_reduction = o4_selection["reference_cost_comparison"]["reduction_pct"]
            o4_receipt = (
                "Sol/Luna: delegated · luna_high ×1 · "
                f"Luna ref-cost ↓{o4_reduction:.1f}% · capability max→high"
            )
            o4_literal = "RC5-O4-LUNA-HIGH-OK"
            result["o4"] = _run_with_real_home_audit(
                label="O4",
                real_home=real_home,
                audits=result["acceptance_audits"],
                expected_home_identity=real_home_identity,
                action=lambda: _run_codex_case(
                    codex_command=args.codex_command,
                    fake_home=fake_home,
                    workspace=workspace,
                    evidence_dir=evidence_dir,
                    case_name="O4",
                    prompt=_selection_prompt(
                        case_name="O4",
                        selection=o4_selection,
                        role="luna_high",
                        literal=o4_literal,
                        receipt=o4_receipt,
                    ),
                    state_dir=o4_state,
                    expected_role="luna_high",
                    expected_effort="high",
                    expected_literal=o4_literal,
                    expected_receipt=o4_receipt,
                ),
            )

            def run_o9() -> dict[str, Any]:
                o9_checks, o9_selection = _run_o9_fail_soft(
                    selector_path=selector_path,
                    fake_home=fake_home,
                    snapshot_path=snapshot_path,
                )
                o9_state = fake_home / "sol-luna-v4/acceptance-state/o9-missing"
                receipt_selection = {
                    key: o9_selection[key]
                    for key in (
                        "capability_degraded",
                        "fallback",
                        "selected_effort",
                        "selected_role",
                        "source_winner_effort",
                    )
                }
                o9_receipt = "Sol/Luna: delegated · luna_max ×1"
                o9_literal = "RC5-O9-FAIL-SOFT-OK"
                o9_receipt_result = _run_codex_case(
                    codex_command=args.codex_command,
                    fake_home=fake_home,
                    workspace=workspace,
                    evidence_dir=evidence_dir,
                    case_name="O9",
                    prompt=_selection_prompt(
                        case_name="O9",
                        selection=receipt_selection,
                        role="luna_max",
                        literal=o9_literal,
                        receipt=o9_receipt,
                    ),
                    state_dir=o9_state,
                    expected_role="luna_max",
                    expected_effort="max",
                    expected_literal=o9_literal,
                    expected_receipt=o9_receipt,
                )
                if "ref-cost" in o9_receipt_result["receipt"]:
                    raise HarnessFailure("O9 Receipt did not omit ref-cost")
                return {
                    "result": "PASS",
                    "fail_soft": o9_checks,
                    "receipt_case": o9_receipt_result,
                }

            result["o9"] = _run_with_real_home_audit(
                label="O9",
                real_home=real_home,
                audits=result["acceptance_audits"],
                expected_home_identity=real_home_identity,
                action=run_o9,
            )
            _assert_no_redirection(fake_home, real_home)
    except Exception as exc:  # final safety audit still runs on every failure
        failure = f"{type(exc).__name__}: {exc}"

    after_auth = _missing_entry()
    after_auth_error: BaseException | None = None
    try:
        after_auth = _snapshot_file(real_auth)
    except BaseException as exc:
        after_auth_error = exc

    after_protected: dict[str, Any] | None = None
    after_protected_error: BaseException | None = None
    try:
        after_protected = _protected_state_snapshot(real_home)
    except BaseException as exc:
        after_protected_error = exc

    after_unexpected: dict[str, Any] | None = None
    after_unexpected_error: BaseException | None = None
    try:
        after_unexpected = _unexpected_write_snapshot(real_home)
    except BaseException as exc:
        after_unexpected_error = exc

    after_sessions: dict[str, Any] | None = None
    after_sessions_error: BaseException | None = None
    try:
        after_sessions = _session_runtime_snapshot(real_home)
    except BaseException as exc:
        after_sessions_error = exc

    after_local_storage: dict[str, Any] | None = None
    after_local_storage_error: BaseException | None = None
    try:
        after_local_storage = _local_storage_snapshot(real_home)
    except BaseException as exc:
        after_local_storage_error = exc

    after_home_identity: tuple[int, int] | None = None
    after_home_error: BaseException | None = None
    try:
        after_home_identity = _plain_real_home_identity(real_home)
    except BaseException as exc:
        after_home_error = exc

    after = {
        "auth": after_auth,
        "protected": after_protected,
        "unexpected": after_unexpected,
        "repo": _git_state(repo_root),
    }
    result["real_codex_home"]["after_hash"] = (
        after_protected["hash"] if after_protected is not None else None
    )
    result["real_codex_home"]["after_inventory"] = (
        _inventory_summary(after_protected) if after_protected is not None else None
    )
    result["real_codex_home"]["after_protected_state"] = result["real_codex_home"][
        "after_inventory"
    ]
    result["real_codex_home"]["auth_after"] = after["auth"]
    result["real_codex_home"]["session_runtime_after"] = (
        _inventory_summary(after_sessions) if after_sessions is not None else None
    )
    result["real_codex_home"]["local_storage_after"] = (
        _inventory_summary(after_local_storage)
        if after_local_storage is not None
        else None
    )
    if after_protected is None or after_protected_error is not None:
        protected_state_unchanged = False
    else:
        protected_state_unchanged = (
            baseline["protected"]["entries"] == after_protected["entries"]
        )
    real_home_identity_unchanged = (
        after_home_error is None and after_home_identity == real_home_identity
    )
    unexpected_write_absent = (
        after_unexpected_error is None
        and after_unexpected is not None
        and baseline["unexpected"]["entries"] == after_unexpected["entries"]
    )
    unexpected_changed_paths = _changed_entry_paths(
        baseline["unexpected"], after_unexpected
    )
    session_runtime_state_valid = after_sessions_error is None
    local_storage_state_valid = after_local_storage_error is None
    session_runtime_activity = (
        after_sessions is not None
        and baseline["sessions"]["entries"] != after_sessions["entries"]
    )
    local_storage_activity = (
        after_local_storage is not None
        and baseline["local_storage"]["entries"]
        != after_local_storage["entries"]
    )
    if (
        after_protected_error is not None
        or after_unexpected_error is not None
        or after_home_error is not None
    ):
        auth_classification = UNEXPECTED_WRITE
    elif after_auth_error is not None:
        auth_classification = AUTH_RUNTIME_STATE_INVALID
    else:
        auth_classification = _classify_auth_runtime_change(
            auth_path=real_auth,
            real_home=real_home,
            before=baseline["auth"],
            after=after["auth"],
        )
        if (
            not protected_state_unchanged
            or not unexpected_write_absent
            or not real_home_identity_unchanged
            or not session_runtime_state_valid
            or not local_storage_state_valid
        ):
            auth_classification = UNEXPECTED_WRITE
    activity_categories: list[str] = []
    if auth_classification == AUTH_RUNTIME_REFRESH_OBSERVED:
        activity_categories.append(AUTH_RUNTIME_ACTIVITY)
    if session_runtime_activity:
        activity_categories.append(SESSION_RUNTIME_ACTIVITY)
    if local_storage_activity:
        activity_categories.append(LOCAL_STORAGE_ACTIVITY)
    if (
        after_protected_error is not None
        or after_unexpected_error is not None
        or after_home_error is not None
        or after_sessions_error is not None
        or after_local_storage_error is not None
        or not protected_state_unchanged
        or not unexpected_write_absent
        or not real_home_identity_unchanged
        or auth_classification == AUTH_RUNTIME_STATE_INVALID
    ):
        activity_category: str | list[str] | None = UNEXPECTED_WRITE
    elif len(activity_categories) == 1:
        activity_category = activity_categories[0]
    elif activity_categories:
        activity_category = activity_categories
    else:
        activity_category = None
    result["real_codex_home"]["auth_classification"] = auth_classification
    result["real_codex_home"]["activity_category"] = activity_category
    result["real_codex_home"]["activity_categories"] = activity_categories
    result["real_codex_home"]["classification"] = activity_category
    result["real_codex_home"][
        "unexpected_changed_paths"
    ] = unexpected_changed_paths
    auth_runtime_state_valid = auth_classification != AUTH_RUNTIME_STATE_INVALID
    auth_mutation_allowlisted = auth_classification in {
        AUTH_UNCHANGED,
        AUTH_RUNTIME_REFRESH_OBSERVED,
    }
    safety = {
        "protected_state_unchanged": protected_state_unchanged,
        "auth_runtime_state_valid": auth_runtime_state_valid,
        "auth_mutation_allowlisted": auth_mutation_allowlisted,
        "session_runtime_state_valid": session_runtime_state_valid,
        "local_storage_state_valid": local_storage_state_valid,
        "unexpected_write_absent": unexpected_write_absent,
        "real_home_identity_unchanged": real_home_identity_unchanged,
        "repo_identical_during_run": baseline["repo"] == after["repo"],
        "artifacts_removed": not artifacts["residual"]
        and not _lexists(acceptance_root),
    }
    result["safety"] = safety
    result["real_codex_home"]["changed"] = (
        auth_classification != AUTH_UNCHANGED
        or session_runtime_activity
        or local_storage_activity
        or not protected_state_unchanged
        or not unexpected_write_absent
        or not real_home_identity_unchanged
    )
    if failure is not None:
        result["failure"] = failure
    elif all(safety.values()) and all(
        result.get(case, {}).get("result") == "PASS" for case in ("o2", "o4", "o9")
    ):
        result["decision"] = "RC5_ACCEPTANCE_HARNESS_SECURITY_FIXED"

    symbolic_values = _evidence_symbolic_values(
        fake_home=fake_home,
        acceptance_root=acceptance_root,
        real_home=real_home,
        repo_root=repo_root,
        temp_parent=temp_parent,
        codex_command=args.codex_command,
        python_command=args.python_command,
    )
    sanitized_result = _sanitize_evidence(
        result, symbolic_values=symbolic_values
    )
    print(json.dumps(sanitized_result, indent=2, sort_keys=True))
    return (
        0
        if result["decision"] == "RC5_ACCEPTANCE_HARNESS_SECURITY_FIXED"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
