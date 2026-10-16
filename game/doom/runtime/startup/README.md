# N3: one-shot real Doom initialization and first frame

The opt-in `--visible` variant requires `--startup --checkpoints --point-side-o0`
on the engine build and `--startup --checkpoints --visible` on the platform build.
It skips the cosmetic opening wipe and exits after exactly two presentations.
`visible_oracle.py` accepts repeated native output, records ticks 2/3 and preserves
two 65,536-byte indexed-frame/palette/padding slots. These early frames are
pixel-identical; movement and interactive input are not established.

Admission binds the BSS slot offset and full 131,072-byte reference digest. The
resident gate copies an immutable archive only after normal owned cleanup and
all existing image checks. UPL1 operation 9 reads fixed 1 KiB windows by archive
generation. Every byte and derived PNG is independently checked before browser
publication; the next engine attempt and final drain retire that archive.
[Visible-frame source, exact builds, card evidence and limits](../../../../artifacts/notes/doom-visible-20261013.md).

This candidate replaces the diagnostic engine entry only when built explicitly
with `--startup`, then packed and admitted with `--startup-oracle` and
`--startup-requests`. Earlier diagnostic identities remain separate. The kernel
requires `--wad-batch --wad-poll --dispatch-atomic` and the existing owned 8 MiB
profile. The startup manifest carries the independent host first-frame reference
and exact WAD request trace; the compiled identity checks canonical image,
metadata and executable text as before.

The entry runs the actual pinned DoomGeneric engine with Freedoom Phase 1,
`-mb 6 -nosound -timedemo demo1`, and explicitly nonexistent read-only config
paths. The platform accepts the negotiated WAB1/4096 ABI. Game time is virtual
(starting at zero, advanced by sleep/tic steps) for repeatability; the startup
budget uses the independent real RTEMS clock. This is not a real-time game loop.

In the default startup build, the first `DG_DrawFrame` copies indexed pixels and palette, computes the existing
FNV hashes, and exits through the owner-local setjmp boundary. STOP and the
1,800,000 ms startup budget are checked at safe points, including after a complete
cache read returns (never while cache assembly owns a destination loan). The
five-second deadline on each runtime read remains unchanged. The host only
permits the extended 1,860-second command timeout for engine command 18; uncertain
completion is never retried or reclaimed. Arbitrary CPU faults still require the
existing quarantine/reboot path, not a promised cooperative return.

After a boundary exit, the WAD backend closes, owned buffers/loans drain and the
private platform retires. Since this is a one-shot image, the complete private
allocation table is released after abandoning engine globals; no attempt is made
to resume them. Application file descriptors are retired with the private image.
Kernel libc is untouched. The kernel independently checks the output contract,
ends the owner scope, authenticates metadata again, reverses only authenticated
text relocations, hashes executable bytes and cancels the image. Unexpected
identity, output, scope or text conditions quarantine it.

Result words retain the twelve-word reporting channel. Version 2 is mandatory:
magic, version, requested 6 MiB zone, pixel FNV, palette FNV, frames, first-frame
completion, peak private bytes, peak blocks, outcome, retired, boundary code.
Normal completion requires exactly one frame with the compiled reference hashes,
outcome 0 and boundary 213. Controlled STOP is outcome 2 / boundary 210; deadline
is outcome 4 / boundary 212; engine errors are outcome 3. Failure is not reported
as a valid frame. Host acceptance additionally rejects any unexpected outcome.

## Private layout contract

Startup builds use GCC i960 `-mold-align` for both the engine and its private
Newlib/platform. GCC 3.3's default i960 aggregate rounding raises many records to
16-byte alignment, while Doom's zone allocator promises only pointer-size
alignment (four bytes). For example, default i960 `side_t` is 32 bytes and
`memblock_t` is 32 bytes/aligned 16; the compatibility layout uses 20 and
24 bytes/aligned four, respectively. Packed WAD records remain unchanged.

`test_abi.py` compiles actual Doom definitions, including `z_zone.c`, and checks
55 size/alignment/offset constants against the 32-bit host. The runtime API is
still 96/128 bytes with identical callback offsets. This setting stays inside
the private engine; RTEMS and its libc keep their existing ABI. The first physical
hang did not yield a fault PC, so this independently established portability
fix must not be presented as a proven explanation of that hang by the retry: that retry reproduced the same first texture-request divergence and timed out.
An exploratory interpreter reproduces the complete host request trace with the
compatibility image; it models runtime services and cannot accept hardware.

## Host proof

