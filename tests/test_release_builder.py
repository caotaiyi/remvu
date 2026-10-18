"""The same committed candidate must not change when packaging at another time."""
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release_builder', ROOT / 'scripts/build_release.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ReleaseBuilderTest(unittest.TestCase):
    def test_committed_packages_are_independent_of_build_wall_clock(self):
        with tempfile.TemporaryDirectory() as directory:
            reports = []
            for index, year in enumerate((2024, 2025)):
                out = Path(directory) / str(index)
                with patch.dict(os.environ, {'TZ': 'Pacific/Honolulu' if index else 'Asia/Singapore'}), \
                     patch.object(sys, 'argv', ['build_release', '--out', str(out)]), redirect_stdout(io.StringIO()), \
                     patch.object(builder.zipfile.time, 'localtime', return_value=(year, 1, 2, 3, 4, 6, 1, 2, 0)):
                    builder.main()
                reports.append({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()})
            self.assertEqual(reports[0], reports[1])
            self.assertTrue(any(name.startswith('remvu-acceptance-') for name in reports[0]))


if __name__ == '__main__':
    unittest.main()
