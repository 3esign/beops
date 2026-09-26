"""Current workspace rule: shared incognito boundary, actual sent persona in receipts."""
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import collect_daemon as cd

FORBIDDEN = ('beops', 'svemir', 'poturak', 'scumutator', '3esign', '@gmail', 'mailto:')


class HonestIdentity(unittest.TestCase):
    def test_the_transport_uses_a_persona_without_a_personal_signature(self):
        p = subprocess.run(['node', str(ROOT / 'tools' / 'net_fetch.js')],
                           input=json.dumps({'url': 'https://example.org/feed', 'headers_only': True}),
                           capture_output=True, text=True, encoding='utf-8', timeout=30, check=True)
        result = json.loads(p.stdout)
        self.assertTrue(result['user_agent'])
        rendered = json.dumps(result['headers']).lower()
        for forbidden in FORBIDDEN:
            self.assertNotIn(forbidden, rendered)
        self.assertNotIn('from', {k.lower() for k in result['headers']})

    def test_both_source_transports_use_the_same_header_boundary(self):
        for rel in ('tools/net_fetch.js', 'src/store.js'):
            text = (ROOT / rel).read_text(encoding='utf-8').lower()
            self.assertIn('network_identity', text, rel)
            self.assertNotIn('poturak', text, rel)
        self.assertIn('incognito.js', (ROOT / 'tools/network_identity.js').read_text(encoding='utf-8'))

    def test_daemon_records_actual_sent_identity_instead_of_a_fixed_label(self):
        self.assertIn('request_user_agent', (ROOT / 'tools/collect_daemon.py').read_text(encoding='utf-8'))

    def test_a_receipt_records_the_identity_that_was_sent(self):
        src = (ROOT / 'tools' / 'collect_daemon.py').read_text(encoding='utf-8')
        self.assertIn('item["request_user_agent"] = res.get("request_user_agent")', src)

    def test_a_network_failure_names_its_cause(self):
        """C-083: 'fetch failed' alone hid why S201 failed three hours in a row."""
        import socket
        s = socket.socket()
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        s.close()                      # nothing listens there now: the connection is refused
        p = subprocess.run(['node', str(ROOT / 'tools' / 'net_fetch.js')],
                           input=json.dumps({'url': f'http://127.0.0.1:{port}/feed', 'timeout_ms': 5000}),
                           capture_output=True, text=True, encoding='utf-8', timeout=30)
        err = json.loads(p.stdout)['error']
        self.assertTrue(err.startswith('fetch failed'), err)
        self.assertIn('ECONNREFUSED', err)
        actual = json.loads(p.stdout)['request_user_agent']
        self.assertTrue(actual, 'a network failure still records the identity actually sent')
        for forbidden in FORBIDDEN:
            self.assertNotIn(forbidden, actual.lower())

    def test_a_request_that_was_never_sent_claims_no_identity(self):
        p = subprocess.run(['node', str(ROOT / 'tools' / 'net_fetch.js')],
                           input=json.dumps({'url': 'ftp://example.org/feed'}),
                           capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertIsNone(json.loads(p.stdout).get('request_user_agent'))


if __name__ == '__main__':
    unittest.main()
