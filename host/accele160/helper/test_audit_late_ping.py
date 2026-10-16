import subprocess
import unittest
from pathlib import Path

from audit_late_ping import audit


ROOT = Path(__file__).resolve().parents[3]
FLASH = ROOT / "artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin"
ART = ROOT / "artifacts/current/accele160-late-ping-20261016"


class LatePingAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flash = FLASH.read_bytes()
        cls.handler = (ART / "late_ping_handler.bin").read_bytes()
        cls.site = (ART / "late_ping_callsite.bin").read_bytes()

    def test_exact_late_route_and_checksums(self):
        result = audit(self.flash, self.handler, self.site)
        self.assertEqual(result["late_branch"], "0xc000c9cc -> 0xc000e1d8")
        self.assertEqual(result["changed_flash_bytes"], 155)
        self.assertTrue(result["known_checksums_pass"])
        self.assertFalse(result["card_executed"])

    def test_rejects_code_drift(self):
        for blob in (self.handler[:-1], self.handler[:-1] + b"\x00"):
            with self.assertRaisesRegex(ValueError, "unreviewed late PING"):
                audit(self.flash, blob, self.site)
        with self.assertRaisesRegex(ValueError, "unreviewed late PING"):
            audit(self.flash, self.handler, self.site[:-1] + b"\x00")

    def test_rejects_stock_drift(self):
        for offset in (0x439cc, 0x451d8, 0x534fc, 0xfc11c, 0xfff30):
            changed = bytearray(self.flash)
            changed[offset] ^= 1
            with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                audit(bytes(changed), self.handler, self.site)


if __name__ == "__main__":
    unittest.main()
