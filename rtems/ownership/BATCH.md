# Persistent resource ownership — automatic 16-step batch

1. Audit the pinned RTEMS mutex, owner-release and task-restart implementations.
2. Define ownership, cancellation, reference and generation contracts.
3. Implement a shared native/target ownership policy.
4. Add a persistent RTEMS profile with real priority-inheritance mutexes.
5. Measure a blocked waiter and inherited owner priority on the card.
6. Cancel at an owner checkpoint: rollback, release, acknowledge and retire.
7. Defer cancellation while a software buffer lease is outstanding.
8. Reject stale generations, wrong tickets, duplicate completion and new leases.
9. Restart a clean retired owner with a new generation in the same RTEMS instance.
10. Refuse a supervisor's attempt to release another task's mutex.
11. Quarantine owner and waiter; prove an unrelated worker continues.
12. Require explicit terminal quiescence before host RAM restoration.
13. Test premature final close and safe resource retention on the card.
14. Replay hardware traces through the exact native policy and run regressions.
15. Preserve original builds/captures and restore production IPv6 HTTP.
16. Document results and remaining limits, verify the Git inventory and commit.

This profile keeps tasks and resources resident across bounded host callbacks.
It does not yet combine these ownership rules with asynchronous timer preemption,
claim exclusive firmware takeover, or operate a physical DMA engine. Buffer
leases in this batch are software-reference tests, not hardware-I/O acknowledgements.
## Completed results

Steps 1–12 passed implementation, native checks and actual card execution.
The 48-callback smoke run and three 371-callback sessions completed 61 owner
cancellations with rollback/handoff, four normal commits, 65 clean restarts,
four quarantines and four full normal closes. Each longer run used 22 epochs.
The same RTEMS objects and guarded stacks persisted within each session.

Step 13 deliberately closed with a mutex owner and blocked waiter. Captured
retention was `[ownership_open=1, pending=0, exec_dirty=1, stage_dirty=1,
dma_present=1, bar_present=1]`; module refcount was 1. Ordinary unload failed,
and a later snapshot was identical. No restoration transaction followed refusal.
Evidence was archived and verified locally before the recovery reboot.

Step 14 replayed all original requests through the exact native C policy and
all real reports through the C host gate under ASan/UBSan, including damaged
report checks. Native regression suite passed. Separate final tests also cover
epoch/ticket exhaustion and repeated cancellation without duplicate acknowledgement.

Step 15 recovered from boot `580ce0b9-ef5f-415d-8cde-ad8b30539db7` to
`c9286a38-14ec-4ac1-9e1e-ad54e6e8ce5a`, with no retained module/driver.
A further 48-callback session passed with the same target/module and full close.
It also captures the finalization log separately: the normal close resets the
transport log, so earlier archives preserve final responses but not that message.
Fresh production preflight/open passed; IPv6 HTTP returned 200 from the Mac.

Totals including the recovery run: **1,209 successful callbacks across five
normally closed sessions**, **62 rollback/handoffs**, **five normal commits**,
**67 clean owner restarts**, **five quarantines**, plus **three callbacks in the
intentional retained-close session**. Every original response matches the native
policy. All five normal closes restored the full 512 KiB snapshot and unloaded.

Step 16 records the contracts, source audit, scope limits, next integration gate,
STORY narrative, Claude guidance, binaries and raw captures in Git with the
artifact manifest. See the [bundle](../../artifacts/rtems-ownership-20261011/README.md).
No flash writes or forced unloads were used.
