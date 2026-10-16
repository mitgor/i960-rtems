> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Two-buffer Doom, optional CRC and binary delivery — 2026-10-14

Status: bounded physical acceptance passed after the two preserved incomplete
attempts below. CRC-on 1.396095 FPS; CRC-off 2.070201 FPS (+48.285%).
The pipeline remains opt-in; CRC remains enabled by default.

First remote workspace: `/home/mit/i960-doom-pipeline-20261014`.
Accepted repeat: `/home/mit/i960-doom-pipeline-20261014c`.
Test boot: `36938147-8109-4114-b7c8-9dc9dcdaf09d`.
Owner: sudo 28436 → runner 28438 → physical test 28439. The public relay was
stopped normally before ownership. Never force-unload retained resources.

## Changes

`game/doom/play/build.py --pipeline` builds a separately admitted two-buffer
engine and DMA-capable RTEMS/host transport. Existing one-buffer modes remain.
`run.py --pipeline` uses CRC by default; `--no-crc` explicitly skips the two
source CRC passes and corresponding host payload CRC. Descriptor checks,
source/destination bounds, generation identity, first-window reread, guards,
DMA completion/quiescence and bounded STOP remain mandatory. CRC-off loses
end-to-end pixel-corruption detection; it does not waive memory ownership.
Image admission hashes, upload CRCs and full system audits are unchanged.

Both 64 KiB card frame slots already fit inside the admitted engine's BSS.
The producer alternates slots and can prepare at most one frame ahead. It
cannot publish another frame until the preceding one is acknowledged. Only
the engine RTEMS task services DMA, at input and backpressure points; no CRC,
preparation or checks move into interrupt context. CPU rendering and CPU DMA
validation therefore do not run simultaneously. The card can render the next
slot while the host reads/checks the completed previous transfer. This is a
bounded pipeline, not an unbounded queue or a second DMA mapping.

The HTTP thread holds immutable host bytes, independent of the card pin. A
32-byte little-endian header contains DFB1 magic, version 1, session, frame,
width 320, height 200, payload bytes 65536, and CRC-enabled boolean. It is
followed by 64,000 indexed pixels, a 768-byte RGB palette and 768 padding bytes.
The browser validates geometry/header/length and expands indices into Canvas.
Its displayed generation comes from the packet itself, avoiding the prior
status/PNG fetch race. No PNG is encoded on the pipeline delivery path.
Host evidence SHA-256 and the per-frame FNV remain enabled.

## Acceptance plan and exact build

Kernel: `7ac15ba79080a635bbddb9ba6c26de4c61206c6086fa0c13d4a8e7ca44e89408`

Module: `d8fcf360acea23bd00812dd2b730b0f55fed315302e32d0d7bd404c40ae59f7f`

Engine: `fad3205ee661157cff07571f690df98ab7993d73f048e2bac8b5936559c381f3`

The fresh build initially lacked archived inputs in its isolated workspace.
Those pinned repository inputs were copied; no hardware was involved in these
build failures. `finish_build.sh` resumes the transport build after adding the
pinned 104-byte runner. The kernel passed the RAM layout audit with 576 bytes
of mutable tail space and 13,024 bytes of separately protected engine code.

`live.sh` runs 52 frames: four exact same-frame mailbox/DMA comparisons (two
CRC-on, two off), then twelve-frame CRC-on/off/off/on blocks. There are no
movement inputs in this measurement. Full monitor/RAM audits run every 60
seconds and at lifecycle boundaries. Both owned STOP and global drain must
pass. The original baseline used movement inputs, so comparison against its
1.376781 FPS is contextual, not isolated proof of each optimization's effect.

Native tests exercise actual target pin/DMA code, 22 host exchange failure
points, both CRC modes, alternating slots/backpressure/STOP/timeout, modeled
52-frame replay and corruption rejection. Actual Canvas code is tested against
valid pixels/palette, a status/generation race and malformed packets. Native
Doom passes 40-frame input/STOP/drain tests and two matching 52-frame no-input
oracle runs. Full physical replay and archive hashes are recorded below.

## First physical run: failed, preserved

Seven frames were delivered; all four paired reads matched, including two
CRC-off frames. The actual browser displayed frame 7 through binary Canvas
(`browser-live.png`). Frame 8 then timed out. Frozen terminal identity is valid:
software abort, heap error zero, isolation checks valid, DMA phase 1, error
zero, last stage marker 13, idle hardware and PCI bus mastering disabled. The
entire retained 73,728-byte destination is still 0xa5. The phase marker is stale
from the previous job; it does not prove frame 8 reached completion.

Double buffering allows rendering/WAD reads while a frame is published. The
host waited for DMA while withholding WAD service; the engine can need that
service before reaching its next task-level DMA service point. The correction
services the existing WAD channel during EAGAIN polling under the same
reentrant gate, without extending the deadline. A regression model refuses
DMA completion until WAD service occurs. All 52 transfers now pass in that
model, with both CRC modes and 27 mutated records rejected.

The failed run is not FPS or shutdown acceptance. Its seven-frame capture prefix
is checked locally, and the full verifier correctly rejects it. Both closed
archives were copied and hash-verified before reboot:

- Failed build: `6537ce9bd686193036cd9c7f83bc91ab25854982d4a889bf03a8e2ebf4f59249`
- Failed capture: `ff13415b307f29992bedeeecc77bdb33ac86808fa8058aedb7d08429416a18a6`

