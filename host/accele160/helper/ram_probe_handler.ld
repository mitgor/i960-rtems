OUTPUT_ARCH(i960)
ENTRY(dispatch_hook)
stock_completion = 0xc004e940;
stock_unsupported = 0xc0023790;
SECTIONS {
 . = 0xc000e1d8;
 .text : { *(.text*) }
 /DISCARD/ : { *(.data*) *(.bss*) *(.comment*) }
}
ASSERT(SIZEOF(.text) <= 0x300, "RAM-probe handler exceeds code slot")
ASSERT(ADDR(.text) + SIZEOF(.text) <= 0xc000f800,
       "RAM-probe handler overlaps result record")
