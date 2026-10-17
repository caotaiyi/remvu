"""Regressions for independently reproduced continuity and validation failures."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/remvu/scripts/remvu_core.py'
spec = importlib.util.spec_from_file_location('remvu_review_core', SCRIPT)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def note(kind='preference', text='Keep comments concise.', **extra):
    return {'kind': kind, 'text': text, 'basis': 'user_confirmed', **extra}


def check(check_id='check-a', **extra):
    return {'id': check_id, 'kind': 'check', 'text': 'Observed unit check passed.',
            'basis': 'observed', 'result': 'passed', 'exit_code': 0, 'visibility': 'public',
            'sources': [{'type': 'tool', 'excerpt': 'python check.py: 1 passed; exit code 0',
                         'visibility': 'public'}], **extra}


class ReviewRegressionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='remvu-review-')
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'sender'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Remvu Regression')
        self.git('config', 'user.email', 'regression@example.invalid')
        (self.repo / 'app.py').write_text('value = 1\n')
        self.git('add', 'app.py')
        self.git('commit', '-qm', 'baseline')
        core.init_state(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def update(self, *entries, **extra):
        proposal = {'base_revision': core.load_state(self.repo)['revision'], 'entries': list(entries), **extra}
        return core.apply_update(self.repo, proposal)

    def issues(self, **extra):
        return [issue['code'] for issue in core.check_project(self.repo, **extra)['issues']]

    def event(self, call_id):
        return core.record_event(self.repo, {'kind': 'tool_result', 'call_id': call_id,
                                            'output': 'failure', 'exit_code': 1})

    def conflict(self):
        self.update(note(id='accepted'))
        stale = {'base_revision': 0, 'base_event_count': 0,
                 'entries': [note('decision', 'Use the reconciled design.', id='stale-proposal')]}
        result = core.apply_update(self.repo, stale)
        return result['conflicts'][0], stale

    @staticmethod
    def replace_metadata(document, mutate):
        before, remaining = document.split('```json\n', 1)
        body, after = remaining.split('\n```', 1)
        metadata = json.loads(body)
        mutate(metadata)
        return before + '```json\n' + json.dumps(metadata, ensure_ascii=False, indent=2) + '\n```' + after

    def test_unrelated_update_cannot_launder_old_passing_check(self):
        self.update(check())
        observed = core.load_state(self.repo)['entries'][0]['observed_code'].copy()
        (self.repo / 'app.py').write_text('value = 2\n')
        self.update(note(id='unrelated'))
        state = core.load_state(self.repo)
        self.assertEqual(state['entries'][0]['observed_code'], observed)
        self.assertNotEqual(observed['fingerprint'], state['repo_snapshot']['fingerprint'])
        issues = self.issues()
        self.assertNotIn('stale_code', issues)
        self.assertIn('stale_check_evidence', issues)
        text = core.render_document(self.repo, 'public', include_patch=True)
        self.assertIn('STALE CHECK EVIDENCE', text)
        self.assertIn('result=passed; exit_code=0; evidence=historical/stale', text)
        self.assertIn('this result does not validate the current code', text)

    def test_duplicate_check_id_never_revalidates_it(self):
        self.update(check())
        observed = core.load_state(self.repo)['entries'][0]['observed_code'].copy()
        (self.repo / 'app.py').write_text('value = 3\n')
        replay = self.update(check())
        self.assertEqual(replay['applied_ids'], [])
        self.assertEqual(core.load_state(self.repo)['entries'][0]['observed_code'], observed)
        self.assertIn('stale_check_evidence', self.issues())
        with self.assertRaises(ValueError):
            self.update(check(observed_code={'fingerprint': '0' * 64, 'commit': None}))

    def test_fresh_check_supersedes_stale_history(self):
        self.update(check())
        (self.repo / 'app.py').write_text('value = 4\n')
        self.update(check('check-b', supersedes=['check-a']))
        self.assertNotIn('stale_check_evidence', self.issues())
        state = core.load_state(self.repo)
        self.assertEqual(state['entries'][0]['superseded_by'], ['check-b'])
        self.assertNotEqual(state['entries'][0]['observed_code']['fingerprint'],
                            state['entries'][1]['observed_code']['fingerprint'])
        text = core.render_document(self.repo)
        self.assertIn('state=superseded; result=passed', text)
        self.assertIn('evidence=historical/stale', text)
        self.assertIn('state=active; result=passed; exit_code=0; evidence=current-code', text)

    def test_commit_only_change_does_not_invalidate_content_evidence(self):
        self.update(check())
        old_commit = core.load_state(self.repo)['entries'][0]['observed_code']['commit']
        self.git('commit', '--allow-empty', '-qm', 'metadata-only revision')
        self.assertNotEqual(old_commit, self.git('rev-parse', 'HEAD'))
        result = core.check_project(self.repo)
        self.assertTrue(result['ok'], result)
        text = core.render_document(self.repo, 'public')
        self.assertNotIn('STALE CODE', text)
        self.assertNotIn('STALE CHECK EVIDENCE', text)

    def test_git_autocrlf_checkout_matches_lf_sender_without_changing_old_lf_hash(self):
        self.git('config', 'core.autocrlf', 'true')
        (self.repo / 'app.py').write_bytes(b'value = 1\n')
        # Match the pre-fix LF fingerprint byte for byte, including mode encoding.
        previous = hashlib.sha256()
        previous.update(b'app.py\0')
        previous.update(hashlib.sha256(b'file\x000\0value = 1\n').digest())
        previous.update(b'\0')
        self.assertEqual(core._snapshot(self.repo)['fingerprint'], previous.hexdigest())
        (self.repo / '.gitignore').write_bytes(b'.remvu/\n__pycache__/\n')
        self.git('add', '.gitignore')
        self.git('commit', '-qm', 'LF generated ignore file')
        self.update(note('goal', 'Share code across checkout EOL policies.'))
        document = core.write_document(self.repo, visibility='public')
        receiver = self.root / 'crlf-receiver'
        subprocess.run(['git', 'clone', '-q', '-c', 'core.autocrlf=true', str(self.repo), str(receiver)], check=True)
        self.assertIn(b'\r\n', (receiver / '.gitignore').read_bytes())
        shutil.copy(document['path'], receiver / 'REMVU.md')
        result = core.check_project(receiver, receiver / 'REMVU.md')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['current_snapshot']['fingerprint'], core._snapshot(self.repo)['fingerprint'])

    def test_explicit_git_text_eol_policy_works_without_autocrlf(self):
        self.git('config', 'core.autocrlf', 'false')
        (self.repo / 'app.py').write_bytes(b'value = 1\n')
        (self.repo / '.gitattributes').write_bytes(b'*.txt text eol=crlf\n')
        (self.repo / 'notes.txt').write_bytes(b'line one\nline two\n')
        self.git('add', '.gitattributes', 'notes.txt')
        self.git('commit', '-qm', 'Explicit text checkout policy')
        sender = core._snapshot(self.repo)
        receiver = self.root / 'attribute-receiver'
        subprocess.run(['git', 'clone', '-q', '-c', 'core.autocrlf=false', str(self.repo), str(receiver)], check=True)
        self.assertIn(b'\r\n', (receiver / 'notes.txt').read_bytes())
        self.assertEqual(sender['fingerprint'], core._snapshot(receiver)['fingerprint'])

    def test_binary_untracked_and_explicit_raw_eol_changes_remain_significant(self):
        self.git('config', 'core.autocrlf', 'true')
        (self.repo / '.gitattributes').write_bytes(b'raw.txt -text\n')
        paths = {'binary.bin': b'\0binary\r\nbytes\r\n', 'raw.txt': b'raw\r\ntext\r\n'}
        for name, body in paths.items():
            (self.repo / name).write_bytes(body)
        self.git('add', '.gitattributes', 'binary.bin', 'raw.txt')
        self.git('commit', '-qm', 'Binary and explicitly raw fixtures')
        baseline = core._snapshot(self.repo)['fingerprint']
        for name, body in paths.items():
            with self.subTest(path=name):
                (self.repo / name).write_bytes(body.replace(b'\r\n', b'\n'))
                self.assertNotEqual(core._snapshot(self.repo)['fingerprint'], baseline)
                (self.repo / name).write_bytes(body)
        untracked = self.repo / 'untracked.txt'
        untracked.write_bytes(b'new\r\nlines\r\n')
        with_crlf = core._snapshot(self.repo)['fingerprint']
        untracked.write_bytes(b'new\nlines\n')
        self.assertNotEqual(core._snapshot(self.repo)['fingerprint'], with_crlf)

    def test_tracked_raw_eol_change_is_not_hidden_without_git_conversion_policy(self):
        self.git('config', 'core.autocrlf', 'false')
        (self.repo / 'app.py').write_bytes(b'value = 1\n')
        baseline = core._snapshot(self.repo)['fingerprint']
        (self.repo / 'app.py').write_bytes(b'value = 1\r\n')
        self.assertNotEqual(core._snapshot(self.repo)['fingerprint'], baseline)

    def test_historical_crlf_index_is_preserved_by_automatic_git_text_policy(self):
        self.git('config', 'core.autocrlf', 'false')
        (self.repo / 'app.py').write_bytes(b'value = 1\n')
        (self.repo / 'historical.txt').write_bytes(b'historical\r\ntext\r\n')
        self.git('add', 'historical.txt')
        self.git('commit', '-qm', 'Historically committed CRLF')
        baseline = core._snapshot(self.repo)['fingerprint']
        self.assertIn('i/crlf', self.git('ls-files', '--eol', '--', 'historical.txt'))
        self.git('config', 'core.autocrlf', 'true')
        self.assertEqual(core._snapshot(self.repo)['fingerprint'], baseline)
        attributes = self.repo / '.git/info/attributes'
        for policy in ('*.txt text=auto\n', '*.txt text=auto eol=lf\n'):
            with self.subTest(policy=policy):
                attributes.write_text(policy, encoding='utf-8')
                self.assertEqual(core._snapshot(self.repo)['fingerprint'], baseline)

    def test_remvu_cli_uses_utf8_json_under_legacy_pipe_encoding(self):
        self.update(note('goal', '保留中文和 emoji ✅'))
        script = SCRIPT.with_name('remvu.py')
        process = subprocess.run([sys.executable, str(script), 'status', '--repo', str(self.repo)],
                                 capture_output=True, env={**os.environ, 'PYTHONIOENCODING': 'cp1252'})
        self.assertEqual(process.returncode, 0, process.stderr.decode('utf-8'))
        self.assertIn('保留中文和 emoji ✅', process.stdout.decode('utf-8'))

    def test_legacy_check_without_derived_provenance_remains_historical(self):
        self.update(check())
        with core._lock(self.repo) as root:
            state = core._load_unlocked(root)
            state['entries'][0].pop('observed_code')
            core._save(root, state, 'test-old-state', {})
        self.update(note(id='unrelated'))
        self.assertIn('stale_check_evidence', self.issues())
        self.assertIn('Observed code fingerprint: unknown', core.render_document(self.repo))

    def test_omitted_event_watermark_acknowledges_no_new_evidence(self):
        self.event('event-one')
        reply = self.update(note())
        self.assertTrue(reply['pending_consolidation'])
        self.assertEqual(reply['event_count'], 1)
        self.assertEqual(reply['consolidated_event_count'], 0)
        self.assertEqual(reply['unconsolidated_event_count'], 1)
        with self.assertRaisesRegex(ValueError, 'pending consolidation'):
            core.render_document(self.repo, 'public')

    def test_new_failure_after_proposal_snapshot_stays_pending(self):
        self.event('already-read')
        prepared = {'base_revision': 0, 'base_event_count': 1,
                    'entries': [note('progress', 'Reviewed the first event.') ]}
        self.event('new-failure-after-read')
        result = core.apply_update(self.repo, prepared)
        self.assertTrue(result['ok'])
        self.assertTrue(result['pending_consolidation'])
        self.assertEqual(result['consolidated_event_count'], 1)
        self.assertEqual(result['event_count'], 2)
        final = self.update(base_event_count=2)
        self.assertFalse(final['pending_consolidation'])
        self.assertEqual(final['unconsolidated_event_count'], 0)

    def test_event_watermark_never_regresses_and_invalid_values_do_not_mutate(self):
        self.event('first')
        self.update(base_event_count=1)
        self.event('second')
        for watermark in (None, 0):
            values = {} if watermark is None else {'base_event_count': watermark}
            result = self.update(**values)
            self.assertEqual(result['consolidated_event_count'], 1)
            self.assertTrue(result['pending_consolidation'])
        before = (self.repo / '.remvu/state.json').read_bytes()
        for invalid in (-1, True, '2', 3):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.update(base_event_count=invalid)
            self.assertEqual((self.repo / '.remvu/state.json').read_bytes(), before)

    def test_stale_proposal_does_not_acknowledge_events(self):
        self.event('first')
        self.update(note(id='latest'))
        stale = core.apply_update(self.repo, {'base_revision': 0, 'base_event_count': 1, 'entries': []})
        self.assertFalse(stale['ok'])
        state = core.load_state(self.repo)
        self.assertTrue(state['pending_consolidation'])
        self.assertEqual(state['consolidated_event_count'], 0)

    def test_conflict_resolution_preserves_proposal_and_unblocks_public_share(self):
        conflict_id, original = self.conflict()
        with self.assertRaisesRegex(ValueError, 'unresolved conflicts'):
            core.render_document(self.repo, 'public')
        self.assertIn('UNRESOLVED CONFLICTS', core.render_document(self.repo))
        self.update(note('decision', 'Reviewed and retained the current design.', id='reconciled'))
        resolution = core.resolve_conflict(self.repo, conflict_id, 2,
                                           'Reviewed both proposals; current design remains correct.', ['reconciled'])
        self.assertTrue(resolution['ok'])
        self.assertEqual(resolution['revision'], 3)
        self.assertFalse((self.repo / '.remvu/conflicts' / (conflict_id + '.json')).exists())
        archive = json.loads((self.repo / '.remvu' / resolution['resolution_ref']).read_text())
        self.assertEqual(archive['original_conflict']['proposal'], original)
        self.assertEqual(archive['entry_ids'], ['reconciled'])
        self.assertIn('both proposals', archive['note'])
        self.assertNotIn('unresolved_conflicts', self.issues())
        self.assertTrue(core.validate_document(core.render_document(self.repo, 'public'))['ok'])
        again = core.resolve_conflict(self.repo, conflict_id, 3, 'Repeated explicit resolution.')
        self.assertTrue(again['already_resolved'])
        self.assertEqual(core.load_state(self.repo)['revision'], 3)

    def test_conflict_resolution_requires_current_revision_note_and_known_entries(self):
        conflict_id, _ = self.conflict()
        before = (self.repo / '.remvu/state.json').read_bytes()
        stale = core.resolve_conflict(self.repo, conflict_id, 0, 'Reviewed.')
        self.assertFalse(stale['ok'])
        for kwargs in ({'note': ' '}, {'note': 'Reviewed.', 'entry_ids': ['unknown']},
                       {'note': 'Reviewed.', 'entry_ids': ['accepted', 'accepted']}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                core.resolve_conflict(self.repo, conflict_id, 1, **kwargs)
        self.assertEqual((self.repo / '.remvu/state.json').read_bytes(), before)
        self.assertFalse((self.repo / '.remvu/conflicts/resolved').exists())
        with self.assertRaises(ValueError):
            core.resolve_conflict(self.repo, '../escape', 1, 'Reviewed.')

    def test_damaged_resolution_archive_cannot_hide_a_conflict(self):
        conflict_id, _ = self.conflict()
        reply = core.resolve_conflict(self.repo, conflict_id, 1, 'Rejected stale duplicate.')
        archive = self.repo / '.remvu' / reply['resolution_ref']
        archive.write_text('{}')
        self.assertIn('unresolved_conflicts', self.issues())
        with self.assertRaisesRegex(ValueError, 'unresolved conflicts'):
            core.render_document(self.repo, 'public')

    def test_conflict_resolution_does_not_acknowledge_unreviewed_events(self):
        conflict_id, _ = self.conflict()
        self.event('unreviewed')
        result = core.resolve_conflict(self.repo, conflict_id, 1, 'Rejected stale duplicate.')
        self.assertTrue(result['pending_consolidation'])
        self.assertEqual(core.load_state(self.repo)['consolidated_event_count'], 0)

    def receiver(self):
        receiver = self.root / 'receiver'
        subprocess.run(['git', 'clone', '-q', str(self.repo), str(receiver)], check=True)
        public = self.repo / 'REMVU.md'
        core.write_document(self.repo, visibility='public')
        shutil.copy(public, receiver / 'REMVU.md')
        return receiver

    def test_cold_receiver_check_is_read_only_and_compares_code(self):
        self.update(check())
        receiver = self.receiver()
        self.assertFalse((receiver / '.remvu').exists())
        index_before = (receiver / '.git/index').read_bytes()
        result = core.check_project(receiver, receiver / 'REMVU.md')
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['standalone'])
        self.assertIsNone(result['revision'])
        self.assertFalse((receiver / '.remvu').exists())
        self.assertEqual((receiver / '.git/index').read_bytes(), index_before)
        (receiver / 'app.py').write_text('value = 999\n')
        stale = core.check_project(receiver, receiver / 'REMVU.md')
        self.assertIn('stale_document', [item['code'] for item in stale['issues']])
        self.assertFalse((receiver / '.remvu').exists())
        self.assertEqual((receiver / '.git/index').read_bytes(), index_before)

    def test_cold_invalid_document_and_missing_memory_do_not_create_state(self):
        receiver = self.root / 'empty'
        receiver.mkdir()
        target = receiver / 'REMVU.md'
        target.write_text('invalid document')
        result = core.check_project(receiver, target)
        self.assertIn('invalid_document', [item['code'] for item in result['issues']])
        self.assertFalse(core.check_project(receiver)['ok'])
        self.assertFalse((receiver / '.remvu').exists())

    def test_validator_checks_every_metadata_type_without_raising(self):
        document = core.render_document(self.repo)
        cases = [('format', []), ('project_id', 2), ('revision', True), ('repo', []),
                 ('generated_at', 0), ('visibility', {}), ('summary_chars', True),
                 ('omitted_private_entries', 0.5)]
        for key, value in cases:
            with self.subTest(key=key):
                candidate = self.replace_metadata(document, lambda m: m.update({key: value}))
                self.assertFalse(core.validate_document(candidate)['ok'])
        for key, value in [('name', []), ('remote', {}), ('commit', 9), ('tree', []),
                           ('fingerprint', False), ('dirty', 0), ('git', None)]:
            with self.subTest(repo_key=key):
                candidate = self.replace_metadata(document, lambda m: m['repo'].update({key: value}))
                self.assertFalse(core.validate_document(candidate)['ok'])

    def test_validator_rejects_unknown_or_missing_metadata_fields(self):
        document = core.render_document(self.repo)
        for mutate in (lambda m: m.update(extra=True), lambda m: m['repo'].update(extra=True),
                       lambda m: m.pop('visibility'), lambda m: m['repo'].pop('git')):
            self.assertFalse(core.validate_document(self.replace_metadata(document, mutate))['ok'])
        null = document.split('```json\n', 1)[0] + '```json\nnull\n```' + document.split('\n```', 1)[1]
        self.assertFalse(core.validate_document(null)['ok'])

    def test_validator_requires_real_timezone_aware_timestamp(self):
        document = core.render_document(self.repo)
        for timestamp in ('2026-10-17T12:00:00', '2026-10-17', '2026-10-17T12:00:00+05:99',
                          '2026-02-31T12:00:00Z', '2026-10-17T12:00:00+24:00'):
            with self.subTest(timestamp=timestamp):
                candidate = self.replace_metadata(document, lambda m: m.update(generated_at=timestamp))
                self.assertFalse(core.validate_document(candidate)['ok'])
        candidate = self.replace_metadata(document, lambda m: m.update(generated_at='2026-10-17T20:00:00+08:00'))
        self.assertTrue(core.validate_document(candidate)['ok'])

    def test_validator_ignores_fenced_headings_and_rejects_unknown_root_headings(self):
        document = core.render_document(self.repo)
        fenced = document + '\n## Patch\n\n~~~~diff\n## Unexpected\n## Goals\n```\n~~~~\n'
        self.assertTrue(core.validate_document(fenced)['ok'], core.validate_document(fenced))
        for addition in ('## Unknown\n', '  ## Unknown\n', '## Goals\n'):
            candidate = document + '\n' + addition
            self.assertFalse(core.validate_document(candidate)['ok'])
        middle_patch = document.replace('## Goals', '## Patch\n\n## Goals', 1)
        self.assertFalse(core.validate_document(middle_patch)['ok'])
        self.assertFalse(core.validate_document(document + '\n```diff\nunclosed')['ok'])

    def test_validator_checks_actual_summary_char_count(self):
        document = core.render_document(self.repo)
        changed = document.replace('## Start Here\n\n', '## Start Here\n\nExtra uncounted text. ', 1)
        result = core.validate_document(changed)
        self.assertFalse(result['ok'])
        self.assertTrue(any('summary_chars' in error for error in result['errors']))

    def test_rendered_user_headings_are_inert_with_strict_validation(self):
        self.update(note('goal', 'User text\n## Unknown\n## Goals\n```json\n{}\n```'))
        document = core.render_document(self.repo)
        self.assertTrue(core.validate_document(document)['ok'])
        self.assertIn('\\#\\# Unknown', document)


if __name__ == '__main__':
    unittest.main()
