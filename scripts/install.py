"""Generate a conflict-aware installation plan without changing CODEX_HOME."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_PLATFORMS = {"Windows", "Linux", "Darwin"}

# Keep this inventory explicit.  A future installer must not accidentally pick up
# an experiment, a legacy ``slr_*`` role, or another file added under
# ``.codex/agents``.  The five names below are the only stable Luna roles in the
# v4.0.0-rc1 plan.
STABLE_AGENT_FILES = (
    "luna-low.toml",
    "luna-medium.toml",
    "luna-high.toml",
    "luna-xhigh.toml",
    "luna-max.toml",
)

# This is a plan-only inventory.  ``destination`` is deliberately expressed
# relative to CODEX_HOME so the rendered plan remains portable; no item is
# written by this module.  The merge strategies make clear that policy and
# config files are not blind overwrites.
FUTURE_ARTIFACTS = (
    {
        "source": ".codex/agents/luna-low.toml",
        "destination": "agents/luna-low.toml",
        "strategy": "agent-conflict-check",
        "kind": "stable-agent",
    },
    {
        "source": ".codex/agents/luna-medium.toml",
        "destination": "agents/luna-medium.toml",
        "strategy": "agent-conflict-check",
        "kind": "stable-agent",
    },
    {
        "source": ".codex/agents/luna-high.toml",
        "destination": "agents/luna-high.toml",
        "strategy": "agent-conflict-check",
        "kind": "stable-agent",
    },
    {
        "source": ".codex/agents/luna-xhigh.toml",
        "destination": "agents/luna-xhigh.toml",
        "strategy": "agent-conflict-check",
        "kind": "stable-agent",
    },
    {
        "source": ".codex/agents/luna-max.toml",
        "destination": "agents/luna-max.toml",
        "strategy": "agent-conflict-check",
        "kind": "stable-agent",
    },
    {
        "source": "AGENTS.md",
        "destination": "AGENTS.md",
        "strategy": "merge-policy",
        "kind": "delegation-policy",
    },
    {
        "source": "src/selector.py",
        "destination": "sol-luna-v4/selector.py",
        "strategy": "copy-if-absent",
        "kind": "daily-selector",
    },
    {
        "source": ".codex/config.toml",
        "destination": "config.toml",
        "strategy": "merge-agents-config",
        "kind": "project-config",
    },
)


class UnsafeTarget(ValueError):
    """Raised when a future installation target is too broad or overlaps the repo."""


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


def validate_target(target: Path, project_root: Path = PROJECT_ROOT) -> None:
    target = target.resolve(strict=False)
    project_root = project_root.resolve(strict=False)
    if target == Path(target.anchor):
        raise UnsafeTarget("CODEX_HOME cannot be a filesystem root")
    if target == project_root or project_root in target.parents:
        raise UnsafeTarget("CODEX_HOME cannot be inside the project repository")


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
) -> dict:
    target = target.resolve(strict=False)
    project_root = project_root.resolve(strict=False)
    validate_target(target, project_root)
    current_platform = platform.system() if platform_name is None else platform_name
    timestamp = (generated_at or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")

    actions = []
    conflicts = []
    source_dir = project_root / ".codex" / "agents"
    for filename in STABLE_AGENT_FILES:
        source = source_dir / filename
        destination = target / "agents" / source.name
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
            {
                "source": str(source),
                "destination": str(destination),
                "status": status,
            }
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly request the only supported release-candidate mode",
    )
    parser.add_argument("--codex-home", help="Target CODEX_HOME to inspect")
    args = parser.parse_args(argv)

    try:
        target = resolve_codex_home(args.codex_home)
        plan = build_plan(target)
    except UnsafeTarget as exc:
        parser.exit(2, f"install plan: {exc}\n")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
