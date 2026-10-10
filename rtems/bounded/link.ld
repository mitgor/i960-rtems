ENTRY(_start)
SECTIONS {
 . = 0xc0f2c000;
 .text : { KEEP(*(.entry)) *(.text*) *(.rodata*) . = ALIGN(16); }
 .data : { *(.data*) . = ALIGN(16); }
 __bss_start = .;
 .bss : { *(.bss*) *(COMMON) . = ALIGN(16); }
 __bss_end = .;
 .image_tail : { BYTE(0) . = ALIGN(4); }
 ASSERT(. <= 0xc0f3c000, "bounded image exceeds verified 64 KiB upload")
}
