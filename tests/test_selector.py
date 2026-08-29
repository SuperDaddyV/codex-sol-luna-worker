import copy
import hashlib
import io
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.install import install

from src.selector import (
    BJT,
    EFFORTS,
    MODELDIAL_API_URL,
    MODELDIAL_SNAPSHOT_URL,
    NO_PROFILE_STATUS,
    USER_AGENT,
    _fetch_bytes,
    _validated_modeldial_url,
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
ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name):
    with (FIXTURES / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def encoded_fixture(name):
    return json.dumps(load_fixture(name)).encode("utf-8")


def tree_inventory(root):
    return [
        (
            path.relative_to(root).as_posix(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_mtime_ns,
        )
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def materialize_fake_global(target):
    install(target, project_root=ROOT)


DIAGNOSTIC_KEYS = {
    "diagnostic_schema_version",
    "generated_at_utc",
    "os",
    "architecture",
    "codex_version",
    "python_version",
    "installed_version",
    "verified_commit_sha",
    "manifest_status",
    "global_policy_status",
    "selector_status",
    "agents_ready",
    "agents_expected",
    "native_leaf",
    "config_status",
    "max_parallel",
    "today_bjt",
    "selection_initialized",
    "selected_role",
    "selected_effort",
    "source_mode",
    "fallback",
    "capability_degraded",
    "snapshot_id",
    "pricing_snapshot_id",
    "reference_cost_metadata_available",
    "reference_cost_reduction_pct",
    "project_override_status",
    "health",
    "reason_codes",
    "locations",
}


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

    def test_complete_api_v11_payload_uses_backend_axis(self):
        payload = load_fixture("api-complete-v1.1.json")
        adapted = adapt_modeldial_api(
            payload,
            now=datetime(2026, 8, 29, 12, tzinfo=BJT),
        )
        profile = select_snapshot(adapted)
        self.assertEqual(adapted["snapshot_id"], payload["batch"]["id"])
        self.assertEqual(profile["selected_effort"], "xhigh")
        self.assertEqual(profile["selected_score"], 61.0)
        self.assertEqual(profile["reference_cost_comparison"]["reduction_pct"], 89.5)
        overall_scores = {
            row["reasoningEffort"]: row["score"]
            for row in payload["overallRankings"]
            if row["model"] == "gpt-5.6-luna"
        }
        self.assertGreater(overall_scores["max"], overall_scores["xhigh"])

    def test_v11_default_ranking_contract_is_required(self):
        for value in (None, "rankings"):
            with self.subTest(value=value):
                payload = load_fixture("api-complete-v1.1.json")
                if value is None:
                    del payload["defaultRanking"]
                else:
                    payload["defaultRanking"] = value
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_api(payload)

    def test_v11_backend_score_identity_is_required(self):
        scenarios = {
            "wrong-basis": ("scoreBasis", "overall"),
            "missing-backend-score": ("backendScore", None),
            "boolean-backend-score": ("backendScore", True),
            "nonfinite-backend-score": ("backendScore", float("nan")),
            "mismatched-backend-score": ("backendScore", 60),
        }
        for scenario, (field, value) in scenarios.items():
            with self.subTest(scenario=scenario):
                payload = load_fixture("api-complete-v1.1.json")
                luna_xhigh = next(
                    row
                    for row in payload["rankings"]
                    if row["model"] == "gpt-5.6-luna"
                    and row["reasoningEffort"] == "xhigh"
                )
                if scenario == "missing-backend-score":
                    del luna_xhigh[field]
                else:
                    luna_xhigh[field] = value
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_api(payload)

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
        )
        for field in fields:
            with self.subTest(field=field):
                payload = load_fixture("api-complete.json")
                payload["batch"][field] = ""
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_api(payload)

    def test_pricing_snapshot_id_is_optional_for_score_selection(self):
        payload = load_fixture("api-complete.json")
        payload["batch"]["pricingSnapshotId"] = ""
        adapted = adapt_modeldial_api(payload)
        self.assertEqual(select_snapshot(adapted)["selected_effort"], "max")
        self.assertNotIn("pricing_snapshot_id", adapted)
        self.assertNotIn("reference_costs", adapted)

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
        missing = next(
            row
            for row in payload["rankings"]
            if row["model"] == "gpt-5.6-luna" and row["reasoningEffort"] == "low"
        )
        payload["rankings"].remove(missing)
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

    def test_api_reference_cost_adapter_projects_five_pairs(self):
        adapted = adapt_modeldial_api(load_fixture("api-complete.json"))
        self.assertEqual(adapted["pricing_snapshot_id"], "pricing-v1-879bc0a00c291f1ac75f7ae3b19ba969edbb307c679c813df5bb464c6c7e4512")
        costs = adapted["reference_costs"]
        self.assertEqual(costs["metric"], "modeldial_estimated_reference_cost_usd")
        self.assertEqual(costs["provider"], "codex")
        self.assertEqual(costs["route"], "official_login")
        self.assertEqual(set(costs["by_effort"]), set(EFFORTS))
        self.assertEqual(
            costs["by_effort"]["high"],
            {"luna_cost_usd": 0.064337, "sol_cost_usd": 1.072283},
        )

    def test_invalid_cost_metadata_is_omitted_without_invalidating_scores(self):
        invalid_values = (None, True, float("nan"), float("inf"), -1)
        for value in invalid_values:
            with self.subTest(value=value):
                payload = load_fixture("api-complete.json")
                luna_high = next(
                    row
                    for row in payload["rankings"]
                    if row["model"] == "gpt-5.6-luna"
                    and row["reasoningEffort"] == "high"
                )
                luna_high["estimatedReferenceCostUsd"] = value
                adapted = adapt_modeldial_api(payload)
                self.assertEqual(set(validate_snapshot(adapted)["scores"]), set(EFFORTS))
                self.assertNotIn("high", adapted["reference_costs"]["by_effort"])

    def test_noncomparable_cost_pair_is_omitted(self):
        payload = load_fixture("api-complete.json")
        luna_max = next(
            row
            for row in payload["rankings"]
            if row["model"] == "gpt-5.6-luna" and row["reasoningEffort"] == "max"
        )
        luna_max["estimatedReferenceCostUsd"] = 3.0
        adapted = adapt_modeldial_api(payload)
        self.assertEqual(select_snapshot(adapted)["selected_effort"], "max")
        self.assertNotIn("max", adapted["reference_costs"]["by_effort"])

    def test_cost_identity_errors_are_isolated_from_scores(self):
        scenarios = ("missing", "wrong-provider", "wrong-route", "duplicate")
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                payload = load_fixture("api-complete.json")
                sol_high = next(
                    row
                    for row in payload["rankings"]
                    if row["model"] == "gpt-5.6-sol"
                    and row["reasoningEffort"] == "high"
                )
                if scenario == "missing":
                    sol_high.pop("estimatedReferenceCostUsd")
                elif scenario == "wrong-provider":
                    sol_high["provider"] = "other"
                elif scenario == "wrong-route":
                    sol_high["route"] = "api_key"
                else:
                    payload["rankings"].append(copy.deepcopy(sol_high))
                    payload["batch"]["entryCount"] += 1
                adapted = adapt_modeldial_api(payload)
                self.assertEqual(select_snapshot(adapted)["selected_effort"], "max")
                self.assertNotIn("high", adapted["reference_costs"]["by_effort"])


class ModelDialFullSnapshotCostTests(unittest.TestCase):
    def test_full_snapshot_reference_cost_adapter_projects_five_pairs(self):
        adapted = adapt_modeldial_snapshot(
            load_fixture("first-party-complete.json"),
            now=datetime(2026, 8, 11, 9, tzinfo=BJT),
        )
        self.assertEqual(adapted["pricing_snapshot_id"], "fixture-pricing-v1")
        self.assertEqual(set(adapted["reference_costs"]["by_effort"]), set(EFFORTS))
        self.assertEqual(
            adapted["reference_costs"]["by_effort"]["max"],
            {"luna_cost_usd": 0.154264, "sol_cost_usd": 2.571067},
        )

    def test_full_snapshot_cost_provenance_errors_are_fail_soft(self):
        scenarios = (
            "wrong-provider",
            "wrong-route",
            "uncontrolled-route",
            "pricing-missing",
            "evidence-mismatch",
            "duplicate",
        )
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                payload = load_fixture("first-party-complete.json")
                sol_high = next(
                    entry
                    for entry in payload["entries"]
                    if entry["model_configuration"]["canonical_model_id"]
                    == "gpt-5.6-sol"
                    and entry["model_configuration"]["reasoning_effort"] == "high"
                )
                if scenario == "wrong-provider":
                    sol_high["model_configuration"]["provider_id"] = "other"
                elif scenario == "wrong-route":
                    sol_high["model_configuration"]["route_type"] = "api_key"
                elif scenario == "uncontrolled-route":
                    sol_high["route_identity"] = "uncontrolled"
                elif scenario == "pricing-missing":
                    payload["pricing_snapshot_id"] = None
                elif scenario == "evidence-mismatch":
                    sol_high["source_evidence_group_id"] = "other-run"
                else:
                    payload["entries"].append(copy.deepcopy(sol_high))
                adapted = adapt_modeldial_snapshot(
                    payload, now=datetime(2026, 8, 11, 9, tzinfo=BJT)
                )
                self.assertEqual(select_snapshot(adapted)["selected_effort"], "max")
                if scenario == "pricing-missing":
                    self.assertNotIn("reference_costs", adapted)
                else:
                    self.assertNotIn(
                        "high", adapted["reference_costs"]["by_effort"]
                    )


class SelectorTests(unittest.TestCase):
    def test_modeldial_request_uses_current_user_agent(self):
        self.assertEqual(USER_AGENT, "codex-sol-luna-worker/4.1.4")
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = None
        response.geturl.return_value = MODELDIAL_API_URL
        response.headers.get_content_type.return_value = "application/json"
        response.read.return_value = b"{}"
        opener = MagicMock()
        opener.open.return_value = response

        with patch("src.selector.urllib.request.build_opener", return_value=opener):
            _fetch_bytes(MODELDIAL_API_URL, expected_type="application/json", timeout=1)

        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_header("User-agent"), USER_AGENT)

    def test_malformed_modeldial_urls_are_snapshot_invalid(self):
        malformed_urls = (
            "https://modeldial.com:abc/api.json",
            "https://modeldial.com:99999/api.json",
            "https://[modeldial.com]/api.json",
            "https://[2001:db8::1/api.json",
        )
        for url in malformed_urls:
            with self.subTest(url=url):
                with self.assertRaisesRegex(
                    SnapshotInvalid, r"^ModelDial URL is malformed$"
                ):
                    _validated_modeldial_url(url)

    def test_malformed_redirect_url_falls_back_to_snapshot(self):
        valid_response = MagicMock()
        valid_response.__enter__.return_value = valid_response
        valid_response.__exit__.return_value = None
        valid_response.geturl.return_value = MODELDIAL_SNAPSHOT_URL
        valid_response.headers.get_content_type.return_value = "application/json"
        valid_response.read.return_value = encoded_fixture("first-party-complete.json")

        opener = MagicMock()
        handlers = []
        open_count = 0

        def build_opener(*args):
            handlers.append(args[0])
            return opener

        def open_response(request, timeout):
            nonlocal open_count
            open_count += 1
            if open_count == 1:
                handlers[-1].redirect_request(
                    None,
                    None,
                    302,
                    "Found",
                    {},
                    "https://modeldial.com:abc/api.json",
                )
            return valid_response

        opener.open.side_effect = open_response
        with patch(
            "src.selector.urllib.request.build_opener", side_effect=build_opener
        ):
            adapted = fetch_modeldial_snapshot()

        self.assertEqual(adapted["source_url"], MODELDIAL_SNAPSHOT_URL)
        self.assertEqual(open_count, 2)

    def test_malformed_final_url_falls_back_to_snapshot(self):
        malformed_response = MagicMock()
        malformed_response.__enter__.return_value = malformed_response
        malformed_response.__exit__.return_value = None
        malformed_response.geturl.return_value = "https://[modeldial.com]/api.json"

        valid_response = MagicMock()
        valid_response.__enter__.return_value = valid_response
        valid_response.__exit__.return_value = None
        valid_response.geturl.return_value = MODELDIAL_SNAPSHOT_URL
        valid_response.headers.get_content_type.return_value = "application/json"
        valid_response.read.return_value = encoded_fixture("first-party-complete.json")

        opener = MagicMock()
        opener.open.side_effect = [malformed_response, valid_response]
        with patch("src.selector.urllib.request.build_opener", return_value=opener):
            adapted = fetch_modeldial_snapshot()

        self.assertEqual(adapted["source_url"], MODELDIAL_SNAPSHOT_URL)
        self.assertEqual(opener.open.call_count, 2)

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
        luna_max = next(
            entry
            for entry in payload["entries"]
            if entry["model_configuration"]["canonical_model_id"] == "gpt-5.6-luna"
            and entry["model_configuration"]["reasoning_effort"] == "max"
        )
        luna_max["source_evidence_group_id"] = "other-run"
        with self.assertRaises(SnapshotInvalid):
            adapt_modeldial_snapshot(
                payload, now=datetime(2026, 8, 11, 9, tzinfo=BJT)
            )

    def test_first_party_snapshot_rejects_wrong_luna_route_provenance(self):
        scenarios = (
            ("provider_id", "other"),
            ("route_type", "api_key"),
            ("route_identity", "uncontrolled"),
        )
        for field, value in scenarios:
            with self.subTest(field=field):
                payload = load_fixture("first-party-complete.json")
                luna_max = next(
                    entry
                    for entry in payload["entries"]
                    if entry["model_configuration"]["canonical_model_id"]
                    == "gpt-5.6-luna"
                    and entry["model_configuration"]["reasoning_effort"] == "max"
                )
                if field == "route_identity":
                    luna_max[field] = value
                else:
                    luna_max["model_configuration"][field] = value
                with self.assertRaises(SnapshotInvalid):
                    adapt_modeldial_snapshot(
                        payload, now=datetime(2026, 8, 11, 9, tzinfo=BJT)
                    )

    @patch("src.selector._fetch_bytes")
    def test_api_success_does_not_fetch_snapshot(self, fetch):
        fetch.return_value = (
            encoded_fixture("api-complete-v1.1.json"),
            MODELDIAL_API_URL,
        )
        adapted = fetch_modeldial_snapshot()
        self.assertEqual(adapted["source_mode"], "modeldial_api_v1")
        self.assertEqual(select_snapshot(adapted)["selected_effort"], "xhigh")
        fetch.assert_called_once_with(
            MODELDIAL_API_URL,
            expected_type="application/json",
            timeout=15.0,
        )

    @patch("src.selector._fetch_bytes")
    def test_api_http_failure_falls_back_with_reference_cost(self, fetch):
        fetch.side_effect = [
            OSError("offline"),
            (encoded_fixture("first-party-complete.json"), MODELDIAL_SNAPSHOT_URL),
        ]
        adapted = fetch_modeldial_snapshot()
        self.assertEqual(adapted["source_mode"], "live_json")
        self.assertEqual(fetch.call_count, 2)
        profile = select_snapshot(adapted)
        self.assertEqual(
            profile["reference_cost_comparison"]["reduction_pct"], 94.0
        )

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
        missing = next(
            row
            for row in api["rankings"]
            if row["model"] == "gpt-5.6-luna" and row["reasoningEffort"] == "low"
        )
        api["rankings"].remove(missing)
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

    @patch("src.selector._fetch_bytes")
    def test_malformed_modeldial_url_then_old_lkg_is_used(self, fetch):
        def malformed_fetch(*args, **kwargs):
            _validated_modeldial_url("https://modeldial.com:abc/api.json")

        fetch.side_effect = malformed_fetch
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
            self.assertEqual(fetch.call_count, 2)

    @patch("src.selector._fetch_bytes")
    def test_malformed_modeldial_url_without_lkg_is_closed(self, fetch):
        def malformed_fetch(*args, **kwargs):
            _validated_modeldial_url("https://modeldial.com:abc/api.json")

        fetch.side_effect = malformed_fetch
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

    def test_same_day_profile_is_not_backfilled(self):
        with tempfile.TemporaryDirectory() as directory:
            now = datetime(2026, 8, 13, 9, tzinfo=BJT)
            legacy = select_snapshot(load_fixture("complete.json"), now=now)
            legacy.pop("metadata_schema_version")
            path = Path(directory) / "daily-profile.json"
            original = json.dumps(legacy, sort_keys=True)
            path.write_text(original, encoding="utf-8")
            profile = ensure_daily_profile(
                adapt_modeldial_api(load_fixture("api-complete.json")),
                state_dir=directory,
                now=now + timedelta(hours=1),
            )
            self.assertEqual(profile, legacy)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertNotIn("metadata_schema_version", profile)
            self.assertNotIn("reference_cost_comparison", profile)

    def test_invalid_same_day_profile_is_reselected(self):
        mutations = (
            lambda profile: profile.pop("fallback"),
            lambda profile: profile.update(fallback="not-a-boolean"),
            lambda profile: profile.update(capability_degraded="not-a-boolean"),
            lambda profile: profile.update(source_winner_effort="ultra"),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate), tempfile.TemporaryDirectory() as directory:
                now = datetime(2026, 8, 13, 9, tzinfo=BJT)
                invalid = select_snapshot(load_fixture("complete.json"), now=now)
                mutate(invalid)
                path = Path(directory) / "daily-profile.json"
                path.write_text(json.dumps(invalid), encoding="utf-8")

                profile = ensure_daily_profile(
                    adapt_modeldial_api(load_fixture("api-complete.json")),
                    state_dir=directory,
                    now=now + timedelta(hours=1),
                )

                self.assertIs(type(profile["fallback"]), bool)
                self.assertIs(type(profile["capability_degraded"]), bool)
                self.assertIn(profile["source_winner_effort"], EFFORTS)
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), profile)

    def test_invalid_same_day_profile_without_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            now = datetime(2026, 8, 13, 9, tzinfo=BJT)
            invalid = select_snapshot(load_fixture("complete.json"), now=now)
            invalid.pop("fallback")
            (Path(directory) / "daily-profile.json").write_text(
                json.dumps(invalid), encoding="utf-8"
            )

            with self.assertRaisesRegex(SelectionUnavailable, NO_PROFILE_STATUS):
                ensure_daily_profile(None, state_dir=directory, now=now + timedelta(hours=1))

    def test_legacy_lkg_selects_without_cost_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            lkg = Path(directory) / "last-good-profile.json"
            lkg.write_text(
                json.dumps({"snapshot": load_fixture("complete.json")}),
                encoding="utf-8",
            )
            profile = ensure_daily_profile(
                None,
                state_dir=directory,
                now=datetime(2026, 8, 13, 9, tzinfo=BJT),
            )
            self.assertTrue(profile["fallback"])
            self.assertNotIn("pricing_snapshot_id", profile)
            self.assertNotIn("reference_cost_comparison", profile)

    def test_capability_degradation_projects_selected_effort_cost(self):
        profile = select_snapshot(
            adapt_modeldial_snapshot(
                load_fixture("first-party-complete.json"),
                now=datetime(2026, 8, 11, 9, tzinfo=BJT),
            ),
            supported_efforts=("low", "medium", "high"),
        )
        self.assertEqual(profile["source_winner_effort"], "max")
        self.assertEqual(profile["selected_effort"], "high")
        self.assertTrue(profile["capability_degraded"])
        self.assertEqual(profile["reference_cost_comparison"]["effort"], "high")
        self.assertEqual(profile["reference_cost_comparison"]["reduction_pct"], 94.0)

    def test_lkg_projects_fallback_and_reference_cost(self):
        with tempfile.TemporaryDirectory() as directory:
            live = adapt_modeldial_api(load_fixture("api-complete.json"))
            day_one = datetime(2026, 8, 13, 9, tzinfo=BJT)
            ensure_daily_profile(live, state_dir=directory, now=day_one)
            profile = ensure_daily_profile(
                load_fixture("missing-row.json"),
                state_dir=directory,
                now=day_one + timedelta(days=1),
            )
            self.assertTrue(profile["fallback"])
            self.assertEqual(profile["reference_cost_comparison"]["effort"], "max")
            self.assertEqual(
                profile["pricing_snapshot_id"],
                "pricing-v1-879bc0a00c291f1ac75f7ae3b19ba969edbb307c679c813df5bb464c6c7e4512",
            )

    def test_print_selection_json_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(
                    [
                        "--snapshot",
                        str(FIXTURES / "api-complete.json"),
                        "--state-dir",
                        directory,
                        "--ensure-daily",
                        "--print-selection",
                    ]
                )
            self.assertEqual(code, 0)
            selection = json.loads(output.getvalue())
            self.assertEqual(
                set(selection),
                {
                    "selected_role",
                    "selected_effort",
                    "fallback",
                    "capability_degraded",
                    "source_winner_effort",
                    "reference_cost_comparison",
                },
            )
            self.assertNotIn("source_url", selection)
            self.assertNotIn("snapshot_hash", selection)
            self.assertNotIn("pricing_snapshot_id", selection)

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


