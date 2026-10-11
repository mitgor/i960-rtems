# Exclusive takeover: 30-iteration ledger — 2026-10-11

Each row is a concrete investigation, implementation or validation iteration;
the count does not mean 30 card reboots or claim every hardware engine is owned.

| # | Iteration | Outcome |
|---:|---|---|
| 1 | Record exclusive-mode authorization and preserve the cooperative branch of the design | Existing profiles retained; no flash change |
| 2 | Inspect host topology and block-device paths | Baseline captured; root disk is not behind the Mylex |
| 3 | Obtain exact Intel RP developer manual and provenance | Order 272736-002 and SHA256 recorded |
| 4 | Audit DMA CCR/CSR stop semantics | Active disable suspends; six nonzero control/status words deny admission |
| 5 | Audit ATU bus-master controls | 16-bit command accesses preserve memory decoding |
| 6 | Audit secondary arbitration | Internal arbiter required; six external priorities can deny grants |
| 7 | Audit secondary reset | Documented fallback; retry/ATU-reset side effects kept out of live writes |
| 8 | Audit external local-bus ownership | Manual forbids disabling that master; cache ownership remains open |
| 9 | Research BA-81C15-related Linux code | FlashPoint lead documented; no guessed register access |
| 10 | Implement phase admission and native failure matrix | 512 cases, ASan/UBSan |
| 11 | Run read-only card inventory | Passed, restored/unloaded |
| 12 | Run inactive DMA disable/readback | Passed, restored/unloaded |
| 13 | Run primary/secondary bus-master and grant isolation | Passed; message channel remained usable |
| 14 | Initialize real RTEMS before completed ARM return | Separate task/workspace state prepared |
| 15 | Integrate task-owned preemptive ISR inside parked outer firmware IRQ | Separate vector and two task IRQ areas |
| 16 | Run eight-tick RTEMS baseline | Both workers progressed and drained |
| 17 | Repeat with DMA disable | Passed |
| 18 | Repeat with all phase-2 isolation controls | Passed |
| 19 | Extend isolated execution to 100 ticks | Passed, exact restoration |
| 20 | Implement irreversible resident state and frozen status channel | Sequence remains 1, ordinary writes disabled, close retains |
| 21 | Regress bounded mode with resident-capable target | 100 ticks, clean close |
| 22 | Run resident deadline case | 1,200 ticks, 1,200 task IRQs drained, parked |
| 23 | Exercise resident command rejection and retained close | Invalid index, stale epoch, repeated entry, firmware write denied; module pinned |
| 24 | Save exact binaries/captures and attempt recovery | Local archives verified; reboot did not return promptly; user restored access |
| 25 | Strengthen acknowledgement consumption check | Repeated token cannot use an old reply while IMR1 remains unconsumed |
| 26 | Verify fresh boot and bounded regression | New boot ID, original RAM, 100 ticks and clean close |
| 27 | Run active resident host STOP | Stopped at tick 581, all task IRQ frames drained |
| 28 | Verify parked-state freeze and preserve second retained run | Frozen worker state, idempotent STOP, local archive verified |
| 29 | Reboot and restore production | Forced reboot returned over SSH; original RAM, fresh production OPEN and IPv6 HTTP 200 verified |
| 30 | Replay, mutation checks, document both paths and collect Git artifacts | See verification evidence and commit |

Nine bounded runs restored/unloaded. Two resident runs intentionally retained.
The first resident cap snapshot is at tick 1, before the second worker ran; its
zero progress is valid. A 100-tick bounded report has timer-0 pending (0x1000),
while timer-1 pending is clear. The offline verifier was corrected to express
these actual invariants; neither observation was hidden or rewritten.

Missing: active-engine abort, cache-coprocessor drain, arbitrary DRAM reclamation,
resident network data transport, unlimited runtime and proven unattended reboot.
No physical SCSI traffic or disk workload was attempted.
