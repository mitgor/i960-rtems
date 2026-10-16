# Browser Doom on the i960

The qualified exact divide is now enabled by default. Use
`--no-fast-fixed-div` to build the original arithmetic for comparison.
Optional [input-consumption tracing](../input_trace/README.md) records the actual
frame/tic processing each key. See the [card evidence](../../../artifacts/notes/input-trace-20261016.md).

See [presentation profiling and optional FNV/direct delivery](PRESENTATION.md) for the new experimental build modes and acceptance evidence.

For connection instructions, controls and launch commands, see [PLAY.md](PLAY.md).
Bulk host-to-card WAD transport is documented in [WAD-DMA.md](../../../rtems/dma/WAD-DMA.md);
its dated acceptance status is [here](../../../artifacts/notes/wad-dma-20261014.md).

This experimental profile keeps the actual DoomGeneric engine running under
RTEMS while Linux supplies its immutable Freedoom WAD, keyboard events and
browser framebuffer delivery. It is separate from the fully replayed two-frame
[acceptance baseline](../../../artifacts/notes/doom-visible-20261013.md).

## Bounded DMA comparison

The opt-in `build.py --dma` and `run.py --dma-test` pair builds and runs a
single 28-frame acceptance, not a persistent interactive DMA session. It reads
four identical pinned frames through DMA and paired mailbox, then measures
mailbox/DMA/DMA/mailbox blocks while retaining the normal full audits. It uses
the same renderer, frame format and input sequence. See the
[ownership contract](../../../rtems/dma/FRAME-DMA.md) and
[original dated evidence](../../../artifacts/notes/doom-dma-20261014.md).
The [subsequent stress test](../../../artifacts/notes/frame-dma-stress-20261014.md)
fixes a reproduced peer-isolation halt during owned DMA; it passed 512 synthetic
frames with full audits and shutdown. The
[fixed Doom comparison](../../../artifacts/notes/doom-dma-fixed-20261014.md)
passed all 28 frames, 29 full monitor/RAM pairs, owned STOP and global drain.
Mailbox delivered 0.972816 FPS versus DMA 1.376781 FPS (+41.525%); average
transfer fell from 503.489 to 228.797 ms. All buffers match the earlier physical
run. Longer interactive lifecycle acceptance is next; DMA remains opt-in.
Do not combine this test with `--bulk`, `--bulk-test` or `--self-test`, or use a
DMA kernel with a non-DMA runner. The accepted normal play modes are unchanged.

## Two-buffer binary pipeline (bounded acceptance passed)

Build with `build.py --work NEW_DIRECTORY --pipeline`, then run with
`sudo python3 game/doom/play/run.py --work NEW_DIRECTORY --output NEW_OUTPUT --pipeline`.
This selects a separately admitted engine with two alternating 64 KiB slots,
DMA readback and indexed binary Canvas delivery. CRC stays enabled by default;
add `--no-crc` only to explicitly omit payload CRC. Image admission, generation,
bounds, DMA completion/quiescence, guard checks and full system audits remain.
The host logs payload hashes for evidence even in CRC-off mode.

`--pipeline --pipeline-test` runs the finite 52-frame CRC-on/off/off/on acceptance,
including four exact mailbox/DMA pairs. It cannot be combined with other test
modes or `--no-crc`. Run `verify_play_pipeline.py` and the full system verifier;
neither replaces the other. See the [dated experiment](../../../artifacts/notes/doom-pipeline-20261014.md)
for physical acceptance status and performance. Never mix a two-buffer engine
with the one-buffer runner or reuse a retained exclusive mapping after failure.

The 52-frame physical test passed all 29 full audit pairs, STOP and heap drain.
CRC-on delivered **1.396095 FPS**; CRC-off **2.070201 FPS (+48.285%)**. The
first attempt exposed WAD starvation during DMA polling; the host now services
WAD requests during that wait. CRC stays on by default and the pipeline remains
opt-in pending longer interactive acceptance.

