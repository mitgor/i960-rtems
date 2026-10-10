import unittest
from pathlib import Path

from package_update import END, START, package

ROOT = Path(__file__).resolve().parents[2] / 'artifacts'


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = [
            (ROOT/'private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes(),
            (ROOT/'vendor-fujitsu/4.07-0-29/unpacked.bin').read_bytes(),
            (ROOT/'romhook-20261010/romhook.bin').read_bytes(),
            (ROOT/'romhook-20261010/candidate-full-rom.bin').read_bytes(),
            (ROOT/'vendor-fujitsu/4.07-0-29/Fgj40729.img.decoded').read_bytes()]

    def test_exact_reconstruction(self):
        stock, _, _, candidate, vendor = self.inputs
        result, report = package(*self.inputs)
        self.assertEqual(result[:512], vendor[:512])
        self.assertEqual(result[-10:], vendor[-10:])
        self.assertEqual(stock[:START] + result[512:-10] + stock[END:], candidate)
        self.assertEqual(len(result), len(vendor))
        self.assertFalse(report['flash_ready'])

    def test_reject_mutated_inputs(self):
        for index in range(len(self.inputs)):
            with self.subTest(index=index):
                inputs = self.inputs.copy()
                data = bytearray(inputs[index])
                data[0] ^= 1
                inputs[index] = bytes(data)
                with self.assertRaises(ValueError):
                    package(*inputs)

    def test_reject_noncomponent_change(self):
        inputs = self.inputs.copy()
        data = bytearray(inputs[3])
        data[0x7c000] ^= 1
        inputs[3] = bytes(data)
        with self.assertRaises(ValueError):
            package(*inputs)
