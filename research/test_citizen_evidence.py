"""Citizen summaries must not turn old data or headline labels into current advice."""
import pathlib
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
from build_public_page import recent_air, safe_url, render_events
from collect_events import extract_events_from_headlines, parse_repertoire, scheduled_events


class CitizenEvidence(unittest.TestCase):
    def repertoire(self, label):
        html = f'<h3 class="entry-title"><a href="https://www.kolarac.rs/koncerti/test/">{label}</a></h3>'
        return parse_repertoire(html.encode(), '2026-09-26T12:00:00Z', 'a' * 64)

    def test_official_schedule_uses_explicit_clock_venue_and_provenance(self):
        ev = self.repertoire('Концерт<br/>11. 10. 2026. у 16<br/>Велика дворана')[0]
        self.assertEqual(ev['event_start'], '2026-10-11T14:00:00Z')
        self.assertEqual(ev['event_start_local'], '2026-10-11T16:00+02:00')
        self.assertEqual(ev['location'], 'Велика дворана')
        self.assertEqual(ev['title'], 'Концерт')
        self.assertEqual(ev['state'], 'forecast')
        self.assertEqual(ev['event_status'], 'scheduled')
        self.assertIsNone(ev['event_end'])
        self.assertIsNone(ev['zone'])
        self.assertIn('11. 10. 2026.', ev['provenance']['source_label'])
        self.assertEqual(self.repertoire('Концерт 28. 11. 2026. у 20:30')[0]['event_start'], '2026-11-28T19:30:00Z')

    def test_missing_or_invalid_clock_and_title_cannot_become_a_calendar_fact(self):
        for label in ('Концерт у суботу', 'Концерт 31. 2. 2026. у 20', '11. 10. 2026. у 16',
                      'Концерт 25. 10. 2026. у 2:30', 'Концерт 29. 3. 2026. у 2:30'):
            self.assertEqual(self.repertoire(label), [], label)

    def test_old_failed_or_future_received_cache_and_past_starts_are_not_upcoming(self):
        event = self.repertoire('Концерт 11. 10. 2026. у 16')[0]
        now = datetime(2026, 9, 26, 13, tzinfo=timezone.utc)
        cache = {'state': 'available', 'received_at': '2026-09-26T12:00:00Z', 'events': [event]}
        self.assertEqual(len(scheduled_events(cache, now)), 1)
        for change in ({'state': 'unavailable'}, {'received_at': '2026-09-24T12:00:00Z'},
                       {'received_at': '2026-09-27T12:00:00Z'}):
            self.assertEqual(scheduled_events({**cache, **change}, now), [])
        self.assertEqual(scheduled_events({**cache, 'events': [{**event, 'event_start': '2026-09-25T12:00:00Z'}]}, now), [])

    def test_calendar_and_unverified_headline_are_visibly_separate(self):
        event = self.repertoire('Концерт 11. 10. 2026. у 16')[0]
        signal = extract_events_from_headlines({'rows': [{'title': 'Radovi na mostu', 'sid': 'S208'}]})[0]
        html = render_events({'events': [signal, event], 'repertoire': {'received_at': '2026-09-26T12:00:00Z'}})
        self.assertIn('11.10.2026. u 16:00', html)
        self.assertLess(html.index('Концерт'), html.index('Signali iz naslova'))
        self.assertGreater(html.index('Radovi na mostu'), html.index('Signali iz naslova'))
        self.assertIn('Jedan zvanični repertoar', html)
        self.assertIn('Nema budućih termina', render_events({}))

    def test_one_latest_timed_point_per_station_and_parameter(self):
        stream = {'station': 'A', 'parameter': 'PM2.5', 'unit': 'µg.m-3', 'points': [
            {'t': '2026-09-26T10:00:00Z', 'v': 10},
            {'t': '2026-09-26T11:00:00Z', 'v': 20},
            {'t': '2026-09-25T10:00:00Z', 'v': 900},
            {'t': '2026-09-26T11:30:00Z', 'v': 500, 'tu': True},
            {'t': '2026-09-26T13:00:00Z', 'v': 800},
        ]}
        snapshot = {'as_of': '2026-09-26T12:00:00Z', 'sources': [{'sid': 'S146', 'datastreams': [stream]}]}
        result = recent_air(snapshot)
        self.assertEqual(len(result), 1)
        self.assertEqual(next(iter(result.values()))[1], 20)
        stream['points'] = [{'t': '2026-09-26T13:00:00Z', 'tc': '2026-09-26T11:00:00Z', 'v': 15}]
        self.assertEqual(next(iter(recent_air(snapshot).values()))[1], 15)
        stream['state'] = 'estimated'
        self.assertEqual(recent_air(snapshot), {})

    def test_headline_does_not_establish_event_time_or_verification(self):
        result = extract_events_from_headlines({'rows': [{'title': 'Koncert u subotu', 'sid': 'S208', 'published': '2026-09-26'}]})
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]['verified'])
        self.assertIsNone(result[0]['event_start'])
        self.assertIsNone(result[0]['zone'])

    def test_compact_snapshot_defaults_keep_measurement_time_and_flags(self):
        source = {'sid': 'S146', 'point_defaults': {'t': '2026-09-26T11:00:00Z'},
                  'datastreams': [{'station': 'A', 'parameter': 'PM2.5', 'unit': 'µg.m-3', 'points': [{'v': 0}]}]}
        snapshot = {'as_of': '2026-09-26T12:00:00Z', 'sources': [source]}
        self.assertEqual(next(iter(recent_air(snapshot).values()))[1], 0)
        source['point_defaults']['tu'] = True
        self.assertEqual(recent_air(snapshot), {})
        source['datastreams'][0]['points'][0]['tu'] = False
        self.assertEqual(len(recent_air(snapshot)), 1)

    def test_source_url_cannot_execute_script_or_break_an_attribute(self):
        self.assertEqual(safe_url('javascript:alert(1)'), 'instrument.html')
        self.assertNotIn('"', safe_url('https://example.org/" onclick="x'))


if __name__ == '__main__':
    unittest.main()
