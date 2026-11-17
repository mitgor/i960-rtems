import json
from pathlib import Path
import unittest

from preflight import verify_pair

ROOT = Path(__file__).resolve().parents[3]
CAPTURE = ROOT / "artifacts/current/accele160-guarded-20261016"
CANDIDATE = ROOT / "artifacts/current/accele160-native-rom-20261020/native-rom-prototype.bin"
SPARE = ROOT / "artifacts/current/accele160-spare-rom-20261025"
SECOND_SPARE = ROOT / "artifacts/current/accele160-second-spare-20261026"


class PreflightTest(unittest.TestCase):
    def test_original_stock_pair_meets_capture_contract(self):
        a, b = (CAPTURE / "rawflash-0", CAPTURE / "rawflash-1")
        boot = json.loads((a / "request.json").read_text())["boot_id"]
        receipt = verify_pair(CANDIDATE.read_bytes(), (a, b), "0000:37:09.1", boot)
        self.assertEqual(receipt["stock_sha256"],
                         "0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a")
        self.assertFalse(receipt["flashimage_issued"])

    def test_rejects_stale_boot_and_tampered_image(self):
        a, b = (CAPTURE / "rawflash-0", CAPTURE / "rawflash-1")
        candidate = CANDIDATE.read_bytes()
        with self.assertRaisesRegex(ValueError, "read 0"):
            verify_pair(candidate, (a, b), "0000:37:09.1", "different-boot")
        changed = bytearray(candidate)
        changed[0x47020] ^= 1
        with self.assertRaisesRegex(ValueError, "candidate identity"):
            verify_pair(bytes(changed), (a, b), "0000:37:09.1",
                        json.loads((a / "request.json").read_text())["boot_id"])

    def test_spare_pair_and_candidate(self):
        a, b = SPARE / "rawflash-0", SPARE / "rawflash-1"
        boot = json.loads((a / "request.json").read_text())["boot_id"]
        receipt = verify_pair((SPARE / "native-rom-spare-prototype.bin").read_bytes(),
                              (a, b), "0000:37:04.1", boot)
        self.assertEqual(receipt["stock_sha256"],
                         "fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816")
        self.assertFalse(receipt["flashimage_issued"])

    def test_second_spare_pair_and_romless_candidate(self):
        a, b = SECOND_SPARE / "rawflash-0", SECOND_SPARE / "rawflash-1"
        boot = json.loads((a / "request.json").read_text())["boot_id"]
        receipt = verify_pair(
            (SECOND_SPARE / "native-rom-second-spare-no-x86-rom.bin").read_bytes(),
            (a, b), "0000:37:04.1", boot)
        self.assertEqual(receipt["stock_sha256"],
                         "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943")
        self.assertEqual(receipt["candidate_sha256"],
                         "33f7a5585c41850690ee0fa05a56382c626e75cd17c8e5185a764f57f741f221")
        self.assertFalse(receipt["flashimage_issued"])


if __name__ == "__main__":
    unittest.main()
