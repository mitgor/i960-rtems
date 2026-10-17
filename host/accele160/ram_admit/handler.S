/* AcceleRAID 160 retained handler. Operations 1-12 are unchanged; operation
 * 13 admits a trusted-host, returning RAM image after grant and digest checks.
 * A payload that fails to return is not made safe by this admission gate. */
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
 cmpobe r5,r6,check_common
 lda 0x06018f00,r6
 cmpobe r5,r6,check_common
 lda 0x07018f00,r6
 cmpobe r5,r6,check_common
 lda 0x08018f00,r6
 cmpobe r5,r6,check_common
 lda 0x09018f00,r6
 cmpobe r5,r6,check_common
 lda 0x0a018f00,r6
 cmpobe r5,r6,check_common
 lda 0x0b018f00,r6
 cmpobe r5,r6,check_common
 lda 0x0c018f00,r6
 cmpobe r5,r6,check_common
 lda 0x0d018f00,r6
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
 lda 0x06018f00,r6
 cmpobe r5,r6,copy_page
 lda 0x07018f00,r6
 cmpobe r5,r6,hash_owned_image
 lda 0x08018f00,r6
 cmpobe r5,r6,call_owned_probe
 lda 0x09018f00,r6
 cmpobe r5,r6,call_owned_rtems
 lda 0x0a018f00,r6
 cmpobe r5,r6,read_inventory
 lda 0x0b018f00,r6
 cmpobe r5,r6,stop_gate
 lda 0x0c018f00,r6
 cmpobe r5,r6,vector_gate
 lda 0x0d018f00,r6
 cmpobe r5,r6,call_manifest_image

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
 /* Host may have restored a staging page after operation 6; discard any
  * D-cache line holding its earlier PCI-written contents before free.
  */
 dcctl 2,0,r11
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

 b complete_ok

copy_page:
 /* Keep the zero-DMA mailbox envelope. The host supplies its bounded
  * index/checksum in a separately read-back control record at f860.
  * The final odd grant page is the only staging source. Index 127 is not
  * a valid target, so the copy can never overwrite its source.
  */
 dcctl 2,0,r11
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
 ld 0xc000f860,r5
 lda 0x59504f43,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f864,r5
 ld 28(r4),r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f868,r9
 lda 126,r10
 cmpobg r9,r10,ping_reject
 mov r9,r11
 shlo 12,r9,r9
 addo r8,r9,r9
 lda 0x7f000,r10
 addo r8,r10,r10
 mov r10,g0
 call fnv_page
 ld 0xc000f86c,r5
 cmpobne g0,r5,ping_reject
 mov r10,r8
 mov r9,r10
 lda 1024,r12
copy_loop:
 ld (r8),r5
 st r5,(r10)
 addo 4,r8,r8
 addo 4,r10,r10
 subo 1,r12,r12
 cmpibne 0,r12,copy_loop
 mov r9,g0
 call fnv_page
 ld 0xc000f86c,r5
 cmpobne g0,r5,ping_reject
 st r11,0xc000f828
 st g0,0xc000f82c
 ld 28(r4),r5
 st r5,0xc000f824
 lda 0x59504f43,r5
 st r5,0xc000f820
 b complete_ok

hash_owned_image:
 /* Fixed owner record and fixed contiguous page count. This operation never
  * writes the payload. A mismatched digest returns stock unsupported status.
  */
 dcctl 2,0,r11
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
 ld 0xc000f870,r5
 lda 0x48534148,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f874,r5
 ld 28(r4),r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f878,r13
 cmpibe 0,r13,ping_reject
 lda 127,r10
 cmpobg r13,r10,ping_reject
 shlo 12,r13,r11
 lda 0x811c9dc5,r9
 lda 0x01000193,r10
hash_image_loop:
 ldob (r8),r12
 xor r12,r9,r9
 mulo r10,r9,r9
 addo 1,r8,r8
 subo 1,r11,r11
 cmpibne 0,r11,hash_image_loop
 ld 0xc000f87c,r5
 cmpobne r9,r5,ping_reject
 lda 0x48534148,r5
 st r5,0xc000f830
 ld 28(r4),r5
 st r5,0xc000f834
 st r13,0xc000f838
 st r9,0xc000f83c
 b complete_ok

