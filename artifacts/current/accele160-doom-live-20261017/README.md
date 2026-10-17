# AcceleRAID live Doom frame transport

The accepted baseline is `../accele160-doom-startup-20261017/`: two unchanged
32-frame runs at 3.660 card-side FPS with full paired flash, owner, arena,
STOP and bank audits. This is a separate RAM-only transport experiment. The
old DAC960PG remains unbound; no firmware write has been made.

`fail0/` records the first live two-slot attempt on boot
`d3cd3a69-fc5d-4be6-9278-e0942448a484`. It passed the same native startup
oracle through all 5,043 reads and published two frame generations, then the
host rejected the first frame's FNV and withheld ACK. The card's finite
500-tick wait ended after three render callbacks. Because the prototype's
early-STOP path was incomplete, it entered the claimed fatal quarantine
(`0xf007700a`); the grant was released only by whole-PC reset. The capture
includes the control page, both raw slot images, complete request/trace logs,
and two independent PCI read attempts. No valid host frame or FPS is claimed.

Cause: PIATVR exposes only the **odd 4 KiB page in each 8 KiB pair**. The
first build stored each 64 KiB frame contiguously; a direct PCI read repeated
or overlaid the inaccessible even-page portions. The first pixels could look
plausible, but the full FNV could never match. The next build stages each
frame in 16 owned odd pages, one 4 KiB chunk per 8 KiB pair. It retains two
separate generations and requires the host to verify every reconstructed
64 KiB frame before ACK. The host failure path now sends exact STOP and saves
its quiescence result.

The corrected odd-page build passed a 32-frame physical run on boot
`907fcb39-d8c8-410a-a8c8-29d14fa02bd0e`. It completed 5,045 WAD reads,
matched the 5,043-request native startup oracle, reconstructed and checked
all 32 frame payloads, ACKed 16 generations per slot, then passed exact STOP,
full bank/arena/owner checks, and quiescence. Paired full READIMAGE audits
before and after the run all matched stock SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`;
the old card stayed unbound. `python3 verify.py` replays the captured bytes,
timing, oracle and audits. The card-side frame interval was 1,331 ticks for
31 intervals at 100 Hz, or **2.329 FPS**. This includes card-side staging and
host ACK; it is not browser-delivered FPS. The earlier render-only baseline
was 3.660 FPS. Exact accepted source, image, kernel, receipts and 32 frames
are in `accepted-1/`.

`rtems/accele160/doom_play/browser.py` and `index.html` expose binary frame
packets, bounded keyboard events and STOP while the sole card owner performs
PCI access. The separate `browser-1/` physical run captured **all 32 HTTP
frames** and compared their payloads byte-for-byte with the checked card
captures. The scripted W-key press and release reached the stage-101 mailbox;
the card's final key sequence and ACK both equal two. Full WAD, owner, bank,
arena, cleanup and STOP checks passed, with **2.320 card-side FPS**. Both
paired pre-run and post-reset full flash reads matched stock with zero status,
residual and guard changes; the old card stayed unbound. `verify_browser.py`
replays the HTTP/card bytes, key acknowledgments, native WAD oracle and all
four flash read receipts.
The [HTTP frame 32 screenshot](browser-1/http/frame-0032.png) is derived from
the exact binary packet.

This bounded 32-frame session is a transport/input qualification, not yet a
long playable session. DMA, long-session STOP acceptance, delivered-FPS
measurement and old/new delivered-FPS comparisons remain open.
