OUTPUT_ARCH(i960)
ENTRY(_start)
SECTIONS {
 . = 0xc0710000;
 .text : { *(.text*) }
 /DISCARD/ : { *(.data*) *(.bss*) *(.comment*) }
}
ASSERT(SIZEOF(.text) <= 0x1000, "lease probe crosses first payload page")
