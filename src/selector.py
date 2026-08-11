"""Fixtures-first Daily ModelDial selector for stable Luna custom-agent roles."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


LUNA_MODEL = "gpt-5.6-luna"
EFFORTS = ("low", "medium", "high", "xhigh", "max")
ROLE_BY_EFFORT = {effort: f"luna_{effort}" for effort in EFFORTS}
BJT = timezone(timedelta(hours=8), name="BJT")
UTC = timezone.utc
MODELDIAL_LATEST_URL = "https://modeldial.com/data/reference-snapshots/latest.json"
MODELDIAL_RADAR_URL = "https://modeldial.com/zh-CN/radar"
MODELDIAL_ALLOWED_HOSTS = frozenset({"modeldial.com", "reference.modeldial.com"})
MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024


class SnapshotInvalid(ValueError):
    """Raised when a published snapshot cannot be compared safely."""


class SelectionUnavailable(RuntimeError):
    """Raised when neither a valid live snapshot nor a valid LKG exists."""


def _aware_bjt(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(BJT)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return now.astimezone(BJT)


def _parse_published_at(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotInvalid("published_at must be a non-empty ISO 8601 string")
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise SnapshotInvalid("published_at must be valid ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SnapshotInvalid("published_at must include a UTC offset")
    return value


def validate_snapshot(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one complete published snapshot and return normalized scores."""

    if not isinstance(payload, Mapping):
        raise SnapshotInvalid("snapshot must be an object")

    snapshot_id = payload.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        raise SnapshotInvalid("snapshot_id must be a non-empty string")

    published_at = _parse_published_at(payload.get("published_at"))
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise SnapshotInvalid("rows must be a list")

    scores: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, Mapping) or row.get("model") != LUNA_MODEL:
            continue
        effort = row.get("effort")
        if effort not in EFFORTS:
            continue
        if effort in scores:
            raise SnapshotInvalid(f"duplicate Luna row: {effort}")
        score = row.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise SnapshotInvalid(f"score must be numeric for: {effort}")
        normalized_score = float(score)
        if not math.isfinite(normalized_score):
            raise SnapshotInvalid(f"score must be finite for: {effort}")
        scores[effort] = normalized_score

    missing = [effort for effort in EFFORTS if effort not in scores]
    if missing:
        raise SnapshotInvalid(f"missing canonical Luna rows: {', '.join(missing)}")

    normalized = {
        "snapshot_id": snapshot_id,
        "published_at": published_at,
        "scores": scores,
    }
    for key in ("source_mode", "source_url", "snapshot_hash"):
        if isinstance(payload.get(key), str) and payload[key]:
            normalized[key] = payload[key]
    return normalized


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SnapshotInvalid(f"ModelDial snapshot lacks {key}")
    return value


