# T1: returning text and framebuffer buffers — hardware validated

2026-10-10. The returning software loader now transfers bounded input and output
buffers. T1 of [the Tetris plan](TETRIS-ON-CARD-PLAN.md) is complete. Game-loop
conversion and interactive Tetris are still T2 onward.

## Live evidence

The installed card ran the new C demo after Linux startup, with the existing
patched firmware and unchanged 104-byte runner. No flash write or reboot occurred.
All five runs used boot `a9429ca4-0144-452d-8a80-7189608ce99b`.

| Test | Sequence | Response | Firmware commands |
| --- | --- | --- | --- |
| Text plus XOR-transformed input | 101 | 36 bytes, status 0 | 128 |
| Card-drawn 24×80 framebuffer | 102 | 1,920 bytes, status 0 | 128 |
| Framebuffer with only 16 bytes capacity | 103 | 0 bytes, status 2 | 128 |
| Different text input after rejection | 104 | 37 bytes, status 0 | 128 |
| Original Fibonacci(20), scalar ABI | — | 6765 | 110 |

The greeting was `Hello from the real i960!` followed by newline. Text mode also
returns each input byte after the mode byte XORed with 0x20; this portion is
binary, not necessarily printable. The framebuffer is a `#` border and a
coordinate-dependent letter pattern calculated on the card. Independent Python
checks compared every returned byte, not just completion/status or a screenshot.

Every run restored the exact 512 KiB staging image, dispatch, temporary code and
result storage, passed firmware health checks, and unloaded the module. The
capacity error was an application-level rejection; the CLI exited nonzero after
saving evidence and safely unloading. The final card is driverless.
Evidence: [artifacts/buffer-io-20261010](artifacts/buffer-io-20261010/), including
[the captured frame](artifacts/buffer-io-20261010/run-frame/frame.txt).

## BIO1 contract

Scalar mode remains available. Opt-in buffer mode uses a fixed block at
`C0F34000`, offset `8000` inside the original 64 KiB payload window. Code and
read-only data must fit below that offset. The host pads code, builds the block,
and uploads a 45,152-byte image (`B060` hex). No arbitrary address parameter is
exposed. The kernel checks the exact size, entry range, fixed argument pointer
and valid request before PCI access.

All integers are unsigned 32-bit little-endian. The first 64 bytes hold:

| Word | Request value | Response rule |
| --- | --- | --- |
| 0 | Magic `314F4942` (`BIO1`) | unchanged |
| 1 | Version 1 | unchanged |
| 2 | Nonzero sequence | unchanged |
| 3 | Input length, 0..4096 | unchanged |
| 4 | Output capacity, 0..8192 | unchanged |
| 5 | Pending `FFFFFFFF` | application status; 0 means success |
| 6 | 0 | actual output length, at most capacity |
| 7 | 0 | request sequence echoed on completion |
| 8..15 | 0 | unchanged |

Input occupies block offsets `0040..103F`, padded with zeros. A 16-byte A5 guard
starts at `1040`; output starts at `1050` and occupies 8192 bytes initialized to
CC. A 16-byte 5A guard starts at `3050`. Only words 5..7 and the declared output
prefix may change. A nonzero application status requires zero output length.
Demo status 1 means invalid input; status 2 means insufficient output capacity.
The runner's return value/completion marker are separate from this block.

The target returns promptly using the existing ABI; no blocking host handshake,
large new stack, BSS or resident loop is introduced. `buffer_io.h` provides wire
helpers shared by the kernel and target; Python independently implements packing
and validation. This is trusted native code, not a memory protection boundary.

## Transaction and cache behavior

After the existing upload/readback/cache-control sequence, the runner calls the
payload exactly once and self-disarms to ROM PING. The host checks the runner
completion, then reads the full 512 KiB staging image twice, with different DMA
sentinels, **before restoring anything**. It checks the response sequence, bounds,
guards, unchanged input/header fields, unchanged code and every other immutable
byte across the full image. These captures are `payload-after-a5.bin` and
`payload-after-5a.bin`; the original `stage-candidate-*` remains the verified
pre-execution upload.

The established write-through CPU cache behavior, pre-call invalidation and
runner invalidation after return remain in use. Actual CPU-produced text/frame
bytes were visible through firmware DMA readback; paired reads agreed. No runner
binary or flash revision was needed for this extension.

A known-complete invalid response enters restoration and reports failure.
Uncertain commands retain DMA resources as before. Unexpected writes beyond the
restored payload prefix leave a failed full-image restoration check and dirty
state; do not force unload or retry. Output is exported to the user only after
independent CLI verification and clean transaction completion. Matching sequences
reject stale responses but do not make uncertain executions safe to replay.

## Build and use

From the repository root on the Linux PC, with the installed i960 toolchain:

```sh
make -C loader/runtime CROSS=/home/mit/i960/tools/bin/i960-coff- buffer_demo.bin
python3 host/loadrun/build.py --out /tmp/i960-bio-module
make -C /lib/modules/$(uname -r)/build M=/tmp/i960-bio-module W=1 modules
python3 -c 'from pathlib import Path; Path("/tmp/frame-input.bin").write_bytes(bytes([1]))'
sudo python3 host/loadrun/loadrun.py loader/runtime/buffer_demo.bin \
  --module /tmp/i960-bio-module/dac960loadrun.ko --buffer-io \
  --input /tmp/frame-input.bin --sequence 1 --expect 0 --framebuffer \
  --output /tmp/i960-frame-new
cat /tmp/i960-frame-new/frame.txt
```

The build/output directories must be new. For text mode, make input bytes
`bytes([0]) + b"abc"` and omit `--framebuffer`. `response.bin` contains the greeting
and transformed data; `response.json` records status, length and sequence.
`--capacity` reduces the output budget. `--framebuffer` checks for exactly 1,920
printable ASCII cells and saves 24 newline-terminated rows; it does not interpret
arbitrary target bytes as terminal escape sequences. Request/response buffers
can later carry game state as well as frames.

The deployed build is under `/home/mit/i960-buffer-t1/` on the remote PC:
`loadrun.py`, `buffer_io.py`, `module/dac960loadrun.ko`, `target/buffer_demo.bin`.
The module is built for Linux 6.8.0-138-generic. Neither source generation nor
building a payload programs flash.

The target's entry stub branches to `_payload`: this old GCC may emit constants
or helpers before a C function and does not support section attributes for this
target. `buffer_start.s` and `buffer.ld` establish the actual entry at C0F2C000.
Do not assume the first C function begins at raw-binary offset zero.

## Validation and next work

Run `python3 -m unittest discover -s host/loadrun -p 'test_*.py' -v`.
Eight tests include target demo execution natively under ASan/UBSan, request and
response boundary checks, stale/oversized/corrupt response rejection, all saved
live captures, 194 scalar and 230 buffer command-boundary failures, and six
response-corruption scenarios. The protocol maximum input/output sizes are
covered offline; the largest live response in this milestone is 1,920 bytes.
Malformed wire headers are tested offline; the live negative case is the valid
request with insufficient capacity. The generated Linux module builds with W=1.

One native test caught a greeting-length off-by-one before live testing; the
capacity calculation now derives from the string literal size and exact-fit/
one-byte-short cases pass. The old GCC entry-layout issue was also resolved
before execution. Neither failure touched the card.

Next: T2, make `game/tetris.c` expose a bounded update/render operation with
explicit state and framebuffer pointers. This milestone supplies transport; it
does not yet make the existing blocking game loop safe to upload unchanged.
