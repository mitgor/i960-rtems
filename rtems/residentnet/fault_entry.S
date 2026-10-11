#ifdef I960_FAULT_OWNER
 .text
 .align 4
 .globl _exclusive_fault_entry
 .globl _exclusive_nmi_entry
 .globl _exclusive_synthetic_nmi
 .globl _exclusive_abort
 .globl _exclusive_raise_fault
_exclusive_fault_entry:
 mov 1,r8
 b exclusive_trap_common
_exclusive_nmi_entry:
 mov 2,r8
 b exclusive_trap_common
_exclusive_synthetic_nmi:
 mov 3,r8
 b exclusive_trap_common
_exclusive_abort:
 mov 4,r8
exclusive_trap_common:
 ld _exclusive_trap_active,r9
 cmpobne 0,r9,exclusive_trap_nested
 mov 1,r9
 st r9,_exclusive_trap_active
 st r8,_exclusive_trap_words+8
 st fp,_exclusive_trap_words+12
 /* Synthetic local call has no hardware fault/interrupt record. */
 cmpobe 3,r8,exclusive_trap_stack
 cmpobe 4,r8,exclusive_trap_stack
 ld -16(fp),r9
 st r9,_exclusive_trap_words+16
 ld -12(fp),r9
 st r9,_exclusive_trap_words+20
 ld -8(fp),r9
 st r9,_exclusive_trap_words+24
 ld -4(fp),r9
 st r9,_exclusive_trap_words+28
exclusive_trap_stack:
 lda 0x1f0000,r9
 modpc 0,r9,r9
 mov 0,r9
 st r9,0xff008504
 lda _exclusive_exception_area+1024,sp
 mov 0,g14
 call _exclusive_trap_park
exclusive_trap_nested:
 b exclusive_trap_nested
_exclusive_raise_fault:
 cmpo 0,0
 faulte
 b exclusive_trap_nested
#endif
