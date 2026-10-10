import shutil
import tempfile
import unittest
from pathlib import Path
from validate_dram_hook import validate


FIXTURE = Path(__file__).resolve().parents[2] / 'artifacts/dram-hook-audit-20261010/live'


class DramHookCaptureTests(unittest.TestCase):
    def test_live_capture(self):
        report = validate(FIXTURE)
        self.assertEqual(report['zero_bytes'], 64)
        self.assertFalse(report['exclusive_ownership_proven'])

    def test_reject_wrong_address_status_and_unpaired_bytes(self):
        for filename, old, new in [
            ('result.txt', 'offset=ff1f4000', 'offset=ff1f4004'),
            ('result.txt', 'status=0000', 'status=0002'),
            ('dram-hook-5a.bin', b'\0', b'\1'),
        ]:
            with self.subTest(filename=filename, old=old):
                with tempfile.TemporaryDirectory() as tmp:
                    dest = Path(tmp) / 'capture'
                    shutil.copytree(FIXTURE, dest)
                    path = dest / filename
                    if isinstance(old, bytes):
                        data = bytearray(path.read_bytes()); data[0] = 1
                        path.write_bytes(data)
                    else:
                        path.write_text(path.read_text().replace(old, new, 1))
                    with self.assertRaises(ValueError): validate(dest)
