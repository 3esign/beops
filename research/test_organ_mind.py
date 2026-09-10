#!/usr/bin/env python3
"""test_organ_mind.py - the mind, offline: the digest and its connections, the organelles, the
validator and the voice validator, one whole conversation (council and relay), the drip, the
notebooks, retraction and scoring - with fake models. No daemon, no network."""
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import organ_mind as om  # noqa: E402

NOW = datetime(2026, 9, 9, 0, 5, tzinfo=timezone.utc)
AS_OF = "2026-09-09T00:04:00Z"
MODELS = ["qwen2.5:3b", "llama3.2:1b", "lfm2.5:1.2b", "paraphrase-multilingual:latest", "qwen3.5:cloud"]
REG = {"id": "mind", "window_hours": 6, "models_preferred": ["qwen2.5:3b"], "allow_cloud": False,
       "models_by_entity": {"observer": ["qwen2.5:3b"], "skeptic": ["qwen2.5:3b"], "connector": ["qwen2.5:3b"]},
       "voice_models": ["qwen2.5:3b"], "ranker_models": ["llama3.2:1b"], "embed_models": ["paraphrase-multilingual"]}


def snapshot(extra_hour: bool = False) -> dict:
    """Two SEPA stations over two hours, one parking lot with two receptions, three outlets, one organ row."""
    def sepa(v1, v2, v3=None):
        pts = [{"t": "2026-09-08T22:00:00Z", "tu": False, "rx": "2026-09-08T22:56:00Z", "v": v1, "q": "source-preliminary"},
               {"t": "2026-09-08T23:00:00Z", "tu": False, "rx": "2026-09-08T23:56:00Z", "v": v2, "q": "source-preliminary"}]
        if extra_hour and v3 is not None:
            pts.append({"t": "2026-09-09T00:00:00Z", "tu": False, "rx": "2026-09-09T00:56:00Z", "v": v3, "q": "source-preliminary"})
        return pts
    return {"schema": "beops-live-snapshot/v1", "as_of": AS_OF, "window_hours": 24,
            "sources": [
                {"sid": "S146", "name": "SEPA", "datastreams": [
                    {"datastream": "1|PM10", "station": "Stari grad", "parameter": "PM10", "unit": "ug.m-3", "lat": 44.8186, "lon": 20.4573, "points": sepa(18.0, 20.0, 25.0)},
                    {"datastream": "2|PM10", "station": "Zemun", "parameter": "PM10", "unit": "ug.m-3", "lat": 44.8458, "lon": 20.4016, "points": sepa(30.0, 41.0, 60.0)}], "events": []},
                {"sid": "S10", "name": "Parking", "datastreams": [
                    {"datastream": "Pinki|free_spaces", "station": "Pinki", "parameter": "free_spaces", "unit": "1", "lat": 44.8, "lon": 20.4,
                     "points": [{"t": None, "tu": True, "rx": "2026-09-08T23:41:00Z", "v": 102, "q": None}, {"t": None, "tu": True, "rx": "2026-09-09T00:01:00Z", "v": 88, "q": None}]}], "events": []},
                {"sid": "S69", "name": "Danas", "datastreams": [], "events": [{"t": "2026-09-08T23:10:00Z", "rx": "2026-09-08T23:30:00Z", "title": "Deo Zemuna sutra bez vode", "link": "x"}]},
                {"sid": "S68", "name": "Tanjug", "datastreams": [], "events": [{"t": "2026-09-08T23:12:00Z", "rx": "2026-09-08T23:30:00Z", "title": "Zemun: sutra bez vode u delu opštine", "link": "y"},
                                                                                {"t": "2026-09-08T23:15:00Z", "rx": "2026-09-08T23:30:00Z", "title": "Koncert na Ušću", "link": "z"}]},
                {"sid": "S70", "name": "Kurir", "datastreams": [], "events": []}],
            "status": {"sources": [{"sid": "S146", "captured": 4, "expected_slots": 24}, {"sid": "S10", "captured": 13, "expected_slots": 96},
                                   {"sid": "S69", "captured": 6, "expected_slots": 48}, {"sid": "S68", "captured": 6, "expected_slots": 48},
                                   {"sid": "S70", "captured": 0, "expected_slots": 48}]},
            "derived": [{"t": "2026-09-08T23:35:00Z", "organ": "news-sorter", "category": "iskljucenja", "belgrade": True, "zones": [{"name": "Zemun", "score": 0.9}]}],
            "organ_runs": []}


