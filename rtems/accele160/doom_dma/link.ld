ENTRY(_start)
SECTIONS {
 . = 0xc0710000;
 .text : { KEEP(*(.entry)) *(.text*) *(.rodata*) . = ALIGN(16); }
 .data : { *(.data*) . = ALIGN(16); }
 __bss_start = .;
 .bss : { *(.bss*) *(COMMON) . = ALIGN(16); }
 __bss_end = .;
 ASSERT(. <= 0xc0724000, "RTEMS image crosses owned interrupt stack")
 . = 0xc0724000;
 .irqstack : { *(.irqstack) . = ALIGN(16); }
 ASSERT(. <= 0xc072c000, "interrupt stacks cross entry stack")
 . = 0xc072c000;
 .entry_stack : { BYTE(0); . = . + 4094; BYTE(0); }
 ASSERT(. <= 0xc078f000, "RTEMS image overlaps staging page")
 /* Explicit grant reservation; NOLOAD preserves the established 29-page image.
  * Workspace ends c0760000, bank scratch ends c0763000, RIP samples c0772000. */
 .service 0xc0775000 (NOLOAD) : { __service_start = .; . = . + 4096; __service_end = .; }
 .terminal 0xc0777000 (NOLOAD) : { . = . + 8192; }
 ASSERT(0xc0779000 <= 0xc078b000, "terminal overlaps upload buffers")
 ASSERT(__service_end <= 0xc078b000, "service overlaps upload buffers")
}
