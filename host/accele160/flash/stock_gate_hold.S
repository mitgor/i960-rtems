/* VPP gate-hold diagnostic for stock 6.00-05, run once from RAM under 0x8f.
 *
 * It sets board-control bit 3 exactly as the stock writer does
 * (c0055410..c0055450), holds it, and clears it exactly as stock does
 * (c005547c..c00554b4). It never addresses the flash aperture: no read-array,
 * identifier, erase, program or lock command is issued. With the gate set and
 * no command, the 28F008S3 stays in read-array mode.
 *
 * Measure the flash VPP pin with a multimeter during the hold.
 *
 * Report, nine words at c000f834 (the slot the flash-ID launcher restores):
 *   +0 magic "GHD1"            +4 board context pointer
 *   +8 shadow before           +12 gate register read before set
 *   +16 gate read at end of hold, bit 3 still requested
 *   +20 gate read after clear  +24 shadow after
 *   +28 polls completed        +32 code: 0 held, 1 bad context, 2 gate busy
 * Codes 1 and 2 return before any write to the context or the register.
 */
 .ifndef HOLD_POLLS
 /* Calibration knob. The loop below follows the operation-11 poll, measured at
  * 0.513 us per poll on stock 6.00-05 (20,000,000 polls in 10.26 s), so this
  * default is about 8 s. The launcher records the real elapsed time. */
 .set HOLD_POLLS,16000000
 .endif

 .text
 .globl _start
_start:
 lda 0xc000f800,g0
 call gate_hold
 lda 0xc0023790,g1          /* stock unsupported completion, as flash-ID */
 bx (g1)

gate_hold:
 mov g0,r4                  /* report base; only r registers are used below */
 mov 0,r3
 st r3,0x34(r4)
 ld 0xc04ad650,r5           /* stock board context */
 st r5,0x38(r4)
 lda 0xff000003,r6
 and r5,r6,r6
 lda 0xc0000000,r7
 cmpobne r6,r7,bad_context
 ld 0x50(r5),r6
 st r6,0x3c(r4)
 bbs 3,r6,gate_busy
 lda 0xe0500000,r8
 ldob (r8),r7
 st r7,0x40(r4)

 setbit 3,r6,r6             /* stock set */
 st r6,0x50(r5)
 ldob 0x50(r5),r7
 setbit 3,r7,r7
 stob r7,(r8)

 lda HOLD_POLLS,r12
 mov 0,r10
hold:
 dcctl 2,0,r11
 ld 0x34(r4),r14
 addo 1,r10,r10
 subo 1,r12,r12
 cmpibne 0,r12,hold

 /* Read back only now, so a read side effect cannot shorten the hold. */
 ldob (r8),r7
 st r7,0x44(r4)

 ld 0x50(r5),r6             /* stock clear */
 clrbit 3,r6,r6
 st r6,0x50(r5)
 ldob 0x50(r5),r7
 lda 0xf7,r13
 and r7,r13,r7
 stob r7,(r8)

 ldob (r8),r7
 st r7,0x48(r4)
 ld 0x50(r5),r6
 st r6,0x4c(r4)
 st r10,0x50(r4)
 mov 0,r3
finish:
 st r3,0x54(r4)
 lda 0x31444847,r3          /* GHD1, published last */
 st r3,0x34(r4)
 mov 0,g0
 ret
bad_context:
 mov 1,r3
 b finish
gate_busy:
 mov 2,r3
 b finish
