import unittest
from pathlib import Path

from stage_plan import build_plan

ROOT = Path(__file__).resolve().parents[2]
STOCK = (ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes()
CANDIDATE = (ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin').read_bytes()
HOOK = (ROOT/'artifacts/romhook-20261010/romhook.bin').read_bytes()


class StagePlanTests(unittest.TestCase):
    def test_exact_three_write_plan(self):
        entries = build_plan(STOCK, CANDIDATE, HOOK)
        self.assertEqual([(e['offset'], e['length']) for e in entries],
                         [(0x60000, 48), (0x67f68, 4), (0x67fdc, 4)])

    def test_rejects_other_image_or_hook(self):
        altered = bytearray(CANDIDATE)
        altered[0x30000] ^= 1
        with self.assertRaises(ValueError):
            build_plan(STOCK, altered, HOOK)
        with self.assertRaises(ValueError):
            build_plan(STOCK, CANDIDATE, HOOK[:-1])
