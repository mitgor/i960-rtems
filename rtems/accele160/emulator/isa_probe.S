/* i960 Jx comparison semantics used by the stock ZIP1 loader and runtime.
 * Link at 0xfeff0000.  The emulator detects the final self-branch address.
 */
 .text
 .globl _start
_start:
 mov 0,g0
 chkbit 2,g0
 bno clear_ok
 b fail
clear_ok:
 lda 4,g0
 chkbit 2,g0
 be set_ok
 b fail
set_ok:
 lda 0x00018000,g0
 mov 1,g1
 cmpis g0,g1
 bl signed_short_ok
 b fail
signed_short_ok:
 lda 0x00010000,g0
 mov 0,g1
 cmpos g0,g1
 be unsigned_short_ok
 b fail
unsigned_short_ok:
 lda 0x00000180,g0
 lda 0x7f,g1
 cmpib g0,g1
 bl signed_byte_ok
 b fail
signed_byte_ok:
 lda 0x00000100,g0
 mov 0,g1
 cmpob g0,g1
 be scan_check
 b fail
scan_check:
 lda 0x80000001,g0
 scanbit g0,g2
 cmpobe 31,g2,span_check
 b fail
span_check:
 lda 0x7ffffffe,g0
 spanbit g0,g2
 cmpobe 31,g2,modpc_check
 b fail
modpc_check:
 /* src1 is a dummy, src2 is the mask, and src/dst supplies new PC bits. */
 lda 0x001f0000,g1
 lda 0x00060000,g0
 modpc g1,g1,g0
 shro 16,g0,g2
 and 31,g2,g2
 cmpobe 0,g2,modpc_readback
 b fail
modpc_readback:
 modpc 0,0,g2
 shro 16,g2,g2
 and 31,g2,g2
 cmpobe 6,g2,good
 b fail
good:
 b good
fail:
 b fail
