ENTRY(_start)
SECTIONS {
  . = 0xc0fac180;
  .text : { *(.text*) }
  ASSERT(_start == 0xc0fac180, "unexpected probe base")
  ASSERT(SIZEOF(.text) <= 128, "probe exceeds fixed scratch window")
  ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "probe needs no runtime storage")
}
