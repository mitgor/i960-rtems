#!/usr/bin/env python3
"""Regression checks for the captured ISP firmware integrity probe."""

from pathlib import Path
import unittest

from inspect_isp_risc import inspect_image


CAPTURE = (Path(__file__).resolve().parents[4] / 'artifacts/current/'
           'accele160-timer-interrupt-20261025/isp-risc-stock-1000-4379.bin')


class InspectIspRiscTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = CAPTURE.read_bytes()

    def test_stock_capture(self):
        report = inspect_image(self.image)
        self.assertEqual(report['end_address'], 0x4379)
        self.assertEqual(report['declared_words'], 0x3379)
        self.assertEqual(report['checksum'], 0)
        self.assertIn('ISP1216 Firmware  Version 10.01', report['header'])

    def test_truncation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'declared length'):
            inspect_image(self.image[:-2])

    def test_bad_checksum_rejected(self):
        changed = bytearray(self.image)
        changed[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'checksum'):
            inspect_image(changed)

    def test_bad_second_word_rejected(self):
        changed = bytearray(self.image)
        changed[2:4] = (0xffff).to_bytes(2, 'little')
        # Preserve the global checksum to isolate the address-range check.
        old = int.from_bytes(changed[-2:], 'little')
        changed[-2:] = ((old - (0xffff - 0x1041)) & 0xffff).to_bytes(2, 'little')
        with self.assertRaisesRegex(ValueError, 'outside the image'):
            inspect_image(changed)


if __name__ == '__main__':
    unittest.main()
