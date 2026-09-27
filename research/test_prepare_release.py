"""Release metadata savings preserve the archived scope and linked-file identity."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_release as P


class PreparationMetadata(unittest.TestCase):
    def test_capacity_source_size_uses_fixed_archive_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            source = pathlib.Path(folder)
            files = {'source.txt': b'code\n', 'research/code.txt': b'research\n',
                     'research/evidence/proof.txt': b'proof' * 100,
                     'research/_scratch/draft.txt': b'draft' * 200}
            for name, raw in files.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            P.git(source, 'init', '-q')
            P.git(source, '-c', 'core.autocrlf=false', 'add', '.')
            P.git(source, '-c', 'user.name=Semir Poturak',
                  '-c', 'user.email=scumutator@gmail.com', 'commit', '-qm', 'fixture')
            oid = P.git(source, 'rev-parse', 'HEAD')
            # A working-tree change must not affect the fixed release estimate.
            (source / 'source.txt').write_bytes(b'new uncommitted bytes' * 100)
            size = P.archive_source_bytes(source, oid, P.archive_paths(source, oid))
            self.assertEqual(size, len(files['source.txt']) + len(files['research/code.txt']))

    def capture(self, source, dest):
        dest.mkdir()
        with patch.dict(os.environ, {'BEOPS_RELEASE_LINK_EVIDENCE': '1'}):
            return P.capture_inputs(source, dest)

    def evidence(self, base):
        source, dest = base / 'source', base / 'release'
        rel = pathlib.Path('research/evidence/S01/proof.txt')
        evidence = source / rel
        evidence.parent.mkdir(parents=True)
        evidence.write_bytes(b'permission evidence\n')
        return source, dest, rel, evidence

    def test_link_identity_reuses_source_stat_without_rereading_path(self):
        with tempfile.TemporaryDirectory() as folder:
            source, dest, rel, evidence = self.evidence(pathlib.Path(folder))
            with patch.object(P.os.path, 'samefile', side_effect=AssertionError('duplicate source stat')):
                rows, _, _ = self.capture(source, dest)
            self.assertTrue(os.path.samefile(evidence, dest / rel))
            self.assertEqual(rows[0]['sha256'], hashlib.sha256(evidence.read_bytes()).hexdigest())

    def test_copy_reported_as_link_is_rejected_even_with_equal_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            source, dest, _, _ = self.evidence(pathlib.Path(folder))
            with patch.object(P.os, 'link', side_effect=shutil.copyfile):
                with self.assertRaisesRegex(RuntimeError, 'linked input is not the captured file'):
                    self.capture(source, dest)

    def accounting_inputs(self, source):
        at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        cycle, pending, attempt = 'a' * 32, 'b' * 32, 'c' * 32
        start = {'schema': 'beops-resource-cycle/v1', 'id': cycle, 'phase': 'start',
                 'activity': 'ai_feed', 'runtime': 'node', 'pid': 123, 'started_at': at}
        finish = {**start, 'phase': 'finish', 'finished_at': at, 'outcome': 'accepted',
                  'wall_seconds': 2, 'cpu_seconds': 1, 'peak_rss_bytes': 100,
                  'tokens': {'state': 'partial_provider_reporting', 'reported_calls': 1,
                             'unreported_calls': 0, 'input_tokens': 10, 'output_tokens': 3},
                  'http': {'request_attempts': 1, 'body_reports': 1,
                           'unreported_bodies': 0, 'response_body_bytes': 25}}
        attempt_row = {'id': attempt, 'at': at, 'state': 'accepted', 'provider': 'fixture'}
        records = {
            f'runtime/resources/receipts/{cycle}-start.json': start,
            f'runtime/resources/receipts/{cycle}-finish.json': finish,
            f'runtime/resources/receipts/{pending}-start.json': {**start, 'id': pending},
            f'runtime/ai-feed/receipts/{attempt}-start.json': {**attempt_row, 'state': 'started'},
            f'runtime/ai-feed/receipts/{attempt}-finish.json': attempt_row,
            f'runtime/ai-feed/responses/{attempt}.json': {
                'usage': {'input_tokens': 10, 'output_tokens': 3}, 'model': 'fixture'},
        }
        for rel, value in records.items():
            file = source / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(json.dumps(value) + '\n', encoding='utf-8')
        return records

    @unittest.skipUnless(shutil.which('node'), 'resource summary needs Node')
    def test_frozen_resource_inputs_preserve_measured_and_unfinished_work(self):
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder)
            source, dest = base / 'source', base / 'release'
            records = self.accounting_inputs(source)
            ignored = ('runtime/resources/receipts/writing.json.tmp',
                       'runtime/resources/receipts/.in-flight.json',
                       'runtime/ai-feed/responses/writing.json.tmp',
                       'runtime/ai-feed/private-note.json')
            for rel in ignored:
                (source / rel).write_text('private/in-flight', encoding='utf-8')
            rows, captured_at, _ = self.capture(source, dest)
            manifest = {row['path']: row for row in rows}
            self.assertEqual(set(manifest), set(records))
            for rel in records:
                raw = (source / rel).read_bytes()
                self.assertEqual((dest / rel).read_bytes(), raw)
                self.assertEqual(manifest[rel]['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertFalse(os.path.samefile(source / rel, dest / rel))
            for rel in ignored:
                self.assertFalse((dest / rel).exists())
            runner = base / 'summary.cjs'
            runner.write_text("const {buildSummary}=require(process.argv[2]);"
                              "process.stdout.write(JSON.stringify(buildSummary(process.argv[3],process.argv[4])));",
                              encoding='utf-8')

            def summary(root):
                result = subprocess.run(['node', str(runner), str(ROOT / 'tools/resource_summary.js'),
                                         str(root), captured_at], check=True, capture_output=True,
                                        text=True, timeout=30)
                return json.loads(result.stdout)

            frozen = summary(dest)
            self.assertEqual(frozen, summary(source))
            day = frozen['windows']['day']
            self.assertEqual((day['finished_cycles'], day['unfinished_cycles']), (1, 1))
            self.assertEqual((day['tokens']['input_tokens'], day['tokens']['output_tokens']), (10, 3))
            self.assertEqual(frozen['historical_provider_usage']['all']['input_tokens'], 10)
            self.assertEqual(frozen['coverage']['incomplete_receipts'], 0)
            self.assertIsNone(day['electricity_wh'])
            # A subsequent rewrite of a live receipt cannot alter frozen bytes.
            next(iter(source.glob('runtime/resources/receipts/*-finish.json'))).write_text('{}', encoding='utf-8')
            self.assertEqual(summary(dest), frozen)

    def test_accounting_input_changed_during_copy_refuses_release(self):
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder)
            source, dest = base / 'source', base / 'release'
            self.accounting_inputs(source)
            target = source / ('runtime/ai-feed/responses/' + 'c' * 32 + '.json')
            real_open = pathlib.Path.open

            def changed_open(path, mode='r', *args, **kwargs):
                if path == target and mode == 'rb':
                    stat = path.stat()
                    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
                return real_open(path, mode, *args, **kwargs)

            with patch.object(pathlib.Path, 'open', changed_open):
                with self.assertRaisesRegex(RuntimeError, 'input changed after capture'):
                    self.capture(source, dest)


if __name__ == '__main__':
    unittest.main()