def adapt_modeldial_snapshot(
    payload: Mapping[str, Any],
    *,
    source_url: str = MODELDIAL_LATEST_URL,
    source_mode: str = "live_json",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate a first-party ModelDial publication and map it to selector rows."""

    if not isinstance(payload, Mapping):
        raise SnapshotInvalid("ModelDial snapshot must be an object")
    if payload.get("kind") != "first_party_snapshot" or payload.get("status") != "complete":
        raise SnapshotInvalid("ModelDial snapshot is not a complete publication")
    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping) or provenance.get("public_official_snapshot") is not True:
        raise SnapshotInvalid("ModelDial snapshot lacks first-party provenance")

    batch_id = _required_text(payload, "batch_id")
    published_at = _parse_published_at(payload.get("published_at"))
    published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    current = datetime.now(UTC) if now is None else now
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if published > current.astimezone(UTC):
        raise SnapshotInvalid("ModelDial snapshot publication time is in the future")

    for key in (
        "question_pack_id",
        "question_pack_version",
        "grader_version",
        "evaluation_profile",
        "score_baseline_id",
        "batch_sha256",
    ):
        _required_text(payload, key)

    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise SnapshotInvalid("ModelDial entries must be a list")

    rows = []
    evidence_groups = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        configuration = entry.get("model_configuration")
        if not isinstance(configuration, Mapping):
            continue
        if configuration.get("canonical_model_id") != LUNA_MODEL:
            continue
        effort = configuration.get("reasoning_effort")
        if effort not in EFFORTS:
            continue
        if entry.get("advisor_eligible") is not True:
            raise SnapshotInvalid(f"ModelDial Luna row is not advisor eligible: {effort}")
        if entry.get("score_integrity") != "first_party_controlled":
            raise SnapshotInvalid(f"ModelDial Luna row lacks score integrity: {effort}")
        evidence_group = entry.get("source_evidence_group_id")
        if not isinstance(evidence_group, str) or not evidence_group:
            raise SnapshotInvalid(f"ModelDial Luna row lacks evidence group: {effort}")
        evidence_groups.add(evidence_group)
        rows.append({"model": LUNA_MODEL, "effort": effort, "score": entry.get("score")})

    if len(evidence_groups) != 1:
        raise SnapshotInvalid("ModelDial Luna rows do not share one evidence group")

    adapted = {
        "snapshot_id": batch_id,
        "published_at": published_at,
        "rows": rows,
        "source_mode": source_mode,
        "source_url": source_url,
        "snapshot_hash": payload["batch_sha256"],
    }
    validate_snapshot(adapted)
    return adapted


def _validated_modeldial_url(url: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() != "https" or parsed.hostname not in MODELDIAL_ALLOWED_HOSTS:
        raise SnapshotInvalid("ModelDial URL is outside the HTTPS allowlist")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise SnapshotInvalid("credentials and non-standard ports are forbidden")
    return parsed


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validated_modeldial_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch_bytes(url: str, *, expected_type: str, timeout: float) -> tuple[bytes, str]:
    _validated_modeldial_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": expected_type,
            "User-Agent": "codex-sol-luna-worker/4.0-prototype",
        },
        method="GET",
    )
    response = urllib.request.build_opener(_SafeRedirectHandler()).open(
        request, timeout=timeout
    )
    with response:
        final_url = response.geturl()
        _validated_modeldial_url(final_url)
        content_type = response.headers.get_content_type()
        if content_type != expected_type:
            raise SnapshotInvalid(f"ModelDial endpoint did not return {expected_type}")
        body = response.read(MAX_SNAPSHOT_BYTES + 1)
        if len(body) > MAX_SNAPSHOT_BYTES:
            raise SnapshotInvalid("ModelDial snapshot exceeds the size limit")
    return body, final_url


def parse_radar_html(
    html_text: str,
    *,
    source_url: str = MODELDIAL_RADAR_URL,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Extract one complete published Luna snapshot from first-party Radar HTML."""

    identifier = re.search(r'"identifier"\s*:\s*"([^"]+)"', html_text)
    published = re.search(r'"dateModified"\s*:\s*"([^"]+)"', html_text)
    pack = re.search(r'"measurementTechnique"\s*:\s*"ModelDial\s+([^"]+)"', html_text)
    if not identifier or not published or not pack:
        raise SnapshotInvalid("Radar HTML lacks published snapshot metadata")

    labels = {"轻度": "low", "中": "medium", "高": "high", "极高": "xhigh", "最高": "max"}
    row_pattern = re.compile(
        r"<span>\s*gpt-5\.6-luna\s*</span><em>(轻度|中|高|极高|最高)</em>"
        r'.{0,2500}?scoreCell[^>]*><strong>\s*([0-9]+(?:\.[0-9]+)?)\s*</strong>',
        re.IGNORECASE | re.DOTALL,
    )
    scores: dict[str, float] = {}
    for label, score_text in row_pattern.findall(html_text):
        effort = labels[label]
        score = float(score_text)
        if effort in scores and scores[effort] != score:
            raise SnapshotInvalid("Radar HTML contains conflicting Luna scores")
        scores[effort] = score
    if set(scores) != set(EFFORTS):
        raise SnapshotInvalid("Radar HTML lacks one complete Luna five-effort batch")

    grader = re.search(r'grader_version\\?"\s*:\s*\\?"([^"\\]+)', html_text)
    profile = re.search(r'evaluation_profile\\?"\s*:\s*\\?"([^"\\]+)', html_text)
    baseline = re.search(r'score_baseline_id\\?"\s*:\s*\\?"([^"\\]+)', html_text)
    group_id = f"radar-html:{identifier.group(1)}"
    publication = {
        "kind": "first_party_snapshot",
        "status": "complete",
        "batch_id": identifier.group(1),
        "published_at": published.group(1),
        "question_pack_id": "coding-fast",
        "question_pack_version": pack.group(1),
        "grader_version": grader.group(1) if grader else "radar-html-published",
        "evaluation_profile": profile.group(1) if profile else "full",
        "score_baseline_id": baseline.group(1) if baseline else pack.group(1),
        "batch_sha256": "html-sha256:"
        + hashlib.sha256(html_text.encode("utf-8")).hexdigest(),
        "provenance": {"public_official_snapshot": True},
        "entries": [
            {
                "model_configuration": {
                    "canonical_model_id": LUNA_MODEL,
                    "reasoning_effort": effort,
                },
                "advisor_eligible": True,
                "score_integrity": "first_party_controlled",
                "score": scores[effort],
                "source_evidence_group_id": group_id,
            }
            for effort in EFFORTS
        ],
    }
    return adapt_modeldial_snapshot(
        publication, source_url=source_url, source_mode="radar_html", now=now
    )


def fetch_modeldial_snapshot(*, timeout: float = 15.0) -> dict[str, Any]:
    """Fetch first-party JSON, falling back to first-party Radar HTML."""

    try:
        body, final_url = _fetch_bytes(
            MODELDIAL_LATEST_URL, expected_type="application/json", timeout=timeout
        )
        payload = json.loads(body.decode("utf-8"))
        return adapt_modeldial_snapshot(payload, source_url=final_url)
    except (OSError, UnicodeError, json.JSONDecodeError, SnapshotInvalid):
        pass

    try:
        body, final_url = _fetch_bytes(
            MODELDIAL_RADAR_URL, expected_type="text/html", timeout=timeout
        )
        return parse_radar_html(body.decode("utf-8"), source_url=final_url)
    except (OSError, UnicodeError, SnapshotInvalid) as exc:
        raise SnapshotInvalid("both first-party ModelDial sources failed") from exc


def _normalize_supported(supported_efforts: Iterable[str] | None) -> tuple[str, ...]:
    if supported_efforts is None:
        return EFFORTS
    requested = set(supported_efforts)
    unknown = requested.difference(EFFORTS)
    if unknown:
        raise SelectionUnavailable(
            f"unsupported local effort names: {', '.join(sorted(unknown))}"
        )
    supported = tuple(effort for effort in EFFORTS if effort in requested)
    if not supported:
        raise SelectionUnavailable("no locally supported Luna effort")
    return supported


def _winner(scores: Mapping[str, float], efforts: Iterable[str]) -> str:
    rank = {effort: index for index, effort in enumerate(EFFORTS)}
    return min(efforts, key=lambda effort: (-scores[effort], rank[effort]))


def select_snapshot(
    payload: Mapping[str, Any],
    *,
    supported_efforts: Iterable[str] | None = None,
    now: datetime | None = None,
    fallback: bool = False,
) -> dict[str, Any]:
    """Select the source winner and best locally supported stable Luna role."""

    snapshot = validate_snapshot(payload)
    supported = _normalize_supported(supported_efforts)
    source_effort = _winner(snapshot["scores"], EFFORTS)
    selected_effort = _winner(snapshot["scores"], supported)
    selected_at = _aware_bjt(now)

    profile = {
        "source_winner_effort": source_effort,
        "source_winner_score": snapshot["scores"][source_effort],
        "selected_effort": selected_effort,
        "selected_score": snapshot["scores"][selected_effort],
        "selected_role": ROLE_BY_EFFORT[selected_effort],
        "capability_degraded": selected_effort != source_effort,
        "snapshot_id": snapshot["snapshot_id"],
        "published_at": snapshot["published_at"],
        "selected_at_bjt": selected_at.isoformat(),
        "selection_date_bjt": selected_at.date().isoformat(),
        "fallback": fallback,
    }
    for key in ("source_mode", "source_url", "snapshot_hash"):
        if key in snapshot:
            profile[key] = snapshot[key]
    return profile


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _same_bjt_day(profile: Any, now: datetime) -> bool:
    if not isinstance(profile, Mapping):
        return False
    effort = profile.get("selected_effort")
    if effort not in EFFORTS or profile.get("selected_role") != ROLE_BY_EFFORT[effort]:
        return False
    selected_at = profile.get("selected_at_bjt")
    if not isinstance(selected_at, str):
        return False
    try:
        parsed = datetime.fromisoformat(selected_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return False
    return parsed.astimezone(BJT).date() == now.date()


def ensure_daily_profile(
    live_snapshot: Mapping[str, Any] | None,
    *,
    state_dir: str | Path,
    supported_efforts: Iterable[str] | None = None,
    now: datetime | None = None,
    live_fetcher: Callable[[], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return today's profile, selecting once or falling back to the LKG."""

    selected_at = _aware_bjt(now)
    state_root = Path(state_dir)
    profile_path = state_root / "daily-profile.json"
    lkg_path = state_root / "last-good-profile.json"

    if profile_path.is_file():
        try:
            existing = _read_json(profile_path)
        except (OSError, json.JSONDecodeError):
            existing = None
        if _same_bjt_day(existing, selected_at):
            return dict(existing)

    if live_snapshot is None and live_fetcher is not None:
        try:
            live_snapshot = live_fetcher()
        except (OSError, SnapshotInvalid):
            live_snapshot = None

    if live_snapshot is not None:
        try:
            profile = select_snapshot(
                live_snapshot,
                supported_efforts=supported_efforts,
                now=selected_at,
                fallback=False,
            )
        except SnapshotInvalid:
            profile = None
        else:
            _write_json(lkg_path, {"snapshot": dict(live_snapshot)})
            _write_json(profile_path, profile)
            return profile

    try:
        lkg_record = _read_json(lkg_path)
        lkg_snapshot = lkg_record["snapshot"]
        profile = select_snapshot(
            lkg_snapshot,
            supported_efforts=supported_efforts,
            now=selected_at,
            fallback=True,
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, SnapshotInvalid) as exc:
        raise SelectionUnavailable("no valid live snapshot or LKG; Luna is disabled") from exc

    _write_json(profile_path, profile)
    return profile


def _load_optional_snapshot(path: str | None) -> Mapping[str, Any] | None:
    if path is None:
        return None
    try:
        payload = _read_json(Path(path))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    if payload.get("kind") == "first_party_snapshot":
        try:
            return adapt_modeldial_snapshot(payload, source_url=str(Path(path)))
        except SnapshotInvalid:
            return None
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", help="Path to one published snapshot JSON file")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch the verified first-party ModelDial JSON source",
    )
    parser.add_argument("--state-dir", default=".var", help="Repo-local state directory")
    parser.add_argument(
        "--supported",
        default=",".join(EFFORTS),
        help="Comma-separated locally supported efforts",
    )
    args = parser.parse_args(argv)
    if args.live and args.snapshot:
        parser.error("--live and --snapshot are mutually exclusive")
    supported = tuple(item.strip() for item in args.supported.split(",") if item.strip())

    live_snapshot = None if args.live else _load_optional_snapshot(args.snapshot)
    live_fetcher = fetch_modeldial_snapshot if args.live else None

    try:
        profile = ensure_daily_profile(
            live_snapshot,
            state_dir=args.state_dir,
            supported_efforts=supported,
            live_fetcher=live_fetcher,
        )
    except (SelectionUnavailable, ValueError) as exc:
        parser.exit(2, f"selector: {exc}\n")

    print(json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
