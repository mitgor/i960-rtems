ENTRY(_start)
stock_complete = 0xc004bad0;
SECTIONS {
  . = 0xc0fac100;
  .text : { *(.text*) }
  ASSERT(_start == 0xc0fac100, "unexpected stub base")
  ASSERT(SIZEOF(.text) <= 20, "stub exceeds handoff allocation")
  ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "stub needs no runtime storage")
}
