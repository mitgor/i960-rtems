# One-shot request handler for a reversible live RAM-table experiment.
# A distinctive completion proves the core returned from a stock flash
# routine after normal startup. FEFC8208 only reads C0000000 in a short
# count-controlled loop and returns; the host sets the count to one here.
    .text
    .globl _start
_start:
    mov g0,r4                 # retain request pointer across the call frame
    icctl 2,0,g0              # invalidate prior bootstrap flash I-cache lines
    mov 1,g0                  # bounded single iteration of stock delay
    callx 0xfefc8208          # target is in the pinned stock flash bootstrap
    mov r4,g0
    dcctl 2,0,g2              # next dispatch sees any DMA-restored table word
    lda 0x017f,g1
    stos g1,0x18(g0)
    lda 0xc004bad0,g1
    bx (g1)                   # stock mailbox completion
