/* Fixed returning CPU-side staging CRC probe. No flash writes.
 * Reads all 512 KiB through the exact C1F2C000 programmer source alias.
 * Baseline callback invalidates D-cache before dispatching here.
 * Return 017F only for the pinned candidate CRC; mismatch returns 0180.
 */
        .text
        .globl _start
_start:
        icctl 2,0,g2
        lda 0xc1f2c000,r4
        lda 0x80000,r5
        lda 0xffffffff,r6
        lda 0xedb88320,r7
byte_loop:
        ldob (r4),r8
        xor r8,r6,r6
        mov 8,r9
bit_loop:
        and 1,r6,r10
        shro 1,r6,r6
        cmpobe 0,r10,no_xor
        xor r7,r6,r6
no_xor:
        subo 1,r9,r9
        cmpobne 0,r9,bit_loop
        addo 1,r4,r4
        subo 1,r5,r5
        cmpobne 0,r5,byte_loop
        not r6,r6
        /* Expected CRC inserted by build_probe.py from pinned full image. */
        lda 0x2012d01f,r7
        lda 0x180,g1
        cmpobne r6,r7,complete
        lda 0x17f,g1
complete:
        dcctl 2,0,g2
        stos g1,0x18(g0)
        lda 0xc004bad0,g1
        bx (g1)
