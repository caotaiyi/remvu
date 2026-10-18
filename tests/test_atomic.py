"""Windows sharing failures must not turn an atomic update into file deletion."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/remvu/scripts'))
import remvu_core as core
import remvu_hooks as hooks
import remvu_init as setup

class AtomicReplaceTest(unittest.TestCase):
    def test_transient_sharing_denial_retries_same_temp_for_each_writer(self):
        for writer in (core._atomic,hooks._atomic,setup._atomic):
            with self.subTest(writer=writer.__module__), tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp).resolve()/'state.json'
                target.write_text('{"old":true}',encoding='utf-8')
                replace=core.os.replace
                seen=[]
                def busy_then_replace(source,destination):
                    seen.append(str(source))
                    self.assertEqual(json.loads(target.read_text(encoding='utf-8')),{'old':True})
                    if len(seen)<3:
                        error=PermissionError('synthetic Windows sharing denial')
                        error.winerror=32
                        raise error
                    replace(source,destination)
                with patch.object(core.os,'replace',side_effect=busy_then_replace),patch.object(core.time,'sleep'):
                    writer(target,'{"new":true}' if writer is setup._atomic else {'new':True})
                self.assertEqual(len(set(seen)),1)
                self.assertEqual(json.loads(target.read_text(encoding='utf-8')),{'new':True})
                self.assertEqual(list(target.parent.iterdir()),[target])

    def test_persistent_denial_is_bounded_preserves_old_file_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp).resolve()/'state.json'
            target.write_text('original',encoding='utf-8')
            error=PermissionError('synthetic persistent Windows denial')
            error.winerror=5
            with patch.object(core.os,'replace',side_effect=error), \
                 patch.object(core.time,'monotonic',side_effect=[0,0.1,0.6]), \
                 patch.object(core.time,'sleep'):
                with self.assertRaises(PermissionError): core._atomic(target,{'new':True})
            self.assertEqual(target.read_text(encoding='utf-8'),'original')
            self.assertEqual(list(target.parent.iterdir()),[target])
