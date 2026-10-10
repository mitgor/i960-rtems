/* The loader is position-dependent: it runs in place from flash, so it is linked
 * at its run address. That address = stock image base + the mkimage.py --at offset:
 *   0xFEFC8000 (base, = 0xFF000000 - 0x38000 stock payload) + 0x4D44 = 0xFEFCCD44.
 * Passed via -Ttext in the Makefile so it stays in one place. objcopy -O binary
 * then yields a flat blob that host/mkimage.py drops at --at and points firstIP to.
 */
ENTRY(_start)
SECTIONS {
  .text   : { *(.text*) }
  .rodata : { *(.rodata*) *(.rdata*) }
  .data   : { *(.data*) }
  .bss    : { *(.bss*) *(COMMON) }   /* expected empty; loader uses no static storage */
  _end = .;
}