class StatusAndDiagnosticTests(unittest.TestCase):
    def status(self, target, state=None, project=None):
        output = io.StringIO()
        arguments = [
            "--status-json",
            "--codex-home",
            str(target),
            "--state-dir",
            str(state or target / "sol-luna-v4" / "state"),
        ]
        if project is not None:
            arguments.extend(["--project-dir", str(project)])
        with redirect_stdout(output):
            code = main(arguments)
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_status_no_profile_is_healthy_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            state = target / "sol-luna-v4" / "state"
            before = tree_inventory(target)
            with (
                patch("src.selector.fetch_modeldial_snapshot", side_effect=AssertionError("network")),
                patch("src.selector._selector_lock", side_effect=AssertionError("lock")),
                patch("src.selector._write_json", side_effect=AssertionError("write")),
            ):
                status = self.status(target, state)
            self.assertEqual(status["health"], "Healthy")
            self.assertIn("TODAY_SELECTION_NOT_INITIALIZED", status["reason_codes"])
            self.assertFalse(status["selection_initialized"])
            self.assertFalse(state.exists())
            self.assertFalse((state / "selector.lock").exists())
            self.assertFalse((state / "daily-profile.json").exists())
            self.assertFalse((state / "last-good-profile.json").exists())
            self.assertEqual(tree_inventory(target), before)
            self.assertNotIn(
                "subprocess",
                (ROOT / "src" / "selector.py").read_text(encoding="utf-8"),
            )

    def test_status_healthy_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            state = target / "sol-luna-v4" / "state"
            ensure_daily_profile(
                adapt_modeldial_api(load_fixture("api-complete.json")),
                state_dir=state,
                now=datetime.now(BJT),
            )
            before = tree_inventory(target)
            with (
                patch("src.selector.fetch_modeldial_snapshot", side_effect=AssertionError("network")),
                patch("src.selector._selector_lock", side_effect=AssertionError("lock")),
                patch("src.selector._write_json", side_effect=AssertionError("write")),
            ):
                status = self.status(target, state)
            self.assertEqual(status["health"], "Healthy")
            self.assertEqual(status["reason_codes"], ["OK"])
            self.assertTrue(status["selection_initialized"])
            self.assertEqual(tree_inventory(target), before)

    def test_status_invalid_today_profile_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            state = target / "sol-luna-v4" / "state"
            state.mkdir(parents=True)
            (state / "daily-profile.json").write_text(
                json.dumps(
                    {
                        "selection_date_bjt": datetime.now(BJT).date().isoformat(),
                        "selected_at_bjt": datetime.now(BJT).isoformat(),
                        "selected_effort": "ultra",
                        "selected_role": "luna_ultra",
                    }
                ),
                encoding="utf-8",
            )
            status = self.status(target, state)
            self.assertEqual(status["health"], "Unavailable")
            self.assertIn("DAILY_PROFILE_INVALID", status["reason_codes"])

    def test_status_invalid_json_profile_remains_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            state = target / "sol-luna-v4" / "state"
            state.mkdir(parents=True)
            (state / "daily-profile.json").write_text("{", encoding="utf-8")

            status = self.status(target, state)

            self.assertEqual(status["health"], "Unavailable")
            self.assertIn("DAILY_PROFILE_INVALID", status["reason_codes"])
            self.assertNotIn("DAILY_PROFILE_READ_FAILED", status["reason_codes"])

    def test_status_profile_read_failures_are_misconfigured_and_read_only(self):
        failures = (
            OSError("OSError SecretUser C:\\Users\\SecretUser"),
            PermissionError("Permission denied C:\\Users\\SecretUser"),
            UnicodeError("UnicodeError SecretUser C:\\Users\\SecretUser"),
        )
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                with tempfile.TemporaryDirectory() as directory:
                    target = Path(directory) / ".codex"
                    materialize_fake_global(target)
                    state = target / "sol-luna-v4" / "state"
                    state.mkdir(parents=True)
                    profile_path = state / "daily-profile.json"
                    profile_path.write_text("{}", encoding="utf-8")
                    before = tree_inventory(target)
                    original_read_text = Path.read_text

                    def fail_profile_read(path, *args, **kwargs):
                        if path.name == "daily-profile.json":
                            raise failure
                        return original_read_text(path, *args, **kwargs)

                    with (
                        patch.object(Path, "read_text", fail_profile_read),
                        patch(
                            "src.selector.fetch_modeldial_snapshot",
                            side_effect=AssertionError("network"),
                        ),
                        patch(
                            "src.selector._selector_lock",
                            side_effect=AssertionError("lock"),
                        ),
                        patch(
                            "src.selector._write_json",
                            side_effect=AssertionError("write"),
                        ),
                        patch(
                            "src.selector.ensure_daily_profile",
                            side_effect=AssertionError("selection"),
                        ),
                    ):
                        status = self.status(target, state)

                    rendered = json.dumps(status)
                    self.assertEqual(status["health"], "Misconfigured")
                    self.assertIn("DAILY_PROFILE_READ_FAILED", status["reason_codes"])
                    self.assertNotIn("DAILY_PROFILE_INVALID", status["reason_codes"])
                    self.assertNotEqual(status["health"], "Unavailable")
                    self.assertFalse(status["selection_initialized"])
                    self.assertEqual(tree_inventory(target), before)
                    for canary in (
                        str(failure),
                        "Permission denied",
                        "C:\\Users\\SecretUser",
                        "SecretUser",
                    ):
                        self.assertNotIn(canary, rendered)

    def test_status_profile_read_failure_does_not_affect_normal_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            state = target / "sol-luna-v4" / "state"
            now = datetime.now(BJT)
            snapshot = adapt_modeldial_api(load_fixture("api-complete.json"), now=now)
            original_profile = ensure_daily_profile(snapshot, state_dir=state, now=now)
            profile_path = state / "daily-profile.json"
            profile_bytes = profile_path.read_bytes()
            original_read_text = Path.read_text

            def fail_profile_read(path, *args, **kwargs):
                if path.name == "daily-profile.json":
                    raise OSError("status-only failure")
                return original_read_text(path, *args, **kwargs)

            with patch.object(Path, "read_text", fail_profile_read):
                status = self.status(target, state)

            self.assertEqual(status["health"], "Misconfigured")
            self.assertIn("DAILY_PROFILE_READ_FAILED", status["reason_codes"])
            self.assertEqual(profile_path.read_bytes(), profile_bytes)

            selected = ensure_daily_profile(snapshot, state_dir=state, now=now)
            self.assertEqual(selected, original_profile)
            self.assertEqual(selected["selected_role"], original_profile["selected_role"])

    def test_status_degraded_projects_both_indicators(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            state = target / "sol-luna-v4" / "state"
            state.mkdir(parents=True)
            profile = select_snapshot(
                adapt_modeldial_snapshot(
                    load_fixture("first-party-complete.json"),
                    now=datetime.now(BJT),
                ),
                supported_efforts=("low", "medium", "high"),
                now=datetime.now(BJT),
                fallback=True,
            )
            (state / "daily-profile.json").write_text(
                json.dumps(profile), encoding="utf-8"
            )
            status = self.status(target, state)
            self.assertEqual(status["health"], "Degraded")
            self.assertEqual(
                status["reason_codes"],
                ["LKG_FALLBACK_ACTIVE", "CAPABILITY_DEGRADED"],
            )
            self.assertTrue(status["fallback"])
            self.assertTrue(status["capability_degraded"])
            self.assertTrue(status["reference_cost_metadata_available"])

    def test_status_misconfigured_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            (target / "sol-luna-v4" / "install-manifest.json").unlink()
            state = target / "sol-luna-v4" / "state"
            state.mkdir(parents=True)
            (state / "daily-profile.json").write_text("{}", encoding="utf-8")
            status = self.status(target, state)
            self.assertEqual(status["health"], "Misconfigured")
            self.assertEqual(status["reason_codes"][0], "MANIFEST_MISSING")

    def test_status_reader_failure_is_isolated(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            (target / "sol-luna-v4" / "install-manifest.json").write_bytes(b"not-json")
            status = self.status(target)
            self.assertEqual(status["health"], "Misconfigured")
            self.assertIn("MANIFEST_INVALID", status["reason_codes"])

    def test_diagnostic_exact_whitelist(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            status = self.status(target)
            self.assertEqual(set(status), DIAGNOSTIC_KEYS)
            self.assertEqual(
                set(status["locations"]),
                {"codex_home", "state_dir", "project_root"},
            )
            self.assertEqual(status["locations"]["codex_home"], "<CODEX_HOME>")
            self.assertEqual(status["locations"]["state_dir"], "<STATE_DIR>")
            self.assertEqual(status["locations"]["project_root"], "Not checked")

    def test_diagnostic_sanitizer_redacts_canaries(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            materialize_fake_global(target)
            state = target / "sol-luna-v4" / "state"
            state.mkdir(parents=True)
            now = datetime.now(BJT)
            profile = select_snapshot(
                adapt_modeldial_api(load_fixture("api-complete.json")), now=now
            )
            windows_canary = "C:\\" + "Users\\SecretUser"
            unc_canary = "\\\\" + "private-server\\share"
            private_url = "https" + "://private.example/repo"
            profile["snapshot_id"] = (
                windows_canary + " Bearer SECRET token=SECRET"
            )
            profile["pricing_snapshot_id"] = (
                f"{unc_canary} {private_url} api_key=SECRET sk-secret ghp_secret"
            )
            (state / "daily-profile.json").write_text(
                json.dumps(profile), encoding="utf-8"
            )
            project = Path(directory) / "SecretUser-project"
            project.mkdir()
            status = self.status(target, state, project)
            rendered = json.dumps(status)
            for canary in (
                str(target),
                str(project),
                windows_canary,
                unc_canary,
                private_url,
                "Bearer",
                "token=",
                "api_key=",
                "sk-",
                "ghp_",
            ):
                self.assertNotIn(canary, rendered)


if __name__ == "__main__":
    unittest.main()
