/* Demo payload: proves the loader actually handed off to loaded code.
 * Writes a magic to OMR1, preserving the loader's GO acknowledgement. After
 * `loadctl go`, the host should read 0xBEEF00EE at BAR0+0x1C (not the READY
 * value) - that change can only come from this code running.
 *
 * C function name `start` -> i960 asm symbol `_start` (matches payload.ld ENTRY).
 * Leaf, no stack, no DRAM: loads into internal RAM at 0x200.
 */
typedef unsigned int u32;
#include "mu.h"
void start(void)
{
    *(volatile u32 *)(MU_LOCAL_BASE + R_OMR1) = PAYLOAD_MAGIC;
    for (;;) ;
}
