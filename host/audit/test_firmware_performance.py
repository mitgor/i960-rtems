#!/usr/bin/env python3
"""Reject corrupted byte evidence and malformed historical diagnostic pages."""
import copy
import json
from pathlib import Path
import tarfile
import unittest

from firmware_performance import ROOT, checked_rows, decode_dram, diagnostic_pages


class EvidenceTests(unittest.TestCase):
    def test_disassembly_bytes_bounds_duplicates(self):
        row = "c0010000:\t00 00 00 0a \tret"
        blob = bytes.fromhex("00 00 00 0a")
        self.assertEqual(checked_rows(row, blob, 0xc0010000)[0xc0010000][1], "ret")
        for text, data, base in [(row, b"\0" * 4, 0xc0010000),
                                 (row, blob, 0xc0010004),
                                 (row + "\n" + row, blob, 0xc0010000),
                                 ("", blob, 0xc0010000)]:
            with self.assertRaises(ValueError):
                checked_rows(text, data, base)

    def test_dram_encoding_is_not_capacity(self):
        decoded = decode_dram([0xb4f, 0xc0000000, 0, 0, 204, 1])
        self.assertTrue(decoded["edo_two_banks"])
        self.assertEqual(decoded["bank_leaf_mib_encoding"], 64)
        self.assertFalse(decoded["installed_capacity_from_encoding"])
        self.assertEqual(decoded["read_fields"]["extra_recovery"], 0)
        self.assertTrue(decoded["parity_enabled"])
        changed = decode_dram([0xb43, 0xc0000000, 0x20103, 0x10202, 0x100cc, 3])
        self.assertFalse(changed["refresh_enabled"])
        self.assertEqual(changed["read_fields"], {"ras_to_cas": 2, "cas_width": 1, "extra_recovery": 3})
        self.assertTrue(changed["parity_odd"])

    def test_archived_pages_and_mutations(self):
        p = ROOT / "artifacts/rtems-residentnet-decode-20261011/residentnet-decode-v3.tar.xz"
        with tarfile.open(p) as t:
            records = json.load(t.extractfile("residentnet-decode-bounded3/cache-pages.json"))
        self.assertEqual(diagnostic_pages(records)[3][:6], [0xb4f, 0xc0000000, 0, 0, 204, 1])
        cases = [records + [records[0]], records[:2]]
        for index, offset in [(0, 150), (3, 152)]:
            altered = copy.deepcopy(records)
            altered[index][offset] ^= 1
            cases.append(altered)
        altered = copy.deepcopy(records)
        altered[0].append(0)
        cases.append(altered)
        for case in cases:
            with self.assertRaises(ValueError):
                diagnostic_pages(case)


if __name__ == "__main__":
    unittest.main()
