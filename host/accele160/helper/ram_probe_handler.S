/* Experimental AcceleRAID 160 0x8f v1 extension for a single exact payload.
 * Stock 6.00-05, late loader hook. Operation 1 retains the accepted PING.
 * Operation 2 admits only the pinned 80-byte probe at c000f900, invalidates
 * both caches on the i960JT, calls it normally, and verifies its 16-byte
 * result at c000f800 before reporting success. No host-supplied address,
 * length, DMA descriptor, or firmware allocation is dereferenced.
 * This file is NOT an RTEMS loader.
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
zero_prefix:
 ld (r5),r7
 cmpibne 0,r7,ping_reject
 addo 4,r5,r5
 cmpobl r5,r6,zero_prefix
 ld 20(r4),r5
 lda 0x01018f00,r6
 cmpobe r5,r6,check_common
 lda 0x02018f00,r6
 cmpobne r5,r6,ping_reject
check_common:
 ld 24(r4),r5
 lda 0x30363949,r6
 cmpobne r5,r6,ping_reject
 ld 28(r4),r5
 cmpibe 0,r5,ping_reject
 lda 32(r4),r5
 lda 64(r4),r6
zero_sge:
 ld (r5),r7
 cmpibne 0,r7,ping_reject
 addo 4,r5,r5
 cmpobl r5,r6,zero_sge
 ld 20(r4),r5
 lda 0x01018f00,r6
 cmpobe r5,r6,complete_ok

 /* The host must finish and read back all 80 bytes before this command.
  * Jx D-cache is write-through; external PCI writes do not snoop it.
  * D-cache invalidation makes the payload visible for the exact comparison;
  * I-cache invalidation follows comparison before CALLX.
  */
 dcctl 2,0,r11
 lda 0xc000f900,r8
 lda expected_probe,r9
 lda 0xc000f950,r10
compare_probe:
 ld (r8),r5
 ld (r9),r6
 cmpobne r5,r6,ping_reject
 addo 4,r8,r8
 addo 4,r9,r9
 cmpobl r8,r10,compare_probe
 icctl 2,0,r11
 lda 0xc000f800,g0
 ld 28(r4),g1
 callx 0xc000f900
 cmpibne 0,g0,ping_reject
 ld 0xc000f800,r5
 lda 0x444f4e45,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f804,r5
 ld 28(r4),r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f808,r5
 lda 496,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f80c,r5
 ld 28(r4),r6
 lda 0x96016001,r7
 xor r6,r7,r7
 cmpobne r5,r7,ping_reject

complete_ok:
 mov 0,g1
 stos g1,0x56(r4)
 mov r4,g0
 b stock_completion

ping_reject:
 b stock_unsupported

expected_probe:
 .incbin "probe.bin"
