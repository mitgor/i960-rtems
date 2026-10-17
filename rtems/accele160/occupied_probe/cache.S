 .text
 .globl _lease_invalidate_dcache
_lease_invalidate_dcache:
 dcctl 2,0,r4
 ret
