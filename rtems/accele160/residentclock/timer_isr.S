/* Retain the hardware frame on the owned entry stack; use a second grant page
 * for C ISR execution. Save all globals and writable TC modes before calls. */
 .text
 .align 4
 .globl _timer_isr
_timer_isr:
 ld _irq_active,r6
 cmpobne 0,r6,irq_reentry
 mov 1,r6
 st r6,_irq_active
 mov sp,r4
 lda _irq_owned_area+64,r5
 stq g0,(r5)
 stq g4,16(r5)
 stq g8,32(r5)
 stq g12,48(r5)
 modtc 0,0,r6
 st r6,64(r5)
 lda _irq_owned_area+192,sp
 mov 0,g14
 mov fp,g0
 call _timer_interrupt
 ld 64(r5),r6
 lda 0xfe,r7
 modtc r7,r6,r7
 mov 0,r6
 st r6,_irq_active
 ldq (r5),g0
 ldq 16(r5),g4
 ldq 32(r5),g8
 ldq 48(r5),g12
 mov r4,sp
 ret
irq_reentry:
 mov 1,r6
 st r6,_irq_fault
 ret

 .section .irqstack,"aw",@nobits
 .align 4
 .globl _irq_owned_area
_irq_owned_area:
 .space 4096
