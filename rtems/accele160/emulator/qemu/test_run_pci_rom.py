#!/usr/bin/env python3
"""Guard the Mylex ROM locator against the earlier VGA-entry false positive."""

import struct
import unittest

from run_pci_rom import GUEST_ROM_WINDOW, decode_lp_mailbox, find_guest_rom


class GuestRomLocatorTest(unittest.TestCase):
    def test_finds_mylex_after_header_is_changed(self):
        memory = bytearray(GUEST_ROM_WINDOW)
        memory[3:6] = b'\xe9\xed\x55'  # Unrelated VGA option ROM entry.
        offset = 0xb000
        memory[offset:offset + 3] = b'\x00\xaa\x00'
        struct.pack_into('<H', memory, offset + 0x18, 0x28)
        memory[offset + 0x28:offset + 0x2c] = b'PCIR'
        struct.pack_into('<HH', memory, offset + 0x2c, 0x1069, 0x0050)
        self.assertEqual(find_guest_rom(memory), 0xcb000)

    def test_rejects_missing_mylex_rom(self):
        with self.assertRaises(RuntimeError):
            find_guest_rom(bytearray(GUEST_ROM_WINDOW))

    def test_decodes_captured_rom_controller_info_request(self):
        captured = ('7f0020100002000096f30900000000000000004040010000'
                    '0000000000000000e0f30900000000000002000000000000'
                    '00000000000000000000000000000000')
        self.assertEqual(decode_lp_mailbox(captured), {
            'id': 0x7f, 'opcode': 0x20, 'control': 0x10,
            'transfer_bytes': 512, 'ioctl': 0x01,
            'sg0_dma': 0x9f3e0, 'sg0_bytes': 512,
        })


if __name__ == '__main__':
    unittest.main()
