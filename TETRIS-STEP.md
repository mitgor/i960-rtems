# T2: bounded Tetris state/update/render — implemented and tested

**T3 passed:** [1,000-call hardware replay and latency](TETRIS-REPLAY.md), plus a separate 64-call repeat. The full conservative loader runs at roughly 3.26 updates/s; interactive T4 remains planned.

2026-10-10. Tetris now runs as returning steps on the real i960, emitting its
state and framebuffer through BIO1. This completes T2 of
[TETRIS-ON-CARD-PLAN.md](TETRIS-ON-CARD-PLAN.md). It is not yet an interactive
terminal game: long live replay and terminal controls remain T3/T4.

## Implementation

`game/tetris.c` contains one deterministic core with explicit state, initialization,
validation, update and rendering. `game/tetris.h` declares its API and wire sizes.
The existing emulator executable retains its doorbell loop in an adapter; compiling
with `TETRIS_CORE_ONLY` removes that loop and all fixed-address emulator I/O.
The hardware payload is `loader/runtime/tetris_payload.c`, using the tested BIO1
runner and the stable assembly entry stub. No loader module or flash update was
needed. The raw target is 4,064 bytes, with no data/BSS allocation in its link map.

There is no hidden mutable game state. A host request supplies the previous
240-byte state; the i960 advances it and returns a new state followed by a
1,920-byte 24×80 ASCII framebuffer. The host retains the state between calls,
allowing the loader to restore all borrowed card RAM after every transaction.

`tetris_init(state, seed)` explicitly initializes every field (zero seed selects
0x01234567). `tetris_step(state, key, ticks)` validates state and returns 0 or 1;
invalid requests leave it unchanged. `tetris_render(state, framebuffer)` expects
a validated state and at least 1,920 writable bytes. The request wrapper checks
length/capacity and validates state before rendering.

## Wire protocol

The BIO1 input is exactly 256 bytes, all integers little-endian:

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 4 | operation: 0 step, 1 initialize/restart |
| 4 | 4 | seed for initialize; zero for step |
| 8 | 4 | key: 0, `a`, `d`, `w`, `s`, `q` |
| 12 | 4 | elapsed simulation ticks, 0..20 |
| 16 | 240 | previous state; all zeros for initialize |

Initialization requires zero key/ticks. A successful BIO1 output is exactly
2,160 bytes: state then framebuffer. Status 1 rejects malformed game input;
status 2 rejects insufficient output capacity. No response bytes are written on
error. These statuses are separate from the runner's scalar return value.

The state begins with ten 32-bit words: version (1), RNG, score, piece index,
rotation, signed x, signed y, gravity tick, phase, reserved (zero). The remaining
200 bytes are the 20×10 board. Encoding/decoding is explicit, not a struct dump.
Board cells are zero or one of `I`, `O`, `T`, `S`, `Z`, `J`, `L`. Phase is 0 running, 1 game over, 2 quit. Running states must have a valid
noncolliding active piece. Signed coordinates are range-checked before indexing;
board contents, version, RNG, score, rotation, phase, timer and reserved fields
are also checked.

## Bounded behavior and compatibility

One request applies one key once, then advances at most 20 ticks. Each tick is
intended as 50 ms of host simulation time; gravity occurs every 20 ticks. A value
above 20 is rejected rather than processed in an unbounded catch-up loop. Zero
ticks allows a key action without gravity. No wall clock is read by the core.

The drop key moves the piece to its lowest fitting position, as in the original
game; locking happens at the next gravity event. Drop search is explicitly
limited to 24 iterations. A call can process at most one gravity event, one lock
and a bounded scan/shift of the 20-row board. Rendering writes exactly 1,920 cells.
Game-over/quit states remain terminal until explicit restart; quit reports phase 2.

The core retains the seven shapes, collision rules, RNG, 100 points per cleared
line and board layout. Score saturates at 999,999,900 and uses a ten-byte decimal
scratch buffer, avoiding the old signed-overflow/eight-byte formatting risk.
Above-board locking reports game over. Frame overlay clips coordinates before
writing. The emulator adapter ignores unknown terminal keys and uses one tick
per doorbell as before; quit now renders a final QUIT state.

