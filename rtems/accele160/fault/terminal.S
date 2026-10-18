/* Software fatal entry only. This is not a hardware fault/NMI vector. */
#if ACCELE_TERMINAL
 .text
 .align 4
 .globl _accele_terminal_enter
_accele_terminal_enter:
 lda 0x1f0000,r4
 modpc 0,r4,r4
 st r4,0xc077704c
 st g0,0xc0777050
 st fp,0xc0777054
 st sp,0xc0777058
 ld 0xc0777060,r4
 cmpobne 0,r4,terminal_nested
 mov 1,r4
 st r4,0xc0777060
 mov 0,r4
 st r4,0xff008504
 st r4,0xff000318
 lda 0xc0778100,sp
 mov 0,g14
 call _accele_terminal_record
terminal_nested:
 b terminal_nested
#endif
