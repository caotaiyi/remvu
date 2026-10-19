#!/usr/bin/env python3
"""Exercise the actual bundled engine with Git but no Python on its PATH."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def smoke(app):
    with tempfile.TemporaryDirectory(prefix='remvu standalone spaces ') as tmp:
        root = Path(tmp).resolve()
        repo, home, binaries = root / 'project', root / 'managed', root / 'git-only'
        repo.mkdir(); binaries.mkdir()
        git = Path(shutil.which('git')).resolve()
        if os.name == 'nt':
            # Git for Windows locates its own DLLs relative to the real binary.
            pass
        else:
            (binaries / 'git').symlink_to(git)
        env = {**os.environ, 'PATH': str(git.parent) if os.name == 'nt' else str(binaries), 'PYINSTALLER_RESET_ENVIRONMENT': '1'}
        assert shutil.which('python', path=env['PATH']) is None
        assert shutil.which('python3', path=env['PATH']) is None
        def run(binary, *args, payload=None, expected=0):
            process = subprocess.run([str(binary), *args, '--repo', str(repo)], input=json.dumps(payload) if payload is not None else '',
                env=env, capture_output=True, encoding='utf-8', timeout=60)
            assert process.returncode == expected, (args, process.returncode, process.stdout, process.stderr)
            return json.loads(process.stdout)
        downloaded = root / 'downloaded app'
        shutil.copytree(app, downloaded)
        executable = downloaded / ('remvu.exe' if os.name == 'nt' else 'remvu')
        def gitrun(*args):
            subprocess.run([str(git), '-C', str(repo), *args], check=True, capture_output=True)
        gitrun('init', '-q'); gitrun('config', 'user.name', 'Remvu fixture'); gitrun('config', 'user.email', 'fixture@example.invalid')
        (repo / 'app.txt').write_text('baseline\n')
        gitrun('add', '.'); gitrun('commit', '-qm', 'baseline')
        installed = run(executable, 'install', '--home', str(home), '--platform', 'both')
        assert installed['preflight']['user_python_required'] is False
        stable = Path(installed['runtime_launcher'][0])
        assert stable != executable and stable.is_file()
        assert run(executable, 'install', '--home', str(home))['runtime_launcher'] == installed['runtime_launcher']
        downloaded.rename(root / 'moved download')
        overlay = run(stable, 'dsh-config')
        assert json.loads(Path(overlay['path']).read_text())[0]['config']['executable'] == str(stable)
        replacement = root / 'reviewed replacement'
        shutil.copytree(app, replacement)
        notice = replacement / 'NOTICE.txt'
        notice.write_text(notice.read_text() + 'Synthetic upgrade fixture.\n')
        import hashlib
        manifest_path = replacement / '.bundle.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['files']['NOTICE.txt'] = hashlib.sha256(notice.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        upgraded = run(stable, 'upgrade', '--source', str(replacement))
        assert upgraded['runtime_launcher'][0] != str(stable)
        changed_launcher = Path(upgraded['runtime_launcher'][0])
        assert run(changed_launcher, 'upgrade', '--rollback')['runtime_launcher'][0] == str(stable)
        hook_config = json.loads((repo / '.claude/settings.local.json').read_text())
        hook = hook_config['hooks']['SessionStart'][0]['hooks'][0]
        # Execute exactly the generated handler, proving it names the stable app.
        if 'args' in hook:
            callback = [hook['command'], *hook['args']]
        else:
            import shlex
            callback = shlex.split(hook['command'])
        assert callback[0] == str(stable) and callback[1] == 'hook', callback
        process = subprocess.run(callback, input=json.dumps({'session_id': 'bundle-fixture', 'cwd': str(repo)}),
            env=env, capture_output=True, encoding='utf-8', timeout=15)
        assert process.returncode == 0 and 'additionalContext' in process.stdout, process.stdout
        def record(index):
            return run(stable, 'record', payload={'kind': 'tool_result', 'tool': 'fixture', 'output': 'failed fixture ' + str(index), 'result': 'failed'})
        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(record, range(12)))
        assert run(stable, 'status')['event_count'] == 12
        assert run(stable, 'save')['pending_consolidation']
        state = run(stable, 'status')
        proposal = {'base_revision': state['revision'], 'base_event_count': state['event_count'], 'entries': [
            {'kind': 'constraint', 'text': 'Keep the complete engine.', 'basis': 'user_confirmed', 'sources': [{'type': 'user', 'excerpt': 'Keep the complete engine.', 'visibility': 'private'}]},
            {'kind': 'check', 'text': 'Fixture check failed.', 'basis': 'observed', 'result': 'failed', 'exit_code': 1,
             'sources': [{'type': 'tool', 'excerpt': 'fixture failed, exit 1', 'visibility': 'private'}]}]}
        saved = run(stable, 'save', '--proposal', '-', payload=proposal)
        assert not saved['pending_consolidation']
        stale = run(stable, 'update', '--proposal', '-', payload=proposal, expected=1)
        assert stale['ok'] is False
        resume = run(stable, 'resume')
        assert resume['memory']['entry_count'] == 2
        (repo / 'app.txt').write_text('changed\n')
        issues = run(stable, 'check', expected=1)['issues']
        assert any('stale' in issue['code'] for issue in issues), issues
        assert run(stable, 'share', expected=1)['ok'] is False
        # Restore old code, then recover a corrupt state with evidence retained.
        (repo / '.remvu/state.json').write_text('{broken')
        recovered = run(stable, 'repair')
        assert recovered['semantic_refresh_claimed'] is False
        assert run(stable, 'status')['pending_consolidation']
        before = (repo / '.remvu/state.json').read_bytes()
        assert run(stable, 'uninstall')['memory_retained']
        assert (repo / '.remvu/state.json').read_bytes() == before
        assert run(stable, 'uninstall')['ok']
        fixture_root = Path(__file__).resolve().parents[1]
        legacy_bundle = root / 'legacy evidence'
        for args in (['export', '--source', str(fixture_root / 'examples/session.jsonl'),
                       '--task', str(fixture_root / 'examples/task.json'), '--out', str(legacy_bundle)],
                     ['verify', str(legacy_bundle)]):
            process = subprocess.run([str(stable), 'legacy', *args], env=env, capture_output=True, encoding='utf-8', timeout=60)
            assert process.returncode == 0, (args, process.stdout, process.stderr)
        assert run(stable, 'import-legacy', str(legacy_bundle))['ok']
        imported = run(stable, 'status')
        assert any(e['basis'] == 'unverified' for e in imported['entries'])
        return {'ok': True, 'platform': os.name, 'python_on_path': False,
                'checks': ['stable_install', 'repeat_install', 'download_relocation', 'bundled_upgrade_and_rollback', 'dsh_overlay', 'exact_hook_callback', '12_events_6_writers',
                           'private_save', 'reviewed_update', 'CAS_conflict_retained', 'resume', 'stale_code',
                           'public_share_refusal', 'verified_repair', 'uninstall_retains_memory', 'bundled_legacy_export_verify_import'],
                'scope': 'Packaged program checks in synthetic repositories, not native agent or Windows 11 acceptance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('application', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = smoke(args.application.resolve())
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
