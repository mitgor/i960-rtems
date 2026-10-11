#ifdef I960_OWNED_STACK
/* Owned C stack; retain the original hardware frame and return through it.
 * r4/r5 live in this ISR's register frame and survive calls/window spills. */
 .text
 .align 4
 .globl _timer_isr
_timer_isr:
 ld _irq_owned_active,r6
 cmpobne 0,r6,owned_reentry
 mov 1,r6
 st r6,_irq_owned_active
 mov sp,r4
 lda _irq_owned_area+64,r5
 stq g0,(r5)
 stq g4,16(r5)
 stq g8,32(r5)
 stq g12,48(r5)
 modtc 0,0,r6
 st r6,64(r5)
 ld -16(fp),r6
 st r6,68(r5)
 ld -12(fp),r6
 st r6,72(r5)
 ld -8(fp),r6
 st r6,76(r5)
 lda _irq_owned_area+192,sp
 mov 0,g14
 mov fp,g0
 call _irq_owned_enter
 call _timer_interrupt
 call _irq_owned_leave
 ld 64(r5),r6
 lda 0xfe,r7
 modtc r7,r6,r7
 mov 0,r6
 st r6,_irq_owned_active
 ldq (r5),g0
 ldq 16(r5),g4
 ldq 32(r5),g8
 ldq 48(r5),g12
 mov r4,sp
 ret
owned_reentry:
 ld _irq_owned_fault,r6
 setbit 6,r6,r6
 st r6,_irq_owned_fault
 ret
#else
/* Dedicated, non-nesting timer-1 ISR. The processor owns the interrupt record.
 * Save every global on this invocation's stack, never a shared global slot. */
 .text
 .align 4
 .globl _timer_isr
_timer_isr:
 mov sp,r4
 lda 64(sp),sp
 stq g0,(r4)
 stq g4,16(r4)
 stq g8,32(r4)
 stq g12,48(r4)
 mov 0,g14
 call _timer_interrupt
 ldq (r4),g0
 ldq 16(r4),g4
 ldq 32(r4),g8
 ldq 48(r4),g12
 ret
#endif
