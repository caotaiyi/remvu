import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/agent-task-export/scripts/task_export.py'
spec = importlib.util.spec_from_file_location('task_export', SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def response(kind, **kwargs):
    return {'type': 'response_item', 'payload': {'type': kind, **kwargs}}


def message(role, text, **kwargs):
    return response('message', role=role, content=[{'type': 'input_text' if role == 'user' else 'output_text', 'text': text}], **kwargs)


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / 'source.jsonl'
        self.bundle = self.root / 'bundle'

    def tearDown(self):
        self.tmp.cleanup()

    def source(self, rows):
        self.src.write_text(''.join(json.dumps(r) + '\n' for r in rows))

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], text=True,
                                encoding='utf-8', capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def export(self, *args, ok=True):
        return self.cli('export', '--source', self.src, '--out', self.bundle, *args, ok=ok)

    def read(self, name):
        return json.loads((self.bundle / name).read_text())

    def test_excludes_private_data_and_unknown_formats(self):
        self.source([
            {'type': 'session_meta', 'payload': {'base_instructions': 'HIDDEN_SYSTEM'}},
            response('reasoning', summary='HIDDEN_REASONING', encrypted_content='HIDDEN_CIPHER'),
            message('system', 'HIDDEN_SYSTEM_2'), message('developer', 'HIDDEN_DEVELOPER'),
            message('assistant', 'HIDDEN_ANALYSIS', channel='analysis'),
            {'type': 'mystery', 'payload': {'text': 'UNKNOWN_BODY'}},
            message('user', 'Fix a bug'), message('assistant', 'Done', phase='final'),
        ])
        self.export()
        all_text = ''.join(p.read_text() for p in self.bundle.rglob('*') if p.is_file())
        for marker in ('HIDDEN_SYSTEM', 'HIDDEN_REASONING', 'HIDDEN_CIPHER', 'HIDDEN_DEVELOPER', 'HIDDEN_ANALYSIS', 'UNKNOWN_BODY'):
            self.assertNotIn(marker, all_text)
        self.assertEqual(self.read('coverage.json')['counts']['events'], 2)
        self.cli('verify', self.bundle)

    def test_redaction_and_deduplication_preserve_full_output(self):
        body = 'API_KEY="sample-secret-value"\nAuthorization: Bearer abcdefghijklmnop\n' + 'long text ' * 2000
        self.source([response('function_call', call_id='c1', name='test', arguments={'password': 'P4SS', 'analysis': 'PRIVATE', 'cmd': 'check'}),
                     response('function_call_output', call_id='c1', output=body),
                     response('custom_tool_call_output', call_id='c2', output=body)])
        self.export()
        shown = json.loads(self.cli('show', self.bundle, '--event', 'e000002', '--max-chars', '80').stdout)
        self.assertTrue(shown['output_truncated_for_display'])
        blob = (self.bundle / shown['output_ref']).read_text()
        self.assertNotIn('sample-secret-value', blob); self.assertNotIn('abcdefghijklmnop', blob)
        self.assertEqual(blob.count('long text '), 2000)
        self.assertEqual(self.read('manifest.json')['storage']['unique_blobs'], 2)
        args = json.loads(self.cli('show', self.bundle, '--event', 'e000001').stdout)['arguments']
        self.assertNotIn('P4SS', args); self.assertNotIn('PRIVATE', args)
        self.assertEqual(self.read('coverage.json')['unpaired_or_ambiguous_calls'], 1)

    def test_pending_duplicate_and_orphan_calls(self):
        self.source([response('function_call', name='test', call_id='same', arguments='a'),
                     response('function_call', name='test', call_id='same', arguments='b'),
                     response('function_call_output', call_id='same', output='ok'),
                     response('function_call', name='pending', arguments='no-id'),
                     response('function_call_output', call_id='orphan', output='ok')])
        self.export()
        c = self.read('coverage.json')
        self.assertEqual(c['unpaired_or_ambiguous_calls'], 2)
        self.assertEqual(c['tool_calls_without_id'], 1)

    def test_malformed_partial_line_and_non_object(self):
        self.source([message('user', 'good')])
        with self.src.open('a') as f:
            f.write('not json\n[]\n{"partial":')
        self.export()
        self.assertEqual(self.read('coverage.json')['counts']['malformed_lines'], 3)

    def test_last_turn_and_line_range(self):
        self.source([{'type': 'event_msg', 'payload': {'type': 'task_started'}}, message('user', 'old'),
                     {'type': 'event_msg', 'payload': {'type': 'task_started'}}, message('user', 'new')])
        self.export('--last-turn')
        self.assertEqual(self.read('coverage.json')['start_line'], 3)
        self.assertEqual(self.read('coverage.json')['counts']['events'], 1)
        self.assertIn('new', self.cli('show', self.bundle, '--event', 'e000001').stdout)
        self.cli('export', '--source', self.src, '--out', self.root / 'range', '--start-line', '2', '--end-line', '2')
        c = json.loads((self.root / 'range/coverage.json').read_text())
        self.assertEqual(c['counts']['events'], 1)

    def test_missing_boundary_fails_without_output(self):
        self.source([message('user', 'x')])
        self.export('--last-turn', ok=False)
        self.assertFalse(self.bundle.exists())

    def test_generic_evidence_and_patch_inventory(self):
        self.source([{'format': 'agent-task-evidence/v1', 'kind': 'decision', 'summary': 'Use SQLite', 'evidence': ['e000002']},
                     response('custom_tool_call', name='apply_patch', call_id='p', input='*** Begin Patch\n*** Update File: src/app.py\n@@\n-x\n+y\n*** End Patch'),
                     response('custom_tool_call_output', call_id='p', output='success'),
                     {'format': 'agent-task-evidence/v1', 'kind': 'message', 'role': 'system', 'text': 'PRIVATE'}])
        self.export()
        edit = self.read('index.json')['edits'][0]
        self.assertEqual(edit['path'], 'src/app.py'); self.assertEqual(edit['event'], 'e000002')
        self.assertIn('attempted', edit['status'])
        self.assertEqual(self.read('coverage.json')['counts']['events'], 3)

    def test_codex_exec_events(self):
        self.source([{'type': 'item.started', 'item': {'type': 'command_execution', 'id': 'i1', 'command': 'test'}},
                     {'type': 'item.completed', 'item': {'type': 'command_execution', 'id': 'i1', 'exit_code': 7, 'aggregated_output': 'failed'}},
                     {'type': 'item.completed', 'item': {'type': 'file_change', 'changes': [{'path': 'a.py', 'kind': 'update'}], 'status': 'completed'}},
                     {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'Check failed'}},
                     {'type': 'item.completed', 'item': {'type': 'reasoning', 'text': 'PRIVATE'}}])
        self.export()
        self.assertEqual(self.read('index.json')['calls'][0]['status'], 'paired')
        value = json.loads(self.cli('show', self.bundle, '--event', 'e000002').stdout)
        self.assertEqual(json.loads(value['output'])['exit_code'], 7)
        self.assertEqual(self.read('coverage.json')['counts']['events'], 4)

    def test_summary_budget_failure_is_atomic(self):
        self.source([message('user', 'goal')])
        task = self.root / 'task.json'; task.write_text(json.dumps({'goal': 'x' * 9000}))
        self.export('--task', task, ok=False)
        self.assertFalse(self.bundle.exists())
        self.assertEqual(list(self.root.glob('.task-export-*')), [])

    def test_summary_is_redacted(self):
        self.source([message('user', 'goal')])
        task = self.root / 'task.json'; task.write_text(json.dumps({'goal': 'ship', 'checks': ['e000001: tests passed'], 'risks': ['token=ordinary'], 'next_steps': ['Review']}))
        self.export('--task', task)
        self.assertIn('e000001: tests passed', (self.bundle / 'START_HERE.md').read_text())

    def test_integrity_and_zip_inventory(self):
        self.source([message('user', 'hi')]); self.export()
        self.cli('verify', self.bundle)
        archive = self.root / 'bundle.zip'
        self.cli('archive', self.bundle, '--out', archive)
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(set(z.namelist()), set(self.read('manifest.json')['files']) | {'manifest.json'})
        (self.bundle / 'events.jsonl').write_text('tampered\n')
        self.cli('verify', self.bundle, ok=False)
        self.cli('archive', self.bundle, '--out', self.root / 'bad.zip', ok=False)
        self.assertFalse((self.root / 'bad.zip').exists())

    def test_rejects_traversal_symlink_and_extra_files(self):
        self.source([message('user', 'hi')]); self.export()
        manifest = self.read('manifest.json'); manifest['files']['../escape'] = {'sha256': '', 'bytes': 0}
        (self.bundle / 'manifest.json').write_text(json.dumps(manifest))
        self.cli('verify', self.bundle, ok=False)
        manifest['files'].pop('../escape'); (self.bundle / 'manifest.json').write_text(json.dumps(manifest))
        (self.bundle / 'extra.txt').write_text('extra'); self.cli('verify', self.bundle, ok=False)
        (self.bundle / 'extra.txt').unlink()
        original = self.bundle / 'START_HERE.md'; moved = self.root / 'outside'; original.rename(moved); original.symlink_to(moved)
        self.cli('verify', self.bundle, ok=False)

    def test_existing_output_is_preserved(self):
        self.source([message('user', 'hi')]); self.export()
        first = (self.bundle / 'manifest.json').read_bytes()
        self.export(ok=False)
        self.assertEqual(first, (self.bundle / 'manifest.json').read_bytes())

    def test_discovery_filters_metadata_only(self):
        self.src = self.root / 'rollout-session-123.jsonl'
        self.source([{'type': 'session_meta', 'payload': {'id': 'session-123', 'cwd': str(self.root), 'base_instructions': 'PRIVATE'}}, message('user', 'TRANSCRIPT')])
        result = self.cli('discover', '--root', self.root, '--cwd', self.root, '--session-id', 'session-123')
        self.assertEqual(json.loads(result.stdout)['matches'], 1)
        self.assertNotIn('TRANSCRIPT', result.stdout); self.assertNotIn('PRIVATE', result.stdout)

    def test_git_snapshot_base_includes_committed_changes_and_untracked_names(self):
        repo = self.root / 'repo'; repo.mkdir()
        def git(*args):
            return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
        git('init', '-q'); git('config', 'user.name', 'Test'); git('config', 'user.email', 'test@example.invalid')
        f = repo / 'app.txt'; f.write_text('before\n'); git('add', '.'); git('commit', '-qm', 'baseline')
        base = git('rev-parse', 'HEAD')
        f.write_text('after\n'); git('commit', '-qam', 'change')
        private = repo / '.env'; private.write_text('NEVER_COPY_THIS')
        self.source([message('user', 'change')]); self.export('--repo', repo, '--base', base)
        snapshot = self.read('git/snapshot.json')
        self.assertEqual(snapshot['base_commit'], base)
        self.assertIn('+after', (self.bundle / 'git/changes.diff').read_text())
        self.assertIn('.env', [x['path'] for x in snapshot['status']])
        all_text = ''.join(p.read_text() for p in self.bundle.rglob('*') if p.is_file())
        self.assertNotIn('NEVER_COPY_THIS', all_text)

    def test_unicode_index_reads_exact_event(self):
        self.source([message('user', '导出刚才的任务 🧪'), message('assistant', '保留中文和 emoji ✅')])
        self.export()
        record = json.loads(self.cli('show', self.bundle, '--event', 'e000002').stdout)
        self.assertEqual(record['text'], '保留中文和 emoji ✅')
        self.assertEqual(self.read('coverage.json')['counts']['malformed_lines'], 0)

    def test_unicode_output_is_utf8_even_when_host_pipes_use_cp1252(self):
        self.source([message('assistant', '中文和 emoji ✅')])
        self.export()
        for script in (SCRIPT, SCRIPT.parents[2] / 'remvu/scripts/legacy_export.py'):
            process = subprocess.run([sys.executable, str(script), 'show', str(self.bundle),
                                      '--event', 'e000001'], capture_output=True,
                                     env={**os.environ, 'PYTHONIOENCODING': 'cp1252'})
            self.assertEqual(process.returncode, 0, process.stderr.decode('utf-8'))
            self.assertEqual(json.loads(process.stdout.decode('utf-8'))['text'], '中文和 emoji ✅')

    def test_archive_refuses_destination_inside_bundle(self):
        self.source([message('user', 'hi')]); self.export()
        self.cli('archive', self.bundle, '--out', self.bundle / 'nested.zip', ok=False)
        self.cli('verify', self.bundle)

    def test_secret_patterns(self):
        values = ["password='test-value'", 'ghp_' + 'a' * 36, 'github_pat_' + 'a' * 25,
                  '--token dummy-value', 'https://user:pass@example.invalid',
                  '-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----']
        for value in values:
            self.assertNotEqual(value, mod.scrub(value))


if __name__ == '__main__':
    unittest.main()
