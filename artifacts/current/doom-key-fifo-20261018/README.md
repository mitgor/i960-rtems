# Bounded card keyboard FIFO — 2026-10-18

Eight fresh games passed on the AcceleRAID 160 in one reusable RTEMS session:
**3,073 fully audited frames, 256 independent paired PIO/DMA comparisons**,
seven rearms and forty stale/invalid rearm rejections. The owner stopped cleanly
in global QUIE. Two full post-reset guarded firmware reads match the accepted image, with
zero guard changes/status/residual. `verification.json` reports
`post_reset_flash_pair=true`. No firmware was written.

Candidate on Linux: `/home/mit/i960-key-fifo-20261018/bundle`.
Explicit launcher: `/home/mit/.local/bin/i960-doom-key-fifo`.
Kernel SHA-256: `8f3b61c3100f96b9eee24d3487bc53553982e4f22c9fb11a2e9abdeb6ce7f185`.
The admitted engine, WAD, DMA pin module, seven fixed arena allocations and
existing hardware ownership/audit paths are unchanged. Kernel build records
`keyboard_fifo_schema=1`. The new kernel also supports mailbox mode, so both
paths can be measured without changing the engine or kernel.

## Protocol and lifetime

The borrowed control page reserves host offset **0xe80..0xfff**, card address
**0xc000fe80..0xc000ffff**: 64-byte header, sixteen 16-byte descriptors, then
64 bytes of guards. Frame timestamps end at 0xe80; DMA state ends at 0xe00.
No new card or host DMA allocation is introduced.

Each descriptor carries global sequence, game run ID, encoded key event and
inverted sequence. The single owning host thread validates free space, writes
every descriptor with exact PCI readback, updates the producer mirror, then
publishes the tail **last**. Only the owning RTEMS Init task consumes entries,
in the existing `DG_GetKey()` checkpoint. It verifies bounds, sequence, run,
event and guards before copying the event and publishing ACK last, with i960
`syncf` ordering. IRQ handlers do not prepare, check or drain keyboard queues.

The sixteen-word header is magic `KBF1`, bridge epoch, version, capacity,
published sequence, ACK cursor, discarded count, run ID, error, high-water depth,
last consumption tick/frame/event, consumed count, mode and inverted magic.
The ACK cursor counts consumed **plus explicitly discarded** entries. Counters
remain monotonic across fresh images and cannot wrap. Capacity is sixteen in
FIFO mode and one in mailbox mode. A full producer refuses to overwrite entries;
the browser's existing bounded queue provides backpressure. Invalid card-side
metadata fails closed and retains ownership.

Mode selection is accepted only while idle for the next game, and latched at
fresh engine entry with an empty transport. STOP may leave a bounded tail of
unconsumed input. All pending descriptors must validate before full rearm audits;
only committed rearm classifies them as discarded. A rejected rearm cannot
change counters or admission. Fresh games cannot consume an old run's events.

The persistent browser gateway also accepts a bounded ordered batch of up to
sixteen key transitions. Both mailbox and FIFO comparisons use that same path.
The acceptance-only `--keyboard-selftest` arms an authenticated `/keys-stop`
probe: it publishes a complete sixteen-entry batch and requests STOP immediately
after commit. It is disabled on ordinary launches and cannot write arbitrary
memory. The next admission must account for every pending old-game entry.

## Native checks and physical comparison

- Actual C consumer under native and 32-bit ASan/UBSan: **80,000 ordered
  events**, ring wraps, full refusal, unpublished descriptor isolation, every
  header/guard/descriptor mutation, stale run, pending-input retirement, mode
  transition and sequence exhaustion.
- Actual Python producer: exact descriptor layout, descriptors-before-tail,
  full/invalid/wrap refusal, quiescent mode changes and stale pending audit.
- Actual rearm functions under 32-bit ASan/UBSan: all existing IRQ/cache/heap/
  DMA/ACK/WAD/terminal gates plus sixteen pending entries, rejected corrupt
  descriptor without mutation, and explicit discard on committed rearm.
