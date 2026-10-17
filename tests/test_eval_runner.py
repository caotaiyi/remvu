"""Evaluation harness unit tests. These never call a live model."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'evals/run_live.py'
spec = importlib.util.spec_from_file_location('remvu_eval_runner', SCRIPT)
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)


class EvalRunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_fixture_is_small_and_does_not_disclose_outstanding_work(self):
        scenario = runner.SCENARIOS['claude-codex']
        repo = self.root / 'fixture'
        metadata = runner.create_fixture(repo, scenario)
        self.assertEqual(set(metadata['tracked_files']), {'tags.py', '.gitignore'})
        self.assertFalse((repo / 'REMVU.md').exists())
        self.assertNotIn('BOM', (repo / 'tags.py').read_text())
        self.assertFalse((repo / '.remvu').exists())
        with self.assertRaises(ValueError):
            runner.create_fixture(repo, scenario)

    def test_hidden_code_acceptance_distinguishes_stages_and_types(self):
        scenario = runner.SCENARIOS['claude-codex']
        repo = self.root / 'fixture'; runner.create_fixture(repo, scenario)
        (repo / 'tags.py').write_text('import csv\ndef normalize_tags(value: str) -> list[str]:\n    return [x.strip() for x in next(csv.reader([value], skipinitialspace=True)) if x.strip()]\n')
        report = runner.evaluate_code(repo, scenario)
        self.assertTrue(all(c['passed'] for c in report['cases'] if c['stage'] != 'next_step'))
        self.assertFalse(next(c for c in report['cases'] if c['stage'] == 'next_step')['passed'])
        (repo / 'tags.py').write_text('import csv\ndef normalize_tags(value: str) -> list[str]:\n    value=value.removeprefix("\\ufeff")\n    return [x.strip() for x in next(csv.reader([value], skipinitialspace=True)) if x.strip()]\n')
        self.assertTrue(runner.evaluate_code(repo, scenario)['all_passed'])
        self.assertFalse((repo / 'acceptance.py').exists())

    def test_money_acceptance_requires_exact_half_up_and_integer_result(self):
        scenario = runner.SCENARIOS['codex-claude']
        repo = self.root / 'fixture'; runner.create_fixture(repo, scenario)
        self.assertFalse(runner.evaluate_code(repo, scenario)['all_passed'])
        (repo / 'money.py').write_text('from decimal import Decimal, ROUND_HALF_UP\ndef parse_cents(amount: str) -> int:\n    amount=amount.strip()\n    if amount.startswith("(") and amount.endswith(")"):\n        amount="-"+amount[1:-1]\n    return int((Decimal(amount)*100).quantize(Decimal("1"),rounding=ROUND_HALF_UP))\n')
        self.assertTrue(runner.evaluate_code(repo, scenario)['all_passed'])
        (repo / 'money.py').write_text('def parse_cents(amount: str) -> int:\n    return 10.0\n')
        result = runner.evaluate_code(repo, scenario)
        self.assertFalse(next(c for c in result['cases'] if c['id'] == 'integer-type')['passed'])

    def test_recall_scoring_reports_groups_without_percentages(self):
        scenario = runner.SCENARIOS['claude-codex']
        recall = {'intent': scenario['intent'], 'constraints': scenario['constraints'],
                  'rejected_directions': scenario['rejected'], 'next_step': scenario['next_step'],
                  'known_failed_checks': ['CSV_BOM failed']}
        result = runner.score_recall(recall, scenario)
        self.assertTrue(result['all_matched'], result)
        self.assertNotIn('percentage', result)
        unknown = runner.score_recall({'needs_context': True, 'next_step': 'unknown'}, scenario)
        self.assertTrue(unknown['needs_context'])
        self.assertFalse(unknown['all_matched'])
        self.assertEqual(unknown['matched_groups'], 0)

    def test_usage_only_copies_actual_numeric_counters(self):
        records = [{'type': 'turn.completed', 'usage': {'input_tokens': 12, 'output_tokens': 4, 'reasoning': 'HIDDEN', 'auth_token': 'SECRET'}},
                   {'type': 'result', 'modelUsage': {'native-model': {'inputTokens': 20, 'outputTokens': 8, 'costUSD': 0.05, 'apiKey': 'SECRET'}}}]
        result = runner.extract_usage(records)
        self.assertEqual(result[0]['counters'], {'input_tokens': 12, 'output_tokens': 4})
        self.assertEqual(result[1]['counters'], {'inputTokens': 20, 'outputTokens': 8})
        self.assertNotIn('SECRET', json.dumps(result))
        self.assertEqual(runner.extract_usage([{'type': 'result'}]), [])

    def test_model_names_come_only_from_native_fields(self):
        records = [{'type': 'system', 'model': 'claude-haiku-5-5', 'apiKey': 'SECRET'},
                   {'type': 'result', 'modelUsage': {'claude-haiku-5-5': {}, 'account-id-123': {}}},
                   {'type': 'message', 'message': {'model': 'gpt-native-model'}}]
        result = runner.extract_models(records, 'model: codex-native\nSECRET_AUTH')
        self.assertEqual(result, ['claude-haiku-5-5', 'codex-native', 'gpt-native-model'])
        self.assertEqual(runner.extract_models([{'type': 'result', 'result': 'I used gpt-guessed'}]), [])

    def test_native_filter_excludes_reasoning_system_auth_and_raw_stderr(self):
        records = [{'type': 'system', 'apiKeySource': 'SECRET_AUTH', 'prompt': 'HIDDEN_SYSTEM'},
                   {'type': 'item.completed', 'item': {'type': 'reasoning', 'text': 'HIDDEN_THOUGHT'}},
                   {'type': 'item.completed', 'item': {'type': 'command_execution', 'aggregated_output': json.dumps([{'type': 'thinking', 'thinking': 'HIDDEN_THINKING'}, {'type': 'text', 'text': 'Visible check'}]), 'exit_code': 1, 'status': 'completed'}},
                   {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'Visible final'}},
                   {'type': 'turn.completed', 'usage': {'input_tokens': 6, 'output_tokens': 4}}]
        output = runner.filter_native_output('\n'.join(json.dumps(r) for r in records), 'authentication error SECRET_STDERR')
        saved = json.dumps(output)
        self.assertNotIn('HIDDEN_', saved)
        self.assertNotIn('SECRET_', saved)
        self.assertIn('Visible check', saved)
        self.assertIn('Visible final', saved)
        self.assertFalse(output['raw_native_logs_persisted'])
        self.assertEqual(output['stderr_diagnostic_categories'], ['authentication_required'])

    def test_claude_result_filter_and_bounded_visible_text(self):
        record = {'type': 'result', 'result': 'Done; token="SECRET_VALUE"', 'usage': {'input_tokens': 13},
                  'session_id': 'PRIVATE_SESSION', 'permission_denials': ['PRIVATE_BODY']}
        output = runner.filter_native_output(json.dumps(record))
        saved = json.dumps(output)
        self.assertNotIn('SECRET_VALUE', saved)
        self.assertNotIn('PRIVATE_SESSION', saved)
        self.assertNotIn('PRIVATE_BODY', saved)
        text, truncated = runner.visible_text('x' * 7000)
        self.assertEqual(len(text), 6000); self.assertTrue(truncated)

    def test_fresh_clone_has_only_code_and_standalone_file(self):
        scenario = runner.SCENARIOS['codex-claude']
        producer = self.root / 'producer'; runner.create_fixture(producer, scenario)
        (producer / '.remvu').mkdir(); (producer / '.remvu/private.json').write_text('PRIVATE')
        (producer / 'REMVU.md').write_text('# Public handoff')
        with_memory = self.root / 'with'; control = self.root / 'without'
        with_info = runner.clone_consumer(producer, with_memory, True)
        control_info = runner.clone_consumer(producer, control, False)
        self.assertTrue((with_memory / 'REMVU.md').exists())
        self.assertFalse((control / 'REMVU.md').exists())
        self.assertFalse((with_memory / '.remvu').exists())
        self.assertEqual(runner.git(with_memory, 'rev-parse', 'HEAD'), runner.git(control, 'rev-parse', 'HEAD'))
        self.assertFalse(with_info['project_remvu_installed'])
        self.assertFalse(control_info['original_chat_copied'])

    def test_native_commands_use_permissions_and_fresh_sessions(self):
        codex = runner.native_command('codex', Path('/bin/codex'), self.root)
        claude = runner.native_command('claude', Path('/bin/claude'), self.root)
        self.assertIn('--ephemeral', codex)
        self.assertIn('workspace-write', codex)
        self.assertIn('--safe-mode', claude)
        self.assertIn('acceptEdits', claude)
        self.assertIn('--no-session-persistence', claude)
        self.assertFalse(any('dangerously' in arg for arg in codex + claude))
        self.assertIn('Bash(python3 *)', ' '.join(claude))
        prompt = runner.consumer_prompt()
        self.assertIn('unknown', prompt)
        self.assertIn('needs_context', prompt)
        self.assertNotIn('UTF-8', prompt)
        self.assertNotIn('parenthes', prompt)


if __name__ == '__main__':
    unittest.main()
