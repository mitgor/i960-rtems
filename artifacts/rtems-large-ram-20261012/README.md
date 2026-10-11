# Exclusive large RAM / workspace batch — 2026-10-12

The final 12 MiB image passed on the card and passed independent replay.
The post-run reboot returned and cooperative public IPv6 HTTP is restored,
verified HTTP 200 from the Mac. No flash write occurred.

Raw captures and exact binaries are stored in the five named `.tar.xz` archives,
following the repository's evidence convention. Extracting an archive recreates
the directory names used below. Each archive contains its own `SHA256SUMS`, and
every member was checked before packaging completed. Readable replay/layout/
latency summaries are also in `evidence/`. The outer `SHA256SUMS` covers archives
and reports. No visitor database was archived.

## Completed physical checkpoints

| Capture | Candidate | Result |
| --- | --- | --- |
| `initial/live-1` | 1 MiB | Passed two dual-stack rounds, saturation, deliberate loss, STOP and replay; initial diagnostic revision 0 |
| `mib-4/live-4` | 4 MiB | Passed three rounds, live 12 KiB stack objects, full reserve scan, STOP and replay; revision 1 |
| `mib-10-failed/live-10` | 10 MiB | Four startup RAM passes and ongoing guards passed; TCP echo timed out; no final drain acceptance |
| `mib-10-host-check-failed/live-10fast` | 10 MiB | Six rounds / 84 client cases completed; full reserve scan and 128 KiB workspace release reported; host checker rejected a real cross-page shutdown transition, so this remains an incomplete session |
| `mib-12final/live-12final` | 12 MiB | Passed 35 minutes, 48 rounds, full reserve scan, workspace proof, deadline drain and independent replay |

The card reports 16 MiB. All regions start at `c0240000`. Workspace is 256 KiB
and three Classic tasks request 64 KiB stacks each, with a fourth reserved slot
for the idle task. Separate task IRQ stacks remain in the upload. The application
heap stays 171,824 bytes; the rest of the candidate is a checked reserve, not a
malloc grant or executable-loader extension.

The first two successful captures replay from their local image and module
folders. `initial/source-1.tar.gz` and `historical-sources.tar.gz` retain source
snapshots for the evolving earlier images. `build.json`, ELF, raw image, symbols,
map, disassembly and exact Linux module are kept per capture. The two failed
sessions are deliberately retained and must not be counted as accepted runs.

## Findings that changed the implementation

- RTEMS initialization used to run in the ARM callback before takeover. The new
  profile defers it until engine isolation, owned exceptions, held SCSI reset and
  large-RAM pattern admission complete. The original cooperative path remains.
- The heap worker previously did not service PIO control. A host word could wait
  for the next 10 ms IRQ. Both workers now poll under the same short priority-31
  serialization, and the image-pinned host uses 50–100 us reply polling.
- The first faster 10 MiB run completed all networking, but a status page recorded
  active shutdown before the later RAM page recorded its completion. The checker
  now recognizes an authorized STOP/deadline transition, without accepting a
  partial scan. Deadline transitions can cross the page capture within one second
  of the configured deadline; final parked ticks still undergo the independent
  deadline gate.
- The full reserve scan initially blocked a control word for 4.459 seconds.
  Final code services control every 4 KiB of reserve/workspace verification and
  every 1 KiB of stack-tail validation, only after both task/IRQ contexts drain.
  Packet admission closes at shutdown. Full-scan completion is published only
  after every word passes; the workspace allocation stays live until then.
- The host now journals every control result and packet refusal incrementally.
  Final JSON must reconstruct exactly, avoiding repeated full-history writes
  during long runs. Failed/incomplete records remain evidence rather than success.

## Scope and remaining gates

Four full address-dependent startup passes, selected protected-region hashes,
ongoing guards/reserve samples and a final complete reserve scan provide evidence
for the tested board and exclusive profile. Hash coverage is low RAM through the
candidate base and the candidate end through the immutable code end; mutable
upload RAM and the high tail above `c0f4c000` are not included in those hashes.
Do not turn this into a claim that all firmware-owned RAM has been inventoried.
Expand the protected-tail inventory before a general application/executable grant.

