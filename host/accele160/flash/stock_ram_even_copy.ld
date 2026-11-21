OUTPUT_ARCH(i960)
ENTRY(stock_ram_even_copy)
stock_unsupported = 0xc0023790;
SECTIONS {
 . = 0xc000fe40;
 .text : { *(.text*) }
 /DISCARD/ : { *(.data*) *(.bss*) *(.comment*) }
}
ASSERT(ADDR(.text) + SIZEOF(.text) <= 0xc0010000,
       "copy stub extends outside erased loader page")
