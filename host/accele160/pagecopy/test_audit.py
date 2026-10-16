import hashlib
from pathlib import Path
import unittest

from audit import make, EXPECTED_CANDIDATE_SHA

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/current"


class PageCopyAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = [p.read_bytes() for p in (
            ART / "accele160-guarded-20261016/rawflash-0/data.bin",
            ART / "accele160-retained-20261016/candidate.bin",
            ROOT / "host/accele160/retained/handler.bin",
            ROOT / "host/accele160/pagecopy/handler.bin",
            ROOT / "host/accele160/pagecopy/probe.bin",
        )]

    def test_exact_image(self):
        image, result = make(*self.inputs)
        self.assertEqual(hashlib.sha256(image).hexdigest(), EXPECTED_CANDIDATE_SHA)
        self.assertEqual(image, (ART / "accele160-pagecopy-20261016/candidate.bin").read_bytes())
        self.assertEqual(result["changed_bytes"], 1231)

    def test_mutations_rejected(self):
        for i in range(len(self.inputs)):
            with self.subTest(i=i):
                inputs = list(self.inputs)
                data = bytearray(inputs[i]); data[len(data) // 2] ^= 1
                inputs[i] = bytes(data)
                with self.assertRaises(ValueError):
                    make(*inputs)


if __name__ == "__main__":
    unittest.main()
