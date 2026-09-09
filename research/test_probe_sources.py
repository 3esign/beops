"""Offline checks for the research probe. No network or runtime writes."""
import io
import json
import unittest
import zipfile
from probe_sources import Tables, gtfs_summary, summarize


class ProbeTests(unittest.TestCase):
    def test_tables_entities_and_nested_markup(self):
        p = Tables()
        p.feed('<table><tr><td>Beograd</td><td><b>23.9</b></td><td>A &amp; B</td></tr></table>')
        self.assertEqual(p.rows, [['Beograd', '23.9', 'A & B']])

    def test_sensor_ids_not_record_count(self):
        row = {"sensor": {"id": 1}, "timestamp": "2026-09-05 01:00:00",
               "sensordatavalues": [{"value_type": "temperature", "value": "23"}]}
        out = summarize('sensor', json.dumps([row, row]).encode(), 'utf-8')
        self.assertEqual(out['unique_sensor_count'], 1)
        self.assertEqual(out['record_count'], 2)

    def test_sensor_wrong_schema_rejected(self):
        with self.assertRaises(ValueError):
            summarize('sensor', b'{}', 'utf-8')

    def test_empty_event_feed_is_valid(self):
        self.assertEqual(summarize('earthquake', b'', 'utf-8')['count'], 0)

    def test_empty_metar_no_invented_value(self):
        self.assertEqual(summarize('metar', b'[]', 'utf-8')['observations'], [])

    def test_missing_station_value_is_preserved(self):
        data = '<table><tr><td>Beograd</td><td>////</td></tr></table>'.encode()
        self.assertEqual(summarize('rhmz', data, 'utf-8')['selected_rows'][0][1], '////')

    def test_gtfs_dates_and_counts(self):
        b = io.BytesIO()
        with zipfile.ZipFile(b, 'w') as z:
            z.writestr('calendar.txt', 'service_id,start_date,end_date\nA,20200101,20291231\n')
            z.writestr('stops.txt', 'stop_id,stop_name\n1,Test\n2,Test2\n')
        out = gtfs_summary(b.getvalue())
        self.assertEqual(out['stops.txt']['count'], 2)
        self.assertEqual(out['calendar.txt']['end_date']['max'], '20291231')

    def test_notice_date_is_not_freshness_verdict(self):
        out = summarize('notice', b'<p>2020-01-01</p>', 'utf-8')
        self.assertEqual(out['date_tokens'], ['2020-01-01'])
        self.assertNotIn('fresh', out)


if __name__ == '__main__':
    unittest.main()
