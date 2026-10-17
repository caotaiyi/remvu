import base64
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/remvu/scripts'
sys.path.insert(0, str(SCRIPTS))
import remvu_hooks as hooks
import remvu_init as setup
import remvu_core as core


class AdapterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="remvu spaces $' ")
        self.root = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def initialize(self, platforms=('claude', 'codex')):
        return setup.initialize(self.root, platforms, SCRIPTS)

    def payload(self, event, **fields):
        return {'session_id': 'session-one', 'cwd': str(self.root), 'permission_mode': 'default',
                'hook_event_name': event, **fields}

    def call(self, event, platform='codex', **fields):
        return hooks.run_hook(platform, event, self.payload(event, **fields), self.root)

    def tool(self, call_id='call-one', **fields):
        return self.call('PostToolUse', turn_id='turn-one', tool_use_id=call_id,
                         tool_name='Bash', tool_input={'command': 'python -m unittest'},
                         tool_response={'exit_code': 1, 'stdout': 'FAILED'}, **fields)

    def state(self):
        return core.load_state(self.root)

    def test_existing_config_and_instructions_survive_idempotent_setup(self):
        (self.root / '.claude').mkdir()
        original = {'env': {'CUSTOM': 'keep'}, 'hooks': {'Stop': [{'matcher': '', 'hooks': [
            {'type': 'command', 'command': 'echo keep'}]}]}}
        config = self.root / '.claude/settings.local.json'
        config.write_text(json.dumps(original))
        (self.root / 'AGENTS.md').write_text('Existing project rules.\n')
        first = self.initialize()
        saved = {p: (self.root / p).read_text() for p in first['changed']}
        second = self.initialize()
        self.assertEqual(second['changed'], [])
        for path, text in saved.items():
            self.assertEqual((self.root / path).read_text(), text)
        merged = json.loads(config.read_text())
        self.assertEqual(merged['env'], original['env'])
        self.assertEqual(merged['hooks']['Stop'][0]['hooks'][0]['command'], 'echo keep')
        self.assertEqual(len(merged['hooks']['Stop']), 2)
        self.assertIn('Existing project rules.', (self.root / 'AGENTS.md').read_text())
        self.assertEqual((self.root / 'AGENTS.md').read_text().count(setup.BEGIN), 1)
        self.assertTrue(first['trust_required'])
        self.assertTrue(first['backups'])
        for backup in first['backups']:
            self.assertTrue((self.root / backup).is_file())
        self.assertNotIn('bypass', json.dumps(merged))

    def test_setup_preserves_other_handlers_in_a_shared_group(self):
        (self.root / '.codex').mkdir()
        target = self.root / '.codex/hooks.json'
        target.write_text(json.dumps({'hooks': {'Stop': [{'matcher': '*', 'hooks': [
            {'type': 'command', 'command': 'python /old/remvu_hooks.py --platform codex --event Stop'},
            {'type': 'command', 'command': 'echo keep'}]}]}}))
        self.initialize(('codex',))
        groups = json.loads(target.read_text())['hooks']['Stop']
        self.assertEqual(groups[0]['hooks'], [{'type': 'command', 'command': 'echo keep'}])
        self.assertEqual(len(groups), 2)

    def test_invalid_config_preflight_changes_nothing(self):
        (self.root / '.codex').mkdir()
        target = self.root / '.codex/hooks.json'
        target.write_text('{broken')
        with self.assertRaises(ValueError):
            self.initialize()
        self.assertEqual(target.read_text(), '{broken')
        self.assertFalse((self.root / 'CLAUDE.md').exists())
        self.assertFalse((self.root / '.remvu').exists())

    def test_unrelated_skill_is_not_overwritten(self):
        target = self.root / '.claude/skills/remvu/SKILL.md'
        target.parent.mkdir(parents=True)
        target.write_text('user owned skill')
        with self.assertRaises(ValueError):
            self.initialize()
        self.assertEqual(target.read_text(), 'user owned skill')
        self.assertFalse((self.root / '.remvu').exists())

    def test_core_unavailable_setup_refuses_without_writes(self):
        with patch.object(setup, '_core', side_effect=ImportError('missing core')):
            with self.assertRaisesRegex(ValueError, 'unavailable'):
                self.initialize()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_missing_runtime_refuses_without_writes(self):
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            setup.initialize(self.root, scripts_dir=self.root)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_exact_private_ignores_and_skill_shims(self):
        self.initialize()
        self.initialize(('codex',))
        ignored = (self.root / '.gitignore').read_text()
        for path in ('/.remvu/', '/.claude/settings.local.json', '/.codex/hooks.json',
                     '/.claude/skills/remvu/', '/.agents/skills/remvu/'):
            self.assertIn(path, ignored)
        self.assertNotIn('\n/.agents/\n', ignored)
        for platform in ('.claude', '.agents'):
            self.assertIn(str(SCRIPTS), (self.root / platform / 'skills/remvu/SKILL.md').read_text())

    def test_path_quoting_and_exec_form(self):
        self.initialize()
        claude = json.loads((self.root / '.claude/settings.local.json').read_text())['hooks']['Stop'][0]['hooks'][0]
        self.assertEqual(claude['command'], str(Path(sys.executable).resolve()))
        self.assertIn(str(self.root), claude['args'])
        codex = json.loads((self.root / '.codex/hooks.json').read_text())['hooks']['Stop'][0]['hooks'][0]
        self.assertEqual(shlex.split(codex['command'])[-1], str(self.root))
        encoded = codex['commandWindows'].split()[-1]
        windows = base64.b64decode(encoded).decode('utf-16le')
        self.assertIn(str(self.root).replace("'", "''"), windows)
        self.assertNotIn('ExecutionPolicy', codex['commandWindows'])
        # Exercise the actual shell-form command from a path containing shell metacharacters.
        result = subprocess.run(codex['command'], input=json.dumps(self.payload('Stop')),
                                shell=True, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsInstance(json.loads(result.stdout), dict)

    def test_tool_dedup_and_bounded_stop(self):
        self.initialize(())
        self.tool()
        self.tool()
        self.assertEqual(len(self.state()['events']), 1)
        first = self.call('Stop', turn_id='turn-one')
        self.assertEqual(first['decision'], 'block')
        self.assertIn(hooks.FLUSH_MARKER, first['reason'])
        self.assertEqual(self.call('Stop', turn_id='turn-one'), {})
        self.assertEqual(self.call('Stop', turn_id='another', stop_hook_active=True), {})
        self.assertTrue(self.state()['pending_consolidation'])

    def test_tool_attempt_survives_interruption_and_pairs_by_call_id(self):
        self.initialize(())
        fields = {'turn_id': 'interrupted-turn', 'tool_use_id': 'interrupted-call',
                  'tool_name': 'Bash', 'tool_input': {'command': 'long-running-check'}}
        self.assertEqual(self.call('PreToolUse', **fields), {})
        self.assertEqual(self.call('PreToolUse', **fields), {})
        self.call('Interrupt', turn_id='interrupted-turn')
        state = self.state()
        self.assertTrue(state['pending_consolidation'])
        self.assertEqual(len(state['events']), 1)
        attempt = json.loads((self.root / '.remvu' / state['events'][0]['blob_ref']).read_text())
        self.assertEqual(attempt['kind'], 'tool_call')
        self.assertEqual(attempt['call_id'], 'interrupted-call')
        self.assertNotIn('output', attempt)
        self.assertEqual(attempt['turn_id'], 'interrupted-turn')
        self.call('PostToolUse', tool_response={'exit_code': 0}, **fields)
        state = self.state()
        result = json.loads((self.root / '.remvu' / state['events'][1]['blob_ref']).read_text())
        self.assertEqual(result['kind'], 'tool_result')
        self.assertEqual(result['call_id'], attempt['call_id'])

    def test_continuation_prompt_cannot_restart_flush_loop(self):
        self.initialize(())
        self.tool()
        first = self.call('Stop', turn_id='turn-one')
        self.call('UserPromptSubmit', turn_id='continued-turn', prompt=first['reason'])
        self.assertEqual(self.call('Stop', turn_id='continued-turn'), {})
        self.assertEqual(len(self.state()['events']), 1)

    def test_claude_identical_prompt_retry_and_new_user_turn(self):
        self.initialize(())
        self.call('UserPromptSubmit', platform='claude', prompt='Same task')
        self.call('UserPromptSubmit', platform='claude', prompt='Same task')
        self.assertEqual(len(self.state()['events']), 1)
        self.assertEqual(self.call('Stop', platform='claude')['decision'], 'block')
        self.assertEqual(self.call('Stop', platform='claude'), {})
        self.call('UserPromptSubmit', platform='claude', prompt='Same task')
        self.assertEqual(len(self.state()['events']), 2)
        self.assertEqual(self.call('Stop', platform='claude')['decision'], 'block')

    def test_plan_mode_preserves_pending_without_any_hook_write(self):
        self.initialize(())
        self.tool()
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = self.call('Stop', turn_id='plan', permission_mode='plan')
        self.assertIn('deferred', result['systemMessage'])
        self.call('PostToolUse', permission_mode='plan', tool_name='Write', tool_input={'file_path': 'main.py'})
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_bookkeeping_does_not_create_new_pending_events(self):
        self.initialize(())
        self.call('PostToolUse', tool_name='Write', tool_input={'file_path': str(self.root / '.remvu/proposal.json')})
        self.call('PostToolUse', tool_name='Bash', tool_input={
            'command': shlex.join([sys.executable, str(SCRIPTS / 'remvu.py'), 'update', '--proposal', '.remvu/proposal.json'])})
        for verb in ('events', 'show'):
            self.call('PreToolUse', tool_name='Bash', tool_input={
                'command': shlex.join([sys.executable, str(SCRIPTS / 'remvu.py'), verb, 'e-example'])})
        self.assertFalse(self.state()['pending_consolidation'])
        self.assertEqual(self.state()['events'], [])
        self.call('PostToolUse', tool_name='Bash', tool_input={
            'command': f'python {SCRIPTS}/remvu.py status; python real_work.py'})
        self.assertTrue(self.state()['pending_consolidation'])

    def test_existing_tracked_private_config_produces_a_warning(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        target = self.root / '.codex/hooks.json'
        target.parent.mkdir()
        target.write_text('{}')
        subprocess.run(['git', '-C', str(self.root), 'add', '.codex/hooks.json'], check=True)
        result = self.initialize(('codex',))
        self.assertTrue(any('already tracks' in warning for warning in result['warnings']))
        tracked = subprocess.run(['git', '-C', str(self.root), 'ls-files', '.codex/hooks.json'],
                                 text=True, capture_output=True, check=True)
        self.assertEqual(tracked.stdout.strip(), '.codex/hooks.json')

    def test_lifecycle_boundaries_never_claim_semantic_refresh(self):
        self.initialize(())
        self.call('SessionEnd')
        self.assertFalse(self.state()['pending_consolidation'])
        self.tool()
        self.call('PreCompact', turn_id='turn-one')
        self.call('Interrupt', turn_id='turn-one')
        self.assertTrue(self.state()['pending_consolidation'])
        ledger = json.loads((self.root / '.remvu/hooks/state.json').read_text())
        session = next(iter(ledger['sessions'].values()))
        self.assertEqual(session['last_boundary']['event'], 'Interrupt')
        self.assertTrue(session['last_boundary']['pending_consolidation'])

    def test_failure_is_observable_and_hidden_fields_are_excluded(self):
        self.initialize(())
        self.call('PostToolUseFailure', platform='claude', tool_name='Bash', tool_use_id='failed',
                  tool_input={'command': 'check', 'analysis': 'HIDDEN_INPUT'},
                  error={'message': 'test failed', 'reasoning': 'HIDDEN_RESULT'},
                  reasoning='HIDDEN_TOP', transcript_path='/do/not/read/transcript')
        content = ''.join(path.read_text() for path in (self.root / '.remvu').rglob('*.json'))
        self.assertNotIn('HIDDEN_', content)
        self.assertNotIn('/do/not/read', content)
        self.assertIn('failed', content)
        self.assertEqual(len(self.state()['events']), 1)

    def test_structured_reasoning_nodes_and_signatures_are_not_stored(self):
        self.initialize(())
        self.call('PostToolUse', tool_name='mcp__example__read', tool_use_id='structured', tool_input={},
                  tool_response={'content': [
                      {'type': 'redacted_thinking', 'data': 'PRIVATE_ENCRYPTED', 'signature': 'PRIVATE_SIGNATURE'},
                      {'type': 'thinking', 'thinking': 'PRIVATE_THOUGHT'},
                      {'type': 'analysis', 'data': 'PRIVATE_ANALYSIS'},
                      {'type': 'text', 'text': 'Visible test result', 'signature': 'PRIVATE_SIGNATURE_2'},
                      {'role': 'developer', 'content': 'PRIVATE_DEVELOPER'},
                  ]})
        content = ''.join(path.read_text() for path in (self.root / '.remvu').rglob('*.json'))
        self.assertNotIn('PRIVATE_', content)
        self.assertIn('Visible test result', content)

    def test_invalid_stdin_is_advisory_json(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'remvu_hooks.py'), '--platform', 'codex',
                                 '--event', 'Stop', '--repo', str(self.root)], input='{bad',
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Invalid JSON', json.loads(result.stdout)['systemMessage'])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_missing_core_hook_has_readable_fallback(self):
        self.initialize(())
        before = (self.root / '.remvu/state.json').read_bytes()
        with patch.object(hooks, '_core', side_effect=ImportError('missing core')):
            result = self.call('Stop')
        self.assertIn('No semantic refresh', result['systemMessage'])
        self.assertEqual((self.root / '.remvu/state.json').read_bytes(), before)

    def test_damaged_hook_ledger_is_preserved(self):
        self.initialize(())
        target = self.root / '.remvu/hooks/state.json'
        target.parent.mkdir()
        target.write_text('{broken')
        result = self.call('Stop')
        self.assertIn('damaged', result['systemMessage'])
        self.assertEqual(target.read_text(), '{broken')

    def test_session_start_uses_summary_and_rejects_stale_memory(self):
        self.initialize(())
        update = {'base_revision': 0, 'entries': [
            {'kind': 'constraint', 'text': 'KEEP THE PUBLIC API STABLE', 'basis': 'user_confirmed',
             'sources': [{'type': 'user', 'excerpt': 'Keep the public API stable.'}]}]}
        self.assertTrue(core.apply_update(self.root, update)['ok'])
        core.write_document(self.root)
        reply = self.call('SessionStart', permission_mode='plan')
        text = reply['hookSpecificOutput']['additionalContext']
        self.assertIn('KEEP THE PUBLIC API STABLE', text)
        self.assertLessEqual(len(text), 8000)
        self.assertNotIn('## Sources and History', text)
        core.apply_update(self.root, {'base_revision': 1, 'entries': [
            {'kind': 'next_step', 'text': 'Add a focused regression check.', 'basis': 'inferred'}]})
        stale = self.call('SessionStart')['hookSpecificOutput']['additionalContext']
        self.assertIn('another memory revision', stale)
        self.assertNotIn('KEEP THE PUBLIC API STABLE', stale)

    def test_successful_semantic_update_satisfies_stop(self):
        self.initialize(())
        self.tool()
        result = core.apply_update(self.root, {'base_revision': 0, 'base_event_count': len(self.state()['events']), 'entries': [
            {'kind': 'progress', 'text': 'Focused check failed; work remains.', 'basis': 'observed',
             'sources': [{'type': 'tool', 'excerpt': 'FAILED; exit code 1'}]}]})
        self.assertTrue(result['ok'])
        self.assertEqual(self.call('Stop', turn_id='turn-one'), {})
        self.assertFalse(self.state()['pending_consolidation'])

    def test_parallel_hook_processes_keep_all_distinct_events(self):
        self.initialize(())
        processes = []
        for index in range(6):
            payload = self.payload('PostToolUse', turn_id='parallel-turn', tool_name='Write',
                                   tool_use_id='parallel-' + str(index),
                                   tool_input={'file_path': 'file-' + str(index) + '.py'},
                                   tool_response={'type': 'create'})
            process = subprocess.Popen([sys.executable, str(SCRIPTS / 'remvu_hooks.py'), '--platform', 'codex',
                                        '--event', 'PostToolUse', '--repo', str(self.root)],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process.stdin.write(json.dumps(payload))
            process.stdin.close()
            processes.append(process)
        for process in processes:
            result = json.loads(process.stdout.read())
            error = process.stderr.read()
            self.assertEqual(process.wait(timeout=10), 0, error)
            self.assertEqual(result, {}, result)
            process.stdout.close()
            process.stderr.close()
        self.assertEqual(len(self.state()['events']), 6)

    @unittest.skipIf(os.name == 'nt', 'Symlink fixture needs POSIX permissions')
    def test_symlinked_hook_lock_is_refused_without_external_write(self):
        self.initialize(())
        outside = self.root / 'outside.txt'
        outside.write_text('unchanged')
        directory = self.root / '.remvu/hooks'
        directory.mkdir()
        (directory / '.lock').symlink_to(outside)
        result = self.call('Stop')
        self.assertIn('symlink', result['systemMessage'])
        self.assertEqual(outside.read_text(), 'unchanged')

    @unittest.skipIf(os.name == 'nt', 'Symlink fixture needs POSIX permissions')
    def test_symlinked_config_destination_is_refused(self):
        external = self.root / 'external'
        external.mkdir()
        (self.root / '.claude').symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.initialize()
        self.assertEqual(list(external.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
