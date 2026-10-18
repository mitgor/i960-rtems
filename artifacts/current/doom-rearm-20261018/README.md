# Reusable RTEMS idle/rearm candidate — 2026-10-18

**Repeated card STOP/Quit/rearm passed:** three games ran in one RTEMS
instance and owning host process on boot
`f95c315b-33b1-4dd3-9f89-aacac7280f7f`. The final paired post-reset stock-flash
reads are still pending. The installed launcher remains unchanged until that
closure. See `card-replay.json` and `verify_card.py` for the physical proof.

| Game | Exit | Frames | WAD reads | Entry to first frame |
| --- | --- | ---: | ---: | ---: |
| 1 | Owned STOP | 65 | 5,045 | 73.86 s |
| 2 | Doom F10/Y menu Quit | 43 | 5,047 | 73.58 s |
| 3 | Owned STOP | 65 | 5,045 | 73.65 s |

Both image reloads succeeded without PC reset, arena initialization, new DMA
mappings or a firmware write. Global generations ran 1–65, 66–108 and
109–173. Source-slot parity followed each engine's local frame index,
including the even global generation 66 using local slot 0. The same pinned
card allocations and coherent host buses (`fff61000`, `fff41000`) survived.

All **173** complete frame captures replay with full guards, native host FNV,
SHA and exact completion/source/generation markers; **96** frames had full
independent PIO comparisons. Every game's first 32 pixel/palette blocks match
the accepted baseline. All **15,137** engine WAD reads replay against the
immutable WAD; each game's first 5,043 requests match the native oracle.
Fifteen independently sampled HTTP payloads also match their DMA receipts.

The kernel rejected **15** stale/invalid rearm requests (old run, wrong
frame/next-run, WAD sequence, key sequence and unacknowledged slot), plus
three attempts to reenter a retired image. Each game passed Init IRQ/stack,
fixed-record/arena/loan, restored-cache, text/relocation, DMA drain/peer,
owner and outside-arena tail audits. Other owned worker IRQ continuations
remained alive between games; their stacks were never cleared. All workers
and IRQ continuations drained on the final planned global STOP.

Menu Quit consumed key sequences 1–3; the outstanding Y-up at sequence **4**
was explicitly recorded as discarded on rearm, then game three started with
transport sequence 4 retained. No old event was injected into the fresh game.
Three stale browser run requests and a restart while running returned HTTP
409 on the live owner; idempotent launcher invocation kept the same PID.
This tests rejection/idempotency, not a positive browser/CLI idle restart.

The measured idle-to-rearm ACK interval was about **0.446 s** each time.
Engine exit to the next first frame was **85.23 / 85.30 s**, including fresh
image upload and cold WAD cache loading. Restart avoids PC reboot but is not
a warm-cache restart. The first 32 frames deliberately use extra PIO auditing;
their timing is not an FPS comparison with ordinary play.

Reproduce the physical replay with:

```sh
python3 artifacts/current/doom-rearm-20261018/verify_card.py
python3 artifacts/current/doom-rearm-20261018/verify_attempt.py
```

`card-acceptance-pre-reset.tar.xz` includes every game, both pre-flash reads,
all command/frame/WAD receipts, idle/rearm/control pages, service log, exact
retry host source/inventory and native oracle. The kernel/engine identities
are unchanged from `candidate.tar.xz`. `retry-host.tar.xz` records the corrected
boundary audit. Remaining gates: final paired post-reset reads, positive
browser/CLI restart after a sustained idle, host loss while idle/uploading,
long repeated play and level transitions. No PM/bus reset or dead-daemon
adoption was attempted.

## Candidate preparation record (before physical acceptance)

The candidate was initially isolated at
`/home/mit/i960-doom-rearm-20261018/bundle-candidate`; the corrected tested
host bundle is `bundle-retry` in the same directory. No firmware write was
issued. The old card remained unbound. The historical preparation snapshot
`status.json` deliberately records that earlier, native-only stage.

