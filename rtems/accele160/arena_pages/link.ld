ENTRY(_start)
SECTIONS {
 . = 0xc0710000;
 .text : { KEEP(*(.entry)) *(.text*) *(.rodata*) . = ALIGN(16); }
 .data : { *(.data*) . = ALIGN(16); }
 __bss_start = .;
 .bss : { *(.bss*) *(COMMON) . = ALIGN(16); }
 __bss_end = .;
 ASSERT(. <= 0xc071f000, "RTEMS image crosses owned entry stack")
 . = 0xc071f000;
 .entry_stack : { BYTE(0); . = . + 4094; BYTE(0); }
 ASSERT(. <= 0xc078f000, "RTEMS image overlaps staging page")
}