The browser uses `/frame.bin` with an embedded session/generation, geometry and
CRC-mode header. It can skip superseded display frames without retaining card
memory. Input queues remain bounded and lost focus releases held keys.

## Connect and play

The October 14 acceptance session has ended; the public web service currently
owns the card. After launching a new play session as described below, open
**http://192.168.2.75:8087/** and click the game to focus it. For a machine that reaches the host only through SSH:

```sh
ssh -N -L 8097:127.0.0.1:8087 mit@192.168.2.75
```

Then open **http://localhost:8097/**. The page reports engine upload, level
loading, frame number and framebuffer readback time. The host renders only PNG
encoding; Doom simulation and rendering execute on the card. There is no sound.

| Control | Action |
| --- | --- |
| W / Up | Forward |
| S / Down | Backward |
| A / Left, D / Right | Turn |
| Ctrl / Space | Fire |
| E | Use / open door |
| Shift | Run |
| Enter | Confirm |
| Escape | Menu |
| Tab | Map |
| 1–7 | Weapon selection |
| Y / N | Menu confirmation / cancellation |
| Stop Doom button | Request owned engine cancellation |

Keys release when browser focus is lost; a short input heartbeat also releases held keys after a disconnected browser stops renewing them. Frame delivery currently uses bounded
PIO readback and blocks the renderer until the host acknowledges the complete
frame. It can be slow; this is a play-first prototype, not a frame-rate claim.
The first physical six-frame test delivered about **0.169 frames/s** after a
roughly 23-minute initial upload/load. No input reaches the card until a published frame is being collected. Hold
movement/fire until a new frame appears: a short press and release between
updates can be consumed in the same game tick. Queue exhaustion requests STOP
rather than discarding a release event. Use the page’s Stop button to quit;
Y/N menu confirmation and weapon-number keys are now mapped. The pinned
DoomGeneric uses fire/use codes 163/162, not classic Ctrl/Space codes 157/32.
Pistol firing has a four-tic animation delay; at this frame rate even an accepted
press takes tens of real seconds to show the shot.

## Build and run

On Linux, after installing the preserved cross tools and 32-bit GCC/ASan
support, build from a full Git checkout (including tracked artifacts):

```sh
python3 game/doom/play/build.py --work /home/mit/i960-play-new
sudo python3 game/doom/play/run.py --work /home/mit/i960-play-new \
  --output /home/mit/i960-play-session-new
```

The builder checks pinned inputs, runs the native engine and channel tests,
then builds the RTEMS image and a module for the running Linux kernel. It does
not touch hardware. `run.py` is the hardware action; the card must already
have the accepted hook and be unowned. `--cross /path/to/i960-coff-` selects a
toolchain, `--debug-audits` enables frequent paired checks, and `--self-test`
runs a short movement/STOP session before reloading the user's session.
The convenience wrapper passed a separate fresh-workspace build with native
tests; the exact dated commands below establish the physical build's provenance.
Build-directory paths appear in Doom assertion strings, so a different workspace
produces its own engine/kernel/module hashes rather than reusing an old identity.

The dated [batch](../../../artifacts/doom-play-20261013/) preserves the exact
`build.sh` and `live.sh`, source/binary identities and physical findings.
The build needs the pinned DoomGeneric source, Newlib, RTEMS/lwIP, cross tools,
Linux kernel headers and accepted loader artifacts. See
[stock-to-applications](../../../docs/reproduce.md) before using another card.
The lab scripts use explicit `/home/mit/...` input paths; adapt these in a new
workspace, keeping the pinned hashes and accepted source directories intact.

### Current-session keyboard correction

The October 13 session on port **8088** uses the temporary `input_bridge.py`
while the original owner continues framebuffer/WAD/STOP work on port 8087.
Use only 8088 for this session. Browser turning and firing (ammo 50→48) passed;
the capture preserves over 130 frames and 57 full audit pairs. The session's
30-minute play budget expires around **23:58 Europe/Berlin, October 13**.

