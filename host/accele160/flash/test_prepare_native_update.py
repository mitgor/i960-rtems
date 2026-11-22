import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_native_update import IMAGE_BYTES, prepare


class PrepareNativeUpdateTests(unittest.TestCase):
    def setUp(self):
        self.base = bytes(IMAGE_BYTES)
        self.target = bytearray(self.base)
        self.target[0x51000] = 0xA5

    def test_valid_target(self):
        manifest = prepare(self.base, bytes(self.target))
        self.assertEqual(manifest["changed_64k_blocks"], ["0x50000"])
        self.assertEqual(len(manifest["chunks_fnv32"]), 256)
        self.assertEqual(manifest["target_sha256"], hashlib.sha256(self.target).hexdigest())

    def test_protected_regions(self):
        for offset in (0, 0x3ffff, 0xc0000, 0xfffff):
            with self.subTest(offset=offset):
                target = bytearray(self.target)
                target[offset] ^= 1
                with self.assertRaises(ValueError):
                    prepare(self.base, target)

    def test_size(self):
        with self.assertRaises(ValueError):
            prepare(self.base[:-1], bytes(self.target))


if __name__ == "__main__":
    unittest.main()
