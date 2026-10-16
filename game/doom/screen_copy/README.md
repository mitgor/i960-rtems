# Fixed indexed-screen presentation copy

Private platform builds specialize the CMAP256 320×200, scale-one path in
`I_FinishUpdate`: one exact 64,000-byte copy replaces 200 generic row copies.
Aligned buffers use four unrolled 32-bit words per iteration. Unaligned buffers
use bytes; other geometry/scaling retains the original implementation. The
source header hash and exact source patches are recorded in the engine manifest.

This retains the persistent `I_VideoBuffer`. Doom caches `ylookup` row pointers
into it, updates portions of the display incrementally, and owns its lifetime
through the zone allocator. Delivery slots rotate separately and may be pinned
by DMA. Simply aliasing/rotating the persistent screen into those slots could
write a pinned frame or lose unchanged HUD/menu pixels. True zero-copy requires
a separately qualified rendering/state/ownership redesign; it is not enabled.

The copy writes only pixels 0–63999; the palette and diagnostic trailers retain
their existing writers. Slot acquisition, exact ACK, DMA1 coordination, STOP,
full guard scans and paired system audits are unchanged.

Run `python3 game/doom/screen_copy/test.py` for ASan/UBSan exact-edge tests across
all pointer alignments. Native engine repeatability and physical controlled
frames provide integration evidence. See
[card results and reproduction](../../../artifacts/notes/screen-copy-20261015.md).