`test_native.py` runs the actual engine with private Newlib against the real
8 MiB allocator. It models the retained 64 KiB + 96 KiB proof buffers and a
900,000-byte pinned image reservation after the original 1 MiB layout proof.
Admission refuses an image larger than that reservation. This matters: keeping
the full temporary 1 MiB reservation while allocating the initial screen buffer
fragments the only contiguous 6 MiB hole and is an incorrect native model.

Cases: first frame, STOP after 100 WAD reads, real-clock deadline at read 100,
read failure at read 100, and a repeated first frame in a fresh process. Each
case must close/retire and return the real heap to its two retained proof buffers,
then drain fully. The instrumented build applies ASan to engine memory accesses
and ASan/UBSan to the private library/port and guarded allocator. Legacy private
platform and diagnostic-entry regressions remain separate.

The first-frame reference is checked byte-for-byte against the existing corpus:
64,000 indexed bytes and 768 palette bytes, frame 0 at gametic 2. This first
presentation is the mostly black initial wipe transition, not a completed
visible level frame; later bounded frames are still required for a useful display. Request tracing
records all 4,747 cache requests for the independent physical wire audit. Native
success is not card acceptance. See the artifact record for physical status.

## Host scheduling and aggregate budget

The initial physical harness forwarded packets only between complete snapshots.
WAD fragment assembly takes the shared host I/O gate; even though a frozen page
holds that gate for only four words at a time, waiting between groups can keep
the main thread away from TUN forwarding for seconds. The revised host pumps
packets after each four-word group, outside the gate. It still reads every word
of all snapshot, RAM and heap pages. Only the main thread freezes/reads monitor
pages; packet and WAD controls keep their independent buffers. The packet pump
is disabled before startup and after the traffic phase, including parked audits.
Existing EAGAIN-only packet retry semantics and uncertain-write refusal remain.

`I960_DOOM_STARTUP`, emitted only for the owned 12 MiB startup profile, admits a
maximum 540,000-tick (90-minute) aggregate acceptance session. Both firmware
entry and runtime use the same `exclusive/session_limit.h`; old profiles retain
their original limits. This accommodates two full initializations plus image
admission, STOP and final drain. It does not change the 30-minute engine budget
or the five-second WAD read deadline. The new host can schedule up to 90 network
rounds for this profile; physical acceptance remains required.

## Physical acceptance

The host preserves all previous runtime/cache/relocation/owned proofs, checks
CRC-valid altered image/metadata refusal, then runs normal / partial-transfer
STOP / normal in fresh images. WAD data, sequence, order, exact lengths, CRC,
padding, invocation control and final drain are independently replayed. The old
N2 small cache benchmark is not repeated after startup: it is a separate accepted
profile with a different batch sequence namespace.

`engine_replay.py` executes the actual native admission/relocation/lifetime core,
while modeling the i960-only engine call from independently checked output.
`startup_replay.py` checks every physical WAD fragment against the pinned file
and the actual host-engine request trace. This is not an i960 emulator. On-card
frame verification uses the two independently compiled FNV references, not a
full pixel readback; only the host reference pixels are retained at this stage.
Browser rendering and persistent gameplay remain later milestones.


Current physical status: both attempts failed before returning a frame. The
second transferred 27,725 correct fragments and completed 36 network rounds,
but there is no startup STOP/restart, final drain or successful-capture mutation
acceptance. See `artifacts/notes/doom-startup-20261013.md` for the exact evidence.
The failure inspector accepts an explicitly identified final partial RAM page
without treating it as a completed audit; it always returns `accepted:false`.


## Opt-in startup checkpoints

`--checkpoints` on both engine and private-platform builds adds recorded source
patches from `instrument.py`. Admission additionally requires
`--startup-checkpoints` pointing to the actual native record stream. The compiled
identity binds that stream alongside the original first-frame and WAD references.
The owned checkpoint ABI (version `0x20001`, 144 bytes) is deliberately distinct
from the existing 128-byte owned API. Callback offset 128 and reserved words are
checked in both private and kernel layouts.

Stages cover engine entry, each level-loading phase, side texture-ID fingerprint,
player/view coordinates and directions, texture lookup/composite selection, BSP,
planes/masked draw, first-frame hashes, owned exit and cleanup. Scalar hashes
exclude pointers/padding. To bound storage, early lookup records sample texture
indexes divisible by 64 and omit patch-selection records until invocation-relative
WAD request 4,600. Other stages are always recorded. No data transfer is skipped.
Normal native startup records 162 events, including camera and composite records
around the previously observed request 4,675 discrepancy.