The repeat uses `/home/mit/i960-doom-pipeline-20261014b`, with unchanged kernel,
module and engine hashes. Only host scheduling of WAD service changes. Capture
wall time includes waiting for task-level service/rendering and WAD requests;
it must not be interpreted as physical PCI transfer time.

## Second attempt: stopped after a network startup failure

Boot `948b0697-8330-4b3f-82b0-5dc569230521`, owner 2787 → 2789 → 2790.
A TCP startup client timed out before the third periodic audit. The executor
then waited for Doom while the main audit loop had already unwound. WAD progress
alone was therefore not evidence that the full acceptance was still running.
The attempt was stopped through its authenticated HTTP STOP endpoint; owned
startup STOP passed, with zero rendered frames. No FPS result is accepted.

`stopped-network-evidence.tar.gz` has SHA-256
`fc573ef0ffbea41d884cac29b68061f66764d2b46785b5a5a359668bbe8506a1`.
It contains the exact host sources, failed run and retained result; the unchanged
card binaries are already in the first build archive. It was hash-verified and
its clean owned STOP confirmed locally before reboot.

The harness now records a failed network future, requests owned STOP through
the engine owner, and keeps the main loop/audits alive until the owner exits.
It then propagates the original failure. The network timeout is unchanged and
no failed network run can become accepted. The actual branch regression test
checks error recording and exactly one STOP request. A third attempt uses
`/home/mit/i960-doom-pipeline-20261014c` with the same card binaries.

## Accepted third attempt

Boot `632acf70-7f7b-4957-ba46-4f442af9aa18`, supervisor 2418. The same kernel,
module and engine hashes listed above were reused unchanged. Only the host WAD
service and failure handling changed. All **52 frames**, four exact paired
mailbox/DMA comparisons (two in each CRC mode), 52 guarded captures totaling
3,833,856 bytes, 260 mailbox reads and three malformed/stale refusals passed.
Both source slots alternate exactly as admitted. All **29 full monitor/RAM
pairs**, owned STOP and global heap drain passed. No timeout occurred.

| Measurement | CRC on | CRC off |
| --- | ---: | ---: |
| Pooled delivered FPS | 1.396095 | 2.070201 |
| First twelve-frame block | 1.342011 | 2.079265 |
| Second twelve-frame block | 1.454722 | 2.061217 |
| Mean capture wall time | 598.119 ms | 382.448 ms |

CRC-off increases delivered FPS by **48.285%** in this run. Each block uses
its eleven within-block intervals; pooled rates include those intervals from
both applicable blocks and exclude block boundaries and the four paired reads.
Capture wall time includes render/task-service waiting and WAD service, not
just PCI DMA. Early CRC-on frames include additional WAD demand. These are
bounded no-input scene measurements, not a guarantee for every scene.

Against the previous single-buffer DMA/PNG result of 1.376781 FPS, the new
CRC-on result is only 1.4% higher and CRC-off is 50.4% higher. That earlier run
used forward/release inputs, so this is context rather than an isolated
measurement of double buffering or binary delivery. **This is not a 3–5× gain.**
The renderer, frame copy/FNV, task-level DMA scheduling and host protocol still
consume time. PNG encoding is absent, and both full source CRC passes are
absent only in the explicit CRC-off blocks.

All 52 frames differ from their deterministic native no-input oracle in exactly
seven pixels each; palettes and padding are identical. This retains the known
small native/card rendering discrepancy, not bit-identical native output.
All 52 HTTP binary packets match their saved packet and payload hashes, with
no missing frames; mean fetch latency is 54.309 ms. These are HTTP receipts,
not browser paint-rate measurements. `browser-repeat-live.png` shows the actual
browser displaying frame 52 while the finite endpoint was still available.

## Closed accepted evidence

- `build-evidence.tar.gz`:
  `e96ee72453e937a1209b8df1b5c90b5975576ce52095f40541aecf7512e3b562`
- `card-evidence.tar.gz`:
  `c937ed93c7ebc1b5c99e81aed460ccc3ae5e9c05729722269bf265cf7007c8fb`

Both archives were copied, hash-verified, extracted and fully replayed locally
before reboot. Full Linux/macOS system and pipeline replays pass, rejecting
**35 frame/journal mutations and 24 snapshot mutations** on both hosts. The
accepted build archive includes the exact reused kernel/module/admission,
current host sources, generated resident sources/disassembly and native oracle.
The larger first build archive retains full original engine/compiler inputs
and outputs; unchanged dependencies/WAD are pinned in the existing repository
artifact sets. Reused binaries were not falsely attributed to later host edits.

Standalone JSON reports include timings, per-command costs, native differences,
HTTP observations and local/remote replay. Failed attempts remain separate and
are never included in FPS statistics. Default one-buffer play is retained;
use `--pipeline`, adding `--no-crc` only when deliberately accepting reduced
pixel-integrity detection. Longer interactive and disconnect acceptance remain
future work; no flash programming or new RAM remapping was performed.

## Final restoration

After accepted archives were locally verified and fully replayed, reboot
released the retained mapping. The public IPv6 HTTP service returned **200**
from the Mac with the RTEMS page; relay IPv4/IPv6 startup checks passed.
Current owner: supervisor **2796**, Python **2798**, boot
`d18b781d-a8e7-4604-b8fc-4a048e18506e`, bound `dac960auto`. All three test
reservations are released. See `restoration.json` and compressed HTTP evidence.
The finite Doom endpoint is closed. Stop the public relay normally before new
hardware work; never force-unload retained exclusive resources.
