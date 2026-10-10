import struct
import unittest
from vendor_symbols import records, analyze


class SymbolTests(unittest.TestCase):
    def test_address_precedes_its_name(self):
        data = (struct.pack('<HHHB', 0x123, 2, 0, 4) + b'_one' +
                struct.pack('<HHHB', 0x456, 3, 0, 4) + b'_two')
        result = records(data, 0, len(data), 0x1800)
        self.assertEqual(result['_one']['file_offset'], 0x1943)
        self.assertEqual(result['_two']['file_offset'], 0x1c86)

    def test_truncated_name(self):
        data = struct.pack('<HHHB', 0, 0, 0, 10) + b'x'
        with self.assertRaises(ValueError):
            records(data, 0, len(data), 0)

    def test_unknown_binary_rejected(self):
        with self.assertRaises(ValueError):
            analyze(b'MZ' + bytes(128))


if __name__ == '__main__':
    unittest.main()
