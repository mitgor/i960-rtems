# AcceleRAID 160 CHIP-8 profile

The build-g8 **reusable play path passed physical testing**: four games,
three restarts, full FIFO batches and stalled-host ownership. It ports the
CHIP-8 workload into the existing exclusive RTEMS owner. It does not program
firmware or replace the installed Doom launcher.

The unchanged CHIP-8 interpreter runs as a trusted RTEMS builtin. The admitted
image contains a checked guest ROM and data, never native guest instructions.
The generator snapshots the audited Doom resident transport into an isolated
bundle and records exact before/after source hashes. All IRQ, private worker,
cache, ownership, timeout, marker, STOP and reusable-session rules remain.
Source-context drift aborts generation rather than applying approximate edits.

## Data path

* Two DMA destinations, each 12 KiB: 4 KiB guard, 512-byte packet, 32-byte
  completion marker, remaining guard. The payload includes the 256-byte packed
  monochrome display, VM state, elapsed-clock counters and up to eight replay
  records. This transfers 128 times less payload than Doom's 64 KiB slot.
* The existing two internal 64 KiB source slots remain reserved. Only their
  512-byte prefixes cross DMA. Full paired PIO captures check the unused tails
  remain zero; existing full arena/system audits are retained. Shrinking the
  exclusive arena is a separate change.
* A separate bounded 16-entry keyboard FIFO receives ordered down/up events.
  Brief presses are latched until an instruction slice consumes them. Video
  credits never gate the independent browser input connection.
* The browser receives a 544-byte binary packet on a pushed WebSocket, with
  two video credits, ordered acknowledgement and bounded latest-frame drawing.
  Blur/disconnect releases keys; stale run IDs cannot control a restarted game.
* Guest speed defaults to 500 instructions/s; timers use elapsed 60 Hz time.
  The RTEMS clock remains 10 ms. Catch-up is bounded to 250 ms/1000
  instructions per slice; this intentionally does not run games faster simply
  because transport becomes faster. Sound remains a timer, without audio.

Every captured frame is independently replayed against the unchanged native
C8G1 core. A bounded trace records cycles, timer ticks and consumed key sequence.
The host checks committed input, cumulative clock budgets, all 304 original
response bytes, packet generation, DMA marker and guards before publication.
Native replay is not proof of physical coherency; the physical acceptance is
still required. Firmware readbacks and full system audits are not removed.

## Build and test

On the Linux build host, with the accepted private-worker base bundle:

```sh
python3 game/chip8/accele160/build.py \
  --work /home/mit/i960-chip8-candidate \
  --base-bundle /home/mit/i960-shutdown-wq-20261018/bundle \
  --rtems-build /home/mit/i960-rtems-20261011/bounded
```

A fresh output directory is required. Optional `--rom FILE --cpu-hz 500` pins a
custom guest ROM/rate into the bundle. The builder verifies the base inventory,
requires the private admission-worker module, builds compact DMA resources and
RTEMS, builds native replay libraries, and inventories the resulting sources and
binaries. Do not copy CHIP-8 modules over a running Doom session.

Native checks:

```sh
make -C game/chip8 test all
python3 game/chip8/stream/test_stream.py
(cd game/chip8/stream && PYTHONPATH=.. python3 test_oracle.py)
python3 game/chip8/stream/benchmark.py
```

The WebSocket tests require the pinned dependency described in
[commands](../../../chip8_commands.md). Linux `gcc -m32` additionally executes
`test_entry.c` against the real adapter and `test_dma.c` against the generated
512-byte descriptor profile. `test_rearm.py --keyboard-fifo` exercises the actual
resident rearm policy with mocked scheduling/MMIO.

The accepted batch included both guarded full-flash reads, compact DMA
versus 128 full paired PIO comparisons, native replay of all 7,123 frames,
input down/up, STOP, repeated rearm, stale-input rejection and a three-second
stalled-host test. Global SIGTERM shutdown and deliberately expired card-side
timeout remain untested in this batch; do not conflate reusable guest STOP
with global shutdown. The owner remains in reusable idle. Retained QUIE
resources require resetting the PC; never force-unload or adopt them.
