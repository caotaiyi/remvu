"""Acceptance tooling must retain failures and isolate cold receivers."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/remvu/scripts'))
import remvu_core as core


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class BetaToolsTest(unittest.TestCase):
    def test_pending_native_ledger_is_not_ready(self):
        gate = module('check_beta_readiness')
        matrix = json.loads((ROOT / 'evals/beta-matrix.json').read_text())
        for row in matrix['profiles']:
            row['status'] = 'pending'
        result = gate.readiness(matrix)
        self.assertFalse(result['release_ready'])
        self.assertEqual(len(result['pending']), 12)
        matrix['profiles'].pop()
        with self.assertRaisesRegex(ValueError, 'twelve'):
            gate.readiness(matrix)

    def test_verified_label_without_checks_or_evidence_is_not_ready(self):
        gate = module('check_beta_readiness')
        matrix = json.loads((ROOT / 'evals/beta-matrix.json').read_text())
        for row in matrix['profiles']:
            row['status'] = 'automatic_verified'
            row['checks'] = {}
            row['evidence'] = []
        self.assertFalse(gate.readiness(matrix)['release_ready'])

    def test_native_fixture_receiver_excludes_private_files_and_verifier_keeps_failures(self):
        native = module('native_acceptance')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / 'native'
            native.prepare(root, 'claude-cli')
            producer = root / 'producer'
            core.init_state(producer)
            (producer / 'REMVU.md').write_text(core.render_document(producer, visibility='private'))
            with self.assertRaisesRegex(ValueError, 'explicitly public'):
                native.receive(root)
            (producer / 'REMVU.md').write_text(core.render_document(producer, visibility='public'))
            (producer / '.remvu/secret.txt').write_text('NEVER-COPY')
            native.receive(root)
            self.assertFalse((root / 'receiver/.remvu').exists())
            report = native.verify(root, root / 'failure.json')
            self.assertFalse(report['baseline_passed'])
            self.assertFalse(report['next_step_passed'])
            self.assertFalse(report['native_client_acceptance_complete'])


if __name__ == '__main__':
    unittest.main()
