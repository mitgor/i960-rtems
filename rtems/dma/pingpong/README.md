# Card-initiated two-buffer DMA proof

This is an opt-in, finite deterministic producer experiment, not the Doom browser
transport. Hardware results and exact binaries: [acceptance record](../../../artifacts/notes/dma-pingpong-20261015.md).

The owning Linux driver allocates two persistent, coherent 73,728-byte buffers.
Each has a 4,096-byte leading guard, 65,536 payload bytes, 4,064 trailing guard
bytes and a 32-byte completion record. Neither userspace nor the renderer may
supply a PCI bus address. The driver registers the two payload addresses once.
No per-frame host DMA start, target status query or metadata read is necessary.
The host still releases each slot explicitly after copying its complete capture.

On the card, the owned engine task prepares a finite chain of two DMA1
descriptors: payload, then completion record. The chain terminates at zero.
The record contains magic, generation, slot, length, card source, start tick,
complemented generation and generation again as the final commit word. The
host checks commit, applies `dma_rmb()`, validates identity and guards, then reads
host RAM. Chaining uses Intel i960Rx Developer Manual 272736-002 §20.3:
six-word descriptors, 32-byte alignment, current descriptor completes before the
next. It does not require a cyclic hardware descriptor list.

Source ownership and destination ownership are separate:

- A card source remains pinned until the DMA channel has completed **and** the
  task has checked the terminal descriptor, disabled DMA and restored isolation.
  The renderer can prepare the other card source while DMA runs.
- A completed host slot remains immutable until its exact generation is released.
  A release arriving before target cleanup is recorded but cannot recycle an
  active destination. Stale and duplicate releases are rejected.
- With both host slots occupied, publication waits. There is no overwrite/drop
  policy. STOP remains independently accessible; active DMA is drained in task
  context before clearing the source. Uncertain hardware completion quarantines
  the session and retains its mappings. A normal reboot releases retained
  exclusive ownership; never force-unload it.
- The ordinary host frame ACK cannot bypass ping-pong ownership after activation.
  ISR control work only registers addresses, records releases and reads small
  status fields. Preparation, polling and checking stay in task context.

The experimental ioctl is `0xc4204d0a`, with the established 1,056-byte fixed
buffer, epoch, zero-reserved words and session lock. Operations: 1 register,
2 host-RAM completion check, 3 host-RAM capture read, 4 exact release,
5 bounded diagnostics (including the system-audit lease counter), 6 activate, 7 clock sample. Release requires all 72
capture chunks to have been read. Host failures retain mappings. The prototype
runs far below generation wrap and supports one activation per resident session;
it is not a reusable, unbounded streaming ABI.

Build the stress image with `rtems/dma/stress/build_engine.py --pingpong`, then
build the resident kernel with its admission directory, exclusive 12 MiB
ownership, shared heap, atomic dispatch and `--doom-dma`. The admission rejects
Doom and frame-profile combinations for now: the legacy profile timestamps
assume synchronous completion. See the archived build/run scripts for exact
commands and dependency workspace. `live.py --pingpong --frame-dma-stress 256`
runs 16 host-started frames then card-started frames, full system/RAM audits,
five full mailbox comparisons, byte-exact pattern checks on every capture,
stalls with both destinations held, resumption and STOP while stalled.

Validation tools:

- `test_client.py`: complete client orchestration with modeled transport and the
  real command deadline validation; no hardware/performance claim.
- `test_target.py`: actual target C with modeled registers under 32-bit ASan/UBSan;
  active-transfer STOP, bounded timeout quarantine, descriptor mutation and slots.
- `test_host.py`: actual ioctl code, ownership/range/failure injection, no target
  exchange for completion/read, full-read release gate and retained mappings.
- `test_protection.py`: actual protected-page table; old capacity refusal and
  corruption detection in every page of the expanded table.
- `verify.py CAPTURE`: independent replay of both transports, all capture bytes,
  mailbox pairs, release order, STOP and measured intervals.
- `test_replay.py CAPTURE`: corrupt evidence and require rejection.
- `rtems/residentnet/verify.py --root BUILD CAPTURE`: full system/RAM/network
  replay is additionally mandatory. It must not be replaced by frame checks.

Start-to-host-observation latency uses the existing 10 ms card clock with
bracketing host samples; report bounds, not sub-millisecond hardware timing.
Throughput includes guard copies, exact pattern checks, journal writes, slot
releases and periodic full audits. Synthetic producer FPS is not Doom rendering,
HTTP delivery or browser painting FPS. Doom integration requires separate
acceptance including WAD service progress, browser backpressure/disconnect,
input and STOP, and unchanged pixel/palette comparisons.