The bridge duplicates the existing owner's file description using pidfd_getfd;
it never opens a second card session. The driver session mutex serializes its
bounded status/key ioctls. It issues no upload, framebuffer select, ACK or direct
STOP. It monitors the original pidfd and upstream HTTP lifetime, logs every
ioctl, stops on transport errors and joins its worker before closing the duplicate.
Queue overflow or terminal bridge failure requests STOP through the original
owner. The duplicate can delay final file release; do not claim final cleanup
until both owners close. This is a dated live-session repair, not the normal
launch path. Future `run.py` launches serve corrected input directly on port 8087
and require no bridge. `test_keys.py` checks the mapping against pinned headers;
`test_bridge.py` checks exact ioctl framing/error propagation without hardware.

The new opt-ins are:

- Engine and private platform: `--startup --checkpoints --point-side-o0 --visible --play` (the platform builder does not take `--point-side-o0`).
- Engine admission: `--play`; no fixed-frame oracle identity is claimed.
- Resident runner: `--play-port 8087`; `--play-accept-frames 6` first exercises a short input/STOP session, then loads a fresh engine for play.
- Normal paired snapshot/RAM checks: `--audit-interval 60`; use `3` for frequent diagnostic checks. No guard, ownership, epoch, transport-uncertainty or executable identity checks are removed.

The engine allows up to 30 minutes to load, then resets its 30-minute
play deadline when the first frame is rendered. Missing frame acknowledgement for 60 seconds returns through the
same owned cleanup. Resident hardware ownership still requires a reboot after
final STOP; do not force-unload `dac960auto`. The public autonomous web-server
profile cannot simultaneously own this exclusive card session.

## Implementation contract

`port.c` uses the existing private owned ABI. In this build, verbose checkpoint
calls are suppressed. Its `mark` extension is used for two reviewed operations:
100 publishes the exact admitted BSS framebuffer pointer/size/sequence, and
101 drains one key event. The target verifies the pointer against its trusted
image geometry. No host-selected address can be read or executed.

The renderer parks with its image still pinned. Mailbox op `0x6b` reports the
published sequence, acknowledges it or enqueues a key; `0x6c`–`0x6e` read bounded
1 KiB windows through existing ioctl op 9. New ioctl op 10 carries control.
The target queue has 31 usable entries, the host queue 128; neither silently
overflows. HTTP uses a per-session token and same-origin checks. HTTP threads
never issue card commands. The upload worker services WAD requests and frames.

The 64,000 indexed pixels, 768 palette bytes and zero padding occupy 65,536
bytes. Full-frame transfer plus a repeated first-window check precedes ACK.
The trusted executable and relocation hashes are still checked before entry
and on return. The engine runs until STOP, then private allocations retire,
owned context ends, executable identity is rechecked and the image is released.

Host verification: `test_native.py` runs the real sanitized 32-bit engine with
input, repeats it deterministically, compares a no-input run, then proves STOP
and heap drain. `rtems/residentnet/test_play_channel.py` tests the actual target
channel's immutability, bounds, stale ACK, queue capacity, STOP and timeout.

## Returning to the public web server

Stop Doom using the page button, then wait for the supervisor to complete its
normal global STOP. Preserve the completed journals, results and RAM checks,
copy and hash-check them locally, then reboot to release the retained resident
module. Do not force-unload it. After Linux returns, confirm the card has no
bound driver before starting the existing autonomous web profile from
`/home/mit/i960-rtems-web-20261011` with a **new output directory**. The historical
[restore recipe](../../../artifacts/doom-visible-20261013/restore.sh) records the
matching payload, system-info module and IPv6 relay options; adapt its dated
output paths rather than overwriting an old result. Verify HTTP and outbound
IPv6 again. No automatic reboot or web restoration is scheduled during play.

