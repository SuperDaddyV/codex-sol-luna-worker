"""Plan and safely validate the v4 installer against an explicit CODEX_HOME."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_PLATFORMS = {"Windows", "Linux", "Darwin"}
VERSION = "v4.0.0"
MANIFEST_RELATIVE = PurePosixPath("sol-luna-v4/install-manifest.json")
LEGACY_MANIFEST_RELATIVE = PurePosixPath("sol-luna-router/install-manifest.json")
LEGACY_HOOKS_RELATIVE = ".".join(("hooks", "json"))
AGENTS_BEGIN = "<!-- BEGIN SOL_LUNA_V4 -->"
AGENTS_END = "<!-- END SOL_LUNA_V4 -->"
CONFIG_BEGIN = "# BEGIN SOL_LUNA_V4_CONFIG"
CONFIG_END = "# END SOL_LUNA_V4_CONFIG"
LEGACY_AGENTS_BEGIN = "<!-- BEGIN SOL_LUNA_DAILY_BEST -->"
LEGACY_AGENTS_END = "<!-- END SOL_LUNA_DAILY_BEST -->"
LEGACY_VERSION = "3.2"

STABLE_AGENT_FILES = (
    "luna-low.toml",
    "luna-medium.toml",
    "luna-high.toml",
    "luna-xhigh.toml",
    "luna-max.toml",
)

FUTURE_ARTIFACTS = (
    *(
        {
            "source": f".codex/agents/{filename}",
            "destination": f"agents/{filename}",
            "strategy": "agent-conflict-check",
            "kind": "stable-agent",
        }
        for filename in STABLE_AGENT_FILES
    ),
    {
        "source": "templates/AGENTS.global.md",
        "destination": "AGENTS.md",
        "strategy": "merge-policy",
        "kind": "delegation-policy",
    },
    {
        "source": "src/selector.py",
        "destination": "sol-luna-v4/selector.py",
        "strategy": "copy-if-owned",
        "kind": "daily-selector",
    },
    {
        "source": ".codex/config.toml",
        "destination": "config.toml",
        "strategy": "merge-agents-config",
        "kind": "minimum-config",
    },
)


class UnsafeTarget(ValueError):
    """Raised when a target path is unsafe."""


class InstallerError(RuntimeError):
    """A stable fail-closed installer error."""

    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_within(path: Path, parent: Path) -> bool:
    path = path.resolve(strict=False)
    parent = parent.resolve(strict=False)
    return path == parent or parent in path.parents


def resolve_codex_home(
    value: str | None,
    *,
    environ: Mapping[str, str] | None = None,
    user_home: Path | None = None,
) -> Path:
    environment = os.environ if environ is None else environ
    home = Path.home() if user_home is None else user_home
    raw = value or environment.get("CODEX_HOME") or str(home / ".codex")
    return Path(raw).expanduser().resolve(strict=False)


def validate_target(
    target: Path,
    project_root: Path = PROJECT_ROOT,
    *,
    allow_validation_sandbox: bool = False,
) -> None:
    target = target.resolve(strict=False)
    project_root = project_root.resolve(strict=False)
    if target == Path(target.anchor):
        raise UnsafeTarget("CODEX_HOME cannot be a filesystem root")
    if target == project_root or project_root in target.parents:
        sandbox = project_root / ".tmp" / "installer-validation"
        if not allow_validation_sandbox or not _is_within(target, sandbox):
            raise UnsafeTarget("CODEX_HOME cannot be inside the project repository")


def _target_path(target: Path, relative: str | PurePosixPath) -> Path:
    relative_path = PurePosixPath(str(relative).replace("\\", "/"))
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise InstallerError("OWNERSHIP_CONFLICT", "owned path escapes CODEX_HOME")
    path = target.joinpath(*relative_path.parts).resolve(strict=False)
    if not _is_within(path, target):
        raise InstallerError("OWNERSHIP_CONFLICT", "owned path escapes CODEX_HOME")
    return path


def _relative_path(target: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(target.resolve(strict=False)).as_posix()
    except ValueError as exc:
        raise InstallerError("OWNERSHIP_CONFLICT", "path is outside CODEX_HOME") from exc


def _codex_version() -> str:
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def build_plan(
    target: Path,
    *,
    project_root: Path = PROJECT_ROOT,
    platform_name: str | None = None,
    generated_at: datetime | None = None,
    allow_validation_sandbox: bool = False,
) -> dict:
    """Return the stable non-mutating v4 deployment inventory."""

    target = target.resolve(strict=False)
    project_root = project_root.resolve(strict=False)
    validate_target(
        target,
        project_root,
        allow_validation_sandbox=allow_validation_sandbox,
    )
    current_platform = platform.system() if platform_name is None else platform_name
    timestamp = (generated_at or _utc_now()).strftime("%Y%m%dT%H%M%SZ")

    actions = []
    conflicts = []
    source_dir = project_root / ".codex" / "agents"
    for filename in STABLE_AGENT_FILES:
        source = source_dir / filename
        destination = target / "agents" / filename
        if not source.exists():
            status = "missing-source"
        elif not destination.exists():
            status = "create"
        elif destination.is_file() and destination.read_bytes() == source.read_bytes():
            status = "identical"
        else:
            status = "conflict"
            conflicts.append(str(destination))
        actions.append(
            {"source": str(source), "destination": str(destination), "status": status}
        )

    return {
        "mode": "dry-run",
        "will_modify": False,
        "platform": current_platform,
        "platform_supported": current_platform in SUPPORTED_PLATFORMS,
        "codex_version": _codex_version(),
        "target_codex_home": str(target),
        "conflicts": conflicts,
        "backup_plan": {
            "required": bool(conflicts),
            "path": str(target / "backups" / "sol-luna-v4" / timestamp),
            "will_create": False,
        },
        "actions": actions,
        "future_artifacts": [
            {
                **artifact,
                "source_path": str(project_root / artifact["source"]),
                "destination_path": str(target / artifact["destination"]),
            }
            for artifact in FUTURE_ARTIFACTS
        ],
    }


def render_global_policy(
    template: str,
    codex_home: str | Path,
    *,
    platform_name: str | None = None,
) -> str:
    """Render the global policy with one safely quoted selector command."""

    current_platform = platform.system() if platform_name is None else platform_name
    if current_platform not in SUPPORTED_PLATFORMS:
        raise InstallerError("UNSUPPORTED_PLATFORM", "global policy platform is unsupported")
    raw_home = str(codex_home)
    if current_platform == "Windows":
        home = PureWindowsPath(raw_home)
        selector = str(home / "sol-luna-v4" / "selector.py")
        state = str(home / "sol-luna-v4" / "state")
        command = subprocess.list2cmdline(
            ["python", selector, "--state-dir", state, "--ensure-daily", "--print-role"]
        )
        rendered_home = str(home)
    else:
        home = PurePosixPath(raw_home.replace("\\", "/"))
        selector = str(home / "sol-luna-v4" / "selector.py")
        state = str(home / "sol-luna-v4" / "state")
        command = shlex.join(
            ["python", selector, "--state-dir", state, "--ensure-daily", "--print-role"]
        )
        rendered_home = str(home)
    rendered = template.replace("<SELECTOR_COMMAND>", command).replace(
        "<CODEX_HOME>", rendered_home
    )
    if "<SELECTOR_COMMAND>" in rendered or "<CODEX_HOME>" in rendered:
        raise InstallerError("POLICY_RENDER_FAILED", "global policy placeholder remains")
    return rendered


def _load_json(path: Path, reason_code: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstallerError(reason_code, f"cannot parse {path.name}") from exc
    if not isinstance(value, dict):
        raise InstallerError(reason_code, f"{path.name} must contain an object")
    return value


def _load_manifest(target: Path, *, required: bool = False) -> dict | None:
    path = _target_path(target, MANIFEST_RELATIVE)
    if not path.exists():
        if required:
            raise InstallerError("MANIFEST_MISSING", "v4 install manifest is missing")
        return None
    manifest = _load_json(path, "MANIFEST_INVALID")
    if not isinstance(manifest.get("owned_files", {}), dict):
        raise InstallerError("MANIFEST_INVALID", "owned_files must be an object")
    cleanup = manifest.get("legacy_cleanup")
    if cleanup is not None and (
        not isinstance(cleanup, dict)
        or cleanup.get("target") != LEGACY_MANIFEST_RELATIVE.as_posix()
        or cleanup.get("status") not in {"pending", "complete"}
    ):
        raise InstallerError("MANIFEST_INVALID", "legacy cleanup record is invalid")
    return manifest


def _owned_hash(manifest: dict | None, relative: str) -> str | None:
    if not manifest:
        return None
    value = manifest.get("owned_files", {}).get(relative)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        result = value.get("sha256")
        return result if isinstance(result, str) else None
    return None


def _marker_bounds(text: str, begin: str, end: str, reason_code: str) -> tuple[int, int] | None:
    begin_count = text.count(begin)
    end_count = text.count(end)
    if begin_count == 0 and end_count == 0:
        return None
    if begin_count != 1 or end_count != 1:
        raise InstallerError(reason_code, "owned marker count is invalid")
    start = text.index(begin)
    try:
        finish = text.index(end, start) + len(end)
    except ValueError as exc:
        raise InstallerError(reason_code, "owned marker order is invalid") from exc
    if finish <= start:
        raise InstallerError(reason_code, "owned marker order is invalid")
    if finish < len(text) and text[finish] == "\r":
        finish += 1
    if finish < len(text) and text[finish] == "\n":
        finish += 1
    return start, finish


def _extract_block(text: str, begin: str, end: str, reason_code: str) -> str | None:
    bounds = _marker_bounds(text, begin, end, reason_code)
    return None if bounds is None else text[bounds[0] : bounds[1]]


def _append_block(text: str, block: str) -> tuple[str, bool]:
    if not text:
        return block, False
    added_newline = not text.endswith(("\n", "\r"))
    return text + ("\n" if added_newline else "") + block, added_newline


def _replace_block(
    text: str,
    begin: str,
    end: str,
    block: str,
    reason_code: str,
) -> str:
    bounds = _marker_bounds(text, begin, end, reason_code)
    if bounds is None:
        raise InstallerError(reason_code, "owned marker is missing")
    return text[: bounds[0]] + block + text[bounds[1] :]


def _remove_block(
    text: str,
    begin: str,
    end: str,
    reason_code: str,
    *,
    added_prefix_newline: bool = False,
) -> str:
    bounds = _marker_bounds(text, begin, end, reason_code)
    if bounds is None:
        raise InstallerError(reason_code, "owned marker is missing")
    start, finish = bounds
    if added_prefix_newline:
        if start == 0 or text[start - 1] != "\n":
            raise InstallerError(reason_code, "owned separator is missing")
        start -= 1
    return text[:start] + text[finish:]


def _block_info(manifest: dict | None, filename: str) -> dict | None:
    if not manifest:
        return None
    value = manifest.get("owned_blocks", {}).get(filename)
    return value if isinstance(value, dict) else None


def _verify_existing_block(
    text: str,
    begin: str,
    end: str,
    reason_code: str,
    info: dict | None,
) -> str | None:
    block = _extract_block(text, begin, end, reason_code)
    if block is None:
        return None
    if info is None:
        raise InstallerError("OWNERSHIP_CONFLICT", "owned marker exists without manifest")
    if info.get("sha256") != _sha256(block.encode("utf-8")):
        raise InstallerError("OWNERSHIP_CONFLICT", "owned block was modified")
    return block


def _merge_agents_policy(
    existing: str,
    policy: str,
    manifest: dict | None,
    *,
    file_created: bool,
) -> tuple[str, dict]:
    info = _block_info(manifest, "AGENTS.md")
    current = _verify_existing_block(
        existing, AGENTS_BEGIN, AGENTS_END, "AGENTS_MARKER_CORRUPT", info
    )
    desired = f"{AGENTS_BEGIN}\n{policy.rstrip()}\n{AGENTS_END}\n"
    if current is not None:
        merged = _replace_block(
            existing,
            AGENTS_BEGIN,
            AGENTS_END,
            desired,
            "AGENTS_MARKER_CORRUPT",
        )
        metadata = dict(info or {})
    else:
        merged, added = _append_block(existing, desired)
        metadata = {
            "added_prefix_newline": added,
            "file_created": file_created,
        }
    metadata["sha256"] = _sha256(desired.encode("utf-8"))
    return merged, metadata


def _agents_table_bounds(text: str) -> tuple[int, int] | None:
    match = re.search(r"(?m)^\s*\[agents\]\s*(?:#.*)?$", text)
    if not match:
        return None
    following = re.search(r"(?m)^\s*\[[^\]]+\]\s*(?:#.*)?$", text[match.end() :])
    finish = len(text) if not following else match.end() + following.start()
    return match.end(), finish


def _merge_config(
    existing: str,
    manifest: dict | None,
    *,
    file_created: bool,
) -> tuple[str, dict]:
    try:
        tomllib.loads(existing) if existing.strip() else {}
    except tomllib.TOMLDecodeError as exc:
        raise InstallerError("CONFIG_MERGE_UNSAFE", "config TOML cannot be parsed") from exc

    info = _block_info(manifest, "config.toml")
    current = _verify_existing_block(
        existing, CONFIG_BEGIN, CONFIG_END, "CONFIG_MERGE_UNSAFE", info
    )
    if current is not None:
        includes_header = "[agents]" in current
        body = (
            "[agents]\n"
            if includes_header
            else ""
        ) + "enabled = true\nmax_concurrent_threads_per_session = 3\n"
        desired = f"{CONFIG_BEGIN}\n{body}{CONFIG_END}\n"
        merged = _replace_block(
            existing, CONFIG_BEGIN, CONFIG_END, desired, "CONFIG_MERGE_UNSAFE"
        )
        metadata = dict(info or {})
    else:
        table = _agents_table_bounds(existing)
        if table:
            section = existing[table[0] : table[1]]
            if re.search(
                r"(?m)^\s*(?:enabled|max_concurrent_threads_per_session)\s*=",
                section,
            ):
                raise InstallerError(
                    "OWNERSHIP_CONFLICT", "user-owned agents settings conflict"
                )
            desired = (
                f"{CONFIG_BEGIN}\n"
                "enabled = true\n"
                "max_concurrent_threads_per_session = 3\n"
                f"{CONFIG_END}\n"
            )
            merged = existing[: table[0]] + "\n" + desired + existing[table[0] :]
            metadata = {
                "added_prefix_newline": True,
                "file_created": file_created,
                "mode": "existing-table",
            }
        else:
            desired = (
                f"{CONFIG_BEGIN}\n"
                "[agents]\n"
                "enabled = true\n"
                "max_concurrent_threads_per_session = 3\n"
                f"{CONFIG_END}\n"
            )
            merged, added = _append_block(existing, desired)
            metadata = {
                "added_prefix_newline": added,
                "file_created": file_created,
                "mode": "owned-table",
            }

    try:
        tomllib.loads(merged)
    except tomllib.TOMLDecodeError as exc:
        raise InstallerError("CONFIG_MERGE_UNSAFE", "merged config is invalid") from exc
    metadata["sha256"] = _sha256(desired.encode("utf-8"))
    return merged, metadata


def _remove_legacy_marker_block(text: str, marker: str, reason_code: str) -> str:
    begin = f"# BEGIN {marker}"
    end = f"# END {marker}"
    bounds = _marker_bounds(text, begin, end, reason_code)
    if bounds is None:
        return text
    return text[: bounds[0]] + text[bounds[1] :]


def _legacy_relative(target: Path, raw: object) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise InstallerError("MANIFEST_INVALID", "legacy owned path is invalid")
    value = raw
    candidate = Path(value)
    if candidate.is_absolute():
        return _relative_path(target, candidate)
    normalized = PurePosixPath(value.replace("\\", "/"))
    if normalized.parts and normalized.parts[0] == ".codex":
        normalized = PurePosixPath(*normalized.parts[1:])
    return _relative_path(target, _target_path(target, normalized))


def _load_legacy_manifest(path: Path) -> dict:
    manifest = _load_json(path, "MANIFEST_INVALID")
    if manifest.get("version") != LEGACY_VERSION:
        raise InstallerError("MANIFEST_INVALID", "legacy manifest version is unsupported")
    if "policy_version" in manifest and manifest.get("policy_version") != LEGACY_VERSION:
        raise InstallerError("MANIFEST_INVALID", "legacy policy version is unsupported")
    for key in ("created_files", "modified_files", "config_owned_markers", "owned_hook_events"):
        value = manifest.get(key)
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            raise InstallerError("MANIFEST_INVALID", f"legacy {key} is invalid")
    return manifest


def _legacy_migration(
    target: Path,
    base_content: dict[str, bytes | None],
) -> tuple[dict[str, bytes | None], dict]:
    manifest_path = _target_path(target, LEGACY_MANIFEST_RELATIVE)
    if not manifest_path.exists():
        raise InstallerError("MANIFEST_MISSING", "legacy manifest is missing")
    manifest = _load_legacy_manifest(manifest_path)

    operations: dict[str, bytes | None] = {}
    created = manifest["created_files"]
    shared = {"config.toml", "AGENTS.md", "hooks.json"}
    legacy_manifest_relative = LEGACY_MANIFEST_RELATIVE.as_posix()
    owned_relatives = []
    for raw in created:
        relative = _legacy_relative(target, raw)
        if relative not in shared and relative != legacy_manifest_relative:
            owned_relatives.append(relative)
            if _target_path(target, relative).is_file():
                operations[relative] = None
    if legacy_manifest_relative not in owned_relatives:
        owned_relatives.append(legacy_manifest_relative)

    agents_relative = "AGENTS.md"
    agents_bytes = base_content.get(agents_relative)
    if agents_bytes is None:
        path = _target_path(target, agents_relative)
        agents_bytes = path.read_bytes() if path.is_file() else b""
    agents_text = agents_bytes.decode("utf-8")
    bounds = _marker_bounds(
        agents_text,
        LEGACY_AGENTS_BEGIN,
        LEGACY_AGENTS_END,
        "AGENTS_MARKER_CORRUPT",
    )
    if bounds:
        agents_text = agents_text[: bounds[0]] + agents_text[bounds[1] :]
        operations[agents_relative] = agents_text.encode("utf-8")

    config_relative = "config.toml"
    config_bytes = base_content.get(config_relative)
    if config_bytes is None:
        path = _target_path(target, config_relative)
        config_bytes = path.read_bytes() if path.is_file() else b""
    config_text = config_bytes.decode("utf-8")
    markers = manifest["config_owned_markers"]
    for marker in markers:
        config_text = _remove_legacy_marker_block(
            config_text, str(marker), "CONFIG_MERGE_UNSAFE"
        )
    if config_text.encode("utf-8") != config_bytes:
        operations[config_relative] = config_text.encode("utf-8")

    hooks_relative = "hooks.json"
    hooks_path = _target_path(target, hooks_relative)
    if hooks_path.is_file():
        hooks = _load_json(hooks_path, "OWNERSHIP_CONFLICT")
        groups = hooks.get("hooks")
        if not isinstance(groups, dict):
            raise InstallerError("OWNERSHIP_CONFLICT", "hooks document is unsupported")
        owned_events = manifest["owned_hook_events"]
        script_names = {
            PurePosixPath(relative).name
            for relative in owned_relatives
            if relative.startswith("hooks/")
        }
        changed = False
        for event in owned_events:
            entries = groups.get(event)
            if not isinstance(entries, list):
                continue
            retained = []
            for entry in entries:
                rendered = json.dumps(entry, sort_keys=True)
                if script_names and any(name in rendered for name in script_names):
                    changed = True
                else:
                    retained.append(entry)
            if retained:
                groups[event] = retained
            elif event in groups:
                del groups[event]
        if changed:
            hooks_created = hooks_relative in {
                _legacy_relative(target, raw) for raw in created
            }
            other_content = set(hooks).difference({"description", "hooks"})
            description = hooks.get("description")
            legacy_description = description is None or (
                isinstance(description, str)
                and re.search(r"(?:sol.?luna|daily best|managed hooks?)", description, re.I)
            )
            if hooks_created and not groups and not other_content and legacy_description:
                operations[hooks_relative] = None
            else:
                operations[hooks_relative] = _json_bytes(hooks)

    summary = {
        "detected": len(set(owned_relatives)),
        "precommit_removals": sum(data is None for data in operations.values()),
        "shared_updates": sum(data is not None for data in operations.values()),
        "source_version": LEGACY_VERSION,
        "state_conversion": False,
        "audit_bundles": "PRESERVE_REVIEW_REQUIRED",
    }
    return operations, summary


def _read_effective(target: Path, relative: str, operations: dict[str, bytes | None]) -> bytes | None:
    if relative in operations:
        return operations[relative]
    path = _target_path(target, relative)
    if path.exists() and not path.is_file():
        raise InstallerError("OWNERSHIP_CONFLICT", f"{relative} is not a file")
    return path.read_bytes() if path.is_file() else None


def _plan_owned_file(
    target: Path,
    relative: str,
    desired: bytes,
    manifest: dict | None,
    operations: dict[str, bytes | None],
) -> None:
    current = _read_effective(target, relative, operations)
    if current == desired:
        return
    if current is not None:
        owned = _owned_hash(manifest, relative)
        if owned is None or _sha256(current) != owned:
            raise InstallerError("OWNERSHIP_CONFLICT", f"{relative} is not installer-owned")
    operations[relative] = desired


def _validate_v4_payloads(desired_files: dict[str, bytes], policy: str) -> None:
    expected_efforts = {
        "luna-low.toml": "low",
        "luna-medium.toml": "medium",
        "luna-high.toml": "high",
        "luna-xhigh.toml": "xhigh",
        "luna-max.toml": "max",
    }
    for filename, effort in expected_efforts.items():
        relative = f"agents/{filename}"
        try:
            value = tomllib.loads(desired_files[relative].decode("utf-8"))
        except (KeyError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            raise InstallerError("PAYLOAD_INVALID", f"{relative} is invalid") from exc
        agents = value.get("agents")
        if (
            value.get("model") != "gpt-5.6-luna"
            or value.get("model_reasoning_effort") != effort
            or not isinstance(agents, dict)
            or agents.get("enabled") is not False
        ):
            raise InstallerError("PAYLOAD_INVALID", f"{relative} contract is invalid")
    try:
        compile(
            desired_files["sol-luna-v4/selector.py"].decode("utf-8"),
            "sol-luna-v4/selector.py",
            "exec",
        )
    except (KeyError, UnicodeError, SyntaxError) as exc:
        raise InstallerError("PAYLOAD_INVALID", "selector payload is invalid") from exc
    if any(value in policy for value in ("<CODEX_HOME>", "<SELECTOR_COMMAND>", ".var")):
        raise InstallerError("PAYLOAD_INVALID", "global policy rendering is invalid")


def _effective_operations(
    target: Path, operations: dict[str, bytes | None]
) -> dict[str, bytes | None]:
    result = {}
    for relative, desired in operations.items():
        path = _target_path(target, relative)
        if path.exists() and not path.is_file():
            raise InstallerError("OWNERSHIP_CONFLICT", f"{relative} is not a file")
        current = path.read_bytes() if path.is_file() else None
        if desired != current:
            result[relative] = desired
    return result


def _choose_backup_root(target: Path, now: datetime) -> Path:
    parent = target / "backups" / "sol-luna-v4"
    stem = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    candidate = parent / stem
    counter = 2
    while candidate.exists():
        candidate = parent / f"{stem}-{counter}"
        counter += 1
    return candidate


def _create_backup(target: Path, relatives: list[str], root: Path) -> Path:
    target_existed = target.exists()
    try:
        root.mkdir(parents=True, exist_ok=False)
        entries = []
        for relative in sorted(set(relatives)):
            source = _target_path(target, relative)
            existed = source.is_file()
            entry = {"path": relative, "existed": existed}
            if existed:
                data = source.read_bytes()
                entry["sha256"] = _sha256(data)
                backup_file = root / "files" / Path(*PurePosixPath(relative).parts)
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                backup_file.write_bytes(data)
            entries.append(entry)
        snapshot = {
            "schema_version": 1,
            "target_existed": target_existed,
            "entries": entries,
        }
        (root / "snapshot.json").write_bytes(_json_bytes(snapshot))
    except (OSError, PermissionError) as exc:
        if root.exists():
            shutil.rmtree(root, ignore_errors=True)
        raise InstallerError("BACKUP_FAILED", "backup snapshot could not be created") from exc
    return root


def _verify_backup(root: Path, relatives: list[str]) -> None:
    snapshot = _load_json(root / "snapshot.json", "BACKUP_FAILED")
    entries = snapshot.get("entries")
    if not isinstance(entries, list) or {
        entry.get("path") for entry in entries if isinstance(entry, dict)
    } != set(relatives):
        raise InstallerError("BACKUP_FAILED", "backup inventory verification failed")
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise InstallerError("BACKUP_FAILED", "backup entry is invalid")
        if entry.get("existed"):
            source = root / "files" / Path(*PurePosixPath(entry["path"]).parts)
            if not source.is_file() or entry.get("sha256") != _sha256(source.read_bytes()):
                raise InstallerError("BACKUP_FAILED", "backup content verification failed")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.sol-luna-v4-", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_descriptor = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_descriptor = None
        if directory_descriptor is not None:
            try:
                os.fsync(directory_descriptor)
            except OSError:
                pass
            finally:
                os.close(directory_descriptor)
    finally:
        if temporary.exists():
            temporary.unlink()


def _remove_empty_parents(path: Path, target: Path) -> None:
    parent = path.parent
    while parent != target and _is_within(parent, target):
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def _apply_operations(target: Path, operations: dict[str, bytes | None]) -> None:
    for relative, desired in sorted(operations.items()):
        path = _target_path(target, relative)
        if desired is None:
            if path.is_file():
                path.unlink()
                _remove_empty_parents(path, target)
        else:
            _atomic_write(path, desired)


def _validate_applied_operations(
    target: Path, operations: dict[str, bytes | None]
) -> None:
    for relative, desired in operations.items():
        path = _target_path(target, relative)
        if desired is None:
            if path.exists():
                raise InstallerError("APPLY_FAILED", f"{relative} was not removed")
        elif not path.is_file() or path.read_bytes() != desired:
            raise InstallerError("APPLY_FAILED", f"{relative} was not installed exactly")
    config = _target_path(target, "config.toml")
    if config.is_file():
        try:
            tomllib.loads(config.read_text(encoding="utf-8"))
        except (UnicodeError, tomllib.TOMLDecodeError) as exc:
            raise InstallerError("APPLY_FAILED", "resulting config is invalid") from exc


def _hit_failpoint(failpoint: Callable[[str], None] | None, name: str) -> None:
    if failpoint is not None:
        failpoint(name)


def _complete_legacy_cleanup(
    target: Path,
    manifest: dict,
    *,
    failpoint: Callable[[str], None] | None,
) -> bool:
    cleanup = manifest.get("legacy_cleanup")
    if not isinstance(cleanup, dict) or cleanup.get("status") != "pending":
        return True
    relative = cleanup.get("target")
    if relative != LEGACY_MANIFEST_RELATIVE.as_posix():
        raise InstallerError("MANIFEST_INVALID", "legacy cleanup target is invalid")
    try:
        path = _target_path(target, relative)
        if path.exists() and not path.is_file():
            raise OSError("legacy manifest target is not a file")
        if path.is_file():
            _hit_failpoint(failpoint, "legacy_manifest_cleanup")
            path.unlink()
            _remove_empty_parents(path, target)
        completed = json.loads(json.dumps(manifest))
        completed["legacy_cleanup"]["status"] = "complete"
        _atomic_write(_target_path(target, MANIFEST_RELATIVE), _json_bytes(completed))
    except Exception:
        return False
    return True


def _ensure_target_writable(target: Path) -> None:
    if target.exists() and not target.is_dir():
        raise InstallerError("TARGET_NOT_WRITABLE", "CODEX_HOME is not a directory")
    probe = target if target.exists() else target.parent
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    if not probe.is_dir() or not os.access(probe, os.W_OK):
        raise InstallerError("TARGET_NOT_WRITABLE", "CODEX_HOME is not writable")


def _backup_relative(target: Path, backup: Path) -> str:
    return _relative_path(target, backup)


def _build_install_plan(
    target: Path,
    project_root: Path,
    *,
    migrate_legacy: bool,
    now: datetime,
) -> tuple[dict[str, bytes | None], dict, dict]:
    manifest = _load_manifest(target)
    operations: dict[str, bytes | None] = {}
    migration = manifest.get("legacy_migration") if manifest else None
    legacy_cleanup = manifest.get("legacy_cleanup") if manifest else None
    if migrate_legacy:
        if manifest:
            if migration is None:
                raise InstallerError(
                    "OWNERSHIP_CONFLICT",
                    "v4 is already installed without a recorded legacy migration",
                )
        else:
            legacy_operations, migration = _legacy_migration(target, operations)
            operations.update(legacy_operations)
            legacy_cleanup = {
                "target": LEGACY_MANIFEST_RELATIVE.as_posix(),
                "status": "pending",
            }

    override = target / "AGENTS.override.md"
    if override.is_file() and override.read_text(encoding="utf-8").strip():
        raise InstallerError(
            "AGENTS_OVERRIDE_PRESENT",
            "non-empty AGENTS.override.md would take precedence over policy",
        )

    desired_files: dict[str, bytes] = {}
    for filename in STABLE_AGENT_FILES:
        desired_files[f"agents/{filename}"] = (
            project_root / ".codex" / "agents" / filename
        ).read_bytes()
    desired_files["sol-luna-v4/selector.py"] = (
        project_root / "src" / "selector.py"
    ).read_bytes()
    policy_template = (project_root / "templates" / "AGENTS.global.md").read_text(
        encoding="utf-8"
    )
    rendered_policy = render_global_policy(policy_template, target)
    _validate_v4_payloads(desired_files, rendered_policy)

    for relative, data in desired_files.items():
        _plan_owned_file(target, relative, data, manifest, operations)

    desired_set = set(desired_files)
    if manifest:
        for relative in manifest.get("owned_files", {}):
            if relative in desired_set:
                continue
            path = _target_path(target, relative)
            if not path.is_file():
                continue
            owned = _owned_hash(manifest, relative)
            if owned is None or _sha256(path.read_bytes()) != owned:
                raise InstallerError("OWNERSHIP_CONFLICT", f"{relative} was modified")
            operations[relative] = None

    agents_relative = "AGENTS.md"
    agents_current = _read_effective(target, agents_relative, operations)
    agents_created = agents_current is None
    agents_text = b"" if agents_current is None else agents_current
    try:
        agents_decoded = agents_text.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InstallerError("OWNERSHIP_CONFLICT", "AGENTS.md is not UTF-8") from exc
    agents_merged, agents_info = _merge_agents_policy(
        agents_decoded,
        rendered_policy,
        manifest,
        file_created=agents_created,
    )
    if agents_merged.encode("utf-8") != agents_current:
        operations[agents_relative] = agents_merged.encode("utf-8")

    config_relative = "config.toml"
    config_current = _read_effective(target, config_relative, operations)
    config_created = config_current is None
    config_bytes = b"" if config_current is None else config_current
    try:
        config_decoded = config_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InstallerError("CONFIG_MERGE_UNSAFE", "config is not UTF-8") from exc
    config_merged, config_info = _merge_config(
        config_decoded, manifest, file_created=config_created
    )
    if config_merged.encode("utf-8") != config_current:
        operations[config_relative] = config_merged.encode("utf-8")

    installed_at = (
        manifest.get("installed_at")
        if manifest and isinstance(manifest.get("installed_at"), str)
        else now.astimezone(timezone.utc).isoformat()
    )
    desired_manifest = {
        "schema_version": 1,
        "version": VERSION,
        "installed_at": installed_at,
        "updated_at": (
            manifest.get("updated_at", installed_at) if manifest else installed_at
        ),
        "owned_files": {
            relative: _sha256(data) for relative, data in sorted(desired_files.items())
        },
        "owned_blocks": {
            "AGENTS.md": agents_info,
            "config.toml": config_info,
        },
        "legacy_migration": migration,
        "legacy_cleanup": legacy_cleanup,
        "last_backup": manifest.get("last_backup") if manifest else None,
    }
    context = {"existing_manifest": manifest, "desired_manifest": desired_manifest}
    return operations, context, migration or {}


def install(
    target: Path,
    *,
    project_root: Path = PROJECT_ROOT,
    migrate_legacy: bool = False,
    generated_at: datetime | None = None,
    allow_validation_sandbox: bool = False,
    failpoint: Callable[[str], None] | None = None,
) -> dict:
    target = target.resolve(strict=False)
    project_root = project_root.resolve(strict=False)
    validate_target(
        target,
        project_root,
        allow_validation_sandbox=allow_validation_sandbox,
    )
    _ensure_target_writable(target)
    now = generated_at or _utc_now()
    operations, context, migration = _build_install_plan(
        target, project_root, migrate_legacy=migrate_legacy, now=now
    )
    manifest_relative = MANIFEST_RELATIVE.as_posix()
    existing_manifest = context["existing_manifest"]
    desired_manifest = context["desired_manifest"]

    preliminary = _effective_operations(target, operations)
    current_manifest_path = _target_path(target, manifest_relative)
    current_manifest_bytes = (
        current_manifest_path.read_bytes() if current_manifest_path.is_file() else None
    )
    preview_manifest = _json_bytes(desired_manifest)
    if not preliminary and current_manifest_bytes == preview_manifest:
        cleanup = desired_manifest.get("legacy_cleanup")
        if isinstance(cleanup, dict) and cleanup.get("status") == "pending":
            cleanup_target_existed = _target_path(
                target, LEGACY_MANIFEST_RELATIVE
            ).is_file()
            completed = _complete_legacy_cleanup(
                target, desired_manifest, failpoint=failpoint
            )
            result_migration = dict(migration)
            result_migration["cleanup_status"] = (
                "complete" if completed else "pending"
            )
            return {
                "status": (
                    "LEGACY_CLEANUP_COMPLETED"
                    if completed
                    else "LEGACY_MANIFEST_CLEANUP_PENDING"
                ),
                "effective_changes": 1 if completed else 0,
                "created": [],
                "modified": [manifest_relative] if completed else [],
                "removed": (
                    [LEGACY_MANIFEST_RELATIVE.as_posix()]
                    if completed and cleanup_target_existed
                    else []
                ),
                "backup": None,
                "migration": result_migration,
            }
        return {
            "status": "IDEMPOTENT_PASS",
            "effective_changes": 0,
            "created": [],
            "modified": [],
            "removed": [],
            "backup": None,
            "migration": migration,
        }

    backup_root = _choose_backup_root(target, now)
    desired_manifest["updated_at"] = now.astimezone(timezone.utc).isoformat()
    desired_manifest["last_backup"] = _backup_relative(target, backup_root)
    effective = _effective_operations(target, operations)
    manifest_bytes = _json_bytes(desired_manifest)
    tracked = set(effective)
    tracked.add(manifest_relative)
    cleanup = desired_manifest.get("legacy_cleanup")
    if isinstance(cleanup, dict) and cleanup.get("status") == "pending":
        tracked.add(LEGACY_MANIFEST_RELATIVE.as_posix())
    before = {relative: _target_path(target, relative).is_file() for relative in tracked}
    _create_backup(target, sorted(tracked), backup_root)
    try:
        _verify_backup(backup_root, sorted(tracked))
        install_relatives = {
            *(f"agents/{filename}" for filename in STABLE_AGENT_FILES),
            "sol-luna-v4/selector.py",
        }
        install_operations = {
            relative: desired
            for relative, desired in effective.items()
            if relative in install_relatives
        }
        shared_operations = {
            relative: desired
            for relative, desired in effective.items()
            if relative in {"config.toml", "AGENTS.md"}
        }
        hook_operations = {
            relative: desired
            for relative, desired in effective.items()
            if relative == LEGACY_HOOKS_RELATIVE
        }
        old_operations = {
            relative: desired
            for relative, desired in effective.items()
            if relative not in install_operations
            and relative not in shared_operations
            and relative not in hook_operations
        }

        _apply_operations(target, install_operations)
        _hit_failpoint(failpoint, "after_agent_install")
        _apply_operations(target, shared_operations)
        _hit_failpoint(failpoint, "after_config_merge")
        _apply_operations(target, hook_operations)
        _hit_failpoint(failpoint, "after_hook_removal")
        _apply_operations(target, old_operations)
        _hit_failpoint(failpoint, "after_old_file_deletion")
        _validate_applied_operations(target, effective)
        _hit_failpoint(failpoint, "before_v4_manifest_write")
        _atomic_write(current_manifest_path, manifest_bytes)
    except Exception as exc:
        try:
            rollback(
                target,
                backup_root,
                project_root=project_root,
                allow_validation_sandbox=allow_validation_sandbox,
            )
        except InstallerError:
            pass
        if isinstance(exc, InstallerError):
            raise
        raise InstallerError("APPLY_FAILED", "installer pre-commit failed") from exc

    cleanup_complete = _complete_legacy_cleanup(
        target, desired_manifest, failpoint=failpoint
    )
    applied = dict(effective)
    applied[manifest_relative] = manifest_bytes
    if isinstance(cleanup, dict) and cleanup.get("status") == "pending" and cleanup_complete:
        applied[LEGACY_MANIFEST_RELATIVE.as_posix()] = None
    created = sorted(
        relative
        for relative, data in applied.items()
        if data is not None and not before.get(relative, False)
    )
    modified = sorted(
        relative
        for relative, data in applied.items()
        if data is not None and before.get(relative, False)
    )
    removed = sorted(
        relative
        for relative, data in applied.items()
        if data is None and before.get(relative, False)
    )
    result_migration = dict(migration)
    if isinstance(cleanup, dict):
        result_migration["cleanup_status"] = (
            "complete" if cleanup_complete else "pending"
        )
    return {
        "status": (
            "LEGACY_MANIFEST_CLEANUP_PENDING"
            if isinstance(cleanup, dict)
            and cleanup.get("status") == "pending"
            and not cleanup_complete
            else ("UPGRADED" if existing_manifest else "INSTALLED")
        ),
        "effective_changes": len(applied),
        "created": created,
        "modified": modified,
        "removed": removed,
        "backup": str(backup_root),
        "migration": result_migration,
    }


def rollback(
    target: Path,
    backup_root: Path,
    *,
    project_root: Path = PROJECT_ROOT,
    allow_validation_sandbox: bool = False,
) -> dict:
    target = target.resolve(strict=False)
    backup_root = backup_root.resolve(strict=False)
    validate_target(
        target,
        project_root,
        allow_validation_sandbox=allow_validation_sandbox,
    )
    allowed_backup_parent = target / "backups" / "sol-luna-v4"
    if not _is_within(backup_root, allowed_backup_parent):
        raise InstallerError("OWNERSHIP_CONFLICT", "backup is outside the owned root")
    snapshot_path = backup_root / "snapshot.json"
    if not snapshot_path.is_file():
        raise InstallerError("BACKUP_NOT_FOUND", "backup snapshot is missing")
    snapshot = _load_json(snapshot_path, "BACKUP_INVALID")
    entries = snapshot.get("entries")
    if not isinstance(entries, list):
        raise InstallerError("BACKUP_INVALID", "backup entries are invalid")
    try:
        for entry in entries:
            relative = entry["path"]
            destination = _target_path(target, relative)
            if entry.get("existed"):
                source = backup_root / "files" / Path(*PurePosixPath(relative).parts)
                data = source.read_bytes()
                if entry.get("sha256") != _sha256(data):
                    raise InstallerError("BACKUP_INVALID", "backup hash mismatch")
                _atomic_write(destination, data)
            elif destination.is_file():
                destination.unlink()
                _remove_empty_parents(destination, target)
        shutil.rmtree(backup_root)
        _remove_empty_parents(backup_root, target)
        if not snapshot.get("target_existed") and target.exists() and not any(target.iterdir()):
            target.rmdir()
    except InstallerError:
        raise
    except (OSError, PermissionError) as exc:
        raise InstallerError("ROLLBACK_FAILED", "backup could not be restored") from exc
    return {"status": "ROLLBACK_EXACT_PASS", "restored": len(entries)}


def uninstall(
    target: Path,
    *,
    project_root: Path = PROJECT_ROOT,
    generated_at: datetime | None = None,
    allow_validation_sandbox: bool = False,
) -> dict:
    target = target.resolve(strict=False)
    validate_target(
        target,
        project_root,
        allow_validation_sandbox=allow_validation_sandbox,
    )
    _ensure_target_writable(target)
    manifest = _load_manifest(target, required=True)
    operations: dict[str, bytes | None] = {}

    for relative in manifest.get("owned_files", {}):
        path = _target_path(target, relative)
        if path.exists() and not path.is_file():
            raise InstallerError("OWNERSHIP_CONFLICT", f"{relative} is not a file")
        if not path.is_file():
            continue
        owned = _owned_hash(manifest, relative)
        if owned is None or _sha256(path.read_bytes()) != owned:
            raise InstallerError("OWNERSHIP_CONFLICT", f"{relative} was modified")
        operations[relative] = None

    for filename, begin, end, reason in (
        ("AGENTS.md", AGENTS_BEGIN, AGENTS_END, "AGENTS_MARKER_CORRUPT"),
        ("config.toml", CONFIG_BEGIN, CONFIG_END, "CONFIG_MERGE_UNSAFE"),
    ):
        info = _block_info(manifest, filename)
        if info is None:
            raise InstallerError("MANIFEST_INVALID", f"{filename} ownership is missing")
        path = _target_path(target, filename)
        if not path.is_file():
            raise InstallerError("OWNERSHIP_CONFLICT", f"{filename} is missing")
        text = path.read_text(encoding="utf-8")
        block = _extract_block(text, begin, end, reason)
        if block is None or info.get("sha256") != _sha256(block.encode("utf-8")):
            raise InstallerError("OWNERSHIP_CONFLICT", f"{filename} owned block changed")
        remaining = _remove_block(
            text,
            begin,
            end,
            reason,
            added_prefix_newline=bool(info.get("added_prefix_newline")),
        )
        operations[filename] = (
            None if info.get("file_created") and not remaining else remaining.encode("utf-8")
        )

    operations[MANIFEST_RELATIVE.as_posix()] = None
    effective = _effective_operations(target, operations)
    now = generated_at or _utc_now()
    backup_root = _choose_backup_root(target, now)
    _create_backup(target, list(effective), backup_root)
    try:
        _apply_operations(target, effective)
    except (OSError, PermissionError) as exc:
        rollback(
            target,
            backup_root,
            project_root=project_root,
            allow_validation_sandbox=allow_validation_sandbox,
        )
        raise InstallerError("APPLY_FAILED", "uninstall failed") from exc
    shutil.rmtree(backup_root)
    _remove_empty_parents(backup_root, target)
    return {
        "status": "UNINSTALLED",
        "effective_changes": len(effective),
        "removed": sorted(r for r, data in effective.items() if data is None),
        "modified": sorted(r for r, data in effective.items() if data is not None),
    }


def _result_or_error(callable_):
    try:
        return callable_(), 0
    except UnsafeTarget as exc:
        return {"status": "FAIL", "reason_code": "UNSAFE_TARGET", "message": str(exc)}, 2
    except InstallerError as exc:
        return {
            "status": "FAIL",
            "reason_code": exc.reason_code,
            "message": str(exc),
        }, 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--uninstall", action="store_true")
    modes.add_argument("--rollback", metavar="BACKUP_PATH")
    parser.add_argument("--codex-home", help="Explicit target CODEX_HOME")
    parser.add_argument("--migrate-v3", action="store_true")
    parser.add_argument(
        "--validation-sandbox",
        action="store_true",
        help="Allow writes only below project .tmp/installer-validation",
    )
    args = parser.parse_args(argv)

    mutating = args.apply or args.uninstall or args.rollback
    if mutating and not args.codex_home:
        parser.error("mutating modes require --codex-home")
    if args.migrate_v3 and not args.apply:
        parser.error("--migrate-v3 requires --apply")
    target = resolve_codex_home(args.codex_home)

    if args.apply:
        result, code = _result_or_error(
            lambda: install(
                target,
                migrate_legacy=args.migrate_v3,
                allow_validation_sandbox=args.validation_sandbox,
            )
        )
    elif args.uninstall:
        result, code = _result_or_error(
            lambda: uninstall(
                target, allow_validation_sandbox=args.validation_sandbox
            )
        )
    elif args.rollback:
        result, code = _result_or_error(
            lambda: rollback(
                target,
                Path(args.rollback),
                allow_validation_sandbox=args.validation_sandbox,
            )
        )
    else:
        result, code = _result_or_error(
            lambda: build_plan(
                target, allow_validation_sandbox=args.validation_sandbox
            )
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
