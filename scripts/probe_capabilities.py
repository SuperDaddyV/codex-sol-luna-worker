"""Probe direct local availability of the five allowed Luna effort levels."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


EFFORTS = ("low", "medium", "high", "xhigh", "max")
BJT = timezone(timedelta(hours=8), name="BJT")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = PROJECT_ROOT / ".var" / "capabilities.json"


def build_command(codex: str, effort: str) -> list[str]:
    marker = f"LUNA_CAPABILITY_{effort.upper()}_OK"
    return [
        codex,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--strict-config",
        "--model",
        "gpt-5.6-luna",
        "--config",
        f'model_reasoning_effort="{effort}"',
        "--sandbox",
        "read-only",
        "--cd",
        str(PROJECT_ROOT),
        f"Return EXACTLY: {marker}",
    ]


def _codex_version(codex: str) -> str:
    result = subprocess.run(
        [codex, "--version"], capture_output=True, text=True, timeout=10, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def run_probe(codex: str, timeout: int) -> dict:
    results = []
    for effort in EFFORTS:
        marker = f"LUNA_CAPABILITY_{effort.upper()}_OK"
        try:
            result = subprocess.run(
                build_command(codex, effort),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=os.environ.copy(),
            )
            supported = result.returncode == 0
            response_exact = result.stdout.strip() == marker
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            supported = False
            response_exact = False
            exit_code = None
        results.append(
            {
                "effort": effort,
                "supported": supported,
                "response_exact": response_exact,
                "exit_code": exit_code,
            }
        )

    return {
        "model": "gpt-5.6-luna",
        "codex_version": _codex_version(codex),
        "probed_at_bjt": datetime.now(BJT).isoformat(),
        "all_supported": all(item["supported"] for item in results),
        "results": results,
    }


def write_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run five ephemeral Codex calls; otherwise print a dry-run plan",
    )
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args(argv)

    codex = shutil.which("codex")
    if codex is None:
        parser.exit(2, "probe: codex executable not found\n")

    if not args.execute:
        plan = {
            "dry_run": True,
            "model": "gpt-5.6-luna",
            "efforts": list(EFFORTS),
            "global_config_ignored": True,
            "sessions_ephemeral": True,
            "state_path": str(args.state),
        }
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    payload = run_probe(codex, args.timeout)
    write_state(args.state.resolve(), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_supported"] else 1


if __name__ == "__main__":
    sys.exit(main())
