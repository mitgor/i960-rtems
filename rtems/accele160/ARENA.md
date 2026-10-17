# AcceleRAID 160 upper-bank arena and reboot-only ownership

The [2026-10-17 Doom WAD-service test](../../artifacts/current/accele160-doom-wad-service-20261017/README.md)
extended the arena claim to arbitrary stable residual upper-bank contents.
It saves each of 2,048 marker preimages and each complete page into the
owned grant while doing the full reversible marker/alias/pattern/read/restore
proof, then verifies the original whole-bank hash. A failed restore
quarantines the callback. Four guarded allocations (engine, zone, frame,
4 KiB WAD cache), STOP and post-reset flash acceptance passed. This does
not make the arena safe for concurrent stock firmware use or eliminate the
reboot-only release rule below.

The new card at `0000:37:09.1` has a physically verified, distinct 8 MiB
upper-bank extent at `c0800000..c0ffffff`. This is **not** part of the stock
allocator's grant table. It becomes an application arena only while the
operation-13 firmware callback is held by a validated, exclusive RTEMS image.
Returning to stock after overwriting the bank is forbidden; card reset is the
release boundary. The old DAC960PG at `0000:37:04.1` stayed unbound and was
not touched.

The [exact source and captures](../../artifacts/current/accele160-fullbank-20261017/README.md)
record the progression:

1. `arena_probe/` required the whole bank to be zero and rejected safely on
   the first populated word, before any upper-bank write. Its recovery script
   restored the completed command, grant and all loader controls. Paired full
   flash reads passed.
2. `arena_census/` read every 32-bit word. Only pages 2042 (`c0ffa000`) and
   2046 (`c0ffe000`) were nonzero: 53 words total. `arena_pages/` copied those
   two exact pages to owned scratch without changing the sources. The first
   holds the values 1–31 at 32-byte intervals plus `ffff0020`; the second
   holds an 8 MiB size word and a power-of-two table. All 1,024 odd pages
   accessible through BAR0 were zero. These are observed boot patterns; their
   firmware purpose is not fully established.
3. `arena_full/` saved those two pages in owned scratch, refused any unexpected
   bank content or active 80303 DMA channel, then put distinct markers into
   all 2,048 pages at once. It read every marker back, compared a full lower
   8 MiB guard hash, restored the markers, and filled/read/restored every
   4 KiB page. STOP and no-host timeout both passed, including ISR/task drain,
   full loader/owner/stage/scratch restoration and two post-test guarded
   complete flash reads. Both paths returned to stock.
4. `arena_persistent/` repeated that gate, then wrote a deterministic pattern
   across the entire upper bank and kept the operation-13 callback pending.
   The host checked all 1,024 BAR-readable odd pages, the card's full-bank
   hash, an independent timer heartbeat, and an exact STOP acknowledgement.
   STOP left RTEMS quiescent with its grant and command **retained**. The
   callback did not return. A whole-card reset is required; ordinary module
   unload, allocator release, or stock commands are unsafe in that state.

The [Doom bridge test](../../artifacts/current/accele160-doom-bridge-20261017/README.md)
adds a guarded allocator in `c0810000..c0feffff`, exact image relocation
and admission, a sequenced PCI sideband, a checked WAD-header input and a
64 KiB diagnostic framebuffer output. It still does **not** execute Doom
or transfer the full WAD. The prior bank pattern remained after the earlier
reset, while stock firmware changed the first upper pages. The bridge's
card-side preflight therefore saves the first 16 pages and both diagnostic
pages, and requires every other page to match the exact known pattern before
writing. The full-bank reversible/alias checks then pass before permanent
claim. Do not generalize this preimage rule to a different card or boot.

The bridge remains a fixed one-shot image with no general runtime ABI,
independent watchdog, or safe DMA cancellation for a permanently stalled
transaction. Its host transfer is BAR0 page exchange, not card DMA. The
accepted operation-13 command and grant remain pinned through STOP until
reset; the old card stays unbound.

Rebuild a source tree on the pinned remote GCC 3.3.6/i960 toolchain with
`build.sh RTEMS_BUILD_DIR TOOLCHAIN_BIN OUT_DIR`. Each host runner pins image,
kernel, handler, firmware, module hashes and two same-boot guarded full-flash
reads before touching the card. `arena_persistent/run_persistent.py` is an
exclusive test: it deliberately leaves the driver command and RAM grant
retained, even after STOP. Read the source and capture before reuse; never run
it concurrently with RAID, Doom on another card, or another module session.
