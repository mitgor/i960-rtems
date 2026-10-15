/* unsigned (a << 16) / b, only after caller proves b>0 and quotient<2^30.
 * Register-window ABI. ediv writes remainder r6, quotient r7. */
.text
.align 4
.globl _doom_div_unsigned
_doom_div_unsigned:
 shlo 16,g0,r4
 shro 16,g0,r5
 ediv g1,r4,r6
 mov r7,g0
 ret
