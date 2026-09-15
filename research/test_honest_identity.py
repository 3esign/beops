"""C-069: every request BEOPS sends to a source names the observatory; no browser persona."""
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import collect_daemon as cd

TOKEN = 'Beops-Research-Collect/1.0'


class HonestIdentity(unittest.TestCase):
    def test_the_transport_names_the_observatory(self):
        p = subprocess.run(['node', str(ROOT / 'tools' / 'net_fetch.js')],
                           input=json.dumps({'url': 'https://example.org/feed', 'headers_only': True}),
                           capture_output=True, text=True, encoding='utf-8', timeout=30, check=True)
        ua = json.loads(p.stdout)['user_agent']
        self.assertTrue(ua.startswith(TOKEN), ua)
        self.assertNotIn('Mozilla', ua)

    def test_no_source_transport_borrows_a_persona(self):
        for rel in ('tools/net_fetch.js', 'src/store.js'):
            text = (ROOT / rel).read_text(encoding='utf-8').lower()
            self.assertNotIn('incognito.js', text, rel)
            self.assertIn(TOKEN.lower(), text, rel)

    def test_the_daemon_label_and_the_sent_identity_agree(self):
        self.assertTrue(cd.UA.startswith(TOKEN))

    def test_a_receipt_records_the_identity_that_was_sent(self):
        src = (ROOT / 'tools' / 'collect_daemon.py').read_text(encoding='utf-8')
        self.assertIn('item["request_user_agent"] = res.get("request_user_agent")', src)


if __name__ == '__main__':
    unittest.main()
