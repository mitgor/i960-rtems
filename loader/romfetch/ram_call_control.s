# Validate callx/ret from the same uploaded RAM region, without flash access.
    .text
    .globl _start
_start:
    icctl 2,0,g0
    callx local_return
    dcctl 2,0,g2
    lda 0x017f,g1
    stos g1,0x18(g0)
    lda 0xc004bad0,g1
    bx (g1)
local_return:
    ret
