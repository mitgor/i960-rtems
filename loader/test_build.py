"""Regression tests for image/layout gates and CLI validation before PCI access."""
import pathlib
import struct
import subprocess
import unittest
from check_build import validate_elf, validate_stock, FLASH_END, STOCK_SIZE, DEFAULT_OFFSET

HERE = pathlib.Path(__file__).resolve().parent


def elf(base=0x200, writable=False, bss=False):
    # Minimal ELF32 with null, .text, and section-name string table sections.
    names = b'\0.text\0.shstrtab\0'
    data = bytearray(256)
    data[:16] = b'\x7fELF\x01\x01\x01' + bytes(9)
    struct.pack_into('<HHIIIIIHHHHHH', data, 16, 2, 19, 1, base, 0, 128, 0, 52, 0, 0, 40, 3, 2)
    data[52:56] = b'\x01\x02\x03\x04'
    data[64:64 + len(names)] = names
    struct.pack_into('<10I', data, 168, 1, 8 if bss else 1, 6 | int(writable), base, 52, 4, 0, 0, 4, 0)
    struct.pack_into('<10I', data, 208, 7, 3, 0, 0, 64, len(names), 0, 0, 1, 0)
    return data


def stock():
    data = bytearray(512 + STOCK_SIZE + 10)
    data[:8] = b'MIMGMYLX'
    struct.pack_into('<I', data, 8, len(data) - 10)
    base = FLASH_END - STOCK_SIZE
    prcb, entry = base + 0xB10, base + DEFAULT_OFFSET
    words = [0, 0, 0, 0, entry, prcb, (-(entry + prcb)) & 0xffffffff, 0]
    struct.pack_into('<8I', data, 512 + STOCK_SIZE - 0xD0, *words)
    return data


class BuildTests(unittest.TestCase):
    def test_valid_layout(self):
        validate_elf(elf(), b'\x01\x02\x03\x04', 0x200, 0x400)

    def test_bad_layouts(self):
        for data, binary, base, limit in [
            (elf(), b'\x01\x02\x03\x04', 0x204, 0x400),
            (elf(writable=True), b'\x01\x02\x03\x04', 0x200, 0x400),
            (elf(bss=True), b'\x01\x02\x03\x04', 0x200, 0x400),
            (elf(), b'\x01\x02\x03\x05', 0x200, 0x400),
            (elf(), b'\x01\x02\x03\x04', 0x200, 0x202),
            (elf(), b'', 0x200, 0x400),
            (elf()[:180], b'\x01\x02\x03\x04', 0x200, 0x400),
        ]:
            with self.subTest(base=base, limit=limit, length=len(data)):
                with self.assertRaises(ValueError):
                    validate_elf(data, binary, base, limit)

    def test_stock(self):
        base = FLASH_END - STOCK_SIZE + DEFAULT_OFFSET
        validate_stock(stock(), base, DEFAULT_OFFSET)
        with self.assertRaises(ValueError):
            validate_stock(stock(), base + 4, DEFAULT_OFFSET)
        with self.assertRaises(ValueError):
            validate_stock(stock()[:-4], base, DEFAULT_OFFSET)
        damaged = stock()
        damaged[512 + STOCK_SIZE - 0xD0 + 24] ^= 1
        with self.assertRaises(ValueError):
            validate_stock(damaged, base, DEFAULT_OFFSET)

    def test_cli_rejects_before_hardware_access(self):
        for args in [[], ['0', 'unknown'], ['0', 'ping', 'extra'],
                     ['0', 'read', '0x100000000'], ['0', 'read', '0x201'],
                     ['0', 'go', '0x40'], ['0', 'load', '0x200'],
                     ['0', 'reg-read', '0x1318'], ['0', 'read', '512garbage'],
                     ['0', 'reg-write', '0x1000', '-1']]:
            with self.subTest(args=args):
                result = subprocess.run([str(HERE / 'loadctl'), *args], capture_output=True)
                self.assertEqual(result.returncode, 2, result.stderr.decode())
                self.assertNotIn(b'PCI sysfs', result.stderr)


if __name__ == '__main__':
    unittest.main()
