# Historical failed attempt only: FEFC8208 is the archived disassembly label,
# not the physical location of those bytes in the 512 KiB card image. This
# callback timed out in attempt 2. Do not use it for another live probe.
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
