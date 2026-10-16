import unittest
from pathlib import Path

from analyze_allocator_table import parse


CAPTURE = (Path(__file__).resolve().parents[3] /
           "artifacts/current/accele160-ramprobe-20261016/live/dram-survey-2/c0384000-0.bin")


class AllocatorTableTest(unittest.TestCase):
    def test_exact_live_snapshot(self):
        parsed = parse(CAPTURE.read_bytes())
        self.assertEqual([(r["first_block"], r["end_block_exclusive"])
                          for r in parsed["lower_pool"]["free_runs"]], [(154, 192)])
        self.assertEqual([(r["first_block"], r["end_block_exclusive"])
                          for r in parsed["upper_pool"]["free_runs"]], [(195, 242)])

    def test_changed_snapshot_rejected(self):
        data = bytearray(CAPTURE.read_bytes())
        data[0x2A0 + 154 * 4] ^= 1
        with self.assertRaises(ValueError):
            parse(bytes(data))


if __name__ == "__main__":
    unittest.main()
