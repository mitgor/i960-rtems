/* RAM-only AcceleRAID owned-stack and cooperative STOP/finite-poll proof.
 * Operation 13 calls _start with g0=fa20 report, g1=nonce, g2=manifest.
 * The whole 2-page image is host-pinned and checked by the retained handler.
 * No timer, interrupt vector or firmware stack is borrowed after the switch.
 */
 .text
 .globl _start
_start:
 lda saved_pair,g3
 stl pfp,(g3)
 stq g8,8(g3)
 stq g12,24(g3)
 mov sp,r5
 st r5,0xc000fa60
 lda 0xc0711f80,sp
 call owned_worker
 mov g0,r4
 mov sp,r5
 st r5,0xc000fa68
 lda saved_pair,g3
 ldq 8(g3),g8
 ldq 24(g3),g12
 ldl (g3),pfp
 mov sp,r5
 st r5,0xc000fa6c
 mov r4,g0
 ret

owned_worker:
 mov sp,r5
 st r5,0xc000fa64
 st r5,-4(sp)
 ld 0xc000fa40,r5
 lda 0x3145534c,r6
 cmpobne r5,r6,worker_reject
 ld 0xc000fa44,r5
 cmpobne r5,g1,worker_reject
 ld 0xc000fa48,r5
 lda 1,r6
 cmpobne r5,r6,worker_reject
 ld 0xc000fa4c,r5
 cmpibne 0,r5,worker_reject
 lda 0x59444152,r5
 st r5,0xc000fa50
 lda 2000000,r12
lease_poll:
 dcctl 2,0,r11
 ld 0xc000fa4c,r5
 lda 0x504f5453,r6
 cmpobe r5,r6,lease_stop
 subo 1,r12,r12
 cmpibne 0,r12,lease_poll
 lda 0x454d4954,r5
 st r5,0xc000fa50
 st r5,24(g0)
 b worker_report
lease_stop:
 ld 0xc000fa40,r5
 lda 0x3145534c,r6
 cmpobne r5,r6,worker_reject
 ld 0xc000fa44,r5
 cmpobne r5,g1,worker_reject
 ld 0xc000fa48,r5
 lda 1,r6
 cmpobne r5,r6,worker_reject
 lda 0x214b4341,r5
 st r5,0xc000fa54
 st g1,0xc000fa58
 lda 1,r6
 st r6,0xc000fa5c
 lda 0x504f5453,r5
 st r5,24(g0)
worker_report:
 lda 0x314e5552,r5
 st r5,(g0)
 st g1,4(g0)
 lda 0x31454e4f,r5
 st r5,8(g0)
 mov 0,g0
 ret
worker_reject:
 lda 1,g0
 ret

 .align 4
saved_pair:
 .space 40
