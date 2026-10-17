"""CLI-level integration: the documented workflow, not implementation mirrors."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/remvu/scripts/remvu.py'


class CliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / 'project with spaces'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Remvu Test')
        self.git('config', 'user.email', 'test@example.invalid')
        (self.repo / '.gitignore').write_text('__pycache__/\n.remvu/\n', encoding='utf-8')
        (self.repo / 'app.py').write_text('def answer():\n    return 42\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.cli('init', '--platform', 'none', '--repo', self.repo)
        self.git('add', '.gitignore')
        self.git('commit', '-qm', 'Ignore local Remvu state')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True)

    def cli(self, *args, ok=True, input=None):
        process = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                 input=input, capture_output=True, text=True)
        if ok:
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        else:
            self.assertNotEqual(process.returncode, 0, process.stdout)
        return json.loads(process.stdout)

    def proposal(self, entries, base=0):
        data = {'base_revision': base, 'entries': entries}
        return self.cli('update', '--repo', self.repo, '--proposal', '-', input=json.dumps(data))

    def test_documented_round_trip_without_receiver_installation(self):
        self.proposal([{'kind': 'constraint', 'text': 'Preserve the public API.',
                        'basis': 'user_confirmed', 'visibility': 'public',
                        'sources': [{'type': 'user', 'excerpt': 'Preserve the public API.', 'visibility': 'public'}]},
                       {'kind': 'next_step', 'text': 'Add a boundary test.', 'basis': 'unverified',
                        'visibility': 'public', 'sources': [{'type': 'user', 'excerpt': 'Next, add a boundary test.', 'visibility': 'public'}]}])
        local = self.cli('handoff', '--repo', self.repo)
        shared = self.cli('share', '--repo', self.repo)
        self.assertEqual(shared['visibility'], 'public')
        text = Path(shared['path']).read_text(encoding='utf-8')
        self.assertIn('Preserve the public API.', text)
        self.assertNotIn(str(self.repo), text)
        self.assertTrue(self.cli('validate', shared['path'])['ok'])
        self.assertTrue(self.cli('check', '--repo', self.repo, '--document', shared['path'])['ok'])
        self.assertTrue(Path(local['path']).is_file())
        status = self.cli('status', '--repo', self.repo)
        self.assertEqual(status['entry_count'], 2)
        # The copied Markdown remains readable and valid without .remvu/ state.
        receiver = self.root / 'receiver'
        subprocess.check_call(['git', 'clone', '-q', str(self.repo), str(receiver)])
        copy = receiver / 'REMVU.md'; copy.write_text(text, encoding='utf-8')
        self.assertTrue(self.cli('validate', copy)['ok'])
        self.assertFalse((receiver / '.remvu').exists())
        self.assertTrue(self.cli('check', '--repo', receiver, '--document', copy)['ok'])
        self.assertFalse((receiver / '.remvu').exists())

    def test_dirty_share_stale_proposal_and_failed_check_are_visible(self):
        result = self.proposal([{'kind': 'check', 'text': 'Boundary suite failed.', 'basis': 'observed',
                                'result': 'failed', 'exit_code': 1,
                                'sources': [{'type': 'tool', 'excerpt': 'exit code 1: assertion failed'}]}])
        self.assertTrue(result['ok'])
        stale = self.cli(
            'update', '--repo', self.repo, '--proposal', '-', ok=False,
            input=json.dumps({'base_revision': 0, 'entries': []}))
        self.assertFalse(stale['ok'])
        (self.repo / 'app.py').write_text('changed\n', encoding='utf-8')
        refused = self.cli('share', '--repo', self.repo, ok=False)
        self.assertIn('uncommitted', refused['error'])
        check = self.cli('check', '--repo', self.repo, ok=False)
        self.assertIn('stale_code', [item['code'] for item in check['issues']])
        self.assertEqual(self.cli('status', '--repo', self.repo)['entries'][0]['result'], 'failed')

    def test_self_contained_legacy_engine_and_import(self):
        bundle = self.root / 'legacy'
        exported = self.cli('legacy', 'export', '--source', ROOT / 'examples/session.jsonl',
                            '--task', ROOT / 'examples/task.json', '--out', bundle)
        self.assertEqual(exported['events'], 6)
        imported = self.cli('import-legacy', '--repo', self.repo, bundle)
        self.assertTrue(imported['ok'])
        state = self.cli('status', '--repo', self.repo)
        self.assertTrue(state['entries'])
        self.assertTrue(all(e['basis'] == 'unverified' for e in state['entries']))
        self.assertTrue(all(e.get('result', 'unknown') == 'unknown' for e in state['entries'] if e['kind'] == 'check'))

    def test_conflict_requires_explicit_review_before_public_share(self):
        self.proposal([])
        conflict = self.cli('update', '--repo', self.repo, '--proposal', '-', ok=False,
                            input=json.dumps({'base_revision': 0, 'entries': []}))
        conflict_id = conflict['conflicts'][0]
        refused = self.cli('share', '--repo', self.repo, ok=False)
        self.assertIn('unresolved conflicts', refused['error'])
        stale = self.cli('resolve-conflict', conflict_id, '--repo', self.repo,
                         '--base-revision', 0, '--note', 'Reviewed the unchanged proposal.', ok=False)
        self.assertFalse(stale['ok'])
        reviewed = self.cli('resolve-conflict', conflict_id, '--repo', self.repo,
                            '--base-revision', 1, '--note', 'Reviewed; no additional entries are needed.')
        self.assertTrue(reviewed['ok'])
        self.assertTrue(self.cli('share', '--repo', self.repo)['ok'])
        self.assertTrue((self.repo / '.remvu' / reviewed['resolution_ref']).is_file())

    def test_inline_proposal_consolidates_reviewed_events_without_a_file(self):
        spec = importlib.util.spec_from_file_location('remvu_inline_test_core', SCRIPT.with_name('remvu_core.py'))
        core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
        core.record_event(self.repo, {'kind': 'tool_result', 'output': 'Observed check output.'})
        result = self.cli('update', '--repo', self.repo, '--proposal-json',
                          json.dumps({'base_revision': 0, 'base_event_count': 1, 'entries': []}))
        self.assertTrue(result['ok'])
        self.assertFalse(result['pending_consolidation'])
        self.assertFalse((self.repo / '.remvu/proposal.json').exists())

    def test_bounded_event_reads_check_blob_integrity(self):
        spec = importlib.util.spec_from_file_location('remvu_cli_test_core', SCRIPT.with_name('remvu_core.py'))
        core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
        entry = core.record_event(self.repo, {'kind': 'tool_result', 'tool': 'test', 'output': 'data ' * 2000})
        listing = self.cli('events', '--repo', self.repo)
        self.assertEqual(listing['total'], 1)
        shown = self.cli('show', entry['event_id'], '--repo', self.repo, '--max-chars', 100)
        self.assertTrue(shown['truncated_for_display'])
        blob = self.repo / '.remvu' / listing['events'][0]['blob_ref']
        blob.write_text('tampered', encoding='utf-8')
        failed = self.cli('show', entry['event_id'], '--repo', self.repo, ok=False)
        self.assertIn('integrity', failed['error'])

    def test_default_status_is_bounded_and_long_entry_remains_retrievable(self):
        original = 'Preserve the important requirement. ' * 2000
        self.proposal([{'kind': 'constraint', 'text': original,
                        'basis': 'user_confirmed',
                        'sources': [{'type': 'user', 'excerpt': 'A long but valid requirement.'}]}])
        status = self.cli('status', '--repo', self.repo)
        self.assertLess(len(json.dumps(status, ensure_ascii=False, indent=2)), 8000)
        self.assertTrue(status['entries'][0]['text_truncated'])
        page = self.cli('entries', '--repo', self.repo)
        self.assertEqual(page['total'], 1)
        detail = self.cli('show', page['entries'][0]['id'], '--repo', self.repo, '--max-chars', 1000)
        self.assertTrue(detail['truncated_for_display'])
        full = self.cli('status', '--repo', self.repo, '--full')
        self.assertEqual(full['entries'][0]['text'], original)


if __name__ == '__main__':
    unittest.main()
