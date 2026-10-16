/* AcceleRAID 160 exact 0x8f handler: preserve PING, RAM proof and op 3.
 * Operation 4 reserves one fixed 512 KiB stock allocation for owner
 * 0x96016004; operation 5 releases only that saved allocation.
 * No host-supplied pointer, length or DMA descriptor is dereferenced.
 * This is a bounded allocator experiment, not an RTEMS loader.
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
 cmpobe r5,r6,check_common
 lda 0x03018f00,r6
 cmpobe r5,r6,check_common
 lda 0x04018f00,r6
 cmpobe r5,r6,check_common
 lda 0x05018f00,r6
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
 lda 0x03018f00,r6
 cmpobe r5,r6,allocator_probe
 lda 0x04018f00,r6
 cmpobe r5,r6,reserve_pool
 lda 0x05018f00,r6
 cmpobe r5,r6,release_pool

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
 b complete_ok

allocator_probe:
 /* The stock image-read path calls c0066b90 with g0=size and g1=caller ID.
  * That calls the 32 KiB block allocator in mode 1. Release through the
  * stock c0066fc0 path with g0=pointer, g1=size, g2=same caller ID.
  */
 lda 0x40000,g0
 lda 0x96016003,g1
 callx 0xc0066b90
 cmpibe 0,g0,ping_reject
 mov g0,r8
 mov r8,g0
 lda 0x40000,g1
 lda 0x96016003,g2
 callx 0xc0066fc0
 /* The expected mode-1 free run was c0618000..c078ffff on this boot.
  * Reject an unexpected pointer after release; the host also compares the
  * entire allocator table before and after the operation.
  */
 lda 0xc0618000,r9
 cmpobl r8,r9,ping_reject
 lda 0xc0790000,r9
 cmpobge r8,r9,ping_reject
 lda 0x7fff,r9
 and r8,r9,r9
 cmpibne 0,r9,ping_reject
 ld 28(r4),r5
 st r5,0xc000f824
 st r8,0xc000f828
 lda 0x40000,r5
 st r5,0xc000f82c
 lda 0x4f4c4c41,r5
 st r5,0xc000f820

 b complete_ok

reserve_pool:
 /* f840..f84f is a card-owned record in the previously erased loader page.
  * Only the allocation owner ID and fixed size below can be used. The host
  * checks the live allocator table before admitting uploads into the grant.
  */
 ld 0xc000f840,r5
 lda 0xffffffff,r6
 cmpobne r5,r6,ping_reject
 lda 0x80000,g0
 lda 0x96016004,g1
 callx 0xc0066b90
 cmpibe 0,g0,ping_reject
 mov g0,r8
 lda 0xc0618000,r9
 cmpobl r8,r9,reserve_invalid
 lda 0xc0710000,r9
 cmpobg r8,r9,reserve_invalid
 lda 0x7fff,r9
 and r8,r9,r9
 cmpibne 0,r9,reserve_invalid
 st r8,0xc000f844
 lda 0x80000,r5
 st r5,0xc000f848
 lda 0x96016004,r5
 st r5,0xc000f84c
 lda 0x56525352,r5
 st r5,0xc000f840
 ld 28(r4),r5
 st r5,0xc000f824
 st r8,0xc000f828
 lda 0x80000,r5
 st r5,0xc000f82c
 lda 0x4f4c4c41,r5
 st r5,0xc000f820
 b complete_ok

reserve_invalid:
 mov r8,g0
 lda 0x80000,g1
 lda 0x96016004,g2
 callx 0xc0066fc0
 b ping_reject

release_pool:
 ld 0xc000f840,r5
 lda 0x56525352,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f844,r8
 ld 0xc000f848,r5
 lda 0x80000,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f84c,r5
 lda 0x96016004,r6
 cmpobne r5,r6,ping_reject
 lda 0xc0618000,r9
 cmpobl r8,r9,ping_reject
 lda 0xc0710000,r9
 cmpobg r8,r9,ping_reject
 lda 0x7fff,r9
 and r8,r9,r9
 cmpibne 0,r9,ping_reject
 mov r8,g0
 lda 0x80000,g1
 lda 0x96016004,g2
 callx 0xc0066fc0
 lda 0xffffffff,r5
 st r5,0xc000f844
 st r5,0xc000f848
 st r5,0xc000f84c
 st r5,0xc000f840
 ld 28(r4),r5
 st r5,0xc000f824
 st r8,0xc000f828
 lda 0x80000,r5
 st r5,0xc000f82c
 lda 0x45455246,r5
 st r5,0xc000f820

complete_ok:
 mov 0,g1
 stos g1,0x56(r4)
 mov r4,g0
 b stock_completion

ping_reject:
 b stock_unsupported

expected_probe:
 .incbin "probe.bin"
