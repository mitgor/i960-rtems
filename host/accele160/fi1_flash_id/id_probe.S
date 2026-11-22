/* FI1 operation-13 returning Intel 28F008S3 identification probe.
 * Only FF, 90, FF are written to the flash command port. No erase, program,
 * lock or board-gate command. Record is written beside the operation-13
 * control report, which is host-visible on the BAR mapping after return.
 */
 .text
 .globl _start
_start:
 lda 0x314e5552,r4
 st r4,(g0)
 st g1,4(g0)
 lda 0x31454e4f,r4
 st r4,8(g0)
 lda 0xfef00000,r8
 lda 0xff,r4
 stob r4,(r8)
 syncf
 lda 0x90,r4
 stob r4,(r8)
 syncf
 ldob (r8),r5
 ldob 1(r8),r6
 ldob 3(r8),r7
 mov 0,r9
 mov 0,r10
 mov 1,r14
 lda 0x10000,r11
 mov r8,r12
locks:
 ldob 2(r12),r13
 cmpobe 0,r13,next
 or r9,r14,r9
next:
 addo r11,r12,r12
 shlo 1,r14,r14
 addo 1,r10,r10
 cmpobne 16,r10,locks
 lda 0xff,r4
 stob r4,(r8)
 syncf
 ldob (r8),r15
 lda 0xc000fa60,r12
 lda 0x32444953,r4
 st r4,(r12)
 st r5,4(r12)
 st r6,8(r12)
 st r7,12(r12)
 st r9,16(r12)
 st r15,20(r12)
 syncf
 mov 0,r4
 st r4,24(g0)
 mov 0,g0
 ret
