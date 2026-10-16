"""Replay accepted hardware evidence and ensure corrupted evidence is rejected."""
import gzip
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_full_dump import verify

ROOT = Path(__file__).resolve().parents[3]
CAPTURE = ROOT / 'artifacts/current/accele160-guarded-20261016'
BASELINE = ROOT / 'artifacts/current/accele160-readimage-20261016/fresh'

class FullDumpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.capture = Path(self.tmp.name) / 'capture'
        for relative in ('rawflash-0/data.bin', 'rawflash-1/data.bin',
                         'rawflash-0/status.txt', 'rawflash-1/status.txt',
                         'guarded-diagnostics-0/data.bin',
                         'retained-ezassist/allocation-0.bin.gz'):
            target = self.capture / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(CAPTURE / relative, target)

    def test_accepted_pair(self):
        result = verify(self.capture, BASELINE)
        self.assertEqual(result['sha256'], '0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a')
        self.assertEqual(result['overrun']['bytes_beyond_request'], 386502)

    def test_pair_tamper(self):
        p = self.capture / 'rawflash-1/data.bin'
        data = bytearray(p.read_bytes()); data[0] ^= 1; p.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'pair mismatch'):
            verify(self.capture, BASELINE)

    def test_guard_status_tamper(self):
        p = self.capture / 'rawflash-0/status.txt'
        p.write_text(p.read_text().replace('guard_changes=0', 'guard_changes=01'))
        with self.assertRaisesRegex(ValueError, 'unaccepted'):
            verify(self.capture, BASELINE)

    def test_owned_buffer_tail_tamper(self):
        p = self.capture / 'retained-ezassist/allocation-0.bin.gz'
        data = bytearray(gzip.decompress(p.read_bytes())); data[-1] ^= 1
        p.write_bytes(gzip.compress(data))
        with self.assertRaisesRegex(ValueError, 'outside expanded image'):
            verify(self.capture, BASELINE)

if __name__ == '__main__':
    unittest.main()
