import unittest
from pathlib import Path

from audit_helper_site import inspect


ROOT = Path(__file__).resolve().parents[3]
FLASH = ROOT / "artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin"
PROBE = ROOT / "artifacts/current/accele160-startup-20261016/probe.bin"


class HelperSiteAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flash = FLASH.read_bytes()
        cls.probe = PROBE.read_bytes()

    def test_dormant_candidate_is_verified_but_not_wired(self):
        result = inspect(self.flash, self.probe)
        self.assertEqual(result["ioctl_dispatch"]["stock_0x8f_target"],
                         "0xc0023790 (unsupported, status 0x104)")
        self.assertEqual(result["loader_cave"]["erased_bytes"], 7720)
        self.assertEqual(result["offline_packaging_rehearsal"]["changed_byte_count"], 88)
        self.assertFalse(result["offline_packaging_rehearsal"]["entry_wired"])

    def test_rejects_unaccepted_flash_and_oversized_probe(self):
        damaged = bytearray(self.flash)
        damaged[0x451d8] = 0
        with self.assertRaisesRegex(ValueError, "loader checksum"):
            inspect(bytes(damaged), self.probe)
        with self.assertRaisesRegex(ValueError, "at most 256"):
            inspect(self.flash, self.probe * 4)


if __name__ == "__main__":
    unittest.main()
