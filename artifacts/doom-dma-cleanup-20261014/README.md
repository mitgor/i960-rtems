# Doom DMA completion diagnosis — 2026-10-14

Status: two full 28-frame comparisons passed, including the exact earlier
target binary. DMA FPS improvement is measured; **the intermittent timeout is
not yet diagnosed or fixed**. Diagnostic capture is implemented, DMA stays opt-in. The earlier frame-12 timeout is documented in
[the previous capture](../doom-dma-20261014/README.md).

The public relay stopped normally with SIGTERM and released `dac960auto`.
First diagnostic workspace `/home/mit/i960-doom-dma-diag-20261014`, supervisor 25843,
Python 25846, boot `91493f0a-3c46-4afa-a40c-6b62ad8304be`.
This owner has exited; its retained module was released by reboot only after
local archive verification. Never force unload retained resident resources.

## Diagnostic changes

Persistent target markers cover source CRC, descriptor publication, bus-master
and channel enable, completion sampling, channel and bus-master disable,
post-CRC and terminal publication. They preserve the original DMA checks.
On a terminal fault, the fault owner freezes the 16-word DMA report, stage,
loop counter and six live registers before other reporting. Read-only terminal
indices 64–95 expose this frozen extension; existing indices are unchanged.

After normal transport poison, a kernel helper attempts a bounded terminal
read: at most two seconds total, 2,000 polls per word, exact epoch and NMF1
identity. It never clears poison, changes DMA controls, ACKs a frame or permits
reuse. The 400-byte `frame-dma-fault.bin` contains four header words (FDF1 magic,
epoch, received count, diagnostic error) and up to 96 terminal words. The last
32 are the frozen DMA extension. `rtems/dma/decode_frame_fault.py` decodes this
negative evidence without treating it as successful transfer acceptance.

Native actual-header tests cover the unchanged pin/release and completion
checks, all 21 host exchange failure points, diagnostic identity and deadline
bounds, and the full comparison client/replay. Two native 28-frame Doom runs
match. The admitted Doom engine remains unchanged.

## Exact diagnostic candidate

- Kernel: `f7b62db481d9bbdaddf5affe1c6733ab63a50a065271b6e49c80a6df89def55b`
- Module: `166ec4bda0eb6e55a693f2d2ad81df7ee1319b9e586cfc4696d75d13573dceea`
- Engine: `9f2472c900bb724e7a69b2490e083c4c633520e1d525623398db2e36f2c1e173`
- `diagnostic-build-evidence.tar.gz`:
  `4df77e9358739ccd707a55205527700697de5bc7ac92dd55ac7c96192e28ce2d`

The exact sources, build outputs, disassembly and native runs are copied and
hash-verified locally. Pinned source/newlib symlinks refer to existing repository
archives. RAM layout passes with 576 mutable bytes free; protected engine gate
code is 12,304 bytes and upload code 28,304 bytes.

## Acceptance protocol

Four complete same-frame DMA/mailbox comparisons, then 6-frame mailbox/DMA/DMA/
mailbox blocks; all full monitor/RAM pairs and native/previous-card comparisons;
owned STOP and global drain; independent replay and tamper rejection. Measure
transfer latency, server delivery FPS and HTTP receipt timing separately.

## Instrumented run completed

All 28 frames, four same-frame pairs, 16 complete guarded DMA captures, 1,040
mailbox reads, planned inputs/ACKs, owned STOP and global heap drain passed.
All **28 full monitor/RAM audit pairs** passed, including post-transfer and
terminal audits. Independent full replay and 30 frame/24 snapshot mutations
passed. The maximum recorded IRQ gap was 10.517 ms.

Mailbox delivery measured **0.965947 FPS**, DMA **1.383805 FPS**: **43.259%**
higher. Mean transfer time was 0.514642 versus 0.224330 seconds (2.2941×).
All 28 buffers exactly match the previous physical mailbox capture. The known
small native/card pixel differences remain unchanged. The Mac observer fetched
all 28 named PNGs with matching hashes; mean fetch time was 58.54 ms. These are
HTTP receipts, not paint-rate measurements. `diagnostic-browser.png` shows the
actual browser displaying frame 28.

`diagnostic-card-evidence.tar.gz` SHA-256:
`4e3ccc1e74d78b14a70a6f0f64ac0c9c6a5af5db71c1de144208d259d5767d34`.
Copied, hash-verified, extracted and fully replayed locally before reboot.

