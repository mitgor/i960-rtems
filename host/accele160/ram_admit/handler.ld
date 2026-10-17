OUTPUT_ARCH(i960)
ENTRY(dispatch_hook)
stock_completion = 0xc004e940;
stock_unsupported = 0xc0023790;
SECTIONS {
 . = 0xc000e1d8;
 .text : { *(.text*) }
 /DISCARD/ : { *(.data*) *(.bss*) *(.comment*) }
}
/* The stock loader cave is erased from e1d8 through the loader end.  The
 * first host-owned records start at f800.  Keep code below that boundary. */
ASSERT(ADDR(.text) + SIZEOF(.text) <= 0xc000f800,
       "retained handler overlaps result record")
