# RAM-only control for the attempted post-startup ROM fetch.
# Deliberately contains no branch to flash and no flash data access.
    .text
    .globl _start
_start:
    icctl 2,0,g0              # isolate I-cache invalidation from flash call
    dcctl 2,0,g2              # next dispatch sees restored DMA table word
    lda 0x017f,g1
    stos g1,0x18(g0)
    lda 0xc004bad0,g1
    bx (g1)
