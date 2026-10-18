"""The comparison judge detects behavior failures and mutation, not agent claims."""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'evals'))
import run_markdown as benchmark

@unittest.skipUnless(shutil.which('node'), 'Node is a developer-only benchmark dependency')
class MarkdownJudgeTest(unittest.TestCase):
    def test_mutation_fails_even_when_return_value_is_correct(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)
            (repo/'app.cjs').write_text('module.exports=x=>{x.push(2);return [1,2]};')
            result=benchmark.verify(repo,{'cases':[[[1],[1,2]]]})
            self.assertEqual(result['passed'],0)
            (repo/'app.cjs').write_text('module.exports=x=>[...x,2];')
            self.assertEqual(benchmark.verify(repo,{'cases':[[[1],[1,2]]]} )['passed'],1)

    def test_broken_module_never_becomes_a_passing_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)
            (repo/'app.cjs').write_text('not JavaScript!')
            self.assertEqual(benchmark.verify(repo,{'cases':[[1,1],[2,2]]})['failed_case_ids'],[0,1])
