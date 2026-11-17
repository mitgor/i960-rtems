import unittest
from pathlib import Path

from pack import build, verify, FW, LOADER, PAYLOAD, TRAILER


ROOT = Path(__file__).resolve().parents[3]
STOCK = ROOT / "artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin"
SPARE = ROOT / "artifacts/current/accele160-spare-rom-20261025/rawflash-0/data.bin"
SECOND_SPARE = ROOT / "artifacts/current/accele160-second-spare-20261026/rawflash-0/data.bin"


class PackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = STOCK.read_bytes()
        cls.stage2 = bytes.fromhex("01020304")
        cls.kernel = bytes.fromhex("1122334455667788")

    def test_stock_regions_and_checksums(self):
        candidate, receipt = build(self.stock, self.stage2, self.kernel)
        self.assertEqual(candidate[:FW], self.stock[:FW])
        self.assertEqual(candidate[0xc0000:], self.stock[0xc0000:])
        self.assertFalse(receipt["safe_to_flash"])
        self.assertFalse(receipt["physical_boot_tested"])
        verify(candidate, self.stock, self.stage2, self.kernel)

    def test_rejects_changed_stock_and_oversized_payload(self):
        tampered = bytearray(self.stock)
        tampered[0] ^= 1
        with self.assertRaisesRegex(ValueError, "accepted full stock"):
            build(bytes(tampered), self.stage2, self.kernel)
        with self.assertRaisesRegex(ValueError, "payload size"):
            build(self.stock, self.stage2, b"X" * (0x70000 + 4))

    def test_detects_corrupt_candidate(self):
        candidate, _ = build(self.stock, self.stage2, self.kernel)
        for address in (0, LOADER, PAYLOAD, PAYLOAD + 16, TRAILER + 8,
                        TRAILER + 24, TRAILER + 124, 0xfff30):
            with self.subTest(address=hex(address)):
                tampered = bytearray(candidate)
                tampered[address] ^= 1
                with self.assertRaises(ValueError):
                    verify(bytes(tampered), self.stock, self.stage2, self.kernel)

    def test_spare_uses_its_own_descriptor(self):
        spare = SPARE.read_bytes()
        candidate, receipt = build(spare, self.stage2, self.kernel)
        self.assertEqual(candidate[0xe0000:0xf0000], spare[0xe0000:0xf0000])
        self.assertNotEqual(candidate[0xe0000:0xf0000], self.stock[0xe0000:0xf0000])
        self.assertEqual(receipt["stock_sha256"],
                         "fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816")

    def test_second_spare_uses_its_own_descriptor(self):
        spare = SECOND_SPARE.read_bytes()
        candidate, receipt = build(spare, self.stage2, self.kernel)
        self.assertEqual(candidate[0xe0000:0xf0000], spare[0xe0000:0xf0000])
        self.assertNotEqual(candidate[0xe0000:0xf0000], SPARE.read_bytes()[0xe0000:0xf0000])
        self.assertEqual(receipt["stock_sha256"],
                         "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943")


if __name__ == "__main__":
    unittest.main()