call_owned_probe:
 /* Operation 8: exact uploaded 80-byte leaf at the start of the fixed
  * owner-tagged allocation. Hash both full pages before I-cache handoff.
  * The leaf writes only f800..f80f and returns normally.
  */
 dcctl 2,0,r11
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
 ld 0xc000f880,r5
 lda 0x43455845,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f884,r5
 ld 28(r4),r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f888,r5
 lda 2,r6
 cmpobne r5,r6,ping_reject
 lda 0x811c9dc5,r9
 lda 0x01000193,r10
 lda 8192,r11
owned_exec_hash_loop:
 ldob (r8),r12
 xor r12,r9,r9
 mulo r10,r9,r9
 addo 1,r8,r8
 subo 1,r11,r11
 cmpibne 0,r11,owned_exec_hash_loop
 ld 0xc000f88c,r5
 cmpobne r9,r5,ping_reject
 ld 0xc000f844,r8
 lda expected_probe,r9
 lda 80,r10
owned_exec_compare:
 ld (r8),r5
 ld (r9),r6
 cmpobne r5,r6,ping_reject
 addo 4,r8,r8
 addo 4,r9,r9
 subo 4,r10,r10
 cmpibne 0,r10,owned_exec_compare
 icctl 2,0,r11
 lda 0xc000f800,g0
 ld 28(r4),g1
 ld 0xc000f844,r8
 callx (r8)
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
 lda 0x214e5552,r5
 st r5,0xc000f830
 ld 28(r4),r5
 st r5,0xc000f834
 ld 0xc000f844,r5
 st r5,0xc000f838
 ld 0xc000f88c,r5
 st r5,0xc000f83c
 b complete_ok

call_owned_rtems:
 /* Fixed 15-page image only. The host pins SHA-256, and the card pins both
  * the complete FNV and exact entry prefix. The trusted-host FNV is an
  * accidental-corruption gate, not a cryptographic authenticator.
  * This image runs ten synchronous RTEMS software ticks and returns.
  */
 dcctl 2,0,r11
 ld 0xc000f840,r5
 lda 0x56525352,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f844,r8
 lda 0xc0710000,r6
 cmpobne r8,r6,ping_reject
 ld 0xc000f848,r5
 lda 0x80000,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f84c,r5
 lda 0x96016004,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f890,r5
 lda 0x39544552,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f894,r5
 ld 28(r4),r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f898,r5
 lda 15,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f89c,r5
 lda 0x648486da,r6
 cmpobne r5,r6,ping_reject
 lda 0x811c9dc5,r9
 lda 0x01000193,r10
 lda 61440,r11
rtems_hash_loop:
 ldob (r8),r12
 xor r12,r9,r9
 mulo r10,r9,r9
 addo 1,r8,r8
 subo 1,r11,r11
 cmpibne 0,r11,rtems_hash_loop
 lda 0x648486da,r5
 cmpobne r9,r5,ping_reject
 ld 0xc000f844,r8
 lda expected_rtems_prefix,r9
 lda 80,r10
rtems_compare_loop:
 ld (r8),r5
 ld (r9),r6
 cmpobne r5,r6,ping_reject
 addo 4,r8,r8
 addo 4,r9,r9
 subo 4,r10,r10
 cmpibne 0,r10,rtems_compare_loop
 icctl 2,0,r11
 lda 0xc000f800,g0
 ld 28(r4),g1
 ld 0xc000f844,r8
 callx (r8)
 cmpibne 0,g0,ping_reject
 ld 0xc000f800,r5
 lda 0x4d455452,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f804,r5
 ld 28(r4),r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f808,r5
 lda 0x46600006,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f80c,r5
 lda 1,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f810,r5
 lda 5,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f814,r5
 lda 11,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f818,r5
 lda 0xc071e270,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f81c,r5
 lda 0x1600a001,r6
 cmpobne r5,r6,ping_reject
 lda 0x214d4552,r5
 st r5,0xc000f830
 ld 28(r4),r5
 st r5,0xc000f834
 ld 0xc000f844,r5
 st r5,0xc000f838
 lda 0x648486da,r5
 st r5,0xc000f83c
 b complete_ok

read_inventory:
 /* No allocator grant or uploaded image. The caller must have saved the
  * whole erased loader page; result occupies f8a0..f947. No TMRx mode
  * register is read because reading it clears terminal count. */
 dcctl 2,0,r11
 lda 0xc000f8a0,r8
 lda 0x31564e49,r5
 st r5,(r8)
 ld 28(r4),r5
 st r5,4(r8)
 lda 15,r5
 st r5,8(r8)
 lda 8,r5
 st r5,12(r8)
 lda inventory_addresses,r9
 addo 16,r8,r8
 lda 15,r12
