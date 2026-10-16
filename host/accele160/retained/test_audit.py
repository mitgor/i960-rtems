import hashlib
from pathlib import Path
import unittest

from audit import make, EXPECTED_CANDIDATE_SHA

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/current"


class RetainedImageAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = [p.read_bytes() for p in (
            ART / "accele160-guarded-20261016/rawflash-0/data.bin",
            ART / "accele160-allocator-20261016/candidate.bin",
            ROOT / "host/accele160/allocator/handler.bin",
            ROOT / "host/accele160/retained/handler.bin",
            ROOT / "host/accele160/retained/probe.bin",
        )]

    def test_exact_candidate(self):
        image, report = make(*self.inputs)
        self.assertEqual(hashlib.sha256(image).hexdigest(), EXPECTED_CANDIDATE_SHA)
        self.assertEqual(image, (ART / "accele160-retained-20261016/candidate.bin").read_bytes())
        self.assertEqual(report["changed_bytes"], 958)

    def test_mutated_inputs_rejected(self):
        for i in range(len(self.inputs)):
            with self.subTest(i=i):
                inputs = list(self.inputs)
                b = bytearray(inputs[i]); b[len(b) // 2] ^= 1
                inputs[i] = bytes(b)
                with self.assertRaises(ValueError):
                    make(*inputs)


if __name__ == "__main__":
    unittest.main()