The target's largest explicit stack adjustment is 240 bytes in the request
wrapper, plus a 16-byte rendering adjustment and architectural call frames.
This has passed the listed live calls, not a general firmware-stack capacity
qualification. The core has no heap, recursion, host waits or resident loop.

## Validation

Native ASan/UBSan and the compiled i960 under the interpreter both produced
`RESULT=1161671136` for the rule/bounds tests and a hash of every state/frame in
1,024 deterministic transitions across four seeds. Tests cover round-trip state,
wall collision, rotation, drop, two-line clearing with falling contents, spawn
collision/game over, quit/restart, malformed fields, large-score rendering,
request sizes/capacity and buffer guards.

Cross-execution exposed the interpreter's missing opcode 583 (`setbit`). It now
sets the bit selected modulo 32; a separate assembly test checks literal/register
bit positions, wraparound and bit 31. Unsupported instruction/budget exhaustion
now returns failure rather than an apparently successful RESULT=0.
Instruction semantics: [Intel i960 RM/RN manual, setbit](https://datasheets.chipdb.org/Intel/80960/manuals/27315801.PDF).
The preserved emulator-style game still builds with the historical toolchain.

Nine live BIO1 transactions passed, each with 128 firmware commands:

| Request | Observed result |
| --- | --- |
| Initialize seed 1 | state and first frame |
| Left | updated state/frame |
| Rotate | updated state/frame |
| Drop plus 20 ticks | landed/locked piece and next piece |
| Quit | phase 2 and QUIT frame |
| Restart seed 1 | freshly initialized state/frame |
| Constructed two-line case | score 200, correct shifted board |
| Constructed spawn-collision case | phase 1 and GAME OVER frame |
| Invalid 21-tick request | status 1, zero output, clean restoration |

Every response was compared byte for byte against a separately compiled native
reference, including all 2,160 bytes on success. Paired staging/output reads,
immutable/guard checks, full restoration, PING/health checks and module unload
passed on every run. The rejection was followed by verified clean unload, not a
retry. All tests used the existing boot ID
`a9429ca4-0144-452d-8a80-7189608ce99b`; no reboot or flash command occurred.
The card remains driverless. Recovery remains untested.

Artifacts: [tetris-t2-20261010](artifacts/tetris-t2-20261010/), including
[the two-line result](artifacts/tetris-t2-20261010/acceptance/run-two-lines/frame.txt)
and [game over](artifacts/tetris-t2-20261010/acceptance/run-game-over/frame.txt).
The 1,024-step run was native/interpreted; the live run was nine transactions.
Do not mistake this for T3's planned 1,000-step hardware replay or T4 playability.

## Reproduce

Offline/native (no hardware access):

```sh
make -C game test
python3 game/check_live.py
python3 -m unittest discover -s host/loadrun -p 'test_*.py' -v
```

On the Linux host with the i960 toolchain:

```sh
python3 game/check_tetris.py --cross /home/mit/i960/tools/bin/i960-coff-
make -C loader/runtime CROSS=/home/mit/i960/tools/bin/i960-coff- tetris_payload.bin
python3 host/loadrun/tetris_wire.py --seed 1 --output /tmp/tetris-init.bin
sudo python3 host/loadrun/loadrun.py loader/runtime/tetris_payload.bin \
  --module /home/mit/i960-buffer-t1/module/dac960loadrun.ko --buffer-io \
  --input /tmp/tetris-init.bin --sequence 1 --expect 0 --output /tmp/tetris-init-run
python3 host/loadrun/tetris_wire.py --response /tmp/tetris-init-run/response.bin \
  --output /tmp/tetris-init-decoded
cat /tmp/tetris-init-decoded/frame.txt
python3 host/loadrun/tetris_wire.py --state /tmp/tetris-init-decoded/state.bin \
  --key a --ticks 1 --output /tmp/tetris-left.bin
```

Use new output paths and a new nonzero BIO1 sequence per call. Do not pass
`--framebuffer` directly to loadrun for this payload: its response includes state;
`tetris_wire.py --response` splits it correctly. `test_tetris_live.py` is an
explicit hardware acceptance runner, never invoked by unit-test discovery.
The deployed build, oracle and captures are in `/home/mit/i960-tetris-t2/`.

Next is T3: longer deterministic hardware replay, latency measurement and repeat
session behavior before building the interactive terminal client.
