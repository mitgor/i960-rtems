#!/usr/bin/env python3
"""Decode Fujitsu GlobalFlash-encoded DAC960 payloads (.img/.exe).

The encoding is a deterministic per-byte transform (NOT compression):
    decoded = PERM(stored XOR 0xC3)
where PERM swaps bit i with bit i^6 (bit0<->bit6, bit1<->bit7, bit2<->bit4,
bit3<->bit5) and is its own inverse. It coincides with plain XOR 0xC3 only on
permutation-invariant bytes (0x00,0xff,0x55,0xaa,0x5a,0xc3,0x3c...), which is why
whole-file XOR 0xC3 never revealed strings.

The .IMG files carry a 512-byte container header ("MIMGMYLX" + "Ver ... Released
on ...") before the raw image; DAC960FL.EXE has no header (encoded from byte 0).

Usage: globalflash_decode.py <in> <out> [--strip-header]
Verified: decodes DAC960FL.EXE -> 'MZ' DOS exe; BGJ41041.IMG[512:] -> 55AA option ROM.
"""
import sys
def _perm(b):
    r = 0
    for i in range(8):
        if (b >> i) & 1:
            r |= 1 << (i ^ 6)
    return r
TABLE = bytes(_perm(x ^ 0xC3) for x in range(256))  # stored byte -> decoded byte
def decode(data: bytes) -> bytes:
    return data.translate(TABLE)
if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--strip-header"]
    strip = "--strip-header" in sys.argv
    d = decode(open(args[0], "rb").read())
    if strip:
        d = d[512:]
    open(args[1], "wb").write(d)
    print(f"decoded {args[0]} -> {args[1]} ({len(d)} bytes), head={d[:4].hex()}")
