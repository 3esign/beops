"""Official programme facts, clocks, routing and independent source freshness."""
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from event_repertoires import SOURCES, explicit_clock, parse_official_programme
import collect_events

AT = '2026-09-27T08:00:00+00:00'
NOW = datetime.fromisoformat(AT)
DOM = SOURCES[1]
KCB = SOURCES[2]


def dom_card(clock='Ponedeljak, 28. septembar 2026. u 19.00', venue='DOB//Tribinska sala',
             url='https://domomladine.org/debate/program/', title='Tribina &amp; razgovor'):
    return f'<div class="ev-data"><h3 class="ev-title entry-title"><a href="{url}"><span class="main-title">{title}</span><span class="cir-title">Drugi jezik</span></a></h3><p class="ev-date">{clock}</p><p class="ev-loc">{venue}</p></div>'


def kcb_card(clock='28.09.2026, 20:00.', venue='Galerija ARTGET', url='https://www.kcb.org.rs/2026/09/program/'):
    return f'<div class="events"><ul><li><div class="text-content"><a href="{url}"><h4>Koncert</h4></a><div class="extra"><div class="date">{clock}</div><div class="location"><ul><li><a href="https://www.kcb.org.rs/premises_cat/galerija-artget/">{venue}</a></li></ul></div></div></div></li></ul></div>'


def parsed(html, source=DOM):
    return parse_official_programme(html.encode('utf8'), source, AT, 'a' * 64)


class OfficialProgrammes(unittest.TestCase):
    def test_dom_explicit_local_clock_and_verbatim_venue(self):
        event = parsed(dom_card())['events'][0]
        self.assertEqual(event['event_start'], '2026-09-28T17:00:00Z')
        self.assertEqual(event['event_start_local'], '2026-09-28T19:00+02:00')
        self.assertEqual(event['title'], 'Tribina & razgovor')
        self.assertEqual(event['location'], 'DOB//Tribinska sala')
        self.assertEqual(event['venue_id'], 'dom-omladine')
        self.assertIsNone(event['event_end'])
        self.assertIsNone(event['published'])
        self.assertEqual(event['provenance']['raw_sha256'], 'a' * 64)

    def test_kcb_nested_venue_and_winter_offset(self):
        event = parsed(kcb_card('28.11.2026, 20:30.'), KCB)['events'][0]
        self.assertEqual(event['event_start'], '2026-11-28T19:30:00Z')
        self.assertEqual(event['location'], 'Galerija ARTGET')
        self.assertEqual(event['venue_id'], 'kcb-artget')

    def test_source_weekday_conflict_is_rejected_not_silently_fixed(self):
        result = parsed(dom_card('Utorak, 29. oktobar 2026. u 20.00'))
        self.assertEqual(result['events'], [])
        self.assertEqual(result['rejected'][0]['reason'], 'source_weekday_date_conflict')

    def test_ranges_dates_without_times_and_invalid_dates_remain_unlocated_in_time(self):
        for clock in ('Od 21. do 24. oktobar 2026.', '28. septembar 2026.',
                      '31. septembar 2026. u 19.00', '28. septembar u 19.00',
                      '28. septembar 2026. od 19.00 do 20.00'):
            self.assertEqual(parsed(dom_card(clock))['events'], [], clock)
        for clock in ('03.09.2026-11.10, 12:00-20:00.', '28.09.2026', '31.09.2026, 20:00.'):
            self.assertEqual(parsed(kcb_card(clock), KCB)['events'], [], clock)

    def test_dst_fold_and_gap_are_rejected(self):
        for sid, clock in (('S226', 'Nedelja, 25. oktobar 2026. u 02.30'),
                           ('S226', 'Nedelja, 29. mart 2026. u 02.30'),
                           ('S227', '25.10.2026, 02:30.'), ('S227', '29.03.2026, 02:30.')):
            self.assertIsNone(explicit_clock(clock, sid)[0])

    def test_official_publisher_does_not_locate_external_venue(self):
        event = parsed(dom_card(venue='Plato ispred paviljona na Kalemegdanu'))['events'][0]
        self.assertIsNone(event['venue_id'])
        event = parsed(kcb_card(venue='Druga galerija'), KCB)['events'][0]
        self.assertIsNone(event['venue_id'])

    def test_unsafe_foreign_and_non_event_routes_are_excluded(self):
        for url in ('javascript:alert(1)', 'https://foreign.example/program/',
                    'https://domomladine.org.evil.example/debate/program/',
                    'https://domomladine.org/debate/', 'https://domomladine.org/debate/program/#x',
                    'https://domomladine.org:443/debate/program/'):
            self.assertEqual(parsed(dom_card(url=url))['events'], [], url)
        self.assertEqual(parsed(kcb_card(url='https://www.kcb.org.rs/premises/galerija/'), KCB)['events'], [])

    def test_missing_title_or_venue_are_not_invented(self):
        self.assertEqual(parsed(dom_card(title=''))['events'], [])
        self.assertEqual(parsed(dom_card(venue=''))['events'], [])

    def test_duplicate_cards_do_not_duplicate_occurrences(self):
        self.assertEqual(len(parsed(dom_card() * 2)['events']), 1)
        self.assertEqual(len(parsed(dom_card() + dom_card('Utorak, 29. septembar 2026. u 19.00'))['events']), 2)

    def test_unstructured_and_script_text_are_not_schedule_cards(self):
        self.assertEqual(parsed('<script>' + dom_card() + '</script>')['events'], [])
        self.assertEqual(parsed(kcb_card().replace('class="events"', 'class="slide"'), KCB)['events'], [])