- Browser/gateway: active/stale mode rejection, atomic bounded batches, disabled
  test probe, balanced STOP probe, authentication, ordered persistent messages,
  disconnect releases, display credits and stale generations.

Reproduce on a fresh boot: launch the candidate with `--keyboard-mode fifo
--keyboard-selftest --paired-frames 32`, start the updated gateway, then run
`stream/benchmark_fifo.py`. Tested predeclared order: **FIFO / mailbox / mailbox /
FIFO** in the same RTEMS instance. Each mode gets a freshly admitted engine,
32 full PIO comparisons and all existing every-frame/system/ownership audits.
Wait through frame 40 before testing. Measure eight lone F6 pulses, eight
two-pulse bursts and six eight-pulse bursts per run through pushed frames.
The first FIFO game ends with the full-ring STOP probe; the following fresh
game must prove discard conservation and zero inherited mode switches.

A lone first press still waits for Doom's next input scan and renderer.
Do not promise a first-key or card-FPS gain from batching alone. Report single
presses and burst tail latency separately, and do not call receipt timing
browser paint/input-to-photon latency. Keep mailbox mode available for matched
comparisons. First 32 captures are now retained **per game**, not merely for
the first global frame range, so repeated admissions keep their paired evidence.

Current sources: `rtems/accele160/doom_dma/key_fifo.{h,py}`, `app.c`, bridge,
browser and manifest/build integration; `game/doom/play/accele160/stream/benchmark_fifo.py`.

## Measured results

Mac → persistent input WebSocket → owning host → card → audited pushed frame.
All runs use the same kernel and admitted engine; only keyboard transport mode
changes. These are **send-to-received-frame** measurements, not browser paint
or input-to-photon latency. The viewport is the stationary E1M1 spawn. A pulse
is F6 down/up; a burst completes when the final expected mode switch arrives.
Even bursts restore textured rendering. Measurements begin after frame 40,
excluding the initial 32 paired PIO comparisons. Full audits continue throughout.

| Probe | Mailbox median | FIFO median | Change |
| --- | ---: | ---: | ---: |
| Two-pulse burst, 16 trials per mode | 204.84 ms | 144.70 ms | 29.4% less latency |
| Eight-pulse burst, 12 trials per mode | 816.67 ms | 452.79 ms | 44.6% less latency |
| Longer single-press ABBA, 64 trials per mode | 113.55 ms | 108.26 ms | 4.7% less; broadly unchanged |

The first shorter single-press sample went the opposite way: **100.23 →
110.36 ms** (16 trials per mode). We therefore ran another FIFO/mailbox/mailbox/
FIFO sequence with 32 singles per game and deterministic phase-varied cooldowns.
Its per-run medians were FIFO 103.98/118.36 ms and mailbox 120.68/110.03 ms.
This does **not** establish a reliable first-key speedup. Longer-sample received
FPS was **19.69 mailbox / 19.75 FIFO**; no renderer/FPS improvement is claimed.
The FIFO usefully reduces the tail of queued input, without changing quality.

The first full-ring STOP left exactly sixteen committed entries unconsumed.
The next rearm validated and classified all sixteen as discarded. End-of-batch
counters were **848 published = 832 consumed + 16 discarded**, with zero pending.
Every fresh engine started with zero inherited F6 switches. Per-game depth never
exceeded sixteen (one in mailbox mode); descriptors were never overwritten.
The ordinary launcher disables the acceptance-only full-ring STOP endpoint.

## What still limits latency

`i_input.c:I_GetEvent()` breaks its drain loop after a key-up event, so even
with a FIFO, successive pulses still span multiple engine input scans. This
explains why eight pulses still take about 453 ms. A future bounded input-drain
experiment should keep ordering and cap work per tic; do not just remove limits.

