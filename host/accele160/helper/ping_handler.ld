OUTPUT_ARCH(i960)
ENTRY(dispatch_hook)
original_setup = 0xc000c6c0;
stock_completion = 0xc004e940;
stock_unsupported = 0xc0023790;
SECTIONS {
 . = 0xc000e1d8;
 .text : { *(.text*) }
 /DISCARD/ : { *(.data*) *(.bss*) *(.comment*) }
}
ASSERT(SIZEOF(.text) <= 256, "PING handler exceeds bounded code slot")
