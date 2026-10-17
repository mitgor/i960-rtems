ENTRY(_start)
SECTIONS {
 . = 0xc0710000;
 .text : { KEEP(*(.entry)) *(.text*) *(.rodata*) . = ALIGN(16); }
 .data : { *(.data*) . = ALIGN(16); }
 __bss_start = .;
 .bss : { *(.bss*) *(COMMON) . = ALIGN(16); }
 __bss_end = .;
 ASSERT(. <= 0xc0711000, "timer code/data crosses ISR stack")
 . = 0xc0711000;
 .irqstack (NOLOAD) : { *(.irqstack) }
 ASSERT(. <= 0xc0712000, "timer ISR stack crosses entry stack")
 . = 0xc0712000;
 .entry_stack : { BYTE(0); . = . + 4094; BYTE(0); }
 ASSERT(. <= 0xc078f000, "timer image overlaps staging page")
}
