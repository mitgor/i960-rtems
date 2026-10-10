ENTRY(_start)
SECTIONS {
  . = 0xc0fac100;
  .text : { *(.text*) }
  ASSERT(_start == 0xc0fac100, "unexpected RAM control base")
  ASSERT(SIZEOF(.text) <= 64, "RAM control exceeds fixed scratch window")
  ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "RAM control needs no runtime storage")
}
