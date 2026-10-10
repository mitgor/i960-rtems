# T5 persistent session — hardware validated 2026-10-10

`host/session/` adds `dac960session.ko` and `/dev/i960-session` for repeated,
bounded BIO1 calls. It uses the installed ROM hook and unchanged 104-byte runner.
The one-shot loader remains available. No flash write or reboot was performed.

## Results

The same DAC960PG at `mit@192.168.2.75`, `0000:37:09.1`, firmware 4.07-0-29,
16 MiB RAM, stayed on boot `a9429ca4-0144-452d-8a80-7189608ce99b`.

- 1,000 consecutive calls matched the native Tetris state and framebuffer byte
  for byte. Median write/read/client-validation latency **41.12 ms**, mean
  41.52 ms, p95 41.55 ms, maximum 54.82 ms. There were 31 periodic full audits.
- A separately paced 400-frame run completed in **19.993 seconds (20.007 Hz)**.
  Median 42.37 ms; 13 frames exceeded their scheduled completion deadline,
  maximum lateness 5.84 ms. Full audits and the first-entry handshake can exceed
  the 50 ms frame budget; subsequent frames caught up. This is a 20-second
  cadence test, not the planned 30-minute interactive acceptance test.
- Two 40-call development runs and a three-call conservative smoke run also
  matched. The first persistent implementation retained full per-frame image
  reads and repeated cache handshakes: 63.85 ms mean. Narrowing routine reads
  gave 53.19 ms; reusing the runner's cache invalidation gave 41.79 ms.
- Lifecycle tests passed twice: 13 SIGKILL timing cases during OPEN, STEP and
  CLOSE, read-before-response, short write, unread-response overwrite rejection,
  competing opens, module unload refusal while owned, and cleanup only after
  the final inherited descriptor closed. Each close had matching saved/restored
  image, callback code and result RAM; the module then unloaded.
- Native ASan/UBSan tests inject **292 command-boundary failures** (known-complete
  errors and uncertain timeouts), including periodic full audit and restoration.
  Stale/malformed requests and six output/immutable corruption cases pass.
  Existing one-shot tests still pass (194 scalar + 230 BIO failure cases).
- The 1,000-frame archive was independently reconstructed on the Mac and checked
  against the native oracle, actual request sequence, immutable bytes, paired
  command statuses, DMA guards and final restoration.

Compared with T3's approximately 306 ms full one-shot CLI call, persistent frame
calls are about 7.4× faster. These are intentionally different operation scopes:
OPEN/CLOSE are amortized, and routine per-frame audit coverage is smaller.
Opening took 61.15 ms and closing, including a full audit, 78.95 ms in the main run.

## Ownership and transaction contract

