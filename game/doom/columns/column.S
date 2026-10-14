/* i960 register-window ABI: g0 is the job pointer; only local r3-r15
 * are modified. No calls, interrupt masking, or self-modifying code.
 * Job offsets are checked by the build's 32-bit ABI assertions. */
.text
.align 4
.globl _doom_column_asm
_doom_column_asm:
 ld (g0),r3
 ld 4(g0),r4
 ld 8(g0),r5
 ld 12(g0),r6
 ld 16(g0),r7
 ld 20(g0),r8
 ld 24(g0),r9
 ld 28(g0),r10
 cmpobe 0,r9,Ldone
 cmpibl 0,r10,Lpost
 lda 127,r14
 cmpobne 0,r4,Lwall2
Lwall1:
 shro 16,r7,r11
 and r14,r11,r11
 ldob (r5)[r11],r12
 ldob (r6)[r12],r12
 stob r12,(r3)
 lda 320(r3),r3
 addo r8,r7,r7
 subo 1,r9,r9
 cmpobne 0,r9,Lwall1
 ret
Lwall2:
 shro 16,r7,r11
 and r14,r11,r11
 ldob (r5)[r11],r12
 ldob (r6)[r12],r12
 stob r12,(r3)
 stob r12,(r4)
 lda 320(r3),r3
 lda 320(r4),r4
 addo r8,r7,r7
 subo 1,r9,r9
 cmpobne 0,r9,Lwall2
 ret
Lpost:
 subo 1,r10,r14
 cmpobne 0,r4,Lpost2
Lpost1:
 shri 16,r7,r11
 cmpibg 0,r11,Lzero1
 cmpible r10,r11,Llast1
 b Lload1
Lzero1:
 mov 0,r11
 b Lload1
Llast1:
 mov r14,r11
Lload1:
 ldob (r5)[r11],r12
 ldob (r6)[r12],r12
 stob r12,(r3)
 lda 320(r3),r3
 addo r8,r7,r7
 subo 1,r9,r9
 cmpobne 0,r9,Lpost1
 ret
Lpost2:
 shri 16,r7,r11
 cmpibg 0,r11,Lzero2
 cmpible r10,r11,Llast2
 b Lload2
Lzero2:
 mov 0,r11
 b Lload2
Llast2:
 mov r14,r11
Lload2:
 ldob (r5)[r11],r12
 ldob (r6)[r12],r12
 stob r12,(r3)
 stob r12,(r4)
 lda 320(r3),r3
 lda 320(r4),r4
 addo r8,r7,r7
 subo 1,r9,r9
 cmpobne 0,r9,Lpost2
Ldone:
 ret
