/* Cold-entry RTEMS diagnostic.  The stock reset block supplies DRAM and a
 * valid PRCB, but the stock controller application is never entered. */
 .section .entry,"ax"
 .globl _start
_start:
#ifdef ACCELE160_EARLY_ENTRY_MARKER
 /* Diagnostic-only milestones in the existing report aperture.  The later
  * C entry and scheduler result replace these words in the same location. */
 lda 0x30544e45,g0 /* ENT0: RTEMS entry before modpc/stack */
 st g0,0xc0001f1c
 syncf
#endif
 lda 0x1f0000,g1
 modpc 0,g1,g1
#ifdef ACCELE160_EARLY_ENTRY_MARKER
 lda 0x31544e45,g0 /* ENT1: modpc returned, before stack/C entry */
 st g0,0xc0001f1c
 syncf
#endif
 lda 0xc003ffc0,sp
 lda 0,fp
 lda 0,pfp
 call _native_main
1: b 1b

 .text
 .globl _native_park
_native_park:
 st g0,0xc0001f20
 syncf
2: b 2b
