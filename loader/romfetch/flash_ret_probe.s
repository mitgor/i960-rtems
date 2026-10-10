# One-shot post-startup flash instruction-fetch probe.
# FEFB022C is the physical 512 KiB image address of a pinned stock RET.
# The archived firmware disassembly labeled these bytes FEFC822C, which is
# not their address in the card's full image. No target data accesses.
    .text
    .globl _start
_start:
    icctl 2,0,g0
    callx 0xfefb022c
    dcctl 2,0,g2
    lda 0x017f,g1
    stos g1,0x18(g0)
    lda 0xc004bad0,g1
    bx (g1)
