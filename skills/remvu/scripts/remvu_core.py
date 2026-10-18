#!/usr/bin/env python3
"""Remvu's dependency-free, local project memory reference implementation.

Only observable evidence and explicit summaries are accepted. Stored content is
untrusted data: no logged command is ever executed by this module.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import time
import uuid

FORMAT = 'remvu/1'
STATE_FORMAT = 'remvu-state/1'
KINDS = {'goal', 'constraint', 'preference', 'architecture', 'decision', 'rejected',
         'progress', 'check', 'next_step', 'risk', 'change'}
BASES = {'user_confirmed', 'observed', 'inferred', 'unverified'}
SOURCE_TYPES = {'user', 'tool', 'file', 'url', 'event', 'legacy'}
EVENT_KINDS = {'message', 'tool_call', 'tool_result', 'edit', 'check', 'decision', 'hook'}
ENTRY_KEYS = {'id', 'kind', 'text', 'basis', 'visibility', 'sources', 'supersedes', 'result', 'exit_code'}
SOURCE_KEYS = {'type', 'label', 'excerpt', 'ref', 'visibility'}
EVENT_KEYS = {'kind', 'role', 'channel', 'text', 'tool', 'arguments', 'output', 'path', 'action',
              'patch', 'command', 'result', 'exit_code', 'call_id', 'platform', 'session_id',
              'turn_id', 'trigger', 'source_id', 'timestamp'}
SECTIONS = ('Start Here', 'Goals', 'Constraints and Preferences', 'Architecture and Code State',
            'Decisions and Rejected Directions', 'Changes and Progress', 'Checks and Evidence',
            'Open Work and Risks', 'Sources and History')
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
HEX = re.compile(r'[0-9a-f]{64}\Z')
PRIVATE_KEYS = {'reasoning', 'analysis', 'encrypted_content', 'base_instructions', 'system_prompt',
                'developer_instructions', 'system', 'developer', 'thinking', 'redacted_thinking',
                'signature', 'reasoning_content', 'encrypted_reasoning', 'chain_of_thought'}
PRIVATE_NODE_TYPES = {'reasoning', 'analysis', 'thinking', 'redacted_thinking', 'encrypted_reasoning'}
SECRET_KEY = re.compile(r'(?i)(?:password|passwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|cookie|credential)')
ASSIGNMENT = re.compile(r'''(?im)(["']?(?:[\w.-]*(?:password|passwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|token|credential|authorization|cookie)[\w.-]*)["']?\s*[:=]\s*)("[^"\n]*"|'[^'\n]*'|[^\s,;\r\n}]+)''')
LOCAL_PATH = re.compile(r'(?<![\w:/])(?:[A-Za-z]:[\\/][^\s<>"`]+|/(?:Users|home|private|tmp|var|Volumes|etc|root|opt)/[^\s<>"`]+|~/[^\s<>"`]+)')
PRIVATE_REF = re.compile(r'(?i)(?:\.remvu[/\\]|\.codex[/\\]sessions|\.claude[/\\]projects|(?:^|[\s/])\.env(?:\b|/)|blobs/[0-9a-f]{64}\.txt)')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def _hidden_node(value):
    return (isinstance(value, dict) and
            ((isinstance(value.get('type'), str) and value['type'] in PRIVATE_NODE_TYPES)
             or value.get('role') in ('system', 'developer') or value.get('channel') in ('analysis', 'reasoning')))


def scrub(value):
    """Best-effort credential redaction and hidden-field exclusion; not a PII oracle."""
    if isinstance(value, dict):
        if _hidden_node(value):
            return None
        return {str(k): ('[REDACTED]' if SECRET_KEY.search(str(k)) else scrub(v))
                for k, v in value.items() if str(k).lower() not in PRIVATE_KEYS}
    if isinstance(value, list):
        return [scrub(v) for v in value if not _hidden_node(v)]
    if not isinstance(value, str):
        return value
    value = re.sub(r'-----BEGIN [^-\n]*PRIVATE KEY-----.*?-----END [^-\n]*PRIVATE KEY-----', '[REDACTED PRIVATE KEY]', value, flags=re.S)
    value = re.sub(r'(?im)^(\s*(?:Authorization|Proxy-Authorization|Cookie|Set-Cookie)\s*:\s*).*$', r'\1[REDACTED]', value)
    value = re.sub(r'(?i)\b(Bearer|Basic)\s+[A-Za-z0-9+/_.=:-]+', r'\1 [REDACTED]', value)
    value = ASSIGNMENT.sub(lambda m: m[1] + '"[REDACTED]"', value)
    value = re.sub(r'\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b', '[REDACTED TOKEN]', value)
    value = re.sub(r'(?i)(--(?:password|token|api-key|secret)(?:=|\s+))(\S+)', r'\1[REDACTED]', value)
    value = re.sub(r'(https?://)[^\s/@:]+:[^\s/@]+@', r'\1[REDACTED]@', value)
    value = re.sub(r'(https?://)[^\s/@]+@', r'\1[REDACTED]@', value)
    return value.replace(str(Path.home()), '~')


def _public_text(text):
    text = scrub(text)
    text = LOCAL_PATH.sub('[LOCAL PATH]', text)
    text = PRIVATE_REF.sub('[PRIVATE REFERENCE]', text)
    return text


def _root(repo):
    p = Path(repo).expanduser().resolve()
    if not p.is_dir():
        raise ValueError('project directory does not exist')
    return p


def _memory(repo):
    path = _root(repo) / '.remvu'
    if path.is_symlink():
        raise ValueError('.remvu must not be a symlink')
    return path


def _safe_child(root, relative):
    rel = PurePosixPath(relative)
    if not isinstance(relative, str) or not relative or rel.is_absolute() or '..' in rel.parts or '\\' in relative or str(rel) != relative:
        raise ValueError('unsafe relative path')
    path = root.joinpath(*rel.parts)
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError('symlink paths are not allowed')
    return path


def _atomic(path, value):
    """Replace one file atomically; fsync so a crash never yields partial JSON."""
    if path.is_symlink():
        raise ValueError('refusing to replace symlink')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    for parent in path.parents:
        if parent.is_symlink():
            raise ValueError('symlink parent is not allowed')
    data = value if isinstance(value, str) else _json(value) + '\n'
    fd, name = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        os.chmod(name, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        if os.name != 'nt':
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)


@contextmanager
def _lock(repo, timeout=20):
    root = _memory(repo)
    root.mkdir(mode=0o700, exist_ok=True)
    lock = _safe_child(root, 'lock')
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    stream = os.fdopen(fd, 'r+b')
    locked = False
    start = time.monotonic()
    try:
        if os.name == 'nt':
            import msvcrt
            if os.fstat(fd).st_size == 0:
                stream.write(b'0'); stream.flush()
            while not locked:
                try:
                    stream.seek(0); msvcrt.locking(fd, msvcrt.LK_NBLCK, 1); locked = True
                except OSError:
                    if time.monotonic() - start > timeout:
                        raise ValueError('project memory lock is busy; retry later')
                    time.sleep(0.03)
        else:
            import fcntl
            while not locked:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); locked = True
                except BlockingIOError:
                    if time.monotonic() - start > timeout:
                        raise ValueError('project memory lock is busy; retry later')
                    time.sleep(0.03)
        yield root
    finally:
        if locked:
            if os.name == 'nt':
                stream.seek(0); msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(fd, fcntl.LOCK_UN)
        stream.close()


def _read_json(path):
    try:
        with path.open(encoding='utf-8') as stream:
            return json.load(stream)
    except (OSError, ValueError, UnicodeError) as error:
        raise ValueError('cannot read valid memory JSON: ' + path.name) from error


def _load_unlocked(root):
    path = _safe_child(root, 'state.json')
    if not path.exists():
        raise ValueError('memory is not initialized; run remvu init')
    state = _read_json(path)
    if not isinstance(state, dict) or state.get('format') != STATE_FORMAT:
        raise ValueError('unsupported or damaged memory state')
    expected = state.get('integrity')
    body = {k: v for k, v in state.items() if k != 'integrity'}
    if expected != _sha(_json(body)):
        raise ValueError('memory state integrity mismatch; preserve files and restore a verified snapshot')
    if type(state.get('revision')) is not int or not isinstance(state.get('entries'), list) or not isinstance(state.get('events'), list):
        raise ValueError('damaged memory state shape')
    return state


def _save(root, state, operation, payload):
    journal_id = uuid.uuid4().hex
    state['last_journal_id'] = journal_id
    state['updated_at'] = _now()
    state.pop('integrity', None)
    state['integrity'] = _sha(_json(state))
    # Journal first, then atomic snapshot. An orphan journal is detectable and is
    # deliberately never replayed as if it had committed.
    journal = {'format': 'remvu-journal/1', 'operation': operation, 'revision': state['revision'],
               'created_at': state['updated_at'], 'state_integrity': state['integrity'], 'payload': payload}
    _atomic(_safe_child(root, 'journal/' + journal_id + '.json'), journal)
    _atomic(_safe_child(root, 'state.json'), state)
    _atomic(_safe_child(root, 'snapshots/latest.json'), state)
    # A bounded set of committed states permits recovery if latest is damaged.
    # Evidence and journals are retained; pruning copies never prunes history.
    _atomic(_safe_child(root, 'snapshots/' + journal_id + '.json'), state)
    snapshots = sorted((p for p in _safe_child(root, 'snapshots').glob('*.json')
                        if re.fullmatch(r'[0-9a-f]{32}\.json', p.name)),
                       key=lambda p: (p.stat().st_mtime_ns, p.name), reverse=True)
    for old in snapshots[5:]:
        if old.is_symlink():
            raise ValueError('Refusing a symlinked recovery snapshot')
        old.unlink()


def _git(repo, *args, required=False):
    result = subprocess.run(['git', '-C', str(repo), '--no-pager', *args], capture_output=True, timeout=60,
                            env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
    if result.returncode:
        if required:
            raise ValueError('git inspection failed')
        return None
    return result.stdout.decode('utf-8', errors='surrogateescape')


def _ignored(name):
    return name == 'REMVU.md' or name == '.remvu' or name.startswith('.remvu/')


def _git_normalized_eol_paths(repo):
    """Recognize Git-authorized checkout EOL conversion without running filters.

    Only tracked text with CRLF worktree lines is eligible. Binary, untracked,
    mixed-EOL and explicitly -text files keep their exact bytes. The existing
    LF fingerprint remains unchanged on every platform.
    """
    autocrlf = (_git(repo, 'config', '--get', 'core.autocrlf') or '').strip().lower()
    configured = autocrlf in ('true', 'input')
    normalized = set()
    for row in (_git(repo, 'ls-files', '--eol', '-z', required=True) or '').split('\0'):
        if '\t' not in row:
            continue
        description, name = row.split('\t', 1)
        fields = description.split()
        if len(fields) < 2 or fields[1] != 'w/crlf':
            continue
        attributes = fields[2:]
        if fields[0] == 'i/-text' or any('-text' in value for value in attributes):
            continue
        auto_text = any(value in ('attr/text=auto', 'text=auto') for value in attributes)
        forced_text = (any(value in ('attr/text', 'text') for value in attributes)
                       or (not auto_text and any(value.startswith(('eol=', 'attr/eol='))
                                                 for value in attributes)))
        # Git's automatic policy preserves files historically stored with CRLF,
        # including text=auto plus eol. Only a forced text policy changes that.
        if forced_text or (fields[0] == 'i/lf' and (configured or auto_text)):
            normalized.add(name)
    return normalized


def _snapshot(repo):
    """Code-state fingerprint with declared Git text EOL normalization."""
    repo = _root(repo)
    try:
        top = _git(repo, 'rev-parse', '--show-toplevel')
    except (OSError, subprocess.SubprocessError):
        top = None
    is_git = bool(top and Path(top.strip()).resolve() == repo)
    commit = tree = remote = None
    tracked_modes = {}
    normalized_eol = set()
    dirty_paths = []
    if is_git:
        commit = _git(repo, 'rev-parse', '--verify', 'HEAD')
        tree = _git(repo, 'rev-parse', '--verify', 'HEAD^{tree}')
        remote = _git(repo, 'remote', 'get-url', 'origin')
        raw = _git(repo, 'ls-files', '-co', '--exclude-standard', '-z', required=True)
        names = sorted(set(x for x in raw.split('\0') if x and not _ignored(x)))
        normalized_eol = _git_normalized_eol_paths(repo)
        if os.name == 'nt':
            for row in (_git(repo, 'ls-files', '--stage', '-z', required=True) or '').split('\0'):
                if '\t' in row:
                    mode, name = row.split('\t', 1)
                    tracked_modes[name] = mode.split(' ', 1)[0] == '100755'
        status = _git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all', required=True).split('\0')
        index = 0
        while index < len(status):
            part = status[index]; index += 1
            if not part:
                continue
            name = part[3:]
            if not _ignored(name):
                dirty_paths.append(name)
            if 'R' in part[:2] or 'C' in part[:2]:
                if index < len(status):
                    old = status[index]; index += 1
                    if not _ignored(old):
                        dirty_paths.append(old)
    else:
        names = []
        for directory, dirs, files in os.walk(repo, followlinks=False):
            dirs[:] = [d for d in dirs if d not in ('.git', '.remvu')]
            for name in files:
                relative = (Path(directory) / name).relative_to(repo).as_posix()
                if not _ignored(relative):
                    names.append(relative)
        names.sort()
    digest = hashlib.sha256()
    for name in names:
        path = repo / name
        digest.update(os.fsencode(name)); digest.update(b'\0')
        if path.is_symlink():
            data = b'link\0' + os.fsencode(os.readlink(path))
        elif path.is_file():
            try:
                executable = tracked_modes.get(name, False) if os.name == 'nt' else bool(os.lstat(path).st_mode & 0o111)
                contents = path.read_bytes()
                if name in normalized_eol:
                    contents = contents.replace(b'\r\n', b'\n')
                data = b'file\0' + (b'1' if executable else b'0') + b'\0' + contents
            except OSError as error:
                raise ValueError('cannot fingerprint project file') from error
        elif path.is_dir() and (path / '.git').exists():
            data = b'gitlink\0' + _json(_snapshot(path)).encode('utf-8')
        else:
            data = b'missing'
        digest.update(hashlib.sha256(data).digest())
        digest.update(b'\0')
    remote = scrub(remote.strip()) if remote else None
    if remote and (LOCAL_PATH.search(remote) or ('://' not in remote and not re.match(r'git@[^:]+:', remote))):
        remote = None
    return {'name': repo.name, 'remote': remote, 'commit': commit.strip() if commit else None,
            'tree': tree.strip() if tree else None, 'fingerprint': digest.hexdigest(),
            'dirty': bool(dirty_paths), 'git': is_git, 'dirty_paths': sorted(set(dirty_paths))}


def init_state(repo):
    with _lock(repo) as root:
        if _safe_child(root, 'state.json').exists():
            return _load_unlocked(root)
        state = {'format': STATE_FORMAT, 'project_id': 'p-' + uuid.uuid4().hex,
                 'revision': 0, 'updated_at': _now(), 'repo_snapshot': _snapshot(repo),
                 'entries': [], 'events': [], 'issues': [], 'pending_consolidation': False,
                 'consolidated_event_count': 0}
        _save(root, state, 'init', {})
        return state


def load_state(repo):
    with _lock(repo) as root:
        return _load_unlocked(root)


def _string(value, name, maximum=100000, required=False):
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise ValueError(name + ' must be a ' + ('nonempty ' if required else '') + 'string of at most ' + str(maximum) + ' characters')
    return scrub(value)


def _entry(raw):
    if not isinstance(raw, dict) or set(raw) - ENTRY_KEYS:
        raise ValueError('entry must be an object with only documented fields')
    if not isinstance(raw.get('kind'), str) or raw['kind'] not in KINDS or not isinstance(raw.get('basis'), str) or raw['basis'] not in BASES:
        raise ValueError('invalid entry kind or basis')
    visibility = raw.get('visibility', 'private')
    if visibility not in ('private', 'public'):
        raise ValueError('invalid entry visibility')
    sources = raw.get('sources', [])
    if not isinstance(sources, list) or len(sources) > 100:
        raise ValueError('sources must be a list of at most 100 citations')
    clean_sources = []
    for source in sources:
        if not isinstance(source, dict) or set(source) - SOURCE_KEYS or not isinstance(source.get('type'), str) or source['type'] not in SOURCE_TYPES:
            raise ValueError('invalid citation or unsupported citation fields')
        source = dict(source)
        source.setdefault('visibility', 'private')
        if source['visibility'] not in ('private', 'public'):
            raise ValueError('invalid citation visibility')
        for key, maximum in (('label', 500), ('excerpt', 100000), ('ref', 2000)):
            if key in source:
                source[key] = _string(source[key], 'source ' + key, maximum)
        if 'ref' in source:
            ref = source['ref']
            if any(ord(c) < 32 for c in ref):
                raise ValueError('citation ref cannot contain control characters')
            if source['type'] == 'url':
                if not re.match(r'https?://[^\s]+\Z', ref) or '[REDACTED]' in ref:
                    raise ValueError('URL citations need an HTTP(S) URL without credentials')
            elif source['type'] == 'file':
                rel = PurePosixPath(ref)
                if not ref or rel.is_absolute() or '..' in rel.parts or '\\' in ref or str(rel) != ref:
                    raise ValueError('file citation ref must be a safe repository-relative path')
        clean_sources.append(source)
    supersedes = raw.get('supersedes', [])
    if not isinstance(supersedes, list) or len(supersedes) > 1000 or any(not isinstance(x, str) or not ID.fullmatch(x) for x in supersedes):
        raise ValueError('supersedes must contain at most 1000 entry IDs')
    value = {'kind': raw['kind'], 'text': _string(raw.get('text'), 'entry text', required=True),
             'basis': raw['basis'], 'visibility': visibility, 'sources': clean_sources,
             'supersedes': list(dict.fromkeys(supersedes))}
    flags = []
    if not clean_sources or not any(x.get('excerpt', '').strip() for x in clean_sources):
        flags.append('unsupported_source')
    if raw['basis'] == 'user_confirmed' and not any(x['type'] == 'user' and x.get('excerpt', '').strip() for x in clean_sources):
        flags.append('basis_source_mismatch')
    if raw['basis'] == 'observed' and not any(x['type'] in ('tool', 'file', 'event', 'url') and x.get('excerpt', '').strip() for x in clean_sources):
        flags.append('basis_source_mismatch')
    if raw['kind'] == 'check':
        result = raw.get('result', 'unknown')
        if result not in ('passed', 'failed', 'unknown'):
            raise ValueError('invalid check result')
        code = raw.get('exit_code')
        if code is not None and type(code) is not int:
            raise ValueError('check exit_code must be an integer or null')
        if code is not None:
            value['exit_code'] = code
        supported = raw['basis'] == 'observed' and any(s['type'] == 'tool' and s.get('excerpt', '').strip() for s in clean_sources)
        if code not in (None, 0):
            if result != 'failed':
                flags.append('result_contradicted_by_exit_code')
            result = 'failed'
        elif result == 'passed' and not (code == 0 and supported):
            flags.append('unsupported_pass_claim')
            value['claimed_result'] = 'passed'
            result = 'unknown'
        value['result'] = result
    elif 'result' in raw or 'exit_code' in raw:
        raise ValueError('result and exit_code are only valid on check entries')
    if 'id' in raw and (not isinstance(raw['id'], str) or not ID.fullmatch(raw['id'])):
        raise ValueError('invalid entry id')
    value['id'] = raw.get('id') or 'm-' + _sha(_json(value))[:16]
    if value['id'] in value['supersedes']:
        raise ValueError('an entry cannot supersede itself')
    value['flags'] = flags
    return value


def apply_update(repo, proposal):
    if not isinstance(proposal, dict) or set(proposal) - {'base_revision', 'base_event_count', 'entries'}:
        raise ValueError('proposal supports base_revision, optional base_event_count and entries only')
    if type(proposal.get('base_revision')) is not int or proposal['base_revision'] < 0:
        raise ValueError('base_revision must be a nonnegative integer')
    if not isinstance(proposal.get('entries'), list) or len(proposal['entries']) > 1000:
        raise ValueError('entries must be a list of at most 1000 entries')
    if 'base_event_count' in proposal and (type(proposal['base_event_count']) is not int or proposal['base_event_count'] < 0):
        raise ValueError('base_event_count must be a nonnegative integer')
    entries = [_entry(x) for x in proposal['entries']]
    if len({e['id'] for e in entries}) != len(entries):
        raise ValueError('duplicate entry ids in proposal')
    with _lock(repo) as root:
        state = _load_unlocked(root)
        event_count = len(state['events'])
        if proposal.get('base_event_count', 0) > event_count:
            raise ValueError('base_event_count exceeds the observed event count')
        if proposal['base_revision'] != state['revision']:
            conflict = {'format': 'remvu-conflict/1', 'created_at': _now(), 'base_revision': proposal['base_revision'],
                        'actual_revision': state['revision'], 'entries': entries,
                        'proposal': scrub(proposal),
                        'reason': 'stale revision; reload and reconcile rather than overwrite'}
            conflict_id = 'c-' + _sha(_json({'base_revision': proposal['base_revision'], 'entries': entries,
                                           'base_event_count': proposal.get('base_event_count')}))[:20]
            _atomic(_safe_child(root, 'conflicts/' + conflict_id + '.json'), conflict)
            return {'ok': False, 'revision': state['revision'], 'applied_ids': [],
                    'conflicts': [conflict_id], 'reason': conflict['reason']}
        by_id = {e['id']: e for e in state['entries']}
        for entry in entries:
            if entry['id'] in by_id:
                old = {k: v for k, v in by_id[entry['id']].items()
                       if k not in ('created_at', 'added_revision', 'superseded_by', 'observed_code')}
                if old != entry:
                    raise ValueError('entry ids are immutable; add a new entry with supersedes')
            for previous in entry['supersedes']:
                if previous not in by_id:
                    raise ValueError('supersedes references an unknown or same-proposal entry')
        new_entries = [e for e in entries if e['id'] not in by_id]
        snapshot = _snapshot(repo)
        state['revision'] += 1
        for entry in new_entries:
            entry['created_at'] = _now(); entry['added_revision'] = state['revision']; entry['superseded_by'] = []
            if entry['kind'] == 'check':
                # Derived provenance is fixed when the check is first recorded.
                # Resubmitting the same ID cannot silently revalidate old evidence.
                entry['observed_code'] = {key: snapshot[key] for key in ('fingerprint', 'commit')}
            for previous in entry['supersedes']:
                by_id[previous].setdefault('superseded_by', []).append(entry['id'])
            state['entries'].append(entry)
        state['repo_snapshot'] = snapshot
        # Events do not advance the semantic revision. A proposal acknowledges
        # only the prefix the author explicitly observed, never racing arrivals.
        previous_count = state.get('consolidated_event_count', 0)
        if type(previous_count) is not int or not 0 <= previous_count <= event_count:
            raise ValueError('invalid consolidated event watermark')
        state['consolidated_event_count'] = max(previous_count, proposal.get('base_event_count', 0))
        state['pending_consolidation'] = state['consolidated_event_count'] < event_count
        _save(root, state, 'apply_update', {'base_revision': proposal['base_revision'],
                                          'base_event_count': proposal.get('base_event_count'),
                                          'consolidated_event_count': state['consolidated_event_count'],
                                          'entry_ids': [e['id'] for e in new_entries]})
        return {'ok': True, 'revision': state['revision'], 'applied_ids': [e['id'] for e in new_entries], 'conflicts': [],
                'pending_consolidation': state['pending_consolidation'], 'event_count': event_count,
                'consolidated_event_count': state['consolidated_event_count'],
                'unconsolidated_event_count': event_count - state['consolidated_event_count']}


def _resolved_conflict_valid(root, resolution):
    if not isinstance(resolution, dict) or not isinstance(resolution.get('ref'), str):
        return False
    if not isinstance(resolution.get('sha256'), str) or not HEX.fullmatch(resolution['sha256']):
        return False
    path = _safe_child(root, resolution['ref'])
    return path.is_file() and _sha(path.read_bytes()) == resolution['sha256']


def _unresolved_conflicts(root, state):
    resolved = state.get('resolved_conflicts', {})
    if not isinstance(resolved, dict):
        raise ValueError('invalid conflict resolution index')
    active = {path.stem for path in _safe_child(root, 'conflicts').glob('*.json')}
    # A damaged archive cannot erase an outstanding conflict.
    active.update(conflict_id for conflict_id, resolution in resolved.items()
                  if not _resolved_conflict_valid(root, resolution))
    return sorted(conflict_id for conflict_id in active
                  if not _resolved_conflict_valid(root, resolved.get(conflict_id)))


def resolve_conflict(repo, conflict_id, base_revision, note, entry_ids=None):
    """Record an explicit reconciliation without deleting the original proposal."""
    if not isinstance(conflict_id, str) or not re.fullmatch(r'c-[0-9a-f]{20}', conflict_id):
        raise ValueError('invalid conflict id')
    if type(base_revision) is not int or base_revision < 0:
        raise ValueError('base_revision must be a nonnegative integer')
    note = _string(note, 'resolution note', maximum=10000, required=True)
    entry_ids = [] if entry_ids is None else entry_ids
    if (not isinstance(entry_ids, list) or len(entry_ids) > 1000
            or any(not isinstance(item, str) or not ID.fullmatch(item) for item in entry_ids)
            or len(set(entry_ids)) != len(entry_ids)):
        raise ValueError('entry_ids must be a list of distinct existing entry IDs')
    with _lock(repo) as root:
        state = _load_unlocked(root)
        if base_revision != state['revision']:
            return {'ok': False, 'revision': state['revision'], 'conflict_id': conflict_id,
                    'reason': 'stale revision; reload memory before resolving a conflict'}
        resolved = state.setdefault('resolved_conflicts', {})
        if not isinstance(resolved, dict):
            raise ValueError('invalid conflict resolution index')
        if conflict_id in resolved:
            if not _resolved_conflict_valid(root, resolved[conflict_id]):
                raise ValueError('existing conflict resolution archive is missing or damaged')
            return {'ok': True, 'already_resolved': True, 'revision': state['revision'],
                    'conflict_id': conflict_id, 'conflicts': _unresolved_conflicts(root, state)}
        known = {entry['id'] for entry in state['entries']}
        if any(item not in known for item in entry_ids):
            raise ValueError('resolution references an unknown entry ID')
        original = _safe_child(root, 'conflicts/' + conflict_id + '.json')
        if not original.is_file():
            raise ValueError('unknown unresolved conflict ID')
        conflict = _read_json(original)
        if not isinstance(conflict, dict) or conflict.get('format') != 'remvu-conflict/1':
            raise ValueError('invalid original conflict record')
        revision = state['revision'] + 1
        resolution = {'format': 'remvu-conflict-resolution/1', 'conflict_id': conflict_id,
                      'base_revision': base_revision, 'resolved_revision': revision, 'resolved_at': _now(),
                      'note': note, 'entry_ids': entry_ids, 'original_conflict': conflict}
        ref = ('conflicts/resolved/' + conflict_id + '-r' + str(revision) + '-'
               + _sha(_json(resolution))[:12] + '.json')
        _atomic(_safe_child(root, ref), resolution)
        resolved[conflict_id] = {'ref': ref, 'sha256': _sha(_json(resolution) + '\n'),
                                 'revision': revision, 'entry_ids': entry_ids}
        state['revision'] = revision
        _save(root, state, 'resolve_conflict', {'conflict_id': conflict_id, 'resolution_ref': ref,
                                              'entry_ids': entry_ids})
        # If interruption happens here, the committed resolution index still
        # recognizes this proposal as resolved; the archive retains its full body.
        original.unlink()
        return {'ok': True, 'revision': revision, 'conflict_id': conflict_id, 'resolution_ref': ref,
                'entry_ids': entry_ids, 'conflicts': _unresolved_conflicts(root, state),
                'pending_consolidation': state['pending_consolidation']}


def withhold_entries(repo, entry_ids, base_revision, note):
    """Narrow public visibility with an audit; existing shared files stay untouched."""
    if (not isinstance(entry_ids, list) or not entry_ids or len(entry_ids) > 1000
            or any(not isinstance(item, str) or not ID.fullmatch(item) for item in entry_ids)):
        raise ValueError('entry_ids must contain one to 1000 valid entry IDs')
    entry_ids = list(dict.fromkeys(entry_ids))
    if type(base_revision) is not int or base_revision < 0:
        raise ValueError('base_revision must be a nonnegative integer')
    note = _string(note, 'withdrawal note', maximum=10000, required=True)
    warning = ('Existing public files may still include withdrawn data. They were not rewritten or removed; '
               'review them and regenerate REMVU.md explicitly when appropriate.')
    with _lock(repo) as root:
        state = _load_unlocked(root)
        if base_revision != state['revision']:
            return {'ok': False, 'revision': state['revision'], 'withheld_ids': [], 'already_private_ids': [],
                    'reason': 'stale revision; reload memory before narrowing public scope', 'warning': warning}
        by_id = {entry['id']: entry for entry in state['entries']}
        if any(item not in by_id for item in entry_ids):
            raise ValueError('withdrawal references an unknown entry ID')
        if any(by_id[item].get('visibility') not in ('public', 'private') for item in entry_ids):
            raise ValueError('invalid entry visibility in stored memory')
        to_withhold = [item for item in entry_ids if by_id[item]['visibility'] == 'public']
        already_private = [item for item in entry_ids if by_id[item]['visibility'] == 'private']
        if to_withhold:
            audit = state.setdefault('share_withdrawals', [])
            if not isinstance(audit, list):
                raise ValueError('invalid share withdrawal audit index')
            originals = [json.loads(_json(by_id[item])) for item in to_withhold]
            revision, timestamp = state['revision'] + 1, _now()
            for item in to_withhold:
                by_id[item]['visibility'] = 'private'
                audit.append({'entry_id': item, 'from_visibility': 'public', 'to_visibility': 'private',
                              'revision': revision, 'note': note, 'at': timestamp})
            state['revision'] = revision
            # Deliberately leave code provenance and the event watermark intact.
            _save(root, state, 'withhold_entries', {'base_revision': base_revision, 'entry_ids': to_withhold,
                                                   'note': note, 'original_public_entries': originals})
        return {'ok': True, 'revision': state['revision'], 'withheld_ids': to_withhold,
                'already_private_ids': already_private, 'pending_consolidation': state['pending_consolidation'],
                'event_count': len(state['events']),
                'consolidated_event_count': state.get('consolidated_event_count', 0), 'warning': warning}


def _check_is_stale(entry, snapshot):
    observed = entry.get('observed_code')
    return (not isinstance(observed, dict)
            or observed.get('fingerprint') != snapshot['fingerprint'])


def _stale_checks(state, snapshot):
    return [entry for entry in state['entries'] if entry['kind'] == 'check'
            and not entry.get('superseded_by') and _check_is_stale(entry, snapshot)]


def record_event(repo, event):
    if not isinstance(event, dict) or not isinstance(event.get('kind'), str) or event['kind'] not in EVENT_KINDS:
        raise ValueError('unsupported observable event kind')
    if event.get('channel') not in (None, 'final', 'commentary') or event.get('role') in ('system', 'developer'):
        return {'excluded': True, 'reason': 'hidden reasoning or instructions are outside observable evidence'}
    clean = scrub({k: v for k, v in event.items() if k in EVENT_KEYS})
    if clean['kind'] == 'message' and clean.get('role') not in ('user', 'assistant'):
        raise ValueError('message events require user or assistant role')
    body = _json(clean)
    if len(body) > 5 * 1024 * 1024:
        raise ValueError('event exceeds 5 MiB; store a bounded observable excerpt with omissions')
    event_id = 'e-' + _sha(body)[:24]
    with _lock(repo) as root:
        state = _load_unlocked(root)
        if any(e['id'] == event_id for e in state['events']):
            return {'event_id': event_id, 'deduplicated': True, 'revision': state['revision'],
                    'pending_consolidation': state['pending_consolidation']}
        ref = 'blobs/' + _sha(body) + '.json'
        blob = _safe_child(root, ref)
        if blob.exists():
            if blob.read_text(encoding='utf-8') != body:
                raise ValueError('existing evidence blob integrity mismatch')
        else:
            _atomic(blob, body)
        state['events'].append({'id': event_id, 'kind': clean['kind'], 'blob_ref': ref,
                                'sha256': _sha(body), 'recorded_at': _now()})
        state['pending_consolidation'] = True
        _save(root, state, 'record_event', {'event_id': event_id, 'blob_ref': ref})
        return {'event_id': event_id, 'deduplicated': False, 'revision': state['revision'], 'pending_consolidation': True}


def _escape(text):
    # Evidence stays inert Markdown text; user content cannot inject headings/fences.
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\\', '\\\\').replace('`', '\\`').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('#', '\\#').replace('\n', '\n  ')


def _check_public_entry(entry):
    remedy = (' Existing entry sources are immutable; withhold this entry, then create a new '
              'self-contained public entry with shareable inline excerpts.')
    if not entry['sources']:
        raise ValueError('public entry ' + entry['id'] + ' has no inline sources.' + remedy)
    for source in entry['sources']:
        if source['visibility'] != 'public' or not source.get('excerpt', '').strip():
            raise ValueError('public entry ' + entry['id'] + ' depends on a private or missing excerpt.' + remedy)
        if source.get('ref') and source['type'] in ('file', 'url'):
            if LOCAL_PATH.search(source['ref']) or PRIVATE_REF.search(source['ref']):
                raise ValueError('public entry ' + entry['id'] + ' source ref points to private data.' + remedy)


def _line(entry, visibility, public_ids=None, snapshot=None):
    clean = _public_text if visibility == 'public' else scrub
    states = ['superseded' if entry.get('superseded_by') else 'active']
    label = entry['kind'] + '; ' + entry['basis'] + '; visibility=' + entry['visibility'] + '; state=' + states[0]
    if entry['kind'] == 'check':
        label += '; result=' + entry.get('result', 'unknown')
        if 'exit_code' in entry:
            label += '; exit_code=' + str(entry['exit_code'])
        label += '; evidence=' + ('historical/stale' if snapshot is None or _check_is_stale(entry, snapshot) else 'current-code')
    lines = ['- **' + entry['id'] + '** [' + label + '] ' + _escape(clean(entry['text']))]
    if entry.get('flags'):
        lines += ['  Evidence flags: ' + ', '.join(entry['flags']) + '.']
    if entry['kind'] == 'check':
        observed = entry.get('observed_code', {})
        lines += ['  Observed code fingerprint: ' + str(observed.get('fingerprint', 'unknown'))
                  + '; commit: ' + str(observed.get('commit') or 'unavailable') + '.']
        if snapshot is None or _check_is_stale(entry, snapshot):
            lines += ['  Historical check evidence: this result does not validate the current code. '
                      'Record a new check with supersedes after revalidation.']
    for key in ('supersedes', 'superseded_by'):
        ids = entry.get(key, [])
        if visibility == 'public':
            missing = [i for i in ids if i not in public_ids]
            if missing:
                raise ValueError('public entry ' + entry['id'] + ' history crosses private entries; '
                                 'history is immutable. Withhold the mistakenly public entry, then create a new '
                                 'self-contained public summary without private entry IDs.')
        if ids:
            lines += ['  ' + key.replace('_', ' ').capitalize() + ': ' + ', '.join(ids) + '.']
    for number, source in enumerate(entry['sources'], 1):
        ref = source.get('ref', '')
        # Internal event/blob/legacy references do not travel; excerpts do.
        if visibility == 'public' and source['type'] not in ('file', 'url'):
            ref = ''
        label = source.get('label') or source['type']
        detail = (' (' + ref + ')') if ref else ''
        lines += ['  Source ' + str(number) + ' [' + source['type'] + ']: ' + _escape(clean(label + detail)) + '.']
        if source.get('excerpt'):
            lines += ['  Excerpt: ' + _escape(clean(source['excerpt']))]
    return '\n'.join(lines)


def _patch(repo, snapshot):
    if not snapshot['git'] or not snapshot['commit']:
        raise ValueError('patch export requires an existing Git commit')
    paths = snapshot.get('dirty_paths', [])
    unsafe = [p for p in paths if PRIVATE_REF.search(p) or re.search(r'(?i)(?:^|/)(?:id_rsa|id_ed25519|credentials|secrets?)(?:\.|/|$)', p)]
    if unsafe:
        raise ValueError('patch touches potentially private files; commit or exclude them before sharing')
    if any((Path(repo) / p).is_symlink() for p in paths):
        raise ValueError('patch touches symlinks; inspect and commit them before sharing')
    tracked = _git(repo, 'diff', '--no-ext-diff', '--no-textconv', '--no-color', 'HEAD', '--', *paths, required=True) if paths else ''
    if '[REDACTED' in scrub(tracked) or LOCAL_PATH.search(tracked) or PRIVATE_REF.search(tracked):
        raise ValueError('patch contains credentials or private references; redact source changes before sharing')
    untracked = [p for p in (_git(repo, 'ls-files', '--others', '--exclude-standard', '-z', required=True) or '').split('\0') if p and not _ignored(p)]
    longest = max([len(x) for x in re.findall(r'`+', tracked)] or [0])
    fence = '`' * max(3, longest + 1)
    lines = ['## Patch', '', 'Explicitly requested review evidence. Inspect before applying; binary contents are not embedded.', '', fence + 'diff', tracked.rstrip(), fence, '']
    if untracked:
        lines += ['Unavailable resources: untracked file contents are not included; commit them before handing off.']
        lines += ['- ' + _escape(_public_text(p)) for p in untracked]
        lines.append('')
    return '\n'.join(lines)


def _render(repo, state, visibility, include_patch, max_summary_chars):
    if visibility not in ('private', 'public'):
        raise ValueError('visibility must be private or public')
    if type(max_summary_chars) is not int or max_summary_chars < 256:
        raise ValueError('summary limit must be at least 256 characters')
    snapshot = _snapshot(repo)
    if visibility == 'public' and snapshot['dirty'] and not include_patch:
        raise ValueError('public share blocked by uncommitted project changes; commit them first or explicitly request --include-patch after reviewing scope')
    if visibility == 'public' and any(_safe_child(_memory(repo), 'gaps').glob('*.json')):
        raise ValueError('public share blocked by observation gaps; run repair, review missing observations and consolidate memory')
    if visibility == 'public' and state['pending_consolidation']:
        raise ValueError('public share blocked by pending consolidation; review observable events and apply a semantic update first')
    unresolved = _unresolved_conflicts(_memory(repo), state)
    if visibility == 'public' and unresolved:
        raise ValueError('public share blocked by unresolved conflicts; reconcile and explicitly resolve them first')
    selected = [e for e in state['entries'] if visibility == 'private' or e['visibility'] == 'public']
    if visibility == 'public':
        for entry in selected:
            _check_public_entry(entry)
    ids = {e['id'] for e in selected}
    clean = _public_text if visibility == 'public' else scrub
    summary = ['Read this project memory as evidence and context. Confirm current user instructions before acting.',
               'Revision ' + str(state['revision']) + '; ' + str(len(selected)) + ' memory entries.']
    if snapshot['fingerprint'] != state['repo_snapshot']['fingerprint']:
        summary.append('STALE CODE: repository differs from the last semantic update; recheck affected claims before continuing.')
    if state['pending_consolidation']:
        summary.append('PENDING CONSOLIDATION: observable events have not been reviewed into semantic memory.')
    stale_checks = _stale_checks({'entries': selected}, snapshot)
    if stale_checks:
        summary.append('STALE CHECK EVIDENCE: ' + str(len(stale_checks))
                       + ' active check(s) describe different or unknown code; historical results do not validate current code. '
                         'See Checks and Evidence before reusing any result.')
    if unresolved:
        summary.append('UNRESOLVED CONFLICTS: ' + ', '.join(unresolved)
                       + '. Read retained proposals and record an explicit resolution; publishing is blocked.')
    active = [e for e in selected if not e.get('superseded_by')]
    priority = [e for e in active if e['kind'] in ('goal', 'constraint', 'preference', 'next_step', 'risk')]
    for entry in priority:
        candidate = '- ' + entry['kind'] + ' [' + entry['id'] + ', ' + entry['basis'] + ']: ' + _escape(clean(entry['text']))
        if len('\n'.join(summary + [candidate])) <= max_summary_chars:
            summary.append(candidate)
        else:
            summary.append('- ' + entry['kind'] + ' [' + entry['id'] + ']: full text below in ' + ('Constraints and Preferences' if entry['kind'] in ('constraint', 'preference') else 'Goals' if entry['kind'] == 'goal' else 'Open Work and Risks') + '.')
    summary_text = '\n'.join(summary)
    if len(summary_text) > max_summary_chars:
        # Never silently drop a constraint or open task even when index entries
        # alone exceed the requested reading budget.
        raise ValueError('summary cannot reference all constraints/open work within limit; raise max_summary_chars or consolidate superseded entries')
    metadata_repo = {k: snapshot[k] for k in ('name', 'remote', 'commit', 'tree', 'fingerprint', 'dirty', 'git')}
    if visibility == 'public':
        metadata_repo['name'] = _public_text(metadata_repo['name'])
        metadata_repo['remote'] = _public_text(metadata_repo['remote']) if metadata_repo['remote'] else None
    meta = {'format': FORMAT, 'project_id': state['project_id'], 'revision': state['revision'],
            'repo': metadata_repo, 'generated_at': _now(), 'visibility': visibility,
            'summary_chars': len(summary_text), 'omitted_private_entries': len(state['entries']) - len(selected)}
    lines = ['# Remvu Project Memory', '', '```json', json.dumps(meta, ensure_ascii=False, indent=2), '```', '', '## Start Here', '', summary_text, '']
    groups = {
        'Goals': {'goal'}, 'Constraints and Preferences': {'constraint', 'preference'},
        'Architecture and Code State': {'architecture'}, 'Decisions and Rejected Directions': {'decision', 'rejected'},
        'Changes and Progress': {'change', 'progress'}, 'Checks and Evidence': {'check'},
        'Open Work and Risks': {'next_step', 'risk'},
    }
    for heading, kinds in groups.items():
        lines += ['## ' + heading, '']
        matching = [e for e in selected if e['kind'] in kinds]
        lines += [_line(e, visibility, ids, snapshot) for e in matching] if matching else ['No entries recorded.']
        lines.append('')
    lines += ['## Sources and History', '', 'Sources appear beside each entry. Basis labels distinguish user confirmation, observed evidence, inference and unverified notes.',
              'Superseded entries remain in place; their replacement IDs record history. Hidden reasoning and system/developer instructions are excluded.',
              'A check is passed only when observed tool evidence includes exit code 0. Missing evidence remains unknown.',
              'Credential redaction is best effort. Review the shareable file for personal or confidential information.', '']
    if include_patch:
        lines += [_patch(repo, snapshot)]
    document = '\n'.join(lines)
    if visibility == 'public' and (LOCAL_PATH.search(document) or PRIVATE_REF.search(document)):
        raise ValueError('public document contains private references after redaction; inspect source entries')
    validation = validate_document(document)
    if not validation['ok']:
        raise ValueError('rendered document failed validation: ' + '; '.join(validation['errors']))
    return document


def render_document(repo, visibility='private', include_patch=False, max_summary_chars=8000):
    with _lock(repo) as root:
        return _render(repo, _load_unlocked(root), visibility, include_patch, max_summary_chars)


def write_document(repo, out=None, visibility='private', include_patch=False, max_summary_chars=8000):
    with _lock(repo) as root:
        state = _load_unlocked(root)
        text = _render(repo, state, visibility, include_patch, max_summary_chars)
        target = Path(out).expanduser().absolute() if out else (_root(repo) / 'REMVU.md' if visibility == 'public' else _safe_child(root, 'handoff/REMVU.md'))
        _atomic(target, text)
        return {'ok': True, 'path': str(target), 'visibility': visibility, 'revision': state['revision'],
                'chars': len(text), 'sha256': _sha(text), 'validation': validate_document(text)}


def _markdown_structure(text):
    """Locate headings outside fences, retaining exact offsets for summary counts."""
    headings, blocks, active, offset = [], [], None, 0
    for line in text.splitlines(keepends=True):
        body = line.rstrip('\r\n')
        if active is not None:
            close = re.fullmatch(r' {0,3}' + re.escape(active['character'])
                                 + '{' + str(active['length']) + r',}[ \t]*', body)
            if close:
                blocks.append({**active, 'body': text[active['content_start']:offset],
                               'end': offset + len(line)})
                active = None
        else:
            opening = re.fullmatch(r' {0,3}(`{3,}|~{3,})([^\r\n]*)', body)
            if opening:
                active = {'character': opening[1][0], 'length': len(opening[1]),
                          'info': opening[2].strip(), 'start': offset,
                          'content_start': offset + len(line)}
            else:
                heading = re.fullmatch(r' {0,3}##(?:[ \t]+(.*)|[ \t]*)', body)
                if heading:
                    name = re.sub(r'[ \t]+#+[ \t]*$', '', heading[1] or '').strip()
                    headings.append({'name': name, 'start': offset, 'content_start': offset + len(line)})
        offset += len(line)
    return headings, blocks, active is not None


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key')
        result[key] = value
    return result


def validate_document(text):
    errors, warnings, meta = [], [], None
    if not isinstance(text, str):
        return {'ok': False, 'errors': ['document must be text'], 'warnings': [], 'metadata': None}
    headings, blocks, unterminated = _markdown_structure(text)
    if unterminated:
        errors.append('unterminated fenced block')
    if not blocks or blocks[0]['info'] != 'json':
        errors.append('first fenced block must contain JSON metadata')
    else:
        try:
            meta = json.loads(blocks[0]['body'], object_pairs_hook=_unique_json_object)
        except (ValueError, TypeError):
            errors.append('invalid JSON metadata')
        if not isinstance(meta, dict):
            errors.append('metadata must be an object')
        if headings and blocks[0]['end'] > headings[0]['start']:
            errors.append('metadata must precede the standard sections')
    if isinstance(meta, dict):
        required = {'format', 'project_id', 'revision', 'repo', 'generated_at', 'visibility', 'summary_chars', 'omitted_private_entries'}
        if not required.issubset(meta):
            errors.append('missing required metadata fields')
        if set(meta) - required:
            errors.append('unsupported metadata fields')
        if meta.get('format') != FORMAT:
            errors.append('unsupported document format')
        if not isinstance(meta.get('project_id'), str) or not ID.fullmatch(meta.get('project_id', '')):
            errors.append('invalid project_id')
        for key in ('revision', 'summary_chars', 'omitted_private_entries'):
            if type(meta.get(key)) is not int or meta.get(key, -1) < 0:
                errors.append('invalid ' + key)
        if meta.get('visibility') not in ('public', 'private'):
            errors.append('invalid visibility')
        repo = meta.get('repo')
        repo_keys = {'name', 'remote', 'commit', 'tree', 'fingerprint', 'dirty', 'git'}
        if not isinstance(repo, dict) or set(repo) != repo_keys:
            errors.append('invalid repository metadata')
        else:
            if not isinstance(repo.get('fingerprint'), str) or not HEX.fullmatch(repo['fingerprint']):
                errors.append('invalid repository fingerprint')
            if (not isinstance(repo.get('name'), str) or type(repo.get('dirty')) is not bool
                    or type(repo.get('git')) is not bool
                    or any(repo.get(key) is not None and not isinstance(repo.get(key), str)
                           for key in ('remote', 'commit', 'tree'))):
                errors.append('invalid repository metadata types')
        try:
            timestamp = meta.get('generated_at')
            if (not isinstance(timestamp, str)
                    or not re.fullmatch(r'\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:[0-5]\d)', timestamp)):
                raise ValueError('timestamp must be timezone-aware RFC3339')
            stamp = datetime.fromisoformat(timestamp.upper().replace('Z', '+00:00'))
            if stamp.tzinfo is None or stamp.utcoffset() is None:
                raise ValueError('timestamp must include timezone')
        except (ValueError, TypeError, AttributeError):
            errors.append('invalid generated_at timestamp; a timezone is required')
        if meta.get('visibility') == 'public' and (LOCAL_PATH.search(text) or PRIVATE_REF.search(text)):
            errors.append('public document contains private paths or attachment references')
    names = [heading['name'] for heading in headings]
    for name in names:
        if name not in SECTIONS and name != 'Patch':
            errors.append('unsupported second-level heading: ' + name)
    positions = []
    for section in SECTIONS:
        matches = [i for i, heading in enumerate(headings) if heading['name'] == section]
        if len(matches) != 1:
            errors.append('required section missing or repeated: ' + section)
        else:
            positions.append(matches[0])
    if len(positions) == len(SECTIONS) and positions != sorted(positions):
        errors.append('sections must follow the standard order')
    if names.count('Patch') > 1 or ('Patch' in names and names[-1] != 'Patch'):
        errors.append('optional Patch section must occur once after the standard sections')
    if len(positions) == len(SECTIONS) and positions == sorted(positions):
        start, end = headings[positions[0]], headings[positions[1]]
        summary = text[start['content_start']:end['start']].strip('\r\n')
        if isinstance(meta, dict) and meta.get('summary_chars') != len(summary):
            errors.append('summary_chars does not match the first-read summary')
    if '[REDACTED' in text:
        warnings.append('document contains redacted values; verify they do not hide required context')
    return {'ok': not errors, 'errors': errors, 'warnings': warnings, 'metadata': meta}


def _document_issues(document, snapshot, state=None):
    target = Path(document)
    if target.is_symlink():
        raise ValueError('document must not be a symlink')
    result = validate_document(target.read_text(encoding='utf-8'))
    if not result['ok']:
        return [{'code': 'invalid_document', 'message': '; '.join(result['errors'])}]
    metadata, issues = result['metadata'], []
    if metadata['repo']['fingerprint'] != snapshot['fingerprint']:
        issues.append({'code': 'stale_document', 'message': 'document describes a different code state'})
    if state is not None:
        if metadata['project_id'] != state['project_id']:
            issues.append({'code': 'wrong_project', 'message': 'document belongs to another project'})
        if metadata['revision'] != state['revision']:
            issues.append({'code': 'stale_revision', 'message': 'document describes a different memory revision'})
    return issues


def check_project(repo, document=None):
    issues = []
    try:
        memory = _memory(repo)
        if not memory.exists():
            if document is None:
                raise ValueError('memory is not initialized; run remvu init or inspect a standalone document')
            snapshot = _snapshot(repo)
            issues = _document_issues(document, snapshot)
            return {'ok': not issues, 'issues': issues, 'revision': None, 'current_snapshot': snapshot,
                    'pending_consolidation': False, 'standalone': True}
        if not _safe_child(memory, 'state.json').is_file():
            raise ValueError('private memory directory has no valid state; preserve it and repair before use')
        with _lock(repo) as root:
            state = _load_unlocked(root)
            snapshot = _snapshot(repo)
            if state['repo_snapshot']['fingerprint'] != snapshot['fingerprint']:
                issues.append({'code': 'stale_code', 'message': 'code differs from the last semantic memory update'})
            for check in _stale_checks(state, snapshot):
                issues.append({'code': 'stale_check_evidence', 'entry_id': check['id'],
                               'message': 'active check evidence describes different or unknown code; '
                                          'revalidate and add a new superseding check'})
            if state['pending_consolidation']:
                issues.append({'code': 'pending_consolidation', 'message': 'observable events await semantic review'})
            if any(_safe_child(root, 'gaps').glob('*.json')):
                issues.append({'code': 'observation_gap', 'message': 'a hook failed; repair can index the gap but cannot reconstruct unobserved work'})
            journal_id = state.get('last_journal_id', '')
            if not re.fullmatch(r'[0-9a-f]{32}', journal_id):
                issues.append({'code': 'invalid_journal_head', 'message': 'memory has no valid committed journal head'})
            else:
                head = _safe_child(root, 'journal/' + journal_id + '.json')
                head_record = _read_json(head) if head.is_file() else {}
                if not isinstance(head_record, dict) or head_record.get('state_integrity') != state['integrity']:
                    issues.append({'code': 'journal_integrity_mismatch', 'message': 'committed journal does not match state'})
                for path in _safe_child(root, 'journal').glob('*.json'):
                    if path.name == journal_id + '.json':
                        continue
                    record = _read_json(path)
                    if not isinstance(record, dict):
                        raise ValueError('invalid memory journal record')
                    if record.get('created_at', '') > state['updated_at']:
                        issues.append({'code': 'uncommitted_journal', 'message': 'interrupted journal is preserved and has not been replayed'})
                        break
            for event in state['events']:
                ref = event.get('blob_ref', '')
                if not re.fullmatch(r'blobs/[0-9a-f]{64}\.json', ref):
                    issues.append({'code': 'invalid_blob_ref', 'message': 'invalid evidence reference'})
                    continue
                path = _safe_child(root, ref)
                if not path.is_file() or _sha(path.read_bytes()) != event['sha256']:
                    issues.append({'code': 'missing_or_damaged_evidence', 'event_id': event['id'], 'message': 'evidence integrity check failed'})
            if _unresolved_conflicts(root, state):
                issues.append({'code': 'unresolved_conflicts', 'message': 'stale proposals are preserved; reconcile them explicitly'})
            if document is not None:
                issues.extend(_document_issues(document, snapshot, state))
            return {'ok': not issues, 'issues': issues, 'revision': state['revision'], 'current_snapshot': snapshot,
                    'pending_consolidation': state['pending_consolidation']}
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return {'ok': False, 'issues': [{'code': 'inspection_failed', 'message': scrub(str(error))}]}


def _legacy_module():
    path = Path(__file__).resolve().parent / 'legacy_export.py'
    if not path.is_file():
        path = Path(__file__).resolve().parents[2] / 'agent-task-export/scripts/task_export.py'
    if not path.is_file():
        raise ValueError('legacy import requires the bundled agent-task-export compatibility skill')
    spec = importlib.util.spec_from_file_location('_remvu_legacy', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def import_legacy(repo, bundle):
    legacy = _legacy_module()
    path = Path(bundle).expanduser().absolute()
    # Existing verifier rejects traversal, symlinks, changed and unlisted files.
    manifest = legacy.verify_bundle(path)
    task = _read_json(path / 'task.json')
    if not isinstance(task, dict):
        raise ValueError('legacy task notes must be an object')
    entries = []
    names = {'goal': 'goal', 'outcome': 'progress', 'constraints': 'constraint', 'decisions': 'decision',
             'checks': 'check', 'next_steps': 'next_step', 'risks': 'risk'}
    for field, kind in names.items():
        values = task.get(field, [])
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError('invalid legacy task notes')
        for value in values:
            if value.strip():
                entry = {'kind': kind, 'text': value, 'basis': 'unverified', 'visibility': 'private',
                         'sources': [{'type': 'legacy', 'label': 'Verified legacy bundle; agent-authored notes are not independently verified',
                                      'excerpt': value, 'ref': 'task.json', 'visibility': 'private'}]}
                if kind == 'check':
                    entry['result'] = 'unknown'
                entries.append(entry)
    init_state(repo)
    # Import observable records too; content addressing makes retries safe.
    events = []
    with (path / 'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if not isinstance(row, dict) or row.get('kind') not in EVENT_KINDS:
                continue
            event = {k: v for k, v in row.items() if k in EVENT_KEYS}
            event['source_id'] = 'legacy:' + _sha(_json(manifest))[:16] + ':' + str(row.get('id', ''))
            for key in ('text', 'arguments', 'output', 'patch'):
                ref = row.get(key + '_ref')
                if ref:
                    if not legacy.SAFE_REF.fullmatch(ref) or ref not in manifest['files']:
                        raise ValueError('unsafe or unlisted legacy blob reference')
                    event[key] = legacy.contained(path, ref).read_text(encoding='utf-8')
            events.append(event)
    for event in events:
        record_event(repo, event)
    state = load_state(repo)
    result = apply_update(repo, {'base_revision': state['revision'],
                                 'base_event_count': len(state['events']), 'entries': entries})
    result['imported_events'] = len(events)
    result['legacy_integrity_verified'] = True
    return result
