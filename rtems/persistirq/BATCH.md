# Persistent asynchronous batch — 2026-10-11

Starting revision: `6ec2c0d`. Target: Mylex at `mit@192.168.2.75`, work directory
`/home/mit/i960-rtems-web-20261011`. This batch uses RAM loading; no flash writes.

| Step | Work and evidence | Status |
|---|---|---|
| 1 | Define persistent epochs and terminal-disposal contract | Complete |
| 2 | Audit fixed IRQ-slot lifetime and restart preconditions | Complete |
| 3 | Add two-resource/four-worker dependency graph | Complete |
| 4 | Reject cycles and close admission transitively | Complete |
| 5 | Exhaust 32,400 graph cases against independent reachability | Complete |
| 6 | Keep RTEMS controller, IDs, stacks and ledger across host calls | Complete |
| 7 | Restart only drained tasks with free mutexes | Complete |
| 8 | Exercise A→R0, B→R1→A, C→B with real RTEMS locks | Complete |
| 9 | Integrate nested-critical asynchronous STOP and clean handoff | Complete |
| 10 | Preserve quarantined A/B/C across repeated Other IRQ epochs | Complete |
| 11 | Add generation/ticket completion and explicit FINALIZE gate | Complete |
| 12 | Run 15-callback smoke and three 29-callback matrix sessions | Complete |
| 13 | Test resident early-close refusal after successful QUIESCED | Complete |
| 14 | Replay original evidence, mutate reports, run native suite | Complete |
| 15 | Reboot retained instance, repeat fresh live test, restore HTTP | Complete |
| 16 | Document results and collect source/binaries/evidence into Git | Complete |

## Actual observations

The smoke completed two clean generations, then quarantined generation 3. The
three matrix sessions each completed eight clean generations, quarantined
 generation 9, and ran twelve more epochs of Other. All four sessions finalized,
restored full original RAM/MU state and unloaded. Total normal callbacks: 102;
clean rollback/handoff epochs: 26; quarantined generations: 4; follow epochs: 40.

Nested-depth-2 STOP deferred controller execution until outer release, as did
STOP from depth 1. Clean generation 1 ended at tick 47; generation 2 at 94.
Matrix sessions ended at tick 471 after 21 asynchronous epochs. Each snapshot
showed identical IDs, stack bases, resource/graph pointers and controller pointer
across callbacks. Native and hardware gates require both mutex holder counts,
task resource counts, suspension states, IRQ lifetimes and register probes.
B observed the previous committed primary value after rollback; C observed B's
secondary update. The controller could not release either worker's lock.

The quarantined chain retained A's original task/IRQ frame and B/C task stacks
across every return to firmware. Their four hashes and A's entire lifetime/probe
report stayed identical. Only Other's start count increased. Wrong generation,
wrong ticket and duplicate completion returned STALE; early FINALIZE returned
BUSY. Completing the reference left quarantine intact. Finalization disposed of
the whole instance without unlocking the trapped workers.

A fifth session ran six callbacks: one clean epoch, one quarantined epoch,
STATUS, admission rejection and two Other epochs. It then closed deliberately
without FINALIZE, with one reference outstanding. All control exchanges and
callbacks had completed. The module nevertheless retained:

```
resident_open=1 pending=0 runner_uncertain=0 exec_dirty=1
stage_dirty=1 dma_present=1 bar_present=1 stop_clean=1
```

Ordinary `rmmod` failed; reference count was 1. A later snapshot was unchanged.
The last quiesced callback finished at tick 114. This is an intentional retention
pass, not a normal reclamation pass. Its original paired capture was saved and
verified locally before reboot. No forced unload or later card command followed.

All 126 saved callbacks passed trace/C-gate replay; 5,922 damaged actual report
copies were rejected. The native suite passed, including 94 fixture mutations
and graph checks under ASan/UBSan. Build output has no new target warnings;
ordinary host compiler/BTF notices remain in the original log.

## Recovery status

Pre-test production closed with full restoration verified. Tests ran on boot
`3f649848-173b-40f5-a56f-c83e72b87105`. The authorized recovery reboot was issued
only after evidence collection. SSH initially timed out, then returned with boot
`82403cf7-9150-4581-b032-e029c2dd6484`, the test module absent and card unbound.
A fresh 18-callback session passed three clean epochs, one quarantine and six
follow epochs, followed by FINALIZE, full restoration and ordinary unload.

Final totals: **120 callbacks across five normal sessions**, 29 clean
rollback/handoffs, five quarantined generations and 46 follow epochs, plus the
**six-callback retained-close session**. This includes 84 asynchronous epochs
across all six sessions. Fresh production autonet preflight/open passed,
original paired staging snapshots match the known ROM SHA, and the Mac received
IPv6 HTTP 200 with the Vader page. No flash writes, forced unloads, actual DMA
completion tests or visitor-log exports occurred.

This establishes persistent state across asynchronous epochs, not an interrupt
source left running while stock firmware executes between callbacks. The graph
is fixed at four tasks/two instrumented locks; references are software leases.
Broader dependency kinds, repeated-session fault paths, real DMA completion and
exclusive firmware takeover remain in [the next-work list](README.md#remaining-work).
