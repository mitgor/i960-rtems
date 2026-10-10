ENTRY(_start)
SECTIONS {
 . = 0xc0fac180;
 .text : { *(.text*) }
 ASSERT(SIZEOF(.text) <= 128, "runner overflow")
 ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "runner must be stateless")
}
