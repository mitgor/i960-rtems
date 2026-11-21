"""Check the pure gates that protect a diagnostic flash attempt."""
import json
from pathlib import Path
import tempfile
import unittest

from flash_native_spare import (SENSE_PROBE_MODULE_SHA, REJECTED_STOCK_SHA,
                                verify_sense_probe)


class SenseProofTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.boot = "new-cold-boot"
        self.sense = "00" * 12 + "8104"
        (self.path / "preflight.json").write_text(json.dumps({
            "boot_id": self.boot, "bdf": "0000:37:09.1",
            "stock_sha256": REJECTED_STOCK_SHA,
            "module_sha256": SENSE_PROBE_MODULE_SHA, "ioctl": "0x8f",
            "flash_program_erase_commands": 0,
        }))
        self.result = {"boot_id": self.boot, "sense": self.sense,
                       "internal_status": "0x104", "module_released": True,
                       "flash_program_erase_commands": 0}
        self.write_result()
        (self.path / "status.txt").write_text(
            f"started=1 done=1 status=2 residual=0 sense_len=14 sense={self.sense}\n")

    def tearDown(self):
        self.temp.cleanup()

    def write_result(self):
        (self.path / "result.json").write_text(json.dumps(self.result))

    def test_completed_unsupported_command(self):
        self.assertEqual(verify_sense_probe(self.path, self.boot)["internal_status"],
                         "0x104")

    def test_wrong_boot_or_unreleased_module_fails(self):
        with self.assertRaises(ValueError):
            verify_sense_probe(self.path, "another-boot")
        self.result["module_released"] = False
        self.write_result()
        with self.assertRaises(ValueError):
            verify_sense_probe(self.path, self.boot)

    def test_missing_sense_fails(self):
        (self.path / "status.txt").write_text(
            "started=1 done=1 status=2 residual=0 sense_len=0 sense=\n")
        with self.assertRaises(ValueError):
            verify_sense_probe(self.path, self.boot)


if __name__ == "__main__":
    unittest.main()
