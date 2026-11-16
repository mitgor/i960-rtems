ENTRY(_start)
SECTIONS {
  . = 0xc0010000;
  .text : { KEEP(*(.entry)) *(.text*) *(.rodata*) . = ALIGN(16); }
  .data : { *(.data*) . = ALIGN(16); }
  __bss_start = .;
  .bss (NOLOAD) : { *(.bss*) *(COMMON) . = ALIGN(16); }
  __bss_end = .;
  ASSERT(__bss_end <= 0xc003e000, "RTEMS image overlaps native entry stack")
}
