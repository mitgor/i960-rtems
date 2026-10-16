import struct
import unittest
from verify_result import verify
class ResultTests(unittest.TestCase):
    def record(self):return b'\xa5'*64+struct.pack('<4I',0x444f4e45,123,496,123^0x96016001)+b'\xa5'*64
    def test_record(self):self.assertTrue(verify(self.record(),123))
    def test_stale(self):
        with self.assertRaises(ValueError):verify(self.record(),124)
    def test_guard(self):
        with self.assertRaises(ValueError):verify(self.record()[:-1]+b'\x00',123)
    def test_incomplete(self):
        b=bytearray(self.record());b[64:68]=bytes(4)
        with self.assertRaises(ValueError):verify(b,123)
