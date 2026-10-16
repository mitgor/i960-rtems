import unittest
import subprocess
from pathlib import Path

from audit_dispatch_rehearsal import audit

ROOT = Path(__file__).resolve().parents[3]
FLASH = ROOT / "artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin"
ART = ROOT / "artifacts/current/accele160-dispatch-rehearsal-20261016"


class DispatchRehearsal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flash = FLASH.read_bytes()
        cls.stub = (ART / "dispatch_stub.bin").read_bytes()
        cls.site = (ART / "dispatch_callsite.bin").read_bytes()

    def test_exact_wiring_preserves_runtime_and_stock_fallback(self):
        receipt = audit(self.flash, self.stub, self.site)
        self.assertEqual(receipt["runtime_table_8e_unchanged"], "0xc00234f8")
        self.assertEqual(receipt["runtime_table_8f_loader_write"],
                         "0xc00234fc -> 0xc000e1f0")
        self.assertEqual(receipt["fallback_target"], "0xc0023790")
        self.assertTrue(receipt["known_checksums_pass"])
        self.assertFalse(receipt["ping_implemented"])

    def test_rejects_drift_in_hook_and_callsite(self):
        for blob in (self.stub[:-1], self.stub[:-1] + b"\x09"):
            with self.assertRaisesRegex(ValueError, "unreviewed routing code"):
                audit(self.flash, blob, self.site)
        with self.assertRaisesRegex(ValueError, "unreviewed routing code"):
            audit(self.flash, self.stub, self.site[:-1] + b"\x08")

    def test_rejects_stock_drift(self):
        for offset in (0x451d8, 0x43638, 0x534fc, 0xfff30):
            damaged = bytearray(self.flash)
            damaged[offset] ^= 1
            with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                audit(bytes(damaged), self.stub, self.site)


if __name__ == "__main__":
    unittest.main()
