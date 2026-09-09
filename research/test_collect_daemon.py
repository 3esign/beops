"""Offline tests for tools/collect_daemon.py. No network; every fetch is a fake.

The rules tested are the project's hard rules, not implementation details:
an unknown is never a permission; received is not measured; missing is not
zero; receipts are never overwritten; 403/429 pauses the source; a
permissive header is not a refusal (C-010 lesson applied to the collector).
"""
import importlib.util
import json
import os
import pathlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("collect_daemon", ROOT / "tools" / "collect_daemon.py")
cd = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cd)

NOW = datetime(2026, 9, 9, 10, 0, tzinfo=timezone.utc)

SEPA_BODY = json.dumps({"data": [
    {"station_id": "1", "parameter_code": "CO", "time_start_utc": "2026-09-09T08:00:00Z",
     "time_end_utc": "2026-09-09T09:00:00Z", "value": 0.19, "unit": "mg.m-3", "data_status": "preliminary",
     "aggregation_type": "hourly_mean", "published_at_utc": "2026-09-09T09:40:16Z"},
    {"station_id": "1", "parameter_code": "PM10", "time_start_utc": "2026-09-09T08:00:00Z",
     "time_end_utc": "2026-09-09T09:00:00Z", "value": None, "unit": "ug.m-3", "data_status": "preliminary",
     "aggregation_type": "hourly_mean", "published_at_utc": "2026-09-09T09:40:16Z"},
]}).encode()

SC_BODY = json.dumps([
    {"id": 1, "location": {"id": 90113, "latitude": "44.796", "longitude": "20.470", "indoor": 0},
     "timestamp": "2026-09-09 09:56:00", "sensor": {"id": 97344, "sensor_type": {"name": "DHT22"}},
     "sensordatavalues": [{"value_type": "temperature", "value": "27.72"}, {"value_type": "humidity", "value": "nan"}]},
    {"id": 2, "location": {"id": 1, "latitude": "44.8", "longitude": "20.4", "indoor": 0},
     "timestamp": None, "sensor": {"id": 5, "sensor_type": {"name": "SDS011"}},
     "sensordatavalues": [{"value_type": "P1", "value": "12.5"}]},
]).encode()

PARKING_HTML = b"""<html><body><ul class="parking-count">
<li><a href="/map/1">Gara\xc5\xbea "Pinki"</a> <span class="count">102</span></li>
<li><a href="/map/2">Parkirali\xc5\xa1te "Kalemegdan"</a> <span class="count">0</span></li>
<li><a href="/map/3">Parkirali\xc5\xa1te "Ada"</a> <span class="count">--</span></li>
</ul></body></html>"""

SRC_SEPA = {"sid": "S146", "name": "SEPA", "url": "https://x/obs?from={from_iso}", "parser": "sepa_hvd",
            "ext": "json", "cadence_seconds": 3600, "timeout_seconds": 5, "max_bytes": 1000, "window_seconds": 3600}
SRC_SC = {"sid": "S04", "name": "SC", "url": "https://x/sc", "parser": "sensor_community", "ext": "json",
          "cadence_seconds": 600, "timeout_seconds": 5, "max_bytes": 1000}
SRC_PARK = {"sid": "S10", "name": "P", "url": "https://x/p", "parser": "parking", "ext": "html",
            "cadence_seconds": 900, "timeout_seconds": 5, "max_bytes": 1000}


def ok(body):
    return lambda url, t, m: {"status": 200, "headers": {"date": "x"}, "body": body, "error": None, "transport": "fake"}


def http(code):
    return lambda url, t, m: {"status": code, "headers": {}, "body": None, "error": f"HTTP {code}", "transport": "fake"}


PERMIT = {"S146": {"sid": "S146", "captured_at_utc": "20260906T000000Z", "allowed_for_us": True, "capture_ok": True},
          "S04": {"sid": "S04", "captured_at_utc": "20260906T000000Z", "allowed_for_us": True, "capture_ok": True,
                  "opt_out_signals_seen": {"https://x/": {"x-robots-tag": "noindex, follow"}}},
          "S10": {"sid": "S10", "captured_at_utc": "20260906T000000Z", "allowed_for_us": True, "capture_ok": True}}


class LiveDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._live = cd.LIVE
        cd.LIVE = pathlib.Path(self.tmp.name) / "live"

    def tearDown(self):
        cd.LIVE = self._live
        self.tmp.cleanup()


