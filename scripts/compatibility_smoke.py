"""Run the lightweight repository-read-only Sol/Luna compatibility smoke."""

from __future__ import annotations

import sys

# Importing the repository helpers must not create repository bytecode artifacts.
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.accept_rc5_runtime_isolation import (  # noqa: E402
    AUTH_RUNTIME_RELATIVE,
    PROTECTED_SOL_LUNA_STATE,
    UNKNOWN,
    HarnessFailure,
    _changed_entry_paths,
    _codex_db_allowlist_from_entries,
    _fingerprint_tree,
    _final_assistant_text,
    _inventory_tree,
    _load_json_lines,
    _protected_state_snapshot,
    _rollout_files,
    _runtime_path_category,
    _session_metadata,
    _unexpected_write_snapshot,
    _validate_protected_state_snapshot,
    _validate_runtime_case,
)
from scripts.probe_capabilities import EFFORTS, run_probe  # noqa: E402


PASS = "PASS"
REVIEW = "REVIEW REQUIRED"
BLOCKED = "BLOCKED"
FAIL = "FAIL"
CHILD_LITERAL = "LUNA_COMPATIBILITY_CHILD_OK"
UUID_COMPONENT = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CheckResult:
    status: str
    reason: str | None = None
    evidence: tuple[str, ...] = ()
    targeted_review: str | None = None


@dataclass(frozen=True)
class SelectorObservation:
    result: CheckResult
    payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RuntimeObservation:
    snapshot: Mapping[str, Any]
    approved_codex_db_paths: frozenset[str]


@dataclass(frozen=True)
class SmokeReport:
    desktop_version: str
    cli_version: str
    cli: CheckResult
    capability: CheckResult
    selector: CheckResult
    delegation: CheckResult
    protected: CheckResult
    runtime: CheckResult
    compatibility: str

    def render(self) -> str:
        lines = [
            "Sol/Luna Compatibility Smoke",
            f"Codex Desktop: {self.desktop_version}",
            f"Codex CLI: {self.cli_version}",
            f"CLI: {self.cli.status}",
            f"Luna capability: {self.capability.status}",
            f"Selector: {self.selector.status}",
            f"Delegation: {self.delegation.status}",
            f"Protected state: {self.protected.status}",
            f"Runtime contract: {self.runtime.status}",
            "Compatibility:",
            self.compatibility,
        ]
        if self.compatibility == REVIEW:
            review_results = (
                self.capability,
                self.selector,
                self.delegation,
                self.protected,
                self.runtime,
            )
            reasons = _unique(
                item.reason
                for item in review_results
                if item.status in {REVIEW, FAIL} and item.reason
            )
            evidence = _unique(
                detail
                for item in review_results
                if item.status in {REVIEW, FAIL}
                for detail in item.evidence
            )
            reviews = _unique(
                item.targeted_review
                for item in review_results
                if item.status in {REVIEW, FAIL} and item.targeted_review
            )
            lines.extend(
                (
                    f"reason: {'; '.join(reasons) or 'compatibility review required'}",
                    f"observed new evidence: {'; '.join(evidence) or 'none'}",
                    f"recommended targeted review: {'; '.join(reviews) or 'compatibility'}",
                )
            )
        return "\n".join(lines)


def _unique(values: Any) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _display_value(value: str | None, *, default: str = "unknown") -> str:
    if not value:
        return default
    first_line = value.strip().splitlines()[0].strip()
    if not first_line or len(first_line) > 160:
        return default
    if any(ord(character) < 32 for character in first_line):
        return default
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._+()\-]*", first_line):
        return default
    if re.search(r"(?i)(?:api[_-]?key|token|password|secret|sk-|ghp_)", first_line):
        return default
    return first_line


