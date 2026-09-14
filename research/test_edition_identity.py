"""An execution clock cannot manufacture a new dataset content edition."""
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import export_permission_dataset as E


class EditionIdentity(unittest.TestCase):
    def test_same_inputs_on_different_days_have_same_edition_and_immutable_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);reg=root/'registry.json';ledger=root/'ledger.jsonl'
            reg.write_text(json.dumps({'sources':[]}));ledger.write_text('')
            with patch.object(E,'ROOT',root),patch.object(E,'OUT',root/'dataset'),patch.object(E,'REG',reg),patch.object(E,'LEDGER',ledger),patch.object(E,'COLLECTORS',root/'absent.json'):
                with patch.object(E,'datetime') as clock:
                    clock.now.return_value=datetime(2026,9,14,tzinfo=timezone.utc)
                    first=E.build()
                    edition=root/'dataset/releases'/first['edition_id']
                    original={p.name:p.read_bytes() for p in edition.iterdir()}
                    clock.now.return_value=datetime(2026,9,20,tzinfo=timezone.utc)
                    second=E.build()
                self.assertEqual(first['edition_id'],second['edition_id'])
                self.assertNotEqual(first['generated_at'],second['generated_at'])
                self.assertEqual(original,{p.name:p.read_bytes() for p in edition.iterdir()})
                self.assertEqual(len(list((root/'dataset/releases').iterdir())),1)


if __name__=='__main__':unittest.main()
