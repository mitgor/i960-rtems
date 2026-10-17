/* Operation-13 entry: use a grant-owned call stack and return to firmware. */
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
 mov sp,r5
 st r5,0xc000fa60
 lda 0x1f0000,g0
 modpc 0,g0,g0
 mov g0,r5
 lda 0xc0712fc0,sp
 mov r4,g0
 mov r6,g1
 call _bounded_main
 mov g0,r4
 mov sp,r6
 st r6,0xc000fa68
 lda _escape_context,g3
 ldq 12(g3),g8
 ldq 28(g3),g12
 ldl (g3),pfp
 mov sp,r6
 st r6,0xc000fa6c
 mov r4,g0
 /* A successful arm must return to firmware at priority 0 so timer 1 can
  * enforce its lease. The ISR restores the saved firmware priority in the
  * interrupted frame when it stops the timer. Failed admission keeps the
  * original priority and never leaves a timer armed. */
 cmpobne 0,r4,restore_original_priority
 lda 0x1f0000,g1
 mov 0,g2
 modpc 0,g1,g2
 ret
restore_original_priority:
 lda 0x1f0000,g1
 mov r5,g2
 modpc 0,g1,g2
 ret

 .text
 .globl _bounded_escape
_bounded_escape:
 st g0,0xc000fa7c
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
 .globl _escape_context
_escape_context:
 .space 48
