import types
import unittest
import zlib
from unpack_firmware import inspect_archive, verify_output


class UnpackTests(unittest.TestCase):
    def test_unrecognized_input_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect_archive(bytes(0x38000))

    def test_truncated_output_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'size/CRC'):
            verify_output(b'abc', types.SimpleNamespace(file_size=4, CRC=0))

    def test_wrong_crc_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'size/CRC'):
            verify_output(b'abc', types.SimpleNamespace(file_size=3, CRC=0))

    def test_correct_crc_alone_does_not_validate_reference(self):
        with self.assertRaisesRegex(ValueError, 'hash'):
            verify_output(b'abc', types.SimpleNamespace(file_size=3, CRC=zlib.crc32(b'abc')))


if __name__ == '__main__':
    unittest.main()
