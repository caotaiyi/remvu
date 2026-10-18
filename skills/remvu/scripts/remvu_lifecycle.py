"""Local installation, health and recovery. Never reads credentials or uploads data."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

import remvu_core as core
import remvu_init as setup


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def _write(path, value):
    setup._atomic(path, setup._json(value))


def _safe(path):
    path = Path(path).expanduser().absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Refusing a symlinked lifecycle destination')
    return path


def default_home():
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local'))) / 'Remvu'
    return Path.home() / '.local/share/remvu'


def preflight():
    return {'python_supported': sys.version_info >= (3, 10),
            'python': platform.python_version(), 'git_available': shutil.which('git') is not None,
            'clients_found': {name: shutil.which(name) is not None for name in ('claude', 'codex', 'code')},
            'system': platform.system(), 'machine': platform.machine()}


def _runtime_files(source):
    source = _safe(source)
    if source.name == 'scripts':
        source = source.parent
    if not (source / 'SKILL.md').is_file() or not (source / 'scripts/remvu.py').is_file():
        raise ValueError('--source must be a complete Remvu skill directory (or its scripts directory)')
    files = {}
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise ValueError('Runtime source contains a symlink')
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc' and path.name != '.runtime.json':
            files[path.relative_to(source).as_posix()] = path.read_bytes()
    return files


def _verify_runtime(skill):
    skill = _safe(skill)
    manifest = _read(_safe(skill / '.runtime.json'))
    if not isinstance(manifest, dict) or not isinstance(manifest.get('files'), dict) or not isinstance(manifest.get('version'), str):
        raise ValueError('Installed runtime checksum manifest is damaged; reinstall from reviewed source')
    files = _runtime_files(skill)
    hashes = {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}
    if manifest.get('files') != hashes:
        raise ValueError('Installed runtime differs from its recorded checksum manifest; reinstall from reviewed source')
    return manifest


def stage_runtime(source, home):
    home = _safe(home)
    files = _runtime_files(source)
    hashes = {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    match = re.search(rb"VERSION = '([^']+)'", files['scripts/remvu.py'])
    if not match or not re.fullmatch(rb'\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?', match[1]):
        raise ValueError('Runtime has no valid version')
    version = match[1].decode('ascii')
    releases = _safe(home / 'runtimes')
    releases.mkdir(parents=True, exist_ok=True)
    destination = _safe(releases / (version + '-' + digest[:16]))
    if destination.exists():
        _verify_runtime(destination)
        return destination
    staging = Path(tempfile.mkdtemp(prefix='.stage-', dir=str(releases)))
    try:
        for name, body in files.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        _write(staging / '.runtime.json', {'format': 'remvu-runtime/1', 'version': version, 'digest': digest, 'files': hashes})
        _verify_runtime(staging)
        try:
            staging.rename(destination)
        except OSError:
            if not destination.exists():
                raise
            _verify_runtime(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination


def _project_paths(repo):
    return [repo / name for name in (
        '.gitignore', 'CLAUDE.md', 'AGENTS.md', '.claude/settings.local.json', '.codex/hooks.json',
        '.claude/skills/remvu/SKILL.md', '.agents/skills/remvu/SKILL.md', '.remvu/adapters.json',
        '.remvu/installation.json', '.remvu/state.json', '.remvu/snapshots/latest.json')]


def _initialize_runtime(repo, platforms, scripts):
    # Let the selected release own its config generation and migrations, rather
    # than installing a new skill with the currently running release's adapter code.
    selection = 'both' if set(platforms) == {'claude', 'codex'} else platforms[0] if len(platforms) == 1 else 'none'
    process = subprocess.run([sys.executable, str(scripts / 'remvu.py'), 'init', '--repo', str(repo), '--platform', selection],
                             capture_output=True, encoding='utf-8', timeout=60,
                             env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    try:
        result = json.loads(process.stdout)
    except ValueError as error:
        raise ValueError('Selected runtime initialization failed; configuration checkpoint was retained') from error
    if process.returncode != 0 or not isinstance(result, dict) or result.get('ok') is not True:
        detail = core.scrub(str(result.get('error', 'inspect the reviewed runtime and retained checkpoint')))[:500] if isinstance(result, dict) else 'invalid result'
        raise ValueError('Selected runtime initialization failed: ' + detail)
    return result


@contextmanager
def _transaction(repo):
    paths = [_safe(path) for path in _project_paths(repo)]
    original = {path: path.read_bytes() if path.exists() else None for path in paths}
    # Keep a durable, private checkpoint for v0.2 migration and failed upgrades.
    checkpoint = _safe(repo / '.remvu/backups' / ('lifecycle-' + uuid.uuid4().hex))
    for path, body in original.items():
        if body is not None:
            target = checkpoint / path.relative_to(repo)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
    try:
        yield checkpoint
    except Exception:
        for path, body in original.items():
            # Initialization never overwrites existing semantic state. A live
            # hook may have written new events meanwhile; never roll those back.
            if path.name == 'state.json' or path.name == 'latest.json':
                continue
            if body is None:
                if path.exists():
                    path.unlink()
            else:
                setup._atomic(path, body.decode('utf-8'))
        raise


def install(repo, source=None, home=None, platforms=None, rollback=False):
    repo = _safe(repo).resolve()
    if not repo.is_dir():
        raise ValueError('Project directory must already exist')
    if sys.version_info < (3, 10):
        raise ValueError('Install Python 3.10+ using the official installer, then retry')
    if not shutil.which('git'):
        raise ValueError('Install Git using the official installer, then retry')
    path = _safe(repo / '.remvu/installation.json')
    old = _read(path) if path.exists() else {}
    adapter_path = _safe(repo / '.remvu/adapters.json')
    adapter = _read(adapter_path) if adapter_path.exists() else {}
    selected = tuple(platforms if platforms is not None else adapter.get('platforms', ('claude', 'codex')))
    if platforms is None and adapter.get('uninstalled_at'):
        selected = ('claude', 'codex')
    # Same advisory project lock as the core. Initialize takes that lock itself,
    # so use a separate lifecycle lock to serialize project configuration changes.
    from remvu_hooks import _ledger_lock
    with _ledger_lock(_safe(repo / '.remvu/lifecycle')):
        if rollback:
            previous = old.get('previous_scripts')
            if not previous:
                raise ValueError('No previous managed runtime is recorded')
            scripts = _safe(previous)
            _verify_runtime(scripts.parent)
        else:
            scripts = stage_runtime(source or Path(__file__).parent.parent, home or default_home()) / 'scripts'
        with _transaction(repo) as checkpoint:
            result = _initialize_runtime(repo, selected, scripts)
            current = old.get('scripts') or adapter.get('scripts_dir')
            if current and not (_safe(current).parent / '.runtime.json').is_file():
                current = None  # A v0.2 checkout is backed up, not a verified rollback runtime.
            previous = current if current and current != str(scripts) else old.get('previous_scripts')
            _write(path, {'format': 'remvu-installation/1', 'scripts': str(scripts),
                          'previous_scripts': previous, 'checkpoint': str(checkpoint.relative_to(repo)),
                          'platforms': list(selected), 'installed_at': core._now()})
    result.update(runtime_scripts=str(scripts), action='rollback' if rollback else 'install',
                  runtime_python=str(Path(sys.executable).resolve()),
                  activation='awaiting_host_review', preflight=preflight(),
                  note='Checksums detect local changes; they do not authenticate the publisher. Review the source/release.')
    return result


def _remove_block(text):
    if setup.BEGIN not in text and setup.END not in text:
        return text
    if text.count(setup.BEGIN) != 1 or text.count(setup.END) != 1:
        raise ValueError('Malformed managed block; inspect before uninstalling')
    start, end = text.index(setup.BEGIN), text.index(setup.END) + len(setup.END)
    if end < start:
        raise ValueError('Malformed managed block order')
    return text[:start] + text[end:]


def uninstall(repo):
    repo = _safe(repo).resolve()
    manifest_path = _safe(repo / '.remvu/adapters.json')
    if not manifest_path.exists():
        return {'ok': True, 'changed': [], 'memory_retained': True}
    manifest = _read(manifest_path)
    scripts = Path(manifest['scripts_dir'])
    from remvu_hooks import _ledger_lock
    with _ledger_lock(_safe(repo / '.remvu/lifecycle')):
        changes, removals = {}, []
        for client in manifest['platforms']:
            config_path = _safe(repo / ('.claude/settings.local.json' if client == 'claude' else '.codex/hooks.json'))
            if config_path.exists():
                config = setup._read_config(config_path)
                expected = list(manifest.get('handlers', {}).get(client, {}).values())
                if not expected:
                    expected = [setup._handler(client, event, scripts, repo) for event in setup.EVENTS[client]]
                for event, groups in config.get('hooks', {}).items():
                    kept = []
                    for group in groups:
                        handlers = [h for h in group['hooks'] if h not in expected]
                        if handlers or not group['hooks']:
                            kept.append({**group, 'hooks': handlers})
                    config['hooks'][event] = kept
                changes[config_path] = setup._json(config)
            instruction = _safe(repo / ('CLAUDE.md' if client == 'claude' else 'AGENTS.md'))
            if instruction.exists():
                changes[instruction] = _remove_block(setup._read(instruction))
            shim = _safe(repo / ('.claude/skills/remvu/SKILL.md' if client == 'claude' else '.agents/skills/remvu/SKILL.md'))
            expected_hash = manifest.get('skill_shims', {}).get(client)
            unchanged = (hashlib.sha256(setup._read(shim).encode('utf-8')).hexdigest() == expected_hash
                         if expected_hash else setup._read(shim) == setup._skill_shim(scripts, manifest.get('python')))
            if shim.exists() and unchanged:
                removals.append(shim)
            elif shim.exists():
                raise ValueError('Project skill was edited since installation; preserve/reconcile it before uninstalling')
        with _transaction(repo):
            for path, content in changes.items():
                setup._atomic(path, content)
            for path in removals:
                path.unlink()
            manifest['platforms'] = []
            manifest['uninstalled_at'] = core._now()
            _write(manifest_path, manifest)
    return {'ok': True, 'changed': [str(p.relative_to(repo)) for p in [*changes, *removals]],
            'memory_retained': True, 'runtime_retained': True,
            'next_steps': ['Restart clients. Private memory, backups, ignore rules and shared runtimes are retained.',
                           'Edited or unrecognized hook definitions are retained; review them in the client.']}


def doctor(repo):
    repo = _safe(repo).resolve()
    report = core.check_project(repo)
    adapters = repo / '.remvu/adapters.json'
    result = {'ok': report['ok'], 'preflight': preflight(), 'memory': report,
              'adapters': [], 'activation': 'not_installed',
              'next_steps': ['Use the Remvu skill to review pending events; repair never invents semantic notes.']}
    if adapters.is_file():
        try:
            manifest = _read(adapters)
            if manifest.get('format') != 'remvu-adapters/1' or not isinstance(manifest.get('platforms'), list):
                raise ValueError('Invalid manifest')
        except (ValueError, OSError, AttributeError):
            result['ok'] = False
            result['memory']['issues'].append({'code': 'damaged_adapter_manifest', 'message': 'Reinstall from reviewed source; private memory is retained.'})
            manifest = {'scripts_dir': '', 'platforms': []}
        scripts = Path(manifest['scripts_dir'])
        for client in manifest['platforms']:
            config_path = repo / ('.claude/settings.local.json' if client == 'claude' else '.codex/hooks.json')
            try:
                config = setup._read_config(config_path)
                installed = all(any(manifest.get('handlers', {}).get(client, {}).get(event, setup._handler(client, event, scripts, repo)) == h
                                    for group in config.get('hooks', {}).get(event, []) for h in group['hooks'])
                                for event in setup.EVENTS[client])
            except (ValueError, OSError):
                installed = False
            observed = []
            receipt = repo / '.remvu/hooks' / ('activation-' + client + '.json')
            if receipt.is_file():
                try:
                    body = _read(receipt)
                    if body.get('scripts') == str(scripts) and body.get('python') == manifest.get('python'):
                        observed = sorted(set(e for e in body.get('events', []) if e in setup.EVENTS[client]))
                except (ValueError, OSError, TypeError, AttributeError):
                    result['ok'] = False
                    result['memory']['issues'].append({'code': 'damaged_activation_receipt', 'message': 'Run repair, then verify hook execution again.'})
            result['adapters'].append({'client': client, 'configured': installed,
                                       'runtime_available': (scripts / 'remvu.py').is_file(),
                                       'observed_events': observed,
                                       'activation': 'hook_execution_observed' if installed and observed else 'awaiting_host_review',
                                       'scope': 'Local receipt is not a trust attestation or desktop/IDE certification.'})
            if not installed or not (scripts / 'remvu.py').is_file():
                result['ok'] = False
        result['activation'] = 'see_per_client_status'
        if (scripts.parent / '.runtime.json').exists():
            try:
                result['runtime'] = _verify_runtime(scripts.parent)['version']
            except (ValueError, OSError):
                result['ok'] = False
                result['runtime'] = 'checksum_mismatch'
    root = repo / '.remvu'
    result['storage'] = {'bytes': sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink()) if root.exists() else 0,
                         'event_count': 0, 'measurement': 'actual local bytes; not tokens or estimated savings'}
    if (root / 'state.json').is_file():
        try:
            state = core.load_state(repo)
            result['storage']['event_count'] = len(state['events'])
            result['storage']['state_bytes'] = (root / 'state.json').stat().st_size
        except (ValueError, OSError):
            pass
    return result


def _valid_snapshot(root, path):
    state = _read(_safe(path))
    if (state.get('format') != core.STATE_FORMAT or type(state.get('revision')) is not int
            or not isinstance(state.get('entries'), list) or not isinstance(state.get('events'), list)
            or state.get('integrity') != core._sha(core._json({k: v for k, v in state.items() if k != 'integrity'}))):
        raise ValueError('Snapshot is invalid')
    journal = _read(core._safe_child(root, 'journal/' + state['last_journal_id'] + '.json'))
    if journal.get('state_integrity') != state['integrity']:
        raise ValueError('Snapshot has no matching committed journal')
    for event in state['events']:
        if not re.fullmatch(r'blobs/[0-9a-f]{64}\.json', event['blob_ref']):
            raise ValueError('Snapshot has invalid evidence reference')
        if core._sha(core._safe_child(root, event['blob_ref']).read_bytes()) != event['sha256']:
            raise ValueError('Snapshot references damaged evidence')
    return state


def _recovery_revision(root, state):
    """Reserve historical/orphan revisions; an older snapshot must not reuse one.

    A stale writer may still hold any previously issued revision. Journal payloads
    are never replayed here. Unreadable revision metadata requires a private
    backup rather than guessing a CAS version and accepting an old proposal.
    """
    ceiling = state['revision']
    for path in core._safe_child(root, 'journal').glob('*.json'):
        try:
            record = _read(_safe(path))
            if (not isinstance(record, dict) or record.get('format') != 'remvu-journal/1'
                    or type(record.get('revision')) is not int or record['revision'] < 0
                    or not isinstance(record.get('state_integrity'), str)
                    or not re.fullmatch(r'[0-9a-f]{64}', record['state_integrity'])):
                raise ValueError('Invalid journal revision metadata')
        except (ValueError, OSError):
            raise ValueError('Journal metadata is damaged; cannot safely choose a recovery revision. Restore a verified private backup.') from None
        ceiling = max(ceiling, record['revision'])
    return ceiling + 1


def repair(repo):
    repo = _safe(repo).resolve()
    if not (repo / '.remvu').is_dir():
        raise ValueError('Run install or init first; no memory exists to repair')
    from remvu_hooks import _ledger_lock, _load_ledger
    repaired, backup = [], None
    # Lock order matches run_hook: ledger, then core. Never delete advisory locks.
    with _ledger_lock(_safe(repo / '.remvu/hooks')):
        with core._lock(repo) as root:
            try:
                core._load_unlocked(root)
                damaged = False
            except (ValueError, OSError):
                damaged = True
            ledger = core._safe_child(root, 'hooks/state.json')
            try:
                _load_ledger(ledger)
                ledger_damaged = False
            except (ValueError, OSError):
                ledger_damaged = True
            if damaged or ledger_damaged:
                backup = core._safe_child(root, 'backups/repair-' + uuid.uuid4().hex)
                backup.mkdir(parents=True)
            if damaged:
                candidates = list(core._safe_child(root, 'snapshots').glob('*.json'))
                valid = []
                for path in candidates:
                    try:
                        state = _valid_snapshot(root, path)
                        valid.append((state['updated_at'], state['revision'], state['integrity'], state))
                    except (ValueError, OSError, KeyError, TypeError):
                        continue
                if not valid:
                    raise ValueError('No verified snapshot with intact evidence is available. Files retained; restore a private backup.')
                state = max(valid, key=lambda v: v[:3])[3]
                state_path = core._safe_child(root, 'state.json')
                if state_path.exists():
                    shutil.copyfile(state_path, backup / 'state.json')
                latest = core._safe_child(root, 'snapshots/latest.json')
                if latest.exists():
                    shutil.copyfile(latest, backup / 'latest.json')
                state['revision'] = _recovery_revision(root, state)
                state['pending_consolidation'] = True
                state['issues'].append({'code': 'recovered_snapshot', 'message': 'Recovered a verified snapshot; inspect retained journals for work not represented here.'})
                core._save(root, state, 'repair_snapshot', {'backup': str(backup.relative_to(root))})
                repaired.append('state_restored_from_verified_snapshot')
            if ledger_damaged:
                shutil.copyfile(ledger, backup / 'hooks-state.json')
                _write(ledger, {'format': 'remvu-hooks/1', 'sessions': {}})
                state = core._load_unlocked(root)
                state['revision'] += 1
                state['pending_consolidation'] = True
                state['issues'].append({'code': 'recovered_hook_ledger', 'message': 'Hook ledger reset from damaged data; review potential missing observations.'})
                core._save(root, state, 'repair_hook_ledger', {})
                repaired.append('hook_ledger_reset')
            for client in setup.EVENTS:
                receipt = core._safe_child(root, 'hooks/activation-' + client + '.json')
                if not receipt.exists():
                    continue
                try:
                    body = _read(receipt)
                    valid = (isinstance(body, dict) and isinstance(body.get('events'), list)
                             and all(isinstance(e, str) and e in setup.EVENTS[client] for e in body['events']))
                except (ValueError, OSError):
                    valid = False
                if not valid:
                    if backup is None:
                        backup = core._safe_child(root, 'backups/repair-' + uuid.uuid4().hex)
                        backup.mkdir(parents=True)
                    shutil.copyfile(receipt, backup / receipt.name)
                    _write(receipt, {'format': 'remvu-activation/1', 'events': [], 'scripts': '', 'python': ''})
                    repaired.append('activation_receipt_reset')
    for gap in list(core._safe_child(repo / '.remvu', 'gaps').glob('*.json'))[:100]:
        if not re.fullmatch(r'[0-9a-f]{32}\.json', gap.name):
            continue
        body = _read(_safe(gap))
        core.record_event(repo, {'kind': 'tool_result', 'source_id': 'gap:' + gap.stem,
                                'output': 'Observation gap: a hook failed. Missing work is unknown, not successful.',
                                'platform': body.get('platform'), 'trigger': body.get('event'),
                                'timestamp': body.get('created_at')})
        archive = core._safe_child(repo / '.remvu', 'gaps/reviewable/' + gap.name)
        archive.parent.mkdir(parents=True, exist_ok=True)
        os.replace(gap, archive)
        repaired.append('observation_gap_indexed_for_semantic_review')
    return {'ok': True, 'repaired': repaired, 'backup': str(backup.relative_to(repo)) if backup else None,
            'remaining_issue_codes': [i['code'] for i in core.check_project(repo)['issues']],
            'next_steps': ['Read status and retained evidence with the Remvu skill; review gaps, update semantic memory and regenerate the handoff.',
                           'Busy OS locks are never removed. Close the active writer and retry.'],
            'semantic_refresh_claimed': False}


def diagnose(repo, out):
    repo = _safe(repo).resolve()
    # Deliberately construct a small allowlisted report. No project paths, entry
    # text, outputs, credentials, remote URLs, config bodies or session IDs.
    health = doctor(repo)
    report = {'format': 'remvu-diagnostic/1', 'created_at': core._now(),
              'preflight': health['preflight'], 'ok': health['ok'],
              'issue_codes': [i['code'] for i in health['memory']['issues']],
              'storage': health['storage'],
              'adapters': [{k: a[k] for k in ('client', 'configured', 'runtime_available', 'observed_events', 'activation')} for a in health['adapters']],
              'privacy': 'Allowlisted metadata only. Preview this local file before choosing to submit it. Nothing was uploaded.'}
    destination = _safe(out)
    if destination.exists():
        raise ValueError('Diagnostic destination exists; choose a new filename')
    if repo == destination or repo in destination.parents and repo / '.remvu' not in destination.parents:
        raise ValueError('Write diagnostics outside the project or under private .remvu/')
    _write(destination, report)
    return {'ok': True, 'path': str(destination), 'uploaded': False, 'next_steps': ['Preview the JSON, then attach it to an issue only if you choose.']}
