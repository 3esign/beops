import pathlib
import tempfile
import unittest
from datetime import timedelta

from observe_10k import LAST, GRACE, name, publish
from write_izvestaj import (GROUPS, can_close, change_rows, location_tables,
                           publish_report, received, trajectory_table)


def sample(value=0):
    return {'state': 'captured', 'slot': LAST.isoformat(), 'attempted_at': LAST.isoformat(),
            'summary': {'locations': [{'name': 'fixture', 'free_spaces': value, 'observed_at': None}]}}


class ReportTests(unittest.TestCase):
    def test_protocol_group_not_baba_visnjina(self):
        group = next(iter(GROUPS.values()))
        self.assertIn('Parkiralište "Opština NBGD"', group)
        self.assertNotIn('Garaža "Baba Višnjina"', group)

    def test_zero_and_missing_preserved(self):
        report = trajectory_table([sample(0), sample(None)])
        self.assertIn('| fixture | 0 | — |', report)
        self.assertIsNone(change_rows(sample(0), sample(None))[0][3])

    def test_failed_receipt_has_no_location_table(self):
        self.assertEqual(location_tables([{'state': 'failed'}]), [])

    def test_added_location_not_dropped(self):
        a, b = sample(), sample()
        b['summary']['locations'][0]['name'] = 'new'
        rows = change_rows(a, b)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r[3] is None for r in rows))

    def test_actual_reception_not_attempt(self):
        s = sample()
        self.assertIn('unknown', received(s))
        s['transport'] = {'retrieved_at': (LAST + timedelta(seconds=40)).isoformat()}
        self.assertEqual(received(s), s['transport']['retrieved_at'])

    def test_close_only_after_terminal_final_or_grace(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            self.assertFalse(can_close(folder, LAST + timedelta(minutes=4)))
            self.assertTrue(can_close(folder, LAST + GRACE + timedelta(seconds=1)))
            publish(folder / ('sample-' + name(LAST) + '.json'), sample())
            self.assertTrue(can_close(folder, LAST + timedelta(minutes=4)))
            self.assertFalse(can_close(folder, LAST - timedelta(seconds=1)))

    def test_unfinished_final_claim_stays_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            publish(folder / ('claim-' + name(LAST) + '.json'), {'claimed_at': LAST.isoformat()})
            self.assertFalse(can_close(folder, LAST + timedelta(minutes=4)))

    def test_publish_does_not_replace_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / 'IZVESTAJ.md'
            publish_report(target, 'original')
            with self.assertRaises(FileExistsError):
                publish_report(target, 'replacement')
            self.assertEqual(target.read_text(), 'original')
            self.assertEqual(len(list(pathlib.Path(tmp).iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
