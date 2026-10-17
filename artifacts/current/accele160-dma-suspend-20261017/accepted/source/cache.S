 .text
 .globl _timer_invalidate_dcache
_timer_invalidate_dcache:
 dcctl 2,0,r4
 ret