The last SSH check still found boot ID
`31291627-dcd0-44bd-9c81-50708c818d80`, the original retained `admit_command`
and `dma_frames`, and an inactive Doom service. Its prior terminal QUIE state
cannot accept a new kernel. A physical power-cycle request is pending.

## What changed

`DOOM_REUSABLE=1` requires a persistent engine and adds an idle/rearm gate
owned by Init. RTEMS, its workers and IRQ stacks, the arena, seven fixed pins,
coherent host mappings and DMA descriptors remain alive between games.
There is no stock-firmware reentry. Global STOP, owner-process death and
failed checks remain reset-only boundaries.

After a clean 210/cleanup return, operation 9 audits the retired engine.
Operation 8 accepts `(expected_run, last_global_frame, last_WAD_request,
next_run, last_key_sequence)` only after all checks pass:

- Empty dynamic allocation slots, no zone loan, all arena guards valid and
  every word of the seven fixed allocation records unchanged.
- Init is outside an engine and IRQ continuation; its IRQ counters balance.
  Every IRQ guard passes. Other workers may retain balanced, owned kernel
  continuations; their stacks and counters are preserved.
- Both frame-slot generations are exactly ACKed, DMA0 hardware is drained,
  its previous descriptor completion remains valid, and DMA1/2 are unchanged.
- WAD is no longer pending, text/relocation metadata match, and the original
  cache map is restored. Host owner, bank-report, untouched-tail, frame and
  coherent-buffer audits also run for each game.

Statuses 40–45 distinguish stale run, invalid lifecycle, frame/next-run,
WAD, key and full-audit rejection. Rejection leaves the old admission retired.
At most one unconsumed old-game key is explicitly discarded and reported in
bridge[23]; it is not represented as engine consumption.

Rearm clears only game adapter state. The host then uploads the original
zero-based template, zero BSS gap and original relocation table. Normal
SHA/geometry admission relocates it once and invalidates the instruction
cache. The arena is never initialized again. Transport counters survive;
local engine frame parity chooses the source slot independently of the
monotonic DMA generation.

The host watchdog also runs in the outer idle/upload loop. The browser has a
Start new game button and run-tagged input/STOP/restart requests. A root-only
control record identifies the existing owner PID and boot; a second launcher
can request restart/stop from that daemon, but cannot adopt retained resources
after daemon death. `shutdown` remains the explicit global STOP action.

## Tests completed

- Cross-compiled the reusable i960 kernel and image; exact hashes are in
  `status.json` and the archived persistent manifest.
- Ran `test_rearm.py` on Linux with 32-bit ASan/UBSan. It compiles the actual
  target rearm/audit functions with mocked MMIO/RTEMS/digest/arena validity.
  Stale run/frame/WAD/key, pending ACK/DMA/WAD, leaked loan/allocation,
  changed fixed pins, IRQ guard/continuation, cache-map, digest and terminal
  STOP rejection passed. A retained peer IRQ continuation is allowed.
  This is a policy test, not a hardware cache/IRQ/DMA proof.
- Browser API tests passed on Mac and Linux: immutable binary frames, keys,
  STOP, idle/restart, stale-game rejection and new-game input reset.
- Existing native DMA descriptor/reuse/peer/error/timeout tests passed.
- Launcher hash-tamper/card-profile tests and Python compilation passed.

The earlier actual Doom/Newlib native STOP → reload/Quit → reload/STOP proof
remains in [the investigation](../doom-reuse-investigation-20261018/README.md).
The Doom engine itself is unchanged from the accepted persistent build.

## Exact next physical gate

After a fresh power cycle, inventory both BDFs, keep the old card unbound,
and close the previous user-play session with two guarded full-flash reads.
Then launch the isolated bundle (not the installed wrapper):

```sh
sudo -n python3 /home/mit/i960-doom-rearm-20261018/bundle-candidate/project/game/doom/play/accele160/launch.py \
  --bundle /home/mit/i960-doom-rearm-20261018/bundle-candidate \
  --port 8087 --max-frames 65 --restart-cycles 3 --quit-game 2 \
  --paired-frames 32 --capture-all
```