The runtime allocates 16,400 bytes from its registered application heap at binding,
retains records through all image invocations, and unpublishes the pointer before
the controller drains that heap. A short runtime lock serializes each publication;
the callback never allocates, waits or accepts application pointers. Overflow
refuses the callback and takes the owned error boundary (214); records are never
overwritten. The host reads a separate frozen eight-word buffer via upload ioctl
operation 7, with unchanged session/epoch/uncertain-state guards. Complete audit
pages, exact WAD bytes, executable authentication and STOP rules are unchanged.

`checkpoint_replay.py` validates the complete raw channel and compares it with the
pinned native trace. Its report always says `accepted:false`: a diagnostic trace
alone cannot certify a frame, cleanup or a complete session. A complete startup
acceptance replay additionally requires normal / partial STOP / normal checkpoint
sequences. The original N3 failure evidence remains separate and unmodified.


## Height and delivery diagnosis — 2026-10-13

The extended opt-in markers and 99-constant ABI proof are recorded in
[the height experiment](../../../../artifacts/notes/doom-height-20261013.md).
They trace the wrong viewing height to spawn subsector/sector selection. A small
scalar probe confirms the exact optimized `R_PointOnSide` body returns wrong
answers outside RTEMS; disabling scheduling alone does not fix it. No full-engine
compiler change or N3 acceptance is established.

`inspect_height.py` validates the wire log before decoding signed height fields;
`inspect_spawn_map.py` independently walks the pinned WAD, with an explicitly
labelled optional model of the captured comparison ordering. `branch_probe.py`
builds bounded probes only; `verify_branch_probe.py` replays their complete loader
captures and preserves semantic failures. Full acceptance still requires normal,
partial-read STOP, normal again, byte-exact reference and all full audits/drain.
Post-render markers are present in the native trace but were not retrieved from
the failed card run; absent records cannot identify a fault PC.

## Narrow comparison workaround and host-confirmed boundaries

`game/doom/build.py --point-side-o0` is restricted to experimental startup builds.
It extracts the unchanged `R_PointOnSide` into its own translation unit, preserving
Doom's real types and license header, and appends `-O0` for that file only. The
remaining engine files, private library and RTEMS keep their original flags.
The expanded `branch_probe.py --expanded --candidate-engine ENGINE_CROSS_ROOT`
requires exact object-text equality with that actual engine function. Its 25-case
corpus covers both axes, signs, equality, neighbouring positions and the original
root/fixed-multiply cases. `verify_branch_probe.py --candidate-only` requires all
25 audited captures to match; the older three-variant failure proof remains valid.

Admission's independent `--checkpoint-barriers` switch enables bounded waits at
spawn 63, display 80, render completion 42–44, frame 50–51 and delivery 81–98.
The ABI and stored record layout are unchanged. The host saves and fsyncs each
selected decoded record before ioctl 8 ACKs its index/generation. The device
requires the active pending record, matching generation and all eight frozen words
read. Two packets carry full-width index and generation payloads: token phases
0 and 1, respectively. The first stages intent, the second validates and consumes
it. Record numbers must never be packed into the eight-bit token index: the first
card batch exposed that error at record 272. The regression compiles the actual
host packet encoder and exercises indices through 512.
The epoch/session/uncertainty guards and full audits remain in force.
There is no automatic retry of an uncertain ACK.

Publication stays under the short lock; waiting occurs unlocked, services control
and periodically yields. STOP exits with owner boundary 210; absent ACK expires
at 3,000 ticks or 10,000,000 polls and reports checkpoint failure 214. No waiting
is added inside pixel-copy loops. A successful ACK establishes a retrieved
boundary, not the CPU location after it. Full acceptance still requires matching
normal/STOP/normal results, complete paired audits and clean drain.

`test_checkpoint_barriers.py` tests the actual runtime wait/control implementation,
STOP and both deadline bounds, persistence-before-ACK, and ten malformed/missing/
duplicate ACK sequences. `checkpoint_replay.py` validates the additional journal
and exposes an incomplete pending ACK without accepting a frame. Existing captures
without the admission flag retain their original read-only behaviour.

The first comparison-workaround batch completed the first wipe frame and STOP,
but refused the repeat ACK described above. See
[the preserved failure](../../../../artifacts/notes/doom-sidefix-20261013.md) and
[the corrected batch](../../../../artifacts/notes/doom-sidefix-ack-20261013.md)
for current physical status; neither native tests nor one frame accept a batch.
