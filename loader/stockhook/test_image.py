import unittest
from pathlib import Path
import build_image as b

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'artifacts'


class StockHookImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = (ART / 'private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes()
        cls.unpacked = (ART / 'vendor-fujitsu/4.07-0-29/unpacked.bin').read_bytes()
        cls.code = (ART / 'stockhook-20261010/stockhook.bin').read_bytes()

    def test_reconstruct_archived_image(self):
        image, report = b.build(self.stock, self.unpacked, self.code)
        self.assertEqual(image, (ART / 'stockhook-20261010/candidate-full-rom.bin').read_bytes())
        self.assertFalse(report['flash_ready'])
        self.assertEqual(image[0x7c000:], self.stock[0x7c000:])
        self.assertEqual(image[0x30000:0x60000], self.stock[0x30000:0x60000])
        self.assertEqual(b.word(image, b.META_OFFSET + 8), b.ENTRY)
        self.assertEqual(b.word(image, b.META_OFFSET + 0x7c),
                         b.checksum(image[b.META_OFFSET:b.META_OFFSET + 0x7c]))

    def test_refuse_damaged_inputs(self):
        bad = bytearray(self.stock)
        bad[0x79c60] ^= 1
        with self.assertRaises(ValueError):
            b.build(bad, self.unpacked, self.code)
        bad = bytearray(self.unpacked)
        bad[b.TABLE_SLOT - 0xc0010000] ^= 1
        with self.assertRaises(ValueError):
            b.build(self.stock, bad, self.code)
        bad = bytearray(self.code)
        bad[-4] ^= 1
        with self.assertRaises(ValueError):
            b.build(self.stock, self.unpacked, bad)


if __name__ == '__main__':
    unittest.main()
