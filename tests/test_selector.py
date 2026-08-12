import json
import io
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.selector import (
    BJT,
    EFFORTS,
    NO_PROFILE_STATUS,
    SelectionUnavailable,
    SnapshotInvalid,
    adapt_modeldial_snapshot,
    ensure_daily_profile,
    fetch_modeldial_snapshot,
    main,
    parse_radar_html,
    select_snapshot,
    validate_snapshot,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "modeldial"


def load_fixture(name):
    with (FIXTURES / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class SelectorTests(unittest.TestCase):
    def test_complete_five_efforts(self):
        snapshot = validate_snapshot(load_fixture("complete.json"))
        self.assertEqual(set(snapshot["scores"]), set(EFFORTS))

    def test_highest_score_wins(self):
        profile = select_snapshot(load_fixture("complete.json"))
        self.assertEqual(profile["source_winner_effort"], "high")
        self.assertEqual(profile["selected_role"], "luna_high")
        self.assertFalse(profile["capability_degraded"])

    def test_tie_uses_lower_effort(self):
        profile = select_snapshot(load_fixture("tie.json"))
        self.assertEqual(profile["source_winner_effort"], "low")
        self.assertEqual(profile["selected_effort"], "low")

    def test_missing_row_is_invalid(self):
        with self.assertRaises(SnapshotInvalid):
            validate_snapshot(load_fixture("missing-row.json"))

    def test_invalid_live_uses_lkg(self):
        with tempfile.TemporaryDirectory() as directory:
            day_one = datetime(2026, 8, 11, 9, tzinfo=BJT)
            day_two = datetime(2026, 8, 12, 9, tzinfo=BJT)
            ensure_daily_profile(
                load_fixture("complete.json"), state_dir=directory, now=day_one
            )
            profile = ensure_daily_profile(
                load_fixture("missing-row.json"), state_dir=directory, now=day_two
            )
            self.assertTrue(profile["fallback"])
            self.assertEqual(profile["snapshot_id"], "fixture-complete-001")

    def test_first_install_failure_is_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SelectionUnavailable):
                ensure_daily_profile(
                    load_fixture("missing-row.json"), state_dir=directory
                )
            self.assertFalse((Path(directory) / "daily-profile.json").exists())

    def test_unsupported_source_winner_degrades_capability(self):
        profile = select_snapshot(
            load_fixture("max-wins.json"),
            supported_efforts=("low", "medium", "high"),
        )
        self.assertEqual(profile["source_winner_effort"], "max")
        self.assertEqual(profile["selected_effort"], "high")
        self.assertEqual(profile["selected_role"], "luna_high")
        self.assertTrue(profile["capability_degraded"])

    def test_bjt_day_rollover_reselects(self):
        with tempfile.TemporaryDirectory() as directory:
            before_midnight = datetime(2026, 8, 11, 23, 59, tzinfo=BJT)
            after_midnight = datetime(2026, 8, 12, 0, 1, tzinfo=BJT)
            first = ensure_daily_profile(
                load_fixture("complete.json"),
                state_dir=directory,
                now=before_midnight,
            )
            second = ensure_daily_profile(
                load_fixture("max-wins.json"),
                state_dir=directory,
                now=after_midnight,
            )
            self.assertEqual(first["selected_effort"], "high")
            self.assertEqual(second["selected_effort"], "max")

    def test_same_day_does_not_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            morning = datetime(2026, 8, 11, 8, tzinfo=BJT)
            evening = datetime(2026, 8, 11, 20, tzinfo=BJT)
            first = ensure_daily_profile(
                load_fixture("complete.json"), state_dir=directory, now=morning
            )
            second = ensure_daily_profile(
                load_fixture("max-wins.json"), state_dir=directory, now=evening
            )
            self.assertEqual(first, second)
            self.assertEqual(second["snapshot_id"], "fixture-complete-001")

    def test_same_day_does_not_call_live_fetcher(self):
        with tempfile.TemporaryDirectory() as directory:
            morning = datetime(2026, 8, 11, 8, tzinfo=BJT)
            evening = datetime(2026, 8, 11, 20, tzinfo=BJT)
            ensure_daily_profile(
                load_fixture("complete.json"), state_dir=directory, now=morning
            )

            def unexpected_fetch():
                self.fail("same-day selection must not refresh the live source")

            profile = ensure_daily_profile(
                None,
                state_dir=directory,
                now=evening,
                live_fetcher=unexpected_fetch,
            )
            self.assertEqual(profile["snapshot_id"], "fixture-complete-001")

    def test_stale_profile_refreshes_once(self):
        with tempfile.TemporaryDirectory() as directory:
            day_one = datetime(2026, 8, 11, 9, tzinfo=BJT)
            day_two = datetime(2026, 8, 12, 9, tzinfo=BJT)
            ensure_daily_profile(
                load_fixture("complete.json"), state_dir=directory, now=day_one
            )
            calls = []

            def fetch():
                calls.append(1)
                return load_fixture("max-wins.json")

            profile = ensure_daily_profile(
                None, state_dir=directory, now=day_two, live_fetcher=fetch
            )
            self.assertEqual(profile["selected_role"], "luna_max")
            self.assertEqual(len(calls), 1)

    def test_concurrent_first_use_refreshes_only_once(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = 0
            calls_lock = threading.Lock()

            def fetch():
                nonlocal calls
                with calls_lock:
                    calls += 1
                return load_fixture("complete.json")

            def select():
                return ensure_daily_profile(
                    None,
                    state_dir=directory,
                    now=datetime(2026, 8, 12, 9, tzinfo=BJT),
                    live_fetcher=fetch,
                )["selected_role"]

            with ThreadPoolExecutor(max_workers=4) as pool:
                roles = list(pool.map(lambda _: select(), range(4)))
            self.assertEqual(roles, ["luna_high"] * 4)
            self.assertEqual(calls, 1)
            self.assertTrue((Path(directory) / "selector.lock").is_file())

    def test_global_cli_prints_only_role(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(
                    [
                        "--snapshot",
                        str(FIXTURES / "complete.json"),
                        "--state-dir",
                        directory,
                        "--ensure-daily",
                        "--print-role",
                    ]
                )
            self.assertEqual(code, 0)
            self.assertEqual(output.getvalue(), "luna_high\n")

    @patch("src.selector.fetch_modeldial_snapshot", side_effect=SnapshotInvalid("offline"))
    def test_global_cli_fail_closed_status(self, _fetch):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(
                    [
                        "--state-dir",
                        directory,
                        "--ensure-daily",
                        "--print-role",
                    ]
                )
            self.assertEqual(code, 3)
            self.assertEqual(output.getvalue(), f"{NO_PROFILE_STATUS}\n")
            self.assertFalse((Path(directory) / "daily-profile.json").exists())
            self.assertFalse((Path(directory) / "last-good-profile.json").exists())

    def test_ultra_never_enters_allowlist(self):
        payload = load_fixture("complete.json")
        payload["rows"].append(
            {"model": "gpt-5.6-luna", "effort": "ultra", "score": 999.0}
        )
        profile = select_snapshot(payload)
        self.assertNotEqual(profile["source_winner_effort"], "ultra")
        with self.assertRaises(SelectionUnavailable):
            select_snapshot(payload, supported_efforts=("ultra",))

    def test_first_party_snapshot_adapter(self):
        adapted = adapt_modeldial_snapshot(
            load_fixture("first-party-complete.json"),
            now=datetime(2026, 8, 11, 9, tzinfo=BJT),
        )
        profile = select_snapshot(adapted)
        self.assertEqual(profile["selected_effort"], "max")
        self.assertEqual(profile["source_mode"], "live_json")

    def test_first_party_snapshot_rejects_cross_group_rows(self):
        payload = load_fixture("first-party-complete.json")
        payload["entries"][-1]["source_evidence_group_id"] = "other-run"
        with self.assertRaises(SnapshotInvalid):
            adapt_modeldial_snapshot(
                payload, now=datetime(2026, 8, 11, 9, tzinfo=BJT)
            )

    def test_radar_html_fallback_parser(self):
        html = (FIXTURES / "radar-complete.html").read_text(encoding="utf-8")
        adapted = parse_radar_html(
            html, now=datetime(2026, 8, 11, 9, tzinfo=BJT)
        )
        profile = select_snapshot(adapted)
        self.assertEqual(profile["selected_effort"], "max")
        self.assertEqual(profile["source_mode"], "radar_html")

    @patch("src.selector._fetch_bytes")
    def test_live_fetch_falls_back_from_json_to_radar(self, fetch):
        html = (FIXTURES / "radar-complete.html").read_bytes()
        fetch.side_effect = [
            (b"not-json", "https://modeldial.com/data/reference-snapshots/latest.json"),
            (html, "https://modeldial.com/zh-CN/radar"),
        ]
        adapted = fetch_modeldial_snapshot()
        self.assertEqual(adapted["source_mode"], "radar_html")
        self.assertEqual(fetch.call_count, 2)


if __name__ == "__main__":
    unittest.main()
