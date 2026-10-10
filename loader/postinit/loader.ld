ENTRY(_start)
SECTIONS {
 . = 0xFEFE0000;
 .text : { *(.text*) }
 .rodata : { *(.rodata*) *(.rdata*) }
 .data : { *(.data*) }
 .bss : { *(.bss*) *(COMMON) }
 ASSERT(_start == 0xFEFE0000, "wrong metadata handoff address")
 ASSERT(. <= 0xFEFE1000, "prototype exceeds reserved padding")
 ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "runtime storage unsupported")
}