The runner repeats STOP → rearm → F10/Y menu Quit → rearm → STOP in one
RTEMS instance and owning process. It checks the first 5,043 native WAD
requests per game, all full DMA captures and guards, 32 complete paired
PIO/DMA frames per game, final frame/text/heap/cache/IRQ/owner checks, retired
entry rejection, stale rearm descriptors and a deliberately stale frame ACK.
It archives each game separately and preserves global command/WAD/key/frame
sequences. These tests are implemented but **have not yet run on the card**.

Next qualify browser/CLI restart from idle, idle heartbeat loss, stalled host
and final global STOP; archive captures before reset and obtain two guarded
post-reset full-flash reads. Keep the default bundle unchanged until physical
acceptance passes. No generic device reset, force-unload or halted-callback
revival is part of this route. WAD cache is rebuilt for each game initially.

Rebuild with `game/doom/play/accele160/build.py --reusable` or reuse the
unchanged accepted engine and compile the kernel with
`DOOM_PERSISTENT=1 DOOM_REUSABLE=1 DOOM_FPS_FRAMES=32`, regenerate its manifest,
then run `provision.py` into a new bundle directory. Full sources, kernel,
manifest, bundle inventory and native test logs are in `candidate.tar.xz`;
WAD, engine and command modules retain their existing accepted identities.

## Follow-up readiness check

On the next test request, SSH still reported the same boot ID and two hours
of uptime. The locked, read-only
[`prelaunch-20261018T1013/result.json`](prelaunch-20261018T1013/result.json)
confirmed terminal QUIE, a heartbeat frozen at 15,733, the previous 1,565 DMA
frames, intact coherent guards and the old card unbound. Its PCI window
selector was restored; no card command or RAM write was issued. This explains
why a fresh admission was not attempted over the retained callback.

The user asked whether a warm reboot could help. A remote `reboot -f` was
issued to try that less disruptive reset; successful reuse testing still
requires a changed Linux boot ID, cleared retained modules and a controller
that passes fresh initialization and both guarded whole-flash reads.

The warm reboot printed `Rebooting.` but repeated SSH connections timed out;
no changed boot ID or controller reinitialization could be verified. Physical
power-off was requested again. The archived v6.8 reader source has a cache
flush in `myrs_remove()`, but **no PCI shutdown callback**, and the generator
does not add one. A driver shutdown-command stall was considered, but the
reviewed source does not support that diagnosis. The actual reboot stall
cause is unproven. No reusable Doom card test has started in this follow-up.

## First physical attempt: clean STOP, host-audit false positive

Boot `05905c4e-1edf-4d19-bad9-3c8e3564ff87` cleared all retained modules.
Both guarded 1 MiB pre-flash reads passed and the old card remained unbound.
The candidate produced **65 frames**, then passed STOP, final-frame, private
heap/zone cleanup, unchanged text, restored cache map and DMA drain checks.
All 65 complete DMA captures replay with exact guards/markers/SHA; the first
32 had full PIO comparisons. Five HTTP samples were independently observed.

Before rearm, the new host audit incorrectly expected the original RAM-test
pattern at page index 1857 (`0xc0f41000`), **inside** an owned staging
allocation. The saved page exactly equals page 8 of paired frame 32, relative
to slot 1's declared staging base `0xc0f31000`. This is legitimate frame data,
not corruption or a failure of the kernel rearm policy. The error path safely
entered terminal QUIE; **no rearm was attempted**. The captures and diagnosis
are retained in `attempt-1.tar.xz`, `tail-audit-diagnosis/`,
`attempt-1-replay.json` and `attempt-1-http/`.

The host check is corrected to all eight accessible odd pages from
`0xc0ff1000` through `0xc0fff000`, outside the `0xc0810000..0xc0ff0000` arena.
Full arena/fixed-record/IRQ/cache/DMA/owner audits remain. Kernel, engine and
firmware are unchanged. The new isolated bundle is
`/home/mit/i960-doom-rearm-20261018/bundle-retry`; use the same acceptance
command with that bundle/path. Another initial physical reset is pending
because the failed attempt correctly stopped the owning daemon and kernel.
The installed bundle remains unchanged.
