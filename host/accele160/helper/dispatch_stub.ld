OUTPUT_ARCH(i960)
ENTRY(dispatch_hook)
original_setup = 0xc000c6c0;
stock_unsupported = 0xc0023790;
SECTIONS {
 . = 0xc000e1d8;
 .text : { *(.text*) }
 /DISCARD/ : { *(.data*) *(.bss*) *(.comment*) }
}
ASSERT(SIZEOF(.text) <= 256, "routing stub exceeds bounded code slot")
