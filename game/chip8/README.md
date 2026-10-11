# Bounded CHIP-8 / RTEMS application

Status (2026-10-11): **implemented and tested on the real card.** The RTEMS
payload passed a reset plus 300 scripted updates and 404 browser-session
callbacks. All 705 replies match the native core byte for byte; 21 periodic full-allocation audits
and both final RAM restorations/unloads passed. Browser movement and restart
were exercised over an SSH tunnel. Production IPv6 HTTP was restored with 200.
Native sanitizer/protocol/HTTP tests pass on macOS and Linux.

## Try the native demo

From the repository root:

```sh
make -C game/chip8 test
python3 game/chip8/server.py
```

Open <http://127.0.0.1:8096/>. The page labels this as **Native host simulation**.
Arrow keys move the original project spaceship demo; `1234/QWER/ASDF/ZXCV`
map to the standard CHIP-8 keypad. `--rom PATH` loads a supplied 2..3584-byte
ROM. The sound timer is displayed, not played as audio. Only one operator should
control a session. The server binds loopback; remote use can go through an SSH
forward (`ssh -L 8096:127.0.0.1:8096 mit@192.168.2.75`).

The host sends elapsed 60 Hz timer ticks and a 500 instructions/s budget, clamps
catch-up to 250 ms and serializes requests. Browser polling is approximately
30 Hz plus request latency. This is neither a promised hardware frame rate nor
an autonomous emulated clock; execution stops while requests stop. Key state is
cleared on blur/hidden tabs. No background session is installed by the program.
Ctrl-C closes the backend; transport exceptions end the server and invoke the
existing audited close path. An uncertain driver state can still retain resources.

## Interpreter contract

`chip8.c` is freestanding C with 32-bit unsigned integers and 16-bit addresses.
The guest has 4,096 bytes RAM, sixteen registers, sixteen return-stack entries,
a 64×32 framebuffer (256 bytes, row-major, high bit first) and 60 Hz timers.
It uses no allocation, libc, floating point or real hardware access.

This is a specified CHIP-8 dialect, not a claim of universal ROM compatibility:

- `8xy6`/`8xyE` shift Vx; `Fx55`/`Fx65` leave I unchanged.
- Drawing wraps both axes and uses XOR collision reporting in VF.
- OR/AND/XOR preserve VF unless VF is the destination itself.
- `Bnnn` uses V0; I arithmetic wraps at 16 bits and actual accesses are checked.
- `Fx0A` accepts a currently held key (lowest key wins), with no release-edge wait.
- `0nnn` native machine-code calls, SCHIP and XO-CHIP are unsupported.
- Invalid opcode, memory access or stack operation latches a guest fault until
  reset. A fault can advance PC before latching; it cannot execute native code.
- At most 1,000 instructions and 60 timer ticks per request; zero-cycle status
  reads are allowed. Timers decrement before the requested instruction batch.

Tests include arithmetic and VF aliasing, RAM/stack boundaries, wrapping and
collision, timers, key wait, rejected requests without mutation, every opcode
encoding under ASan/UBSan and 1,000 seeded random programs. Exhaustive opcode
*safety* coverage is not exhaustive semantic validation against every dialect.
The original demo passes 1,200 deterministic native replay frames (24,000 guest
instructions); the HTTP tests exercise controls, malformed input and origin checks.

## C8G1 protocol

All wire integers are explicitly little endian, never a memcpy of a C struct.

Request header: six 32-bit words: magic `0x31473843`, operation, instruction
budget, key bitmap, elapsed timer ticks, RNG seed. Operation 0 resets and loads
an appended ROM with zero budget/keys/ticks. Operation 1 steps the existing
state; length must be 24 bytes and seed must be zero. Reset accepts a zero seed
as deterministic seed 1. An invalid request or short output capacity leaves
guest state unchanged.