class GateTests(unittest.TestCase):
    def test_no_capture_is_not_permission(self):
        self.assertFalse(cd.may_collect("S999", {})[0])

    def test_unknown_verdict_is_not_permission(self):
        self.assertFalse(cd.may_collect("S1", {"S1": {"allowed_for_us": None, "capture_ok": True, "captured_at_utc": "x"}})[0])

    def test_incomplete_capture_is_not_permission(self):
        self.assertFalse(cd.may_collect("S1", {"S1": {"allowed_for_us": True, "capture_ok": False, "captured_at_utc": "x"}})[0])

    def test_refusal_and_decision_hold(self):
        self.assertFalse(cd.may_collect("S1", {"S1": {"allowed_for_us": True, "capture_ok": True, "captured_at_utc": "x", "manual_verdict": "refused"}})[0])
        self.assertFalse(cd.may_collect("S1", {"S1": {"allowed_for_us": True, "capture_ok": True, "captured_at_utc": "x", "manual_verdict": "needs_decision"}})[0])

    def test_content_signal_ai_input_no_refuses(self):
        e = {"allowed_for_us": True, "capture_ok": True, "captured_at_utc": "x", "content_signal": {"o": {"ai-input": "no"}}}
        self.assertFalse(cd.may_collect("S1", {"S1": e})[0])

    def test_permissive_header_is_not_refusal(self):
        # C-010: a search-engine header (noindex) recorded in the capture must not refuse reading.
        self.assertTrue(cd.may_collect("S04", PERMIT)[0])


class ParserTests(unittest.TestCase):
    def test_sepa_interval_is_phenomenon_time_and_null_is_missing(self):
        rows = cd.parse_sepa_hvd(SEPA_BODY, NOW, SRC_SEPA)
        self.assertEqual(len(rows), 2)
        co, pm = rows
        self.assertEqual(co["phenomenonTime"], {"start": "2026-09-09T08:00:00Z", "end": "2026-09-09T09:00:00Z"})
        self.assertFalse(co["phenomenonTimeUnknown"])
        self.assertEqual(co["resultTime"], "2026-09-09T09:40:16Z")
        self.assertEqual(co["receivedTime"], "2026-09-09T10:00:00Z")
        self.assertEqual(co["resultQuality"], "source-preliminary")
        self.assertIsNone(pm["result"])
        self.assertEqual(pm["resultQuality"], "missing")
        self.assertNotEqual(pm["result"], 0)

    def test_sensor_community_timestamp_and_unknown_time(self):
        rows = cd.parse_sensor_community(SC_BODY, NOW, SRC_SC)
        temp, hum, p1 = rows
        self.assertEqual(temp["phenomenonTime"], "2026-09-09T09:56:00Z")
        self.assertFalse(temp["phenomenonTimeUnknown"])
        self.assertEqual(temp["result"], 27.72)
        self.assertIsNone(hum["result"])            # "nan" is missing, not zero
        self.assertEqual(hum["resultQuality"], "missing")
        self.assertTrue(p1["phenomenonTimeUnknown"])  # record without a timestamp keeps the value, flags the time
        self.assertEqual(p1["result"], 12.5)
        self.assertIsNone(p1["resultTime"])

    def test_parking_has_no_measurement_time_and_keeps_zero(self):
        rows = cd.parse_parking(PARKING_HTML, NOW, SRC_PARK)
        self.assertEqual([r["result"] for r in rows], [102, 0, None])
        self.assertTrue(all(r["phenomenonTimeUnknown"] for r in rows))
        self.assertTrue(all(r["phenomenonTime"] is None for r in rows))
        self.assertEqual(rows[1]["resultQuality"], "unvalidated")   # zero is a value
        self.assertEqual(rows[2]["resultQuality"], "missing")       # "--" is not a value

    def test_parking_empty_page_raises(self):
        with self.assertRaises(ValueError):
            cd.parse_parking(b"<html><body>nothing</body></html>", NOW, SRC_PARK)


