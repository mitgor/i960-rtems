import struct
import unittest
from pathlib import Path
from staging_geometry import model

ROOT = Path(__file__).resolve().parents[2]/'artifacts'


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.data = (ROOT/'staging-allocation-20261010/control/enquiry-before.bin').read_bytes()

    def test_live_and_historical_geometry_agree(self):
        old = (ROOT/'private-dumps/snapshot-fresh-20261010T125336Z/00000/enquiry-before.bin').read_bytes()
        for data in (self.data, old):
            report = model(data)
            self.assertEqual(report['allocation_unit'], 0x2000)
            self.assertEqual(report['pool_blocks'], 0x739)
            self.assertEqual(report['reserved_blocks'], 65)
            self.assertEqual(report['predicted_staging_base'], 0xc0f2c000)
            self.assertEqual(report['allocation_end_exclusive'], 0xc0fae000)
            self.assertEqual((report['predicted_staging_base']+report['pointer_read_offset']) & 0xffffffff, 0xc0112a70)
            self.assertFalse(report['pointer_observed'])

    def test_refuse_invalid_geometry(self):
        for offset, fmt, value in [(0x68, '<H', 0), (0x20, '<I', 0x40000),
                                   (0x1c, '<I', 1), (0x1c, '<I', 0x2000),
                                   (0x18, '<I', 0x100000)]:
            with self.subTest(offset=offset, value=value):
                data = bytearray(self.data); struct.pack_into(fmt, data, offset, value)
                with self.assertRaises(ValueError): model(data)

    def test_refuse_short_or_wrong_version(self):
        with self.assertRaises(ValueError): model(self.data[:100])
        data = bytearray(self.data); data[6] = 39
        with self.assertRaises(ValueError): model(data)
