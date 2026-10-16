OUTPUT_ARCH(i960)
ENTRY(late_callsite)
dispatch_hook = 0xc000e1d8;
SECTIONS {
 . = 0xc000c9cc;
 .text : { *(.text*) }
 /DISCARD/ : { *(.data*) *(.bss*) *(.comment*) }
}
ASSERT(SIZEOF(.text) == 4, "late hook must be one instruction")
