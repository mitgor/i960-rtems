# AcceleRAID Doom live play transport

This is an isolated fork of the accepted 32-frame new-card baseline. It keeps
its RAM-only firmware callback, exact engine/WAD admission, 8 MiB exclusive
arena, four owned timer contexts, full bank audit, old-card isolation and
STOP/quiescence checks. It adds two generation-numbered frame slots and a
single-event key mailbox. The card does not reuse a frame slot until the host
has reconstructed its 16 odd-page chunks, checked its 64 KiB FNV and ACKed
that slot's exact generation. A missing ACK has a 500-tick bound. This is a
bounded transport gate, not an interactive browser session yet.

PIATVR exposes only odd 4 KiB pages. Each slot therefore reserves 17×8 KiB
and stages a contiguous 64 KiB Doom frame as 16 chunks in odd pages. The
host `run_bridge.py` reads those odd pages through BAR0 and checks the FNV
before ACK. The card still owns the contiguous render copy for its final
frame and engine cleanup audit. The two slots are separate arena allocations
from the WAD cache and engine image. The first contiguous-slot attempt failed
its FNV; see the [failure capture](../../../artifacts/current/accele160-doom-live-20261017/README.md).

On the qualified host, build with `DOOM_FPS_FRAMES=32` and the pinned RTEMS
build/toolchain, then record the resulting image SHA/FNV in
`live-32-manifest.json`. `run_live32.sh` requires two guarded full READIMAGE
reads on the same boot, plus the exact old-card-unbound state. It preserves
all accepted upload, WAD, full bank, owner, STOP and stock-firmware checks.
After any retained run, use a whole-PC reset and paired post-reset full flash
reads; never force-unload the retained module.

The first failure is preserved. The odd-page version passed its 32-frame
physical acceptance and paired pre/post flash reads; replay it with
`python3 artifacts/current/accele160-doom-live-20261017/verify.py`. It measured
2.329 card-side FPS, compared with 3.660 render-only baseline FPS. Neither
number is browser-delivered FPS. `browser.py` and `index.html` provide an
optional HTTP/binary-frame/key/STOP endpoint. Its separate physical run
delivered all 32 frames byte-for-byte, acknowledged W press/release on the
card and passed paired pre/post flash plus full runtime audits at 2.320
card-side FPS; replay it with `verify_browser.py` in the evidence directory.
A long-running session, clean user STOP, DMA delivery and old/new delivered-
FPS comparisons remain next gates.
