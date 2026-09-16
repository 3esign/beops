"""C-071: a number keeps the role of the fact it came from. Every sentence below was on the public page."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import organ_mind as m  # noqa: E402

F4 = {"id": "F4", "kind": "spread", "parameter": "PM10",
      "en": "PM10 in that hour, compared across 31 stations: lowest 8 (Zemun TB), highest 85 (Surčin) µg/m³."}
F5 = {"id": "F5", "kind": "connection", "parameter": "PM10",
      "en": "Connection: the highest measured value of PM10 moved from 76 to 85 µg/m³ between the hours 19:00 and 20:00 (source labels)."}
F8 = {"id": "F8", "kind": "spread", "parameter": "PM2.5",
      "en": "PM2.5 in that hour, compared across 31 stations: lowest 5 (Topčiderska zvezda), highest 63 (Surčin) µg/m³."}
F9 = {"id": "F9", "kind": "connection", "parameter": "PM2.5",
      "en": "Connection: the highest measured value of PM2.5 moved from 18 to 63 µg/m³ between the hours 19:00 and 20:00 (source labels)."}
DG = {"facts": [F4, F5, F8, F9], "numbers": set().union(*(m._nums(f["en"]) for f in (F4, F5, F8, F9))), "sids": {}}


def ok(text):
    return m.validate({"text": text, "cites": []}, DG)


class Roles(unittest.TestCase):
    def test_a_spread_across_stations_is_not_a_rise(self):
        good, why = ok("SEPA reported 32 instruments with PM10 values rising from 8 to 85 µg/m³ [F4].")
        self.assertFalse(good)
        self.assertTrue(any("spread" in w or "no cited connection" in w for w in why), why)

    def test_a_number_of_another_pollutant_is_refused(self):
        good, why = ok("Air quality improved, with PM10 values dropping from 85 to 63 µg/m³. [F4][F5][F8][F9]")
        self.assertFalse(good)
        self.assertTrue(any("belongs to PM2.5" in w for w in why), why)

    def test_a_real_change_is_accepted(self):
        self.assertEqual(ok("The highest PM10 value moved from 76 to 85 µg/m³ between the labelled hours [F5]."), (True, []))

    def test_a_spread_stated_as_places_is_accepted(self):
        self.assertEqual(ok("PM10 ranged across stations between 8 and 85 µg/m³ in that hour [F4]."), (True, []))

    def test_words_put_in_a_source_s_mouth_in_any_tense(self):
        self.assertFalse(ok("SEPA reported that the air is bad, PM10 at 85 µg/m³ [F4].")[0])
        self.assertFalse(ok("Tanjug warned of pollution with PM10 at 85 µg/m³ [F4].")[0])


class Template(unittest.TestCase):
    def test_new_numbers_do_not_make_a_new_sentence(self):
        a = "SEPA reported 32 instruments 16 min ago [F2], while citizen sensors arrived 4 min ago [F10]."
        b = "SEPA reported 32 instruments 61 min ago [F2], while citizen sensors arrived 7 min ago [F10]."
        self.assertTrue(m.echo_of(b, [a])[0])


class Script(unittest.TestCase):
    def test_a_word_in_two_scripts_is_refused(self):
        self.assertEqual(m.mixed_script_words("PM10 je dosegaо 51"), ["dosegaо"])
        self.assertEqual(m.mixed_script_words("Уханшени и uhapšeni"), [])


class Digest(unittest.TestCase):
    def test_the_digest_words_a_spread_as_places(self):
        src = (ROOT / "tools" / "organ_mind.py").read_text(encoding="utf-8")
        self.assertIn("compared across", src)
        self.assertNotIn("in that hour: from", src)


if __name__ == "__main__":
    unittest.main()
