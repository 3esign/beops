"""A media topic and a publisher's city do not establish event/instrument overlap."""
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'research'))
import build_public_page as page
import headline_geo
import organ_mind as mind
from test_organ_mind import snapshot, NOW, REG

AT = '2026-09-26T12:00:00Z'


def row(title, **extra):
    return {'title': title, 'source': 'Belgrade newsroom', 'link': 'https://example.org/news',
            'published': '2026-09-26T11:00:00Z', 'received': '2026-09-26T11:15:00Z', **extra}


def location(scope='belgrade', name='Beograd', status='estimated'):
    return {'scope': scope, 'status': status, 'estimate':
            {'name': name, 'radius_m': 20000, 'lat': 44.81, 'lon': 20.46}
            if status == 'estimated' else None, 'candidates': []}


class HeadlineGeography(unittest.TestCase):
    def test_real_shared_resolver_keeps_national_foreign_and_ambiguous_out(self):
        titles = ['Zagađen vazduh u Beogradu', 'Zagađen vazduh u Srbiji',
                  'Smog u Sarajevu', 'Smog na Paliluli', 'Smog je opasan']
        local, excluded = page.headline_air_context([row(t) for t in titles], AT)
        self.assertEqual([r['row']['title'] for r in local], titles[:1])
        self.assertEqual(len(excluded), 4)

    def test_unscoped_headlines_never_receive_local_measurement_beside_them(self):
        titles = [row('Kvalitet vazduha u Srbiji'), row('Smog u Sarajevu'), row('Smog na Paliluli')]
        values = [location('serbia'), location('outside'), location('unknown', status='ambiguous')]
        with patch('build_public_page.locate_headlines', return_value=values):
            html = page.render_air_context(titles, AT, 'TEST MEASURE 123')
        self.assertNotIn('TEST MEASURE 123', html)
        self.assertIn('3 izdvojeno', html)
        self.assertIn('više mogućih lokacija', html)
        for item in titles:
            self.assertIn(item['title'], html)
        self.assertIn('href="https://example.org/news"', html)

    def test_local_estimate_is_context_and_does_not_claim_confirmation(self):
        with patch('build_public_page.locate_headlines', return_value=[location()]):
            html = page.render_air_context([row('Smog u Beogradu')], AT, 'TEST MEASURE 123')
        self.assertIn('TEST MEASURE 123', html)
        self.assertIn('poluprečnik 20 km', html)
        self.assertIn('merenje ne potvrđuje niti opovrgava naslov', html)
        self.assertIn('vreme objave nije vreme događaja', html)

    def test_old_publication_cannot_become_current_from_new_receipt(self):
        titles = [row('Smog u Beogradu', published='2026-09-20T11:00:00Z'),
                  row('Smog u Zemunu', published=None, received='2026-09-26T11:00:00Z'),
                  row('Smog u Beogradu', published='bad'),
                  row('Smog u Beogradu', received='2026-09-27T11:00:00Z')]
        with patch('build_public_page.locate_headlines', return_value=[location() for _ in titles]):
            local, excluded = page.headline_air_context(titles, AT)
        self.assertEqual([item['row']['title'] for item in local], ['Smog u Zemunu'])
        self.assertEqual(len(excluded), 3)

    def test_water_pollution_and_kosmogenit_are_not_air_quality(self):
        titles = [row('Ministarstvo demantovalo navode o zagađenju Velikog Rzava: Voda je potpuno bistra'),
                  row('Kosmogenit u Beogradu'), row('Zagađenje vode u Beogradu'),
                  row('NADLEŽNI OBJAŠNjAVAJU: Kakav je kvalitet vazduha u Beogradu i u kom slučaju je potreban oprez')]
        with patch('build_public_page.locate_headlines', side_effect=lambda rs: [location() for _ in rs]):
            local, excluded = page.headline_air_context(titles, AT)
        self.assertEqual([item['row']['title'] for item in local], [titles[-1]['title']])
        self.assertEqual(excluded, [])

    def test_unavailable_resolver_stays_unknown_and_does_not_use_publisher(self):
        headline_geo._locate_titles.cache_clear()
        with patch('headline_geo.subprocess.run', side_effect=OSError('no node')):
            result = headline_geo.locate_headlines([row('Nepoznat događaj 782')])[0]
        self.assertEqual(result['scope'], 'unknown')
        self.assertFalse(headline_geo.local_estimate(result))
        headline_geo._locate_titles.cache_clear()

    def test_mind_rejects_model_zone_when_title_is_nonlocal_or_ambiguous(self):
        for geo in [location('serbia'), location('outside'), location('unknown', status='ambiguous'), location(name='Beograd')]:
            with patch('organ_mind.locate_headlines', return_value=[geo]), patch('organ_mind.register', return_value=REG):
                digest = mind.digest(snapshot(), now=NOW, context={})
            self.assertFalse(any(f.get('zone') == 'Zemun' for f in digest['facts']), geo)

    def test_mind_local_name_match_discloses_unverified_event_time(self):
        with patch('organ_mind.locate_headlines', return_value=[location(name='Zemun')]), patch('organ_mind.register', return_value=REG):
            digest = mind.digest(snapshot(), now=NOW, context={})
        facts = [f for f in digest['facts'] if f.get('zone') == 'Zemun']
        self.assertEqual(len(facts), 1)
        self.assertIn('not correlation or causation', facts[0]['en'])


if __name__ == '__main__':
    unittest.main()
