/* Two-phase, flashless installer for the already accepted 4324-byte handler.
 * Host BAR0 exposes c000f000 but not c000e000. First 0x8f call copies the
 * 3624-byte first part from f000 to e1d8 and compares every word. The host
 * then replaces f000..f2bb with the 700-byte tail and sets phase=2. Second
 * 0x8f call checks the complete image sum and changes the dispatch pointer
 * from the i960 side. Both calls return through stock_unsupported.
 * This stub occupies fe40..ffff; fe30..fe3f is its report/control record.
 */
 .text
 .globl stock_ram_even_copy
stock_ram_even_copy:
 dcctl 2,0,r11
 ld 0xc000fe34,r5
 cmpibe 2,r5,phase_two

 lda 0xc000f000,r5
 lda 0xc000e1d8,r6
 lda 0xc000fe28,r7
copy_loop:
 ld (r5),r8
 st r8,(r6)
 addo 4,r5,r5
 addo 4,r6,r6
 cmpobl r5,r7,copy_loop

 lda 0xc000f000,r5
 lda 0xc000e1d8,r6
compare_loop:
 ld (r5),r8
 ld (r6),r9
 cmpobne r8,r9,copy_bad
 addo 4,r5,r5
 addo 4,r6,r6
 cmpobl r5,r7,compare_loop
 mov 0,r9
 st r9,0xc000fe38
 lda 0x31435059,r9 /* YPC1 */
 st r9,0xc000fe30
 b stock_unsupported
copy_bad:
 lda 1,r9
 st r9,0xc000fe38
 b stock_unsupported

phase_two:
 ld 0xc000fe30,r5
 lda 0x31435059,r6
 cmpobne r5,r6,phase_bad
 ld 0xc000fe38,r5
 cmpibne 0,r5,phase_bad
 lda 0xc000e1d8,r5
 lda 0xc000f2bc,r6
 mov 0,r9
sum_loop:
 ld (r5),r8
 addo r8,r9,r9
 addo 4,r5,r5
 cmpobl r5,r6,sum_loop
 lda 0xf7c53a95,r8 /* additive checksum of exact pinned handler */
 cmpobne r8,r9,phase_bad
 icctl 2,0,r11
 lda 0xc000e1ec,r8
 st r8,0xc00234fc
 mov 0,r9
 st r9,0xc000fe38
 lda 0x32435059,r9 /* YPC2 */
 st r9,0xc000fe30
 b stock_unsupported
phase_bad:
 lda 2,r9
 st r9,0xc000fe38
 b stock_unsupported
