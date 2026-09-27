"""Citizen summaries must not turn old data or headline labels into current advice."""
import pathlib
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
from build_public_page import recent_air, safe_url, render_events, format_citizen_page
from collect_events import extract_events_from_headlines, parse_repertoire, scheduled_events


class CitizenEvidence(unittest.TestCase):
    def citizen_page(self, snapshot=None, events=None, headlines=None):
        inputs = {'city-overview.json': {'snapshot': snapshot or {}},
                  'events.json': {'events': events or []},
                  'headlines.json': {'rows': headlines or []}}
        with patch('build_public_page.read_json', side_effect=lambda path, default=None: inputs.get(path.name, default)):
            return format_citizen_page()

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
        self.assertIn('Svaki izvor ima zasebnu svežinu', html)
        self.assertIn('Nema budućih termina', render_events({}))

    def test_each_calendar_source_discloses_its_own_state_and_receipt(self):
        html = render_events({'events': [], 'repertoire': {'sources': [
            {'source_id': 'S225', 'name': 'Kolarac', 'url': 'https://www.kolarac.rs/',
             'state': 'available', 'received_at': '2026-09-27T07:00:00Z'},
            {'source_id': 'S226', 'name': '<Untrusted>', 'url': 'javascript:alert(1)',
             'state': 'unavailable', 'received_at': '2026-09-26T01:00:00Z'}]}})
        self.assertIn('program pročitan', html)
        self.assertIn('trenutno nedostupan', html)
        self.assertIn('2026-09-26T01:00:00Z', html)
        self.assertIn('&lt;Untrusted&gt;', html)
        self.assertNotIn('javascript:', html)

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

    def test_traffic_card_links_to_every_counted_notice_even_after_general_list_limit(self):
        events = [{'title': f'Radovi {n}', 'category': 'saobracaj_radovi', 'state': 'untimed',
                   'verified': False, 'source': 'Gradske najave', 'published': f'2026-09-{n + 10:02d}',
                   'url': f'https://example.org/radovi/{n}'} for n in range(8)]
        html = self.citizen_page(events=events)
        card = html.split('<div class="action-name">Kretanje kroz grad</div>', 1)[1].split('</div>\n        </div>', 1)[0]
        self.assertIn('8 naslova', card)
        self.assertIn('href="#saobracaj-dokazi"', card)
        proof = html.split('id="saobracaj-dokazi"', 1)[1].split('</section>', 1)[0]
        self.assertEqual(proof.count('<li>'), 8)
        for event in events:
            self.assertIn(f'href="{event["url"]}"', proof)
            self.assertIn(f'Objava: {event["published"]}', proof)
        self.assertIn('datum objave nije datum događaja', proof)
        self.assertIn('Prijem: nije poznat', proof)

    def test_comparison_preserves_original_url_publication_and_reception(self):
        headline = {'title': 'Kvalitet vazduha <provera>', 'source': 'Primer & izvor',
                    'link': 'https://example.org/vest?x=1&y=2', 'published': '2026-09-20T10:00:00Z',
                    'received': '2026-09-26T11:00:00Z'}
        html = self.citizen_page(headlines=[headline])
        comparison = html.split('<!-- BLOK 4:', 1)[1].split('id="pm25-dokazi"', 1)[0]
        self.assertIn('href="https://example.org/vest?x=1&amp;y=2"', comparison)
        self.assertIn('Kvalitet vazduha &lt;provera&gt;', comparison)
        self.assertIn('Primer &amp; izvor', comparison)
        self.assertIn('Objava: 2026-09-20T10:00:00Z', comparison)
        self.assertIn('Prijem: 2026-09-26T11:00:00Z', comparison)
        self.assertIn('vreme objave nije vreme događaja', comparison)
        self.assertIn('href="#pm25-dokazi"', comparison)
        self.assertNotIn('href="obrasci.html"', comparison)

    def test_pm_proof_is_exact_membership_of_displayed_average_with_inherited_clocks(self):
        source = {'sid': 'S146', 'name': 'Merna mreža',
                  'point_defaults': {'t': '2026-09-26T11:00:00Z', 'rx': '2026-09-26T11:30:00Z', 'q': 'preliminary'},
                  'datastreams': [
                      {'station': 'A', 'datastream': 'a|PM2.5', 'parameter': 'PM2.5', 'unit': 'ug.m-3',
                       'points': [{'t': '2026-09-26T10:00:00Z', 'v': 100}, {'v': 10}]},
                      {'station': 'B', 'datastream': 'b|PM2.5', 'parameter': 'PM2.5', 'unit': 'µg/m³',
                       'points': [{'t': '2026-09-26T13:00:00Z', 'tc': '2026-09-26T11:15:00Z', 'v': 30}]},
                      {'station': 'OLD', 'parameter': 'PM2.5', 'unit': 'ug.m-3',
                       'points': [{'t': '2026-09-25T11:00:00Z', 'v': 800}]},
                      {'station': 'UNTIMED', 'parameter': 'PM2.5', 'unit': 'ug.m-3',
                       'points': [{'v': 900, 'tu': True}]},
                      {'station': 'OTHER', 'parameter': 'PM10', 'unit': 'ug.m-3', 'points': [{'v': 50}]}]}
        html = self.citizen_page(snapshot={'as_of': '2026-09-26T12:00:00Z', 'sources': [source]})
        self.assertIn('prosek 20.0 µg/m³ iz 2 serije', html)
        proof = html.split('id="pm25-dokazi"', 1)[1].split('</section>', 1)[0]
        self.assertEqual(proof.count('<li>'), 2)
        for text in ('A: 10 µg/m³', 'B: 30 µg/m³', 'S146', 'a|PM2.5', 'b|PM2.5',
                     'Vreme merenja: 2026-09-26T11:00:00Z', 'Korigovano vreme merenja: 2026-09-26T11:15:00Z',
                     'Izvorno vreme: 2026-09-26T13:00:00Z', 'Prijem: 2026-09-26T11:30:00Z', 'preliminary'):
            self.assertIn(text, proof)
        for text in ('OLD', 'UNTIMED', 'OTHER', '100 µg/m³', '800 µg/m³', '900 µg/m³'):
            self.assertNotIn(text, proof)

    def test_empty_proofs_and_unknown_publication_do_not_invent_availability_or_dates(self):
        html = self.citizen_page(headlines=[{'title': 'Smog u gradu', 'received': '2026-09-26T11:00:00Z'}])
        self.assertIn('Nema upotrebljivih PM2.5 vrednosti', html)
        self.assertIn('prosek nije izračunat', html)
        self.assertIn('To nije potvrda da radova ili zastoja nema', html)
        self.assertIn('Objava: nije poznata · Prijem: 2026-09-26T11:00:00Z', html)


if __name__ == '__main__':
    unittest.main()
