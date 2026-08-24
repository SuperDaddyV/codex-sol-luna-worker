"""Deterministic, approval-gated assistance around the Sol/Luna installer."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.install import (  # noqa: E402
    MANIFEST_RELATIVE,
    VERSION,
    InstallerError,
    UnsafeTarget,
    _compare_project_semver,
    dry_run_install,
    install as transactional_install,
    resolve_codex_home,
)
from scripts.probe_capabilities import run_probe  # noqa: E402


ASSIST_SCHEMA = 1
CATALOG_PATH = PROJECT_ROOT / "scripts" / "install_recovery_catalog.json"
REPOSITORY_URL = "https://github.com/SuperDaddyV/codex-sol-luna-worker.git"
SUPPORTED_PLATFORMS = {"Windows", "Linux", "Darwin"}
SUPPORTED_APPROVAL_POLICIES = (
    "unknown",
    "untrusted",
    "on-request",
    "never",
    "granular",
)
SUPPORTED_SANDBOX_MODES = (
    "unknown",
    "read-only",
    "workspace-write",
    "danger-full-access",
)
PHASES = (
    "CHECKING",
    "SAFE_RECOVERY",
    "AWAITING_APPROVAL",
    "RECHECKING",
    "CAPABILITY_PRECHECK",
    "DRY_RUN",
    "INSTALLING",
    "RELOAD_REQUIRED",
    "FRESH_TASK_SMOKE",
    "COMPLETE",
    "NEEDS_USER_ACTION",
    "BLOCKED",
)
OFFICIAL_SOURCE_HOSTS = {
    "docs.brew.sh",
    "documentation.ubuntu.com",
    "learn.chatgpt.com",
    "learn.microsoft.com",
    "wiki.debian.org",
    "www.debian.org",
}
HARD_BLOCKERS = {
    "CURRENT_VERSION_NEWER",
    "MANIFEST_INVALID",
    "UNSUPPORTED_PLATFORM",
}
BLOCKER_ORDER = (
    "UNSUPPORTED_PLATFORM",
    "CODEX_CLI_MISSING_OR_UNUSABLE",
    "PYTHON_MISSING_OR_UNSUPPORTED",
    "GIT_MISSING",
    "GITHUB_HTTPS_BLOCKED",
    "MANIFEST_INVALID",
    "CURRENT_VERSION_NEWER",
)
ACTION_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9.]+)*")
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
)


class AssistError(RuntimeError):
    """A stable, non-sensitive installation assistance failure."""

    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class CommandOutcome:
    returncode: int | None
    stdout: str = ""
    timed_out: bool = False


Runner = Callable[..., CommandOutcome]


def run_command(
    command: Sequence[str],
    *,
    timeout: int,
    cwd: Path | None = None,
) -> CommandOutcome:
    """Run one argument vector without a shell and discard stderr."""

    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return CommandOutcome(None, timed_out=True)
    except OSError:
        return CommandOutcome(None)
    return CommandOutcome(completed.returncode, completed.stdout)


def _safe_tool_version(kind: str, value: str) -> str:
    first_line = value.strip().splitlines()[0].strip() if value.strip() else ""
    if not first_line or len(first_line) > 96:
        return "available"
    if any(pattern.search(first_line) for pattern in SECRET_PATTERNS):
        return "available"
    if "\\" in first_line or "/" in first_line or ":\\" in first_line:
        return "available"
    patterns = {
        "codex": re.compile(
            r"(?i)^(?:codex(?:-cli)?|openai codex)\s+v?[0-9][0-9A-Za-z.+-]*$"
        ),
        "git": re.compile(r"(?i)^git version [0-9][0-9A-Za-z.+-]*$"),
    }
    pattern = patterns.get(kind)
    return first_line if pattern is not None and pattern.fullmatch(first_line) else "available"


def _safe_report_version(kind: str, value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if kind in {"codex", "git"}:
        return _safe_tool_version(kind, value)
    if any(pattern.search(value) for pattern in SECRET_PATTERNS):
        return "available"
    if "\n" in value or "\r" in value or "\\" in value or "/" in value:
        return "available"
    return value if re.fullmatch(r"Python [0-9]+\.[0-9]+\.[0-9]+", value) else "available"


def _tool_check(
    name: str,
    kind: str,
    *,
    which: Callable[[str], str | None],
    runner: Runner,
) -> dict:
    executable = which(name)
    if executable is None:
        return {"status": "MISSING", "version": None}
    outcome = runner([executable, "--version"], timeout=10)
    if outcome.returncode != 0:
        return {"status": "UNUSABLE", "version": None}
    return {
        "status": "PASS",
        "version": _safe_tool_version(kind, outcome.stdout),
    }


def _python_check() -> dict:
    supported = sys.version_info >= (3, 11) and importlib.util.find_spec("tomllib") is not None
    return {
        "status": "PASS" if supported else "UNSUPPORTED",
        "version": f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


def _linux_distro_id(os_release: Path = Path("/etc/os-release")) -> str | None:
    try:
        content = os_release.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in content.splitlines():
        if line.startswith("ID="):
            return line[3:].strip().strip('"\'').lower() or None
    return None


def _is_wsl(platform_name: str) -> bool:
    if platform_name != "Linux":
        return False
    release = platform.release().lower()
    return "microsoft" in release or "WSL_INTEROP" in os.environ


def _package_manager(
    platform_name: str,
    distro_id: str | None,
    which: Callable[[str], str | None],
) -> str | None:
    if platform_name == "Windows" and which("winget"):
        return "winget"
    if platform_name == "Darwin" and which("brew"):
        return "brew"
    if platform_name == "Linux" and distro_id in {"ubuntu", "debian"} and which("apt-get"):
        return "apt-get"
    return None


def _github_https_check(
    git_available: bool,
    *,
    runner: Runner,
    attempts: int,
    sleeper: Callable[[float], None],
) -> dict:
    if attempts not in {1, 2, 3}:
        raise AssistError("NETWORK_RETRY_BUDGET_INVALID")
    if not git_available:
        return {"status": "NOT_CHECKED", "attempts": 0}
    last_timed_out = False
    for attempt in range(1, attempts + 1):
        outcome = runner(
            ["git", "ls-remote", "--exit-code", REPOSITORY_URL, "HEAD"],
            timeout=30,
        )
        if outcome.returncode == 0:
            return {"status": "PASS", "attempts": attempt}
        last_timed_out = outcome.timed_out
        if attempt < attempts:
            sleeper(float(attempt))
    return {
        "status": "BLOCKED",
        "attempts": attempts,
        "timed_out": last_timed_out,
    }


def classify_installed(codex_home: Path) -> dict:
    manifest_path = codex_home / Path(MANIFEST_RELATIVE.as_posix())
    if not manifest_path.exists():
        return {"state": "ABSENT", "version": None, "source_commit": None}
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return {"state": "INVALID", "version": None, "source_commit": None}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"state": "INVALID", "version": None, "source_commit": None}
    if not isinstance(manifest, dict):
        return {"state": "INVALID", "version": None, "source_commit": None}
    version = manifest.get("version")
    try:
        comparison = _compare_project_semver(version, VERSION)
    except InstallerError:
        return {"state": "INVALID", "version": None, "source_commit": None}
    state = "CURRENT" if comparison == 0 else ("OLDER" if comparison < 0 else "NEWER")
    source_commit = manifest.get("source_commit")
    if not isinstance(source_commit, str) or SHA_PATTERN.fullmatch(source_commit.lower()) is None:
        source_commit = None
    return {
        "state": state,
        "version": version,
        "source_commit": source_commit,
    }


def collect_snapshot(
    codex_home: Path,
    *,
    approval_policy: str,
    sandbox_mode: str,
    network_attempts: int = 3,
    platform_name: str | None = None,
    distro_id: str | None = None,
    wsl: bool | None = None,
    which: Callable[[str], str | None] = shutil.which,
    runner: Runner = run_command,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict:
    platform_name = platform.system() if platform_name is None else platform_name
    if platform_name == "Linux" and distro_id is None:
        distro_id = _linux_distro_id()
    if platform_name != "Linux":
        distro_id = None
    wsl = _is_wsl(platform_name) if wsl is None else wsl

    codex = _tool_check("codex", "codex", which=which, runner=runner)
    git = _tool_check("git", "git", which=which, runner=runner)
    python = _python_check()
    github = _github_https_check(
        git["status"] == "PASS",
        runner=runner,
        attempts=network_attempts,
        sleeper=sleeper,
    )
    installed = classify_installed(codex_home)

    blockers = []
    if platform_name not in SUPPORTED_PLATFORMS:
        blockers.append("UNSUPPORTED_PLATFORM")
    if codex["status"] != "PASS":
        blockers.append("CODEX_CLI_MISSING_OR_UNUSABLE")
    if python["status"] != "PASS":
        blockers.append("PYTHON_MISSING_OR_UNSUPPORTED")
    if git["status"] != "PASS":
        blockers.append("GIT_MISSING")
    elif github["status"] != "PASS":
        blockers.append("GITHUB_HTTPS_BLOCKED")
    if installed["state"] == "INVALID":
        blockers.append("MANIFEST_INVALID")
    elif installed["state"] == "NEWER":
        blockers.append("CURRENT_VERSION_NEWER")
    blockers = [item for item in BLOCKER_ORDER if item in blockers]

    return {
        "schema": ASSIST_SCHEMA,
        "target_version": VERSION,
        "platform": platform_name,
        "distro": distro_id,
        "wsl": bool(wsl),
        "approval_policy": approval_policy,
        "sandbox_mode": sandbox_mode,
        "package_manager": _package_manager(platform_name, distro_id, which),
        "tools": {"codex": codex, "python": python, "git": git},
        "github_https": github,
        "installed": installed,
        "blockers": blockers,
        "ready": not blockers,
    }


def _validate_vector(vector: object, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(vector, list) or (not vector and not allow_empty):
        raise AssistError("RECOVERY_CATALOG_INVALID")
    if not all(isinstance(item, str) and item for item in vector):
        raise AssistError("RECOVERY_CATALOG_INVALID")
    unsafe_tokens = {"|", "||", "&", "&&", ";", ">", ">>", "<", "`"}
    for item in vector:
        if "\n" in item or "\r" in item or "\0" in item:
            raise AssistError("RECOVERY_CATALOG_INVALID")
        if item in unsafe_tokens or "$(" in item or "`" in item:
            raise AssistError("RECOVERY_CATALOG_INVALID")
    return list(vector)


def _validate_action(action: object) -> dict:
    if not isinstance(action, dict):
        raise AssistError("RECOVERY_CATALOG_INVALID")
    required = {
        "action_id",
        "administrator",
        "blocker",
        "classification",
        "commands",
        "distro_ids",
        "instruction",
        "package_manager",
        "persistent_changes",
        "platform",
        "proof",
        "rollback",
        "rollback_instruction",
        "scope",
        "source",
    }
    if set(action) != required:
        raise AssistError("RECOVERY_CATALOG_INVALID")
    if not isinstance(action["action_id"], str) or ACTION_ID_PATTERN.fullmatch(action["action_id"]) is None:
        raise AssistError("RECOVERY_CATALOG_INVALID")
    if action["classification"] not in {"approval_required", "user_action"}:
        raise AssistError("RECOVERY_CATALOG_INVALID")
    if action["platform"] not in SUPPORTED_PLATFORMS | {"*"}:
        raise AssistError("RECOVERY_CATALOG_INVALID")
    if not isinstance(action["distro_ids"], list) or not all(
        isinstance(item, str) and item for item in action["distro_ids"]
    ):
        raise AssistError("RECOVERY_CATALOG_INVALID")
    if not isinstance(action["persistent_changes"], list) or not all(
        isinstance(item, str) and item for item in action["persistent_changes"]
    ):
        raise AssistError("RECOVERY_CATALOG_INVALID")
    for key in (
        "administrator",
        "blocker",
        "instruction",
        "package_manager",
        "rollback_instruction",
        "scope",
        "source",
    ):
        if not isinstance(action[key], str) or not action[key]:
            raise AssistError("RECOVERY_CATALOG_INVALID")
    source = urlparse(action["source"])
    if source.scheme != "https" or source.hostname not in OFFICIAL_SOURCE_HOSTS:
        raise AssistError("RECOVERY_CATALOG_INVALID")

    commands = action["commands"]
    rollback = action["rollback"]
    if not isinstance(commands, list) or not isinstance(rollback, list):
        raise AssistError("RECOVERY_CATALOG_INVALID")
    validated_commands = [_validate_vector(item) for item in commands]
    validated_rollback = [_validate_vector(item) for item in rollback]
    proof = _validate_vector(action["proof"])
    if action["classification"] == "approval_required":
        if not validated_commands or not validated_rollback:
            raise AssistError("RECOVERY_CATALOG_INVALID")
    elif validated_commands:
        raise AssistError("RECOVERY_CATALOG_INVALID")

    return {
        **action,
        "commands": validated_commands,
        "proof": proof,
        "rollback": validated_rollback,
    }


def load_catalog(path: Path = CATALOG_PATH) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AssistError("RECOVERY_CATALOG_INVALID") from exc
    if not isinstance(payload, dict) or set(payload) != {"actions", "last_verified", "schema"}:
        raise AssistError("RECOVERY_CATALOG_INVALID")
    if payload["schema"] != 1 or not isinstance(payload["last_verified"], str):
        raise AssistError("RECOVERY_CATALOG_INVALID")
    if not isinstance(payload["actions"], list):
        raise AssistError("RECOVERY_CATALOG_INVALID")
    actions = [_validate_action(action) for action in payload["actions"]]
    action_ids = [action["action_id"] for action in actions]
    if len(action_ids) != len(set(action_ids)):
        raise AssistError("RECOVERY_CATALOG_INVALID")
    return {**payload, "actions": actions}


def _action_matches(action: Mapping[str, object], snapshot: Mapping[str, object], blocker: str) -> bool:
    if action["blocker"] != blocker:
        return False
    if action["platform"] not in {"*", snapshot["platform"]}:
        return False
    distro_ids = action["distro_ids"]
    if distro_ids and snapshot.get("distro") not in distro_ids:
        return False
    if action["classification"] == "approval_required":
        return action["package_manager"] == snapshot.get("package_manager")
    return True


def _public_action(action: Mapping[str, object]) -> dict:
    return {
        key: action[key]
        for key in (
            "action_id",
            "administrator",
            "blocker",
            "classification",
            "commands",
            "instruction",
            "persistent_changes",
            "proof",
            "rollback",
            "rollback_instruction",
            "scope",
            "source",
        )
    }


def _plan_identity(plan_core: Mapping[str, object]) -> str:
    encoded = json.dumps(
        plan_core,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def build_recovery_plan(snapshot: Mapping[str, object], catalog: Mapping[str, object]) -> dict:
    actions = []
    unresolved = []
    seen = set()
    for blocker in snapshot["blockers"]:
        selected = next(
            (
                action
                for action in catalog["actions"]
                if _action_matches(action, snapshot, blocker)
            ),
            None,
        )
        if selected is None:
            unresolved.append(blocker)
            continue
        if selected["action_id"] not in seen:
            actions.append(_public_action(selected))
            seen.add(selected["action_id"])

    if any(blocker in HARD_BLOCKERS for blocker in snapshot["blockers"]):
        phase = "BLOCKED"
    elif not snapshot["blockers"]:
        phase = "CAPABILITY_PRECHECK"
    elif any(action["classification"] == "approval_required" for action in actions):
        phase = "AWAITING_APPROVAL"
    else:
        phase = "NEEDS_USER_ACTION"

    administrators = {action["administrator"] for action in actions}
    if "yes" in administrators:
        administrator_required = "YES"
    elif "may-prompt" in administrators:
        administrator_required = "MAY_PROMPT"
    elif "unknown" in administrators:
        administrator_required = "UNKNOWN"
    else:
        administrator_required = "NO"

    core = {
        "schema": ASSIST_SCHEMA,
        "target_version": VERSION,
        "platform": snapshot["platform"],
        "distro": snapshot.get("distro"),
        "approval_policy": snapshot["approval_policy"],
        "sandbox_mode": snapshot["sandbox_mode"],
        "package_manager": snapshot.get("package_manager"),
        "catalog_last_verified": catalog["last_verified"],
        "blockers": list(snapshot["blockers"]),
        "actions": actions,
        "unresolved": unresolved,
    }
    return {
        **core,
        "plan_id": _plan_identity(core),
        "phase": phase,
        "administrator_required": administrator_required,
        "ready": bool(snapshot["ready"]),
        "environment": {
            "platform": snapshot["platform"],
            "distro": snapshot.get("distro"),
            "wsl": snapshot["wsl"],
            "approval_policy": snapshot["approval_policy"],
            "sandbox_mode": snapshot["sandbox_mode"],
            "administrator_required": administrator_required,
            "package_manager": snapshot.get("package_manager"),
            "tools": snapshot["tools"],
            "github_https": snapshot["github_https"],
            "installed": snapshot["installed"],
        },
    }


def check_result(plan: Mapping[str, object], *, include_actions: bool) -> dict:
    result = {
        "schema": ASSIST_SCHEMA,
        "target_version": VERSION,
        "phase": plan["phase"],
        "status": "READY" if plan["ready"] else "NOT_READY",
        "reason_codes": list(plan["blockers"]),
        "ready": plan["ready"],
        "plan_id": plan["plan_id"],
        "administrator_required": plan["administrator_required"],
        "environment": plan["environment"],
        "recovery_action_ids": [action["action_id"] for action in plan["actions"]],
        "unresolved": list(plan["unresolved"]),
    }
    if include_actions:
        result["actions"] = plan["actions"]
    return result


def execute_recovery(
    plan: Mapping[str, object],
    approved_plan_id: str,
    *,
    runner: Runner = run_command,
) -> dict:
    if approved_plan_id != plan["plan_id"]:
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "BLOCKED",
            "status": "BLOCKED",
            "reason_code": "RECOVERY_PLAN_CHANGED",
            "attempted_actions": [],
            "writes_performed": "NO",
        }
    if plan["phase"] == "BLOCKED":
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "BLOCKED",
            "status": "BLOCKED",
            "reason_code": next(
                (
                    blocker
                    for blocker in plan["blockers"]
                    if blocker in HARD_BLOCKERS
                ),
                "RECOVERY_NOT_ALLOWED",
            ),
            "attempted_actions": [],
            "writes_performed": "NO",
        }
    executable = [
        action
        for action in plan["actions"]
        if action["classification"] == "approval_required"
    ]
    if not executable:
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "NEEDS_USER_ACTION",
            "status": "NEEDS_USER_ACTION",
            "reason_code": "NO_APPROVED_RECOVERY_ACTION",
            "attempted_actions": [],
            "writes_performed": "NO",
        }

    attempted = []
    for action in executable:
        action_result = {"action_id": action["action_id"], "status": "RUNNING"}
        attempted.append(action_result)
        for command in action["commands"]:
            outcome = runner(command, timeout=900)
            if outcome.returncode != 0:
                action_result["status"] = "FAILED"
                return {
                    "schema": ASSIST_SCHEMA,
                    "target_version": VERSION,
                    "phase": "NEEDS_USER_ACTION",
                    "status": "NEEDS_USER_ACTION",
                    "reason_code": (
                        "RECOVERY_COMMAND_TIMEOUT"
                        if outcome.timed_out
                        else "RECOVERY_COMMAND_FAILED"
                    ),
                    "attempted_actions": attempted,
                    "writes_performed": "POSSIBLE",
                }
        proof = runner(action["proof"], timeout=30)
        if proof.returncode != 0:
            action_result["status"] = "PROOF_FAILED"
            return {
                "schema": ASSIST_SCHEMA,
                "target_version": VERSION,
                "phase": "NEEDS_USER_ACTION",
                "status": "NEEDS_USER_ACTION",
                "reason_code": "RECOVERY_PROOF_FAILED",
                "attempted_actions": attempted,
                "writes_performed": "YES",
            }
        action_result["status"] = "PASS"

    return {
        "schema": ASSIST_SCHEMA,
        "target_version": VERSION,
        "phase": "RECHECKING",
        "status": "RECOVERY_COMMANDS_PASS",
        "reason_code": None,
        "attempted_actions": attempted,
        "writes_performed": "YES",
    }


def verify_source_checkout(
    source_commit: str,
    *,
    runner: Runner = run_command,
    require_detached: bool = True,
) -> dict:
    normalized = source_commit.lower()
    if SHA_PATTERN.fullmatch(normalized) is None:
        return {"ok": False, "reason_code": "SOURCE_COMMIT_INVALID"}
    head = runner(["git", "rev-parse", "HEAD"], timeout=10, cwd=PROJECT_ROOT)
    if head.returncode != 0 or head.stdout.strip().lower() != normalized:
        return {"ok": False, "reason_code": "SOURCE_COMMIT_MISMATCH"}
    status = runner(["git", "status", "--short"], timeout=10, cwd=PROJECT_ROOT)
    if status.returncode != 0 or status.stdout.strip():
        return {"ok": False, "reason_code": "SOURCE_CHECKOUT_DIRTY"}
    if require_detached:
        symbolic = runner(
            ["git", "symbolic-ref", "-q", "HEAD"],
            timeout=10,
            cwd=PROJECT_ROOT,
        )
        if symbolic.returncode == 0:
            return {"ok": False, "reason_code": "SOURCE_NOT_DETACHED"}
        if symbolic.returncode not in {1}:
            return {"ok": False, "reason_code": "SOURCE_CHECKOUT_UNVERIFIED"}
    return {"ok": True, "reason_code": None, "source_commit": normalized}


def _symbolic_backup(value: object, codex_home: Path) -> str:
    if not isinstance(value, str) or not value:
        return "NONE"
    try:
        relative = Path(value).resolve(strict=False).relative_to(codex_home.resolve(strict=False))
    except (OSError, ValueError):
        return "CREATED"
    return "<CODEX_HOME>/" + relative.as_posix()


def _resume_block(phase: str, reason_code: str | None = None) -> str:
    pending = reason_code or "FRESH_TASK_SMOKE_REQUIRED"
    return (
        "SOL_LUNA_ASSIST_RESUME\n"
        f"Target: {VERSION}\n"
        f"Phase: {phase}\n"
        f"Pending blocker: {pending}\n"
        "Next proof: run the documented read-only validation in a fresh task"
    )


def install_workflow(
    snapshot: Mapping[str, object],
    codex_home: Path,
    *,
    source_commit: str,
    apply: bool,
    migrate_v3: bool,
    capability_timeout: int,
    allow_validation_sandbox: bool = False,
    source_verifier: Callable[..., dict] | None = None,
    capability_probe: Callable[[str, int], dict] | None = None,
    dry_runner: Callable[..., dict] | None = None,
    apply_runner: Callable[..., dict] | None = None,
) -> dict:
    catalog = load_catalog()
    plan = build_recovery_plan(snapshot, catalog)
    if snapshot["blockers"]:
        return check_result(plan, include_actions=True)

    source_verifier = verify_source_checkout if source_verifier is None else source_verifier
    verified = source_verifier(
        source_commit,
        require_detached=not allow_validation_sandbox,
    )
    if not verified.get("ok"):
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "BLOCKED",
            "status": "BLOCKED",
            "reason_code": verified.get("reason_code", "SOURCE_CHECKOUT_UNVERIFIED"),
            "writes_performed": "NO",
        }

    capability_probe = run_probe if capability_probe is None else capability_probe
    try:
        capability = capability_probe("codex", capability_timeout)
    except Exception:
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "NEEDS_USER_ACTION",
            "status": "NEEDS_USER_ACTION",
            "reason_code": "LUNA_CAPABILITY_PRECHECK_FAILED",
            "writes_performed": "NO",
            "resume": _resume_block(
                "CAPABILITY_PRECHECK", "LUNA_CAPABILITY_PRECHECK_FAILED"
            ),
        }
    raw_results = capability.get("results", []) if isinstance(capability, Mapping) else []
    if not isinstance(raw_results, list):
        raw_results = []
    capability_summary = {
        "all_supported": bool(capability.get("all_supported"))
        if isinstance(capability, Mapping)
        else False,
        "results": [
            {
                "effort": item.get("effort"),
                "supported": bool(item.get("supported")),
                "response_exact": bool(item.get("response_exact")),
                "exit_code": item.get("exit_code") if isinstance(item.get("exit_code"), int) else None,
            }
            for item in raw_results
            if isinstance(item, dict)
        ],
    }
    expected_efforts = {"low", "medium", "high", "xhigh", "max"}
    observed_efforts = {item["effort"] for item in capability_summary["results"]}
    if (
        not capability_summary["all_supported"]
        or len(capability_summary["results"]) != len(expected_efforts)
        or observed_efforts != expected_efforts
        or not all(
            item["supported"]
            and item["response_exact"]
            and item["exit_code"] == 0
            for item in capability_summary["results"]
        )
    ):
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "NEEDS_USER_ACTION",
            "status": "NEEDS_USER_ACTION",
            "reason_code": "LUNA_CAPABILITY_UNAVAILABLE",
            "capability": capability_summary,
            "writes_performed": "NO",
            "resume": _resume_block("CAPABILITY_PRECHECK", "LUNA_CAPABILITY_UNAVAILABLE"),
        }

    dry_runner = dry_run_install if dry_runner is None else dry_runner
    try:
        dry = dry_runner(
            codex_home,
            migrate_legacy=migrate_v3,
            source_commit=source_commit,
            allow_validation_sandbox=allow_validation_sandbox,
        )
    except InstallerError as exc:
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "BLOCKED",
            "status": "BLOCKED",
            "reason_code": exc.reason_code,
            "capability": capability_summary,
            "writes_performed": "NO",
        }
    except UnsafeTarget:
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "BLOCKED",
            "status": "BLOCKED",
            "reason_code": "UNSAFE_TARGET",
            "capability": capability_summary,
            "writes_performed": "NO",
        }

    if dry.get("status") == "IDEMPOTENT_PASS":
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "FRESH_TASK_SMOKE",
            "status": "CURRENT_INSTALLATION_PASS",
            "reason_code": None,
            "source_commit": source_commit.lower(),
            "capability": capability_summary,
            "effective_changes": 0,
            "backup": "NONE",
            "writes_performed": "NO",
            "configuration_preserved": True,
            "resume": _resume_block("FRESH_TASK_SMOKE"),
        }

    if not apply:
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "DRY_RUN",
            "status": dry.get("status", "DRY_RUN_PASS"),
            "reason_code": None,
            "source_commit": source_commit.lower(),
            "capability": capability_summary,
            "effective_changes": dry.get("effective_changes"),
            "backup": "NONE",
            "writes_performed": "NO",
        }

    apply_runner = transactional_install if apply_runner is None else apply_runner
    try:
        applied = apply_runner(
            codex_home,
            migrate_legacy=migrate_v3,
            source_commit=source_commit,
            allow_validation_sandbox=allow_validation_sandbox,
        )
    except InstallerError as exc:
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "BLOCKED",
            "status": "BLOCKED",
            "reason_code": exc.reason_code,
            "capability": capability_summary,
            "writes_performed": "UNKNOWN",
        }
    except UnsafeTarget:
        return {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "BLOCKED",
            "status": "BLOCKED",
            "reason_code": "UNSAFE_TARGET",
            "capability": capability_summary,
            "writes_performed": "NO",
        }

    return {
        "schema": ASSIST_SCHEMA,
        "target_version": VERSION,
        "phase": "RELOAD_REQUIRED",
        "status": applied.get("status", "INSTALLED"),
        "reason_code": None,
        "source_commit": source_commit.lower(),
        "capability": capability_summary,
        "effective_changes": applied.get("effective_changes"),
        "backup": _symbolic_backup(applied.get("backup"), codex_home),
        "writes_performed": "YES",
        "configuration_preserved": True,
        "resume": _resume_block("FRESH_TASK_SMOKE"),
    }


def make_support_report(snapshot: Mapping[str, object], plan: Mapping[str, object]) -> dict:
    installed = snapshot["installed"]
    source_commit = installed.get("source_commit")
    if not isinstance(source_commit, str) or SHA_PATTERN.fullmatch(source_commit.lower()) is None:
        source_commit = None
    else:
        source_commit = source_commit.lower()
    return {
        "schema": ASSIST_SCHEMA,
        "target_version": VERSION,
        "phase": plan["phase"],
        "reason_codes": list(plan["blockers"]),
        "platform": snapshot["platform"],
        "distro": snapshot.get("distro"),
        "wsl": bool(snapshot["wsl"]),
        "approval_policy": snapshot["approval_policy"],
        "sandbox_mode": snapshot["sandbox_mode"],
        "administrator_required": plan["administrator_required"],
        "package_manager": snapshot.get("package_manager"),
        "tools": {
            name: {
                "status": snapshot["tools"][name]["status"],
                "version": _safe_report_version(
                    name, snapshot["tools"][name]["version"]
                ),
            }
            for name in ("codex", "python", "git")
        },
        "github_https": snapshot["github_https"]["status"],
        "installed": {
            "state": installed["state"],
            "version": installed["version"],
            "source_commit": source_commit,
            "location": "<CODEX_HOME>",
        },
        "recovery_action_ids": [action["action_id"] for action in plan["actions"]],
        "plan_id": plan["plan_id"],
        "ready": bool(snapshot["ready"]),
    }


def render_support_markdown(report: Mapping[str, object]) -> str:
    reasons = ", ".join(report["reason_codes"]) or "NONE"
    actions = ", ".join(report["recovery_action_ids"]) or "NONE"
    lines = [
        "# Sol/Luna Installation Support Report",
        "",
        f"- Target: `{report['target_version']}`",
        f"- Phase: `{report['phase']}`",
        f"- Reasons: `{reasons}`",
        f"- Platform: `{report['platform']}`",
        f"- Distro: `{report['distro'] or 'N/A'}`",
        f"- WSL: `{'YES' if report['wsl'] else 'NO'}`",
        f"- Approval policy: `{report['approval_policy']}`",
        f"- Sandbox mode: `{report['sandbox_mode']}`",
        f"- Administrator required: `{report['administrator_required']}`",
        f"- Package manager: `{report['package_manager'] or 'NONE'}`",
        f"- Codex CLI: `{_tool_report_line(report['tools']['codex'])}`",
        f"- Python: `{_tool_report_line(report['tools']['python'])}`",
        f"- Git: `{_tool_report_line(report['tools']['git'])}`",
        f"- GitHub HTTPS: `{report['github_https']}`",
        f"- Installed state: `{report['installed']['state']}`",
        f"- Installed version: `{report['installed']['version'] or 'NONE'}`",
        f"- Installed source: `{report['installed']['source_commit'] or 'UNRECORDED'}`",
        f"- Location: `{report['installed']['location']}`",
        f"- Recovery actions: `{actions}`",
        f"- Plan ID: `{report['plan_id']}`",
        f"- Ready: `{'YES' if report['ready'] else 'NO'}`",
    ]
    return "\n".join(lines) + "\n"


def render_card(payload: Mapping[str, object]) -> str:
    phase = str(payload.get("phase", "BLOCKED"))
    reason = payload.get("reason_code") or next(
        iter(payload.get("reason_codes", [])), "NONE"
    )
    if phase == "COMPLETE":
        repairs = ", ".join(payload.get("repairs", [])) or "NONE"
        approved = ", ".join(payload.get("approved_system_changes", [])) or "NONE"
        return (
            "Installation Complete\n"
            f"Version: {payload.get('target_version', VERSION)}\n"
            f"Source: {payload.get('source_commit', 'UNRECORDED')}\n"
            f"Repairs: {repairs}\n"
            f"Approved system changes: {approved}\n"
            f"Backup: {payload.get('backup', 'NONE')}\n"
            "Configuration preserved: YES\n"
            "Next: installation and fresh-task smoke are complete"
        )
    if phase == "NEEDS_USER_ACTION":
        action = payload.get("next_action", "Follow the single documented recovery action")
        proof = payload.get("next_proof", "Run the documented read-only proof")
        resume = payload.get("resume", _resume_block(phase, str(reason)))
        return (
            "Needs User Action\n"
            f"Phase: {phase}\n"
            f"Reason: {reason}\n"
            f"Action: {action}\n"
            f"Proof: {proof}\n"
            f"Resume:\n{resume}"
        )
    if phase == "BLOCKED":
        return (
            "Blocked\n"
            f"Phase: {phase}\n"
            f"Reason: {reason}\n"
            f"Writes performed: {payload.get('writes_performed', 'NO')}\n"
            "Next: stop; do not patch managed state or retry automatically"
        )
    return (
        "Sol/Luna Assisted Installation\n"
        f"Target: {payload.get('target_version', VERSION)}\n"
        f"Phase: {phase}\n"
        f"Status: {payload.get('status', 'IN_PROGRESS')}\n"
        f"Ready: {'YES' if payload.get('ready') else 'NO'}"
    )


def _emit(payload: Mapping[str, object], output: str) -> None:
    if payload.get("phase") not in PHASES:
        raise AssistError("INSTALL_ASSIST_PHASE_INVALID")
    if output == "card":
        print(render_card(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _exit_code(payload: Mapping[str, object]) -> int:
    if payload.get("phase") == "BLOCKED":
        return 3
    if payload.get("phase") in {"NEEDS_USER_ACTION", "AWAITING_APPROVAL"}:
        return 2
    return 0


def _tool_report_line(tool: Mapping[str, object]) -> str:
    version = tool.get("version")
    return f"{tool['status']} {version}" if version else str(tool["status"])


def _add_context_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--codex-home", required=True)
    parser.add_argument(
        "--approval-policy",
        choices=SUPPORTED_APPROVAL_POLICIES,
        default="unknown",
        help="Caller-supplied display context; user configuration is not inspected.",
    )
    parser.add_argument(
        "--sandbox-mode",
        choices=SUPPORTED_SANDBOX_MODES,
        default="unknown",
        help="Caller-supplied display context; sandbox settings are not changed.",
    )
    parser.add_argument("--network-attempts", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--output", choices=("json", "card"), default="json")


def _snapshot_from_args(args: argparse.Namespace) -> tuple[Path, dict, dict]:
    codex_home = resolve_codex_home(args.codex_home)
    snapshot = collect_snapshot(
        codex_home,
        approval_policy=args.approval_policy,
        sandbox_mode=args.sandbox_mode,
        network_attempts=args.network_attempts,
    )
    catalog = load_catalog()
    plan = build_recovery_plan(snapshot, catalog)
    return codex_home, snapshot, plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    for name in ("check", "plan"):
        subparser = commands.add_parser(name)
        _add_context_arguments(subparser)

    recover_parser = commands.add_parser("recover")
    _add_context_arguments(recover_parser)
    recover_parser.add_argument("--approve", required=True)

    install_parser = commands.add_parser("install")
    _add_context_arguments(install_parser)
    install_parser.add_argument("--source-commit", required=True)
    install_parser.add_argument("--apply", action="store_true")
    install_parser.add_argument("--migrate-v3", action="store_true")
    install_parser.add_argument("--capability-timeout", type=int, default=180)
    install_parser.add_argument(
        "--validation-sandbox",
        action="store_true",
        help="Repository tests only; never use for a real global installation.",
    )

    report_parser = commands.add_parser("report")
    _add_context_arguments(report_parser)
    report_parser.add_argument("--format", choices=("json", "markdown"), default="json")

    args = parser.parse_args(argv)
    if args.command == "install" and args.migrate_v3 and not args.apply:
        parser.error("--migrate-v3 requires --apply")
    try:
        codex_home, snapshot, plan = _snapshot_from_args(args)
        if args.command == "check":
            payload = check_result(plan, include_actions=False)
        elif args.command == "plan":
            payload = check_result(plan, include_actions=True)
        elif args.command == "recover":
            recovered = execute_recovery(plan, args.approve)
            if recovered["phase"] == "RECHECKING":
                _, refreshed, refreshed_plan = _snapshot_from_args(args)
                payload = check_result(refreshed_plan, include_actions=True)
                payload["attempted_actions"] = recovered["attempted_actions"]
                payload["recovery_status"] = recovered["status"]
            else:
                payload = recovered
        elif args.command == "install":
            payload = install_workflow(
                snapshot,
                codex_home,
                source_commit=args.source_commit,
                apply=args.apply,
                migrate_v3=args.migrate_v3,
                capability_timeout=args.capability_timeout,
                allow_validation_sandbox=args.validation_sandbox,
            )
        else:
            payload = make_support_report(snapshot, plan)
            if args.format == "markdown":
                print(render_support_markdown(payload), end="")
                return 0
        _emit(payload, args.output)
        return _exit_code(payload)
    except AssistError as exc:
        payload = {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "BLOCKED",
            "status": "BLOCKED",
            "reason_code": exc.reason_code,
            "writes_performed": "NO",
        }
        _emit(payload, getattr(args, "output", "json"))
        return 3
    except Exception:
        payload = {
            "schema": ASSIST_SCHEMA,
            "target_version": VERSION,
            "phase": "BLOCKED",
            "status": "BLOCKED",
            "reason_code": "INSTALL_ASSIST_INTERNAL_ERROR",
            "writes_performed": "UNKNOWN",
        }
        _emit(payload, getattr(args, "output", "json"))
        return 3


if __name__ == "__main__":
    sys.exit(main())
