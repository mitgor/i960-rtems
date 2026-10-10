"""Ensure the live probe embeds only the two inspected target builds."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADER = (ROOT / 'host/dump/rom_exec.h').read_text()


def array(name):
    match = re.search(r'\b' + name + r'\[[^]]+\]\s*=\s*\{([^}]+)\}', HEADER)
    if not match:
        raise AssertionError('missing array ' + name)
    return bytes(int(x, 16) for x in re.findall(r'0x([0-9a-fA-F]{2})\b', match.group(1)))


class RomExecBuildTests(unittest.TestCase):
    def test_flash_ret_address_is_in_full_rom(self):
        rom = (ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes()
        self.assertEqual(rom[0x3022c:0x30230], bytes.fromhex('0000000a'))
        self.assertEqual(rom[0x4822c:0x48230], bytes.fromhex('794a49b0'))
        capture = ROOT/'artifacts/romfetch-live-20261010/flash-map3'
        for base in (0xfefb0200, 0xfefc8200, 0xfefe0000):
            name = f'{base:08x}'
            live = (capture/f'{name}-a5.bin').read_bytes()
            self.assertEqual(live, (capture/f'{name}-5a.bin').read_bytes())
            self.assertEqual(len(live), 64)
            for i in range(0, 64, 4):
                observed = int.from_bytes(live[i:i+4], 'little')
                expected = ((base+i) & 0xffffff00) | rom[base+i-0xfef80000]
                self.assertEqual(observed, expected)

    def test_target_binaries_pinned(self):
        self.assertEqual(array('exec_ram_code'),
                         (ROOT/'loader/romfetch/ram-status.bin').read_bytes())
        self.assertEqual(array('exec_flash_code'),
                         (ROOT/'loader/romfetch/flash-ret-probe.bin').read_bytes())

    def test_second_stub_targets_pinned_physical_flash_ret(self):
        code = array('exec_flash_code')
        self.assertEqual(code, (ROOT/'loader/romfetch/flash-ret-probe.bin').read_bytes())
        self.assertIn(bytes.fromhex('821d8065'), code)  # icctl 2,0,g0
        self.assertNotIn(bytes.fromhex('003000860882fcfe'), code)  # wrong address
        self.assertIn(bytes.fromhex('003000862c02fbfe'), code)  # callx flash RET
        self.assertIn(bytes.fromhex('021e9065'), code)  # dcctl 2,0,g2
        self.assertIn(bytes.fromhex('7f01888c18208c8a'), code)  # status 017f
        self.assertTrue(code.endswith(bytes.fromhex('d0ba04c000500484')))

    def test_ram_stub_invalidates_data_cache(self):
        code = array('exec_ram_code')
        self.assertTrue(code.startswith(bytes.fromhex('021e9065')))
        self.assertIn(bytes.fromhex('7e01888c18208c8a'), code)