inventory_register_loop:
 ld (r9),r10
 ld (r10),r11
 st r10,(r8)
 st r11,4(r8)
 addo 4,r9,r9
 addo 8,r8,r8
 subo 1,r12,r12
 cmpibne 0,r12,inventory_register_loop
 /* The fixed ROM PRCB address is pinned by the stock boot record. Never
  * dereference the live FF008700 pointer in this observational command. */
 lda 0xfeffdd20,r9
 lda 8,r12
inventory_prcb_loop:
 ld (r9),r11
 st r11,(r8)
 addo 4,r9,r9
 addo 4,r8,r8
 subo 1,r12,r12
 cmpibne 0,r12,inventory_prcb_loop
 b complete_ok

inventory_addresses:
 .word 0xff000300,0xff000304,0xff000310,0xff000314
 .word 0xff008500,0xff008504,0xff008510
 .word 0xff008520,0xff008524,0xff008528
 .word 0xff008700,0xff008704,0xff008708,0xff008710
 .word 0x0000003c

stop_gate:
 /* The host preloads f960..f96c through the PCI translated aperture.
  * Poll only that word, with full D-cache invalidation for non-snooped PCI
  * writes. A finite budget guarantees that loss of the host cannot strand
  * the stock direct-command mutex indefinitely. */
 dcctl 2,0,r11
 ld 0xc000f960,r5
 lda 0x31504f54,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f964,r5
 ld 28(r4),r6
 cmpobne r5,r6,ping_reject
 lda 0x161610b1,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f968,r5
 lda 1,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f96c,r5
 cmpibne 0,r5,ping_reject
 lda 0x59444152,r5
 st r5,0xc000f970
 lda 20000000,r12
stop_poll:
 dcctl 2,0,r11
 ld 0xc000f96c,r5
 lda 0x504f5453,r6
 cmpobe r5,r6,stop_seen
 subo 1,r12,r12
 cmpibne 0,r12,stop_poll
 lda 0x454d4954,r5
 st r5,0xc000f970
 b ping_reject
stop_seen:
 ld 0xc000f960,r5
 lda 0x31504f54,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f964,r5
 lda 0x161610b1,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f968,r5
 lda 1,r6
 cmpobne r5,r6,ping_reject
 lda 0x214b4341,r5
 st r5,0xc000f974
 lda 0x161610b1,r5
 st r5,0xc000f978
 lda 1,r5
 st r5,0xc000f97c
 b complete_ok

vector_gate:
 /* Intel 80303 manual Table 8-7 maps cached vector 18 to internal RAM
  * address 04h and vector 130 to 20h. Loads cannot alter these words.
  * TMR1 mode ff000318 is read-clear for terminal-count status. Do not
  * touch it unless count/reload=0, IPND.tip1=0, IMSK.tim1=0, and IMAP2
  * maps TINT1 to the undefined field 0; repeat those guards immediately
  * before the read. A set pre-read TC bit cannot be restored by software.
  */
 ld 28(r4),r5
 lda 0x161610c1,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f980,r5
 lda 0xffffffff,r6
 cmpobne r5,r6,ping_reject
 lda 0xc000f980,r8
 lda 0x31434556,r5
 st r5,0(r8)
 lda 0x161610c1,r5
 st r5,4(r8)
 mov 0,r10
 st r10,8(r8)
 ld 0x00000004,r5
 st r5,12(r8)
 ld 0x00000020,r5
 st r5,16(r8)
 ld 0xff008500,r5
 st r5,20(r8)
 ld 0xff008504,r5
 st r5,24(r8)
 ld 0xff008528,r5
 st r5,28(r8)
 ld 0xff000310,r5
 st r5,32(r8)
 ld 0xff000314,r5
 st r5,36(r8)
 lda 0xffffffff,r5
 st r5,40(r8)
 ld 32(r8),r5
 cmpibne 0,r5,vector_skip_mode
 ld 36(r8),r5
 cmpibne 0,r5,vector_skip_mode
 ld 20(r8),r5
 lda 0x2000,r6
 and r5,r6,r6
 cmpibne 0,r6,vector_skip_mode
 ld 24(r8),r5
 lda 0x2000,r6
 and r5,r6,r6
 cmpibne 0,r6,vector_skip_mode
 ld 28(r8),r5
 lda 0x00f00000,r6
 and r5,r6,r6
 cmpibne 0,r6,vector_skip_mode
 ld 0xff000310,r5
 cmpibne 0,r5,vector_skip_mode
 ld 0xff000314,r5
 cmpibne 0,r5,vector_skip_mode
 ld 0xff008500,r5
 lda 0x2000,r6
 and r5,r6,r6
 cmpibne 0,r6,vector_skip_mode
 ld 0xff008504,r5
 lda 0x2000,r6
 and r5,r6,r6
 cmpibne 0,r6,vector_skip_mode
 ld 0xff008528,r5
 lda 0x00f00000,r6
 and r5,r6,r6
 cmpibne 0,r6,vector_skip_mode
 ld 0xff000318,r5
 st r5,40(r8)
 lda 3,r10
 lda 1,r6
 and r5,r6,r6
 cmpibe 0,r6,vector_skip_mode
 lda 7,r10
