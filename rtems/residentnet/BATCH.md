# Resident network batch — 2026-10-11

Thirty work iterations, not thirty card boots. The cache investigation produced
completion leads and ambiguous live reads; **whole-engine completion and broader
RAM reclamation are not established**. Networking advances within the existing
owned allocation without relying on those missing proofs.

| # | Work and result |
|---|---|
| 1 | Rechecked remote boot, production service and existing exclusive isolation contract. |
| 2 | Matched Fujitsu unpacked firmware to the saved card dump; checked 73,608 disassembly rows against bytes. |
| 3 | Located command `4080001c`, eight result/descriptor words and bit-0 wait/ack sequence. |
| 4 | Traced status/mask pairing at `40800008/0a` and firmware error-service use. |
| 5 | Separated the board timer's bit-5 completion from the operation's bit-0 completion. |
| 6 | Traced the DMA0 bit-10 wait and firmware event-bit-6 dependency in the assisted cache path. |
| 7 | Kept global drain and RAM-reclaim proof false; no cache command/mask/ACK writes. |
| 8 | Added two-seed, register-indirect read-only probes. All three bounded phases gave the same address-like values. |
| 9 | Added a temporary CPU D-cache-disable probe with original-state restoration; all three phases still returned address-like values; NMISR zero, ATUCR 0x26, original D-cache status 0x7221. |
| 10 | Compared observe, DMA-disable and bus-isolate bounded sessions; engine controls restored and RAM/unload passed. |
| 11 | Recorded immutable code, guards, mutable RAM, BIO and unreclaimed firmware regions. |
| 12 | Implemented RAM interval/overflow/zero-length checks and an unconditional new-region denial. |
| 13 | Audited linked symbols for workspace, task/IRQ stacks, packet state and lwIP pools inside the existing grant. |
| 14 | Built separate `residentnet` i960/RTEMS/lwIP image and image-pinned Linux module. |
| 15 | Integrated a single-owner lwIP task pump using hardware timer ticks; no lwIP calls in ISR context. |
| 16 | Implemented ordered PIO RX begin/word/commit with length and running-state validation. |
| 17 | Implemented frozen PIO TX read/release and zeroed trailing bytes; no host DMA. |
| 18 | Added serialized host bulk ioctl with epoch, sequence, ownership, completion and teardown gates. |
| 19 | Added a five-second whole-packet deadline and uncertainty quarantine. |
| 20 | Exercised the actual host exchange C function with mock absent/stale replies, deadline and hardware-mask/completion faults. |
| 21 | Tested 1,481 valid input lengths plus malformed ordering, premature commit, TX bounds and parked requests with ASan/UBSan. |
| 22 | First 100-tick network-image bring-up restored and unloaded; subsequent bounded probe matrix also passed. |
| 23 | Card IPv4 UDP echo passed 1, 31, 500, 1,400 and 1,472-byte payloads (1,500-byte IP packet). |
| 24 | Card IPv6 UDP echo passed 1, 31, 500, 1,400 and 1,452-byte payloads (1,500-byte IP packet). |
| 25 | Card TCP echo matched 4,096 bytes in each IP family in both resident sessions. |
| 26 | Resident HTTP returned 200 over IPv4 and IPv6 in both sessions, with no second firmware callback. |
| 27 | Deliberately dropped one card-to-host TCP data packet per IP family; both streams recovered. |
| 28 | Host STOP parked at 533 ticks; target deadline parked at exactly 6,000. Both drained all task IRQs and rejected post-park packets. |
| 29 | Offline replay checked 150 IP packets/checksums and matching TCP streams, rejected 38 corrupted snapshots and verified one ARM per resident session. Full native RTEMS suite passed. |
| 30 | Captured sources, target/kernel binaries, traces and restoration/reboot evidence; updated documentation and Git inventory. Production recovery status is recorded in the artifact README. |

The first resident session's reboot was slow/unreachable long enough to request
physical recovery; a fresh boot was subsequently observed. The record does not
establish whether physical intervention caused that recovery. Do not claim
unattended reboot reliability. The second reboot and final production restoration
must be read from the final evidence, not inferred from command success.

## Remaining gates

- Qualify the actual cache register mapping and access semantics; the currently
  observed address-like values do not prove a completion or idle condition.
- Prove cache command/queue completion and any already-issued SCSI transactions
  drained, then enumerate firmware allocations and saved continuations before
  reclaiming another RAM range. No destructive RAM probe is authorized by a zero
  status alone.
- Establish a clean reset/reboot path from retained exclusive mode.
- Extend resident service lifetime, timer accuracy under masked network work and
  sustained traffic testing before replacing production autonet.
- DMA transport needs explicit descriptors, buffers, cache coherency, PCI-master
  permissions and cancellation ownership. Direct Mylex↔NIC is still later work.
