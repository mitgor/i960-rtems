import json
from pathlib import Path
import struct
import tempfile
import unittest

from verify_live import verify, OWNER, SIZE


class RetainedReplayTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        p = self.path = Path(self.temp.name)
        before = bytearray(b"\xff" * 4096)
        reserve = bytearray(before)
        release = bytearray(before)
        ptr = 0xc0710000
        struct.pack_into("<4I", reserve, 0x820, 0x4f4c4c41, 0x16161041, ptr, SIZE)
        struct.pack_into("<4I", reserve, 0x840, 0x56525352, ptr, SIZE, OWNER)
        struct.pack_into("<4I", release, 0x820, 0x45455246, 0x16161051, ptr, SIZE)
        for name, blob in (("page-before", before), ("page-reserved", reserve),
                           ("page-after", release)):
            (p / f"{name}.bin").write_bytes(blob)
        tb = bytearray(4096); tr = bytearray(tb)
        first = (ptr - 0xc0000000) // 0x8000
        for i in range(first, first + 16):
            struct.pack_into("<I", tr, 0x2a0 + i * 4, 16)
            struct.pack_into("<I", tr, 0x6a0 + i * 4, OWNER)
        for name, blob in (("table-before", tb), ("table-reserved", tr),
                           ("table-after", tb)):
            (p / f"{name}.bin").write_bytes(blob)
        for name in ("reserve", "release"):
            (p / f"{name}-status.txt").write_text(
                "started=1 done=1 status=0 residual=0 released=0\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_and_tampered(self):
        self.assertTrue(verify(self.path)["reserve_and_release_passed"])
        for name, offset in (("page-reserved", 0x700),
                             ("page-reserved", 0x840),
                             ("table-reserved", 0x2a0),
                             ("table-after", 0x6a0)):
            with self.subTest(name=name, offset=offset):
                p = self.path / f"{name}.bin"
                original = p.read_bytes()
                modified = bytearray(original); modified[offset] ^= 1
                p.write_bytes(modified)
                with self.assertRaises(ValueError):
                    verify(self.path)
                p.write_bytes(original)

    def test_adjacent_firmware_change_allowed(self):
        p = self.path / "table-after.bin"
        blob = bytearray(p.read_bytes()); blob[0xaa0] ^= 1
        p.write_bytes(blob)
        self.assertTrue(verify(self.path)["reserve_and_release_passed"])


if __name__ == "__main__":
    unittest.main()
