#!/usr/bin/env python3
"""Install the reviewed checkout's Remvu skill into a stable user location."""
import sys
import platform
from pathlib import Path

if sys.version_info < ((3, 10) if platform.system() == 'Windows' else (3, 9)):
    raise SystemExit('Optional engine: Python 3.10+ on Windows, 3.9+ on macOS/Linux. '
                     'The default Markdown skill needs no Python; use install-skill instead.')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/remvu/scripts'))
from remvu import main

if __name__ == '__main__':
    raise SystemExit(main(['install', *sys.argv[1:]]))
