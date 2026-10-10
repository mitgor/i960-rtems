/* Intel i960 setbit (583): dst = src | (1 << (bitpos % 32)). */
    .text
    .globl _main
_main:
    setbit 8,0,g1
    lda 33,g0
    setbit g0,g1,g1
    setbit 31,g1,g1
    setbit 0,g1,g1
    st g1,0x00090788
    mov 1,g0
    st g0,0x0009078c
    ret
