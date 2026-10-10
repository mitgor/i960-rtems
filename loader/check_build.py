#!/usr/bin/env python3
"""Validate target ELF layout and stock/link-address agreement without hardware."""
import argparse
import pathlib
import struct
import sys

STOCK_SIZE = 0x38000
FLASH_END = 0xFF000000
DEFAULT_OFFSET = 0x4D44
PAYLOAD_BASE, PAYLOAD_END = 0x200, 0x400


def elf_layout(data):
    if len(data) < 52 or data[:6] != b'\x7fELF\x01\x01':
        raise ValueError('expected a little-endian ELF32 target image')
    entry = struct.unpack_from('<I', data, 24)[0]
    shoff = struct.unpack_from('<I', data, 32)[0]
    shsize, shnum, names_index = struct.unpack_from('<HHH', data, 46)
    if shsize != 40 or not shnum or names_index >= shnum or shoff + shsize * shnum > len(data):
        raise ValueError('invalid ELF section table')
    headers = [struct.unpack_from('<10I', data, shoff + i * shsize) for i in range(shnum)]
    names = headers[names_index]
    if names[4] + names[5] > len(data):
        raise ValueError('invalid ELF section names')
    strings = data[names[4]:names[4] + names[5]]
    sections = []
    for h in headers:
        name_off, kind, flags, address, offset, size = h[:6]
        if name_off >= len(strings):
            raise ValueError('invalid section name offset')
        name = strings[name_off:].split(b'\0', 1)[0].decode('ascii')
        if kind != 8 and offset + size > len(data):
            raise ValueError('section extends beyond ELF file')
        sections.append((name, kind, flags, address, offset, size))
    return entry, sections


def validate_elf(data, binary, base, limit):
    entry, sections = elf_layout(data)
    if entry != base or base & 3:
        raise ValueError(f'entry 0x{entry:x} differs from binary placement 0x{base:x}')
    if not binary or base + len(binary) > limit:
        raise ValueError('binary is empty or exceeds its allowed region')
    allocated = [s for s in sections if s[2] & 2 and s[5]]
    if not allocated:
        raise ValueError('no allocated target sections')
    if not any(s[0] == '.text' and s[3] == base and s[2] & 4 for s in allocated):
        raise ValueError('entry must begin executable .text')
    rebuilt = bytearray(len(binary))
    occupied = set()
    for name, kind, flags, address, offset, size in allocated:
        if kind == 8 or flags & 1:
            raise ValueError(f'{name}: writable storage/BSS has no startup initialization')
        if name not in ('.text', '.rodata'):
            raise ValueError(f'unexpected allocated section {name}')
        start = address - base
        if start < 0 or start + size > len(binary):
            raise ValueError(f'{name}: section outside flat binary')
        positions = set(range(start, start + size))
        if occupied & positions:
            raise ValueError('overlapping allocated sections')
        occupied |= positions
        rebuilt[start:start + size] = data[offset:offset + size]
    if len(binary) != max(s[3] + s[5] for s in allocated) - base:
        raise ValueError('binary size does not match allocated ELF sections')
    if rebuilt != binary:
        raise ValueError('flat binary contents differ from ELF')


def validate_stock(data, entry, at):
    if len(data) != 512 + STOCK_SIZE + 10 or data[:8] != b'MIMGMYLX':
        raise ValueError('loader requires the known 0x38000-byte decoded stock payload')
    if struct.unpack_from('<I', data, 8)[0] != len(data) - 10:
        raise ValueError('stock header length does not match file')
    base = FLASH_END - STOCK_SIZE
    if at != DEFAULT_OFFSET or entry != base + at:
        raise ValueError('stock placement and linked loader entry disagree')
    words = struct.unpack_from('<8I', data, 512 + STOCK_SIZE - 0xD0)
    if sum(words) & 0xFFFFFFFF or words[5] != base + 0xB10:
        raise ValueError('stock IBR checksum or expected PRCB pointer differs')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf', required=True)
    p.add_argument('--binary', required=True)
    p.add_argument('--kind', choices=('loader', 'payload'), required=True)
    p.add_argument('--stock')
    a = p.parse_args()
    try:
        elf = pathlib.Path(a.elf).read_bytes()
        binary = pathlib.Path(a.binary).read_bytes()
        if a.kind == 'loader':
            base = FLASH_END - STOCK_SIZE + DEFAULT_OFFSET
            limit = FLASH_END - STOCK_SIZE + 0x18000 # next preserved table
        else:
            base, limit = PAYLOAD_BASE, PAYLOAD_END
        validate_elf(elf, binary, base, limit)
        if a.stock:
            if a.kind != 'loader':
                raise ValueError('--stock is only valid for loader validation')
            validate_stock(pathlib.Path(a.stock).read_bytes(), base, DEFAULT_OFFSET)
    except (OSError, ValueError, struct.error, UnicodeError) as e:
        p.exit(1, f'build validation failed: {e}\n')
    print(f'{a.kind} layout validated: {len(binary)} bytes at 0x{base:08x}')


if __name__ == '__main__':
    main()
