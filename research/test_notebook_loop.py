#!/usr/bin/env python3
"""test_notebook_loop.py - a rejected output may not be shown to the thing that produced it when the
reason for rejection was the output's form.

C-037 rendered the refusal REASON without digits, so a model copying it could not import numbers that
are by construction absent from the digest. That stopped the echo reaching the page and left the loop
running: the refused sentence still went into the notebook and the notebook still quoted it back, so
the skeptic repeated one such sentence in rounds 369, 375, 381, 387 and 393 - each time with the newer,
digit-free wording pasted into it.

Quoting a sentence back to a model is not neutral. It is the copy.
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import organ_mind as om  # noqa: E402

# The real entity, not a hand-made stand-in: a fixture missing role_en passed the first draft of this
# file and failed against the actual prompt builder, which is the fixture lying about the system.
ENT = next(e for e in om.ENTITIES if e["id"] == "skeptic")
DG = {"facts": [{"id": "F1", "en": "PM10 at Vracar is 41 ug/m3"}], "clock": [], "numbers": {"41"},
      "sids": [], "sid_names": {}, "window_hours": 6}


def prompt(memory):
    return om.prompt_for(ENT, DG, memory, [])


class Notebook(unittest.TestCase):
    def test_an_echoed_sentence_is_never_quoted_back(self):
        """The exact shape measured on 2026-09-10, with the fix's own wording inside it."""
        poisoned = ("The city's maximum values of PM10 and NO2 have significantly increased between "
                    "08:00 and 09:00 UTC, as indicated by the ' and it was refused because you named "
                    "an hour outside the window you were given. Do not say it again.")
        p = prompt([{"at": "2026-09-10T05:00", "state": "rejected", "text": poisoned,
                     "reason": "echoed its own notebook: as indicated by the '"}])
        self.assertNotIn("as indicated by the '", p,
                         "the echoed sentence was handed back to the entity that produced it")
        self.assertNotIn("08:00", p, "the echoed sentence's contents reached the prompt anyway")
        self.assertIn("deliberately not repeated here", p,
                      "the entity is not told why its sentence is missing")

    def test_an_ordinary_refusal_is_still_quoted_verbatim(self):
        """For everything that was not an echo, the entity's own words ARE the feedback and must not
        be withheld - withholding them would be a different kind of blindness."""
        p = prompt([{"at": "2026-09-10T05:00", "state": "rejected",
                     "text": "PM10 at Vracar is 99 and rising fast",
                     "reason": "number not in the cited facts: 99"}])
        self.assertIn("PM10 at Vracar is 99", p,
                      "an ordinary refusal no longer shows the entity what it said")

    def test_the_reason_still_carries_no_digits(self):
        """C-037's own guarantee, held in place beside the new one."""
        self.assertNotRegex(om.reason_category("number not in the cited facts: 447"), r"\d")
        self.assertNotRegex(om.reason_category("time outside the window: 09:00"), r"\d")

    def test_the_validators_vocabulary_is_still_refused_in_an_utterance(self):
        """Muting the loop must not be mistaken for removing the guard that catches it."""
        self.assertTrue(om.NOTEBOOK_VOCAB.search("... and it was refused because you named an hour "
                                                 "outside the window you were given"))
        self.assertTrue(om.NOTEBOOK_VOCAB.search("as indicated by the '"))

    def test_every_sentence_the_validator_can_say_is_refused_inside_an_utterance(self):
        """C-047's second half. The vocabulary was written by hand against the RAW refusal strings;
        C-037 then changed what the entity is actually told and nobody updated it, so the loop was
        caught by an unrelated fragment rather than by the guard meant to catch it. Derived now, and
        asserted here so it cannot drift again."""
        missed = [said for _k, said in om.REASON_CATEGORY
                  if not om.NOTEBOOK_VOCAB.search("the city is calm, " + said + " today")]
        self.assertEqual(missed, [],
                         "the validator can say things its own guard does not recognise: " + "; ".join(missed))

    def test_an_ordinary_observation_is_not_refused_for_containing_a_common_word(self):
        """The guard must not be so wide that it refuses the city. 'claim', 'too short' and 'not
        English' are ordinary English and are deliberately not in the derived list."""
        for ok_text in ("PM10 at Vracar is 41 and the claim is due in two hours [F1]",
                        "the queue was too short to measure [F1]",
                        "the notice was not in English [F1]"):
            self.assertIsNone(om.NOTEBOOK_VOCAB.search(ok_text),
                              "an ordinary observation was refused as validator language: " + ok_text)


if __name__ == "__main__":
    unittest.main()
