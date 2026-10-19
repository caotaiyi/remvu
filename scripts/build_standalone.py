#!/usr/bin/env python3
"""Developer build: bundle CPython with the complete engine (PyInstaller 6.22.3)."""
import argparse
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
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(out, allow_dirty=False):
    import PyInstaller
    if PyInstaller.__version__ != '6.22.3':
        raise ValueError('Build with pinned pyinstaller==6.22.3')
    dirty = bool(subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip())
    if dirty and not allow_dirty:
        raise ValueError('Release builds require a clean committed checkout; --allow-dirty is development-only')
    if out == ROOT or ROOT in out.parents:
        raise ValueError('Build output must be outside the checkout')
    out.mkdir(parents=True, exist_ok=True)
    skill = ROOT / 'skills/remvu'
    version = re.search(r"VERSION = '([^']+)'", (skill / 'scripts/remvu.py').read_text())[1]
    with tempfile.TemporaryDirectory(prefix='remvu bundle build ') as temporary:
        temp = Path(temporary)
        entry = temp / 'entry.py'
        entry.write_text('from remvu import main\nraise SystemExit(main())\n')
        skill_source = temp / 'reviewed-skill'
        for path in skill.rglob('*'):
            if path.is_symlink() or path.name.startswith('.env') or path.suffix == '.jsonl':
                raise ValueError('Unexpected private/session/symlink resource in skill')
        shutil.copytree(skill, skill_source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir',
                   '--name', 'remvu', '--distpath', str(temp / 'dist'), '--workpath', str(temp / 'work'),
                   '--specpath', str(temp), '--paths', str(skill / 'scripts'),
                   '--add-data', str(skill_source) + os.pathsep + 'skill']
        for module in ('remvu_core', 'remvu_init', 'remvu_hooks', 'remvu_lifecycle', 'remvu_runtime', 'legacy_export'):
            command.extend(['--hidden-import', module])
        subprocess.run([*command, str(entry)], check=True, env={**os.environ, 'PYINSTALLER_CONFIG_DIR': str(temp / 'cache')})
        source = temp / 'dist/remvu'
        # Distribute regular files only; resolve PyInstaller's internal links while
        # checking they cannot escape the app. copytree preserves executable modes.
        for path in source.rglob('*'):
            if path.is_symlink() and source.resolve() not in path.resolve().parents:
                raise ValueError('Bundle symlink escapes application')
        target = out / ('remvu-' + version + '-' + platform.system().lower() + '-' + platform.machine().lower())
        if target.exists():
            raise ValueError('Destination exists: ' + str(target))
        shutil.copytree(source, target, symlinks=False, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy2(ROOT / 'LICENSE', target / 'LICENSE')
    shutil.copytree(ROOT / 'docs/licenses', target / 'licenses')
    (target / 'NOTICE.txt').write_text('Remvu bundles CPython and the PyInstaller bootloader. See licenses/ for their licenses and CPython third-party notices. Source: https://github.com/caotaiyi/remvu\n', encoding='utf-8')
    hashes = {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(target.rglob('*')) if p.is_file()}
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    (target / '.bundle.json').write_text(json.dumps({'format': 'remvu-bundle/1', 'version': version,
        'source_revision': revision, 'source_dirty': dirty, 'system': platform.system(),
        'machine': platform.machine(), 'python': platform.python_version(), 'files': hashes}, indent=2) + '\n')
    archive = out / (target.name + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        for p in sorted(target.rglob('*')):
            if p.is_file():
                zipped.write(p, str(Path(target.name) / p.relative_to(target)))
    (out / (archive.name + '.sha256')).write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + archive.name + '\n')
    print(json.dumps({'application': str(target), 'archive': str(archive)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--allow-dirty', action='store_true', help='Development test only; never a release artifact')
    args = parser.parse_args()
    build(args.out.resolve(), allow_dirty=args.allow_dirty)