## Opt-in mailbox bulk reader (October 14 accepted batch)

Add `--bulk` to `run.py` to select fixed 1 KiB transfers using eight-byte
message-register beats. Scalar readback remains the default. The module and
RTEMS image must both be rebuilt; this cannot be enabled in an older running
module. No new DMA mapping or card RAM aperture is used. Full paired audits,
immutable frame ownership, the first-window reread, post-read generation check,
STOP and uncertainty retention remain required.

`--bulk-test` runs four byte-exact same-frame comparisons and three refusal
checks, then six-frame scalar/bulk/bulk/scalar blocks. It exits at frame 28
with owned STOP and global shutdown. Use it by itself, without `--self-test`,
and avoid manual keyboard input during measurement. Replay with
`rtems/residentnet/verify_play_bulk.py` plus the full system verifier.
See the [dated results and reproduction](../../../artifacts/notes/doom-bulk-20261014.md)
for the full evidence: mean transfer **5.447 → 0.509 s**, delivered FPS
**0.167 → 0.999**, with all 30 full audit pairs and STOP/drain passing.
The earlier native/card pixel discrepancy remains documented.

## Release-priority and private-memory options

For the bounded ping-pong runner, `--release-schedule priority` gives pending
frame releases precedence between complete audit reads and makes validated host
frames available to HTTP before release finishes. `--frames 520` extends the
acceptance run; it requires the existing ping-pong/WAD loading-test options.
`abba` and `baab` are comparison schedules, not normal play policies.

Build with `--fast-memory` to enable the pinned private Newlib's word-copy/fill
paths for memcpy/memset. This is separate from RTEMS's libc and from Doom's
explicit calloc/realloc loops. Priority is now the default for Doom ping-pong; `--release-schedule baseline`
retains the comparison policy. The memory build remains opt-in. Exact binaries,
long-run comparisons and reproduction commands are in
[`release-priority-20261015`](../../../artifacts/notes/release-priority-20261015.md).
All ownership, full-audit, guard and STOP checks remain enabled.

### Qualified renderer candidate

Add `--fast-render` to the build command for exact span improvements and selective
BSP/plane/drawing compilation. Four matched full-audit runs reach 5.334 FPS versus
4.831 baseline, with identical images. It remains opt-in for broader interactive
qualification. See [renderer instructions](../render/README.md) and
[full evidence](../../../artifacts/notes/render-20261015.md).


## Runtime quality selection

Add `--runtime-detail` when building to permit high/low detail selection within
one engine binary. `--low-detail` then sets only the initial preference. Use F5,
Doom's Options menu, or **Toggle detail** in the browser. With CPU profiling,
the browser button reflects the actual renderer mode from the latest frame.
Without `--runtime-detail`, fixed-detail profiling builds keep their prior behavior.

The bounded ping-pong acceptance runner rejects interactive keyboard input and
hides the quality button. In explicit `--pipeline-test` runtime-detail acceptance,
it injects two F5 presses itself and checks the actual low/high/low transitions;
CPU/frame profiling is required for that test. It is not an interactive play session.
Normal interactive builds must omit the test-only ping-pong/WAD-profile options.
See [quality validation](../../../artifacts/columns-20261015/QUALITY.md).

Future quality-reducing experiments must have independent switches and preserve
the normal renderer. Exact `--fast-render` and `--fast-columns` optimizations are
separate from quality selection; benchmarks must use matched detail settings.

### Exact BSP point-side candidate

`--fast-point-side` selects the defined exact helper described in
[point-side validation](../point_side/README.md). It remains opt-in; omitting it
keeps the original `-O0` comparison workaround. Specialized C columns also remain
opt-in (`--fast-columns`); recent measured builds explicitly enable them with
`--fast-render`. These switches do not reduce render quality. Exact FixedDiv is
already the playable default, with `--no-fast-fixed-div` retaining the original.
