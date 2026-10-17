"""Explicit, audited narrowing of share scope without rewriting project history."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/remvu/scripts/remvu_core.py'
spec = importlib.util.spec_from_file_location('remvu_scope_core', SCRIPT)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def entry(entry_id, text='Project decision.', visibility='private', **extra):
    return {'id': entry_id, 'kind': 'decision', 'text': text, 'basis': 'user_confirmed',
            'visibility': visibility, 'sources': [{'type': 'user', 'excerpt': text, 'visibility': visibility}],
            **extra}


class PublicScopeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='remvu-scope-')
        self.repo = Path(self.tmp.name).resolve()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Remvu Scope Test')
        self.git('config', 'user.email', 'scope@example.invalid')
        (self.repo / 'app.py').write_bytes(b'value = 1\n')
        self.git('add', 'app.py')
        self.git('commit', '-qm', 'baseline')
        core.init_state(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def state(self):
        return core.load_state(self.repo)

    def update(self, *entries):
        return core.apply_update(self.repo, {'base_revision': self.state()['revision'], 'entries': list(entries)})

    def problematic_history(self, include_unrelated=False):
        self.update(entry('private-history', 'Original private rationale.'))
        entries = [entry('mistaken-public', 'Replacement with a private history link.', 'public',
                         supersedes=['private-history'])]
        if include_unrelated:
            entries.append(entry('unrelated-public', 'Independent shareable decision.', 'public'))
        self.update(*entries)

    def test_withdraw_problematic_entry_then_share_independent_public_summary(self):
        self.problematic_history()
        with self.assertRaisesRegex(ValueError, 'mistaken-public.*history crosses private'):
            core.render_document(self.repo, 'public')
        withdrawn = core.withhold_entries(self.repo, ['mistaken-public'], 2,
                                          'The source history is private; withdraw this public scope.')
        self.assertEqual(withdrawn['withheld_ids'], ['mistaken-public'])
        self.assertEqual(withdrawn['revision'], 3)
        self.update(entry('public-summary', 'Use the reviewed public interface.', 'public'))
        document = core.render_document(self.repo, 'public')
        self.assertIn('Use the reviewed public interface.', document)
        self.assertNotIn('Original private rationale.', document)
        self.assertNotIn('Replacement with a private history link.', document)
        self.assertTrue(core.validate_document(document)['ok'])
        by_id = {item['id']: item for item in self.state()['entries']}
        self.assertEqual(by_id['private-history']['text'], 'Original private rationale.')
        self.assertEqual(by_id['private-history']['superseded_by'], ['mistaken-public'])
        self.assertEqual(by_id['mistaken-public']['supersedes'], ['private-history'])
        self.assertEqual(by_id['mistaken-public']['visibility'], 'private')

    def test_withdrawal_preserves_all_other_entry_fields_and_audits_original(self):
        self.problematic_history()
        before = self.state()
        original = next(item for item in before['entries'] if item['id'] == 'mistaken-public')
        core.withhold_entries(self.repo, ['mistaken-public'], 2, 'Reviewed and narrowed public scope.')
        after = self.state()
        updated = next(item for item in after['entries'] if item['id'] == 'mistaken-public')
        self.assertEqual({**updated, 'visibility': 'public'}, original)
        self.assertEqual(after['entries'][0], before['entries'][0])
        self.assertEqual(updated['sources'], original['sources'])
        audit = after['share_withdrawals'][-1]
        self.assertEqual(audit['entry_id'], 'mistaken-public')
        self.assertEqual(audit['from_visibility'], 'public')
        self.assertEqual(audit['to_visibility'], 'private')
        self.assertEqual(audit['revision'], 3)
        self.assertEqual(audit['note'], 'Reviewed and narrowed public scope.')
        self.assertTrue(audit['at'])
        journal = json.loads((self.repo / '.remvu/journal' / (after['last_journal_id'] + '.json')).read_text(encoding='utf-8'))
        self.assertEqual(journal['operation'], 'withhold_entries')
        self.assertEqual(journal['payload']['original_public_entries'], [original])
        self.assertEqual(journal['payload']['note'], audit['note'])
        self.assertIn('Original private rationale.', core.render_document(self.repo))

    def test_other_unresolved_public_history_links_still_block_sharing(self):
        self.problematic_history(include_unrelated=True)
        core.withhold_entries(self.repo, ['unrelated-public'], 2, 'Narrow this separate public entry.')
        with self.assertRaisesRegex(ValueError, 'mistaken-public.*history crosses private.*Withhold'):
            core.render_document(self.repo, 'public')

    def test_withdrawal_does_not_rewrite_existing_public_file(self):
        self.update(entry('public-goal', 'Previously shared project statement.', 'public'))
        path = Path(core.write_document(self.repo, visibility='public')['path'])
        before = path.read_bytes()
        result = core.withhold_entries(self.repo, ['public-goal'], 1, 'Withdraw the previous public statement.')
        self.assertEqual(path.read_bytes(), before)
        self.assertIn('may still include withdrawn data', result['warning'])
        self.assertIn('not rewritten', result['warning'])
        replacement = core.render_document(self.repo, 'public')
        self.assertNotIn('Previously shared project statement.', replacement)
        self.assertIn('Previously shared project statement.', core.render_document(self.repo))

    def test_private_entry_withdrawal_is_idempotent_and_validates_inputs(self):
        self.update(entry('already-private'))
        before = (self.repo / '.remvu/state.json').read_bytes()
        result = core.withhold_entries(self.repo, ['already-private'], 1, 'Keep this entry private.')
        self.assertEqual(result['withheld_ids'], [])
        self.assertEqual(result['already_private_ids'], ['already-private'])
        self.assertEqual(result['revision'], 1)
        self.assertEqual((self.repo / '.remvu/state.json').read_bytes(), before)
        for ids, revision, note in ((['already-private'], 1, ' '), ([], 1, 'No IDs'),
                                    (['already-private'], True, 'Invalid revision'),
                                    (['../invalid'], 1, 'Invalid ID')):
            with self.subTest(ids=ids, revision=revision), self.assertRaises(ValueError):
                core.withhold_entries(self.repo, ids, revision, note)
            self.assertEqual((self.repo / '.remvu/state.json').read_bytes(), before)

    def test_stale_or_unknown_requests_never_partially_withdraw(self):
        self.update(entry('public-entry', visibility='public'))
        before = (self.repo / '.remvu/state.json').read_bytes()
        stale = core.withhold_entries(self.repo, ['public-entry'], 0, 'Stale request.')
        self.assertFalse(stale['ok'])
        self.assertEqual(stale['withheld_ids'], [])
        with self.assertRaisesRegex(ValueError, 'unknown entry'):
            core.withhold_entries(self.repo, ['public-entry', 'unknown-entry'], 1, 'Validate all IDs first.')
        self.assertEqual((self.repo / '.remvu/state.json').read_bytes(), before)
        self.assertEqual(self.state()['entries'][0]['visibility'], 'public')

    def test_withdrawal_never_acknowledges_events_or_refreshes_check_provenance(self):
        self.update({'id': 'public-check', 'kind': 'check', 'text': 'Observed test passed.', 'basis': 'observed',
                     'visibility': 'public', 'result': 'passed', 'exit_code': 0,
                     'sources': [{'type': 'tool', 'excerpt': '1 passed; exit code 0', 'visibility': 'public'}]})
        (self.repo / 'app.py').write_bytes(b'value = 2\n')
        core.record_event(self.repo, {'kind': 'tool_result', 'call_id': 'unreviewed', 'output': 'new failure', 'exit_code': 1})
        before = self.state()
        result = core.withhold_entries(self.repo, ['public-check'], 1, 'Keep this historical check private.')
        after = self.state()
        self.assertTrue(result['pending_consolidation'])
        self.assertEqual(after['events'], before['events'])
        self.assertEqual(after['consolidated_event_count'], before['consolidated_event_count'])
        self.assertEqual(after['repo_snapshot'], before['repo_snapshot'])
        self.assertEqual(after['entries'][0]['observed_code'], before['entries'][0]['observed_code'])
        self.assertEqual(after['entries'][0]['result'], 'passed')
        codes = [issue['code'] for issue in core.check_project(self.repo)['issues']]
        self.assertIn('pending_consolidation', codes)
        self.assertIn('stale_code', codes)
        self.assertIn('stale_check_evidence', codes)

    def test_withdrawn_id_cannot_be_republished_by_replaying_old_proposal(self):
        original = entry('public-entry', visibility='public')
        self.update(original)
        core.withhold_entries(self.repo, ['public-entry', 'public-entry'], 1, 'Narrow the public scope once.')
        self.assertEqual(len(self.state()['share_withdrawals']), 1)
        before = (self.repo / '.remvu/state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'immutable'):
            self.update(original)
        self.assertEqual((self.repo / '.remvu/state.json').read_bytes(), before)
        again = core.withhold_entries(self.repo, ['public-entry'], 2, 'Repeated narrowing request.')
        self.assertEqual(again['already_private_ids'], ['public-entry'])
        self.assertEqual((self.repo / '.remvu/state.json').read_bytes(), before)

    def test_public_source_errors_identify_entry_and_explain_immutable_recovery(self):
        broken = entry('bad-sources', visibility='public')
        broken['sources'][0]['visibility'] = 'private'
        self.update(broken)
        with self.assertRaisesRegex(ValueError, 'bad-sources.*sources are immutable.*withhold'):
            core.render_document(self.repo, 'public')
        core.withhold_entries(self.repo, ['bad-sources'], 1, 'Original citation is private.')
        self.update(entry('safe-summary', 'Self-contained shareable summary.', 'public'))
        document = core.render_document(self.repo, 'public')
        self.assertIn('Self-contained shareable summary.', document)
        self.assertNotIn('bad-sources', document)


if __name__ == '__main__':
    unittest.main()
