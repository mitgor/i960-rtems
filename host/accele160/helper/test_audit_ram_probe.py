import hashlib
from pathlib import Path
import unittest

from audit_ram_probe import make, CANDIDATE_SHA

ROOT = Path(__file__).resolve().parents[3]
CURRENT = ROOT / "artifacts/current"


class RamProbeAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = [p.read_bytes() for p in (
            CURRENT / "accele160-guarded-20261016/rawflash-0/data.bin",
            CURRENT / "accele160-flash-candidate-20261016/candidate.bin",
            CURRENT / "accele160-late-ping-20261016/late_ping_handler.bin",
            CURRENT / "accele160-late-ping-20261016/late_ping_callsite.bin",
            CURRENT / "accele160-ramprobe-20261016/handler.bin",
            CURRENT / "accele160-startup-20261016/probe.bin",
        )]

    def test_exact_candidate(self):
        image, audit = make(*self.inputs)
        self.assertEqual(hashlib.sha256(image).hexdigest(), CANDIDATE_SHA)
        self.assertTrue(audit["boot_block_unchanged"])
        self.assertEqual(image, (CURRENT / "accele160-ramprobe-20261016/candidate.bin").read_bytes())

    def test_mutated_original_rejected(self):
        inputs = list(self.inputs)
        original = bytearray(inputs[1]); original[0x80000] ^= 1
        inputs[1] = bytes(original)
        with self.assertRaises(ValueError): make(*inputs)

    def test_mutated_handler_rejected(self):
        inputs = list(self.inputs)
        handler = bytearray(inputs[4]); handler[42] ^= 1
        inputs[4] = bytes(handler)
        with self.assertRaises(ValueError): make(*inputs)

    def test_mutated_probe_rejected(self):
        inputs = list(self.inputs)
        probe = bytearray(inputs[5]); probe[4] ^= 1
        inputs[5] = bytes(probe)
        with self.assertRaises(ValueError): make(*inputs)


if __name__ == "__main__":
    unittest.main()
