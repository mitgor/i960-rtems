# AcceleRAID 160 Doom admission and transport bridge

This is the exact one-shot RTEMS source for the
[2026-10-17 physical test](../../../artifacts/current/accele160-doom-bridge-20261017/README.md).
It is **not** a Doom launcher. The old DAC960PG must remain unbound.

`build.sh` links the bounded RTEMS image, the repository's guarded arena and
SHA-256 implementation. The host `run_bridge.py` pins the exact image,
firmware, handler, five command modules, card IDs and two same-boot guarded
full-flash reads. It stages 27 image pages through an owned 512 KiB grant,
checks per-page copy receipts and a whole-image card digest, and starts a
retained operation-13 callback. The callback has an owned IRQ stack and
timer, proves the full upper bank, claims it, allocates/pins three guarded
objects and never returns to stock firmware after claim.

The request sideband is the loader page at `c000fb80`, epoch `161610e1`.
The host writes the payload to the odd inbound page at `c078b000`, then
publishes a sequence number last. The card checks epoch, sequence, bounds,
FNV and arena guards; it ACKs last. The outbound page is `c078d000`.
Operations are: 1 ordered 4 KiB image upload, 2 exact WAD-header admission,
3 one 4 KiB diagnostic frame page, 4 exact SHA/relocation image admission.
This path uses BAR0 page exchange, **not DMA**, and moves only the first
512 bytes of the WAD.

The card preflight is intentionally tied to the observed prior pattern. It
backs up the first 16 upper pages and the two stock diagnostic pages into
the grant, requires all other 2,030 pages to match the exact prior pattern,
then marks all 2,048 pages, checks lower-bank alias freedom, fills/reads/
restores every page, and confirms the entire preimage hash. A changed bank
must be investigated; do not bypass this guard to make a run start. The
allocator excludes the first/last 64 KiB of the eight-megabyte bank.

`run_bridge.py` is a full fresh-run harness. `resume_bridge.py` was used
only to continue a retained test after an early *host assertion* and assumes
an untouched bridge with sequence zero. `finish_bridge.py` was used after
another host-only logging failure once all 232 requests had completed. On
an unknown card state, retain the grant/module and capture the page/status;
neither resume helper is a general recovery mechanism. STOP drains workers
and timer but keeps the command/grant pinned until whole-card reset.

`verify_live.py` checks the exact captured identities, 232 ordered receipts,
image geometry, WAD rejection/admission, diagnostic framebuffer bytes,
full-bank/arena/STOP reports and two post-reset flash-read records.
`test_verify_live.py` rejects three altered captures. The pinned remote
GCC 3.3.6/i960 rebuild byte-matches both archived binaries.

The next implementation needs the new board's Doom runtime ABI, full-WAD
read service, bounded entry/STOP boundary and a real-frame oracle. Do not
call the admitted entry directly with this prototype: its callbacks are
unbound and the complete WAD is absent.
