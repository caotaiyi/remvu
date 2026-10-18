#!/usr/bin/env python3
"""Repeat the synthetic six-writer transport check; no native-client claim."""
import argparse
import io
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_hooks import AdapterTest

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iterations', type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 100:
        parser.error('--iterations must be 1..100')
    trials = []
    for index in range(args.iterations):
        output = io.StringIO()
        suite = unittest.TestSuite([AdapterTest('test_parallel_hook_processes_keep_all_distinct_events')])
        started = time.monotonic()
        result = unittest.TextTestRunner(stream=output).run(suite)
        trials.append({'trial': index + 1, 'passed': result.wasSuccessful(),
                       'elapsed_seconds': round(time.monotonic() - started, 3)})
        if not result.wasSuccessful():
            sys.stderr.write(output.getvalue())
            break
    ok = len(trials) == args.iterations and all(t['passed'] for t in trials)
    print(json.dumps({'format': 'remvu-hook-stress/1', 'ok': ok, 'trials': trials,
                      'assertion': 'Each trial requires six distinct synthetic events and zero hook warnings.',
                      'native_client_acceptance': False}, indent=2))
    raise SystemExit(0 if ok else 1)
