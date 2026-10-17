/* Four owned ISR continuations: controller, two workers, and RTEMS idle.
 * A dispatch in C may suspend here, so no live save area is shared. */
 .text
 .align 4
 .globl _timer_isr
_timer_isr:
 mov rip,r6
 lda _engine_irq_rip,r7
 st r6,(r7)
 ld __Thread_Executing,r6
 ld _switch_threads,r7
 mov 0,r8
 cmpobe r6,r7,slot_found
 ld _switch_threads+4,r7
 mov 1,r8
 cmpobe r6,r7,slot_found
 ld _switch_threads+8,r7
 mov 2,r8
 cmpobe r6,r7,slot_found
 ld _switch_threads+12,r7
 mov 3,r8
 cmpobne r6,r7,slot_bad
slot_found:
 lda _switch_active,r9
 shlo 2,r8,r7
 addo r7,r9,r9
 ld (r9),r6
 cmpobne 0,r6,slot_nested
 mov 1,r6
 st r6,(r9)
 mov sp,r4
 lda _switch_irq_areas+64,r5
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
 mov r8,g0
 mov fp,g1
 call _switch_irq_enter
 call _switch_irq_body
 mov r8,g0
 mov fp,g1
 call _switch_irq_leave
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
/* RTEMS lowers the interrupt level inside _Thread_Dispatch before this
 * owner's earlier ISR continuation has unwound. Reentry must not overwrite
 * that owner's save area or dispatch again. The interrupt is counted and
 * returned without touching the interrupted globals or RTEMS scheduler. */
slot_nested:
 ld _switch_nested_count,r6
 addo 1,r6,r6
 st r6,_switch_nested_count
 ret
slot_bad:
 st r6,_switch_unknown_thread
 mov rip,r7
 st r7,_switch_unknown_rip
 ld _switch_fault,r6
 setbit 6,r6,r6
 st r6,_switch_fault
 ret

 .section .irqstack,"aw",@nobits
 .align 4
 .globl _switch_irq_areas
_switch_irq_areas:
 .space 32768
