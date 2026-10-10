import tempfile
import unittest
import shutil
from pathlib import Path
from validate_scratch import validate

FIXTURE=Path(__file__).resolve().parents[2]/'artifacts/ram-scratch-20261010'


class ScratchTests(unittest.TestCase):
    def test_live_fixture(self):
        self.assertTrue(validate(FIXTURE)['original_region_restored'])

    def test_surrounding_or_restore_damage(self):
        for name,offset in [('scratch-test',0),('scratch-test',16),('scratch-restored',16)]:
            with tempfile.TemporaryDirectory() as tmp:
                dest=Path(tmp)/'fixture';shutil.copytree(FIXTURE,dest)
                for suffix in ['-a5.bin','-5a.bin']:
                    p=dest/(name+suffix);b=bytearray(p.read_bytes());b[offset]^=1;p.write_bytes(b)
                with self.assertRaises(ValueError):validate(dest)

    def test_dirty_pending_and_wrong_upload(self):
        for old,new in [('scratch-dirty=0','scratch-dirty=1'),('pending=0','pending=1'),
                        ('submit op=21 id=16 len=16 offset=00080010','submit op=21 id=16 len=16 offset=00000000')]:
            with tempfile.TemporaryDirectory() as tmp:
                dest=Path(tmp)/'fixture';shutil.copytree(FIXTURE,dest)
                p=dest/'result.txt';p.write_text(p.read_text().replace(old,new,1))
                with self.assertRaises(ValueError):validate(dest)
