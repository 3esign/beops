"""Offline regression of the provider probe: no model, no network, no menu."""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Probe(unittest.TestCase):
    def test_offline_probe_contracts(self):
        r = subprocess.run(['node', str(ROOT / 'research/test_ai_feed_probe_node.js')],
                           capture_output=True, text=True, encoding='utf-8', timeout=120,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(r.returncode, 0, r.stdout + '\n' + r.stderr)
        self.assertIn('probe contracts passed', r.stdout)

    def test_the_probe_is_not_wired_to_a_key(self):
        """The whole point of this route is that it goes through the Svemir CLI menu.
        A key read here would be a second, quieter path to a model."""
        source = (ROOT / 'tools' / 'ai_feed_probe.js').read_text(encoding='utf-8')
        for forbidden in ('API_KEY', 'Authorization', 'key_env', 'process.env.'):
            self.assertNotIn(forbidden, source, forbidden)


if __name__ == '__main__':
    unittest.main()
