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
from recovery_fixtures import permission
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
        self._live, self._root = cd.LIVE, cd.ROOT
        cd.ROOT = pathlib.Path(self.tmp.name)
        cd.LIVE = cd.ROOT / "live"
        self._permit = dict(PERMIT)
        for source in (SRC_SEPA, SRC_SC, SRC_PARK):
            PERMIT[source["sid"]] = permission(cd.ROOT, source["sid"], cd.render_url(source, NOW), NOW)

    def tearDown(self):
        cd.LIVE, cd.ROOT = self._live, self._root
        PERMIT.clear(); PERMIT.update(self._permit)
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
        self.assertTrue(cd.permission_policy.access_state(PERMIT["S04"])[0])


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
        self.assertEqual(json.loads(rows[0])["permission_capture"], PERMIT["S146"]["captured_at_utc"])
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

    def test_export_re_checks_ekavica_on_thoughts_voiced_under_the_old_guard(self):
        _cfg, _root = cd.CONFIG, cd.ROOT
        cfgp = cd.LIVE.parent / "COLLECTORS.json"
        cfgp.parent.mkdir(parents=True, exist_ok=True)
        cfgp.write_text(json.dumps({"sources": [SRC_SEPA]}), encoding="utf-8")
        md = cd.LIVE / "derived" / "mind"
        md.mkdir(parents=True, exist_ok=True)
        base = {"schema": "beops-derived-row/v1", "state": "thought", "organ": "mind", "conversation": "c", "entity": "observer", "round": 1,
                "derivedTime": (NOW + timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ"), "en": "Two stations reported.", "sr_state": "voiced"}
        with open(md / "2026-09.jsonl", "w", encoding="utf-8") as fh:
            fh.write(json.dumps({**base, "sr": "Dvije stanice su javile.", "hypotheses_sr": []}) + "\n")
            fh.write(json.dumps({**base, "round": 2, "sr": "Dve stanice su javile.", "hypotheses_sr": ["možda pada prije jutra"]}) + "\n")
            fh.write(json.dumps({**base, "round": 3, "sr": "Dve stanice su javile.", "hypotheses_sr": ["možda pada pre jutra"], "questions_sr": ["Zašto?"]}) + "\n")
        cd.CONFIG, cd.ROOT = cfgp, cd.LIVE.parent
        try:
            out = json.loads(cd.export(NOW + timedelta(minutes=1)).read_text(encoding="utf-8"))
        finally:
            cd.CONFIG, cd.ROOT = _cfg, _root
        th = sorted(out["thoughts"], key=lambda t: t["round"])
        self.assertEqual(len(th), 3)
        self.assertTrue(th[0]["sr_state"].startswith("refused at export: ijekavian"), th[0]["sr_state"])
        self.assertEqual(th[0]["sr"], "")
        self.assertTrue(th[1]["sr_state"].startswith("refused at export"))
        self.assertEqual(th[1]["hypotheses_sr"], [])
        self.assertEqual((th[2]["sr_state"], th[2]["hypotheses_sr"], th[2]["questions_sr"]), ("voiced", ["možda pada pre jutra"], ["Zašto?"]))


CITY_HTML = """<html><body><div class="general-news-list"><h1 class="general-news-list__title">Beoinfo vesti</h1>
<div class="general-news-list__content">
<div class="simple-news-card"><a href="/lat/beoinfo-vesti/a115575/Delovi-Zvezdare-i-Cukarice-sutra-bez-vode.html" title="Delovi Zvezdare i &#268;ukarice sutra bez vode" class="simple-news-card__link"><div class="simple-news-card__image"><figure><img src="x"></figure></div> <div class="simple-news-card__content"><h2 class="simple-news-card__title">Delovi Zvezdare i Čukarice sutra bez vode</h2> <!----> <div class="news-card__time">09.09.2026.</div></div></a></div>
<div class="simple-news-card"><a href="/lat/beoinfo-vesti/a115568/Materijal.html" title="Materijal za crtanje" class="simple-news-card__link"><div class="simple-news-card__content"><h2 class="simple-news-card__title">Materijal za crtanje</h2> <div class="news-card__time">08.09.2026.</div></div></a></div>
</div></div></body></html>""".encode("utf-8")
SRC_CITY = {"sid": "S208", "name": "Beoinfo", "url": "https://www.beograd.rs/lat/beoinfo-vesti", "parser": "city_listing", "ext": "html", "store_raw": False,
            "cadence_seconds": 1800, "timeout_seconds": 5, "max_bytes": 1000000}


class DisabledSourceTests(unittest.TestCase):
    def test_a_disabled_source_is_not_reported_as_silent(self):
        tmp = tempfile.TemporaryDirectory()
        _cfg, _live = cd.CONFIG, cd.LIVE
        cd.LIVE = pathlib.Path(tmp.name) / "live"
        cfgp = cd.LIVE.parent / "COLLECTORS.json"
        cfgp.parent.mkdir(parents=True, exist_ok=True)
        cfgp.write_text(json.dumps({"sources": [SRC_RSS, {**SRC_RSS, "sid": "S70", "enabled": False}]}), encoding="utf-8")
        cd.CONFIG = cfgp
        try:
            st = cd.status(NOW)
        finally:
            cd.CONFIG, cd.LIVE = _cfg, _live
            tmp.cleanup()
        self.assertEqual([s["sid"] for s in st["sources"]], ["S68"])


EDS_HTML = """<HTML><BODY><TABLE><TR><TD>БЕОГРАД - Планирана искључења за датум: 2026-09-10</TD></TR>
<TR><TD>Општина</TD><TD>Време</TD><TD>Улице</TD></TR>
<TR><TD>Звездара</TD><TD>02:00 - 07:00</TD><TD>ВОЈИСЛАВА ИЛИЋА: 139,</TD></TR>
<TR><TD>Вождовац</TD><TD>10:00 - 14:00</TD><TD>УСТАНИЧКА: 170,</TD></TR></TABLE></BODY></HTML>""".encode("utf-8")
RHMZ_HTML = """<html><body><p>09.09.2026.&nbsp;&nbsp;termin:&nbsp;13:30</p><table>
<tr><th>Stanica</th><th>Temp.(°C)</th><th>Prit.(hPa)</th><th>Vlažnost(%)</th><th>Vetarpravac</th><th>Vetarbrzina(m/s)</th><th>Detaljnije</th></tr>
<tr><td>Palić</td><td>31.6</td><td>998.3</td><td>21</td><td>ESE</td><td>3.6</td><td>Detaljnije</td></tr>
<tr><td>Beograd</td><td>33.5</td><td>995.0</td><td>18</td><td>SE</td><td>2.6</td><td>Detaljnije</td></tr>
<tr><td>Košutnjak</td><td>13:25</td><td>32.0</td><td>986.8</td><td>20</td><td>181</td><td>2.8</td><td>Detaljnije</td></tr>
</table></body></html>""".encode("utf-8")


class UtilityAndWeatherParserTests(unittest.TestCase):
    def test_eds_outages_become_dated_notices_keyed_by_content(self):
        src = {"sid": "S12", "url": "https://www.elektrodistribucija.rs/x/Dan_1_Iskljucenja.htm"}
        rows = cd.parse_eds_outages(EDS_HTML, NOW, src)
        self.assertEqual(len(rows), 2)
        self.assertIn("Звездара", rows[0]["result"]); self.assertIn("02:00 - 07:00", rows[0]["result"])
        self.assertEqual((rows[0]["resultTime"], rows[0]["resultTimeResolution"], rows[0]["outage_day"]), ("2026-09-10", "day", "2026-09-10"))
        self.assertTrue(rows[0]["phenomenonTimeUnknown"])
        self.assertEqual(rows[0]["dedupe_key"], cd.parse_eds_outages(EDS_HTML, NOW, src)[0]["dedupe_key"])
        self.assertNotEqual(rows[0]["dedupe_key"], rows[1]["dedupe_key"])

    def test_rhmz_belgrade_stations_get_utc_phenomenon_time_and_text_wind_is_not_a_number(self):
        rows = cd.parse_rhmz_auto(RHMZ_HTML, NOW, {"sid": "S01", "url": "x"})
        by = {r["datastream"]: r for r in rows}
        self.assertEqual(len(rows), 10)                       # two Belgrade stations x five parameters; Palić dropped
        self.assertEqual(by["Beograd|temperature"]["result"], 33.5)
        self.assertEqual(by["Beograd|temperature"]["phenomenonTime"], "2026-09-09T11:30:00Z")   # 13:30 CEST
        self.assertEqual(by["Košutnjak|pressure"]["phenomenonTime"], "2026-09-09T11:25:00Z")     # its own 13:25
        self.assertEqual((by["Beograd|wind_direction"]["result"], by["Beograd|wind_direction"]["result_text"], by["Beograd|wind_direction"]["unit"]), (None, "SE", "compass"))
        self.assertEqual((by["Košutnjak|wind_direction"]["result"], by["Košutnjak|wind_direction"]["unit"]), (181.0, "deg"))
        self.assertFalse(by["Beograd|humidity"]["phenomenonTimeUnknown"])
        with self.assertRaises(ValueError):
            cd.parse_rhmz_auto(b"<html>no termin here</html>", NOW, {"sid": "S01"})
        self.assertEqual(cd._belgrade_local_offset(datetime(2026, 1, 15, tzinfo=timezone.utc)), 1)
        self.assertEqual(cd._belgrade_local_offset(datetime(2026, 7, 15, tzinfo=timezone.utc)), 2)


class CityListingTests(unittest.TestCase):
    def test_city_listing_keeps_title_link_and_day_only(self):
        rows = cd.parse_city_listing(CITY_HTML, NOW, SRC_CITY)
        self.assertEqual(len(rows), 2)
        r = rows[0]
        self.assertEqual(r["result"], "Delovi Zvezdare i Čukarice sutra bez vode")
        self.assertEqual(r["link"], "https://www.beograd.rs/lat/beoinfo-vesti/a115575/Delovi-Zvezdare-i-Cukarice-sutra-bez-vode.html")
        self.assertEqual((r["resultTime"], r["resultTimeResolution"]), ("2026-09-09", "day"))
        self.assertTrue(r["phenomenonTimeUnknown"])
        self.assertNotEqual(rows[0]["dedupe_key"], rows[1]["dedupe_key"])
        self.assertEqual(cd.parse_city_listing(CITY_HTML, NOW, SRC_CITY)[1]["dedupe_key"], rows[1]["dedupe_key"])
        self.assertEqual(cd.parse_city_listing(b"<html><body>nothing here</body></html>", NOW, SRC_CITY), [])


METAR_JSON = json.dumps([
    {"icaoId": "LYBE", "obsTime": 1788955200, "reportTime": "2026-09-09T12:00:00.000Z", "name": "Beograd/Nikola Tesla, RS",
     "temp": 34, "dewp": 9, "wdir": 110, "wspd": 7, "altim": 1010, "lat": 44.824, "lon": 20.291},
    {"icaoId": "LYBE", "obsTime": 1788951600, "reportTime": "2026-09-09T11:00:00.000Z",
     "temp": 33, "dewp": None, "wdir": "VRB", "wspd": 5, "altim": 1010, "lat": 44.824, "lon": 20.291},
    {"icaoId": "LYBE", "reportTime": "2026-09-09T10:00:00.000Z", "temp": 32},          # no obsTime: no instant, no row
]).encode("utf-8")

GAUGE_HTML = """<html><body><div id="sadrzaj">
<h1>Hidrološki podaci: &nbsp;SREDA&nbsp;09.09.2026.&nbsp;&nbsp;vreme:&nbsp;8:00&nbsp;(06:00 UTC)</h1>
<table>
 <tr><td class="bela75 levo">&nbsp;SAVA</td><td class="bela75"><img src="0.gif" /></td>
     <td class="bela75 levo">&nbsp;<a href="prognoza.php?hm_id=45099">BEOGRAD</a></td>
     <td class="bela75"><a href="x"><img src="nrt.gif" /></a></td><td class="bela75"><a href="y"><img src="izv.gif" /></a></td>
     <td class="bela75 ">&nbsp;132</td><td class="bela75 ">&nbsp;0</td><td class="bela75 ">&nbsp;*</td><td class="bela75 ">&nbsp;26.1</td>
     <td class="bela75 "><img src="nema.gif" /></td></tr>
 <tr><td class="bela75 levo">&nbsp;DUNAV</td><td class="bela75"><img src="0.gif" /></td>
     <td class="bela75 levo">&nbsp;<a href="prognoza.php?hm_id=42035">ZEMUN</a></td>
     <td class="bela75"><a href="x"><img src="nrt.gif" /></a></td><td class="bela75"><a href="y"><img src="izv.gif" /></a></td>
     <td class="bela75 ">&nbsp;218</td><td class="bela75 ">&nbsp;-4</td><td class="bela75 ">&nbsp;2380</td><td class="bela75 ">&nbsp;24,8</td>
     <td class="bela75 "><img src="nema.gif" /></td></tr>
 <tr><td class="bela75 levo">&nbsp;DUNAV</td><td class="bela75"><img src="0.gif" /></td>
     <td class="bela75 levo">&nbsp;<a href="prognoza.php?hm_id=42045">PAN&#268;EVO</a></td>
     <td class="bela75"><a href="x"><img src="nrt.gif" /></a></td><td class="bela75"><a href="y"><img src="izv.gif" /></a></td>
     <td class="bela75 ">&nbsp;225</td><td class="bela75 ">&nbsp;-3</td><td class="bela75 ">&nbsp;*</td><td class="bela75 ">&nbsp;25.0</td>
     <td class="bela75 "><img src="nema.gif" /></td></tr>
</table></div></body></html>""".encode("utf-8")


class MetarTests(unittest.TestCase):
    """The airport observation states its own instant; the parser must never invent one, and must never
    turn an absent value into a zero."""

    def test_metar_uses_the_sources_own_observation_instant(self):
        rows = cd.parse_metar(METAR_JSON, NOW, {"sid": "S03", "url": "https://aviationweather.gov/api/data/metar"})
        by = {(r["datastream"], r["phenomenonTime"]): r for r in rows}
        self.assertEqual(len(rows), 10)                     # two observations x five fields; the third has no instant
        a = by[("LYBE|temperature", "2026-09-09T12:00:00Z")]
        self.assertEqual((a["result"], a["unit"], a["resultQuality"]), (34.0, "Cel", "unvalidated"))
        self.assertFalse(a["phenomenonTimeUnknown"])
        self.assertEqual(a["resultTime"], "2026-09-09T12:00:00.000Z")
        self.assertEqual((a["lat"], a["lon"]), (44.824, 20.291))
        self.assertIn("airport", a["spatial_binding"])
        self.assertEqual(a["station_name"], "Beograd/Nikola Tesla, RS")

    def test_absent_values_are_missing_and_a_text_wind_is_not_a_number(self):
        rows = cd.parse_metar(METAR_JSON, NOW, {"sid": "S03"})
        by = {(r["datastream"], r["phenomenonTime"]): r for r in rows}
        dewp = by[("LYBE|dew_point", "2026-09-09T11:00:00Z")]
        wdir = by[("LYBE|wind_direction", "2026-09-09T11:00:00Z")]
        self.assertEqual((dewp["result"], dewp["resultQuality"]), (None, "missing"))
        self.assertEqual((wdir["result"], wdir["resultQuality"]), (None, "missing"))   # "VRB" is not a bearing

    def test_the_same_observation_twice_is_the_same_key_and_a_bad_body_raises(self):
        first = cd.parse_metar(METAR_JSON, NOW, {"sid": "S03"})
        again = cd.parse_metar(METAR_JSON, NOW + timedelta(minutes=15), {"sid": "S03"})
        self.assertEqual([r["dedupe_key"] for r in first], [r["dedupe_key"] for r in again])
        self.assertEqual(len(set(r["dedupe_key"] for r in first)), len(first))
        self.assertEqual(cd.parse_metar(b"[]", NOW, {"sid": "S03"}), [])
        with self.assertRaises(ValueError):
            cd.parse_metar(b'{"icaoId":"LYBE"}', NOW, {"sid": "S03"})


class RiverGaugeTests(unittest.TestCase):
    """The hydrological table states its instant in UTC. Only the two gauges inside Belgrade are kept,
    a level is never a discharge, and '*' is a missing value, never a zero."""

    def test_only_belgrade_gauges_and_the_pages_own_utc_instant(self):
        rows = cd.parse_rhmz_gauges(GAUGE_HTML, NOW, {"sid": "S52", "url": "https://www.hidmet.gov.rs/x/stanje_voda.php"})
        by = {r["datastream"]: r for r in rows}
        self.assertEqual(len(rows), 8)                       # two gauges x four parameters; Pancevo is another city
        self.assertNotIn("Pančevo (Dunav)|water_level", by)
        self.assertEqual(by["Beograd (Sava)|water_level"]["result"], 132.0)
        self.assertEqual(by["Beograd (Sava)|water_level"]["unit"], "cm")
        self.assertEqual(by["Beograd (Sava)|water_level"]["phenomenonTime"], "2026-09-09T06:00:00Z")
        self.assertFalse(by["Beograd (Sava)|water_level"]["phenomenonTimeUnknown"])
        self.assertEqual(by["Zemun (Dunav)|water_level_change"]["result"], -4.0)
        self.assertEqual(by["Zemun (Dunav)|discharge"]["result"], 2380.0)
        self.assertEqual(by["Zemun (Dunav)|water_temperature"]["result"], 24.8)   # a decimal comma is a decimal point
        self.assertEqual(by["Zemun (Dunav)|water_temperature"]["river"], "Dunav")

    def test_a_star_is_missing_and_not_a_zero(self):
        by = {r["datastream"]: r for r in cd.parse_rhmz_gauges(GAUGE_HTML, NOW, {"sid": "S52"})}
        d = by["Beograd (Sava)|discharge"]
        self.assertIsNone(d["result"])
        self.assertEqual(d["resultQuality"], "missing")
        self.assertEqual(d["unit"], "m3/s")

    def test_coordinates_say_they_are_approximate_and_a_page_without_a_time_yields_nothing(self):
        rows = cd.parse_rhmz_gauges(GAUGE_HTML, NOW, {"sid": "S52"})
        self.assertTrue(all("approximate" in r["spatial_binding"] for r in rows))
        self.assertEqual((rows[0]["lat"], rows[0]["lon"]), (44.8206, 20.4489))
        self.assertEqual(len(set(r["dedupe_key"] for r in rows)), len(rows))
        with self.assertRaises(ValueError):
            cd.parse_rhmz_gauges(b"<html><table><tr><td>SAVA</td></tr></table></html>", NOW, {"sid": "S52"})


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
        PERMIT2 = dict(PERMIT, S68=permission(cd.ROOT, "S68", SRC_RSS["url"], NOW))
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
            self.assertIn("allowed_for_us", latest[s["sid"]])  # live permission can expire; this offline test checks registration, not current authority

    def test_sepa_url_always_asks_for_a_window(self):
        cfg = cd.load_config()
        sepa = next(s for s in cfg["sources"] if s["sid"] == "S146")
        self.assertIn("{from_iso}", sepa["url"])
        self.assertLessEqual(sepa["window_seconds"], 24 * 3600)


if __name__ == "__main__":
    unittest.main()
