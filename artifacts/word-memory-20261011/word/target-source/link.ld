ENTRY(_start)
SECTIONS {
 . = 0xc0f2c000;
 .text : { KEEP(*(.entry)) *(.text*) *(.rodata*) . = ALIGN(16); }
 ASSERT(. <= 0xc0f4c000, "code exceeds immutable 128 KiB")
 . = 0xc0f4c010;
 .data : { *(.data*) . = ALIGN(16); }
 __bss_start = .;
 .bss : { *(.bss*) *(COMMON) . = ALIGN(16); }
 __bss_end = .;
 .image_tail : { BYTE(0) . = ALIGN(4); }
 ASSERT(. <= 0xc0f9bff0, "RTEMS workspace overlaps upper guard")
}
