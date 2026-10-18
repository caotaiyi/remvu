#!/usr/bin/env python3
"""Build audited plugin and standalone skill ZIPs from a committed revision.

Uses Git and the Python standard library. The output directory must be outside
the checkout. Untracked files, private memory and local caches cannot enter it.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    # Git's ZIP DOS timestamps otherwise use the builder's local timezone.
    return subprocess.check_output(['git', '-C', str(ROOT), *args], env={**os.environ, 'TZ': 'UTC'})


def audit(path, skill=False, kit=False):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        for name in names:
            parts = PurePosixPath(name).parts
            if name.startswith('/') or '..' in parts or any(part in {'.git', '.remvu', '__pycache__', '.env'} for part in parts):
                raise ValueError('unsafe archive path: ' + name)
            if name.endswith(('.pyc', '.jsonl')):
                raise ValueError('unexpected cache/session file: ' + name)
        if kit:
            for expected in ('skills/remvu/scripts/remvu.py', 'scripts/native_acceptance.py', 'scripts/package_smoke.py',
                             'scripts/install.py', 'scripts/check_beta_readiness.py', 'docs/native-acceptance.md', 'LICENSE', 'START-HERE.txt'):
                if expected not in names:
                    raise ValueError('missing acceptance-kit component: ' + expected)
        elif skill:
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
    kit = out / ('remvu-acceptance-v' + version + '.zip')
    sums = out / 'SHA256SUMS'
    if any(path.exists() for path in (plugin, skill, kit, sums)):
        parser.error('use a fresh output directory')
    git('archive', '--format=zip', '--output=' + str(plugin), commit, 'plugin.json', 'LICENSE', 'skills')
    with zipfile.ZipFile(plugin) as source, zipfile.ZipFile(skill, 'w', compression=zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            if info.filename.startswith('skills/remvu/') and not info.is_dir():
                new = zipfile.ZipInfo(info.filename[len('skills/'):], date_time=info.date_time)
                new.create_system = 3
                new.external_attr = info.external_attr
                new.compress_type = zipfile.ZIP_DEFLATED
                target.writestr(new, source.read(info))
        license_info = source.getinfo('LICENSE')
        new = zipfile.ZipInfo('remvu/LICENSE', date_time=license_info.date_time)
        new.create_system = 3
        new.external_attr = license_info.external_attr
        new.compress_type = zipfile.ZIP_DEFLATED
        target.writestr(new, source.read('LICENSE'))
    git('archive', '--format=zip', '--output=' + str(kit), commit,
        'LICENSE', 'skills/remvu', 'scripts/install.py', 'scripts/native_acceptance.py',
        'scripts/package_smoke.py', 'scripts/windows-preflight.ps1', 'scripts/check_beta_readiness.py',
        'docs/native-acceptance.md', 'docs/quickstart.md', 'docs/quickstart.zh-CN.md',
        'docs/faq.md', 'evals/beta-matrix.json')
    with zipfile.ZipFile(kit, 'a', compression=zipfile.ZIP_DEFLATED) as target:
        def add_kit(name, body):
            info = zipfile.ZipInfo(name, date_time=target.getinfo('LICENSE').date_time)
            info.create_system = 3
            info.external_attr = target.getinfo('LICENSE').external_attr
            info.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(info, body)
        add_kit('packages/' + skill.name, skill.read_bytes())
        add_kit('packages/SHA256SUMS', hashlib.sha256(skill.read_bytes()).hexdigest() + '  ' + skill.name + '\n')
        add_kit('START-HERE.txt',
            'Remvu ' + version + ' candidate acceptance kit / 候选验收包\n\n'
            'Requires Python 3.10+ and Git. Windows 11 x64 is a native test target, not a verified claim.\n'
            '需要 Python 3.10+ 和 Git。在解压后的此目录中打开终端。\n\n'
            '1. Run / 运行: python scripts/package_smoke.py packages\n'
            '   This uses only temporary synthetic projects; it is not a native-client test.\n'
            '   这一步仅检查临时合成项目，不代表真实客户端通过。\n'
            '2. Read / 阅读: docs/native-acceptance.md\n'
            '3. Run each client profile using scripts/native_acceptance.py as documented.\n'
            '   按说明在真实客户端逐项测试。登录与 hook 信任使用客户端正常流程。\n'
            '4. Return the small result reports and actual versions. Do not send private logs or keys.\n'
            '   回传小型结果报告和版本信息即可，不要发送私人日志或密钥。\n\n'
            'Nothing is uploaded automatically. The beta is unpublished until native acceptance is complete.\n'
            '不会自动上传。真实验收完成前不发布该测试版。\n')
    assets = []
    for path, is_skill, is_kit in ((plugin, False, False), (skill, True, False), (kit, False, True)):
        count = audit(path, skill=is_skill, kit=is_kit)
        assets.append({'name': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'bytes': path.stat().st_size, 'archive_entries': count})
    sums.write_text(''.join(item['sha256'] + '  ' + item['name'] + '\n' for item in assets), encoding='utf-8')
    print(json.dumps({'commit': commit, 'version': version, 'assets': assets,
                      'scope': 'Committed plugin/skill components and a synthetic native-acceptance kit; no private records.'}, indent=2))


if __name__ == '__main__':
    main()
