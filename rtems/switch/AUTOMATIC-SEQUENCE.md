# Automatic containment sequence — 2026-10-11

Requested: proceed through the next 10–20 steps automatically. This batch follows
the containment prerequisites before resident RTEMS or network DMA changes.

1. Define critical-section and uncertain-completion acceptance conditions.
2. Add a separate nested-critical-section containment target.
3. Add exact-image host gating for its extended report.
4. Exercise both validators with damaged critical-section evidence.
5. Build the target and pinned Linux module.
6. Test STOP at nested dispatch depth 2 in three fresh sessions.
7. Test STOP at dispatch depth 1 in three fresh sessions.
8. Compose the existing lifetime/retention instrumentation with containment.
9. Test omitted STOP with final user-fd close; preserve before recovery reboot.
10. Test omitted RELEASE with driver unbind; preserve before recovery reboot.
11. Reject a deliberately invalid containment report after real callback completion;
    verify that dirty resources remain retained even when pending is cleared.
12. Independently verify original paired captures, binaries and retention evidence.
13. Verify recovery and restore the production IPv6 HTTP service.
14. Run the full native regression suite and artifact inventory checks.
15. Document measured findings, preserve exact builds, and commit the batch.

No step is complete merely because it appears here. Results and any changes to
this sequence are recorded below as evidence arrives. Permanent interrupt masks,
unbounded critical sections and arbitrary corrupted kernels remain outside this
bounded test contract. No flash programming is part of this batch.

## Results

All 15 steps are complete; this file and the evidence are included in the batch commit. Six initial and six final critical-section sessions
passed. The final module fixes an observed kernel stack-frame warning by moving
the extended decoding array to allocated memory. Both depths deliver STOP before
outer release; controller wake occurs at tick 40 and quarantine at tick 44.
Both complete critical archives pass exact-image, paired-byte, full-restoration
and unload checks; each rejects 240 damaged actual reports.

All three failure tests passed. Omitted STOP/final close and omitted RELEASE/
unbind retained pending/dirty state. Invalid local report/final close retained
resources even after actual completion cleared pending and runner-uncertain.
All refused ordinary unload; no post-injection firmware submissions or unsafe
restoration occurred. Captures were copied and verified before each reboot.

The full native regression suite passed. All three recovery reboots completed;
four distinct boot IDs match the capture identities. Fresh firmware preflight
and paired original staging hashes passed; production IPv6 HTTP returned 200.
The artifact inventory and Git index are verified as part of the final commit.
See [measured details](CONTAINMENT-BATCH.md) for precise limits and next gates.
