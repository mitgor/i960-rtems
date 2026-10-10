/* Returning call gate, linked in the extra firmware-owned staging block. */
    .text
    .globl _start
_start:
    icctl 2,0,g2
    mov g0,r4
    dcctl 2,0,g2
    lda 0x12345678,g0       /* ARG_LITERAL: patched by host */
    lda 0xc0f2c000,g1       /* ENTRY_LITERAL: checked offset within uploaded bytes */
    mov 0,g14
    callx (g1)
    lda 0xc1fac280,g1
    st g0,(g1)
    lda 0x52554e31,g2       /* RUN1 completion marker */
    st g2,4(g1)
    lda 0xfefe001c,g1
    st g1,0xc001f9bc       /* self-disarm before reporting completion */
    dcctl 2,0,g2
    mov r4,g0
    lda 0x017f,g1
    stos g1,0x18(g0)
    lda 0xc004bad0,g1
    bx (g1)
