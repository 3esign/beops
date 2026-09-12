"""D-002 must rank deterministically, keep future data out and freeze its replay."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import decision_d002 as d002


def point(value, when, received=None):
    return {"v": value, "t": when, "tu": False, "rx": received or when,
            "rt": when, "q": "fixture"}


class DecisionD002(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "schema": "beops-d002-policy/v1", "decision_id": "D-002",
            "question": "Šta proveriti?",
            "alternatives": ["proveri_sada", "nastavi_pracenje", "nedovoljno_dokaza"],
            "signal": {"minimum_points": 3, "minimum_persistent_intervals": 2,
                       "maximum_verification_window_minutes": 120,
                       "independent_domain_max_age_minutes": 1440},
            "ranking": ["permission", "clock", "persistence", "independence", "age", "information", "id"],
            "sources": {
                "S1": {"domain": "air", "expected_cadence_seconds": 3600, "maximum_age_minutes": 180,
                       "bindings": {"Zemun": "Zemun"}},
                "S2": {"domain": "river", "expected_cadence_seconds": 86400, "maximum_age_minutes": 1800,
                       "bindings": {"Zemun gauge": "Zemun"}},
                "S3": {"domain": "parking", "expected_cadence_seconds": 900, "maximum_age_minutes": 60,
                       "bindings": {"Slavija lot": "Slavija"}},
            },
            "binding_method": "fixture", "binding_evidence": "fixture.json",
            "limits": ["fixture"],
        }
        air = [point(10, "2026-09-12T08:00:00Z"), point(12, "2026-09-12T09:00:00Z"),
               point(15, "2026-09-12T10:00:00Z"), point(99, "2026-09-12T13:00:00Z")]
        parking = [{"v": v, "rx": t, "q": "fixture"} for v, t in
                   [(1, "2026-09-12T10:15:00Z"), (2, "2026-09-12T10:30:00Z"),
                    (3, "2026-09-12T10:45:00Z")]]
        self.snapshot = {"schema": "beops-live-snapshot/v1", "as_of": "2026-09-12T11:00:00Z",
                         "sources": [
                             {"sid": "S1", "name": "Air", "datastreams": [
                                 {"station": "Zemun", "datastream": "air|x", "parameter": "x", "unit": "u", "points": air}]},
                             {"sid": "S2", "name": "River", "datastreams": [
                                 {"station": "Zemun gauge", "datastream": "river|level", "parameter": "level", "unit": "cm",
                                  "points": [point(100, "2026-09-12T06:00:00Z")]}]},
                             {"sid": "S3", "name": "Parking", "datastreams": [
                                 {"station": "Slavija lot", "datastream": "parking|free", "parameter": "free", "unit": "1",
                                  "points": parking}]},
                         ]}
        self.permissions = {sid: {"allowed": True, "checked_at": "2026-09-12T11:00:00Z", "evidence": "fixture"}
                            for sid in self.policy["sources"]}

    def test_measurement_time_wins_and_future_point_never_leaks(self):
        cutoff = datetime(2026, 9, 12, 11, tzinfo=timezone.utc)
        first = d002.build_episode(self.snapshot, self.policy, cutoff, self.permissions, "a" * 64, "b" * 64)
        again = d002.build_episode(self.snapshot, self.policy, cutoff, self.permissions, "a" * 64, "b" * 64)
        self.assertEqual(first, again)
        self.assertEqual(first["deterministic_result"]["alternative"], "proveri_sada")
        selected = next(row for row in first["candidates"]
                        if row["candidate_id"] == first["deterministic_result"]["selected_candidate_id"])
        self.assertEqual(selected["sid"], "S1")
        self.assertEqual(selected["independent_domains_present"], ["river"])
        self.assertEqual([row["value"] for row in selected["evidence"]], [10, 12, 15])
        self.assertNotIn(99, [row["value"] for candidate in first["candidates"] for row in candidate["evidence"]])
        self.assertEqual(selected["uncertainty_reduction_proxy_ppm"], 333333)
        self.assertEqual(first["deterministic_result"]["top_rank_tie_count"], 1)
        self.assertFalse(first["deterministic_result"]["stable_id_tiebreak_used"])
        self.assertIsNone(first["human_decision"])
        self.assertIsNone(first["ai_interpretation"])
        self.assertIsNone(first["outcome"])

    def test_no_confirmed_zone_is_insufficient_not_zero(self):
        snapshot = {"schema": "beops-live-snapshot/v1", "as_of": "2026-09-12T11:00:00Z",
                    "sources": [{"sid": "S1", "name": "Air", "datastreams": [
                        {"station": "Unknown", "datastream": "x", "parameter": "x", "unit": "u",
                         "points": [point(1, "2026-09-12T08:00:00Z"), point(2, "2026-09-12T09:00:00Z"),
                                    point(3, "2026-09-12T10:00:00Z")]}]}]}
        episode = d002.build_episode(snapshot, self.policy,
                                     datetime(2026, 9, 12, 11, tzinfo=timezone.utc),
                                     self.permissions, "a" * 64, "b" * 64)
        self.assertEqual(episode["candidates"], [])
        self.assertEqual(episode["deterministic_result"]["alternative"], "nedovoljno_dokaza")

    def test_replay_is_immutable_and_has_ten_unsettled_episodes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / "public").mkdir()
            (root / "research").mkdir()
            snapshot = root / "public/live-snapshot.json"
            policy = root / "research/D002_POLICY.json"
            output = root / "research/replay.json"
            snapshot.write_text(json.dumps(self.snapshot), encoding="utf-8")
            policy.write_text(json.dumps(self.policy), encoding="utf-8")
            result = d002.prepare_replay(root, snapshot, policy, output, count=10, spacing_minutes=120,
                                         now=datetime(2026, 9, 12, 11, tzinfo=timezone.utc),
                                         permissions_override=self.permissions)
            self.assertEqual(result["episodes"], 10)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(packet["episode_count"], 10)
            self.assertEqual(packet["closed_outcomes"], 0)
            self.assertTrue(all(row["candidate_count"] >= len(row["candidates"]) for row in packet["episodes"]))
            self.assertTrue(all(len(row["candidates"]) <= 12 for row in packet["episodes"]))
            self.assertTrue(all(row["future_data_used"] is False for row in packet["episodes"]))
            with self.assertRaises(FileExistsError):
                d002.prepare_replay(root, snapshot, policy, output, permissions_override=self.permissions)

            escaped = root.parent / (root.name + "-escaped.json")
            with self.assertRaisesRegex(ValueError, "inside the project"):
                d002.prepare_replay(
                    root, snapshot, policy, escaped, permissions_override=self.permissions
                )
            self.assertFalse(escaped.exists())


if __name__ == "__main__":
    unittest.main()
