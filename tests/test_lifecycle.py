"""Black-box lifecycle invariants: preserve user data and recover truthfully."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/remvu/scripts'
sys.path.insert(0, str(SCRIPTS))
import remvu_core as core
import remvu_hooks as hooks
import remvu_init as setup
import remvu_lifecycle as life


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='remvu lifecycle spaces ')
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'project'
        self.repo.mkdir()
        self.home = self.root / 'managed'

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, source=None):
        # The old suite also runs on Apple's system Python 3.9. Production
        # installation rejects it; CI and acceptance use actual Python 3.10+.
        with patch.object(life.sys, 'version_info', (3, 12)):
            return life.install(self.repo, source or SCRIPTS.parent, self.home)

    def test_stable_install_source_relocation_repeat_and_uninstall(self):
        source = self.root / 'source'
        shutil.copytree(SCRIPTS.parent, source, ignore=shutil.ignore_patterns('__pycache__'))
        original = {'theme': 'keep', 'hooks': {'Stop': [{'hooks': [{'type': 'command', 'command': 'user-hook'}]}]}}
        config = self.repo / '.claude/settings.local.json'
        config.parent.mkdir()
        config.write_text(json.dumps(original))
        (self.repo / 'CLAUDE.md').write_text('User instructions.\n')
        installed = self.install(source)
        scripts = Path(installed['runtime_scripts'])
        self.assertNotIn(str(source), str(scripts))
        self.assertEqual(self.install(source)['runtime_scripts'], str(scripts))
        shutil.rmtree(source)
        result = subprocess.run([sys.executable, str(scripts / 'remvu.py'), 'status', '--repo', str(self.repo)], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        before = (self.repo / '.remvu/state.json').read_bytes()
        self.assertTrue(life.uninstall(self.repo)['memory_retained'])
        self.assertEqual(before, (self.repo / '.remvu/state.json').read_bytes())
        remaining = json.loads(config.read_text())
        self.assertEqual(remaining['theme'], 'keep')
        self.assertEqual(remaining['hooks']['Stop'], original['hooks']['Stop'])
        self.assertIn('User instructions.', (self.repo / 'CLAUDE.md').read_text())
        self.assertNotIn(setup.BEGIN, (self.repo / 'CLAUDE.md').read_text())
        self.assertTrue(scripts.exists())
        self.assertTrue(life.uninstall(self.repo)['ok'])

    def test_upgrade_rollback_and_modified_runtime_refused(self):
        first = self.install()['runtime_scripts']
        source = self.root / 'changed'
        shutil.copytree(SCRIPTS.parent, source, ignore=shutil.ignore_patterns('__pycache__'))
        (source / 'SKILL.md').write_text((source / 'SKILL.md').read_text() + '\nA revised instruction.\n')
        second = self.install(source)['runtime_scripts']
        self.assertNotEqual(first, second)
        with patch.object(life.sys, 'version_info', (3, 12)):
            self.assertEqual(life.install(self.repo, rollback=True)['runtime_scripts'], first)
        self.assertEqual(json.loads((self.repo / '.remvu/adapters.json').read_text())['scripts_dir'], first)
        (Path(second) / 'remvu.py').write_text('tampered')
        with patch.object(life.sys, 'version_info', (3, 12)):
            with self.assertRaisesRegex(ValueError, 'checksum'):
                life.install(self.repo, rollback=True)

    def test_failed_install_restores_configs_without_discarding_concurrent_events(self):
        setup.initialize(self.repo, ('claude',), SCRIPTS)
        config = self.repo / '.claude/settings.local.json'
        before = config.read_bytes()
        original = life._initialize_runtime

        def fail(*args, **kwargs):
            original(*args, **kwargs)
            core.record_event(self.repo, {'kind': 'tool_result', 'output': 'new concurrent evidence'})
            raise OSError('simulated interruption')

        with patch.object(life, '_initialize_runtime', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'interruption'):
                self.install()
        self.assertEqual(before, config.read_bytes())
        self.assertEqual(len(core.load_state(self.repo)['events']), 1)
        self.assertTrue(list((self.repo / '.remvu/backups').glob('lifecycle-*')))

    def test_doctor_does_not_claim_trust_from_configuration(self):
        self.install()
        health = life.doctor(self.repo)
        self.assertTrue(all(a['activation'] == 'awaiting_host_review' for a in health['adapters']))
        scripts = Path(json.loads((self.repo / '.remvu/adapters.json').read_text())['scripts_dir'])
        result = subprocess.run([sys.executable, str(scripts / 'remvu_hooks.py'), '--platform', 'codex', '--event', 'SessionStart', '--repo', str(self.repo)],
                                input=json.dumps({'session_id': 'synthetic-not-a-native-client'}).encode(), capture_output=True)
        self.assertEqual(result.returncode, 0)
        codex = next(a for a in life.doctor(self.repo)['adapters'] if a['client'] == 'codex')
        self.assertEqual(codex['activation'], 'hook_execution_observed')
        self.assertIn('not a trust attestation', codex['scope'])

    def test_cold_doctor_is_read_only(self):
        self.assertFalse(life.doctor(self.repo)['ok'])
        self.assertFalse((self.repo / '.remvu').exists())

    def test_repair_snapshot_retains_corrupt_file_and_pending(self):
        setup.initialize(self.repo, (), SCRIPTS)
        core.record_event(self.repo, {'kind': 'tool_result', 'output': 'retained'})
        damaged = self.repo / '.remvu/state.json'
        damaged.write_text('{broken')
        result = life.repair(self.repo)
        self.assertFalse(result['semantic_refresh_claimed'])
        self.assertEqual((self.repo / result['backup'] / 'state.json').read_text(), '{broken')
        self.assertTrue(core.load_state(self.repo)['pending_consolidation'])
        self.assertEqual(len(core.load_state(self.repo)['events']), 1)
        self.assertIn('pending_consolidation', [i['code'] for i in core.check_project(self.repo)['issues']])

    def test_repair_uses_older_verified_copy_and_never_replays_orphan(self):
        setup.initialize(self.repo, (), SCRIPTS)
        root = self.repo / '.remvu'
        core.record_event(self.repo, {'kind': 'tool_result', 'output': 'retained'})
        (root / 'state.json').write_text('{}')
        (root / 'snapshots/latest.json').write_text('{}')
        orphan = root / ('journal/' + 'a' * 32 + '.json')
        orphan.write_text(json.dumps({'format': 'remvu-journal/1', 'revision': 1, 'state_integrity': 'f' * 64,
                                      'created_at': '2999', 'operation': 'uncommitted', 'payload': 'do not replay'}))
        self.assertTrue(life.repair(self.repo)['ok'])
        self.assertTrue(orphan.exists())
        self.assertIn('uncommitted_journal', [i['code'] for i in core.check_project(self.repo)['issues']])

    def test_repair_cannot_restore_missing_evidence_or_fabricate_success(self):
        setup.initialize(self.repo, (), SCRIPTS)
        core.record_event(self.repo, {'kind': 'tool_result', 'output': 'lost'})
        root = self.repo / '.remvu'
        # Every recoverable snapshot now references the missing blob.
        for path in (root / 'snapshots').glob('*.json'):
            if not json.loads(path.read_text())['events']:
                path.unlink()
        next((root / 'blobs').glob('*.json')).unlink()
        (root / 'state.json').write_text('broken')
        with self.assertRaisesRegex(ValueError, 'No verified snapshot'):
            life.repair(self.repo)
        self.assertEqual((root / 'state.json').read_text(), 'broken')

    def test_older_snapshot_recovery_never_reuses_a_stale_writer_revision(self):
        setup.initialize(self.repo, (), SCRIPTS)
        for revision in range(5):
            core.apply_update(self.repo, {'base_revision': revision, 'entries': []})
        root = self.repo / '.remvu'
        for path in (root / 'snapshots').glob('*.json'):
            if json.loads(path.read_text())['revision'] > 1:
                path.unlink()
        (root / 'state.json').write_text('damaged')
        life.repair(self.repo)
        self.assertEqual(core.load_state(self.repo)['revision'], 6)
        stale = core.apply_update(self.repo, {'base_revision': 2, 'entries': []})
        self.assertFalse(stale['ok'])
        self.assertTrue(stale['conflicts'])

    def test_recovery_refuses_unreadable_revision_history(self):
        setup.initialize(self.repo, (), SCRIPTS)
        root = self.repo / '.remvu'
        (root / 'journal' / ('b' * 32 + '.json')).write_text('{}')
        (root / 'state.json').write_text('damaged')
        with self.assertRaisesRegex(ValueError, 'cannot safely choose a recovery revision'):
            life.repair(self.repo)
        self.assertEqual((root / 'state.json').read_text(), 'damaged')

    def test_ledger_repair_preserves_original_and_does_not_clear_events(self):
        setup.initialize(self.repo, (), SCRIPTS)
        ledger = self.repo / '.remvu/hooks/state.json'
        ledger.parent.mkdir()
        ledger.write_text('bad')
        result = life.repair(self.repo)
        self.assertEqual((self.repo / result['backup'] / 'hooks-state.json').read_text(), 'bad')
        self.assertTrue(core.load_state(self.repo)['pending_consolidation'])
        self.assertEqual(hooks._load_ledger(ledger)['sessions'], {})

    def test_diagnostic_allowlist_excludes_private_content_paths_and_urls(self):
        self.install()
        core.record_event(self.repo, {'kind': 'tool_result', 'output': 'Bearer SECRET-DIAGNOSTIC-CANARY https://private.invalid'})
        destination = self.root / 'report.json'
        life.diagnose(self.repo, destination)
        text = destination.read_text()
        for secret in ('CANARY', 'private.invalid', str(self.root), 'tool_result'):
            self.assertNotIn(secret, text)
        self.assertFalse(json.loads(text)['ok'])
        with self.assertRaisesRegex(ValueError, 'exists'):
            life.diagnose(self.repo, destination)

    def test_uninstall_refuses_edited_skill_and_retains_edited_hooks(self):
        self.install()
        shim = self.repo / '.agents/skills/remvu/SKILL.md'
        before = shim.read_text()
        shim.write_text(before + 'user edits')
        with self.assertRaisesRegex(ValueError, 'edited'):
            self.install()
        self.assertEqual(shim.read_text(), before + 'user edits')
        with self.assertRaisesRegex(ValueError, 'edited'):
            life.uninstall(self.repo)
        shim.write_text(before)
        config = self.repo / '.codex/hooks.json'
        body = json.loads(config.read_text())
        body['hooks']['Stop'][0]['hooks'][0]['timeout'] = 999
        config.write_text(json.dumps(body))
        life.uninstall(self.repo)
        self.assertEqual(json.loads(config.read_text())['hooks']['Stop'][0]['hooks'][0]['timeout'], 999)

    def test_recovery_snapshots_are_bounded_but_journals_retained(self):
        setup.initialize(self.repo, (), SCRIPTS)
        for index in range(8):
            core.record_event(self.repo, {'kind': 'tool_result', 'source_id': str(index), 'output': str(index)})
        self.assertEqual(len(list((self.repo / '.remvu/snapshots').glob('*.json'))), 6)
        self.assertEqual(len(list((self.repo / '.remvu/journal').glob('*.json'))), 9)

    def test_powershell_parser_literals_and_ambiguous_commands(self):
        self.assertEqual(hooks._powershell_words("& 'C:\\Python\\python.exe' 'C:\\Remvu\\remvu.py' 'status'"),
                         ['C:\\Python\\python.exe', 'C:\\Remvu\\remvu.py', 'status'])
        self.assertEqual(hooks._powershell_words("& 'python' 'remvu.py' 'update' '--proposal-json' '{\"text\":\"it''s $() ; & literal\"}'")[-1],
                         '{"text":"it\'s $() ; & literal"}')
        for value in ("& 'python' 'remvu.py' status; Write-Host work", "& 'python' 'remvu.py' status | other", "& '$python' \"$script\" status",
                      "& 'python' 'remvu.py' status > out", "& 'python' 'remvu.py' status\nwork", "& 'python' 'unterminated"):
            self.assertIsNone(hooks._powershell_words(value), value)

    def test_hook_failure_leaves_gap_and_repair_does_not_invent_missing_work(self):
        setup.initialize(self.repo, (), SCRIPTS)
        payload = {'session_id': 'gap-fixture', 'prompt': 'synthetic', 'permission_mode': 'default'}
        with patch.object(core, 'record_event', side_effect=ValueError('synthetic observation failure')):
            warning = hooks.run_hook('codex', 'UserPromptSubmit', payload, self.repo)
        self.assertIn('could not finish', warning['systemMessage'])
        root = self.repo / '.remvu'
        self.assertEqual(len(list((root / 'gaps').glob('*.json'))), 1)
        self.assertIn('observation_gap', [i['code'] for i in core.check_project(self.repo)['issues']])
        self.assertIn('OBSERVATION GAPS', core.render_document(self.repo))
        compact = subprocess.run([sys.executable, str(SCRIPTS / 'remvu.py'), 'status', '--repo', str(self.repo)],
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertTrue(json.loads(compact.stdout)['observation_gaps_present'])
        context = hooks.run_hook('codex', 'SessionStart', {'session_id': 'gap-fixture'}, self.repo)
        self.assertIn('Observation gaps remain', context['hookSpecificOutput']['additionalContext'])
        first_stop = hooks.run_hook('codex', 'Stop', {'session_id': 'gap-fixture'}, self.repo)
        self.assertEqual(first_stop, {})
        self.assertEqual(hooks.run_hook('codex', 'Stop', {'session_id': 'gap-fixture'}, self.repo), {})
        with self.assertRaisesRegex(ValueError, 'observation gaps'):
            core.render_document(self.repo, visibility='public')
        repaired = life.repair(self.repo)
        self.assertIn('observation_gap_indexed_for_semantic_review', repaired['repaired'])
        self.assertTrue(core.load_state(self.repo)['pending_consolidation'])
        self.assertEqual(len(list((root / 'gaps/reviewable').glob('*.json'))), 1)
        self.assertEqual(core.load_state(self.repo)['events'][0]['kind'], 'tool_result')

    def test_diagnostic_filters_receipt_strings_to_known_events(self):
        self.install()
        manifest = json.loads((self.repo / '.remvu/adapters.json').read_text())
        receipt = self.repo / '.remvu/hooks/activation-codex.json'
        receipt.parent.mkdir()
        receipt.write_text(json.dumps({'scripts': manifest['scripts_dir'], 'python': manifest['python'],
                                       'events': ['SECRET-CANARY', 'SessionStart']}))
        output = self.root / 'filtered-report.json'
        life.diagnose(self.repo, output)
        self.assertNotIn('CANARY', output.read_text())

    def test_uninstall_then_default_install_restores_platforms(self):
        self.install()
        life.uninstall(self.repo)
        self.install()
        self.assertEqual(set(json.loads((self.repo / '.remvu/adapters.json').read_text())['platforms']), {'claude', 'codex'})

    def test_different_worktree_cwd_cannot_record_into_original_project(self):
        setup.initialize(self.repo, (), SCRIPTS)
        other = self.root / 'other-worktree'
        other.mkdir()
        payload = {'session_id': 'other-worktree', 'cwd': str(other), 'tool_name': 'Bash',
                   'tool_input': {'command': 'echo PRIVATE-OTHER-PROJECT'}}
        result = hooks.run_hook('codex', 'PreToolUse', payload, self.repo)
        self.assertIn('outside the configured project', result['systemMessage'])
        self.assertEqual(core.load_state(self.repo)['events'], [])
        self.assertFalse((other / '.remvu').exists())
        nested = self.repo / 'nested-worktree'
        nested.mkdir()
        (nested / '.git').write_text('gitdir: synthetic-worktree-fixture')
        payload['cwd'] = str(nested)
        self.assertIn('nested repository or worktree', hooks.run_hook('codex', 'PreToolUse', payload, self.repo)['systemMessage'])
        self.assertEqual(core.load_state(self.repo)['events'], [])
        for blob in (self.repo / '.remvu').rglob('*.json'):
            self.assertNotIn('PRIVATE-OTHER-PROJECT', blob.read_text())

    def test_shim_records_interpreter_and_uninstall_uses_recorded_interpreter(self):
        installed = self.install()
        manifest = json.loads((self.repo / '.remvu/adapters.json').read_text())
        shim = (self.repo / '.agents/skills/remvu/SKILL.md').read_text()
        self.assertEqual(installed['runtime_python'], manifest['python'])
        self.assertIn('Python interpreter: `' + manifest['python'] + '`', shim)
        with patch.object(setup.sys, 'executable', str(self.root / 'different-python')), \
             patch.object(setup, '_skill_shim', return_value='a future version template'):
            self.assertTrue(life.uninstall(self.repo)['ok'])

    @unittest.skipUnless(sys.platform == 'win32', 'Actual Windows path semantics')
    def test_windows_bookkeeping_excludes_only_canonical_installed_call(self):
        argv = [str(Path(sys.executable).resolve()), str(SCRIPTS / 'remvu.py'), 'status', '--repo', str(self.repo)]
        command = '& ' + ' '.join("'" + part.replace("'", "''") + "'" for part in argv)
        payload = {'tool_name': 'Bash', 'tool_input': {'command': command}}
        self.assertTrue(hooks._memory_only(payload, self.repo))
        payload['tool_input']['command'] += '; Write-Host actual-work'
        self.assertFalse(hooks._memory_only(payload, self.repo))


if __name__ == '__main__':
    unittest.main()
