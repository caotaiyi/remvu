"""Actual offline installation without a Python binary in the installer's PATH."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

@unittest.skipIf(os.name == 'nt', 'POSIX installer; PowerShell requires separate native acceptance')
class SkillInstallTest(unittest.TestCase):
    def test_offline_no_python_and_existing_skill_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'project with spaces'
            project.mkdir()
            binaries = root / 'bin'
            binaries.mkdir()
            for cmd in ('git', 'mktemp', 'rm', 'mkdir', 'cp'):
                (binaries / cmd).symlink_to(shutil.which(cmd))
            env = {**os.environ, 'PATH': str(binaries), 'REMVU_SOURCE': str(ROOT)}
            def install():
                return subprocess.run(['/bin/sh', str(ROOT / 'scripts/install-skill.sh'), str(project)],
                                      env=env, capture_output=True, text=True)
            first = install()
            self.assertEqual(first.returncode, 0, first.stderr)
            for client in ('.claude', '.agents'):
                target = project / client / 'skills/remvu'
                self.assertEqual((target / 'SKILL.md').read_bytes(), (ROOT / 'skills/remvu/SKILL.md').read_bytes())
                self.assertTrue((target / 'assets/note-template.md').is_file())
                self.assertEqual(list(target.rglob('*.py')), [])
                self.assertTrue((target / 'LICENSE').is_file())
            self.assertFalse((project / '.remvu').exists())
            self.assertFalse((project / '.claude/settings.local.json').exists())
            self.assertFalse((project / '.codex/hooks.json').exists())
            edited = project / '.agents/skills/remvu/SKILL.md'
            edited.write_text('user edit')
            self.assertNotEqual(install().returncode, 0)
            self.assertEqual(edited.read_text(), 'user edit')

    def test_refuses_symlink_before_writing_other_client(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'project'
            project.mkdir()
            outside = root / 'outside'
            outside.mkdir()
            (project / '.agents').symlink_to(outside, target_is_directory=True)
            result = subprocess.run(['/bin/sh', str(ROOT / 'scripts/install-skill.sh'), str(project)],
                                    env={**os.environ, 'REMVU_SOURCE': str(ROOT)}, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((project / '.claude').exists())
            self.assertEqual(list(outside.iterdir()), [])
