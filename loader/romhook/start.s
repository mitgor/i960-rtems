# Stock-preserving opcode-0x6f proof hook, with the handler resident in flash.
# Metadata enters here after the stock bootstrap has decompressed the program.
# Patch one RAM command-table word and resume the original stock entry.
    .text
    .globl _start
    .globl _ping_handler
    .globl _ping_handler_end
_start:
    lda _ping_handler,g0
    st g0,0xc001f9bc          # opcode 0x6f: table[(0x6f & 0x7f)-1]
    mov 0,g14
    bx 0xc004a2e0           # resume the untouched stock entry

_ping_handler:
    lda 0x017e,g1
    stos g1,0x18(g0)        # request completion status
    lda stock_complete,g1
    bx (g1)                 # tail transfer; g0 request pointer survives
_ping_handler_end:
