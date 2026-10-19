"""Bookkeeping exclusions must never hide unrelated tool work."""
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/remvu/scripts'
sys.path.insert(0, str(SCRIPTS))
import remvu_hooks as hooks
import remvu_core as core


class HookClassificationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='remvu-hook-classification-')
        self.repo = Path(self.tmp.name).resolve()
        (self.repo / '.remvu').mkdir()
        self.script = SCRIPTS / 'remvu.py'

    def tearDown(self):
        self.tmp.cleanup()

    def classified(self, command, tool='Bash', **args):
        return hooks._memory_only({'tool_name': tool, 'tool_input': {'command': command, **args}}, self.repo)

    def python_call(self, *arguments):
        return shlex.join([sys.executable, str(self.script), *arguments])

    def test_exact_installed_direct_call_and_python_invocation_are_bookkeeping(self):
        expected = os.name != 'nt'
        for action in ('status', 'entries', 'events', 'show', 'check', 'handoff', 'share', 'resolve-conflict', 'withhold'):
            with self.subTest(action=action):
                self.assertEqual(self.classified(self.python_call(action)), expected)
                self.assertEqual(self.classified(shlex.join([str(self.script), action])), expected)

    @unittest.skipIf(os.name == 'nt', 'POSIX literal command parsing')
    def test_frozen_save_exclusion_preserves_mixed_real_work(self):
        executable = self.repo / 'installed app/remvu'
        executable.parent.mkdir()
        executable.write_text('fixture')
        with patch.object(hooks.runtime, 'frozen', return_value=True), patch.object(hooks.runtime, 'scripts_dir', return_value=SCRIPTS), patch.object(hooks.sys, 'executable', str(executable)):
            self.assertTrue(self.classified(shlex.join([str(executable), 'save'])))
            self.assertTrue(self.classified(shlex.join([str(executable), 'resume'])))
            self.assertFalse(self.classified(shlex.join([str(executable), 'save']) + ' && change-project'))
            self.assertFalse(self.classified(shlex.join([str(self.repo / 'other/remvu'), 'save'])))

    def test_standalone_inline_update_accepts_literal_shell_characters_in_json(self):
        proposal = json.dumps({'base_revision': 0, 'base_event_count': 0, 'entries': [
            {'kind': 'goal', 'basis': 'user_confirmed', 'text': 'Keep ; | && > and $(literal) `literal` as evidence.'}]})
        self.assertEqual(self.classified(self.python_call('update', '--repo', str(self.repo), '--proposal-json', proposal)), os.name != 'nt')
        self.assertEqual(self.classified(self.python_call('update', '--proposal-json', proposal) + ' --repo "$PWD"'), os.name != 'nt')

    def test_only_installed_script_in_command_position_is_excluded(self):
        other = self.repo / 'remvu.py'
        other.write_text('print("unrelated script")\n')
        cases = [shlex.join([sys.executable, str(other), 'status']),
                 shlex.join([sys.executable, '-c', 'print("real work")', str(self.script), 'status']),
                 shlex.join([sys.executable, '-m', 'other_module', str(self.script), 'status']),
                 shlex.join(['echo', str(self.script), 'status']),
                 shlex.join(['env', sys.executable, str(self.script), 'status']),
                 shlex.join([str(self.repo / 'python3'), str(self.script), 'status'])]
        for command in cases:
            with self.subTest(command=command):
                self.assertFalse(self.classified(command))

    def test_compound_commands_and_substitutions_are_recorded(self):
        call = self.python_call('status')
        cases = [call + '; python3 real_work.py', call + ' && python3 real_work.py',
                 call + '\npython3 real_work.py', call + ' | cat', call + ' > output.txt',
                 call + ' --repo "$(python3 real_work.py)"',
                 call + ' --repo "`python3 real_work.py`"',
                 call + ' --repo <(python3 real_work.py)']
        for command in cases:
            with self.subTest(command=command):
                self.assertFalse(self.classified(command))

    def test_private_path_exclusion_requires_a_known_file_tool(self):
        for tool in ('Read', 'Edit', 'Write'):
            self.assertTrue(hooks._memory_only({'tool_name': tool, 'tool_input': {'file_path': '.remvu/proposal.json'}}, self.repo))
            self.assertTrue(hooks._memory_only({'tool_name': tool, 'tool_input': {'path': 'REMVU.md'}}, self.repo))
            self.assertFalse(hooks._memory_only({'tool_name': tool, 'tool_input': {'file_path': 'app.py'}}, self.repo))
        for tool in ('Bash', 'mcp__example__run', 'UnknownWrite'):
            self.assertFalse(self.classified('python3 real_work.py', tool=tool, file_path='.remvu/proposal.json'))
        self.assertFalse(self.classified(self.python_call('status'), tool='mcp__example__run'))
        self.assertFalse(hooks._memory_only({'tool_name': 'Write', 'tool_input': {'file_path': '.remvu/invalid\0.json'}}, self.repo))

    def test_private_looking_symlink_to_project_code_is_recorded(self):
        target = self.repo / 'app.py'
        target.write_text('value = 1\n')
        alias = self.repo / '.remvu/proposal.json'
        try:
            alias.symlink_to(target)
        except OSError:
            self.skipTest('This host does not permit creating symlinks.')
        self.assertFalse(hooks._memory_only({'tool_name': 'Write', 'tool_input': {'file_path': str(alias)}}, self.repo))
        relocated = self.repo / 'alias' / 'remvu.py'
        relocated.parent.mkdir()
        relocated.symlink_to(self.script)
        self.assertFalse(self.classified(shlex.join([sys.executable, str(relocated), 'status'])))

    def test_ambiguous_or_windows_shell_syntax_is_recorded(self):
        for command in ('', self.python_call('status') + ' "unterminated',
                        'powershell.exe -Command ' + self.python_call('status')):
            self.assertFalse(self.classified(command))
        with patch.object(hooks.os, 'name', 'nt'):
            self.assertFalse(self.classified(self.python_call('status')))

    def test_valid_inline_update_is_omitted_but_lookalikes_retain_attempt_and_result(self):
        core.init_state(self.repo)
        common = {'session_id': 'classifier', 'turn_id': 'one', 'tool_name': 'Bash',
                  'permission_mode': 'default', 'cwd': str(self.repo)}
        calls = [(self.python_call('update', '--proposal-json', '{"base_revision":0,"entries":[]}'), 'bookkeeping'),
                 (shlex.join([sys.executable, '-c', 'print("work")', str(self.script), 'status']), 'real-work')]
        for command, call_id in calls:
            for event in ('PreToolUse', 'PostToolUse'):
                payload = {**common, 'hook_event_name': event, 'tool_use_id': call_id,
                           'tool_input': {'command': command}, 'tool_response': {'exit_code': 0, 'stdout': 'work'}}
                hooks.run_hook('codex', event, payload, self.repo)
        state = core.load_state(self.repo)
        expected_ids = ['real-work', 'real-work']
        expected_kinds = ['tool_call', 'tool_result']
        if os.name == 'nt':
            expected_ids = ['bookkeeping', 'bookkeeping', *expected_ids]
            expected_kinds = ['tool_call', 'tool_result', *expected_kinds]
        self.assertEqual([e['kind'] for e in state['events']], expected_kinds)
        bodies = [json.loads((self.repo / '.remvu' / e['blob_ref']).read_text()) for e in state['events']]
        self.assertEqual([e['call_id'] for e in bodies], expected_ids)
        self.assertTrue(state['pending_consolidation'])


if __name__ == '__main__':
    unittest.main()
