/* Offline-only routing rehearsal for the accepted 6.00-05 image.
 * Entry replaces the loader's call at c000c638. It calls the original
 * c000c6c0 setup routine, then changes only IOCTL table slot 0x8f.
 * The target deliberately branches to the original unsupported handler.
 * No new request can succeed with this stub; it is not a PING implementation.
 */
 .text
 .globl dispatch_hook
 .globl unsupported_fallback
dispatch_hook:
 call original_setup
 lda unsupported_fallback,g1
 st g1,0xc00234fc
 ret
unsupported_fallback:
 b stock_unsupported
