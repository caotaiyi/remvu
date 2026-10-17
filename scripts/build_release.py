#!/usr/bin/env python3
"""Build audited plugin and standalone skill ZIPs from a committed revision.

Uses Git and the Python standard library. The output directory must be outside
the checkout. Untracked files, private memory and local caches cannot enter it.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def audit(path, skill=False):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        for name in names:
            parts = PurePosixPath(name).parts
            if name.startswith('/') or '..' in parts or any(part in {'.git', '.remvu', '__pycache__', '.env'} for part in parts):
                raise ValueError('unsafe archive path: ' + name)
            if name.endswith(('.pyc', '.jsonl')):
                raise ValueError('unexpected cache/session file: ' + name)
        if skill:
            for expected in ('remvu/SKILL.md', 'remvu/LICENSE', 'remvu/scripts/remvu.py', 'remvu/scripts/legacy_export.py'):
                if expected not in names:
                    raise ValueError('missing skill component: ' + expected)
        else:
            manifest = json.loads(archive.read('plugin.json'))
            if manifest['name'] != 'remvu' or manifest['$schema'] != 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json':
                raise ValueError('unexpected plugin manifest')
            for expected in ('skills/remvu/SKILL.md', 'skills/agent-task-export/SKILL.md', 'LICENSE'):
                if expected not in names:
                    raise ValueError('missing plugin component: ' + expected)
        return len(names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--ref', default='HEAD')
    args = parser.parse_args()
    out = args.out.expanduser().resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('--out must be outside the checkout')
    if args.ref.startswith('-'):
        parser.error('invalid revision')
    commit = git('rev-parse', '--verify', args.ref + '^{commit}').decode().strip()
    manifest = json.loads(git('show', commit + ':plugin.json'))
    version = manifest['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        parser.error('package version must be SemVer')
    out.mkdir(parents=True, exist_ok=True)
    plugin = out / ('remvu-plugin-v' + version + '.zip')
    skill = out / ('remvu-skill-v' + version + '.zip')
    sums = out / 'SHA256SUMS'
    if any(path.exists() for path in (plugin, skill, sums)):
        parser.error('use a fresh output directory')
    git('archive', '--format=zip', '--output=' + str(plugin), commit, 'plugin.json', 'LICENSE', 'skills')
    with zipfile.ZipFile(plugin) as source, zipfile.ZipFile(skill, 'w', compression=zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            if info.filename.startswith('skills/remvu/') and not info.is_dir():
                new = zipfile.ZipInfo(info.filename[len('skills/'):], date_time=info.date_time)
                new.external_attr = info.external_attr
                new.compress_type = zipfile.ZIP_DEFLATED
                target.writestr(new, source.read(info))
        license_info = source.getinfo('LICENSE')
        new = zipfile.ZipInfo('remvu/LICENSE', date_time=license_info.date_time)
        new.external_attr = license_info.external_attr
        new.compress_type = zipfile.ZIP_DEFLATED
        target.writestr(new, source.read('LICENSE'))
    assets = []
    for path, is_skill in ((plugin, False), (skill, True)):
        count = audit(path, skill=is_skill)
        assets.append({'name': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'bytes': path.stat().st_size, 'archive_entries': count})
    sums.write_text(''.join(item['sha256'] + '  ' + item['name'] + '\n' for item in assets), encoding='utf-8')
    print(json.dumps({'commit': commit, 'version': version, 'assets': assets,
                      'scope': 'Committed plugin components only; source, tests and reports remain in the repository.'}, indent=2))


if __name__ == '__main__':
    main()