The original producer proof deliberately excluded Doom. Doom has a concrete additional constraint: `wad_target.h` and the
frame path both program **DMA1** and PCI Command bus-master enable. A renderer
WAD miss during an outstanding frame DMA must first drain that frame transaction
or use an explicitly validated shared-channel scheduler. Calling the current WAD
DMA routine concurrently would correctly fail its idle check. The initial admission was therefore restricted to a zero-WAD-read producer.
The opt-in Doom integration now drains DMA1 in task context before publishing a
WAD request; see `../../../artifacts/doom-pingpong-20261015/README.md`.
The Doom runner has passed separate 52-/100-frame acceptance and remains
explicitly bounded pending longer interactive qualification. The finite runner also retains ordinary Upload command
completion queries; these are separate from the eliminated frame-DMA start and
completion protocol and remain a possible host-overhead optimization.

Full system snapshots now use the same exact owned-transaction validation as the
heap isolation checker, with task switching masked during capture and validation.
Only a matching source pin, generation, approved destination, descriptor chain,
guards, phase and allowed DMA1 control/status can be represented as owned activity
in the audit's local snapshot. Other channels and unknown state remain visible;
no hardware register or sticky error flag is cleared. The sixth diagnostics word
counts system snapshots that validated an active lease. Protocol version 2
acceptance requires this counter to be positive. Native tests reject a changed
completion descriptor and an active foreign DMA channel through the actual
system-report wrapper. Earlier v9 evidence demonstrates why this is necessary:
its frame and STOP checks passed, but the unadapted snapshot latched 0x100 and the
full verifier rejected the run.

## Bulk host capture (2026-10-15)

`PingPong.capture()` uses operation **8** of `0xc4204d0a` once per capture,
replacing 72 operation-3 calls. This is a host coherent-RAM copy, not a new PCI
DMA submission. The card kernel, descriptors and source/destination ownership
protocol are unchanged. The first 16 host-started comparison frames deliberately
retain their older transport in the bounded acceptance test.

Operation 8 has an explicitly bounded extended buffer ABI: **73,760 bytes**,
32-byte header `<8I>(8, epoch, generation, 73728, 0, 0, 0, 0)`, followed by a
73,728-byte output area. The ioctl number retains the legacy 1,056-byte encoding;
callers must allocate the full operation-specific size, not `_IOC_SIZE(cmd)`.
The Python client zero-initializes the entire buffer. The kernel validates the
legacy header/reserved input prefix, exact length, session and generation; checks
the completion record after `dma_rmb()` and scans both complete guards. Under
`session_lock`, it copies the entire guarded allocation to userspace in one
`copy_to_user`. It grants all 72 read credits only after that copy succeeds.
A short/faulting copy returns `EFAULT`, does not grant new release credit, and
retains ownership and both mappings. Old operation 3 remains available and now
also grants its individual credit only after successful copyout.

Release remains a separate generation-checked operation. Capture does not ACK,
recycle, rearm or accept a userspace DMA address. Full raw request/response bytes
are journaled; replay accepts both historical chunked captures and new bulk
captures and compares all guards, pixels, palette and completion words.

Tests: `test_host.py` executes the actual ioctl with partial-copy failures and
corrupted metadata/guards; `test_bulk_client.py` asserts a single ioctl and the
exact ABI; `test_bulk_replay.py CAPTURE` checks backward compatibility and rejects
truncated, wrong-length, corrupted and missing bulk journal records. Hardware
acceptance and measured costs: `artifacts/notes/bulk-capture-20261015.md`.

## Release priority and timing

The Doom runner defaults to `--release-schedule priority` for the opt-in ping-pong
profile. A pending release gets the next host I/O gate after its current holder
finishes. Audit reads then hold the gate for one word instead of four; all 64
words are still read from the same frozen page, and packet pumping plus the
1 ms pacing sleep still occur once per four words. This changes lock granularity,
not audit coverage or snapshot cadence. The kernel session lock and all original
slot/generation/guard/release checks remain.

After validating and copying a frame, priority mode publishes the immutable host
copy to HTTP before the synchronous release. It does not release the card buffer
early or queue unbounded work. STOP still drains the existing synchronous path.

Every ping-pong journal call now records `start_ns`, `acquired_ns`, `end_ns`,
`gate_wait_ns` and `ioctl_ns`; `ns` equals their sum. The ioctl component includes
any kernel-mutex/scheduler wait and must not be labeled pure card execution.
`audit-gate.jsonl` records each audit lock hold and exact word range;
`browser-publish.jsonl` records when a validated frame becomes available to HTTP,
not browser paint. Replay validates timing arithmetic, every frozen-page word,
policy and publication-before/after-release order.

For bounded comparison, use `--frames 520 --release-schedule abba` and then
`baab`. Blocks 100–199/200–299/300–399/400–499 run opposite policies in the two
captures. Initial stall, scripted level restart and final held-frame STOP remain
outside those blocks. Full measurements and reproduction:
`artifacts/notes/release-priority-20261015.md`.
