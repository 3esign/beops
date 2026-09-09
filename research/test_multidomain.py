import unittest
import json
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from probe_multidomain import parking_get, page_summary, prices_summary, river_summary


class MultiDomainTests(unittest.TestCase):
    def test_windows_status_survives_transport_boundary(self):
        for code in (403, 429, 503):
            response = {'url': 'https://example.org', 'status': code, 'error': 'Request failed'}
            with self.subTest(code=code), patch('probe_multidomain.subprocess.run', return_value=SimpleNamespace(stdout=json.dumps(response).encode())):
                with self.assertRaises(HTTPError) as caught:
                    parking_get()
                self.assertEqual(caught.exception.code, code)

    def test_windows_tls_failure_never_becomes_data(self):
        response = {'status': None, 'error': 'Verified-TLS public request failed'}
        with patch('probe_multidomain.subprocess.run', return_value=SimpleNamespace(stdout=json.dumps(response).encode())):
            with self.assertRaises(OSError):
                parking_get()

    def test_parking_zero_is_not_missing(self):
        html = '<ul class="parking-count"><li><a href="https://example.org">A &amp; B</a><span class="count no-space">0</span></li></ul>'
        result = page_summary(html, 'https://example.org', 'parking')['locations'][0]
        self.assertEqual(result['free_spaces'], 0)
        self.assertEqual(result['name'], 'A & B')
        self.assertIsNone(result['observed_at'])

    def test_parking_unknown_is_not_zero(self):
        html = '<ul class="parking-count"><li><a>A</a><span class="count">--</span></li></ul>'
        self.assertIsNone(page_summary(html, '', 'parking')['locations'][0]['free_spaces'])

    def test_missing_parking_list_fails(self):
        with self.assertRaises(ValueError):
            page_summary('<html>maintenance</html>', '', 'parking')

    def test_river_fixed_offset_in_summer(self):
        html = 'UTC+1<table><tr><td>05.09.2026 03:00</td><td>-12</td></tr></table>'
        row = river_summary(html)['latest']
        self.assertEqual(row['observed_at'], '2026-09-05T02:00:00+00:00')
        self.assertEqual(row['level_cm'], -12)

    def test_river_missing_value_not_zero(self):
        result = river_summary('UTC+1<table><tr><td>05.09.2026 03:00</td><td>--</td></tr></table>')
        self.assertIsNone(result['latest'])
        self.assertEqual(result['rejected_values'], 1)

    def test_river_refuses_unknown_clock(self):
        with self.assertRaises(ValueError):
            river_summary('<table></table>')

    def test_prices_preserve_identifiers_and_missing(self):
        result = prices_summary(b'Ident;Redovna cena\n001;1,679.99\n;10.00\n')
        self.assertEqual(result['rows'], 2)
        self.assertEqual(result['distinct_product_ids'], 1)
        self.assertEqual(result['missing_id_rows'], 1)

    def test_price_snapshot_is_not_live(self):
        result = prices_summary(b'Barkod proizvoda;Redovna cena;Datum cenovnika;VRSTA_CENOVNIKA\n001;1;01-09-2026;MESECNI_PRESEK\n')
        self.assertEqual(result['price_list_types'], {'MESECNI_PRESEK': 1})
        self.assertNotIn('fresh', result)

    def test_bad_price_schema_rejected(self):
        with self.assertRaises(ValueError):
            prices_summary(b'<html>Error</html>')

    def test_ragged_price_rows_rejected(self):
        with self.assertRaises(ValueError):
            prices_summary(b'Ident;Redovna cena\n1;20;extra\n')


if __name__ == '__main__':
    unittest.main()
