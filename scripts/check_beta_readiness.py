#!/usr/bin/env python3
"""Validate the beta acceptance ledger. CI passing is not native acceptance."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {'install', 'first_use', 'cold_handoff', 'intent_preserved', 'failed_check_preserved',
            'upgrade', 'rollback', 'uninstall', 'privacy_review'}
AUTO = {'multiple_turns', 'compaction', 'interruption', 'concurrent_sessions', 'bounded_repair'}
PROFILES = {f'{system}/{client}/{surface}' for system in ('macos', 'windows11-x64')
            for client in ('claude', 'codex') for surface in ('cli', 'desktop', 'vscode')}


def readiness(matrix, root=ROOT):
    if matrix.get('format') != 'remvu-beta-acceptance/1' or matrix.get('version') != '0.3.0-beta.3':
        raise ValueError('Unrecognized beta acceptance ledger')
    rows = matrix.get('profiles', [])
    if len(rows) != 12 or {r['id'] for r in rows} != PROFILES:
        raise ValueError('Ledger must contain each of the twelve target profiles once')
    pending = []
    for row in rows:
        status = row.get('status')
        if status not in {'pending', 'manual_verified', 'automatic_verified', 'unsupported'}:
            raise ValueError('Unknown profile status')
        reasons = []
        if status not in {'manual_verified', 'automatic_verified'}:
            reasons.append('native acceptance not complete')
        else:
            needed = REQUIRED | (AUTO if status == 'automatic_verified' else set())
            if any(row.get('checks', {}).get(key) is not True for key in needed):
                reasons.append('required checks missing')
            if not row.get('client_versions') or not row.get('runtime_digest'):
                reasons.append('client/runtime version missing')
            references = row.get('evidence', [])
            if not references:
                reasons.append('reviewed evidence summary missing')
            for ref in references:
                path = root / ref
                if not isinstance(ref, str) or path.is_symlink() or root.resolve() not in path.resolve().parents or not path.is_file():
                    reasons.append('evidence summary unavailable')
        if reasons:
            pending.append({'profile': row['id'], 'reasons': reasons})
    return {'ok': True, 'release_ready': not pending, 'pending': pending,
            'note': 'A structured reviewed evidence ledger; not independent proof of model behavior. No native result is inferred from CI.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, default=ROOT / 'evals/beta-matrix.json')
    parser.add_argument('--require-ready', action='store_true')
    args = parser.parse_args()
    try:
        result = readiness(json.loads(args.matrix.read_text(encoding='utf-8')))
        print(json.dumps(result, indent=2))
        raise SystemExit(1 if args.require_ready and not result['release_ready'] else 0)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'ok': False, 'release_ready': False, 'error': str(error)}))
        raise SystemExit(1)
