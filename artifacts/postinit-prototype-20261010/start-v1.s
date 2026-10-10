# Experimental entry after stock decompression. No reset-vector modification.
# Patch RAM only: replace call at C004E844 with an absolute branch after the
# stock ATU initialization and EBCR store, before the enumeration wait loop.
    .text
    .globl _start
_start:
    intdis
    lda 0x84003000,g0          # bx absolute instruction word
    st g0,0xc004e844
    lda _postinit,g0
    st g0,0xc004e848
    icctl 2,0,g0
    mov 0,g14
    bx 0xc004a2e0             # original firmware entry; existing stack retained
_postinit:
    intdis
    dcctl 0,0,g0              # disable write-through Rx D-cache
    icctl 2,0,g0
    mov 0,g14
    call _loader_main         # inherit initialized external-memory call stack
.Lhalt:
    b .Lhalt
