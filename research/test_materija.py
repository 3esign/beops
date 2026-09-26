"""Unverified material stubs must never become observed public points."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class MaterijaContract(unittest.TestCase):
    def test_material_layer_is_explicitly_unavailable(self):
        data = json.loads((ROOT / 'public' / 'materija.json').read_text(encoding='utf-8'))
        self.assertEqual(data['schema'], 'beops-material-layer/v1')
        self.assertEqual(data['state'], 'unavailable')
        self.assertEqual(data['records'], [])
        self.assertIn('S195', data['reason'])
        self.assertIn('RTS', data['reason'])
        self.assertGreaterEqual(len(data['required_before_publication']), 4)


if __name__ == '__main__':
    unittest.main()
