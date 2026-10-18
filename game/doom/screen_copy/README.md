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

## Opt-in 8-byte copy on the cached AcceleRAID

`game/doom/build.py --wide-screen-copy` selects [wide.h](wide.h) for private
play builds. It uses paired 8-byte i960 loads/stores when both pointers are
8-byte aligned; the exact 4-byte and byte paths remain for other alignments.
The source remains Doom's persistent screen, and the destination remains the
owned rotating delivery slot. No DMA, framebuffer geometry or redraw ownership
changes. The pinned compiler emits `ldl`/`stl` for the fast path.

Two bounded 32-frame runs on the cached AcceleRAID reproduced 17.593 card FPS
versus the accepted 16.964 baseline, with the presentation-copy phase falling
from 6.5 to 3.0 ms/frame in frames 12–31. Every delivered pixel/palette block
matched; host sanitizer, native play, full system/ownership/DMA/WAD/HTTP,
stalled-host and STOP checks passed. The 10 ms phase clock and short steady
window limit the precision. Keep this option scoped to tested exclusive Doom
builds; do not infer safe zero-copy or old-card behavior. [Exact captures and
flash-audit status](../../../artifacts/current/wide-screen-copy-20261018/README.md).
