> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# RTEMS peer-service yield experiment — 2026-10-15

Functional card audits and replay passed; interrupt-latency qualification remains open. This implements the scheduling lead from parallel chat
“Find i960MC board design guidance” (`01a12b47-c24d-7f81-b310-d62d0b33ae0a`),
whose offline firmware audit identified two continuously runnable, equal-priority
workers and approximately half CPU attribution to Doom. The firmware itself is
parked during exclusive operation. The source audit remains untouched.

## Policy

Opt-in `--peer-yield` on the RTEMS or Doom play builder requires the profiled
Doom/WAD-ring configuration. While owned application code runs, after every complete worker-0 network/control/heap/
shared-peer service pass, it invokes `rtems_task_wake_after(RTEMS_YIELD_PROCESSOR)`.
The pinned RTEMS 4.6.6 source takes its zero-delay `_Thread_Yield_processor` path,
not `STATES_DELAYING`. Both workers retain priority 2/time slicing; controller
priority remains 1. No priority boost, sleep, idle context, timer-rate change,
IRQ work migration or early omission of peer checks is introduced. If Doom
blocks, worker 0 remains runnable and continues servicing. STOP bypasses this
new yield and retains the original equal-priority two-worker arrival/drain path.

Three telemetry words record completed peer passes and maximum gap between
completion ticks (10 ms resolution; includes preemption and service duration).
Version 4 of the existing 65-word read-only WAD profile uses header words 6/7
for maximum peer gap in ticks and completed pass count. Version 2 remains
unchanged. Full replay binds profile version 3/4 to the `I960_PEER_YIELD` build
flag, checks the raw command/reply journal, and rejects measured peer gaps over
100 ticks (one-second acceptance ceiling, not a new guaranteed deadline).
The profile is read after engine STOP; peer counters are individually sampled
while the peer still runs, not an atomic multiword scheduler snapshot.

The initial link exceeded the immutable kernel code window by 80 bytes.
Telemetry implementation was moved into the already owned/audited engine code
window. No linker/memory-map change or protection reduction; `failed-link.log`
preserves this offline failure. A second offline placement in the upload window crossed a protected-page
boundary and was rejected by the existing audit; `failed-page-budget.log`
preserves it. No failed candidate was loaded on hardware.

## Test plan

Use the exact screen-copy engine/settings as baseline, fixed-scene FPS and
CPU/wall timings, cold load and warm restart separately, complete 100-frame
comparison, full paired audits, network/control progress, IRQ/peer gaps,
held-slot stall/resume, STOP and global heap drain. Keep all captured frames,
including four known native pixel differences. Archive and replay locally before
rebooting to release retained DMA mappings and restore the public web server.

## First physical experiment (preserved in `v1/`)

The all-session yield policy passed 100 frames and full replay, delivering
5.321 FPS versus the 4.517 FPS screen-copy baseline. However, engine upload
regressed from 79.615 to 106.514 seconds while first-frame execution improved
116.923 → 95.189 seconds. The report measured 200 ms maximum completed-peer gap.
This prompted a narrower policy: version 4 yields only while the existing
`owned_running` flag is true; preparation/upload keep their original scheduling.
This revision retains the first experiment's exact admitted engine binary and
rebuilds the kernel/transport only. The second physical run completed; results follow.

The initial 65-word profile schema version 3 remains replayable. Final schema 4
identifies owned-execution-only yielding; both use words 6/7 for whole-session
peer telemetry. The first captures and exact sources/binaries are retained in
`v1/candidate.tar.gz` and `v1/card.tar.gz`, with hashes and replay results.

## Final physical comparison (schema 4)

