# Stock-preserving opcode-0x6f proof hook for the pinned 4.07-0-29 image.
# Metadata enters here after the stock bootstrap has decompressed the program.
# The handler is copied into candidate DRAM, then one RAM dispatch-table word
# is changed. Normal firmware startup resumes at its original entry.
    .text
    .globl _start
    .globl _ping_handler
    .globl _ping_handler_end
_start:
    lda _ping_handler,g0
    lda 0xc0120000,g1
    ldq (g0),g4
    stq g4,(g1)
    ld 16(g0),g4
    st g4,16(g1)
    icctl 2,0,g0
    lda 0xc0120000,g0
    st g0,0xc001f9bc          # opcode 0x6f: table[(0x6f & 0x7f)-1]
    mov 0,g14
    bx 0xc004a2e0           # resume the untouched stock entry

_ping_handler:
    lda 0x017e,g1
    stos g1,0x18(g0)        # request completion status
    lda stock_complete,g1
    bx (g1)                 # tail transfer; g0 request pointer survives
_ping_handler_end:
