#!/usr/bin/env python3
"""The native PCI release must reproduce the stock register writes.

Compares the real pci_release.c (built for the host with sanitizers) against
the stock 6.00-05 trace captured by emulator/pci_register_trace.py. Offline.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'emulator'))
import pci_register_trace as trace  # noqa: E402

STOCK = ROOT / 'artifacts/current/accele160-pci-release-20261117/stock-pci-reg-writes.json'
SCAN_SELECTOR = 0x12a8   # stock secondary scan, deliberately not reproduced


class PciRelease(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.binary = Path(cls.tmp.name) / 'driver'
        subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                        '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                        str(HERE / 'pci_release.c'),
                        str(HERE / 'test_pci_release_driver.c'),
                        '-o', str(cls.binary)], check=True)
        cls.stock = json.loads(STOCK.read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_driver(self, options, signature, ebcr=4, command=0):
        out = subprocess.run([str(self.binary), f'{options:x}', f'{signature:x}',
                              f'{ebcr:x}', f'{command:x}'],
                             text=True, capture_output=True, check=True).stdout
        writes, report = [], None
        for line in out.splitlines():
            parts = line.split()
            if parts[0] == 'W':
                writes.append({'seq': len(writes) + 1, 'origin': 'i960',
                               'addr': int(parts[1], 16), 'size': int(parts[2]),
                               'value': int(parts[3], 16),
                               'retry_before': parts[4] == 'retry-before=1'})
            elif parts[0] == 'REPORT':
                report = [int(x, 16) for x in parts[1:8]] + [int(parts[8]), int(parts[9])]
            else:
                self.fail(line)
        return writes, report

    def stock_sequence(self):
        return [(w['addr'], w['size'], w['value']) for w in self.stock['writes']
                if w['addr'] != SCAN_SELECTOR]

    def test_stock_trace_fixture_is_the_expected_capture(self):
        self.assertEqual(self.stock['image_sha256'],
                         '0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943')
        self.assertTrue(self.stock['summary']['released'])
        self.assertEqual(self.stock['summary']['release_ip'], 'c0052e00')
        self.assertEqual(len(self.stock['writes']), 65)

    def test_rom_kept_matches_stock_write_for_write(self):
        writes, _ = self.run_driver(0, 0xaa55)
        native = [(w['addr'], w['size'], w['value']) for w in writes]
        expected = self.stock_sequence()
        # Only documented difference: aligned 16-bit SISR store instead of the
        # stock unaligned 32-bit store at 0x1042.
        self.assertIn((0x1042, 4, 0x3ff), expected)
        expected[expected.index((0x1042, 4, 0x3ff))] = (0x1042, 2, 0x3ff)
        self.assertEqual(native, expected)

    def test_release_is_last_and_only_then_clears_retry(self):
        for options, signature in ((0, 0xaa55), (1, 0xaa55), (0, 0xaa00)):
            writes, report = self.run_driver(options, signature)
            self.assertEqual((writes[-1]['addr'], writes[-1]['size'],
                              writes[-1]['value']), (0x1040, 2, 0x48))
            self.assertTrue(all(w['retry_before'] for w in writes))
            self.assertEqual(trace.release_seq(writes), len(writes))
            self.assertEqual(report[1:3], [4, 0x48])   # EBCR before, after

    def test_hidden_rom_uses_the_stock_no_rom_path(self):
        for options, signature, flags in ((1, 0xaa55, 3), (0, 0xaa00, 1), (1, 0, 1)):
            writes, report = self.run_driver(options, signature)
            self.assertEqual([(w['size'], w['value']) for w in writes
                              if w['addr'] == 0x1274], [(4, 0)])
            self.assertFalse([w for w in writes if w['addr'] == 0x1278])
            self.assertEqual(report[3], flags)
        _, report = self.run_driver(0, 0xaa55)
        self.assertEqual(report[3], 2)

    def test_state_at_release_equals_stock_except_documented(self):
        writes, _ = self.run_driver(1, 0xaa55)
        native = trace.compared_state(writes)
        expected = dict(self.stock['state_at_release'])
        expected['1274'] = 0          # ERLR: option ROM deliberately hidden
        expected['1278'] = None       # ERTVR untouched on the no-ROM path
        self.assertEqual(native, expected)
        writes, _ = self.run_driver(0, 0xaa55)
        self.assertEqual(trace.compared_state(writes), self.stock['state_at_release'])

    def test_bridge_command_is_saved_and_restored(self):
        writes, report = self.run_driver(1, 0xaa55, command=0x0147)
        command = [w['value'] for w in writes if w['addr'] == 0x1004]
        self.assertEqual(command, [0, 0x0147])
        self.assertEqual(report[6], 0x0147)

    def test_report_identity_and_count(self):
        writes, report = self.run_driver(1, 0xaa55)
        self.assertEqual(report[0], 0x30494350)
        self.assertEqual(report[4], 0x00501069)
        self.assertEqual(report[5], 0x00541069)
        self.assertEqual(report[7], len(writes))
        self.assertEqual(report[8], len(writes))

    def test_already_released_strap_is_reported_not_assumed(self):
        # If the board were strapped RETRY low, EBCR starts without bit 2.
        _, report = self.run_driver(1, 0xaa55, ebcr=0x18)
        self.assertEqual(report[1:3], [0x18, 0x48])


if __name__ == '__main__':
    unittest.main()