| Measurement | Accepted screen-copy baseline | Owned-execution yield |
|---|---:|---:|
| Frames 21–50 delivery FPS | 4.517 | 5.273 (+16.73%) |
| First-frame execution, seconds | 116.923 | 100.105 |
| Separate engine upload, seconds | 79.615 | 80.086 |
| Warm restart, seconds | 2.780 | 2.830 |
| Renderer elapsed wall time, ms | 209.333 | 177.000 |
| Screen copy elapsed wall time, ms | 12.000 | 9.333 |
| Maximum IRQ gap, ms | 10.546 | **59.855** |

One bounded run per policy, not a soak or statistical confidence interval.
CPU attribution is tick-sampled and becomes phase-biased with voluntary yields:
renderer samples increase from 104.667 to 174.333 ms while wall time decreases.
This is not evidence of increased renderer work or a cycle-accurate CPU-share
measurement. Warm restart did not improve. Maximum completed-peer gap was
200 ms; 45,569 sampled passes are bounded by 45,751 final worker-0 passes.

All 100 frames, 58 full paired audits at unchanged cadence, four paired
DMA/mailbox comparisons, three-second held-slot stall/resume, held frames
99/100 across STOP, network progress and global heap drain pass. First 52 frames
match baseline pixels/palettes exactly; the four known native differences at
29260, 29261, 29580 and 29581 are preserved. Linux and Mac replay pass; 24 frame,
3 WAD and 8 profile mutations are rejected. Host HTTP observation captured 88
frames, all exact, with mean fetch 30.13 ms (HTTP receipt, not browser paint).

**Do not promote to default:** the final 59.855 ms IRQ gap is unexplained. The
first candidate measured 10.623 ms. Existing aggregate telemetry lacks the
phase/PC/time needed to locate it; heap protected-call maxima do not establish
its cause. Instrument long-gap attribution and repeat before claiming bounded
interrupt-latency acceptance. No validation or ownership check was weakened.

## Exact evidence and reproduction

- `candidate-owned.tar.gz`: final `project3`, `build3`, admitted source/binaries.
- `card-owned.tar.gz`: `live-owned`, native frames and card evidence. Adjacent
  SHA256 files authenticate both archives; `source-check.json` compares 795 sources.
- `comparison.json`, `system.json`, `frames.json`, `wad.json`, `profile.json`,
  tamper reports and `local-replay.log`: measured/replayed results.
- `http-observations.jsonl` and `http-verification.json`: bounded HTTP observations.
- `v1/`: first experiment, exact sources/binaries, failures and full replay.
- `rebuild-owned.sh`, `run-owned.sh`, `native-owned.py`, `verify-owned.sh`:
  exact final remote commands. Older scripts without `owned` reproduce v1.

Final kernel SHA256:
`d4aa9a9f632d7161db4eea4dfeda2df2536f9bbd2dcab47a4fba16662d89aaca`.
Engine SHA256 (identical between the two yield experiments):
`e9e43e211d1abf31da7d6a29d9a2c7c42f09ada8e7255af4ec2a2a93d32813dd`.
Module SHA256:
`3062b027c9272b97ead89b6d2c4d63c219f11a1f7b1fe6aa54009855324f6618`.
The fixed engine/settings match the baseline source; rebuilt binary identity
across baseline is not claimed. Pixels are compared independently.

Extract both final archives into one directory and run:

```sh
bash artifacts/peer-yield-20261015/replay-owned.sh /path/to/extracted /path/to/freedoom1.wad
python3 artifacts/peer-yield-20261015/compare.py /path/to/baseline/live-screen /path/to/extracted/live-owned --native /path/to/extracted/native-frames3
```

WAD SHA256: `7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d`.
Never force-unload retained mappings. `restore.sh` restores the unchanged public
IPv6 service after archives are verified locally and a normal reboot releases
the bounded session. Restoration status is recorded in `restoration.json`.

Public IPv6 HTTP restored and independently verified: 200 / 2,891 bytes; boot
`74c0c2d0-c166-4185-9c75-8754a93ce11d`, relay 1658 (supervisor 1656)
owns `dac960auto`. Bounded Doom port 8087 is closed.
