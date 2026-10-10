ENTRY(_start)
stock_complete = 0xc004bad0;
SECTIONS {
  . = 0xfefe0000;
  .text : { *(.text*) }
  .rodata : { *(.rodata*) *(.rdata*) }
  .data : { *(.data*) }
  .bss : { *(.bss*) *(COMMON) }
  ASSERT(_start == 0xfefe0000, "unexpected metadata entry")
  ASSERT(_ping_handler_end - _ping_handler == 20, "handler copy must be 20 bytes")
  ASSERT(. <= 0xfefe1000, "code exceeds verified zero padding")
  ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "runtime storage unsupported")
}
