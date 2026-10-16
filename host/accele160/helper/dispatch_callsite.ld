OUTPUT_ARCH(i960)
ENTRY(dispatch_callsite)
dispatch_hook = 0xc000e1d8;
SECTIONS {
 . = 0xc000c638;
 .text : { *(.text*) }
 /DISCARD/ : { *(.data*) *(.bss*) *(.comment*) }
}
ASSERT(SIZEOF(.text) == 4, "callsite must be exactly one instruction")
