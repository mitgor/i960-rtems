import subprocess
import unittest
from pathlib import Path

from audit_ping_candidate import audit


ROOT = Path(__file__).resolve().parents[3]
FLASH = ROOT / "artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin"
ART = ROOT / "artifacts/current/accele160-ping-handler-20261016"
SITE = ROOT / "artifacts/current/accele160-dispatch-rehearsal-20261016/dispatch_callsite.bin"


class PingCandidateAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flash = FLASH.read_bytes()
        cls.handler = (ART / "ping_handler.bin").read_bytes()
        cls.site = SITE.read_bytes()

    def test_exact_in_memory_candidate(self):
        result = audit(self.flash, self.handler, self.site)
        self.assertEqual(result["handler_bytes"], 148)
        self.assertEqual(result["changed_flash_bytes"], 157)
        self.assertTrue(result["known_checksums_pass"])
        self.assertFalse(result["image_written"])
        self.assertFalse(result["card_executed"])

    def test_rejects_handler_and_callsite_drift(self):
        for handler in (self.handler[:-1], self.handler[:-1] + b"\x00"):
            with self.assertRaisesRegex(ValueError, "unreviewed i960 PING"):
                audit(self.flash, handler, self.site)
        with self.assertRaisesRegex(ValueError, "unreviewed i960 PING"):
            audit(self.flash, self.handler, self.site[:-1] + b"\x00")

    def test_rejects_stock_drift(self):
        for offset in (0x451d8, 0x43638, 0x534fc, 0xfff30):
            changed = bytearray(self.flash)
            changed[offset] ^= 1
            with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                audit(bytes(changed), self.handler, self.site)


if __name__ == "__main__":
    unittest.main()