**This does not establish a root-cause fix.** Phase markers and a per-poll RAM
store change code generation and timing. A controlled repeat was subsequently run in
`/home/mit/i960-doom-dma-repro-20261014` using the exact earlier target binary
`d0f89f2dd509d1ed26d3b4e2213d6437f09e63d9127c6e0e462fce7ee3ad3ce4`.
Only the Linux module gains failure-only terminal reads; its hash is
`4eaba3be9e3d209ea113b1da943113602b4379ac41ec425c67ecd6d23fc3fa6e`.
That earlier target supports terminal words 0–63, so a partial 64-word fault
capture followed by a diagnostic timeout is expected if it enters its fault
monitor; it cannot supply the new phase extension. Normal success paths and
all audits are unchanged. The first run was released by reboot after local verification.

The successful target reported 57–63 hardware polling iterations per transfer,
well below the unchanged 200,000 bound. Across all sixteen DMA frames, submit
ioctls averaged 0.808 ms, successful final-report ioctls 10.354 ms, and 1 KiB
coherent-buffer read ioctls 0.0111 ms. The 711 pending polls averaged 3.172 ms.
Those command timings exclude Python logging/sleep and are not the hardware
transfer duration. Complete DMA delivery still includes both target CRC passes,
all guards, report and generation checks, complete capture and first-window
reread. No validation was dropped to obtain the FPS figure.

## Exact earlier target also passed

The controlled repeat ran on boot `9b2805db-ad04-4649-a6fa-59c2b155557d`,
supervisor 2558 / Python 2563. It passed all 28 frames, four byte-exact pairs,
16 guarded DMA captures, 1,040 mailbox reads, all input/ACK events, owned STOP
and global drain, with **28 full audit pairs**. Full replay and 30 frame/24
snapshot mutations passed. All 28 images match the earlier physical mailbox
run. The maximum recorded IRQ gap was 10.659 ms.

| Build | Mailbox delivery | DMA delivery | FPS increase | Mean mailbox / DMA transfer |
| --- | ---: | ---: | ---: | ---: |
| Instrumented target | 0.965947 FPS | 1.383805 FPS | 43.259% | 0.514642 / 0.224330 s |
| Exact earlier target | 0.968993 FPS | 1.380308 FPS | 42.448% | 0.509132 / 0.225325 s |

Both use the same four dual-read frames followed by mailbox/DMA/DMA/mailbox
six-frame blocks. These are bounded single-scene results, not general gameplay
or browser paint-rate claims. See both `*-measurements.json`, `*-journal-costs.json`
and `*-http-summary.json` files for separate costs and HTTP observations.
The repeat browser screenshot was taken after the finite endpoint closed: its
retained image and “Failed to fetch” label are not a live-service acceptance.

Repeat build archive SHA-256:
`9b5904556a604d77bdc9e2f5730cdebc23bd3c23124cd3f4ecc4c77d985023a7`.
Repeat card archive SHA-256:
`c7316e280ed6a63edcc45b4ab8b25beab4fb17aef3cacfc3c557b00a3e141b09`.
Both are copied and hash-verified locally; the card archive was extracted and
fully replayed before the recovery reboot. The target in the repeat archive is
copied unchanged from the previous accepted build inputs in
`../doom-dma-20261014/build-evidence.tar.gz`; its project directory supplies the
new host builder, not a claim that its instrumented target sources produced
that old target binary. `build_repro.sh` makes this distinction explicit.

## Diagnosis and remaining work

The earlier timeout is **intermittent**, not reproduced in these two complete
runs. The exact old target passing disproves any claim that instrumentation is
a demonstrated cure. There is no new physical terminal fault record to decode;
the new failure reader has native modeled coverage, not live fault-path
acceptance. No timeout was enlarged, no completion gate removed, and no
uncertain mapping was manually released. DMA remains opt-in.

The next useful experiment is a fast repeated-frame stress harness using the
same pinned-frame target and kernel path, avoiding a 23-minute WAD startup for
each attempt. Preserve all full audits; deliberately cover timer interrupts
across DMA polling and cleanup, retain phase/fault data on the first failure,
and use an unchanged reference binary alongside any proposed correction.
A fix requires a reproduced failure or a demonstrated code defect plus its
regression test. Two passing bounded runs establish performance, not a root
cause or long-duration reliability. The public IPv6 service is restored and returned HTTP 200 from the Mac.
The relay passed its IPv4/IPv6 startup checks. Final ownership is recorded in
`restoration.json`; no test owner remains.
