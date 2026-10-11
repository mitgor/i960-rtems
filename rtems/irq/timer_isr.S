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
