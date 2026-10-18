/* Non-returning terminal entries. Hardware records precede the new frame. */
#if ACCELE_TERMINAL
 .text
 .align 4
 .globl _accele_terminal_enter
 .globl _accele_fault_entry
 .globl _accele_nmi_entry
 .globl _accele_raise_fault
_accele_fault_entry:
 mov 1,r8
 lda 0x7d003,g0
 b terminal_common
_accele_nmi_entry:
 mov 2,r8
 lda 0x7d004,g0
 b terminal_common
_accele_terminal_enter:
 mov 0,r8
terminal_common:
 lda 0x1f0000,r5
 modpc 0,r5,r5
 /* Latch before writing any record fields: nested entries preserve evidence. */
 ld 0xc0777060,r4
 cmpobne 0,r4,terminal_nested
 mov 1,r4
 st r4,0xc0777060
 st r8,0xc0777280
 st g0,0xc0777050
 st fp,0xc0777054
 st sp,0xc0777058
 cmpobe 0,r8,terminal_stack
 ld -16(fp),r4
 st r4,0xc0777284
 ld -12(fp),r4
 st r4,0xc0777288
 ld -8(fp),r4
 st r4,0xc077728c
 ld -4(fp),r4
 st r4,0xc0777290
terminal_stack:
 st r5,0xc077704c
 mov 0,r4
 st r4,0xff008504
 st r4,0xff000318
 lda 0xc0778100,sp
 mov 0,g14
 call _accele_terminal_record
terminal_nested:
 b terminal_nested
_accele_raise_fault:
 cmpo 0,0
 faulte
 b terminal_nested
#endif
