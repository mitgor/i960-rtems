/* flat RAM image; emulator sets up the stack frame and enters at _main */
ENTRY(_main)
SECTIONS {
  . = 0x2000;
  .text : { *(.text*) }
  .rodata : { *(.rodata*) *(.rdata*) }
  .data : { *(.data*) }
  .bss : { *(.bss*) *(COMMON) }
  _end = .;
}
