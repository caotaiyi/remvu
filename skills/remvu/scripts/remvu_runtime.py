"""Shared source/bundled launch paths. A bundled executable is never Python."""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys


def frozen():
    return bool(getattr(sys, 'frozen', False))


def skill_dir():
    return Path(sys._MEIPASS) / 'skill' if frozen() else Path(__file__).resolve().parent.parent


def scripts_dir():
    return skill_dir() / 'scripts'


def bundle_for_scripts(scripts):
    scripts = Path(scripts).resolve()
    app = scripts.parent.parent.parent
    if scripts == app / '_internal/skill/scripts' and (app / '.bundle.json').is_file():
        return app
    return None


def executable_name():
    return 'remvu.exe' if os.name == 'nt' else 'remvu'


def cli_command(scripts=None, python=None):
    scripts = Path(scripts) if scripts is not None else scripts_dir()
    app = bundle_for_scripts(scripts)
    if app:
        return [str(app / executable_name())]
    if frozen() and scripts.resolve() == scripts_dir().resolve():
        return [str(Path(sys.executable).resolve())]
    return [str(Path(python or sys.executable).resolve()), str(scripts / 'remvu.py')]


def hook_command(scripts):
    cli = cli_command(scripts)
    return [*cli, 'hook'] if len(cli) == 1 else [cli[0], str(Path(scripts) / 'remvu_hooks.py')]


def child_env():
    return {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYINSTALLER_RESET_ENVIRONMENT': '1'}


@contextmanager
def external_loader():
    """Do not make external Git load the bundled interpreter's libraries."""
    if frozen() and os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetDllDirectoryW(None)
        try:
            yield
        finally:
            ctypes.windll.kernel32.SetDllDirectoryW(str(sys._MEIPASS))
    else:
        yield


def run_external(argv, **kwargs):
    env = dict(kwargs.pop('env', os.environ))
    if frozen():
        for key in ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'):
            old = env.get(key + '_ORIG')
            if old is None:
                env.pop(key, None)
            else:
                env[key] = old
    with external_loader():
        return subprocess.run(argv, env=env, **kwargs)
