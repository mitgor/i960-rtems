# AcceleRAID 160: first real Doom frame gate

**Latest bounded result (2026-10-17):** the four-owner RTEMS build completed
two matched 32-frame Doom runs, full bank/arena/owner and STOP checks, and
measured 3.660 card-side FPS in each. The variable startup stall was same-owner
timer ISR reentry inside `_Thread_Dispatch`, not a WAD-offset fault. The
reentry path counts and returns without overwriting the active continuation;
10 and 11 events were observed, with zero owner faults. Both runs had paired
pre-run full flash audits, and the first run had paired post-reset reads. The
final post-second-run pair also passed after reset, matching the unchanged
stock firmware SHA-256 with clean guard, status and residual fields.
[Exact forensic trace, binaries, frames
and replay](../../../artifacts/current/accele160-doom-startup-20261017/README.md).
Interactive controls and ping-pong host DMA have not been ported to this card.
The 29-page test image now owns four 8 KiB ISR continuations, including RTEMS
idle; firmware and the 8 MiB Doom arena are unchanged.

**First-frame gate passed on the third run:** 5,043 engine WAD reads matched
the native request trace, one real 320×200 Doom frame was read back in 16
checked pages, and engine-owned exit, all arena loans, executable text,
timer/STOP and old-card isolation passed. Engine entry to first frame took
123.54 seconds. The retained session was reset; two guarded complete post-reset flash reads passed on boot `c9773c0f-9b64-414b-8712-4d9e6bf1ae5e`. [Exact image, frame and evidence](../../../artifacts/current/accele160-doom-first-frame-20261017/README.md).
This is not sustained play or a measured FPS.

This builds on the [accepted full-WAD service](../doom_wad_service/README.md).
The card at `0000:37:09.1` admits the same pinned Doom engine into the
verified 8 MiB upper bank, then calls its owned entry once from an RTEMS
task. A guarded 6 MiB zone, checked 4 KiB WAD cache, 64 KiB framebuffer,
bounded read callbacks, STOP and timer ownership remain in force. The old
DAC960PG at `0000:37:04.1` must stay unbound. This is a RAM-only test; the
stock firmware callback and grant stay retained until whole-card reset.

`app.c` supplies the engine's allocation, file, clock, owner, wait, STOP and
frame-mark callbacks. The card publishes each exact WAD request; the host
provides the immutable file slice, and the card checks sequence, bounds,
length and FNV before and after copying. Any post-copy checksum failure
quarantines the card session. The first real frame, if reached, is copied into
the guarded frame allocation, read back in 16 checked pages, and must cause
the engine to leave through its owned 210 boundary. All engine loans must be
released and its executable text hash must remain unchanged before STOP.

The first two physical engine attempts **did not produce a game frame**.
The first monitor initially mishandled the uninitialized engine-report
sentinel, leaving the host absent for the first WAD request; its 500-tick
timeout worked. The corrected monitor then served 1,401 actual engine
requests, with the first 1,400 recorded requests matching the native trace,
but the engine made no further progress. After reset, an instrumented run
served 3,801 requests, all matching the native trace, then made no WAD or
frame progress for 120 seconds. Host STOP was published; Doom did not reach
a cooperative STOP point. Those runs were diagnostic failures. Exact
captures and post-reset audits are in
[the artifact](../../../artifacts/current/accele160-doom-first-frame-20261017/README.md).

The current source adds a read counter and a grant-owned interrupt sample
ring at `c0772000`. The ISR records the interrupted return address without
changing the hardware frame. The host saves the ring if WAD/frame progress
stalls for 120 seconds, then publishes STOP. If STOP cannot be handled, keep
the module and grant retained until whole-PC reset. Do not unload them.

Build against the pinned new-card RTEMS library and i960 toolchain:

```sh
rtems/accele160/doom_first_frame/build.sh \
  /home/mit/i960-accele160-rtems-20261017/accele160 \
  /home/mit/i960/tools/bin OUT_DIR
```

The runner requires explicit exact module, handler, firmware, image, WAD,
template, relocation and two same-boot guarded full-flash read paths. It
refuses a changed identity, wrong BDF, bound old card, active stock
descriptor, block device or stale owner. The current binary hashes in
`run_bridge.py` must match the exact rebuild; do not substitute a new binary
without updating and reviewing those gates. No firmware write is issued.

Next: add bounded repeated frames, input and host presentation. Keep the same native
WAD request oracle, ownership/arena/frame audits, and reset-only release.

