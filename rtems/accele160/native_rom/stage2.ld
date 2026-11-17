ENTRY(_stage2_entry)
SECTIONS {
  . = 0xc000a000;
  .text : { KEEP(*(.entry)) *(.text*) *(.rodata*) *(.data*) }
  .bss : { *(.bss*) *(COMMON) }
  ASSERT(. <= 0xc0010000, "stage-two loader exceeds stock loader window")
}
