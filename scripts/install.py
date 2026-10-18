#!/usr/bin/env python3
"""Install the reviewed checkout's Remvu skill into a stable user location."""
import sys
from pathlib import Path

if sys.version_info < (3, 9):
    raise SystemExit('Remvu installation needs Python 3.9+. Install it from python.org, then retry.')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/remvu/scripts'))
from remvu import main

if __name__ == '__main__':
    raise SystemExit(main(['install', *sys.argv[1:]]))
