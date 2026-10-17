#!/usr/bin/env python3
"""Check synthetic Remvu examples with the reference CLI and optional JSON Schema."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / 'skills' / 'remvu' / 'scripts' / 'remvu.py'
EXAMPLES = ROOT / 'examples' / 'remvu'


def call(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-jsonschema', action='store_true')
    args = parser.parse_args()
    failures = []
    required = ('REMVU.md', 'invalid-format.md', 'invalid-missing-section.md',
                'invalid-private-path.md', 'update.proposal.json',
                'invalid-unknown-field.proposal.json', 'invalid-negative-event-count.proposal.json')
    failures.extend('missing conformance fixture: ' + name for name in required if not (EXAMPLES / name).is_file())
    validator = None
    try:
        import jsonschema
        validator = jsonschema.Draft202012Validator
    except ImportError:
        if args.require_jsonschema:
            failures.append('jsonschema is required for this run')
    schemas = {name: json.loads((ROOT / 'spec' / (name + '.schema.json')).read_text(encoding='utf-8')) for name in ('metadata', 'proposal')}
    if validator:
        for schema in schemas.values():
            validator.check_schema(schema)
    for path in sorted(EXAMPLES.glob('*.md')):
        if path.name == 'README.md':
            continue
        expected = not path.name.startswith('invalid-')
        result = call('validate', path)
        if (result.returncode == 0) != expected:
            failures.append(path.name + ': unexpected CLI validation result: ' + result.stdout[:1000] + result.stderr[:1000])
        if expected and validator:
            text = path.read_text(encoding='utf-8')
            match = re.search(r'^```json\n(.*?)\n```', text, re.M | re.S)
            if not match:
                failures.append(path.name + ': metadata block missing')
            else:
                errors = list(validator(schemas['metadata'], format_checker=jsonschema.FormatChecker()).iter_errors(json.loads(match.group(1))))
                failures.extend(path.name + ': ' + error.message for error in errors)
        print(('ACCEPT ' if expected else 'REJECT ') + path.name)
    for path in sorted(EXAMPLES.glob('*.proposal.json')):
        expected = not path.name.startswith('invalid-')
        proposal = json.loads(path.read_text(encoding='utf-8'))
        if validator:
            valid = not list(validator(schemas['proposal']).iter_errors(proposal))
            if valid != expected:
                failures.append(path.name + ': unexpected JSON Schema validation result')
        with tempfile.TemporaryDirectory(prefix='remvu-conformance-') as directory:
            initialized = call('init', '--repo', directory, '--platform', 'none')
            if initialized.returncode:
                failures.append(path.name + ': fixture initialization failed')
                continue
            result = call('update', '--repo', directory, '--proposal', path)
            if (result.returncode == 0) != expected:
                failures.append(path.name + ': unexpected proposal result: ' + result.stdout[:1000] + result.stderr[:1000])
        print(('ACCEPT ' if expected else 'REJECT ') + path.name)
    if failures:
        print('\n'.join(failures), file=sys.stderr)
        return 1
    print('Examples passed; JSON Schema ' + ('checked.' if validator else 'not installed (CLI validation passed).'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
