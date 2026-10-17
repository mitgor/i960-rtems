#!/usr/bin/env python3
"""Pinned firmware-candidate scope and mutation checks."""
import unittest
from pathlib import Path
import audit
ROOT=Path(__file__).resolve().parents[3]

class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=[(ROOT/p).read_bytes() for p in (
            'artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin',
            'artifacts/current/accele160-ownedexec-20261017/candidate.bin',
            'host/accele160/ownedexec/handler.bin',
            'host/accele160/rtems_gate/handler.bin',
            'host/accele160/rtems_gate/prefix.bin')]
    def test_exact_candidate(self):
        image,receipt=audit.make(*self.inputs)
        self.assertEqual(audit.sha(image),audit.CANDIDATE_SHA)
        self.assertTrue(receipt['runtime_unchanged'] and receipt['boot_block_unchanged'])
    def test_mutated_inputs_rejected(self):
        for index in (0,1,3,4):
            with self.subTest(input=index):
                values=list(self.inputs);bad=bytearray(values[index]);bad[8]^=1;values[index]=bytes(bad)
                with self.assertRaises(ValueError):audit.make(*values)

if __name__=='__main__':unittest.main()