vector_skip_mode:
 st r10,8(r8)
 ld 0xff008500,r5
 st r5,44(r8)
 ld 0xff008504,r5
 st r5,48(r8)
 ld 0xff008528,r5
 st r5,52(r8)
 ld 0xff000310,r5
 st r5,56(r8)
 ld 0xff000314,r5
 st r5,60(r8)
 ld 0x00000004,r5
 st r5,64(r8)
 ld 0x00000020,r5
 st r5,68(r8)
 b complete_ok

fnv_page:
 mov g0,r8
 lda 0x811c9dc5,r9
 lda 0x01000193,r10
 lda 4096,r11
fnv_loop:
 ldob (r8),r12
 xor r12,r9,r9
 mulo r10,r9,r9
 addo 1,r8,r8
 subo 1,r11,r11
 cmpibne 0,r11,fnv_loop
 mov r9,g0
 ret

call_manifest_image:
 /* Host writes an eight-word manifest at fa00 and initializes the fa20
  * report to a sentinel.  Page count excludes the last grant staging page.
  * The owner tag is the accepted stock allocator grant, not a claim about
  * arbitrary card RAM.  FNV detects corruption; host pins SHA-256 identity.
  */
 dcctl 2,0,r11
 ld 0xc000f840,r5
 lda 0x56525352,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f844,r8
 lda 0xc0710000,r6
 cmpobne r8,r6,ping_reject
 ld 0xc000f848,r5
 lda 0x80000,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000f84c,r5
 lda 0x96016004,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000fa00,r5
 lda 0x314d4152,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000fa04,r5
 ld 28(r4),r6
 cmpobne r5,r6,ping_reject
 ld 0xc000fa08,r5
 cmpobne r5,r8,ping_reject
 ld 0xc000fa0c,r5
 lda 0x80000,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000fa10,r13
 cmpibe 0,r13,ping_reject
 lda 127,r6
 cmpobg r13,r6,ping_reject
 ld 0xc000fa14,r14
 lda 3,r6
 and r14,r6,r6
 cmpibne 0,r6,ping_reject
 shlo 12,r13,r11
 cmpobge r14,r11,ping_reject
 ld 0xc000fa1c,r5
 cmpibne 0,r5,ping_reject
 lda 0x811c9dc5,r9
 lda 0x01000193,r10
manifest_hash_loop:
 ldob (r8),r12
 xor r12,r9,r9
 mulo r10,r9,r9
 addo 1,r8,r8
 subo 1,r11,r11
 cmpibne 0,r11,manifest_hash_loop
 ld 0xc000fa18,r5
 cmpobne r9,r5,ping_reject
 /* A small trusted returning payload receives report, nonce and manifest.
  * The host must not use this opcode for an unbounded or unreviewed image. */
 icctl 2,0,r11
 lda 0xc000fa20,g0
 ld 28(r4),g1
 lda 0xc000fa00,g2
 ld 0xc000fa08,r8
 ld 0xc000fa14,r9
 addo r8,r9,r8
 callx (r8)
 cmpibne 0,g0,ping_reject
 ld 0xc000fa20,r5
 lda 0x314e5552,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000fa24,r5
 ld 28(r4),r6
 cmpobne r5,r6,ping_reject
 ld 0xc000fa28,r5
 lda 0x31454e4f,r6
 cmpobne r5,r6,ping_reject
 ld 0xc000fa08,r5
 st r5,0xc000fa2c
 ld 0xc000fa10,r5
 st r5,0xc000fa30
 ld 0xc000fa18,r5
 st r5,0xc000fa34
 b complete_ok

complete_ok:
 mov 0,g1
 stos g1,0x56(r4)
 mov r4,g0
 b stock_completion

ping_reject:
 b stock_unsupported

expected_probe:
 .incbin "probe.bin"

expected_rtems_prefix:
 .incbin "prefix.bin"
