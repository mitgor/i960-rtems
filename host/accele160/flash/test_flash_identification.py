import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run_ram_payload import SID1, decode_flash_identification  # noqa: E402


class IdentificationTests(unittest.TestCase):
    def test_expected_unlocked_s3(self):
        result = decode_flash_identification([SID1, 0x89, 0xa6, 0, 0])
        self.assertTrue(result["expected_s3_unlocked"])
        self.assertEqual(result["block_lock_mask"], "0x0000")

    def test_locked_or_wrong_chip_is_not_qualified(self):
        for record in ([SID1, 0x89, 0xa6, 0, 1],
                       [SID1, 0x89, 0xa6, 1, 0],
                       [SID1, 0x89, 0xa5, 0, 0]):
            self.assertFalse(decode_flash_identification(record)
                             ["expected_s3_unlocked"])

    def test_missing_record_rejected(self):
        with self.assertRaises(RuntimeError):
            decode_flash_identification([0, 0x89, 0xa6, 0, 0])


if __name__ == "__main__":
    unittest.main()
