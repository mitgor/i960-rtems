ENTRY(_start)
SECTIONS {
  . = 0xc0fac180;
  .text : { *(.text*) }
  ASSERT(_start == 0xc0fac180, "unexpected stub base")
  ASSERT(SIZEOF(.text) <= 64, "stub exceeds fixed scratch window")
  ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "stub needs no runtime storage")
}
