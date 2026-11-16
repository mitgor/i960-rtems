/* Synthetic Jx timer interrupt: run a one-shot timer and return to spin. */
 .text
 .globl _start
_start:
 mov 0,g14
 lda 0xff000300,g0
 mov 3,g1
 st g1,(g0)
 st g1,4(g0)
 mov 2,g1
 st g1,8(g0)
 lda 0xff008504,g0
 lda 0x1000,g1
 st g1,(g0)
 inten
spin:
 b spin

 .org 0x100
handler:
 call nested
 ret

 .org 0x120
nested:
 lda 0xc0001f00,g0
 ld (g0),g1
 addo 1,g1,g1
 st g1,(g0)
 ret
