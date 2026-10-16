/* Offline-only AcceleRAID 160 PING candidate, late-loader variant.
 * Stock 6.00-05 only. c000c9cc is the common loader return, after the
 * compressed image, stock setup and descriptor initialization. Replace its
 * 4-byte ret with a branch here; this hook restores the return.
 * No flash image is produced by the audit. r4 is the IOCTL command object
 * at dispatch. Nonzero nonce is admission only, not a response echo.
 */
 .text
 .globl dispatch_hook
 .globl ping_handler
dispatch_hook:
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
