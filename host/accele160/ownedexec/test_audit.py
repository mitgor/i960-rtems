import hashlib
from pathlib import Path
import unittest
from audit import make, EXPECTED_CANDIDATE_SHA
ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'artifacts/current'
class DigestAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = [p.read_bytes() for p in (
            ART/'accele160-guarded-20261016/rawflash-0/data.bin',
            ART/'accele160-digest-20261017/candidate.bin',
            ROOT/'host/accele160/digest/handler.bin',
            ROOT/'host/accele160/ownedexec/handler.bin',
            ROOT/'host/accele160/ownedexec/probe.bin')]
    def test_exact(self):
        image, receipt=make(*self.inputs)
        self.assertEqual(hashlib.sha256(image).hexdigest(),EXPECTED_CANDIDATE_SHA)
        self.assertEqual(image,(ART/'accele160-ownedexec-20261017/candidate.bin').read_bytes())
        self.assertEqual(receipt['changed_bytes'],1919)
    def test_mutations_rejected(self):
        for i in range(len(self.inputs)):
            with self.subTest(i=i):
                inputs=list(self.inputs);data=bytearray(inputs[i]);data[len(data)//2]^=1;inputs[i]=bytes(data)
                with self.assertRaises(ValueError):make(*inputs)
if __name__=='__main__':unittest.main()
