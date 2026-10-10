/* Tiny demo payload, loaded into internal data RAM at 0x200 (above the loader's
 * stack region) so the whole load-and-run chain can be proven with NO DRAM.
 * Real programs set a higher load address in DRAM (see README milestone 2b).
 */
ENTRY(_start)
SECTIONS {
  . = 0x200;
  .text   : { *(.text*) }
  .rodata : { *(.rodata*) *(.rdata*) }
  .data   : { *(.data*) }
  _end = .;
}