class CollectTests(LiveDirCase):
    def test_capture_writes_receipt_raw_and_rows(self):
        r = cd.collect_one(SRC_SEPA, NOW, PERMIT, fetcher=ok(SEPA_BODY))
        self.assertEqual(r["state"], "captured")
        self.assertEqual(r["rows"], 2)
        self.assertEqual(r["rows_missing"], 1)
        rec = json.loads((cd.LIVE / "receipts" / "S146" / (cd.stamp(NOW) + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(rec["raw_bytes"], len(SEPA_BODY))
        self.assertTrue((cd.LIVE / "raw" / "S146" / (cd.stamp(NOW) + ".json.gz")).exists())
        rows = (cd.LIVE / "rows" / "S146" / "2026-09.jsonl").read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(rows), 2)
        self.assertIn('"permission_capture": "20260906T000000Z"', rows[0])
        self.assertIn("from=2026-09-09T09:00:00Z", rec["url"])
        self.assertFalse((cd.LIVE / "receipts" / "S146" / (cd.stamp(NOW) + ".claim")).exists())

    def test_same_slot_is_never_refetched(self):
        cd.collect_one(SRC_SEPA, NOW, PERMIT, fetcher=ok(SEPA_BODY))
        calls = []
        r = cd.collect_one(SRC_SEPA, NOW, PERMIT, fetcher=lambda *a: calls.append(a) or ok(SEPA_BODY)(*a))
        self.assertEqual(r["state"], "already_recorded")
        self.assertEqual(calls, [])

    def test_not_permitted_makes_no_request(self):
        calls = []
        r = cd.collect_one(SRC_SEPA, NOW, {}, fetcher=lambda *a: calls.append(a))
        self.assertEqual(r["state"], "not_permitted")
        self.assertEqual(calls, [])
        self.assertFalse((cd.LIVE / "receipts").exists())

    def test_failure_leaves_receipt_without_numbers(self):
        r = cd.collect_one(SRC_SC, NOW, PERMIT, fetcher=http(500))
        self.assertEqual(r["state"], "failed")
        self.assertEqual(r["rows"], 0)
        self.assertFalse((cd.LIVE / "rows").exists())
        rec = json.loads((cd.LIVE / "receipts" / "S04" / (cd.stamp(NOW) + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(rec["http_status"], 500)

    def test_429_pauses_source_until_a_person_clears_it(self):
        cd.collect_one(SRC_PARK, NOW, PERMIT, fetcher=http(429))
        self.assertTrue((cd.LIVE / "receipts" / "S10" / "PAUSED").exists())
        calls = []
        r = cd.collect_one(SRC_PARK, NOW + timedelta(hours=1), PERMIT, fetcher=lambda *a: calls.append(a))
        self.assertEqual(r["state"], "source_paused")
        self.assertEqual(calls, [])

    def test_unparsed_body_is_kept_but_yields_no_rows(self):
        r = cd.collect_one(SRC_PARK, NOW, PERMIT, fetcher=ok(b"<html>changed layout</html>"))
        self.assertEqual(r["state"], "unparsed")
        self.assertTrue((cd.LIVE / "raw" / "S10").exists())
        self.assertFalse((cd.LIVE / "rows").exists())

    def test_publish_never_overwrites(self):
        p = cd.LIVE / "x.json"
        cd.publish(p, {"a": 1})
        with self.assertRaises(FileExistsError):
            cd.publish(p, {"a": 2})
        self.assertEqual(json.loads(p.read_text())["a"], 1)

    def test_due_logic_and_quorum(self):
        self.assertTrue(cd.is_due(SRC_SC, NOW)[0])
        cd.collect_one(SRC_SC, NOW, PERMIT, fetcher=ok(SC_BODY))
        self.assertFalse(cd.is_due(SRC_SC, NOW + timedelta(seconds=300))[0])
        self.assertTrue(cd.is_due(SRC_SC, NOW + timedelta(seconds=600))[0])
        cells = cd._quorum_cells(SRC_SC, cd.receipts("S04"), NOW + timedelta(seconds=1), 1)
        self.assertEqual(len(cells), 6)
        self.assertEqual(cells.count("#"), 1)


class DedupeAndExportTests(LiveDirCase):
    def test_window_resend_is_not_a_new_row_but_unknown_time_is(self):
        cd.collect_one(SRC_SEPA, NOW, PERMIT, fetcher=ok(SEPA_BODY))
        r2 = cd.collect_one(SRC_SEPA, NOW + timedelta(hours=1), PERMIT, fetcher=ok(SEPA_BODY))
        self.assertEqual(r2["rows"], 2)
        rec = json.loads((cd.LIVE / "receipts" / "S146" / (cd.stamp(NOW + timedelta(hours=1)) + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(rec["rows_new"], 0)
        lines = (cd.LIVE / "rows" / "S146" / "2026-09.jsonl").read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 2)
        # parking has no measurement time: the same displayed value received again IS a new reception
        cd.collect_one(SRC_PARK, NOW, PERMIT, fetcher=ok(PARKING_HTML))
        cd.collect_one(SRC_PARK, NOW + timedelta(minutes=15), PERMIT, fetcher=ok(PARKING_HTML))
        lines = (cd.LIVE / "rows" / "S10" / "2026-09.jsonl").read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 6)

    def test_station_filter_keeps_belgrade_only_and_names(self):
        src = dict(SRC_SEPA, station_ids=["2"], station_names={"2": "X"})
        self.assertEqual(cd.parse_sepa_hvd(SEPA_BODY, NOW, src), [])
        src = dict(SRC_SEPA, station_ids=["1"], station_names={"1": "Stari grad"})
        rows = cd.parse_sepa_hvd(SEPA_BODY, NOW, src)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["station_name"], "Stari grad")

    def test_export_copies_rows_and_keeps_missing(self):
        _cfg, _root = cd.CONFIG, cd.ROOT
        cfgp = cd.LIVE.parent / "COLLECTORS.json"
        cfgp.parent.mkdir(parents=True, exist_ok=True)
        cfgp.write_text(json.dumps({"sources": [SRC_SEPA, SRC_PARK]}), encoding="utf-8")
        cd.CONFIG, cd.ROOT = cfgp, cd.LIVE.parent
        try:
            cd.collect_one(SRC_SEPA, NOW, PERMIT, fetcher=ok(SEPA_BODY))
            cd.collect_one(SRC_PARK, NOW, PERMIT, fetcher=ok(PARKING_HTML))
            out = json.loads(cd.export(NOW + timedelta(minutes=1)).read_text(encoding="utf-8"))
        finally:
            cd.CONFIG, cd.ROOT = _cfg, _root
        sepa = next(s for s in out["sources"] if s["sid"] == "S146")
        pm = next(d for d in sepa["datastreams"] if d["parameter"] == "PM10")
        self.assertEqual(pm["points"][0]["v"], None)
        self.assertEqual(pm["points"][0]["q"], "missing")
        park = next(s for s in out["sources"] if s["sid"] == "S10")
        self.assertTrue(all(p["tu"] for d in park["datastreams"] for p in d["points"]))
        self.assertEqual(out["status"]["sources"][0]["captured"], 1)

    def test_export_takes_coordinates_from_later_rows_and_keeps_scope(self):
        """The month file is append-only. Rows captured before station_coords / station_names existed
        in COLLECTORS.json carry null lat/lon/name; a datastream first seen through such a row stayed
        null for ever, and the 32 SEPA stations never reached the map. Rows captured before the
        Belgrade station filter existed are national and must not enter the observatory's snapshot."""
        _cfg, _root = cd.CONFIG, cd.ROOT
        cfgp = cd.LIVE.parent / "COLLECTORS.json"
        cfgp.parent.mkdir(parents=True, exist_ok=True)
        src_now = dict(SRC_SEPA, station_ids=["1"], station_names={"1": "Stari grad"}, station_coords={"1": [44.8186, 20.4573]})
        cfgp.write_text(json.dumps({"sources": [src_now]}), encoding="utf-8")
        cd.CONFIG, cd.ROOT = cfgp, cd.LIVE.parent
        try:
            old_body = json.dumps({"data": [
                {"station_id": "1", "parameter_code": "CO", "time_start_utc": "2026-09-09T07:00:00Z", "time_end_utc": "2026-09-09T08:00:00Z",
                 "value": 0.11, "unit": "mg.m-3", "data_status": "preliminary", "aggregation_type": "hourly_mean", "published_at_utc": "2026-09-09T08:40:00Z"},
                {"station_id": "999", "parameter_code": "CO", "time_start_utc": "2026-09-09T07:00:00Z", "time_end_utc": "2026-09-09T08:00:00Z",
                 "value": 0.5, "unit": "mg.m-3", "data_status": "preliminary", "aggregation_type": "hourly_mean", "published_at_utc": "2026-09-09T08:40:00Z"},
            ]}).encode()
            cd.collect_one(SRC_SEPA, NOW - timedelta(hours=1), PERMIT, fetcher=ok(old_body))   # no filter, no coords: the early days
            cd.collect_one(src_now, NOW, PERMIT, fetcher=ok(SEPA_BODY))                          # today's configuration
            out = json.loads(cd.export(NOW + timedelta(minutes=1)).read_text(encoding="utf-8"))
        finally:
            cd.CONFIG, cd.ROOT = _cfg, _root
        sepa = next(s for s in out["sources"] if s["sid"] == "S146")
        co = next(d for d in sepa["datastreams"] if d["datastream"] == "1|CO")
        self.assertEqual((co["lat"], co["lon"]), (44.8186, 20.4573))
        self.assertEqual(co["station"], "Stari grad")
        self.assertEqual(len(co["points"]), 2, "the old row itself is kept - only its null coordinates are superseded")
        self.assertFalse(any(d["datastream"].startswith("999|") for d in sepa["datastreams"]), "a station outside the Belgrade scope must not appear")


RSS_BODY = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>
<item><title>  Radovi na Brankovom mostu   od ponedeljka</title><link>https://ex/1</link><guid>g1</guid><pubDate>Tue, 08 Sep 2026 20:10:00 +0200</pubDate><description>LONG BODY THAT MUST NOT BE KEPT</description></item>
<item><title>Bez naslova</title><link>https://ex/2</link><guid>g2</guid></item>
</channel></rss>"""
SRC_RSS = {"sid": "S68", "name": "T", "url": "https://x/rss", "parser": "rss", "ext": "xml", "store_raw": False,
           "cadence_seconds": 1800, "timeout_seconds": 5, "max_bytes": 1000}


class ClockAndCoordTests(unittest.TestCase):
    def test_sepa_clock_note_keeps_label_and_adds_marked_estimate(self):
        src = dict(SRC_SEPA, source_clock_note={"offset_seconds": 7200, "text": "labels local as Z"})
        rows = cd.parse_sepa_hvd(SEPA_BODY, NOW, src)
        self.assertEqual(rows[0]["phenomenonTime"]["end"], "2026-09-09T09:00:00Z")          # as received, untouched
        self.assertEqual(rows[0]["phenomenonTimeCorrected"]["end"], "2026-09-09T07:00:00Z")
        self.assertEqual(rows[0]["phenomenonTimeCorrected"]["state"], "estimated")
        self.assertEqual(rows[0]["resultTimeCorrected"], "2026-09-09T07:40:16Z")
        self.assertNotIn("phenomenonTimeCorrected", cd.parse_sepa_hvd(SEPA_BODY, NOW, SRC_SEPA)[0])

    def test_parking_coordinates_come_from_the_operator_link(self):
        html = PARKING_HTML.replace(b'href="/map/1"', b'href="https://www.google.com/maps/place/44.801441,20.474145"')
        rows = cd.parse_parking(html, NOW, SRC_PARK)
        self.assertEqual((rows[0]["lat"], rows[0]["lon"]), (44.801441, 20.474145))
        self.assertIsNone(rows[1]["lat"])


class RssTests(LiveDirCase):
    def test_headline_only_publication_is_result_time_and_raw_not_stored(self):
        PERMIT2 = dict(PERMIT, S68={"sid": "S68", "captured_at_utc": "20260906T000000Z", "allowed_for_us": True, "capture_ok": True})
        r = cd.collect_one(SRC_RSS, NOW, PERMIT2, fetcher=ok(RSS_BODY))
        self.assertEqual(r["state"], "captured")
        self.assertEqual(r["rows"], 2)
        self.assertFalse((cd.LIVE / "raw").exists())
        lines = (cd.LIVE / "rows" / "S68" / "2026-09.jsonl").read_text(encoding="utf-8").strip().split("\n")
        a = json.loads(lines[0])
        self.assertEqual(a["result"], "Radovi na Brankovom mostu od ponedeljka")
        self.assertEqual(a["resultTime"], "2026-09-08T18:10:00Z")
        self.assertTrue(a["phenomenonTimeUnknown"])
        self.assertNotIn("LONG BODY", "\n".join(lines))
        b = json.loads(lines[1])
        self.assertIsNone(b["resultTime"])
        # same guid on the next tick is not a new row
        r2 = cd.collect_one(SRC_RSS, NOW + timedelta(minutes=30), PERMIT2, fetcher=ok(RSS_BODY))
        rec = json.loads((cd.LIVE / "receipts" / "S68" / (cd.stamp(NOW + timedelta(minutes=30)) + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(rec["rows_new"], 0)
        self.assertEqual(rec["raw_file"], None)
        self.assertIn("raw_not_stored", rec)


class ConfigTests(unittest.TestCase):
    def test_repo_config_is_valid_and_every_source_has_a_capture(self):
        cfg = cd.load_config()
        latest = cd.gate()
        for s in cfg["sources"]:
            self.assertIn(s["sid"], latest, f"{s['sid']} listed in COLLECTORS.json without a permission capture")
            self.assertTrue(cd.may_collect(s["sid"], latest)[0], s["sid"])

    def test_sepa_url_always_asks_for_a_window(self):
        cfg = cd.load_config()
        sepa = next(s for s in cfg["sources"] if s["sid"] == "S146")
        self.assertIn("{from_iso}", sepa["url"])
        self.assertLessEqual(sepa["window_seconds"], 24 * 3600)


if __name__ == "__main__":
    unittest.main()
