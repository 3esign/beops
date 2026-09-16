"""C-080: a release links permission evidence instead of rewriting ~585 MB every half hour.

What must stay true: the release still names the exact bytes (sha256), a link is really the captured
file, a changed input still refuses the release, only research/evidence is linked, and a machine that
cannot link copies exactly as before."""
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_release as P  # noqa: E402

EVIDENCE = b'<html>permission page</html>\n' * 50
RAW = b'<rss>captured</rss>\n'


class ReleaseLinks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = pathlib.Path(self.tmp.name)
        self.source, self.releases = base / 'source', base / 'releases'
        self.ev = self.source / 'research/evidence/S01/20260901T000000Z/page.html'
        self.raw = self.source / 'data/live/raw/S01/20260901T000000Z.xml'
        for f, b in ((self.ev, EVIDENCE), (self.raw, RAW)):
            f.parent.mkdir(parents=True)
            f.write_bytes(b)
        self.releases.mkdir()
        self.n = 0
        env = patch.dict(os.environ, {'BEOPS_RELEASE_LINK_EVIDENCE': '1'})
        env.start()
        self.addCleanup(env.stop)

    def capture(self):
        self.n += 1
        dest = self.releases / f'beops-release-{self.n:032x}'
        dest.mkdir()
        metrics = {}
        inputs, _, _ = P.capture_inputs(self.source, dest, metrics)
        return dest, {r['path']: r for r in inputs}, metrics

    def test_evidence_is_linked_and_still_hashed(self):
        dest, rows, m = self.capture()
        rel = 'research/evidence/S01/20260901T000000Z/page.html'
        self.assertTrue(os.path.samefile(self.ev, dest / rel))
        self.assertEqual(rows[rel]['sha256'], hashlib.sha256(EVIDENCE).hexdigest())
        self.assertEqual(rows[rel]['bytes'], len(EVIDENCE))
        self.assertEqual((m['linked_files'], m['linked_bytes']), (1, len(EVIDENCE)))

    def test_nothing_outside_research_evidence_is_linked(self):
        dest, rows, _ = self.capture()
        rel = 'data/live/raw/S01/20260901T000000Z.xml'
        self.assertFalse(os.path.samefile(self.raw, dest / rel))
        self.assertEqual((dest / rel).read_bytes(), RAW)
        self.assertEqual(rows[rel]['sha256'], hashlib.sha256(RAW).hexdigest())

    def test_removing_the_release_leaves_the_evidence(self):
        import shutil
        dest, _, _ = self.capture()
        shutil.rmtree(dest)
        self.assertEqual(self.ev.read_bytes(), EVIDENCE)

    def test_the_second_release_does_not_reread_unchanged_evidence(self):
        self.capture()
        _, rows, m = self.capture()
        self.assertEqual(m['evidence_bytes_hashed'], 0)
        self.assertEqual(rows['research/evidence/S01/20260901T000000Z/page.html']['sha256'],
                         hashlib.sha256(EVIDENCE).hexdigest())

    def test_a_cached_hash_older_than_a_day_is_measured_again(self):
        self.capture()
        cache = self.releases / P.HASH_CACHE_NAME
        doc = json.loads(cache.read_text(encoding='utf-8'))
        for row in doc['files'].values():
            row['hashed_at'] = time.time() - 25 * 3600
        cache.write_text(json.dumps(doc), encoding='utf-8')
        _, _, m = self.capture()
        self.assertEqual(m['evidence_bytes_hashed'], len(EVIDENCE))

    def test_a_rewritten_evidence_file_is_hashed_again_not_trusted(self):
        self.capture()
        new = EVIDENCE.replace(b'permission', b'PERMISSION')
        self.ev.write_bytes(new)
        st = self.ev.stat()
        os.utime(self.ev, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
        _, rows, _ = self.capture()
        self.assertEqual(rows['research/evidence/S01/20260901T000000Z/page.html']['sha256'],
                         hashlib.sha256(new).hexdigest())

    def test_evidence_changed_during_capture_refuses_the_release(self):
        real = P.EvidenceHashes.sha

        def touch_then_hash(hashes, path, rel, stat):
            os.utime(path, ns=(stat[1], stat[1] + 7_000_000_000))
            return real(hashes, path, rel, stat)
        with patch.object(P.EvidenceHashes, 'sha', touch_then_hash):
            with self.assertRaisesRegex(RuntimeError, 'input changed after capture'):
                self.capture()

    def test_no_link_support_copies_as_before(self):
        with patch.object(P.os, 'link', side_effect=OSError('cross-device')):
            dest, rows, m = self.capture()
        rel = 'research/evidence/S01/20260901T000000Z/page.html'
        self.assertFalse(os.path.samefile(self.ev, dest / rel))
        self.assertEqual((dest / rel).read_bytes(), EVIDENCE)
        self.assertEqual(m['linked_files'], 0)

    def test_the_switch_turns_linking_off(self):
        with patch.dict(os.environ, {'BEOPS_RELEASE_LINK_EVIDENCE': '0'}):
            dest, _, m = self.capture()
        self.assertFalse(os.path.samefile(self.ev, dest / 'research/evidence/S01/20260901T000000Z/page.html'))
        self.assertEqual(m['linked_files'], 0)
        self.assertNotIn('evidence_bytes_hashed', m)

    def test_a_linked_release_records_the_same_manifest_rows_as_a_copied_one(self):
        _, linked, _ = self.capture()
        with patch.dict(os.environ, {'BEOPS_RELEASE_LINK_EVIDENCE': '0'}):
            _, copied, _ = self.capture()
        self.assertEqual(linked, copied)


if __name__ == '__main__':
    unittest.main()
