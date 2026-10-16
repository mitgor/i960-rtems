# Fifteen-step slot-validation batch — 2026-10-11

All fifteen steps completed. Full paired allocation audits remain mandatory on
every request. The kernel module, ownership/return/cache policy and RAM grant are
unchanged. No flash change, force-unload, test retry or reboot was needed in the
accepted card batch. Parallel-task reboots delayed preparation before testing.

| Step | Work | Verified outcome |
| --- | --- | --- |
| 1 | Pin baseline and remote ownership | Exact accepted combined target/module hashes; waited for parallel fault/RAM tests and verified production CLOSE. |
| 2 | Derive remaining cost model | Prior callback 11.218 ms, full audit 11.606 ms; identify occupied-slot and publication hash passes. |
| 3 | Add bounded diagnostic operation | Explicit diagnostic-only opcode, 0–32 repetitions, checked results; no timer/IRQ borrowed. |
| 4 | Independent model and state checks | Oracle covers diagnostic errors and immutable queue/renderer state. |
| 5 | Test limits and corruptions | Bad counts/selectors/requests, 512 diagnostic bit mutations per candidate, complete slot corruption sweeps pass. |
| 6 | Cross-build and inspect | Five isolated i960 targets; manifests and binaries verified. Disassembly retains repetition cap, inner loops, comparisons and outer back edge. |
| 7 | Measure byte reference on card | 67 full-audit requests; hash 1.755 ms/repeat, validation 2.021 ms/repeat. Clean restore. |
| 8 | Word-loaded FNV | Exact four serial byte-order FNV updates, aligned alias-safe loads and bounded prefix/tail. |
| 9 | Word metadata and guards | All original fields and guard bytes checked; unaligned fallback retained. |
| 10 | Differential/boundary tests | Both release/diagnostic profiles pass combined tests. Per candidate: 20,484 hash length/alignment cases, 163,840 corruptions and protected-page boundaries, on Mac/Linux. |
| 11 | Candidate diagnostic measurements | 134 more full-audit requests. Hash 1.317 ms; complete words validation 1.341 ms. Both restore. |
| 12 | Balanced release comparison | Six sessions, 684 replies/audits, identical 80-frame trajectories. Words callback −10.14%, kernel −4.00%. |
| 13 | Two-slot stress | 806 requests, 512 replacements, eight epochs, stale/duplicate/backpressure checks; CLOSE with both slots unacknowledged restores completely. |
| 14 | Restore and replay | HTTP 200 restored; seven binary hashes, five source manifests, 1,691 full audits, 59,284 commands and ten restorations replayed. |
| 15 | Document and preserve | Findings, Claude guidance, game plan and story updated; exact builds/captures retained and Git artifact inventory checked for this commit. |

Steps 8–10 were prepared during isolated builds and the wait for hardware; candidate
acceptance followed the baseline card measurement. The final diagnostic and release
programs remain separate. No performance claim relies on the diagnostic opcode.

Words has lower callback time and validation slope than hash-only, but its extra
0.016 ms aggregate kernel advantage is within host-side variability. That small
increment is not advertised as an established end-to-end win. Both candidates
remain opt-in, and the original paths remain reproducible.

[Measurements, counts, limits and artifacts](../../../artifacts/notes/slotopt-20261011.md).
Next: connect the verified combined queue to the browser bridge with full audits,
input/disconnect tests, and measured displayed-frame delivery.