Every valid response is 304 bytes: eight words (magic, guest status, instructions
executed this call, total executed, PC, I, delay timer, sound timer), sixteen V
register bytes, then 256 frame bytes. Guest status: 0 running, 1 waiting for a
key, 2 opcode fault, 3 memory fault, 4 stack fault. Wire rejection returns outer
RIO status 1 or 2 and no output. Successful outer status can contain a guest
fault. Total instruction count wraps modulo 2^32.

## RTEMS build and hardware reproduction

The adapter uses the existing bounded `session` startup, context switch, libc
helpers and linker layout. Init wakes a worker by semaphore, the worker executes
one bounded request, then Init yields back to stock firmware. No timer/vector
or production network ownership changes. Validated 60 Hz request ticks also
advance RTEMS's 100 Hz software clock with fractional carry. The guest reset
resets only the guest, not the RTEMS kernel or its clock.

Build in a **fresh isolated directory** on the remote toolchain host:

```sh
python3 game/chip8/build_target.py \
  --work /home/mit/i960-chip8-build-NEW \
  --sources /home/mit/i960-rtems-web-20261011/sources
```

The builder snapshots the existing RTEMS build machinery and substitutes this
application only in that snapshot. It does not modify `rtems/build.py`, the
parallel profile, source archives or an existing build. The source tarball
hashes are checked by the existing builder. Result is `WORK/session/kernel.bin`;
`profile: session` in build.json describes the reused execution profile, while
chip8-build.json identifies the application and exact profile-source hashes.

Recorded target: 22,560 bytes text, 452 bytes data, 55,472 bytes BSS; the latter
includes a 48 KiB RTEMS workspace. Flat binary extent is 187,012 bytes because
it includes the immutable/private-region gap and materialized BSS. This is below
the existing RIO1 limits, not evidence of new memory ownership. Immutable code
ends before `0xc0f4c000`; private data starts at `0xc0f4c010` and ends before
`0xc0f9bff0`. The normal lower/upper guards and RIO block remain unchanged.

For the next hardware session, generate/build the **baseline** transport from
`rtems/transport/build.py` in a separate output directory (not an autonomous,
IRQ or quarantine profile). Wait for the active hardware test owner to finish
and establish exclusive use; do not stop its service/test to make room. Then:

```sh
make -C game/chip8 all
sudo python3 game/chip8/check_card.py \
  --payload /path/to/session/kernel.bin \
  --module /path/to/dac960rtems.ko \
  --output /path/to/fresh-chip8-capture --steps 300
```

This uses the existing exclusive lock, paired reads and periodic full audits;
it refuses an already bound driver. It compares reset plus every reply to the
native oracle and requires full restoration and unload. Save the captures and
latencies, then test keyboard/reset/close through `server.py --backend card`
with the same three path arguments. Restore and check the previous production
web service afterward. These commands were run after the parallel batch completed and its normal
production-service cleanup passed. Scripted median callback latency was 51.43 ms
(maximum 74.03 ms); browser-session median was 51.65 ms. These include host
transport/audits, not just interpreter CPU time. The native demo remains available
independently; the card browser session was closed to restore production HTTP.

See [the progression and Doom decision](../../GAME-PROGRESSION.md) and
[build/test evidence](../../artifacts/chip8-20261011/README.md).

## Replay the preserved card evidence

Extract `artifacts/chip8-20261011/chip8-live.tar.gz` into a fresh temporary
folder, then use `verify_card.py CAPTURE --payload .../kernel.bin --module
.../dac960rtems.ko`; add `--browser` for the `live-web` capture. The verifier checks
payload/module hashes, native responses, required periodic audits and the existing
full-RAM restoration contract. `live1-verified.json` and `live-web-verified.json`
record the results. `chip8-build.json` retains its **build-time**
`hardware_tested: false`; the later live evidence documents the subsequent runs.

Next: broader dialect/conformance ROM coverage and a longer interactive soak are
useful follow-ups. The next progression milestone is a fixed-point raycaster and
measurement of the frame transport; unrestricted resident execution is not needed
for these bounded applications.
