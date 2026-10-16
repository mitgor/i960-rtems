import hashlib
from pathlib import Path
import unittest

from audit import make, EXPECTED_CANDIDATE_SHA

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/current"


class AllocatorImageAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = [p.read_bytes() for p in (
            ART / "accele160-guarded-20261016/rawflash-0/data.bin",
            ART / "accele160-ramprobe-20261016/candidate.bin",
            ART / "accele160-ramprobe-20261016/handler.bin",
            ROOT / "host/accele160/allocator/handler.bin",
            ART / "accele160-startup-20261016/probe.bin",
        )]

    def test_exact_image(self):
        image, receipt = make(*self.inputs)
        self.assertEqual(hashlib.sha256(image).hexdigest(), EXPECTED_CANDIDATE_SHA)
        self.assertEqual(image, (ART / "accele160-allocator-20261016/candidate.bin").read_bytes())
        self.assertEqual(receipt["changed_bytes"], 484)

    def test_each_binary_mutation_fails(self):
        for index in range(len(self.inputs)):
            with self.subTest(index=index):
                inputs = list(self.inputs)
                value = bytearray(inputs[index]); value[len(value) // 2] ^= 1
                inputs[index] = bytes(value)
                with self.assertRaises(ValueError):
                    make(*inputs)


if __name__ == "__main__":
    unittest.main()