CONTEXT = {"hexes": [[20.4016, 44.8458, 5200], [20.405, 44.847, 3100], [20.70, 44.60, 900]]}


class LiveDir(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._out, self._ctx = om.OUT_DIR, om.CONTEXT
        om.OUT_DIR = pathlib.Path(self.tmp.name) / "mind"
        om.CONTEXT = om.OUT_DIR / "context.json"
        self._reg = om.register
        om.register = lambda: dict(REG)

    def tearDown(self):
        om.OUT_DIR, om.CONTEXT = self._out, self._ctx
        om.register = self._reg
        self.tmp.cleanup()


class DigestTests(unittest.TestCase):
    def test_facts_connections_and_context(self):
        dg = om.digest(snapshot(), hours=6, now=NOW, context=CONTEXT)
        kinds = [f["kind"] for f in dg["facts"]]
        self.assertIn("spread", kinds)
        self.assertIn("silence", kinds)
        self.assertIn("headlines", kinds)
        conns = [f for f in dg["facts"] if f["kind"] == "connection"]
        self.assertTrue(any(f.get("parameter") == "PM10" and f.get("delta") == 11 for f in conns), "the city maximum moved 30 -> 41")
        self.assertTrue(any(f.get("station") == "Pinki" and f.get("delta") == -14 for f in conns), "displayed free spaces moved 102 -> 88")
        self.assertTrue(any(f.get("zone") == "Zemun" and f.get("station") == "Zemun" for f in conns), "news zone meets a station")
        ctx = [f for f in dg["facts"] if f["kind"] == "context"]
        self.assertTrue(any(f["station"] == "Zemun" and f["people_thousands"] == 8 for f in ctx), "5200 + 3100 within 1 km of Zemun")
        for n in ("41", "30", "102", "88", "8"):
            self.assertIn(n, dg["numbers"])
        self.assertEqual(len(dg["headlines"]), 3)

    def test_untimed_source_is_said_to_be_untimed(self):
        dg = om.digest(snapshot(), hours=6, now=NOW)
        park = next(f for f in dg["facts"] if f.get("sid") == "S10" and f["kind"] == "reception")
        self.assertTrue(park["untimed"])
        self.assertIn("publishes no measurement time", park["en"])


def fake_embed(model, texts):
    """Same event -> nearly parallel vectors; the concert -> orthogonal."""
    return [[1.0, 0.05, 0.0] if "bez vode" in t else [0.0, 0.0, 1.0] for t in texts]


class OrganelleTests(unittest.TestCase):
    def test_embed_linker_links_the_same_event_across_outlets_only(self):
        dg = om.digest(snapshot(), hours=6, now=NOW)
        links = om.embed_linker(dg, "paraphrase-multilingual", embed=fake_embed)
        self.assertEqual(len(links), 1)
        self.assertEqual({links[0]["a"]["sid"], links[0]["b"]["sid"]}, {"S68", "S69"})
        self.assertGreaterEqual(links[0]["similarity"], 0.99)
        self.assertIn("similarity", links[0]["en"])
        dg2 = om.annotate(dg, links, {}, None, "paraphrase-multilingual")
        self.assertIn("1.00", dg2["numbers"])
        self.assertEqual(dg2["facts"][-1]["kind"], "link")

    def test_surprise_ranker_keeps_only_valid_ratings(self):
        dg = om.digest(snapshot(), hours=6, now=NOW)
        conn_ids = [f["id"] for f in dg["facts"] if f["kind"] == "connection"]
        def chat(model, prompt, schema=None, num_predict=0, temperature=0.0):
            return {"ratings": [{"id": conn_ids[0], "surprise": 4}, {"id": "F99", "surprise": 5}, {"id": conn_ids[1], "surprise": 9}]}
        r = om.surprise_ranker(dg, "llama3.2:1b", chat)
        self.assertEqual(r, {conn_ids[0]: 4})
        dg2 = om.annotate(dg, [], r, "llama3.2:1b", None)
        self.assertEqual(dg2["facts"][-1]["kind"], "helper")
        self.assertIn("4", dg2["numbers"])


class ValidatorTests(unittest.TestCase):
    dg = {"as_of": "x", "window_hours": 6, "numbers": ["2", "20", "41", "102"], "facts": [{"id": "F1"}, {"id": "F2"}]}

    def ans(self, **kw):
        base = {"text": "Two stations [F1] reported, the highest at 41.", "cites": ["F1"],
                "hypotheses": ["maybe Zemun is busier at night"], "questions": [], "next_check": "", "claim": {}}
        base.update(kw)
        return base

    def test_grounded_is_accepted(self):
        self.assertEqual(om.validate(self.ans(), self.dg), (True, []))

    def test_foreign_number_unknown_fact_and_no_inline_citation_are_refused(self):
        ok, why = om.validate(self.ans(text="Stations reported 999 values.", cites=["F1"]), self.dg)
        self.assertFalse(ok)
        self.assertTrue(any("999" in r for r in why))
        self.assertTrue(any("cites nothing inside" in r for r in why))
        ok2, why2 = om.validate(self.ans(text="Stations [F7] reported."), self.dg)
        self.assertTrue(any("unknown fact" in r for r in why2))

    def test_prediction_as_fact_prompt_echo_and_claim_shape(self):
        ok, _ = om.validate(self.ans(text="It will be worse tomorrow [F1]."), self.dg)
        self.assertFalse(ok)
        ok2, why2 = om.validate(self.ans(text="You notice. Two stations [F1] reported at 41."), self.dg)
        self.assertTrue(any("echoed the prompt" in r for r in why2))
        ok3, _ = om.validate(self.ans(claim={"kind": "spread", "sid": "S146", "parameter": "PM10", "lo": 20, "hi": 41, "within_minutes": 120}), self.dg)
        self.assertTrue(ok3)
        ok4, why4 = om.validate(self.ans(claim={"kind": "reception", "sid": "S146", "within_minutes": 3}), self.dg)
        self.assertTrue(any("horizon" in r for r in why4))

    def test_program_binds_citations_by_numbers_when_the_model_forgot(self):
        dg = om.digest(snapshot(), hours=6, now=NOW)
        text, how = om.ensure_citations("PM10 ranged from 20 to 41 with 2 stations; the maximum moved from 30 to 41.", dg)
        self.assertEqual(how, "numbers")
        self.assertIn("[F4]", text)     # the spread fact carries 20 and 41
        self.assertIn("[F5]", text)     # the connection fact carries 30 and 41
        ok, why = om.validate({"text": text, "cites": [], "hypotheses": [], "questions": [], "next_check": "", "claim": {}}, dg)
        self.assertTrue(ok, why)
        t2, how2 = om.ensure_citations("Nothing here points anywhere.", dg)
        self.assertEqual(how2, "none")
        t3, how3 = om.ensure_citations("Already cited [F2].", dg)
        self.assertEqual((t3, how3), ("Already cited [F2].", "inline"))

    def test_restating_the_conversation_is_refused(self):
        prev = ["The city's maximum PM10 and NO2 values have increased significantly between 07:00 and 08:00 UTC, as indicated by the spread model."]
        ok, why = om.validate(self.ans(text="The city's maximum PM10 and NO2 values have increased significantly between 07:00 and 08:00 UTC [F1], as indicated by the spread model."), self.dg, previous=prev)
        self.assertFalse(ok)
        self.assertTrue(any("restates" in r for r in why))
        ok2, _ = om.validate(self.ans(), self.dg, previous=prev)
        self.assertTrue(ok2)

    def test_voice_split_keeps_citations_out_of_the_models_hands(self):
        plain, cites = om.voice_split("Two stations [F2] reported [F4], the highest at 41 [F4].")
        self.assertEqual((plain, cites), ("Two stations reported, the highest at 41.", "[F2][F4]"))
        ok, why = om.validate_voice("Vrijednosti su se promijenile [F1].", "Values changed [F1].", self.dg)
        self.assertTrue(any("ijekavian" in r for r in why))

    def test_ekavica_guard_catches_ijekavian_and_croatian_and_spares_ekavian(self):
        bad = ["Kvalitet zraka u gradu.", "To sugerira viši uticaj.", "Na cesti je gužva.", "Milijun ljudi.", "Vrijeme je lijepo.", "Provjerio sam mjesto i vrijednost.", "Gdje je stanica? Ovdje.", "Sljedeći tjedan, u ponedjeljak.",
               "Dvije stanice su promijenile vrijednost.", "Riječ je o mjerenju.", "Kvalitet zraka: utjecaj prometa, vjerojatno.",
               "U posljednjih sat vremena", "Tisuću ljudi", "obje stanice", "Prosjek je 12", "Primjer:", "u ljeto", "sugerira viši utjecaj"]
        for b in bad:
            self.assertTrue(om.ijekavian_hits(b), b)
        good = ["Vreme je lepo, proverio sam mesto i vrednost.", "Grad Beograd, Republika Srbije, linije 16 i 95, informacije o prijemu.",
                "Objekat na pijaci, dijeta, hijerarhija i orijentacija.", "Odjednom su se Sjedinjene Države javile.",
                "Gradjevina medju zgradama, izmedju.", "Kolovoz je mokar, travnjak zelen.", "Odjek, prijem, prijava, prijatelj, subjekat, objektivno.",
                "Sledeće nedelje u ponedeljak; u poslednjih sat vremena, uvek.", "Deca i susedi; svet je mali; osećam; zamenio; primer.",
                "Voljen, želje, bolje, polje, poljem", "Stanica Vračar javila 44 µg/m³ PM10 [F3][F5]", "Mesec, mesečno, mešavina, smeša",
                "Ne verujem, Srbije, avenije, serije, bijenale, pijenje", "jednom, jesen, jezik, ujedno, podjednako, najednom, nije, nijedan, sjaj, sjediniti"]
        for g in good:
            self.assertEqual(om.ijekavian_hits(g), [], g)
        # the guard is applied to the hypotheses and questions too, and their count must match
        en = "Two stations [F1] reported, the highest at 41."
        ok, why = om.validate_voice("Dve stanice [F1] su javile, najviše 41.", en, self.dg, ["možda pada prije jutra"], [], 1, 0)
        self.assertTrue(any("ijekavian hypothesis" in r for r in why), why)
        ok2, why2 = om.validate_voice("Dve stanice [F1] su javile, najviše 41.", en, self.dg, [], ["Zašto?"], 2, 1)
        self.assertTrue(any("hypothesis count" in r for r in why2), why2)
        self.assertEqual(om.validate_voice("Dve stanice [F1] su javile, najviše 41.", en, self.dg, ["možda pada pre jutra"], ["Zašto ćuti?"], 1, 1), (True, []))

    def test_stale_numbers_of_earlier_utterances_are_blanked_before_they_are_shown(self):
        dg = {"numbers": ["32", "08", "00"]}
        self.assertEqual(om.stale_numbers_blanked("PM10 rose from 85 to 119 [F5] at 08:00 with 32 stations [F2].", dg),
                         "PM10 rose from [n] to [n] [F5] at 08:00 with 32 stations [F2].")
        dg2 = {"facts": [{"id": "F1", "en": "a", "kind": "x"}, {"id": "F4", "en": "b", "kind": "x"}], "numbers": ["41"], "headlines": []}
        prompt = om.prompt_for(om.ENTITIES[0], dg2, [], [{"entity": "skeptic", "en": "The maximum was 777 [F4], not 41."}])
        self.assertIn("[n]", prompt)
        self.assertNotIn("777", prompt)
        self.assertIn("41", prompt)

    def test_voice_retries_once_with_the_refusal_read_back_and_shows_nothing_when_it_still_fails(self):
        calls = []
        def chat(model, prompt, schema=None, num_predict=1000, temperature=0.5):
            calls.append(prompt)
            if len(calls) == 1:
                return {"sr": "Dvije stanice su javile, najviše 41.", "hypotheses": [], "questions": []}
            return {"sr": "Dve stanice su javile, najviše 41.", "hypotheses": [], "questions": []}
        row = {"hypotheses": [], "questions": []}
        om.voice(row, "Two stations [F1] reported, the highest at 41.", self.dg, "fake-voice", chat)
        self.assertEqual((row["sr_state"], row["voice_attempts"]), ("voiced", 2))
        self.assertTrue(row["sr"].endswith("[F1]"))
        self.assertIn("Prethodni pokušaj je odbijen", calls[1])
        self.assertIn("dvije", calls[1])
        calls.clear()
        def stubborn(model, prompt, schema=None, num_predict=1000, temperature=0.5):
            calls.append(prompt)
            return {"sr": "Dvije stanice su javile, najviše 41.", "hypotheses": ["vjerojatno pada"], "questions": []}
        row2 = {"hypotheses": ["probably falls"], "questions": []}
        om.voice(row2, "Two stations [F1] reported, the highest at 41.", self.dg, "fake-voice", stubborn)
        self.assertTrue(row2["sr_state"].startswith("refused: ijekavian"), row2["sr_state"])
        self.assertEqual((row2["sr"], row2["hypotheses_sr"], row2["voice_attempts"], len(calls)), ("", [], 2, 2))
        # C-033. `sr` stays empty so nothing downstream can show an unvalidated sentence as validated,
        # but the sentence is KEPT: it is the only Serbian this thought ever had. Measured before this:
        # 27 refused renderings, 0 of them with their text still in the row.
        self.assertIn("Dvije stanice", row2["sr_refused"])
        self.assertEqual(row2["hypotheses_sr_refused"], ["vjerojatno pada"])
        row3 = {"hypotheses": [], "questions": []}
        om.voice(row3, "Two stations [F1] reported.", self.dg, None, stubborn)
        self.assertEqual(row3["sr_state"], "no voice model")

    def test_a_model_that_will_not_answer_hands_the_step_to_the_next_one(self):
        """C-036. The body has 8 GB and the preferred thinker is 3.4 GB. When free memory dips the
        daemon cannot load it, the call times out, and the step used to record silence and move on.
        Measured 2026-09-10: from 00:38 to 01:22 every model step failed that way and the mind said
        nothing for 44 minutes, while a 1 GB model that was already pulled sat unused. The register
        lists the models in order for exactly this reason; now the order is used."""
        avail = ["qwen3.5:4b", "qwen2.5:1.5b", "llama3.2:1b"]
        chain = om._chain(avail, ["qwen3.5:4b", "qwen2.5:1.5b", "llama3.2:1b"], False)
        self.assertEqual(chain, avail)
        self.assertEqual(om._chain(avail, ["qwen3.5:4b"], False), ["qwen3.5:4b"])
        seen = []

        def dead_then_alive(model, prompt, **kw):
            seen.append(model)
            if model == "qwen3.5:4b":
                raise TimeoutError("timed out")
            return {"text": "ok"}
        rec = {}
        answer, spoke, tried = om.chat_chain(chain, "p", dead_then_alive, rec)
        self.assertEqual((answer, spoke), ({"text": "ok"}, "qwen2.5:1.5b"))
        self.assertEqual(tried, ["qwen3.5:4b: TimeoutError"])
        self.assertEqual(rec["calls"], 1)          # the call that worked, not the one that did not
        self.assertEqual(seen, ["qwen3.5:4b", "qwen2.5:1.5b"])

        def all_dead(model, prompt, **kw):
            raise TimeoutError("timed out")
        answer2, spoke2, tried2 = om.chat_chain(chain, "p", all_dead, {})
        self.assertIsNone(answer2)
        self.assertIsNone(spoke2)                  # nothing spoke, so nothing is credited
        self.assertEqual(len(tried2), 3)

    def test_a_clock_is_a_time_not_a_number(self):
        """C-034. `number not in digest: 08` was the commonest reason an utterance was thrown away -
        17 of them, with 09, 02, 23 and 03 behind it, every one an HOUR. The entity wrote "between
        08:00 and 09:00 UTC", the validator pulled 08 and 09 out as quantities, did not find them
        among the digest's numbers, and refused a sentence that was right."""
        dg = om.digest(snapshot(), hours=6, now=NOW)
        self.assertIn("clock", dg)
        self.assertNotIn("08", om._nums("between 08:00 and 09:00 UTC"))
        self.assertEqual(om._clocks("between 08:00 and 09:00 UTC"), {"08:00", "09:00"})
        self.assertIn("22:00", dg["clock"])       # a fact's own hour
        self.assertIn("00:00", dg["clock"])       # a whole hour of the window
        fid = next(f["id"] for f in dg["facts"] if "41" in om._nums(f["en"]))
        ok, why = om.validate({"text": f"The highest PM10 was 41 in the hour ending 23:00 [{fid}].", "cites": [fid],
                               "hypotheses": [], "questions": [], "next_check": "", "claim": None}, dg)
        self.assertTrue(ok, why)
        ok2, why2 = om.validate({"text": f"The highest PM10 was 41 at 05:00 [{fid}].", "cites": [fid],
                                 "hypotheses": [], "questions": [], "next_check": "", "claim": None}, dg)
        self.assertTrue(any("time outside the window" in r for r in why2), why2)

    def test_a_claim_that_names_its_source_is_resolved_to_the_id_that_can_be_settled(self):
        """C-035. Every claim ever settled named S146; every `unverifiable` one named SEPA, RHMZ
        automatic stations or Sensor.Community - 10 of 19, none of them because reality was unclear.
        The scorer looks a source up by id, so the id is what has to be stored."""
        dg = om.digest(snapshot(), hours=6, now=NOW)
        self.assertEqual(om.resolve_sid("S146", dg), "S146")
        self.assertEqual(om.resolve_sid("SEPA", dg), "S146")
        self.assertEqual(om.resolve_sid("sepa", dg), "S146")
        self.assertIsNone(om.resolve_sid("Elektrodistribucija", dg))
        fid = next(f["id"] for f in dg["facts"] if f.get("sid") == "S146")
        answer = {"text": f"SEPA has been reporting through the window [{fid}].", "cites": [fid], "hypotheses": [], "questions": [],
                  "next_check": "", "claim": {"kind": "reception", "sid": "SEPA", "within_minutes": 90}}
        ok, why = om.validate(answer, dg)
        self.assertTrue(ok, why)
        self.assertEqual(answer["claim"]["sid"], "S146")   # normalised in place, so the scorer can find it
        answer2 = dict(answer); answer2["claim"] = {"kind": "reception", "sid": "the weather people", "within_minutes": 90}
        ok2, why2 = om.validate(answer2, dg)
        self.assertTrue(any("not in these facts" in r for r in why2), why2)

    def test_the_prompt_tells_the_entity_which_source_ids_exist(self):
        dg = om.digest(snapshot(), hours=6, now=NOW)
        p = om.prompt_for(om.ENTITIES[0], dg, [], [])
        self.assertIn("Sources you may name in a claim:", p)
        self.assertIn("S146 = ", p)
        self.assertIn("cannot be scored", p)

    def test_voice_must_be_faithful_and_serbian(self):
        en = "Two stations [F1] reported, the highest at 41."
        self.assertEqual(om.validate_voice("Dve stanice [F1] su javile, najviše 41.", en, self.dg), (True, []))
        ok, why = om.validate_voice("Dve stanice [F1] su javile, najviše 777.", en, self.dg)
        self.assertTrue(any("not in the original" in r for r in why))
        ok2, why2 = om.validate_voice("možeš da se to je ne dovolno [F1] [F2]", en, self.dg)
        self.assertTrue(any("citations differ" in r for r in why2))
        ok3, why3 = om.validate_voice("Two stations [F1] reported, the highest at 41.", en, self.dg)
        self.assertFalse(ok3)


def fake_chat_factory(log: list):
    """Entities answer in English; the voice call renders Serbian; the ranker rates."""
    def chat(model, prompt, schema=None, num_predict=1000, temperature=0.5):
        if prompt.startswith("Prevedi ovu misao"):
            text = prompt.split("Misao: ", 1)[1].split("\nPretpostavke:", 1)[0]
            hyps = json.loads(prompt.split("Pretpostavke: ", 1)[1].split("\nPitanja:", 1)[0])
            qs = json.loads(prompt.split("Pitanja: ", 1)[1].split("\n\nOdgovori", 1)[0])
            def sr_of(t):
                return t.replace("Two stations", "Dve stanice").replace("reported", "su javile").replace("the highest at", "najviše").replace("Kurir is silent", "Kurir ćuti") \
                        .replace("Parking publishes no measurement time", "Parking ne objavljuje vreme merenja").replace("that is a reception, not a measurement", "to je prijem, ne merenje") \
                        .replace("The Skeptic is right", "Sumnjalo je u pravu").replace("PM10 up to", "PM10 do").replace("may follow traffic", "možda prati saobraćaj").replace("across", "u") \
                        .replace("maybe it falls by morning", "možda padne do jutra").replace("Why is Kurir silent?", "Zašto Kurir ćuti?")
            log.append(("voice", False, False, prompt))
            return {"sr": sr_of(text), "hypotheses": [sr_of(h) for h in hyps], "questions": [sr_of(q) for q in qs]}
        if prompt.startswith("You rate connections"):
            log.append(("ranker", False, False, prompt))
            return {"ratings": []}
        ent = "observer" if "You are Observer" in prompt else "skeptic" if "You are Skeptic" in prompt else "connector"
        replying = "What the other entities just said" in prompt
        log.append((ent, replying, "Your notebook" in prompt, prompt))
        if ent == "observer":
            if replying:   # a different sentence when answering: restating is refused by code
                return {"text": "Both of you leave out the silence: Kurir sent nothing [F10] while two stations kept reporting [F2].", "cites": ["F10"],
                        "hypotheses": [], "questions": [], "next_check": "", "claim": {"kind": "reception", "sid": "S146", "within_minutes": 90}}
            return {"text": "Two stations [F2] reported, the highest at 41 [F4]; Kurir is silent [F10].", "cites": ["F2"], "hypotheses": [],
                    "questions": ["Why is Kurir silent?"], "next_check": "Kurir", "claim": {"kind": "reception", "sid": "S146", "within_minutes": 90}}
        if ent == "skeptic":
            if replying:
                return {"text": "The Observer counts 2 stations [F2] but one of them carries the maximum alone [F4]; two points are not a trend.", "cites": ["F4"],
                        "hypotheses": [], "questions": [], "next_check": "", "claim": {}}
            return {"text": "Parking publishes no measurement time [F6]; that is a reception, not a measurement.", "cites": ["F6"],
                    "hypotheses": [], "questions": [], "next_check": "", "claim": {}}
        if not replying:   # connector alone: an invented number -> refused, never shown to the others
            return {"text": "PM10 up to 41 [F4] across 7777 stations.", "cites": ["F4"], "hypotheses": [], "questions": [], "next_check": "", "claim": {}}
        return {"text": "The Skeptic is right [F6]; PM10 up to 41 [F4] may follow traffic.", "cites": ["F6", "F4"],
                "hypotheses": ["maybe it falls by morning"], "questions": [], "next_check": "",
                "claim": {"kind": "spread", "sid": "S146", "parameter": "PM10", "lo": 20, "hi": 50, "within_minutes": 120}}
    return chat


class ConversationTests(LiveDir):
    def test_council_two_rounds_voice_notebook_and_no_echo_of_refused(self):
        log = []
        rec = om.run(now=NOW, chat=fake_chat_factory(log), tags=lambda: MODELS, embed=fake_embed, snap=snapshot(), orchestration="council")
        self.assertEqual(rec["state"], "derived")
        self.assertEqual(rec["models"]["voice"], "qwen2.5:3b")
        self.assertEqual(rec["organelles"]["embed-linker"], "paraphrase-multilingual:latest")
        self.assertEqual(rec["organelles"]["links"], 1)
        rows = [r for r in om._rows(om.OUT_DIR / "2026-09.jsonl") if r["state"] in ("thought", "rejected")]
        self.assertEqual(len(rows), 6)
        r1_conn = next(r for r in rows if r["entity"] == "connector" and r["round"] == 1)
        self.assertEqual(r1_conn["state"], "rejected")
        for ent, replying, _, prompt in log:
            if replying and ent != "connector":
                self.assertNotIn("7777", prompt)
        r2_conn = next(r for r in rows if r["entity"] == "connector" and r["round"] == 2)
        self.assertEqual(r2_conn["state"], "thought")
        self.assertEqual(sorted(r2_conn["replies_to"]), ["observer", "skeptic"])
        self.assertEqual(r2_conn["sr_state"], "voiced")
        self.assertIn("Sumnjalo je u pravu", r2_conn["sr"])
        self.assertTrue(r2_conn["sr"].endswith("[F6][F4]"), r2_conn["sr"])
        self.assertGreaterEqual(rec["voiced"], 3)   # the fake voice only knows a few phrases
        self.assertTrue(all(r["ai_generated"] for r in rows))
        claims = om._rows(om.OUT_DIR / "claims.jsonl")
        self.assertEqual([c["entity"] for c in claims], ["observer", "observer", "connector"])
        nb = om.notebook("connector")
        self.assertEqual([n["state"] for n in nb], ["rejected", "thought"])
        log2 = []
        om.run(now=NOW + timedelta(minutes=30), chat=fake_chat_factory(log2), tags=lambda: MODELS, embed=fake_embed, snap=snapshot(), orchestration="council")
        # the notebook reads back only what went wrong (refusals, claim outcomes) - an entity never re-reads its own
        # accepted text, because on the first night that is what it copied
        self.assertTrue(all(has_mem for e, _, has_mem, _ in log2 if e == "connector"))
        self.assertFalse(any(has_mem for e, _, has_mem, _ in log2 if e == "skeptic"))
        self.assertIn("7777", next(p for e, rep, _, p in log2 if e == "connector" and not rep))

    def test_relay_orchestration_and_alternation(self):
        log = []
        rec = om.run(now=NOW, chat=fake_chat_factory(log), tags=lambda: MODELS, embed=fake_embed, snap=snapshot(), orchestration="relay")
        rows = [r for r in om._rows(om.OUT_DIR / "2026-09.jsonl") if r["state"] in ("thought", "rejected")]
        self.assertEqual([(r["entity"], r["round"]) for r in rows], [("observer", 1), ("skeptic", 2), ("connector", 3), ("observer", 4)])
        self.assertEqual(rows[1]["replies_to"], ["observer"])
        self.assertEqual(sorted(rows[2]["replies_to"]), ["observer", "skeptic"])
        rec2 = om.run(now=NOW + timedelta(minutes=30), chat=fake_chat_factory([]), tags=lambda: MODELS, embed=fake_embed, snap=snapshot())
        self.assertEqual(rec2["orchestration"], "relay", "one receipt so far -> odd index -> relay")

    def test_silent_daemon_and_cloud_only_leave_receipts(self):
        rec = om.run(now=NOW, chat=lambda *a, **k: {}, tags=lambda: None, snap=snapshot())
        self.assertEqual(rec["state"], "organ_silent")
        rec2 = om.run(now=NOW + timedelta(minutes=1), chat=lambda *a, **k: {}, tags=lambda: ["qwen3.5:cloud"], snap=snapshot())
        self.assertIn("no local model", rec2["reason"])


class DripTests(LiveDir):
    def test_six_drops_make_one_cycle_and_context_fills(self):
        log = []
        chat = fake_chat_factory(log)
        names = []
        for i in range(6):
            rec = om.step(now=NOW + timedelta(minutes=4 * i), chat=chat, tags=lambda: MODELS, embed=fake_embed, snap=snapshot(extra_hour=(i == 5)))
            names.append(rec["step_name"])
        self.assertEqual(names, list(om.STEPS))
        ctx = om._context()
        self.assertEqual((ctx["step"], ctx["cycle"]), (6, 1))
        self.assertEqual(len(ctx["links"]), 1)
        self.assertEqual([c["entity"] for c in ctx["conversation"]], ["observer", "skeptic", "connector"], "the connector answered the others and was accepted")
        rows = om._rows(om.OUT_DIR / "2026-09.jsonl")
        kinds = [(r["entity"], r["state"]) for r in rows]
        self.assertIn(("organelle", "organelle"), kinds)
        conn = next(r for r in rows if r["entity"] == "connector")
        self.assertEqual(conn["state"], "thought")
        self.assertEqual(sorted(conn["replies_to"]), ["observer", "skeptic"])
        self.assertEqual(conn["sr_state"], "voiced")
        # the sixth step is the scoring step; the observer's 90-minute claim is not due yet, so it stays open -
        # scoring never settles a claim early
        claims = om._rows(om.OUT_DIR / "claims.jsonl")
        obs = next(c for c in claims if c["entity"] == "observer")
        self.assertIsNone(obs["outcome"])
        om.score(now=NOW + timedelta(hours=3), snap=snapshot(extra_hour=True))
        obs = next(c for c in om._rows(om.OUT_DIR / "claims.jsonl") if c["entity"] == "observer")
        self.assertEqual(obs["outcome"], "true")
        self.assertEqual(om.scoreboard()["organelle"]["drops"], 1)

    def test_paused_file_stops_the_drip(self):
        om.OUT_DIR.mkdir(parents=True, exist_ok=True)
        (om.OUT_DIR / "PAUSED").write_text("editor: reviewing", encoding="utf-8")
        rec = om.step(now=NOW, chat=lambda *a, **k: {}, tags=lambda: MODELS, snap=snapshot())
        self.assertEqual(rec["state"], "paused")
        self.assertEqual(om._context()["step"], 0)


class RetractionAndScoringTests(LiveDir):
    def test_retraction_voids_claim_and_scoring_settles(self):
        log = []
        om.run(now=NOW, chat=fake_chat_factory(log), tags=lambda: MODELS, embed=fake_embed, snap=snapshot(), orchestration="council")
        row = om.retract(om.stamp(NOW), "connector", 2, "test retraction", now=NOW + timedelta(minutes=1))
        self.assertEqual(row["state"], "retracted")
        claims = om._rows(om.OUT_DIR / "claims.jsonl")
        self.assertEqual(next(c for c in claims if c["entity"] == "connector")["outcome"], "retracted")
        self.assertEqual(om.scoreboard()["connector"]["retracted"], 1)
        res = om.score(now=NOW + timedelta(hours=3), snap=snapshot(extra_hour=True))
        self.assertEqual(res["settled_now"], 2)
        by = {(c["entity"], c["claim"]["kind"]): c for c in om._rows(om.OUT_DIR / "claims.jsonl")}
        self.assertEqual(by[("observer", "reception")]["outcome"], "true")
        self.assertTrue(any(n.get("claim_outcome") == "true" for n in om.notebook("observer")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
