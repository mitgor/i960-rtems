/* Offline-only AcceleRAID 160 zero-DMA PING candidate.
 * Stock 6.00-05 only; no flash output or live execution from this source.
 * c000c638 loader callsite uses the previously verified 4-byte replacement.
 * At dispatch the stock IOCTL handler has r4 = copied command object.
 * Valid packet: internal status 0, ordinary completion. Any mismatch:
 * branch to stock unsupported (internal 0x104 -> host status 2).
 * Nonce is an admission marker, not echoed or authenticated.
 */
 .text
 .globl dispatch_hook
 .globl ping_handler
dispatch_hook:
 call original_setup
 lda ping_handler,g1
 st g1,0xc00234fc
 ret

ping_handler:
 ldos 2(r4),r5
 lda 0x4020,r6
 cmpobne r5,r6,ping_reject
 lda 4(r4),r5
 lda 20(r4),r6
ping_zero_prefix:
 ld (r5),r7
 cmpibne 0,r7,ping_reject
 addo 4,r5,r5
 cmpobl r5,r6,ping_zero_prefix
 ld 20(r4),r5
 lda 0x01018f00,r6
 cmpobne r5,r6,ping_reject
 ld 24(r4),r5
 lda 0x30363949,r6
 cmpobne r5,r6,ping_reject
 ld 28(r4),r5
 cmpibe 0,r5,ping_reject
 lda 32(r4),r5
 lda 64(r4),r6
ping_zero_sge:
 ld (r5),r7
 cmpibne 0,r7,ping_reject
 addo 4,r5,r5
 cmpobl r5,r6,ping_zero_sge
 mov 0,g1
 stos g1,0x56(r4)
 mov r4,g0
 b stock_completion

ping_reject:
 b stock_unsupported