Loading the module performs read-only controller/profile preflight. Opening the
root-only device exclusively saves and checks the entire 512 KiB staging image
against installed-ROM SHA256
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`, saves
callback table/code/result RAM, uploads the fixed payload and installs the runner.
The table still points to ROM PING when OPEN returns.

Each `write(fd, block, 12384)` submits exactly one BIO1 request, synchronously.
The sequence must increase strictly, with no wrap within a session. Only the BIO
block is uploaded; executable bytes stay fixed. The first STEP performs the
benign cache-control handshake. Later steps rely on the unchanged runner's
self-disarm and `dcctl` before returning, and its instruction/data invalidation
on entry. There is no intervening 6F dispatch between steps. Each STEP writes a
fresh result sentinel, arms the runner with paired table verification, executes
it once, proves it self-disarmed to ROM PING, and checks its paired RUN1 result.
There is no retry of user code.

A following exact-size `read(fd, block, 12384)` retrieves the response. No next
write is allowed until it is consumed. Read before response returns EAGAIN;
malformed/stale writes return EINVAL without card commands. A second open returns
EBUSY. The file owns the session, so `dup`/`fork` keep ownership until the last
reference closes. O_CLOEXEC is used by the Python client.

Final release restores the saved table, helper/runner bytes and result RAM,
then the original payload prefix, and verifies the entire original staging
image with paired reads and the pinned hash. It checks stock firmware health.
A mutex serializes writes, final release and driver removal. File ownership pins
the module; krefs protect driver state through removal. A pending command,
unproven runner disarm or failed restoration retains the allocation and module
until reboot. Exiting a process does not make uncertain DMA safe to free.

Linux ignores a file `release` callback's return value. `Session.close()` therefore
checks the final debugfs restoration record after closing, rather than treating
successful `close(2)` as proof. Low-level users must do the same. Deliberately
closing only one of several inherited descriptors uses `close(verify=False)`;
verification belongs to the final owner. Never unload a failed/pinned session.

## Audit coverage and evidence

Every STEP reads the **45,152-byte payload region twice**, including all code,
padding, input, output guards and unused output capacity. Only the BIO response
fields and declared output bytes may differ from the expected request image.
Every 32nd STEP reads and validates the **whole 524,288-byte staging image twice**.
CLOSE performs another full output audit when a validated response exists, before
restoring, then full paired restoration verification. Normal steps use 12 firmware
commands, first step 16, periodic full-audit steps 28. Wrapped 8-bit command tags
were exercised repeatedly; each completion still matches the outstanding tag.

This deliberately permits detection of corruption beyond the payload to lag by
up to 31 calls. It is for the bounded, trusted cooperative payload, not isolation
for arbitrary programs. There is still no preemption for a hung i960 payload.
Actual timeout/failing-restore injection was simulated, not deliberately induced
on the card. Hardware SIGKILL delay sweeps sample execution phases; they do not
claim an exhaustive kill at every CPU instruction or an actual SSH network drop.
Hot unplug/unbind and recovery remain untested.

Debugfs `result.txt` holds the latest operation only, bounded in memory. Capture
it before the next operation. `payload-after-{a5,5a}.bin` expose exactly the latest
STEP's audit length; other before/restored image files remain full size. The
replay archives retain every command transcript, BIO response, request, and a
lossless XOR of the paired-verified audit region against the original firmware.
They do not invent fresh reads of the unaudited tail on short-audit steps.

## Build and use

From the repository root:

```sh
python3 host/session/build.py --out /tmp/dac960session-source
python3 host/session/test_session.py
python3 -m unittest discover -s host/loadrun
```

Copy the generated module source to Linux and run `make` against that host's
kernel headers. Build the Tetris payload using `loader/runtime/Makefile` and the
known i960 toolchain, or use the pinned T2 binary in the artifacts. The driver
requires a BIO1 image prepared by `host/loadrun/buffer_io.py`, installed under
`/lib/firmware`, and the same driverless PCI profile as the one-shot loader.

The explicit hardware acceptance runner handles firmware preparation, module
loading, capture, final restoration checks and unload, under the existing loader
lock. With the repository available on Linux:

```sh
sudo python3 host/session/live_test.py \
  --payload /path/to/tetris_payload.bin --module /path/to/dac960session.ko \
  --oracle /path/to/native-tetris-oracle --output /new/capture-directory --steps 1000
```

`lifecycle_test.py` and `cadence_test.py` are also explicit hardware programs;
they are not run by offline test discovery. Run them only with no existing owner
or bound controller driver. The lifetime test sends SIGKILL only to its own test
children. `session.py` is the API for the future terminal client: load the module
with `pointer_check=1 runtime_check=1 stage_check=1 buffer_io=1`,
`payload_argument=0xc0f34000`, and `firmware_name=i960/your-bio-image.bin`, then
use `with Session() as s: status, output, block = s.step(request_block)`.

For offline replay validation, extract the evidence tar, compile the native oracle
(`cc -DTETRIS_CORE_ONLY -Igame game/tetris.c game/oracle.c -o /tmp/tetris-oracle`),
then run:

```sh
python3 host/session/validate.py /extracted/replay \
  --payload artifacts/tetris-t5-20261010/target/tetris_payload.bin \
  --oracle /tmp/tetris-oracle
```

Evidence: [artifacts/tetris-t5-20261010](artifacts/tetris-t5-20261010/README.md).
Next is T4's keyboard/terminal client and longer interactive/disconnect testing.
RTEMS, firmware recovery and hardware boot mode changes are separate work.
