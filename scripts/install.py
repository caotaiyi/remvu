#!/usr/bin/env python3
"""Install the reviewed checkout's Remvu skill into a stable user location."""
import sys
import platform
from pathlib import Path

if sys.version_info < ((3, 10) if platform.system() == 'Windows' else (3, 9)):
    raise SystemExit('Source development: Python 3.10+ on Windows, 3.9+ on macOS/Linux. '
                     'Use the complete standalone app with its bundled runtime. The Markdown fallback also needs no Python.')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/remvu/scripts'))
from remvu import main

if __name__ == '__main__':
    raise SystemExit(main(['install', *sys.argv[1:]]))
