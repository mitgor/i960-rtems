> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Card-initiated ping-pong DMA: bounded acceptance

**Accepted: v10, 256 delivered frames and two held frames, with all full audits.**
The card initiates DMA into two persistent host buffers. Host completion/readback
uses coherent host RAM; the host explicitly releases each generation. This is
an opt-in deterministic producer proof, **not Doom or browser integration**.
Protocol, ownership rules and test commands: [subproject manual](../../rtems/dma/pingpong/README.md).

## Measured result

| Measurement | Result |
| --- | ---: |
| Host-started baseline, frames 5–15 | 7.9213 FPS |
| Card-started delivery, frames 21–256 | 14.2423 FPS |
| Within-run throughput improvement | **79.80%** |
| Card-started rate including first deliberate stall | 11.9789 FPS |
| Steady frame interval, median / mean / maximum | 62.36 / 70.21 / 179.43 ms |
| Card start marker → host completion observation, estimated mean bounds | **8.08–29.67 ms** |
| Observation → full capture, validation, logging and release, mean | 53.59 ms |
| Card start marker → validated capture/release, estimated mean bounds | **61.68–83.26 ms** |

This is one ordered comparison: ten baseline intervals and 235 card-started
intervals, with no slow interval removed. Setup, full paired-mailbox comparison
windows and deliberate stalls are identified separately. It is not a statistical
confidence interval or a Doom FPS prediction. Both modes disable payload CRC,
use the same producer and keep complete byte/guard validation and system audits.
The card clock resolves 10 ms; host clock exchanges bracket the run. Latency
bounds include quantization and observed clock-offset variation. They measure
host observation/capture, not pure PCI DMA time, rendering, HTTP or browser paint.

The first fully accepted implementation, v8, measured **8.1168 → 9.8246 FPS
(+21.04%)** over 80 delivered frames. Its generic uploader still queried engine
command completion after each frame: 59 steady-window queries averaged **42.51 ms**.
V10 queries that independent status once per second while streaming, immediately
after STOP, retaining its overall command deadline and every full audit. It made
16 such queries over 235 intervals (43.88 ms each, 702.12 ms total).

V10 frame-DMA submission previously cost 7.04 ms/call and target completion
polling 3.15 ms/call. Ping-pong host-memory completion checks average 0.059 ms;
release calls average 1.92 ms. These ioctl timings include gate/scheduling waits
and intentionally rejected calls. Full readback still uses 72 one-KiB calls per
capture, exact pattern checking and JSON/binary evidence writes; this remains a
substantial host cost. See `local-pingpong-v10.json` and `local-overhead-v10.json`.

## Acceptance and ownership

- **258 complete guarded buffers**, 19,021,824 captured bytes; all 16,908,288
  payload bytes match the independent generation-specific pattern exactly.
- **20 full monitor/RAM audit pairs**, including **five snapshots that validated
  an active owned DMA lease**; all 145 protected pages remain covered.
- Five complete mailbox/DMA comparisons: frames 1, 2, 3, 4 and 16.
- Both destinations held for **3.109 s**, unchanged, then delivery resumed.
  They were held again for **3.173 s**, with STOP requested while both remained
  occupied. Both captures stayed unchanged after STOP. Final DMA phase is 2.
- Stale/duplicate ownership and premature release are rejected. The driver
  requires all capture chunks before release. Source pins survive until hardware
  completion and task-level cleanup; host destinations survive until release.
- Owned STOP, global shutdown and complete allocation drain pass. Dual-stack
  network checks remain enabled. No forced unload, firmware reflash or RAM remap.
- Maximum measured interrupt gap was **10.520 ms**; nominal mean period 10.000 ms.
- Linux and Mac full-system/frame replay pass. Linux rejects 22 capture/journal
  mutations plus two acceptance-counter/version mutations; Mac rejects all 24
  through `test_replay.py`. `local-tamper-v10.log` records the result.
- Native actual-C tests additionally cover STOP during active DMA, bounded
  hardware-timeout quarantine, the stalled-consumer wait bound, descriptor/guard
  mutations, foreign DMA rejection, legacy-to-ping-pong transition, host exchange
  failures and retained mappings. Hardware timeout injection and active-transfer
  STOP were modeled here; the physical STOP case was a stalled consumer.

## Bugs found and preserved

