/* Slot 0 remains live across the RTEMS task run. Slot 1 handles task ticks. */
 .text
 .align 4
 .globl _timer_isr
_timer_isr:
 ld _resident_phase,r8
 cmpobe 0,r8,phase_ok
 cmpobe 1,r8,phase_ok
 b irq_bad
phase_ok:
 lda _irq_active,r9
 shlo 2,r8,r7
 addo r7,r9,r9
 ld (r9),r6
 cmpobne 0,r6,irq_bad
 mov 1,r6
 st r6,(r9)
 mov sp,r4
 lda _irq_owned_area+64,r5
 shlo 13,r8,r7
 addo r7,r5,r5
 stq g0,(r5)
 stq g4,16(r5)
 stq g8,32(r5)
 stq g12,48(r5)
 modtc 0,0,r6
 st r6,64(r5)
 lda 192(r5),sp
 mov 0,g14
 mov fp,g0
 mov r8,g1
 call _timer_interrupt
 ld 64(r5),r6
 lda 0xfe,r7
 modtc r7,r6,r7
 mov 0,r6
 st r6,(r9)
 ldq (r5),g0
 ldq 16(r5),g4
 ldq 32(r5),g8
 ldq 48(r5),g12
 mov r4,sp
 ret
irq_bad:
 ld _irq_fault,r6
 setbit 6,r6,r6
 st r6,_irq_fault
 ret

 .section .irqstack,"aw",@nobits
 .align 4
 .globl _irq_owned_area
_irq_owned_area:
 /* Keep slot 1 on odd grant page 17; page 16 is an untouched gap. */
 .space 12288
