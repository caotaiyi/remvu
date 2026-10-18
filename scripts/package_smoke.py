#!/usr/bin/env python3
"""Exercise a fresh skill archive's install/relocation/recovery/uninstall locally.

No model calls, credentials or native-client support claims. Only temporary
synthetic projects are written. Requires Python 3.10+ and Git.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile


def run(script, action, repo, *args, expected=0):
    result = subprocess.run([sys.executable, str(script), action, '--repo', str(repo), *map(str, args)],
                            capture_output=True, encoding='utf-8', env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    if result.returncode != expected:
        raise ValueError('Smoke action failed: ' + action + ': ' + result.stdout[:600])
    return json.loads(result.stdout)


def smoke(archive):
    if sys.version_info < (3, 10):
        raise ValueError('Use Python 3.10+')
    if Path(archive).is_dir():
        candidates = list(Path(archive).glob('remvu-skill-v*.zip'))
        if len(candidates) != 1:
            raise ValueError('Expected exactly one skill ZIP in the package directory')
        archive = candidates[0]
    with tempfile.TemporaryDirectory(prefix='remvu archive smoke ') as directory:
        root = Path(directory).resolve()
        source = root / 'extracted'
        source.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            for item in bundle.infolist():
                path = PurePosixPath(item.filename)
                if (path.is_absolute() or '..' in path.parts or '\\' in item.filename
                        or any(':' in p for p in path.parts) or ((item.external_attr >> 16) & 0o170000) == 0o120000):
                    raise ValueError('Unsafe archive entry')
            bundle.extractall(source)
        script = source / 'remvu/scripts/remvu.py'
        repo = root / 'project'
        repo.mkdir()
        (repo / 'code.py').write_text('VALUE = 1\n')
        installed = run(script, 'install', repo, '--home', root / 'managed')
        script = Path(installed['runtime_scripts']) / 'remvu.py'
        shutil.rmtree(source)
        repeated = run(script, 'install', repo, '--home', root / 'managed')
        if repeated['runtime_scripts'] != str(script.parent):
            raise ValueError('Reinstallation is not stable')
        run(script, 'status', repo)
        run(script, 'handoff', repo)
        run(script, 'doctor', repo)
        state = repo / '.remvu/state.json'
        state.write_text('interrupted synthetic state')
        repaired = run(script, 'repair', repo)
        if repaired['semantic_refresh_claimed']:
            raise ValueError('Recovery incorrectly claimed semantic refresh')
        run(script, 'doctor', repo, expected=1)
        report = root / 'diagnostic.json'
        run(script, 'diagnose', repo, '--out', report)
        retained = state.read_bytes()
        run(script, 'uninstall', repo)
        if retained != state.read_bytes():
            raise ValueError('Uninstall altered private memory')
    return {'ok': True, 'format': 'remvu-package-smoke/1', 'python': sys.version.split()[0],
            'platform': sys.platform, 'archive_sha256': hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
            'checks': ['fresh_install', 'source_relocation', 'repeat_install', 'status', 'handoff',
                       'doctor', 'snapshot_recovery', 'truthful_pending', 'local_diagnostic', 'uninstall_preserves_memory'],
            'native_client_acceptance': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(smoke(args.archive), indent=2))
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        raise SystemExit(1)
