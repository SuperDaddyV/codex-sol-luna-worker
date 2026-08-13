import copy
import io
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from src.selector import (
    BJT,
    EFFORTS,
    MODELDIAL_API_URL,
    MODELDIAL_SNAPSHOT_URL,
    NO_PROFILE_STATUS,
    SelectionUnavailable,
    SnapshotInvalid,
    adapt_modeldial_api,
    adapt_modeldial_snapshot,
    ensure_daily_profile,
    fetch_modeldial_snapshot,
    main,
    select_snapshot,
    validate_snapshot,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "modeldial"


def load_fixture(name):
    with (FIXTURES / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def encoded_fixture(name):
    return json.dumps(load_fixture(name)).encode("utf-8")


class ModelDialApiAdapterTests(unittest.TestCase):
    def test_complete_api_payload(self):
        adapted = adapt_modeldial_api(
            load_fixture("api-complete.json"),
            now=datetime(2026, 8, 13, 8, tzinfo=BJT),
        )
        normalized = validate_snapshot(adapted)
        self.assertEqual(set(normalized["scores"]), set(EFFORTS))
        self.assertEqual(adapted["source_mode"], "modeldial_api_v1")
        self.assertEqual(adapted["source_url"], MODELDIAL_API_URL)

    def test_schema_missing_or_malformed_is_invalid(self):
        for value in (None, "", 1):
            with self.subTest(value=value):
                payload = load_fixture("api-complete.json")
                if value is None:
                    del payload["schemaVersion"]
                else:
                    payload["schemaVersion"] = value
                with self.assertRaisesRegex(SnapshotInvalid, "API_SCHEMA_INVALID"):
                    adapt_modeldial_api(payload)

    def test_unsupported_schema_is_rejected(self):
        payload = load_fixture("api-complete.json")
        payload["schemaVersion"] = "2.0"
        with self.assertRaisesRegex(SnapshotInvalid, "API_SCHEMA_UNSUPPORTED"):
            adapt_modeldial_api(payload)

    def test_source_kind_mismatch_is_rejected(self):
        payload = load_fixture("api-complete.json")
        payload["source"]["kind"] = "third_party"
        with self.assertRaises(SnapshotInvalid):
            adapt_modeldial_api(payload)

    def test_batch_id_is_required(self):
        payload = load_fixture("api-complete.json")
        payload["batch"]["id"] = ""
        with self.assertRaises(SnapshotInvalid):
            adapt_modeldial_api(payload)

    def test_revision_must_be_positive_integer(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value):
                payload = load_fixture("api-complete.json")
                payload["batch"]["revision"] = value
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_api(payload)

    def test_published_at_must_be_timezone_aware(self):
        for value in ("invalid", "2026-08-13T00:00:00"):
            with self.subTest(value=value):
                payload = load_fixture("api-complete.json")
                payload["batch"]["publishedAt"] = value
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_api(payload)

    def test_clock_skew_accepts_ten_minutes_and_rejects_more(self):
        payload = load_fixture("api-complete.json")
        published = datetime(2026, 8, 13, 0, tzinfo=timezone.utc)
        accepted = adapt_modeldial_api(payload, now=published - timedelta(minutes=10))
        self.assertEqual(accepted["snapshot_id"], payload["batch"]["id"])
        with self.assertRaises(SnapshotInvalid):
            adapt_modeldial_api(
                payload,
                now=published - timedelta(minutes=10, seconds=1),
            )

    def test_protocol_identity_fields_are_required(self):
        fields = (
            "questionPackVersion",
            "graderVersion",
            "evaluationProfile",
            "scoreBaselineId",
            "pricingSnapshotId",
        )
        for field in fields:
            with self.subTest(field=field):
                payload = load_fixture("api-complete.json")
                payload["batch"][field] = ""
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_api(payload)

    def test_entry_count_must_match_rankings(self):
        payload = load_fixture("api-complete.json")
        payload["batch"]["entryCount"] += 1
        with self.assertRaises(SnapshotInvalid):
            adapt_modeldial_api(payload)

    def test_batch_sha256_format_is_strict(self):
        for value in ("", "fixture", "sha256:ABC", "sha256:" + "0" * 63):
            with self.subTest(value=value):
                payload = load_fixture("api-complete.json")
                payload["batch"]["sha256"] = value
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_api(payload)

    def test_missing_effort_is_rejected(self):
        payload = load_fixture("api-complete.json")
        payload["rankings"] = payload["rankings"][:-1]
        payload["batch"]["entryCount"] -= 1
        with self.assertRaises(SnapshotInvalid):
            adapt_modeldial_api(payload)

    def test_duplicate_effort_is_rejected(self):
        payload = load_fixture("api-complete.json")
        payload["rankings"].append(copy.deepcopy(payload["rankings"][0]))
        payload["batch"]["entryCount"] += 1
        with self.assertRaises(SnapshotInvalid):
            adapt_modeldial_api(payload)

    def test_wrong_provider_model_or_route_is_ignored_then_incomplete(self):
        for field, value in (
            ("provider", "other"),
            ("model", "gpt-5.6-sol"),
            ("route", "api_key"),
        ):
            with self.subTest(field=field):
                payload = load_fixture("api-complete.json")
                payload["rankings"][0][field] = value
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_api(payload)

    def test_bool_score_is_rejected(self):
        payload = load_fixture("api-complete.json")
        payload["rankings"][0]["score"] = True
        with self.assertRaises(SnapshotInvalid):
            adapt_modeldial_api(payload)

    def test_nonfinite_score_is_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                payload = load_fixture("api-complete.json")
                payload["rankings"][0]["score"] = value
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_api(payload)

    def test_ultra_is_ignored(self):
        payload = load_fixture("api-complete.json")
        ultra = copy.deepcopy(payload["rankings"][0])
        ultra["id"] = "cloudflare-reference:gpt-5.6-luna:ultra"
        ultra["reasoningEffort"] = "ultra"
        ultra["score"] = 999
        payload["rankings"].append(ultra)
        payload["batch"]["entryCount"] += 1
        profile = select_snapshot(adapt_modeldial_api(payload))
        self.assertEqual(profile["selected_effort"], "max")


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

    @patch("src.selector._fetch_bytes")
    def test_api_success_does_not_fetch_snapshot(self, fetch):
        fetch.return_value = (encoded_fixture("api-complete.json"), MODELDIAL_API_URL)
        adapted = fetch_modeldial_snapshot()
        self.assertEqual(adapted["source_mode"], "modeldial_api_v1")
        fetch.assert_called_once_with(
            MODELDIAL_API_URL,
            expected_type="application/json",
            timeout=15.0,
        )

    @patch("src.selector._fetch_bytes")
    def test_api_http_failure_falls_back_to_snapshot(self, fetch):
        fetch.side_effect = [
            OSError("offline"),
            (encoded_fixture("first-party-complete.json"), MODELDIAL_SNAPSHOT_URL),
        ]
        adapted = fetch_modeldial_snapshot()
        self.assertEqual(adapted["source_mode"], "live_json")
        self.assertEqual(fetch.call_count, 2)

    @patch("src.selector._fetch_bytes")
    def test_invalid_api_json_falls_back_to_snapshot(self, fetch):
        fetch.side_effect = [
            (b"not-json", MODELDIAL_API_URL),
            (encoded_fixture("first-party-complete.json"), MODELDIAL_SNAPSHOT_URL),
        ]
        adapted = fetch_modeldial_snapshot()
        self.assertEqual(adapted["source_url"], MODELDIAL_SNAPSHOT_URL)

    @patch("src.selector._fetch_bytes")
    def test_unsupported_api_schema_falls_back_to_snapshot(self, fetch):
        api = load_fixture("api-complete.json")
        api["schemaVersion"] = "2.0"
        fetch.side_effect = [
            (json.dumps(api).encode("utf-8"), MODELDIAL_API_URL),
            (encoded_fixture("first-party-complete.json"), MODELDIAL_SNAPSHOT_URL),
        ]
        adapted = fetch_modeldial_snapshot()
        self.assertEqual(adapted["source_url"], MODELDIAL_SNAPSHOT_URL)

    @patch("src.selector._fetch_bytes")
    def test_incomplete_api_falls_back_to_snapshot(self, fetch):
        api = load_fixture("api-complete.json")
        api["rankings"] = api["rankings"][:-1]
        api["batch"]["entryCount"] -= 1
        fetch.side_effect = [
            (json.dumps(api).encode("utf-8"), MODELDIAL_API_URL),
            (encoded_fixture("first-party-complete.json"), MODELDIAL_SNAPSHOT_URL),
        ]
        adapted = fetch_modeldial_snapshot()
        self.assertEqual(adapted["source_url"], MODELDIAL_SNAPSHOT_URL)

    @patch("src.selector._fetch_bytes", side_effect=OSError("offline"))
    def test_both_json_sources_fail_then_old_lkg_is_used(self, _fetch):
        with tempfile.TemporaryDirectory() as directory:
            lkg_path = Path(directory) / "last-good-profile.json"
            lkg_path.write_text(
                json.dumps({"snapshot": load_fixture("complete.json")}),
                encoding="utf-8",
            )
            profile = ensure_daily_profile(
                None,
                state_dir=directory,
                now=datetime(2026, 8, 13, 9, tzinfo=BJT),
                live_fetcher=fetch_modeldial_snapshot,
            )
            self.assertTrue(profile["fallback"])
            self.assertEqual(profile["selected_role"], "luna_high")

    @patch("src.selector._fetch_bytes", side_effect=OSError("offline"))
    def test_both_json_sources_fail_without_lkg_is_closed(self, _fetch):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(SelectionUnavailable, NO_PROFILE_STATUS):
                ensure_daily_profile(
                    None,
                    state_dir=directory,
                    live_fetcher=fetch_modeldial_snapshot,
                )

    def test_old_daily_profile_reuses_same_day_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            now = datetime(2026, 8, 13, 9, tzinfo=BJT)
            old_profile = select_snapshot(load_fixture("complete.json"), now=now)
            (Path(directory) / "daily-profile.json").write_text(
                json.dumps(old_profile),
                encoding="utf-8",
            )

            def unexpected_fetch():
                self.fail("old same-day profile must remain reusable")

            profile = ensure_daily_profile(
                None,
                state_dir=directory,
                now=now + timedelta(hours=1),
                live_fetcher=unexpected_fetch,
            )
            self.assertEqual(profile, old_profile)

    def test_api_lkg_remains_compatible_with_existing_snapshot_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            adapted = adapt_modeldial_api(load_fixture("api-complete.json"))
            ensure_daily_profile(adapted, state_dir=directory)
            record = json.loads(
                (Path(directory) / "last-good-profile.json").read_text(encoding="utf-8")
            )
            normalized = validate_snapshot(record["snapshot"])
            self.assertEqual(set(normalized["scores"]), set(EFFORTS))

    def test_runtime_has_no_radar_html_path(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "selector.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("parse_radar_html", source)
        self.assertNotIn("/zh-CN/radar", source)
        self.assertFalse((FIXTURES / "radar-complete.html").exists())


if __name__ == "__main__":
    unittest.main()
