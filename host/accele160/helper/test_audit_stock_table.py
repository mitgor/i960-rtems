import subprocess
import unittest
from pathlib import Path

from audit_stock_table import audit


ROOT = Path(__file__).resolve().parents[3]
FLASH = ROOT / "artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin"
PAGE = ROOT / "artifacts/current/accele160-table-snapshot-20261016/table-page.bin"


class StockTableAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flash = FLASH.read_bytes()
        cls.page = PAGE.read_bytes()

    def test_full_page_equals_stock(self):
        result = audit(self.flash, self.page)
        self.assertEqual(result["matched_stock_runtime_bytes"], 4096)
        self.assertEqual(result["stock_8f"], "0xc0023790")
        self.assertFalse(result["patched_table_persistence_proven"])

    def test_rejects_page_mutation_or_length(self):
        for offset in (0, 0x4F8, 0x4FC, 4095):
            page = bytearray(self.page)
            page[offset] ^= 1
            with self.assertRaisesRegex(ValueError, "live page differs"):
                audit(self.flash, bytes(page))
        with self.assertRaisesRegex(ValueError, "one 4 KiB"):
            audit(self.flash, self.page[:-1])

    def test_rejects_stock_drift(self):
        flash = bytearray(self.flash)
        flash[0xFFF30] ^= 1
        with self.assertRaises((ValueError, subprocess.CalledProcessError)):
            audit(bytes(flash), self.page)


if __name__ == "__main__":
    unittest.main()
