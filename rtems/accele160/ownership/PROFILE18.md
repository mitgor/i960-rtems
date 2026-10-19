# Profile 18: one-shot QLogic RISC pause/release qualification

This opt-in profile qualifies the first control transition in the
[exclusive SCSI stop contract](STOP-CONTRACT.md). It combines profile 17's
identity/RAM/chip snapshots with one pause/release transaction at ready. It
retains all firmware queues, descriptors and host pins. It does not stop DMA,
change register banks, reset SCSI, alter PCI mastering or reclaim memory.

## Preconditions and transaction

The helper requires the exact physical PCI identity `1077:1016`, memory decoding
and bus mastering enabled, BAR `fff00000`, mapping `8bf00000`, and checked context
`c0600d00`. The captured ring bases/capacities must match 256/128 entries. Pending
head/tail and channel-0 active exchanges must be zero. Both chip passes must agree,
ISR must be zero, the semaphore lock clear, and hardware consumer/producer indices
must agree with their relevant software counterparts. The stale cached request
consumer is not used as a drain gate. These are refusal gates for this bounded
experiment, not proof that SXP/DMA are idle.

Only a nonzero nonce at sequence 1, phase 0 can attempt the transaction. A static
latch is set before any access; failures and success cannot be retried in the
same loaded kernel. Later snapshots change only the current sequence/phase in
the pause extension and retain the original transaction payload. Later HCCR
values are retained evidence, not fresh HCCR reads; the profile-17 chip-index
snapshot is refreshed separately at each phase.

1. Read 16-bit CONF1 `+06` and ICR `+08`. Refuse nonzero bank bits `0300` or
   soft reset. Only then read HCCR `+c0`; refuse PAUSE, RESET, HOST_INT or the
   documented parity-error bit (`04e0` mask). A pre-paused RISC is not ours to
   release. HCCR aliases a DMA register in the DMA bank.
2. Write HCCR **`2000`** once using `stos`, `syncf`, and poll HCCR at most
   **10,000 reads** for PAUSE `0020`. Require other HCCR bits unchanged.
3. On acknowledgement only, write HCCR **`3000`** once, `syncf`, and poll at most
   **10,000 reads** for PAUSE clear. No other command or fallback write exists.
4. Read back CONF1/ICR; if the bank/reset state is wrong, stop before another
   HCCR access. Otherwise capture HCCR, ISR, semaphore and queue indices.
   Require exact control restoration, ISR zero, and unchanged semaphore/indices.

A bounded poll count is not a wall-clock bound on a stalled bus access. In a
failure after a write, the write count records attempted commands, not guaranteed
bus completion. A timeout or changed-state failure preserves evidence and blocks
retries; it does not attempt a speculative release/reset. The host verifier
rejects the run and its existing failure path requests STOP while retaining all
allocations, the pending callback and pins for reset. An owned exception also
retains resources. Successful release is not a claim that RAID/SCSI service has
been restored; these sessions still end in a host reset.

## Record and checks

Words 416..463 of the grant-owned report contain:

| Relative words | Contents |
| --- | --- |
| 0..7 | QPS1, version 1, nonce, current sequence, phase, result, attempt latch, origin sequence |
| 8..10 | CONF1, ICR, HCCR before |
| 11..15 | HCCR at pause, pause polls, HCCR at release, release polls, attempted writes |
| 16..22 | CONF1, ICR, HCCR, ISR, semaphore, mailbox4, mailbox5 after |
| 23..24 | RTEMS ticks before/after (observations only) |
| 25..47 | Reserved zero |

Results: 0 success; 1 prerequisite refusal; 2 epoch/phase refusal; 3 initial
control-state refusal; 4 pause timeout/in progress; 5 release timeout/in progress;
6 unexpected transition/post-state. Shared ack 166 publishes the complete report
last. Host acceptance requires result 0 and two acknowledged writes. No fault/NMI
injection token is added. The actual exception object equals normal profile 5.

Sanitizer tests cover exact ordered accesses, 32 prerequisite perturbations,
initial bank/reset/pause refusals, both poll-limit paths, unexpected pause/post
state, and no second attempt after failure or success. Decoder tests cover
identity, counts, transitions, restored indices and reserved fields. Linux also
runs the existing DMA containment/refusal tests. Physical acceptance exercises
the successful quiet-workload path; timeout failures are simulated, not injected
into the physical chip.

The source basis is preserved in the [stop contract](STOP-CONTRACT.md) and
[artifact archive](../../../artifacts/current/accele160-qlogic-pause-20261019/README.md).

## Physical acceptance and recovery

Session `20261019T131024Z`, boot `5c6b3e15-f29b-4ce1-93f1-47595fdcb283`, kernel
`59590ebc1acc41527f24e7ee098617278a82c8f4fad6db6bcc122b1f284f07c8` passed 64 frames, 5045 WAD reads and
713 external console exchanges without errors. Maximum observed console reply
was 2714.825 ms, not a bound. HCCR before/paused/released was
`0000/0020/0000`, with one poll each and exactly two recorded command writes.
CONF1 was `0074`, ICR `0006` before and after; ISR zero, semaphore 2 and mailbox
indices 37/22 were unchanged. Ticks before/after were both 10; no duration is
inferred from that coarse observation. All four phases retain the same original
payload, while current sequence/phase changes. Owned vectors/stacks/guards pass.

Final STOP acknowledged QUIE/ACK and retained the callback and DMA pins with
no guard changes. After reset, boot `4cdd0e35-4d6a-4430-bbe9-be167070673e` passed paired
full flash reads matching
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
Normal profile-5 session `20261019T131711Z`, kernel
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`, passed 64 frames,
5045 WAD reads and 709 external exchanges. Prompt idle, zero zone loan and
HTTP 200 on gateway 8088 were checked. Leave that normal owner running.
