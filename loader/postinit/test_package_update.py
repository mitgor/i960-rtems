import unittest
from pathlib import Path
from package_update import package, START, END

ROOT = Path(__file__).resolve().parents[2]


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a = ROOT / 'artifacts'
        cls.inputs = [
            (a/'private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes(),
            (a/'postinit-preflight-20261010/experimental-full-rom.bin').read_bytes(),
            (a/'postinit-preflight-20261010/loader.bin').read_bytes(),
            (a/'vendor-fujitsu/4.07-0-29/unpacked.bin').read_bytes(),
            (a/'vendor-fujitsu/4.07-0-29/Fgj40729.img.decoded').read_bytes()]

    def test_reconstruct_and_preserve_container(self):
        stock, candidate, _, _, vendor = self.inputs
        result, report = package(*self.inputs)
        self.assertEqual(len(result), 229898)
        self.assertEqual(result[:512], vendor[:512])
        self.assertEqual(result[-10:], vendor[-10:])
        self.assertEqual(stock[:START]+result[512:-10]+stock[END:], candidate)
        self.assertFalse(report['flash_ready'])
        self.assertFalse(report['vendor_acceptance_verified'])

    def test_reject_unrelated_candidate_changes(self):
        for offset in (0, START, 0x60000, 0x67f68, END, 0x7ff40):
            with self.subTest(offset=offset):
                inputs = self.inputs.copy()
                data = bytearray(inputs[1]); data[offset] ^= 1
                inputs[1] = bytes(data)
                with self.assertRaises(ValueError):
                    package(*inputs)

    def test_reject_donor_or_container_corruption(self):
        for index in (0, 3, 4):
            with self.subTest(index=index):
                inputs = self.inputs.copy()
                inputs[index] = bytes([inputs[index][0] ^ 1])+inputs[index][1:]
                with self.assertRaises(ValueError):
                    package(*inputs)

    def test_reject_truncation(self):
        for index in range(5):
            with self.subTest(index=index):
                inputs = self.inputs.copy(); inputs[index] = inputs[index][:-1]
                with self.assertRaises(ValueError):
                    package(*inputs)