## Bounded render-FPS gate (2026-10-17, in progress)

`DOOM_FPS_FRAMES=32 build.sh ...` produces a separate RTEMS image that lets the
same admitted Doom engine present exactly 32 frames. The card records its 100 Hz
timer at each `stage=100` boundary and exits through the existing owned 210
cleanup on frame 32. The final 65,536-byte frame contains the 32 timestamp
words at byte offset 64,768, outside its 320×200 pixels and 768-byte palette.
The host checks each 4 KiB readback page, the final pixel/palette hashes,
monotonic timestamps, engine cleanup, arena guards, full bank/ownership audit,
STOP and old-card isolation. FPS is `(31 * 100) / (tick[31] - tick[0])`;
the preceding WAD startup is excluded. This is **card-side frame-boundary FPS**,
not browser delivery FPS. The one-frame default remains available.

The exact 32-frame build hashes are pinned in `fps-32-manifest.json`. On the
test PC, `run_fps32.sh PROJECT_ROOT BUILD_DIR NEW_OUTPUT_DIR READBACK0 READBACK1` supplies only the
accepted module, handler, WAD and engine paths. It requires two guarded 1 MiB
same-boot flash reads before touching the card. A retained test module and
grant are released only by whole-PC reset; never unload them after an uncertain
run. Three 32-frame attempts stalled during startup after 1,301, 4,809 and 79
WAD reads, respectively, before any frame timing. Each completed request
sequence matches the native oracle prefix. The 120-second idle timeout saved
the page and published STOP each time. The retained callback/grant were
released by whole-PC reset, never module unload. On a new boot, load the
preserved driver with `read_bdf=0000:37:09.1`; the parameter is mandatory.
The interrupt sample page read back as all `ff` even after correcting the
PIATVR page selection, so it does not locate the stall. Obtain a reliable
live task/ISR trace before treating startup as stable.

This gate uses the same pinned Doom engine as the accepted first frame. The
startup stall was localized to same-owner timer ISR reentry inside RTEMS
dispatch and fixed with a counted no-dispatch nested path. Two matched
unchanged-image runs each completed 5,045 WAD reads and 32 frames, with
identical pixels/palette and 847 ticks over 31 intervals: **3.660 card-side
FPS**. Both passed full pre/post-reset paired flash, ownership, bank, STOP and
quiescence audits.
This number excludes WAD startup and browser delivery. See the
[exact trace and replay](../../../artifacts/current/accele160-doom-startup-20261017/README.md).
Building the qualified exact renderer options
(`--fast-render --fast-columns`, bounded FixedDiv, direct frame, no play-mode
FNV) and a delivery-FPS test remain separate follow-ups. Quality-reducing
flat planes, half height and low detail stay off for the normal-quality run.

For a fresh run, copy the pinned `native-requests.bin` oracle from
`artifacts/current/accele160-doom-first-frame-20261017/` into the isolated
project's `doom_first_frame/` directory. Rebuild with
`DOOM_FPS_FRAMES=32`, verify the source and image hashes in the manifest,
load `myrsread.ko read_bdf=0000:37:09.1`, and obtain two fresh same-boot
guarded full-flash reads. `run_fps32.sh` requires their directory paths.

## Route to interactive play on this card

1. The variable startup stall is fixed, two 32-frame normal-quality runs
   agree, and all paired pre/post-reset flash audits passed. Preserve the
   exact accepted image as the render baseline.
2. Add a separate interactive build, with bounded keyboard-event replay and
   a longer matched render window. Keep the accepted baseline binary pinned
   while changing the session path.
3. Replace the one-shot final-frame copy with owned, generation-numbered frame slots
   and an ACK/STOP protocol. Coordinate WAD requests and frame transfer under
   the same DMA ownership; a stalled/disconnected host must not recycle a
   pinned slot or free the grant.
4. Add bounded keyboard events, focus-loss key release, binary browser frame
   delivery and a persistent session. Report render FPS, host-delivered FPS
   and latency separately. Port the old card's exact optimizations in a
   second matched build; leave optional quality reductions off.

The old DAC960PG already has the persistent RTEMS Doom session, keyboard,
WAD ring, ping-pong frame DMA and browser play. The AcceleRAID currently has
the stock firmware's retained operation-13 callback, a verified exclusive
8 MiB upper-bank arena, a single admitted Doom entry, and checked 4 KiB
WAD/frame sideband transfers. These are distinct transports and ownership
contracts; old-card FPS figures do not predict the new card's performance.
