# Continuous execution / hardware lease batch — 2026-10-11

Starting revision: `22b314a`. Card host `mit@192.168.2.75`, work directory
`/home/mit/i960-rtems-web-20261011`. All tests remained on boot
`82403cf7-9150-4581-b032-e029c2dd6484`; no reboot, flash write or forced unload.

| Step | Implemented and verified work | Result |
|---|---|---|
| 1 | Audit parked callback, RAM reservation and current timer/MU contracts | Explicit limited lease; DMA/SCSI excluded |
| 2 | Specify ownership table, acquisition, release and failure retention | Documented in README |
| 3 | Independent READY/GRANT acknowledgement | Passed on card |
| 4 | Monotonic renewal, stale-epoch and duplicate-grant rejection | Passed native and live |
| 5 | Local expiry, deadline precedence, non-renewable cap | Native model and live expiry/cap passed |
| 6 | Remove finite worker instruction budget; keep checkpoint exit | Sustained full-context probes passed |
| 7 | Validate active timer/vector/masks/control on every IRQ | 40,111 checks, zero reported drift |
| 8 | Keep callback pending; serialize independent host control | No stock submissions inside saved lease windows |
| 9 | Preserve FINALIZE and uncertain-resource retention guards | All nine normal closes restored and unloaded |
| 10 | Exercise control admission failures before hardware writes | ESTALE/EPERM/EALREADY observed |
| 11 | Renewed and host-silent one-second execution | Passed |
| 12 | Grant withheld and renewal withheld expiry | Passed; STATUS alone did not renew |
| 13 | Persistent clean restart and transitive quarantine under leases | A/B/C unchanged while Other advanced |
| 14 | 60-second sustained run plus full administrative cap | Both passed with exact stop reasons |
| 15 | Full native suite, original trace replay and corrupted-report gate tests | Passed |
| 16 | Restore production, document, preserve binaries/captures in Git | HTTP 200 verified; artifacts inventoried |

## Results

Nine sessions completed **23 callbacks and 13 continuous leases**. Every session
finalized, restored the original full RAM/MU state and unloaded normally. The
resource-chain session used seven callbacks: two clean generations, quarantine,
follow, reference completion, expiry-driven follow, FINALIZE. Others used one
lease plus FINALIZE. There were nine host STOPs, three expiry stops and one cap
stop. Total successful renewals: 890.

| Case | Lease ticks | Renewals | Stop reason | Evidence |
|---|---:|---:|---|---|
| Initial smoke | 211 | 5 | Host STOP | Full restoration |
| Matrix smoke | 210 | 5 | Host STOP | Full restoration |
| No grant | 512 | 0 | Deadline | No GRANT required to reach safe QUIESCED |
| Granted, no renewal | 513 from READY, 512 from grant | 0 | Deadline | STATUS traffic did not renew |
| Host silent | 210 | 0 | Host STOP | One second with no control call after GRANT |
| Chain clean generations | 211 / 419 | 5 / 10 | Host STOP | Same IDs/stacks; rollback/handoff |
| Chain quarantine and follow | 211 / 210 | 5 / 5 | Host STOP | Frozen A/B/C dependency chain |
| Chain expired follow | 513 from READY, 512 from grant | 0 | Deadline | Only Other advances; original A IRQ frame preserved |
| Sustained run | 12,502 | 291 | Host STOP | 60.009 s grant-to-STOP; 12,516 hardware checks |
| Administrative cap | 24,000 | 559 | Cap | 115.236 s grant-to-release request; 24,014 checks |
| Final module regression | 211 | 5 | Host STOP | Corrected before-RELEASE status capture |

The sustained run recorded 6,255 A IRQ entries and 6,261 Other entries. The cap
run recorded 12,004 and 12,010 respectively. Both drained their continuations
and passed the complete register/condition-code probe. The observed lease clock
was approximately 208 Hz. This is a measurement of this configuration, not a
new bus-clock specification or long-term drift characterization.

During the chain test, A's lifetime report and A/B/C stack hashes were identical
across quarantine, later continuous work and software-reference completion.
Only Other's IRQ entries advanced, ending at 1,191 versus A's fixed 436. The
controller could not release either mutex, and cycle/admission checks remained
in force. Software reference completion did not repair trapped locks.

## Development findings and verification

The initial host build failed because replacement of the old control helper also
removed the `resident_retained` declaration. That declaration and an output-length
constant were fixed before any hardware invocation. The original build failure
log is retained. The v2 module passed the matrix and cap. The final v3 change
preserves the ODB snapshot from **before** RELEASE rather than replacing it with
a later read that could race firmware completion; a fresh live smoke passed.
Target binary is unchanged between v2 and v3. Both exact modules are archived.

Offline replay initially compared Linux errno numbers with macOS errno constants.
The captures were correct; replay now explicitly interprets Linux values 116,
1 and 114. Original raw files were not changed. Initial polling EAGAIN (11)
remains in the later control transcripts.

Native tests compare 192 lease transitions with an independent integer model,
including stale/skipped sequences, duplicate observations, deadline equality,
tick wrap and cap precedence, under ASan/UBSan. The host report fixture rejects
29 new hardware-proof mutations; inherited resource/IRQ gates retain their own
coverage. The full RTEMS native suite passes. Offline actual-report verification
checks all 23 callbacks, immutable bytes and paired final reads, exact binary
identities, identity/quarantine continuity and cleanup, and rejects **1,610**
damaged actual reports. Saved first-command logs prove the grant-to-QUIESCED
window contains no new stock submission or early completion.

The pre-test web service belonged to the intervening CHIP-8 run; its actual
`http-after-chip8/close` was verified and archived. Production restarted into
`http-after-leaseirq`, with fresh preflight/open and paired known-original ROM
SHA. The Mac received the IPv6 Vader page with HTTP 200. Visitor logs are excluded.

## Limits and next step

Continuous means work continues inside a single leased callback without returning
for host scheduling. The 24,000-tick cap is intentional. Stock firmware remains
parked; RAM reservation, timer ownership and eventual callback return are still
part of the contract. This does **not** complete the plan's full-board P2 takeover
gate. No new DMA/SCSI/NIC engine was claimed, disabled or programmed, and no
storage workload ran. Timer-0 interrupt delivery is delayed while masked; clean
return does not establish RAID coexistence or accurate firmware elapsed time.

Next: a separately acknowledged monitor handoff without an outstanding firmware
command, preceded by complete DMA/SCSI/watchdog quiescence and RAM ownership.
Keep disconnect/failed-control/teardown and longer soak tests explicit; the
successful expiry cases still had a host present to observe QUIESCED and send
RELEASE. Production stays on the tested `autonet` profile.
