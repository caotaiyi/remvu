#!/usr/bin/env python3
"""Remvu reference CLI. Local project memory; no model or network API calls."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

VERSION = '0.3.0-beta.1'


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--version', action='version', version='Remvu ' + VERSION)
    commands = cli.add_subparsers(dest='command', required=True)
    for name, help_text in (
        ('init', 'Initialize private memory and optional host adapters'),
        ('install', 'Copy a reviewed runtime to a stable user directory and configure this project'),
        ('upgrade', 'Install reviewed local source, or roll back the previous managed runtime'),
        ('uninstall', 'Remove unchanged project adapters, retaining memory and shared runtimes'),
        ('doctor', 'Inspect memory, runtime checksums and observed hook activation'),
        ('repair', 'Recover verified snapshots or a damaged ledger without inventing semantic notes'),
        ('diagnose', 'Write a local allowlisted diagnostic report for user preview'),
        ('status', 'Read compact current project memory'),
        ('entries', 'Page through bounded memory-entry previews'),
        ('events', 'List recent evidence IDs without loading full output'),
        ('show', 'Read one bounded, integrity-checked evidence event'),
        ('update', 'Apply a revision-checked memory proposal'),
        ('handoff', 'Write a private, standalone Markdown handoff'),
        ('share', 'Write an explicitly public, standalone Markdown handoff'),
        ('check', 'Check memory integrity and code freshness'),
        ('import-legacy', 'Import a verified v0.1 evidence bundle as unverified notes'),
        ('resolve-conflict', 'Record a reviewed resolution while retaining the original proposal'),
        ('withhold', 'Withdraw selected entries from future public files, retaining local history'),
    ):
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument('--repo', default='.', help='Project root (default: current directory)')
        if name == 'init':
            sub.add_argument('--platform', choices=('both', 'claude', 'codex', 'none'), default='both')
        elif name in ('install', 'upgrade'):
            sub.add_argument('--source', help='Reviewed local skill directory; no remote code is fetched')
            sub.add_argument('--home', help='Managed runtime directory (default: user local application data)')
            sub.add_argument('--platform', choices=('both', 'claude', 'codex', 'none'))
            if name == 'upgrade':
                sub.add_argument('--rollback', action='store_true')
        elif name == 'diagnose':
            sub.add_argument('--out', required=True, help='New local JSON file; nothing is uploaded')
        elif name == 'status':
            sub.add_argument('--full', action='store_true')
        elif name in ('events', 'entries'):
            sub.add_argument('--limit', type=int, default=20)
            if name == 'entries':
                sub.add_argument('--offset', type=int, default=0)
        elif name == 'show':
            sub.add_argument('event_id')
            sub.add_argument('--max-chars', type=int, default=4000)
        elif name == 'update':
            proposal = sub.add_mutually_exclusive_group(required=True)
            proposal.add_argument('--proposal', help='Proposal JSON file, or - for stdin')
            proposal.add_argument('--proposal-json', help='Inline JSON proposal; avoids a separate proposal-file write')
        elif name in ('handoff', 'share'):
            sub.add_argument('--out', help='Output Markdown path')
            sub.add_argument('--include-patch', action='store_true', help='Explicitly include reviewable uncommitted changes')
            sub.add_argument('--max-summary-chars', type=int, default=8000)
        elif name == 'check':
            sub.add_argument('--document', help='Also inspect a standalone REMVU.md')
        elif name == 'import-legacy':
            sub.add_argument('bundle')
        elif name == 'resolve-conflict':
            sub.add_argument('conflict_id')
            sub.add_argument('--base-revision', type=int, required=True)
            sub.add_argument('--note', required=True)
            sub.add_argument('--entry-id', action='append', default=[])
        elif name == 'withhold':
            sub.add_argument('entry_ids', nargs='+', metavar='ID')
            sub.add_argument('--base-revision', type=int, required=True)
            sub.add_argument('--note', required=True)
    validate = commands.add_parser('validate', help='Validate a standalone REMVU.md without importing it')
    validate.add_argument('document')
    legacy = commands.add_parser('legacy', help='Run the preserved v0.1 evidence exporter')
    legacy.add_argument('arguments', nargs=argparse.REMAINDER)
    return cli


def entry_preview(entry):
    value = {k: entry[k] for k in ('id', 'kind', 'basis', 'visibility', 'flags', 'result', 'exit_code', 'superseded_by') if k in entry}
    text = entry.get('text', '')
    value.update(text=text[:200], text_truncated=len(text) > 200)
    return value


def bounded_page(entries, offset, limit):
    result = {'ok': True, 'total': len(entries), 'offset': offset, 'entries': []}
    for entry in entries[offset:offset + limit]:
        preview = entry_preview(entry)
        if len(json.dumps({**result, 'entries': result['entries'] + [preview]}, ensure_ascii=False, indent=2)) > 7400:
            break
        result['entries'].append(preview)
    next_offset = offset + len(result['entries'])
    result['next_offset'] = next_offset if next_offset < len(entries) else None
    result['next_read'] = 'show ID --max-chars 4000 retrieves a full entry or evidence event.'
    return result


def compact_state(state):
    entries = state.get('entries', [])
    active = [e for e in entries if not e.get('superseded_by')]
    result = {
        'format': state.get('format'),
        'project_id': state.get('project_id'),
        'revision': state.get('revision'),
        'updated_at': state.get('updated_at'),
        'pending_consolidation': state.get('pending_consolidation', False),
        'entry_count': len(entries),
        'event_count': len(state.get('events', [])),
        'issue_count': len(state.get('issues', [])),
        'recovery_flags': sorted({str(i.get('code', 'unknown'))[:100] for i in state.get('issues', []) if isinstance(i, dict)})[:20],
        'entries': [],
    }
    for entry in active:
        preview = entry_preview(entry)
        if len(json.dumps({**result, 'entries': result['entries'] + [preview]}, ensure_ascii=False, indent=2)) > 7400:
            break
        result['entries'].append(preview)
    result['omitted_active_entries'] = len(active) - len(result['entries'])
    result['next_read'] = 'Use entries --offset 0 --limit 20, then show ID --max-chars 4000. --full is explicitly unbounded.'
    return result


def main(argv=None):
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    arguments = sys.argv[1:] if argv is None else list(argv)
    # Preserve the legacy parser's own help and option handling verbatim.
    if arguments and arguments[0] == 'legacy':
        engine = Path(__file__).with_name('legacy_export.py')
        return subprocess.call([sys.executable, str(engine), *arguments[1:]])
    args = parser().parse_args(arguments)
    try:
        import remvu_core as core
        if args.command == 'validate':
            result = core.validate_document(Path(args.document).read_text(encoding='utf-8'))
        else:
            repo = Path(args.repo).expanduser().resolve()
            if args.command in ('install', 'upgrade', 'uninstall', 'doctor', 'repair', 'diagnose'):
                import remvu_lifecycle as lifecycle
                if args.command in ('install', 'upgrade'):
                    if getattr(args, 'rollback', False) and (args.source or args.home):
                        raise ValueError('--rollback cannot be combined with --source or --home')
                    if args.command == 'upgrade' and not args.source and not args.rollback:
                        raise ValueError('upgrade requires --source REVIEWED_SKILL_DIRECTORY or --rollback')
                    platforms = None if args.platform is None else ('claude', 'codex') if args.platform == 'both' else () if args.platform == 'none' else (args.platform,)
                    result = lifecycle.install(repo, source=args.source, home=args.home, platforms=platforms,
                                               rollback=getattr(args, 'rollback', False))
                elif args.command == 'diagnose':
                    result = lifecycle.diagnose(repo, args.out)
                else:
                    result = getattr(lifecycle, args.command)(repo)
            elif args.command == 'init':
                from remvu_init import initialize
                platforms = ('claude', 'codex') if args.platform == 'both' else () if args.platform == 'none' else (args.platform,)
                result = initialize(repo, platforms=platforms, scripts_dir=Path(__file__).parent)
            elif args.command == 'status':
                state = core.load_state(repo)
                result = state if args.full else compact_state(state)
            elif args.command == 'events':
                if not 1 <= args.limit <= 1000:
                    raise ValueError('--limit must be between 1 and 1000')
                state = core.load_state(repo)
                result = {'ok': True, 'revision': state['revision'], 'total': len(state['events']),
                          'events': state['events'][-args.limit:]}
            elif args.command == 'entries':
                if not 1 <= args.limit <= 1000 or args.offset < 0:
                    raise ValueError('--limit must be 1..1000 and --offset must be nonnegative')
                state = core.load_state(repo)
                result = bounded_page(state['entries'], args.offset, args.limit)
            elif args.command == 'show':
                if not 1 <= args.max_chars <= 100000:
                    raise ValueError('--max-chars must be between 1 and 100000')
                state = core.load_state(repo)
                entry = next((e for e in state['events'] if e['id'] == args.event_id), None)
                kind = 'event'
                if entry is not None:
                    path = core._safe_child(repo / '.remvu', entry['blob_ref'])
                    raw = path.read_bytes()
                    if hashlib.sha256(raw).hexdigest() != entry['sha256']:
                        raise ValueError('evidence integrity check failed')
                    body = raw.decode('utf-8')
                else:
                    entry = next((e for e in state['entries'] if e['id'] == args.event_id), None)
                    if entry is None:
                        raise ValueError('unknown memory entry or evidence event ID')
                    body = json.dumps(entry, ensure_ascii=False)
                    kind = 'entry'
                result = {'ok': True, 'event_id': args.event_id, 'chars': len(body),
                          'truncated_for_display': len(body) > args.max_chars}
                if len(body) <= args.max_chars:
                    result[kind] = json.loads(body)
                else:
                    result['preview'] = body[:args.max_chars]
            elif args.command == 'update':
                if args.proposal_json is not None:
                    proposal = json.loads(args.proposal_json)
                elif args.proposal == '-':
                    proposal = json.load(sys.stdin)
                else:
                    proposal = json.loads(Path(args.proposal).read_text(encoding='utf-8'))
                result = core.apply_update(repo, proposal)
            elif args.command in ('handoff', 'share'):
                if args.max_summary_chars < 1:
                    raise ValueError('--max-summary-chars must be positive')
                result = core.write_document(
                    repo, out=args.out, visibility='public' if args.command == 'share' else 'private',
                    include_patch=args.include_patch, max_summary_chars=args.max_summary_chars,
                )
            elif args.command == 'check':
                result = core.check_project(repo, document=args.document)
            elif args.command == 'import-legacy':
                result = core.import_legacy(repo, args.bundle)
            elif args.command == 'resolve-conflict':
                result = core.resolve_conflict(repo, args.conflict_id, args.base_revision,
                                               args.note, entry_ids=args.entry_id)
            elif args.command == 'withhold':
                result = core.withhold_entries(repo, args.entry_ids, args.base_revision, args.note)
            else:
                raise ValueError('unsupported command')
        emit(result)
        return 1 if isinstance(result, dict) and result.get('ok') is False else 0
    except (ValueError, OSError, KeyError, TypeError, ImportError, RuntimeError, subprocess.SubprocessError) as error:
        # Error messages must not echo full proposal bodies or credentials.
        try:
            from legacy_export import scrub
            message = scrub(str(error))[:1000]
        except ImportError:
            message = type(error).__name__
        emit({'ok': False, 'error': message})
        return 1


if __name__ == '__main__':
    sys.exit(main())