The persistent engine calls `doom_platform_startup(0)` and remains in virtual
clock mode. Its outer `DG_SleepMs(29)` advances **virtual time**, calling the
safety checkpoint, rather than sleeping 29 ms on the wall clock. The older
backlog suggestion to reduce a real 29 ms sleep is therefore inaccurate for this
path. Separating deterministic startup timing from live-play pacing is a separate
engine experiment, with native determinism and STOP tests. Neither engine behavior
was changed to make the FIFO comparison look better.

## Evidence and replay

- `build-evidence.tar.xz`: exact tested kernel/ELF/map/symbols/build record,
  owning bundle sources and complete bundle hash inventory. Unchanged engine,
  modules and other inputs resolve against `accele160-flat-20261018/acceptance-pre-reset.tar.xz`;
  WAD resolves against the single retained Freedoom upstream archive.
- `card-evidence-final.tar.xz`: eight game journals, all 3,073 frame receipts,
  266 retained guarded captures, all first 32 captures **per game**, keyboard
  publication/ACK journals, idle/STOP/rearm pages, native WAD request receipts,
  final global audit and exact gateway journal. Repeated PGM previews and duplicate
  ROM bytes are omitted; canonical firmware remains in the existing artifact.
- `mac-abba/`, `mac-single-abba/`: raw client trials and every observed frame hash.
  `measurement-client.tar.xz` preserves the exact client scripts, including the
  longer phase-varied single-press experiment.
- `verify.py`, `verification.json`: resolve all **204** pinned bundle members,
  check captures/guards/markers, WAD source hashes and all **5,043 native startup
  requests per game**, 2,663 gateway payloads and 2,648 client-frame identities,
  counters, stale requests, pending retirement and reset firmware reads. All
  **256** first-32 card images match the existing native-qualified textured
  baseline pixels/palette exactly; its four known native/card pixel differences
  are not reclassified as new FIFO differences. Six deliberate frame/hash/
  sequence/run/guard mutations must be rejected.

```sh
python3 artifacts/current/doom-key-fifo-20261018/verify.py
```

The test runner injects input and owns the browser controller: run it only when
nobody is playing. Retained DMA resources remain reboot-only after **global**
shutdown; ordinary game STOP/Quit still parks for safe reusable restart.

## Ordinary launch and rollback

`./doom` now uses this accepted FIFO-enabled kernel through the existing
flat-enabled reusable wrapper and pushed-frame gateway. Textured is still the
initial mode; F6 switches flat floors/ceilings. Open http://192.168.2.75:8088/.
Game Stop/Quit parks for another `./doom`/Start new game; `./doom shutdown`
is terminal and needs a PC reset. Ordinary sessions do not enable keyboard selftest.

On a **fresh hardware session**, `./doom --keyboard-mode mailbox` selects the
comparison mailbox in the same kernel. Launch flags do not reconfigure an
already running daemon; the authenticated idle-only `/keyboard-mode` endpoint
used by the test runner chooses the next game instead. Never replace an active
owner or adopt retained modules to switch bundles. The pre-FIFO core wrapper is
preserved at `/home/mit/i960-doom-stream-20261018/owner-launcher-pre-fifo`; restore
it only on a fresh session and regenerate the gateway identity manifest.

`post-0`/`post-1` contain the closing guarded-read records and symlinks to the
single canonical full ROM. The same approach closes the preceding flat batch
without storing extra identical firmware binaries.

The installed default was then exercised on the next boot with selftest **off**:
ordinary `./doom --paired-frames 32`, eight F6 pulses through pushed frames, and
ordinary `./doom stop` passed. This adds **168 audited frames and 32 paired PIO
comparisons**. Its `/keys-stop` request was rejected with HTTP 409 as required.
The game is parked in live reusable idle on port 8088. `production-smoke.json`
and `.tar.xz` retain that check; it is a deployment smoke test, not another matched
performance comparison. `deployment.tar.xz` holds the exact installed gateway,
identity manifest and new/previous core wrappers; the verifier resolves its
unchanged dependency against the already retained pinned wheel.
