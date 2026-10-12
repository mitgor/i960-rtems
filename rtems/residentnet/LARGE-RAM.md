# Exclusive RAM, kernel workspace and task stacks

**Resident upload extension:** [UPLOAD.md](UPLOAD.md) describes opt-in
`--resident-upload`: protected high-tail/code pages, an 8 MiB guarded application
arena, separate bootstrap placement and resident PIO. It replaces the reserve
pattern contract only for that explicit grant. The baseline below remains the
contract when this flag is absent; libc malloc is unchanged.

Accepted on the known card on 2026-10-12: 12 MiB startup patterns, 35 minutes,
48 dual-stack rounds, two timer wraps, complete allocation drain and full final
reserve scan. See [captures and failures](../../artifacts/rtems-large-ram-20261012/README.md).
Compilation alone grants no RAM.

`--owned-mib {1,4,10,12}` requires the release residentnet profile with
`--secondary-reset --fault-owner --extra-ram --general-heap --heap-shared
--queue-reclaim`. Default/cooperative profiles remain available and unchanged.
This is reboot-only exclusive takeover. No flash changes are required.

## Admission and layout

The fixed candidate begins at `c0240000`, immediately above the existing tested
256 KiB region. Sizes end at `c0340000`, `c0640000`, `c0c40000`, or `c0e40000`.
The maximum ends below the original upload/monitor at `c0f2c000` and below cache
descriptors at `c0fe8000`. These addresses belong to stock cache data until takeover.

The original ARM callback now defers RTEMS initialization for this profile.
After it returns, the monitor acquires engine isolation, installs owned fault/NMI
paths and holds secondary SCSI reset. The large-memory admission then checks the
exact board/ROM dispatch/staging identity, disabled DMA state, empty software
interrupt table and no overlap with the parked original frame plus 64 KiB margin.
It disables data cache and runs four full address-dependent write/read passes.
After every pass it compares hashes of low RAM and the region from the candidate
end through the immutable upload code. These detect unintended writes to those
protected intervals, with the usual collision limitation of a 32-bit hash.
Runtime mutable upload RAM is excluded because the test itself modifies state there.
Without `--resident-upload`, the high tail above `c0f4c000` is outside these
hashes. The upload extension inventories and fingerprints the stable upper
intervals before granting the application arena; see its separate contract.

Only after successful admission may RTEMS initialize its external workspace and
stacks. The existing external queue/application heap are then admitted separately.
An error retains the exclusive machine state; it never resumes stock firmware.

| Region | Purpose |
| --- | --- |
| `c0240000..c0240040` | Lower guard |
| `c0240040..c0280040` | 256 KiB RTEMS kernel workspace |
| `c0280040..c0280080` | Workspace/stack boundary guard |
| `c0280080..c02c0280` | Four stack slots, each 64 KiB plus 128 bytes |
| `c02c0280..c02d0000` | Reserved separation; not allocated |
| `c02d0000..candidate_end-64` | Pattern-filled reserve, not yet an application heap |
| `candidate_end-64..candidate_end` | Upper guard |

The Init and two worker tasks request 64 KiB each. The idle task retains its
small RTEMS request within a reserved 64 KiB-capacity slot. Two separate 8 KiB
owned interrupt stacks and the terminal fault stack remain in the original
upload allocation. Workspace increases from 48 to 256 KiB; application heap
remains 171,824 bytes. No executable/upload window is enlarged by this change.

Both workers preserve and periodically check a live 12 KiB stack object across
interrupt-driven execution. A 128 KiB allocation through the RTEMS kernel workspace allocator remains live
through the session, then receives a complete content check and is freed.
Shutdown checks the stack guards and unused tails.
During shutdown, control is serviced every 4 KiB of workspace/reserve checking
and every 1 KiB of stack-tail validation, after both worker/IRQ contexts drain.
New packets are rejected. Completion counters are published only after the entire
scan succeeds, and the workspace proof allocation remains live until that point.

The reserve is sampled every 64 KiB during heap/ownership validation; after tasks
and ISR contexts drain, every reserve word is checked before publishing parked
state. Sparse runtime checks do not detect every transient or unsampled write.

## Control and endurance

The image-pinned large-memory host module uses 50–100 us polling for resident
control replies instead of 1–1.5 ms. Timeout remains bounded by a 20-second wall
clock; initial takeover permits 180 seconds for full RAM testing. Packet polling,
sequence validation, poisoning on uncertainty and resource retention remain.
This changes host reply-detection latency, not the 100 Hz scheduling period.
The host records every successful control and packet refusal in an append journal;
full controls JSON is materialized at finalization. Snapshot capture no longer
rewrites the entire growing control history. Replay checks journal and final JSON
for exact equality, including refusal records.

RAM diagnostic page 2 reports the candidate, passes, word count, error/address,
workspace/stack layout, reserve checks, original frame and actual stack requests.
Both workers poll the serialized channel, including the CPU-bound heap worker;
previously only the network worker and timer ISR did so. STOP acknowledgement
can therefore arrive before the next timer, although controller notification
still occurs on the timer path.

The large profile permits up to 360,000 ticks (one hour); ordinary residentnet
keeps its existing 180,000-tick maximum. Each test still has an explicit deadline.

## Remaining ownership work

The [segmented prototype](../../loader/segmented/README.md) now implements an
guarded arena and image state machine. It is now integrated by the opt-in
[resident upload profile](UPLOAD.md), including an on-card 6 MiB proof. Baseline
reserve patterns and libc heap remain unchanged without that option.

Even a successful 12 MiB test is not an 11+ MiB malloc arena. Next add a guarded
allocator arena to the reserve, replace its immutable-pattern contract with
allocation/reference ownership, and test large allocations, sharing, cancellation,
fragmentation and failure retention. Then provide a segmented loader for larger
code/data, independently of RTEMS kernel workspace. See the
[Doom OS plan](../../game/doom/OS-PLAN.md).

## Accepted image and practical limits

Release payload SHA-256:
`e8ed21867f362f234d5ef3622efa469a577fc4503c6b6e1b81536599c81814c3`.
It contains 129,616 bytes of text, leaving only 1,456 bytes in the immutable
128 KiB window. Its payload is 374,788 bytes and mutable upload tail has 83,952
unused bytes; neither is an automatic application allocation grant.

Word ioctls across all phases: 130,496 samples, median 0.182 ms, P95 2.931 ms,
maximum 10.644 ms. The 768 reads classified by the last status as draining had
a 1.845 ms maximum; the complete final scan still took several seconds.
The 11.038 ms maximum ISR gap and 0.668 ms maximum heap-check section show that
larger reserve sampling has a cost. Do not claim a universal latency bound or
an IRQ-latency improvement. Fast active PIO currently relies on worker polling;
Doom needs a service hook or an independent control service.
