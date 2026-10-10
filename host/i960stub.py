#!/usr/bin/env python3
"""Hand-assembled i960 proof-of-life stub for the DAC960PG.

Writes a magic word to the i960 Messaging Unit's Outbound Message Register 0
(OMR0, i960 local bus address 0x00001318), then spins forever.

The host reads that same register at BAR0 + 0x18 (physical 0xee000018 on this box),
because the card's PG register window maps i960 local 0x1300+X -> BAR0+X. Verified by
the Linux DAC960 PG map agreeing on IDR(0x1320->+0x20), ODR(0x132C->+0x2C) and
OIMR(0x1334->+0x34). MU registers are internal MMRs, so this needs NO memory-controller
or DRAM initialisation - it is safe as the very first instruction after reset.

Instruction encoding cross-checked against our own verified i960 interpreter (host/emu.c).
"""
import struct, sys
OMR0  = 0x00001318
MAGIC = 0xC0FFEE01
LDA, ST, G0 = 0x8c, 0x92, 16        # regs 0-15 = locals r0-r15; 16-31 = globals g0-g15

def mem_b12(op, reg, disp):          # MEM format, MEMB mode 12: two-word absolute disp
    return struct.pack("<II", (op << 24) | ((reg & 0x1f) << 19) | (12 << 10), disp)

def build(magic=MAGIC, target=OMR0):
    return (mem_b12(LDA, G0, magic)          # lda  magic, g0
          + mem_b12(ST,  G0, target)         # st   g0, target
          + struct.pack("<I", 0x08000000))   # b .      (spin)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "i960stub.bin"
    code = build()
    open(out, "wb").write(code)
    print(f"wrote {out} ({len(code)} B): {code.hex(' ')}")
    print(f"  lda 0x{MAGIC:08X}, g0 ; st g0, 0x{OMR0:08X} (OMR0) ; b .")
    print(f"  host verifies:  sudo ./myflash probe 0xee000000   -> BAR0+0x18 == 0x{MAGIC:08X}")
