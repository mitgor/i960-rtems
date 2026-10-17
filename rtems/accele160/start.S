    .section .entry,"ax"
    .globl _start
_start:
    mov g0,r4
    mov g1,r6
    lda _escape_context,g3
    modpc 0,0,g2
    st g2,8(g3)
    stq g8,12(g3)
    stq g12,28(g3)
    stl pfp,(g3)
    lda 0x1f0000,g0
    modpc 0,g0,g0
    mov g0,r5
    mov r4,g0
    mov r6,g1
    call _bounded_main
    mov g0,r4
    lda 0x1f0000,g1
    mov r5,g2
    modpc 0,g1,g2
    lda _escape_context,g3
    ldq 12(g3),g8
    ldq 28(g3),g12
    ldl (g3),pfp
    mov r4,g0
    ret

    .text
    .globl _bounded_escape
_bounded_escape:
    lda _escape_context,g1
    flushreg
    lda 0x1f0000,g2
    ld 8(g1),g3
    ldq 28(g1),g12
    ldl (g1),pfp
    ldq 12(g1),g8
    modpc 0,g2,g3
    ret
    .data
    .align 4
_escape_context:
    .space 48
