/* A bounded, returning admission test. Build with PROBE_VALUE=0x... .
 * g0: six-word report, g1: nonce, g2: eight-word manifest.
 */
#ifndef PROBE_VALUE
#define PROBE_VALUE 0x16010001
#endif
 .text
 .globl _start
_start:
 lda 0x314e5552,r4
 st r4,(g0)
 st g1,4(g0)
 lda 0x31454e4f,r4
 st r4,8(g0)
 lda PROBE_VALUE,r4
 st r4,24(g0)
 mov 0,g0
 ret
