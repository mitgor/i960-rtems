/* One complete ISR continuation per registered task. Never share live save areas. */
 .text
 .align 4
 .globl _timer_isr
_timer_isr:
#ifdef I960_DOOM_ENGINE
 mov 1,r10
#endif
 ld __Thread_Executing,r6
 ld _switch_threads,r7
 mov 0,r8
 cmpobe r6,r7,slot_found
 ld _switch_threads+4,r7
 mov 1,r8
 cmpobne r6,r7,slot_bad
slot_found:
#ifdef I960_DOOM_ENGINE
 mov 2,r10
#endif
 lda _switch_active,r9
 shlo 2,r8,r7
 addo r7,r9,r9
 ld (r9),r6
 cmpobne 0,r6,slot_bad
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
 lda 128(r5),sp
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
slot_bad:
#ifdef I960_DOOM_ENGINE
 ld _engine_irq_reject,r6
 cmpobne 0,r6,rejection_recorded
 st r10,_engine_irq_reject+4
 ld __Thread_Executing,r6
 st r6,_engine_irq_reject+8
 ld _switch_active,r6
 st r6,_engine_irq_reject+12
 ld _switch_active+4,r6
 st r6,_engine_irq_reject+16
 st fp,_engine_irq_reject+20
 ld -16(fp),r6
 st r6,_engine_irq_reject+24
 ld -12(fp),r6
 st r6,_engine_irq_reject+28
 ld -8(fp),r6
 st r6,_engine_irq_reject+32
 ld _switch_threads,r6
 st r6,_engine_irq_reject+36
 ld _switch_threads+4,r6
 st r6,_engine_irq_reject+40
 lda 0x31524a49,r6
 st r6,_engine_irq_reject
rejection_recorded:
 ld _engine_irq_reject+44,r6
 addo 1,r6,r6
 st r6,_engine_irq_reject+44
#endif
 ld _switch_fault,r6
 setbit 6,r6,r6
 st r6,_switch_fault
 ret
