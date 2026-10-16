/* Candidate normal-call leaf, NOT a flash image or a standalone reset entry.
 * g0: proven-owned, aligned 16-byte local-RAM result; g1: host nonce.
 * Caller provides valid i960 call frame and instruction visibility.
 * Writes exactly four words, performs 32 additions, then returns g0=0.
 * g1..g14 preserved; arithmetic condition codes are clobbered.
 * No MMIO, DMA, firmware calls, interrupt manipulation or host polling.
 */
 .text
 .align 4
 .globl bounded_probe
bounded_probe:
 mov g0,r4
 st g1,4(r4)
 mov 0,r5
 mov 0,r6
 lda 32,r7
probe_loop:
 addo r6,r5,r5
 addo 1,r6,r6
 cmpobl r6,r7,probe_loop
 st r5,8(r4)
 lda 0x96016001,r5
 xor g1,r5,r5
 st r5,12(r4)
 lda 0x444f4e45,r5
 st r5,0(r4)
 mov 0,g0
 ret
