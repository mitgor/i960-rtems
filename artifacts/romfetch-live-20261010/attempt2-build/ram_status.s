# RAM-only control callback. The RP/Jx core does not snoop DMA writes.
# Its write-through D-cache can be invalidated before the next dispatch.
    .text
    .globl _start
_start:
    dcctl 2,0,g2
    lda 0x017e,g1
    stos g1,0x18(g0)
    lda 0xc004bad0,g1
    bx (g1)
