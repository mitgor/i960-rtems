# Asynchronous ownership integration — 16-step batch

1. Audit the two task-owned ISR continuations and borrowed-timer boundaries.
2. Define checkpoint retirement versus dependency quarantine and final disposal.
3. Add a separate `ownirq` profile without changing production autonet.
4. Bind the persistent ownership policy to a real RTEMS owner-only mutex.
5. Add a blocked waiter and an independently preempted CPU-bound worker.
6. Deliver cancellation through concurrent host control during a running callback.
7. Measure STOP at nested dispatch depths two and one with a held mutex.
8. Defer owner retirement until an outstanding software lease completes.
9. Validate rollback before waiter handoff and full owner ISR return.
10. Reject wrong tickets, old epochs, duplicate completions and non-owner unlock.
11. Quarantine the owner and waiter without unwinding or reclaiming their stacks.
12. Prove unrelated interrupt-driven work continues after retirement/quarantine.
13. Require timer restoration, safe task/frame state and zero references for cleanup.
14. Test an outstanding lease after real quiescence/completion; retain resources.
15. Replay original captures, run native regressions, preserve builds and recover HTTP.
16. Update findings, narrative, Claude guidance, artifact inventory and Git.

The work uses a bounded one-shot RTEMS instance, two owned ISR areas, one shared
mutex and one software-reference slot. It integrates the ownership rules with
actual asynchronous preemption, but is not unrestricted persistent execution,
physical DMA cancellation, or exclusive firmware takeover.

## Development finding: target ABI padding

The first mode-1 card run completed the callback with all runtime checks passing,
but the host rejected diagnostic word 51. The i960 compiler rounded the eleven
32-bit ownership fields to a 48-byte C struct. Copying `sizeof(resource)` into a
44-byte wire slot overwrote the following diagnostic. Native `sizeof` was 44,
so host-only tests did not expose it. The fix copies exactly eleven wire words.

The strict gate retained resources despite completed control/callback. Ordinary
unload was refused. The original binary, source, paired response, log, retention
snapshot and pre-test production close are saved in `initial.tar.xz`. Offline
diagnosis changes only a temporary copy of word 51 to verify the remaining gate;
the original bytes remain rejected and unchanged. Evidence was copied and checked
before reboot. This is not counted as a successful normal cleanup session.

## Measured matrix (fixed target)

The corrected smoke run and two repetitions of each mode 1–4 passed. All nine
sessions restored full RAM and MU state, then unloaded normally.

| Mode | STOP | Controller | Lease completion / retirement | Quarantine | Final tick |
|---|---|---|---|---|---|
| 1 | 18 | 40 | 44 / 44 | — | 50 |
| 2 | 30 | 40 | 44 / 44 | — | 50 |
| 3 | 17 | 17 | 21 / — | 21 | 25 |
| 4 | 18 | 40 | 44 / — | 44 | 48 |

Clean modes recorded three deferred owner checkpoints, then the waiter observed
`0x10203040` and committed `0x55667788`. Owner IRQ entries/returns were 32/32.
The unrelated task retained one frame (18/17 entries/returns). Quarantine modes
kept owner entries/returns at 11/10 (mode 3) or 34/33 (mode 4), and unrelated task
entries/returns at 14/13. Quarantined owner/task IRQ areas and waiter stacks were
unchanged while the unrelated task advanced for four additional timer ticks.
Every final report had zero faults and 10,000 stable observations.

Mode 5 also completed its real control handshake and callback: STOP tick 17,
quarantine tick 21, final tick 25, one outstanding lease. The host returned
ENODATA (61), retaining `[stop_started=1, stop_clean=0, pending=0,
runner_uncertain=0, exec_dirty=1, stage_dirty=1, dma_present=1, bar_present=1]`.
The module reference count was 1; ordinary unload failed, and a later snapshot
was identical. No command followed rejection. This is a successful refusal test,
not successful reclamation or physical DMA completion. Its archive was copied and
verified before the second reboot.

The earlier persistent `ownership` report copied the same padded structure but
immediately rewrote the next word as its heartbeat, which explains its intact
wire reports. It now also copies exactly eleven words, as does the native replay
oracle. A fresh pinned module and card regression cover that follow-up; the
archived older binaries remain unchanged.

## Final recovery and acceptance

The second reboot returned with the test module absent and the card unbound.
A new 48-callback persistent-ownership session passed with the explicit 44-byte
serialization and full restoration. A further asynchronous mode-4 session passed
on the unchanged fixed target/module (STOP 18, controller 40, quarantine 44,
final 48), again restoring full RAM/MU state and unloading.

Final count: **ten successful asynchronous sessions** (five owner-retirement and
five quarantine), **one intended outstanding-reference refusal**, and **one
preserved initial ABI-report rejection**. The latter two retained resources until
reboot; they are not counted as normal cleanup passes. Offline verification checks
all original paired responses, exact binaries, control handshake, immutable bytes,
normal restoration or refusal evidence. The C gate rejects 308 damaged copies of
actual fixed-target reports in addition to 112 native fixture mutations. The
persistent serialization regression's 48 reports match its native policy oracle.
The complete native RTEMS suite passes.

All sixteen steps are complete within the stated bounded scope. Three distinct
boot IDs match the original requests. Fresh production preflight/open passed,
paired original staging hashes match, and the IPv6 Vader/system-info page returned
HTTP 200 from the Mac. No flash writes, forced unloads, physical DMA tests or
visitor-log exports were performed. Source, original/fixed binaries, captures,
replay results and documentation are collected in the Git artifact inventory.
