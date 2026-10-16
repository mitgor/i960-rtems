import unittest

from verify_owned_page import verify


class OwnedPageReplayTest(unittest.TestCase):
    def setUp(self):
        from test_verify_live import RetainedReplayTest
        RetainedReplayTest.setUp(self)
        pattern = bytes(((i * 37 + 0x5a) ^ (i >> 4)) & 0xff for i in range(4096))
        for name, blob in (("owned-before", b"\x00" * 4096),
                           ("owned-pattern", pattern),
                           ("owned-readback", pattern),
                           ("owned-restored", b"\x00" * 4096)):
            (self.path / f"{name}.bin").write_bytes(blob)

    def tearDown(self):
        self.temp.cleanup()

    def test_owned_page_capture(self):
        self.assertEqual(verify(self.path)["local_page"], "0xc0711000")
        p = self.path / "owned-readback.bin"
        blob = bytearray(p.read_bytes()); blob[23] ^= 1; p.write_bytes(blob)
        with self.assertRaises(ValueError):
            verify(self.path)


if __name__ == "__main__":
    unittest.main()
