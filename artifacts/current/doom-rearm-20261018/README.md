# Reusable RTEMS idle/rearm candidate — 2026-10-18

**Implemented and cross-built; physical acceptance is pending the initial
power cycle.** This is not a claim that Doom has already restarted on the
card. The installed `/home/mit/.local/bin/i960-doom` still selects the
accepted `bundle-v2`, which globally halts after a game. The new candidate
is isolated at `/home/mit/i960-doom-rearm-20261018/bundle-candidate`.
No flash write, card command, driver unload or reset was issued in this batch.
The old card was not touched.

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
