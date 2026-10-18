#!/usr/bin/env python3
"""Prepare a synthetic native-client handoff and verify its behavior locally.

This does not launch agents, grant hook trust, read chat logs or certify a client.
Run each producer/receiver prompt in the named real client, following the guide.
"""
import argparse
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

PROFILES = tuple(f'{client}-{surface}' for client in ('claude', 'codex') for surface in ('cli', 'desktop', 'vscode'))
BASELINE = '''import unittest
from tags import normalize_tags

class TagsTest(unittest.TestCase):
    def test_order_and_case(self):
        self.assertEqual(normalize_tags(' One, TWO,one, ,two, Three '), ['One', 'TWO', 'Three'])
    def test_empty(self):
        self.assertEqual(normalize_tags(' , , '), [])
    def test_signature(self):
        self.assertEqual(normalize_tags('A'), ['A'])
'''
PRODUCER = '''Use this local project in the named real client. Install the reviewed
Remvu candidate using its documented installer; review exact hooks through the
normal host trust flow. Keep the workspace's normal permissions.

Implement normalize_tags(value) with the Python standard library. Split on
commas, trim whitespace, omit empty fields, and deduplicate case-insensitively.
Preserve the original spelling and order of the first occurrence. Keep its public
signature unchanged. Run the baseline tests. No dependencies or regex splitter:
the input format is comma-delimited, not a general CSV grammar.

Then use Remvu to preserve these confirmed constraints and the rejected regex
direction. Record one unfinished next step: handle exactly one leading UTF-8 BOM
at the start of the whole input, without removing a BOM inside later labels.
Do not implement that next step yet. Generate a handoff, explicitly select these
synthetic project facts for public sharing, and create REMVU.md. Do not publish
or upload anything. Leave any failed checks or pending observations visible.
'''
RECEIVER = '''This is a fresh session. You have project code and REMVU.md only.
Read the handoff as project evidence, then complete the recorded next step.
Keep recorded constraints, run checks and explain any remaining uncertainty.
Do not install Remvu or seek the original chat. Use normal permissions.
'''


def fresh(path):
    path = path.expanduser().absolute()
    if path.exists() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Choose a new directory under non-symlinked parents')
    path.mkdir(parents=True)
    return path


def prepare(out, profile):
    root = fresh(out)
    project = root / 'producer'
    project.mkdir()
    (project / 'tags.py').write_text('def normalize_tags(value):\n    raise NotImplementedError\n', encoding='utf-8')
    (project / 'test_baseline.py').write_text(BASELINE, encoding='utf-8')
    (project / '.gitignore').write_text('__pycache__/\nREMVU.md\n', encoding='utf-8')
    for args in (['init'], ['config', 'user.name', 'Remvu acceptance fixture'], ['config', 'user.email', 'fixture@example.invalid'],
                 ['add', '.'], ['commit', '-m', 'Synthetic acceptance fixture']):
        subprocess.run(['git', '-C', str(project), *args], check=True, capture_output=True)
    (root / 'producer-prompt.txt').write_text(PRODUCER, encoding='utf-8')
    (root / 'receiver-prompt.txt').write_text(RECEIVER, encoding='utf-8')
    (root / 'profile.json').write_text(json.dumps({'format': 'remvu-native-fixture/1', 'profile': profile,
                                                  'system': platform.system(), 'machine': platform.machine()}, indent=2), encoding='utf-8')
    return {'ok': True, 'root': str(root), 'next': 'Run producer-prompt.txt in producer/, then receive --root THIS_DIRECTORY.'}


def receive(root):
    root = root.expanduser().resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/remvu/scripts'))
    from remvu_core import validate_document
    producer = root / 'producer'
    document = producer / 'REMVU.md'
    if document.is_symlink():
        raise ValueError('Fixture handoff must not be a symlink')
    validation = validate_document(document.read_text(encoding='utf-8'))
    if not validation['ok'] or validation['metadata'].get('visibility') != 'public':
        raise ValueError('Producer handoff must be a valid explicitly public remvu/1 document')
    names = ('tags.py', 'test_baseline.py', '.gitignore', 'REMVU.md')
    for name in names:
        if (producer / name).is_symlink() or not (producer / name).is_file():
            raise ValueError('Fixture inputs must be regular non-symlink files')
    receiver = fresh(root / 'receiver')
    # Fixed allowlist: no hidden memory, adapter files, original prompts or chats.
    for name in names:
        shutil.copyfile(producer / name, receiver / name)
    return {'ok': True, 'receiver': str(receiver), 'next': 'Open a fresh session in the OTHER agent, using receiver-prompt.txt. No Remvu install.'}


def verify(root, out):
    root = root.expanduser().resolve()
    receiver = root / 'receiver'
    for forbidden in ('.remvu', '.claude', '.codex', '.agents', 'AGENTS.md', 'CLAUDE.md'):
        if (receiver / forbidden).exists():
            raise ValueError('Receiver isolation boundary violated: ' + forbidden)
    baseline = subprocess.run([sys.executable, '-m', 'unittest', 'test_baseline', '-q'], cwd=receiver, capture_output=True, timeout=60)
    check = "from tags import normalize_tags as f; assert f('\\ufeff One, TWO,one') == ['One','TWO']; assert f('One,\\ufeffTWO') == ['One','\\ufeffTWO']; assert f(' , ') == []"
    behavior = subprocess.run([sys.executable, '-c', check], cwd=receiver, capture_output=True, timeout=60)
    profile = json.loads((root / 'profile.json').read_text(encoding='utf-8'))
    result = {'format': 'remvu-native-behavior/1', 'profile': profile,
              'baseline_passed': baseline.returncode == 0, 'next_step_passed': behavior.returncode == 0,
              'receiver_private_files_absent': True, 'python': platform.python_version(),
              'native_client_acceptance_complete': False,
              'remaining': 'Record actual client versions, memory intent review, lifecycle and recovery checks using docs/native-acceptance.md. This verifies behavior only.'}
    destination = out.expanduser().absolute()
    if destination.exists():
        raise ValueError('Choose a new report filename')
    destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--out', type=Path, required=True)
    prep.add_argument('--profile', choices=PROFILES, required=True)
    for action in ('receive', 'verify'):
        sub = commands.add_parser(action)
        sub.add_argument('--root', type=Path, required=True)
        if action == 'verify':
            sub.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.out, args.profile) if args.action == 'prepare' else receive(args.root) if args.action == 'receive' else verify(args.root, args.out)
        print(json.dumps(result, indent=2))
        if result.get('baseline_passed') is False or result.get('next_step_passed') is False:
            raise SystemExit(1)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        raise SystemExit(1)