class IndependentSourceCache(unittest.TestCase):
    def cache(self, sid='S226'):
        event = parsed(dom_card())['events'][0]
        return {'source_id': sid, 'state': 'available', 'attempted_at': AT,
                'received_at': AT, 'events': [{**event, 'source_id': sid}]}

    def test_failed_stale_future_sources_cannot_borrow_healthy_receipt(self):
        healthy = self.cache()
        for change in ({'state': 'unavailable'}, {'received_at': '2026-09-25T08:00:00Z'},
                       {'received_at': '2026-09-28T08:00:00Z'}):
            other = {**self.cache('S227'), **change}
            result = collect_events.scheduled_events({'state': 'partial', 'received_at': AT,
                                                     'sources': [healthy, other]}, NOW)
            self.assertEqual([e['source_id'] for e in result], ['S226'])

    def test_legacy_cache_migration_keeps_receipt_age(self):
        old = {**self.cache('S225'), 'received_at': '2026-09-25T08:00:00Z'}
        self.assertEqual(collect_events.source_caches(old), [old])
        self.assertEqual(collect_events.scheduled_events(old, NOW), [])

    def test_public_health_cannot_say_available_for_stale_or_future_receipts(self):
        for receipt in ('2026-09-25T08:00:00Z', '2026-09-28T08:00:00Z', None):
            source = {**self.cache(), 'received_at': receipt}
            summary = collect_events.public_source_status(source, NOW)
            self.assertEqual(summary['state'], 'unavailable')
            self.assertEqual(summary['collection_state'], 'available')
            self.assertEqual(summary['scheduled_count'], 0)
            self.assertEqual(summary['received_at'], receipt)
            self.assertEqual(source['state'], 'available')
            self.assertTrue(summary['error'])

    def test_healthy_cache_avoids_network_and_failure_retries_after_half_hour(self):
        import transport
        with patch.object(transport, 'fetch') as fetch:
            healthy = self.cache()
            self.assertEqual(collect_events.refresh_source(DOM, healthy, NOW), healthy)
            failed = {**healthy, 'state': 'unavailable'}
            self.assertEqual(collect_events.refresh_source(DOM, failed, NOW + timedelta(minutes=29)), failed)
            fetch.assert_not_called()

    def test_no_permission_never_fetches_or_refreshes_old_receipt(self):
        import transport, permission_policy
        old = {**self.cache(), 'attempted_at': '2026-09-25T08:00:00Z'}
        with patch.object(permission_policy, 'latest', return_value={}), \
             patch.object(permission_policy, 'authorize', return_value=(False, 'no permission capture')), \
             patch.object(transport, 'fetch') as fetch:
            result = collect_events.refresh_source(DOM, old, NOW)
            self.assertEqual(result['state'], 'unavailable')
            self.assertEqual(result['received_at'], old['received_at'])
            self.assertEqual(collect_events.scheduled_events(result, NOW), [])
            fetch.assert_not_called()

    def test_calendar_sources_have_captured_permission_and_registry_entries(self):
        import permission_policy
        registry = json.loads((ROOT / 'research/SOURCE_REGISTRY.json').read_text(encoding='utf8'))
        by_sid = {source['id']: source for source in registry['sources']}
        entries = permission_policy.latest(ROOT / 'research/08-provenance/LEDGER.jsonl')
        for source in SOURCES:
            sid = source['source_id']
            self.assertIn(sid, by_sid)
            self.assertNotIn(by_sid[sid]['status'], ('opted_out', 'needs_decision', 'restricted', 'blocked'))
            self.assertIn(sid, entries)
            self.assertTrue(permission_policy.access_state(entries[sid])[0], sid)


if __name__ == '__main__':
    unittest.main(verbosity=2)
