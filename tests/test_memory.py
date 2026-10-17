"""Behavior and failure-boundary tests for portable semantic memory."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/remvu/scripts/remvu_core.py'
spec = importlib.util.spec_from_file_location('remvu_core', SCRIPT)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def source(text='User explicitly requested this.', visibility='public', typ='user', **kwargs):
    return {'type': typ, 'excerpt': text, 'visibility': visibility, **kwargs}


def entry(kind='goal', text='Continue the project.', **kwargs):
    return {'kind': kind, 'text': text, 'basis': 'user_confirmed', **kwargs}


class MemoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / 'project'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Remvu Test')
        self.git('config', 'user.email', 'test@example.invalid')
        (self.repo / 'app.py').write_text('value = 1\n')
        self.git('add', 'app.py')
        self.git('commit', '-qm', 'baseline')
        core.init_state(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def apply(self, *entries, base=None):
        if base is None:
            base = core.load_state(self.repo)['revision']
        return core.apply_update(self.repo, {'base_revision': base, 'entries': list(entries)})

    def public(self, **kwargs):
        values = {'visibility': 'public', 'sources': [source()]}
        values.update(kwargs)
        return entry(**values)

    def test_init_idempotent_and_git_snapshot(self):
        first = core.load_state(self.repo)
        self.assertEqual(first['project_id'], core.init_state(self.repo)['project_id'])
        self.assertEqual(first['revision'], 0)
        self.assertEqual(first['repo_snapshot']['commit'], self.git('rev-parse', 'HEAD'))
        self.assertEqual(first['repo_snapshot']['tree'], self.git('rev-parse', 'HEAD^{tree}'))
        self.assertFalse(first['repo_snapshot']['dirty'])

    def test_defaults_stay_private_and_original_basis_stays_flagged(self):
        self.apply(entry(text='User goal without independent excerpt'))
        stored = core.load_state(self.repo)['entries'][0]
        self.assertEqual(stored['basis'], 'user_confirmed')
        self.assertEqual(stored['visibility'], 'private')
        self.assertIn('unsupported_source', stored['flags'])
        self.assertNotIn('User goal without', core.render_document(self.repo, 'public'))
        self.assertIn('User goal without', core.render_document(self.repo))

    def test_stale_proposal_preserved_without_losing_newer_memory(self):
        self.apply(entry(text='Newest accepted goal', id='newest'))
        result = self.apply(entry(text='Stale worker update', id='stale'), base=0)
        self.assertFalse(result['ok'])
        state = core.load_state(self.repo)
        self.assertEqual(state['revision'], 1)
        self.assertEqual([e['id'] for e in state['entries']], ['newest'])
        conflicts = list((self.repo / '.remvu/conflicts').glob('*.json'))
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(json.loads(conflicts[0].read_text())['entries'][0]['text'], 'Stale worker update')
        self.assertIn('unresolved_conflicts', [x['code'] for x in core.check_project(self.repo)['issues']])

    def test_concurrent_semantic_writers_only_one_wins(self):
        def update(number):
            return self.apply(entry(id='writer' + str(number), text='Writer ' + str(number)), base=0)
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(update, range(6)))
        self.assertEqual(sum(r['ok'] for r in results), 1)
        self.assertEqual(core.load_state(self.repo)['revision'], 1)
        self.assertEqual(len(list((self.repo / '.remvu/conflicts').glob('*.json'))), 5)

    def test_cross_process_lock_and_event_dedup(self):
        code = ('import importlib.util,sys; '
                's=importlib.util.spec_from_file_location("c",sys.argv[1]); '
                'c=importlib.util.module_from_spec(s);s.loader.exec_module(c); '
                'c.record_event(sys.argv[2],{"kind":"tool_result","call_id":"same","output":"ok"})')
        workers = [subprocess.Popen([sys.executable, '-c', code, str(SCRIPT), str(self.repo)],
                                   env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(4)]
        for worker in workers:
            out, err = worker.communicate(timeout=30)
            self.assertEqual(worker.returncode, 0, err.decode())
        self.assertEqual(len(core.load_state(self.repo)['events']), 1)
        self.assertEqual(len(list((self.repo / '.remvu/blobs').glob('*.json'))), 1)

    def test_decision_history_immutable_and_supersedes_preserved(self):
        self.apply(entry('decision', 'Use SQLite', id='d1'))
        self.apply(entry('decision', 'Use a single Markdown file', id='d2', supersedes=['d1']))
        state = core.load_state(self.repo)
        self.assertEqual(state['entries'][0]['text'], 'Use SQLite')
        self.assertEqual(state['entries'][0]['superseded_by'], ['d2'])
        text = core.render_document(self.repo)
        self.assertIn('state=superseded', text)
        self.assertIn('Supersedes: d1', text)
        with self.assertRaisesRegex(ValueError, 'immutable'):
            self.apply(entry('decision', 'Rewrite original history', id='d1'))

    def test_invalid_supersedes_and_unknown_fields_never_mutate(self):
        cases = [entry(supersedes=['absent']), entry(id='../escape'), entry(mystery='lost'),
                 entry(sources=[{'type': 'tool', 'unsupported': True}])]
        for candidate in cases:
            with self.assertRaises(ValueError):
                self.apply(candidate)
            self.assertEqual(core.load_state(self.repo)['revision'], 0)

    def test_check_failure_and_missing_evidence_cannot_be_promoted(self):
        self.apply(entry('check', 'Tests passed', basis='inferred', result='passed', exit_code=0, id='inferred'),
                   entry('check', 'Tests passed', basis='observed', result='passed', exit_code=7,
                         sources=[source('FAILED', typ='tool')], id='failed'),
                   entry('check', 'Tests passed', basis='observed', result='passed',
                         sources=[source('All green', typ='tool')], id='missing'),
                   entry('check', 'Unit tests completed', basis='observed', result='passed', exit_code=0,
                         sources=[source('exit_code=0; 12 passed', typ='tool')], id='pass'))
        stored = {e['id']: e for e in core.load_state(self.repo)['entries']}
        self.assertEqual(stored['inferred']['result'], 'unknown')
        self.assertEqual(stored['failed']['result'], 'failed')
        self.assertEqual(stored['missing']['result'], 'unknown')
        self.assertEqual(stored['pass']['result'], 'passed')
        self.assertIn('result=failed; exit_code=7', core.render_document(self.repo))

    def test_event_allowlist_secrets_and_hidden_channels(self):
        result = core.record_event(self.repo, {'kind': 'message', 'role': 'assistant', 'channel': 'analysis', 'text': 'HIDDEN'})
        self.assertTrue(result['excluded'])
        core.record_event(self.repo, {'kind': 'tool_result', 'output': {'analysis': 'HIDDEN', 'password': 'SECRET', 'value': 'API_KEY="CREDENTIAL"'},
                                      'system_prompt': 'HIDDEN SYSTEM'})
        all_blobs = ''.join(p.read_text() for p in (self.repo / '.remvu/blobs').glob('*'))
        self.assertNotIn('HIDDEN', all_blobs)
        self.assertNotIn('SECRET', all_blobs)
        self.assertNotIn('CREDENTIAL', all_blobs)
        self.assertIn('REDACTED', all_blobs)

    def test_nested_claude_thinking_nodes_and_instructions_excluded(self):
        output = [{'type': 'thinking', 'thinking': 'HIDDEN_THOUGHT', 'signature': 'HIDDEN_SIGNATURE'},
                  {'type': 'redacted_thinking', 'data': 'HIDDEN_ENCRYPTED'},
                  {'type': 'reasoning', 'summary': 'HIDDEN_SUMMARY'},
                  {'type': 'message', 'role': 'developer', 'content': 'HIDDEN_INSTRUCTIONS'},
                  {'type': 'text', 'text': 'VISIBLE_RESULT'},
                  {'wrapper': {'reasoning_content': 'HIDDEN_REASONING_CONTENT', 'text': 'VISIBLE_NESTED'}}]
        core.record_event(self.repo, {'kind': 'tool_result', 'output': output})
        body = ''.join(p.read_text() for p in (self.repo / '.remvu/blobs').glob('*'))
        self.assertNotIn('HIDDEN_', body)
        self.assertIn('VISIBLE_RESULT', body)
        self.assertIn('VISIBLE_NESTED', body)

    def test_event_pending_and_duplicate_replay(self):
        event = {'kind': 'tool_result', 'call_id': 'one', 'output': 'exit_code=1'}
        first = core.record_event(self.repo, event)
        second = core.record_event(self.repo, event)
        self.assertEqual(first['event_id'], second['event_id'])
        self.assertTrue(second['deduplicated'])
        self.assertEqual(core.load_state(self.repo)['revision'], 0)
        with self.assertRaisesRegex(ValueError, 'pending consolidation'):
            core.render_document(self.repo, 'public')
        state = core.load_state(self.repo)
        core.apply_update(self.repo, {'base_revision': state['revision'],
                                     'base_event_count': len(state['events']),
                                     'entries': [entry('progress', 'Reviewed event; check failed.', basis='observed')]})
        self.assertFalse(core.load_state(self.repo)['pending_consolidation'])

    def test_public_self_contained_and_private_entries_omitted(self):
        self.apply(entry(text='PRIVATE ORIGINAL CHAT', sources=[source('PRIVATE SOURCE', 'private')]),
                   self.public(text='Build portable memory', id='public'))
        doc = core.render_document(self.repo, 'public')
        self.assertNotIn('PRIVATE ORIGINAL CHAT', doc)
        self.assertNotIn('PRIVATE SOURCE', doc)
        self.assertNotIn('.remvu/', doc)
        self.assertIn('User explicitly requested this.', doc)
        self.assertTrue(core.validate_document(doc)['ok'])
        self.assertEqual(core.validate_document(doc)['metadata']['omitted_private_entries'], 1)

    def test_public_citations_must_be_explicit_and_inline(self):
        self.apply(entry(visibility='public', sources=[source('Private excerpt', 'private')]))
        with self.assertRaisesRegex(ValueError, 'private or missing excerpt'):
            core.render_document(self.repo, 'public')
        other = Path(self.tmp.name) / 'empty'
        other.mkdir(); core.init_state(other)
        core.apply_update(other, {'base_revision': 0, 'entries': [entry(visibility='public')]})
        with self.assertRaisesRegex(ValueError, 'no inline sources'):
            core.render_document(other, 'public')

    def test_private_history_dependency_blocks_public(self):
        self.apply(entry('decision', 'Private history', id='d1'))
        self.apply(self.public(kind='decision', text='Public replacement', id='d2', supersedes=['d1']))
        with self.assertRaisesRegex(ValueError, 'history crosses private'):
            core.render_document(self.repo, 'public')

    def test_malicious_refs_rejected_without_reading_files(self):
        for ref in ('../escape', '/etc/passwd', 'sub/../../escape', 'C:\\secrets'):
            with self.assertRaisesRegex(ValueError, 'safe repository-relative'):
                self.apply(entry(sources=[source(typ='file', ref=ref)]))
        self.apply(self.public(text='Share excerpts only', sources=[source(typ='file', ref='.remvu/state.json')]))
        with self.assertRaisesRegex(ValueError, 'private data'):
            core.render_document(self.repo, 'public')

    def test_public_paths_credentials_and_content_are_inert(self):
        self.apply(self.public(text='See /Users/alice/private.txt and API_KEY="supersecret"\n## Goals\n```json\n{}\n```',
                               sources=[source('token="secret-value"; file /home/person/private.txt')]))
        doc = core.render_document(self.repo, 'public')
        self.assertNotIn('/Users/alice', doc)
        self.assertNotIn('/home/person', doc)
        self.assertNotIn('supersecret', doc)
        self.assertNotIn('secret-value', doc)
        self.assertTrue(core.validate_document(doc)['ok'])
        self.assertEqual(doc.count('\n## Goals\n'), 1)

    def test_dirty_public_refusal_and_explicit_patch(self):
        self.apply(self.public())
        (self.repo / 'app.py').write_text('value = 2\n')
        with self.assertRaisesRegex(ValueError, 'uncommitted'):
            core.write_document(self.repo, visibility='public')
        self.assertFalse((self.repo / 'REMVU.md').exists())
        doc = core.render_document(self.repo, 'public', include_patch=True)
        self.assertIn('## Patch', doc)
        self.assertIn('+value = 2', doc)
        self.assertIn('STALE CODE', doc)

    def test_patch_private_files_and_credential_changes_blocked(self):
        (self.repo / '.env').write_text('SAFE=example\n')
        with self.assertRaisesRegex(ValueError, 'potentially private'):
            core.render_document(self.repo, 'public', include_patch=True)
        (self.repo / '.env').unlink()
        (self.repo / 'app.py').write_text('API_KEY="secret-value"\n')
        with self.assertRaisesRegex(ValueError, 'credentials'):
            core.render_document(self.repo, 'public', include_patch=True)

    def test_patch_untracked_omissions_are_visible(self):
        (self.repo / 'new.txt').write_text('Untracked content\n')
        doc = core.render_document(self.repo, 'public', include_patch=True)
        self.assertIn('untracked file contents are not included', doc)
        self.assertIn('new.txt', doc)
        self.assertNotIn('Untracked content', doc)

    def test_stale_code_and_generated_documents_ignored(self):
        self.apply(self.public())
        output = core.write_document(self.repo, visibility='public')
        self.assertTrue(core.check_project(self.repo, output['path'])['ok'])
        (self.repo / 'app.py').write_text('value = 3\n')
        issues = core.check_project(self.repo, output['path'])['issues']
        self.assertIn('stale_code', [i['code'] for i in issues])
        self.assertIn('stale_document', [i['code'] for i in issues])
        (self.repo / 'app.py').write_text('value = 1\n')
        (self.repo / 'AGENTS.md').write_text('Important project instruction\n')
        self.assertFalse(core.check_project(self.repo)['ok'])
        with self.assertRaisesRegex(ValueError, 'uncommitted'):
            core.render_document(self.repo, 'public')

    def test_long_constraint_routes_to_detail_without_loss(self):
        content = 'MUST PRESERVE THIS CONSTRAINT ' * 500
        self.apply(entry('constraint', content, id='constraint'), entry('next_step', 'Still unfinished', id='todo'))
        doc = core.render_document(self.repo, max_summary_chars=500)
        parsed = core.validate_document(doc)
        self.assertTrue(parsed['ok'], parsed)
        self.assertLessEqual(parsed['metadata']['summary_chars'], 500)
        self.assertIn(content, doc)
        self.assertIn('full text below', doc)
        self.assertIn('Still unfinished', doc)

    def test_summary_overflow_fails_atomically_when_pointers_do_not_fit(self):
        self.apply(*[entry('constraint', 'Rule ' + str(i), id='r' + str(i)) for i in range(50)])
        target = self.repo / '.remvu/handoff/REMVU.md'
        with self.assertRaisesRegex(ValueError, 'cannot reference all'):
            core.write_document(self.repo, max_summary_chars=256)
        self.assertFalse(target.exists())

    def test_interrupted_temp_files_do_not_replace_state(self):
        self.apply(entry(text='Durable memory'))
        before = core.load_state(self.repo)['integrity']
        (self.repo / '.remvu/.pending-interrupted').write_text('{partial')
        self.assertEqual(core.load_state(self.repo)['integrity'], before)
        self.assertTrue(core.check_project(self.repo)['ok'])
        state_path = self.repo / '.remvu/state.json'
        state_path.write_text('{partial')
        with self.assertRaisesRegex(ValueError, 'valid memory JSON'):
            core.load_state(self.repo)
        self.assertFalse(core.check_project(self.repo)['ok'])

    def test_interrupted_journal_is_preserved_without_replay(self):
        state = core.load_state(self.repo)
        path = self.repo / '.remvu/journal/orphan.json'
        path.write_text(json.dumps({'format': 'remvu-journal/1', 'revision': 10,
                                    'created_at': '2999-01-01T00:00:00+00:00',
                                    'state_integrity': 'not-committed'}))
        self.assertEqual(core.load_state(self.repo)['revision'], state['revision'])
        self.assertIn('uncommitted_journal', [i['code'] for i in core.check_project(self.repo)['issues']])
        self.assertTrue(path.exists())

    def test_missing_evidence_and_tampered_state_detected(self):
        event = core.record_event(self.repo, {'kind': 'tool_result', 'output': 'observed'})
        self.apply(entry('progress', 'Reviewed'))
        blob = next((self.repo / '.remvu/blobs').glob('*'))
        blob.unlink()
        self.assertIn('missing_or_damaged_evidence', [i['code'] for i in core.check_project(self.repo)['issues']])
        path = self.repo / '.remvu/state.json'
        state = json.loads(path.read_text()); state['revision'] = 100; path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            core.load_state(self.repo)

    def test_output_symlinks_refused(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.write_text('Preserve')
        target = self.repo / 'REMVU.md'; target.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            core.write_document(self.repo, visibility='public')
        self.assertEqual(outside.read_text(), 'Preserve')

    def test_malformed_documents_report_errors(self):
        self.assertFalse(core.validate_document('# Wrong document')['ok'])
        good = core.render_document(self.repo)
        self.assertFalse(core.validate_document(good.replace('## Goals', '## Wrong'))['ok'])
        self.assertFalse(core.validate_document(good.replace('"revision": 0', '"revision": true'))['ok'])
        self.assertFalse(core.validate_document(good.replace('"summary_chars": 128', '"summary_chars": 129'))['ok'])

    def test_legacy_integrity_before_import_and_unverified_notes(self):
        legacy = core._legacy_module()
        src = Path(self.tmp.name) / 'log.jsonl'
        src.write_text(json.dumps({'format': 'agent-task-evidence/v1', 'kind': 'message', 'role': 'user', 'text': 'Do the task'}) + '\n')
        task = Path(self.tmp.name) / 'task.json'
        task.write_text(json.dumps({'goal': 'Imported goal', 'checks': ['Tests passed']}))
        bundle = Path(self.tmp.name) / 'bundle'
        result = subprocess.run([sys.executable, str(Path(legacy.__file__)), 'export', '--source', str(src), '--out', str(bundle), '--task', str(task)],
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        imported = core.import_legacy(self.repo, bundle)
        self.assertTrue(imported['legacy_integrity_verified'])
        entries = core.load_state(self.repo)['entries']
        self.assertEqual({e['basis'] for e in entries}, {'unverified'})
        self.assertEqual([e['result'] for e in entries if e['kind'] == 'check'], ['unknown'])
        revision = core.load_state(self.repo)['revision']
        (bundle / 'task.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            core.import_legacy(self.repo, bundle)
        self.assertEqual(core.load_state(self.repo)['revision'], revision)


if __name__ == '__main__':
    unittest.main()