| Attempt | Finding and correction | Evidence |
| --- | --- | --- |
| Initial admission | Larger service needs 145 protected pages, exceeding 144. Add the entry only in this opt-in build, plus an offline capacity check. Never omit the extra page. | `failed-admission.tar.gz` |
| v4 runner | Missing DMA helper import path. Explicit import path and preflight before hardware ownership. | `failed-client-import.tar.gz` |
| v5 runner | A 600-second timeout was outside the Upload API's accepted budgets. Use the existing 1860-second engine budget; no bound relaxed. Complete client model added. | `failed-client-deadline.tar.gz` |
| v6 baseline | Before activation, the new service failed to execute legacy DMA requests. Delegate to `fd_step()` while inactive; regression covers this transition. | `failed-legacy-transition.tar.gz` |
| v9 faster host | Frames and owned STOP passed, but a full snapshot latched `runtime_error=0x100` on legitimate active DMA. The old host gate had previously serialized these snapshots against DMA. | `failed-system-audit-v9.tar.gz` |

V10 applies the existing exact lease validator to the full system report while
task switching is masked. Only matching phase, pinned source, generation,
approved destination, descriptors and allowed DMA1 state may be normalized in
the local report. Hardware state and sticky errors are never cleared. Descriptor
mutation or another DMA channel still fails. A separate counter proves physical
snapshot overlap; v10 recorded five. Full replay rejects v9 despite its successful
frame/STOP checks (`rejected-v9.txt`). V8 remains a historical bounded pass, not
proof that its unadapted snapshot path was safe at every timing alignment.

A local replay portability issue was also fixed: captures contain **Linux errno
numbers**, which must not be compared to macOS errno constants. The capture bytes
were not modified. The host-shared activation flag is explicitly volatile.

## Exact identities and reproduction

- Kernel: `72f0d10f60746ceae0c58f64040aab1252eee6aaf23a9366e6d4c07b32e69be0`.
- Linux module: `55b7474e02acba59d527179d722316a94335cc88def80f11ea266f278557c4f3`.
- Engine template: `28f11790a47bdc129961095eee53208637e202712ee0eeb3f486238fcf0b6709`.
- Final build/source archive `build-v10.tar.gz`:
  `303cc3e0fec654bd9493d173c5f4a25c83269efb63ab3b80c966b3a043cc96de`.
- Final card/verifier archive `card-v10.tar.gz`:
  `629f3b140842bf05d129017d78d7050312d1dcd2a858242c696ab87d5cdd7e79`.
- Mutable kernel tail: **304 bytes**. Engine service: 16,752 bytes. Protected
  pages: **145**. Legacy builds retain the original 144-entry table.
- Acceptance boot: `e00d007f-d515-4827-b7a2-e15ddefaac08`.

Extract `build-v10.tar.gz`, then `card-v10.tar.gz`, into one directory. Run
`bash artifacts/dma-pingpong-20261015/replay.sh DIRECTORY` from the repository.
The second archive includes the final portable verifier and extra tamper cases;
tracked source contains the same validation code. Earlier binaries/captures are
retained separately for archaeology; use v10 for this accepted baseline.
Unnumbered build logs and `build-evidence.tar.gz` belong to the preliminary v4
build. Final build logs are inside `card-v10.tar.gz`; explicitly named v10 files
and the identities above are authoritative.

`build.sh` and `run.sh` record exact commands. The isolated remote workspace is
`/home/mit/i960-pingpong-20261015`, with dependencies copied from the earlier
column experiment. The final module is `build/residentnet-module-pingpong-v10`,
engine admission is `build/pingpong-engine/admission`, and capture is `live-v10`.
The stress build explicitly rejects Doom/frame-profile admission. Do not run
these scripts over another owner or force-unload retained resources.

## Remaining work

Integrate the accepted protocol into Doom only after coordinating WAD and frame
DMA: **both currently program DMA1 and PCI bus-master enable**. Drain an active
frame transfer before a WAD transfer, or introduce and validate a shared-channel
scheduler. Then validate pixels/palettes, inputs, browser delivery, disconnect,
STOP and all full audits. Adapt the synchronous profiling timestamps separately.
A bulk host-memory capture can remove many ioctl/logging round trips while still
recording every byte and validating all guards. No cyclic DMA list, arbitrary
user DMA address, unbounded frame queue or destination overwrite is enabled.

## Service restoration

All final evidence was copied, hash-verified and replayed on the Mac before a
normal reboot to release retained exclusive ownership. Public IPv6 HTTP
was restored and verified HTTP 200 from the Mac (2,891 bytes). Boot
`2225b1d9-c77e-4cb6-900e-9841154cd719`; supervisor 2569 / relay 2571 now
owns `dac960auto`. See `restoration.json` and `restore-relay.log`. Stop that relay
normally before another card test. The accepted
DMA experiment stays opt-in and does not start an interactive Doom session.
