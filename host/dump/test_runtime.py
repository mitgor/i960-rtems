import shutil
import tempfile
import unittest
from pathlib import Path
from validate_runtime import validate

FIXTURE=Path(__file__).resolve().parents[2]/'artifacts/runtime-read-20261010/hardened'


class RuntimeTests(unittest.TestCase):
    def test_live_capture(self):
        self.assertTrue(validate(FIXTURE)['runtime_reads_verified'])

    def test_bad_status_guard_and_pending(self):
        for old,new in [('status=0000','status=0002'),('guard-changed=0','guard-changed=4'),
                        ('experiment-result=0 pending=0','experiment-result=0 pending=1')]:
            with tempfile.TemporaryDirectory() as tmp:
                dest=Path(tmp)/'capture';shutil.copytree(FIXTURE,dest)
                p=dest/'result.txt';p.write_text(p.read_text().replace(old,new,1))
                with self.assertRaises(ValueError): validate(dest)

    def test_corrupt_paired_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'capture';shutil.copytree(FIXTURE,dest)
            for name in ['board-a5.bin','board-5a.bin']:
                p=dest/name;b=bytearray(p.read_bytes());b[0xec]^=1;p.write_bytes(b)
            with self.assertRaises(ValueError): validate(dest)
