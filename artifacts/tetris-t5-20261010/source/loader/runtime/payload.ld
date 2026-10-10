ENTRY(_payload)
SECTIONS {
 . = 0xc0f2c000;
 .text : { *(.text*) *(.rodata*) . = ALIGN(4); }
 .data : { *(.data*) . = ALIGN(4); }
 .bss : { *(.bss*) *(COMMON) }
 ASSERT(_payload == 0xc0f2c000, "entry must be first")
 ASSERT(SIZEOF(.bss) == 0, "initialize writable storage explicitly; no implicit BSS")
 ASSERT(SIZEOF(.text) + SIZEOF(.data) <= 0x10000, "payload exceeds 64 KiB")
}