def _check_cli(
    codex_command: str,
    codex_home: Path,
    timeout: int,
) -> tuple[CheckResult, str]:
    try:
        completed = subprocess.run(
            [codex_command, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "CODEX_HOME": str(codex_home)},
            timeout=min(timeout, 30),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return (
            CheckResult(BLOCKED, reason="Codex CLI is missing or unusable"),
            "unknown",
        )
    version = _display_value(completed.stdout)
    if completed.returncode != 0 or version == "unknown":
        return (
            CheckResult(BLOCKED, reason="Codex CLI is missing or unusable"),
            "unknown",
        )
    return CheckResult(PASS), version


@contextmanager
def _codex_home_environment(codex_home: Path):
    previous = os.environ.get("CODEX_HOME")
    os.environ["CODEX_HOME"] = str(codex_home)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("CODEX_HOME", None)
        else:
            os.environ["CODEX_HOME"] = previous


def _check_capability(
    codex_command: str,
    codex_home: Path,
    timeout: int,
) -> CheckResult:
    try:
        with _codex_home_environment(codex_home):
            payload = run_probe(codex_command, timeout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return CheckResult(
            REVIEW,
            reason="Luna capability probe failed",
            evidence=("five-effort probe did not complete",),
            targeted_review="Luna capability",
        )
    rows = payload.get("results") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        unsupported = list(EFFORTS)
    else:
        by_effort = {
            item.get("effort"): item
            for item in rows
            if isinstance(item, Mapping) and item.get("effort") in EFFORTS
        }
        unsupported = [
            effort
            for effort in EFFORTS
            if not isinstance(by_effort.get(effort), Mapping)
            or by_effort[effort].get("supported") is not True
        ]
    if unsupported or payload.get("all_supported") is not True:
        return CheckResult(
            REVIEW,
            reason="Luna capability mismatch",
            evidence=(f"unsupported efforts: {','.join(unsupported) or 'unknown'}",),
            targeted_review="Luna capability",
        )
    return CheckResult(PASS)


def _selector_command(
    *,
    python_command: str,
    selector_path: Path,
    codex_home: Path,
) -> list[str]:
    return [
        python_command,
        "-B",
        str(selector_path),
        "--status-json",
        "--codex-home",
        str(codex_home),
        "--state-dir",
        str(codex_home / "sol-luna-v4" / "state"),
        "--project-dir",
        str(PROJECT_ROOT),
    ]


def _check_selector(
    *,
    python_command: str,
    codex_home: Path,
    timeout: int,
) -> SelectorObservation:
    selector_path = codex_home / "sol-luna-v4" / "selector.py"
    state_dir = codex_home / "sol-luna-v4" / "state"
    try:
        state_before = _fingerprint_tree(state_dir)
        completed = subprocess.run(
            _selector_command(
                python_command=python_command,
                selector_path=selector_path,
                codex_home=codex_home,
            ),
            cwd=PROJECT_ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=min(timeout, 60),
            check=False,
        )
        state_after = _fingerprint_tree(state_dir)
    except (OSError, subprocess.TimeoutExpired, HarnessFailure):
        return SelectorObservation(
            CheckResult(
                REVIEW,
                reason="Selector status path failed",
                evidence=("read-only status did not complete",),
                targeted_review="selector status",
            )
        )
    if state_before != state_after:
        return SelectorObservation(
            CheckResult(
                REVIEW,
                reason="Selector status changed selector state",
                evidence=("sol-luna-v4/state",),
                targeted_review="selector read-only behavior",
            )
        )
    if completed.returncode != 0:
        return SelectorObservation(
            CheckResult(
                REVIEW,
                reason="Selector status path failed",
                evidence=("status command returned non-zero",),
                targeted_review="selector status",
            )
        )
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        payload = None
    if not isinstance(payload, Mapping):
        return SelectorObservation(
            CheckResult(
                REVIEW,
                reason="Selector status output is invalid",
                evidence=("status JSON was not an object",),
                targeted_review="selector status schema",
            )
        )
    health = payload.get("health")
    if (
        payload.get("diagnostic_schema_version") != 1
        or health not in {"Healthy", "Degraded", "Unavailable", "Misconfigured"}
        or not isinstance(payload.get("reason_codes"), list)
    ):
        reason_codes = payload.get("reason_codes")
        rendered_codes = ",".join(
            code
            for code in reason_codes
            if isinstance(code, str) and re.fullmatch(r"[A-Z0-9_]+", code)
        ) if isinstance(reason_codes, list) else "status mismatch"
        return SelectorObservation(
            CheckResult(
                REVIEW,
                reason="Selector status is not compatible",
                evidence=(rendered_codes or "status mismatch",),
                targeted_review="selector status",
            ),
            payload,
        )
    if payload.get("selection_initialized") is True:
        effort = payload.get("selected_effort")
        role = payload.get("selected_role")
        if effort not in EFFORTS or role != f"luna_{effort}":
            return SelectorObservation(
                CheckResult(
                    REVIEW,
                    reason="Selector selected role is invalid",
                    evidence=("selected role/effort mismatch",),
                    targeted_review="selector selection metadata",
                ),
                payload,
            )
    return SelectorObservation(CheckResult(PASS), payload)


def _delegation_prompt(role: str, effort: str, receipt: str) -> str:
    selection = json.dumps(
        {"selected_effort": effort, "selected_role": role},
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"""Controlled read-only Sol/Luna compatibility smoke.
Do not read or write files, run commands, browse, call selector or status, inspect
configuration, or use any tool except spawn_agent and wait_agent.

Saved read-only selection metadata: {selection}

Spawn exactly one direct native custom-agent child with agent_type {role} and
fork_turns \"none\". The child must return exactly {CHILD_LITERAL}, use no tools,
and spawn no descendants. Wait until it completes. Do not spawn another child.

If and only if the child completed with the exact literal, state that fact and
make the final line exactly:
{receipt}
"""


def _delegation_rollout_scope(
    rollout_paths: set[Path],
    *,
    expected_receipt: str,
) -> set[Path]:
    try:
        records = {path: _load_json_lines(path) for path in rollout_paths}
        metadata = {path: _session_metadata(rows) for path, rows in records.items()}
        if any(not isinstance(meta, Mapping) for meta in metadata.values()):
            raise HarnessFailure("rollout evidence is malformed")
        parent_candidates = []
        for path, meta in metadata.items():
            if meta.get("parent_thread_id") or meta.get("agent_role"):
                continue
            final_lines = [
                line.strip()
                for line in _final_assistant_text(records[path]).splitlines()
                if line.strip()
            ]
            if final_lines and final_lines[-1] == expected_receipt:
                parent_candidates.append(path)
        if len(parent_candidates) != 1:
            raise HarnessFailure(
                f"expected one compatibility parent, found {len(parent_candidates)}"
            )
        scope = {parent_candidates[0]}
        frontier = {metadata[parent_candidates[0]].get("id")}
        while frontier:
            descendants = {
                path
                for path, meta in metadata.items()
                if path not in scope and meta.get("parent_thread_id") in frontier
            }
            scope.update(descendants)
            frontier = {metadata[path].get("id") for path in descendants}
        return scope
    except (AttributeError, KeyError, TypeError) as exc:
        raise HarnessFailure("rollout evidence is malformed") from exc


def _compatibility_rollout_files(codex_home: Path) -> set[Path]:
    return _rollout_files(codex_home) | set(
        (codex_home / "sessions").glob("**/*.jsonl")
    )


def _wait_for_delegation_evidence(
    *,
    codex_home: Path,
    before_rollouts: set[Path],
    expected_role: str,
    expected_effort: str,
    expected_receipt: str,
    timeout: int,
) -> None:
    deadline = time.monotonic() + min(timeout, 5)
    last_error: BaseException | None = None
    while True:
        try:
            new_rollouts = _compatibility_rollout_files(codex_home) - before_rollouts
            rollout_scope = _delegation_rollout_scope(
                new_rollouts,
                expected_receipt=expected_receipt,
            )
            _validate_runtime_case(
                rollout_scope,
                expected_role=expected_role,
                expected_effort=expected_effort,
                expected_literal=CHILD_LITERAL,
                expected_receipt=expected_receipt,
            )
            return
        except (OSError, ValueError, KeyError, TypeError, AttributeError, HarnessFailure) as exc:
            last_error = exc
        if time.monotonic() >= deadline:
            raise HarnessFailure("delegation evidence did not settle") from last_error
        time.sleep(0.25)


def _delegation_failure_evidence(error: BaseException) -> str:
    current: BaseException | None = error
    messages = []
    while current is not None:
        message = str(current)
        if re.fullmatch(
            r"(?:rollout .*|spawn_agent arguments|child source metadata) "
            r"(?:is |are )?malformed(?: at line [0-9]+)?",
            message,
        ):
            messages.append("rollout evidence is malformed")
            current = current.__cause__
            continue
        if re.fullmatch(
            r"(?:delegation evidence did not settle|"
            r"expected one compatibility parent, found [0-9]+|"
            r"rollout evidence is malformed|"
            r"expected one direct child, found [0-9]+|"
            r"expected one parent rollout, found [0-9]+|"
            r"expected one spawn_agent call, found [0-9]+|"
            r"unexpected parent tool calls: \[[A-Za-z0-9_', ]*\]|"
            r"child [A-Za-z0-9 -]+|"
            r"parent Receipt does not match the saved selection)",
            message,
        ):
            messages.append(message)
        current = current.__cause__
    return messages[-1] if messages else "one direct native Luna child was not attested"


def _check_delegation(
    *,
    codex_command: str,
    codex_home: Path,
    selector_payload: Mapping[str, Any] | None,
    timeout: int,
) -> CheckResult:
    if not selector_payload or selector_payload.get("selection_initialized") is not True:
        return CheckResult(
            REVIEW,
            reason="Daily selection is not initialized",
            evidence=("delegation role was not selected",),
            targeted_review="selector initialization before delegation",
        )
    role = selector_payload.get("selected_role")
    effort = selector_payload.get("selected_effort")
    if effort not in EFFORTS or role != f"luna_{effort}":
        return CheckResult(
            REVIEW,
            reason="Delegation role metadata is invalid",
            evidence=("selected role/effort mismatch",),
            targeted_review="delegation metadata",
        )
    receipt = f"Sol/Luna: delegated · {role} ×1"
    try:
        before_rollouts = _compatibility_rollout_files(codex_home)
        state_dir = codex_home / "sol-luna-v4" / "state"
        state_before = _fingerprint_tree(state_dir)
        child_environment = {
            **os.environ,
            "CODEX_HOME": str(codex_home),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        codex_args = [
                codex_command,
                "exec",
                "--strict-config",
                "--json",
                "--skip-git-repo-check",
                "-s",
                "read-only",
                "-C",
                str(PROJECT_ROOT),
                "-",
        ]
        completed = subprocess.run(
            codex_args,
            cwd=PROJECT_ROOT,
            env=child_environment,
            input=_delegation_prompt(role, effort, receipt),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        state_after = _fingerprint_tree(state_dir)
    except (OSError, subprocess.TimeoutExpired, HarnessFailure):
        return CheckResult(
            REVIEW,
            reason="Delegation smoke failed",
            evidence=("one-child delegation did not complete",),
            targeted_review="native delegation",
        )
    if state_before != state_after:
        return CheckResult(
            REVIEW,
            reason="Delegation changed selector state",
            evidence=("sol-luna-v4/state",),
            targeted_review="delegation selector-state isolation",
        )
    if completed.returncode != 0:
        return CheckResult(
            REVIEW,
            reason="Delegation command failed",
            evidence=("codex exec returned non-zero",),
            targeted_review="native delegation",
        )
    try:
        _wait_for_delegation_evidence(
            codex_home=codex_home,
            before_rollouts=before_rollouts,
            expected_role=role,
            expected_effort=effort,
            expected_receipt=receipt,
            timeout=timeout,
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError, HarnessFailure) as exc:
        return CheckResult(
            REVIEW,
            reason="Delegation evidence is incompatible",
            evidence=(_delegation_failure_evidence(exc),),
            targeted_review="native delegation evidence",
        )
    return CheckResult(PASS)


def _capture_runtime(
    codex_home: Path,
    approved_codex_db_paths: frozenset[str] | None = None,
) -> RuntimeObservation:
    approved = approved_codex_db_paths
    if approved is None:
        inventory = _inventory_tree(
            codex_home,
            excluded_relatives=(AUTH_RUNTIME_RELATIVE,),
            hash_file=lambda _: False,
        )
        approved = _codex_db_allowlist_from_entries(inventory["entries"])
    snapshot = _unexpected_write_snapshot(
        codex_home,
        approved_codex_db_paths=approved,
    )
    return RuntimeObservation(snapshot, approved)


def _sanitize_relative(relative: str) -> str | None:
    normalized = relative.replace("\\", "/")
    path = Path(normalized)
    if path.is_absolute() or ".." in path.parts:
        return None
    parts = ["<id>" if UUID_COMPONENT.fullmatch(part) else part for part in path.parts]
    return "/".join(parts)


def _private_path_fingerprints(paths: list[str]) -> tuple[str, ...]:
    normalized = sorted(
        dict.fromkeys(
            sanitized
            for relative in paths
            if (sanitized := _sanitize_relative(relative)) is not None
        )
    )
    return tuple(
        f"sha256:{hashlib.sha256(relative.encode('utf-8')).hexdigest()[:12]}"
        for relative in normalized
    )


def _minimal_relative_paths(paths: list[str]) -> tuple[str, ...]:
    rendered = sorted(
        dict.fromkeys(
            sanitized
            for relative in paths
            if (sanitized := _sanitize_relative(relative)) is not None
        ),
        key=lambda item: (item.count("/"), item),
    )
    roots: list[str] = []
    for relative in rendered:
        if not any(relative == root or relative.startswith(f"{root}/") for root in roots):
            roots.append(relative)
    return tuple(roots)


def _runtime_result(
    before: RuntimeObservation | None,
    after: RuntimeObservation | None,
) -> CheckResult:
    if before is None or after is None:
        return CheckResult(
            REVIEW,
            reason="Runtime contract snapshot failed",
            evidence=("runtime observation was incomplete",),
            targeted_review="runtime snapshot compatibility",
        )
    changed = _changed_entry_paths(before.snapshot, after.snapshot)
    contract_changes = [
        relative
        for relative in changed
        if _runtime_path_category(relative, before.approved_codex_db_paths)
        != PROTECTED_SOL_LUNA_STATE
    ]
    unknown = [
        relative
        for relative in contract_changes
        if _runtime_path_category(relative, before.approved_codex_db_paths) == UNKNOWN
    ]
    invalid_known = [relative for relative in contract_changes if relative not in unknown]
    minimal_unknown = _private_path_fingerprints(unknown)
    minimal_known = _private_path_fingerprints(invalid_known)
    if minimal_unknown or minimal_known:
        evidence = []
        if minimal_unknown:
            evidence.append(f"UNKNOWN path fingerprints: {','.join(minimal_unknown)}")
        if minimal_known:
            evidence.append(
                f"contract-invalid path fingerprints: {','.join(minimal_known)}"
            )
        return CheckResult(
            REVIEW,
            reason=(
                "New runtime UNKNOWN observed"
                if minimal_unknown
                else "Runtime contract-invalid change observed"
            ),
            evidence=tuple(evidence),
            targeted_review="runtime contract for reported relative paths",
        )
    return CheckResult(PASS)


def _not_run(reason: str) -> CheckResult:
    return CheckResult(REVIEW, reason=reason, evidence=("check not run",))


def run_smoke(
    *,
    codex_home: Path,
    codex_command: str,
    python_command: str,
    desktop_version: str,
    timeout: int,
) -> SmokeReport:
    protected_before: Mapping[str, Any] | None = None
    runtime_before: RuntimeObservation | None = None
    try:
        protected_before = _protected_state_snapshot(codex_home)
        _validate_protected_state_snapshot(protected_before)
    except (OSError, ValueError, HarnessFailure):
        protected_before = None
    try:
        runtime_before = _capture_runtime(codex_home)
    except (OSError, ValueError, HarnessFailure):
        runtime_before = None

    cli, cli_version = _check_cli(codex_command, codex_home, timeout)
    if cli.status == BLOCKED:
        capability = _not_run("Codex CLI is blocked")
        selector_result = _not_run("Codex CLI is blocked")
        delegation = _not_run("Codex CLI is blocked")
    elif protected_before is None:
        capability = _not_run("Protected state baseline is unavailable")
        selector_result = _not_run("Protected state baseline is unavailable")
        delegation = _not_run("Protected state baseline is unavailable")
    else:
        capability = _check_capability(codex_command, codex_home, timeout)
        selector_observation = _check_selector(
            python_command=python_command,
            codex_home=codex_home,
            timeout=timeout,
        )
        selector_result = selector_observation.result
        delegation = _check_delegation(
            codex_command=codex_command,
            codex_home=codex_home,
            selector_payload=selector_observation.payload,
            timeout=timeout,
        )

    protected_after: Mapping[str, Any] | None = None
    try:
        protected_after = _protected_state_snapshot(codex_home)
        _validate_protected_state_snapshot(protected_after)
    except (OSError, ValueError, HarnessFailure):
        protected_after = None
    if protected_before is None or protected_after is None:
        protected = CheckResult(
            FAIL,
            reason="Protected state could not be validated",
            evidence=("protected snapshot unavailable",),
            targeted_review="protected state integrity",
        )
    else:
        protected_changes = _changed_entry_paths(protected_before, protected_after)
        if protected_changes:
            protected = CheckResult(
                FAIL,
                reason="Protected state changed",
                evidence=(
                    f"changed protected paths: {','.join(_minimal_relative_paths(protected_changes))}",
                ),
                targeted_review="protected state integrity",
            )
        else:
            protected = CheckResult(PASS)

    runtime_after: RuntimeObservation | None = None
    try:
        frozen_approved = (
            runtime_before.approved_codex_db_paths if runtime_before is not None else None
        )
        runtime_after = _capture_runtime(codex_home, frozen_approved)
    except (OSError, ValueError, HarnessFailure):
        runtime_after = None
    runtime = _runtime_result(runtime_before, runtime_after)

    if cli.status == BLOCKED:
        compatibility = BLOCKED
    elif any(
        result.status in {REVIEW, FAIL}
        for result in (capability, selector_result, delegation, protected, runtime)
    ):
        compatibility = REVIEW
    else:
        compatibility = PASS
    return SmokeReport(
        desktop_version=_display_value(desktop_version),
        cli_version=cli_version,
        cli=cli,
        capability=capability,
        selector=selector_result,
        delegation=delegation,
        protected=protected,
        runtime=runtime,
        compatibility=compatibility,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    default_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    parser.add_argument("--codex-home", type=Path, default=default_home)
    parser.add_argument("--codex-command", default=shutil.which("codex") or "codex")
    parser.add_argument("--python-command", default=sys.executable)
    parser.add_argument("--desktop-version", default="unknown")
    parser.add_argument("--timeout", type=int, default=300)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.timeout < 1:
        raise SystemExit("--timeout must be positive")
    report = run_smoke(
        codex_home=args.codex_home.resolve(strict=False),
        codex_command=args.codex_command,
        python_command=args.python_command,
        desktop_version=args.desktop_version,
        timeout=args.timeout,
    )
    print(report.render())
    return {PASS: 0, REVIEW: 1, BLOCKED: 2}[report.compatibility]


if __name__ == "__main__":
    raise SystemExit(main())
