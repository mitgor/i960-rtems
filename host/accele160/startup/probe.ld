OUTPUT_ARCH(i960)
ENTRY(bounded_probe)
SECTIONS {
 . = 0;
 .text : { *(.text*) }
 /DISCARD/ : { *(.data*) *(.bss*) *(.comment*) }
}
ASSERT(SIZEOF(.text) <= 256, "probe exceeds bounded code slot")
