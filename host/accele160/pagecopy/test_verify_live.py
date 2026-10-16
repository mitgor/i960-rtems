from pathlib import Path
import struct
import tempfile
import unittest

from verify_live import verify, fnv


class PageCopyReplayTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = p = Path(self.temp.name)
        ptr = 0xc0710000
        pattern = bytes(((i * 53 + 0x96) ^ (i >> 3)) & 0xff for i in range(4096))
        digest = fnv(pattern)
        before = bytearray(b"\xff" * 4096)
        reserved = bytearray(before)
        copied = bytearray(before)
        after = bytearray(before)
        struct.pack_into("<4I", reserved, 0x820, 0x4f4c4c41, 0x16161041, ptr, 0x80000)
        struct.pack_into("<4I", reserved, 0x840, 0x56525352, ptr, 0x80000, 0x96016004)
        copied[:] = reserved
        struct.pack_into("<4I", copied, 0x820, 0x59504f43, 0x16161061, 0, digest)
        struct.pack_into("<4I", copied, 0x860, 0x59504f43, 0x16161061, 0, digest)
        struct.pack_into("<4I", after, 0x820, 0x45455246, 0x16161051, ptr, 0x80000)
        for name, blob in (("page-before", before), ("page-reserved", reserved),
                           ("page-copied", copied), ("page-after", after)):
            (p / f"{name}.bin").write_bytes(blob)
        tb = bytearray(4096); tr = bytearray(tb)
        first = (ptr - 0xc0000000) // 0x8000
        for i in range(first, first + 16):
            struct.pack_into("<I", tr, 0x2a0 + i * 4, 16)
            struct.pack_into("<I", tr, 0x6a0 + i * 4, 0x96016004)
        for name, blob in (("table-before", tb), ("table-reserved", tr),
                           ("table-after", tb)):
            (p / f"{name}.bin").write_bytes(blob)
        for name, blob in (("staging-before", b"\x00" * 4096),
                           ("staging-pattern", pattern),
                           ("staging-readback", pattern),
                           ("staging-restored", b"\x00" * 4096)):
            (p / f"{name}.bin").write_bytes(blob)
        for name in ("reserve", "copy", "release"):
            (p / f"{name}-status.txt").write_text(
                "started=1 done=1 status=0 residual=0 released=0\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_and_tampered(self):
        self.assertEqual(verify(self.path)["target_page"], "0xc0710000")
        for name, offset in (("staging-readback.bin", 23),
                             ("page-copied.bin", 0x82c),
                             ("page-copied.bin", 0x700),
                             ("table-reserved.bin", 0xa28)):
            with self.subTest(name=name, offset=offset):
                path = self.path / name
                original = path.read_bytes()
                altered = bytearray(original); altered[offset] ^= 1
                path.write_bytes(altered)
                with self.assertRaises(ValueError):
                    verify(self.path)
                path.write_bytes(original)

    def test_indexed_odd_target_readback(self):
        index = 1
        pattern = bytes(((i * 53 + 0x96 + index) ^ (i >> 3)) & 0xff
                        for i in range(4096))
        digest = fnv(pattern)
        (self.path / "staging-pattern.bin").write_bytes(pattern)
        (self.path / "staging-readback.bin").write_bytes(pattern)
        p = self.path / "page-copied.bin"
        copied = bytearray(p.read_bytes())
        for offset in (0x820, 0x860):
            struct.pack_into("<4I", copied, offset, 0x59504f43,
                             0x16161061, index, digest)
        p.write_bytes(copied)
        (self.path / "target-before.bin").write_bytes(b"\x00" * 4096)
        (self.path / "target-after.bin").write_bytes(pattern)
        self.assertTrue(verify(self.path)["independent_odd_target_readback"])
        altered = bytearray(pattern); altered[500] ^= 1
        (self.path / "target-after.bin").write_bytes(altered)
        with self.assertRaises(ValueError):
            verify(self.path)


if __name__ == "__main__":
    unittest.main()