The reserve must next gain allocation, sharing and cancellation ownership before
applications use it. Larger code needs a segmented resident loader; the existing
128 KiB code window remains. RTEMS still has a fixed task/context count. The
[Doom plan](../../game/doom/OS-PLAN.md) orders these gates and the missing runtime,
WAD service, headless correctness, frame/input and endurance work.

## Final acceptance

- Boot: `14d58713-ab6e-4305-9d44-8cc2b8f699a5`.
- Payload SHA-256: `e8ed21867f362f234d5ef3622efa469a577fc4503c6b6e1b81536599c81814c3`.
- Four startup passes: 12,582,912 word comparisons in total across 12 MiB.
- Final scan: all 2,998,256 words / 11,993,024 bytes in the reserve; no error.
- Each worker checked its live 12 KiB stack object 2,101 times. Actual TCBs lie
  in the external workspace, and task IRQ frames lie in distinct external stacks.
- A real 128 KiB workspace allocation was checked in full and freed.
- Parked at tick 210,002; both task IRQ contexts drained; 220,066 application
  allocations freed and 16,402 shared objects retired. Zero final live bytes,
  references or pins. 16,401 cancellation cycles and 64,349 retained-content checks.
- 48 rounds / 672 client cases, 3,812 checked IP packets, 29 retransmitted TCP
  segments. Saturation reached 128 slots with the expected 31 queue drops.
- Two counter carries; nominal mean ISR period 10,000.221 us. Maximum ISR gap
  11,038.232 us. Both large-copy paths spanned interrupts in 209 calls each.
- 130,496 word ioctls: median 0.182 ms, P95 2.931 ms, P99 5.986 ms, maximum
  10.644 ms. Draining: 768 words, median 1.701 ms and maximum 1.845 ms.
  Compare with the preserved earlier 4.459-second blocked scan; this is an
  observational comparison across different runs, not an isolated A/B benchmark.

`evidence/mib-12final-verification.json`, `evidence/mib-12final-control-latency.json`
and `evidence/mib-12final-layout.json` contain the exact values; the archive also
contains these reports and all raw captures. `source-12final.tar.gz` preserves the source
at the start of the accepted card run. Current replay additionally validates
external TCB/frame ranges and requires two timer carries for this duration.
The complete offline suite and focused RAM/control/journal tests passed.

## Reproduction

Use an isolated build directory with the pinned source archives and existing
GCC 3.3.6 i960 cross toolchain; preserve a fresh image/module pair per run.

```sh
python3 project/rtems/build.py --work . --profile residentnet \
  --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared \
  --queue-reclaim --owned-mib 12
python3 project/rtems/residentnet/build_transport.py \
  --out residentnet-module --payload residentnet/kernel.bin
make -C residentnet-module
sudo python3 project/rtems/residentnet/live.py \
  --payload residentnet/kernel.bin --module residentnet-module/dac960auto.ko \
  --output live --secondary-reset --fault-owner --extra-ram --general-heap \
  --heap-shared --queue-reclaim --owned-mib 12 --ticks 210000 --rounds 48 \
  --round-interval 40 --parallel --burst --drop-data --deadline
python3 project/rtems/residentnet/verify.py --root . live
python3 project/rtems/residentnet/control_latency.py live
```

Stop the cooperative service normally before the single-owner card test. Archive
captures before reboot. Never force-unload a resident/uncertain module. Restore
and check the public service after reboot. Visitor databases stay on the host.

## Recovery and service restoration

Final boot: `bdb6d828-c873-4dbf-98b3-8d6f274732b5`. `production/host-status.txt`
records the active cooperative service and its image/module hashes;
`production/http-check.json` records the Mac HTTP 200 check at the unchanged
public IPv6 URL. Visitor databases/statistics were not copied. The new exclusive
profile is an accepted bounded experiment; production remains cooperative autonet.

To replay the accepted archive from this repository:

```sh
tar -xJf artifacts/rtems-large-ram-20261012/mib-12final.tar.xz -C /tmp
python3 rtems/residentnet/verify.py --root /tmp/mib-12final \
  /tmp/mib-12final/live-12final
```

Choose a fresh extraction directory when `/tmp/mib-12final` already exists.
