/* Demo payload: proves the loader actually handed off to loaded code.
 * Writes a DIFFERENT magic to OMR0 than the loader's READY, then spins. After
 * `loadctl go`, the host should read 0xBEEF00EE at BAR0+0x18 (not the READY
 * value) - that change can only come from this code running.
 *
 * C function name `start` -> i960 asm symbol `_start` (matches payload.ld ENTRY).
 * Leaf, no stack, no DRAM: loads into internal RAM at 0x200.
 */
typedef unsigned int u32;
void start(void)
{
    *(volatile u32 *)0x1318u = 0xBEEF00EEu;   /* OMR0 */
    for (;;) ;
}
