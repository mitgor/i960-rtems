# CHIP-8 on AcceleRAID 160 — accepted reusable play, 2026-10-18

Build **g8** passed four games and three restarts on boot
`6b1199a3-8fe8-4aad-abe7-e0fa1649c01f`. The guest is stopped in reusable RTEMS
idle; the owning process and DMA resources remain pinned. Use root `./chip8`
or click Start new game at <http://192.168.2.75:8096/>. See
[commands](../../../chip8_commands.md).

## Physical results

* **7,123 frames** independently replayed against the unchanged C8G1 core.
  Every compact DMA allocation guard, eight-word completion marker, payload
  hash and input/clock trace passed, both online and in offline replay.
* **128 full paired PIO comparisons** (32 per game), with unused source tails
  checked zero. Full system/arena/ownership audits stayed enabled.
* **98 cumulative consumed input events**, FIFO depth 16, down/up and brief
  batches, stale-game rejection, and STOP while video credits were withheld.
* Four guest STOP/idle audits and three fresh guest admissions passed without
  rebooting. The GUI also started/stopped game 4 and sent arrow-key movement.
* A **3.004-second paused host** left both guarded 12 KiB DMA destinations
  unchanged. RTEMS resumed safely. The gateway intentionally failed closed on
  its two-second owner HTTP timeout; an explicit launch command restarted only
  the gateway against the same verified owner. Refresh reconnects the browser.
* Both guarded 1 MiB pre-run flash reads match accepted SHA-256
  `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
  No firmware write was issued.

`g8-card-summary.json`, `g8-card-replay.json`, `g8-card-evidence.tar.gz` and
`g8-owner-status.txt` preserve the result and exact boundary. The immutable
builder's `hardware_tested:false` records its offline creation state; physical
acceptance is recorded separately in the summary and this document.

## Performance and scope

| Measurement | Result |
| --- | --- |
| Scripted LAN WebSocket delivery, 150 received frames per game | 48.09 / 47.75 / 47.02 FPS |
| Key submission to received frame showing changed key state | 29.83 / 31.34 / 38.70 ms median |
| Maximum observed key-state latency per game | 80.12 / 88.38 / 65.36 ms |
| Actual in-app browser display, longer game 4 observation | about 52 FPS |
| Steady card cadence in games 3 and 4 | 60 Hz |

The LAN latency excludes browser paint and is not a measurement of visible
spaceship movement. The timer uses 10 ms RTEMS ticks and bounded elapsed-time
catch-up. Guest speed stays 500 instructions/s. This is an original CHIP-8
dialect, with displayed sound timer but no audio. No matched comparison with
the physically removed DAC960 was possible; no old/new FPS multiplier is claimed.

The 512-byte DMA payload is 128× smaller than Doom's 65536-byte payload; the
12288-byte complete capture is 6.33× smaller than Doom's 77824-byte capture.
These are byte reductions, not FPS gains. Two internal 64 KiB source slots and
the inherited exclusive arena remain reserved. The shared Doom gateway's
constructor defaults preserve its existing behavior; installed Doom launchers
and binaries were not replaced.

**Limits:** global SIGTERM/shutdown and an intentionally expired card-side
transport timeout were not run in this accepted reusable batch. Guest STOP,
stalled-video STOP and three-second host backpressure were run. Global shutdown
remains terminal and requires resetting the PC; it must not be advertised as a
reusable game Stop. Cold-start provisioning still requires a genuinely fresh
host boot when another terminal session owns the card. The final PC power-off
investigation remains separate work.

## Evidence and reproduction

* `g8-build.tar.gz`: exact kernel/image, modules, ROM/data image, manifests,
  compact DMA source, generated resident/host code and CHIP-8 sources.
  Remaining base project files are identified by the complete bundle inventory
  and repository source. Remote bundle:
  `/home/mit/i960-chip8-upgrade-20261018/build-g8/bundle`.
* `g8-card-evidence.tar.gz`: complete four-game captures, input/frame journals,
  full system audit records, firmware reads, three-second pause captures and
  transport journal. `browser-card.png` shows the actual game before STOP.
* `g8-card-stream.json` / `g8-card-client.txt`: scripted input/video timings and
  lifecycle results. `card_client.py` leaves the guest idle after testing.
* `native-core.txt`, `native-replay.txt`, `native-stream.txt`,
  `native-timing.json`, `client-native-regression.json`: exhaustive core,
  bounded player, independent replay, gateway/input/lifecycle and native timing
  tests. Native timing was 60.07 FPS / 20.12 ms median; it is not card performance.
* `profile-generation.txt`, `rearm-policy.txt`, `doom-gateway-regression.txt`:
  strict source generation, actual generated wait/commit ASan/UBSan
  normal/STOP/timeout fixture, Linux32 rearm policy, and shared gateway regression.
* `g6-*` / `g7-*`: failed-batch evidence, summaries and offline replays retained
  to explain the two fixes. G6 accepted 96 frames, then rejected leftover Doom
  WAD admission. G7 accepted 338+202 frames; first rearm passed, second STOP
  exposed a counter committed before DMA slot ownership. G8 removes the WAD
  command, uses explicit global STOP, and commits the counter after ownership.
  Strict captured-frame equality and all audits remain. No intermediate
  candidate kernels besides the final g8 build are archived here.

Offline replay (anonymous seekable spool, bounded memory, no path extraction):

```sh
PYTHONPATH=game/chip8:game/chip8/stream python3 game/chip8/stream/replay.py \
 artifacts/current/chip8-stream-20261018/g8-card-evidence.tar.gz
python3 game/chip8/accele160/test_generate.py
```

A modified actual card pixel was rejected by independent native replay.
The native suite additionally rejects 11 state/input/budget/trace mutations.
