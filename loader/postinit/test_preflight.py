import tempfile
import unittest
from pathlib import Path
import preflight

class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.bdf='0000:37:09.1';self.d=self.root/self.bdf;self.d.mkdir()
        (self.d/'vendor').write_text('0x1069\n');(self.d/'device').write_text('0x0010\n')
        c=bytearray(256);c[4]=6;(self.d/'config').write_bytes(c)
        (self.d/'resource').write_text('00000000ee000000 00000000ee001fff 0000000000042208\n')
    def tearDown(self):self.tmp.cleanup()
    def test_read_only_snapshot(self):
        before={p.name:p.read_bytes() for p in self.d.iterdir()}
        r=preflight.inspect(self.root,self.bdf)
        self.assertEqual(r['bar0']['size'],8192)
        self.assertTrue(r['read_only']);self.assertFalse(r['flash_ready'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.d.iterdir()})
    def test_wrong_card_and_short_configuration(self):
        (self.d/'device').write_text('0x0001')
        with self.assertRaises(ValueError):preflight.inspect(self.root,self.bdf)
        (self.d/'device').write_text('0x0010');(self.d/'config').write_bytes(b'')
        with self.assertRaises(ValueError):preflight.inspect(self.root,self.bdf)
    def test_bound_driver_rejected(self):
        target=self.root/'myrb';target.mkdir();(self.d/'driver').symlink_to(target)
        r=preflight.inspect(self.root,self.bdf)
        self.assertEqual(r['driver'],'myrb');self.assertFalse(r['host_preconditions_pass'])
    def test_wrong_window_and_disabled_memory(self):
        (self.d/'resource').write_text('ee000000 ee000fff 200\n')
        self.assertFalse(preflight.inspect(self.root,self.bdf)['host_preconditions_pass'])
        (self.d/'resource').write_text('ee000000 ee001fff 200\n')
        (self.d/'config').write_bytes(bytes(256))
        self.assertFalse(preflight.inspect(self.root,self.bdf)['host_preconditions_pass'])
    def test_bdf_is_not_a_path(self):
        with self.assertRaises(ValueError):preflight.inspect(self.root,'../config')
if __name__=='__main__':unittest.main()
