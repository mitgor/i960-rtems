#!/usr/bin/env python3
"""Build a custom DAC960PG i960 firmware image that passes DAC960FL.EXE validation.

Strategy (safe): start from the DECODED stock firmware image and only redirect the IBR's
first-instruction pointer at our code, keeping Mylex's known-good PRCB and system tables.
The i960 therefore initialises exactly as stock, then jumps into our code.

Verified facts this relies on (see docs/firmware/FLASHER.md / docs/firmware/REFLASH.md):
  * decoded image = [512-byte MIMG header][payload][10-byte constant trailer]
  * payload is linked so its END maps to 0xFF000000  =>  base = 0xFF000000 - len(payload)
    (stock: payload 0x38000, base 0xFEFC8000)
  * IBR sits at payload offset len(payload) - 0xD0  ->  address 0xFEFFFF30
  * IBR words: 0-3 = PMCON bytes (all 0x00 in stock), 4 = firstIP, 5 = PRCB,
    6 = checksum word, 7 = 0
  * boot checksum rule: sum(IBR words 0..7) == 0 (mod 2^32)  =>  word6 = -(word4+word5)

Usage:
  mkimage.py --stock STOCK.bin --code CODE.bin [--at 0x4d44] --out CUSTOM.img
  mkimage.py --stock STOCK.bin --selftest
"""
import argparse, struct, sys

IBR_FROM_END = 0xD0
HDR, TRAILER = 512, 10
# structures the i960 hardware reads during init - never overwrite these
PRESERVE = {"control table": 0x690, "interrupt table": 0x700, "PRCB": 0xB10,
            "system procedure table": 0x18000}

def split(img):
    if len(img) < HDR + TRAILER:
        sys.exit("image too small")
    if img[:8] != b"MIMGMYLX":
        sys.exit("not a MIMG image (bad magic)")
    return bytearray(img[:HDR]), bytearray(img[HDR:-TRAILER]), bytes(img[-TRAILER:])

def ibr_fields(pay):
    off = len(pay) - IBR_FROM_END
    base = 0xFF000000 - len(pay)
    return off, base, list(struct.unpack_from("<8I", pay, off))

def patch(pay, code=None, at=None, verbose=True):
    off, base, w = ibr_fields(pay)
    if verbose:
        print(f"  payload {len(pay)} (0x{len(pay):x}) base=0x{base:08x} IBR@0x{off:x} -> 0x{base+off:08x}")
        print(f"  stock firstIP=0x{w[4]:08x} PRCB=0x{w[5]:08x} chk=0x{w[6]:08x} sum8=0x{sum(w)&0xFFFFFFFF:08x}")
    if code is not None:
        end = at + len(code)
        if end > off:
            sys.exit(f"code [0x{at:x},0x{end:x}) would reach the IBR at 0x{off:x}")
        for name, a in PRESERVE.items():
            if at <= a < end:
                sys.exit(f"code would overwrite the {name} at 0x{a:x}")
        region = pay[at:end]
        if any(b not in (0x00, 0xFF) for b in region):
            print(f"  WARNING: target 0x{at:x} is not pure filler "
                  f"(overwriting {sum(1 for b in region if b not in (0,255))} non-filler bytes)")
        pay[at:end] = code
        w[4] = base + at                      # firstIP -> our code
        if verbose:
            print(f"  placed {len(code)} B of code at 0x{at:x} (addr 0x{base+at:08x})")
    # keep PMCON (w0..3) and w7 as stock(=0); solve the checksum word
    w[6] = (-(sum(w[:6]) + w[7])) & 0xFFFFFFFF
    struct.pack_into("<8I", pay, off, *w)
    total = sum(struct.unpack_from("<8I", pay, off)) & 0xFFFFFFFF
    if total != 0:
        sys.exit(f"checksum solve failed: sum8=0x{total:08x}")
    if verbose:
        print(f"  new   firstIP=0x{w[4]:08x} PRCB=0x{w[5]:08x} chk=0x{w[6]:08x} sum8=0x{total:08x} OK")
    return pay

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stock", required=True)
    p.add_argument("--code"); p.add_argument("--out")
    p.add_argument("--at", default="0x4d44")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    img = open(a.stock, "rb").read()
    hdr, pay, tr = split(img)

    if a.selftest:
        print("[selftest] round-trip with no code change (must reproduce stock byte-for-byte):")
        out = hdr + patch(bytearray(pay), None, None) + tr
        print("  identical to stock:", "PASS" if out == img else "FAIL")
        print(f"  header: len field=0x{struct.unpack_from('<I',hdr,8)[0]:x} "
              f"(filesize-10=0x{len(img)-10:x}) type=0x{hdr[0x0d]:02x} "
              f"ver={hdr[0x18:0x40].split(bytes(1))[0].decode('latin1','replace')!r}")
        print("  trailer:", tr.hex(' '))
        return
    if not (a.code and a.out):
        sys.exit("need --code and --out (or --selftest)")
    code = open(a.code, "rb").read()
    print("[build] custom image:")
    pay = patch(pay, code, int(a.at, 0))
    out = bytes(hdr) + bytes(pay) + tr
    assert len(out) == len(img), "size changed - flasher checks expected file size"
    open(a.out, "wb").write(out)
    print(f"  wrote {a.out} ({len(out)} B, identical size to stock) "
          f"type=0x{hdr[0x0d]:02x} len_field=0x{struct.unpack_from('<I',hdr,8)[0]:x}")

if __name__ == "__main__":
    main()
