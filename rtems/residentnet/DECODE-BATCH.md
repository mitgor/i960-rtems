# Cache-path qualification and resident networking — 2026-10-11

This follow-up distinguishes the card's selected internal-controller path from
external-cache code in the same firmware. It expands network storage **inside the
existing grant**, not arbitrary DRAM ownership. The cooperative net/autonet and
stock-firmware profiles remain supported; exclusive sessions retain resources
until reboot. No flash changes, cache commands or SCSI operations were made.

## Decode findings

The positive-control probe reads known RAM as `a5a5a5a5`, `5a5a5a5a`, `a5a5`,
`5a5a`, while two reads of ATUCR agree at `26`. With CPU D-cache temporarily
disabled, the suspect 32-bit cache reads still return `40800000` and `40800008`.
They cannot be used as hardware completion status.

The i960 registers are coherent with the internal-controller boot path:

| Register | Observed | Meaning / limit |
|---|---|---|
| PMCON4_5 | `00800000` | Region entry requests 32-bit width, **but** BCON must also be checked. |
| PMCON14_15 / BCON | `0` / `1` | BCON bit 2 clear: region entries are not valid; default width applies. |
| ATUCR | `26` | Direct-address mode bit 8 clear. |
| MBCR / bank bases | `007100f1`, `fe000000`, `e0000000` | Matches the boot's ROM/peripheral setup. Not an exhaustive external chip-select map. |
| DBCR / DRAM base | `b4f` / `c0000000` | Internal DRAM enabled; this is also the firmware sizing routine's probe configuration. |
| NMISR | `0` | No recorded NMI indication; not proof of a valid external register read. |

DBCR's arrangement field is 9, with 64 MiB bank/leaf encoding. **Do not infer
installed capacity from that**: `c004fc40` deliberately installs `b4f` before
alias tests at 4, 16 and 64 MiB offsets. It returns the detected size. This batch
does not repeat the destructive startup sizing test.

The decisive new evidence is in the bootstrap, not the unpacked program alone:

- Flash `fefcb46c..fefcb49c` reads byte `e0400000`, masks with 31 and selects
  internal setup for value 6. A second entry repeats the same selection.
- Flash `fefcc1f0` installs CPU XOR at runtime `c000d540` in dispatch offset `c0`,
  DRAM sizing `c004fc40` at `168`, and internal timer `c0050430` at `164`.
- Flash `fefcc310` instead installs `c004e940` or `c004ea80`, the previously
  recovered external-cache command/completion routines. It installs different
  status/mask hooks and external sizing `c004f9d0`.
- The live dispatch pointer is `c0110780`; offsets `170..18c` match the internal
  setup exactly. Several are the no-op `c004c3b0`, not external status/ACK functions.
- The internal XOR implementation is a CPU load/XOR/store loop ending in return.
  Its operation completion is synchronous CPU return, not the external bit-0
  wait. This does not drain SCSI or establish ownership of every firmware range.

Bootstrap flash addresses in the disassembly are not their relocated execution
addresses: copied raw offsets `1000..6fff` run at offset + `c0009000`.
`decode_audit.py` checks 48,750 bootstrap rows against bytes; `audit.py` checks
73,608 unpacked rows. The corresponding excerpts are archived with the evidence.
The final probe also reads board selector `6`, primary dispatch `c000d540`, sizing
`c004fc40`, timer `c0050430`, and UART pointers `e0600000/e0600005`. These match
that bootstrap branch. The firmware's detected size at `c00a8718` is `01000000`
(16 MiB). The active CPU-XOR path is qualified; physical absence of every external
engine, global quiescence and new RAM allocation rights are not established.

Register interpretation uses the [Intel i960 Rx manual, order 272736-002](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF),
§12.2–12.3 (PMCON/BCON), §14.5–14.6 (memory-bank/DRAM configuration), and
§16.3.6 (ATU decode). Its configured geometry is not a physical capacity test.

## RAM and networking changes

The resident transmit queue grows from 8 to 32 packets: 49,152 bytes of packet
storage, plus length metadata. The additional 36,912 bytes come from the existing
mutable allocation. The linked image leaves 61,232 bytes before the upper guard.
The RAM audit now checks the entire queue object extent as well as symbol bounds.
No outside range is admitted; `ram_reclaim()` continues to return zero.

The resident-only tick ceiling is 60,000 (nominal ten minutes); the exclusive
non-network profile retains its 6,000 ceiling. The tested deadline is **12,000**,
not the maximum. A successful run performed three rounds of UDP (including MTU
limits), TCP echo and HTTP over each IP family, with a deliberately dropped TCP
data packet in each family. It then stayed resident without host packet traffic
until its deadline, parked at exactly 12,000 ticks, drained both IRQ contexts,
rejected post-park packets and retained the module. There was one firmware ARM
callback, with no firmware submission after takeover.

The first longer run found a real relay defect: `EAGAIN` from an RX-begin rejection
was fatal to the harness, losing its pending TUN packet. The correction keeps
that exact packet pending, services TX and retries only a definite `EAGAIN`.
Timeout, protocol error and other uncertain outcomes still terminate the session.
The failed run and its retained-close evidence are preserved. The successful
rerun did not happen to encounter busy RX; native tests force repeated busy
responses and verify packet preservation and no uncertain-operation retry.

`test_queue.py` exercises the actual queue functions at both 8 and 32 slots:
full rejection, insufficient output capacity, repeated wrap, ordered drain and
oversized input. It runs with ASan/UBSan. `test_pump.py` forces three busy replies
and five non-retryable errors. Existing packet/host/native tests remain applicable.

## Remaining work

1. Use the qualified internal CPU path to revise the whole-engine ownership
   checklist; do not wait on unrelated external-cache status. Check the primary
   dispatch on every future takeover before relying on this board-specific fact.
2. Enumerate firmware allocations, saved interrupt continuations and SCSI-local
   DMA/bus ownership before granting a new physical RAM interval. Firmware size
   reports and address decoding are evidence, not allocation permission.
3. Qualify timer accuracy under sustained load, RX-busy retry on the card, queue
   saturation on the card, concurrent connections and the full ten-minute limit.
4. Establish dependable reboot/reset from retained exclusive mode. Keep production
   on autonet until resident recovery and longer service operation are qualified.
5. Host-RAM DMA and direct-NIC operation still require separate descriptor,
   coherency, PCI-master and cancellation ownership contracts.

## Thirty work iterations completed

These are thirty investigation/implementation/validation steps, not thirty boots.
There were three successful bounded probes, one failed resident attempt and one
successful resident run, followed by production restoration.

| # | Result |
|---|---|
| 1 | Rechecked clean repository, remote boot and current production owner. |
| 2 | Rechecked matching dumped/Fujitsu firmware bytes. |
| 3 | Added fixed decode pages with no arbitrary-address host input. |
| 4 | Added positive RAM controls for both 16-bit and 32-bit access. |
| 5 | Read PMCON and BCON together; found PMCON validity bit clear. |
| 6 | Confirmed direct-address mode clear and coherent ATU reads. |
| 7 | Captured ROM/peripheral decode configuration and NMISR. |
| 8 | Captured internal DRAM registers without changing them. |
| 9 | Ran the first 100-tick phase-2 probe; restored/unloaded. |
| 10 | Separated configured DRAM probe geometry from installed capacity. |
| 11 | Located alternative internal/external sizing implementations. |
| 12 | Found previously missing function references in the bootstrap. |
| 13 | Byte-checked bootstrap instructions and recovered board selection. |
| 14 | Recovered internal CPU XOR versus external command dispatch. |
| 15 | Ran the second bounded probe; read the live dispatch subset. |
| 16 | Ran the final bounded probe; qualified board 6, primary CPU XOR pointer and internal sizing/timer pointers. |
| 17 | Captured firmware's detected 16 MiB size without rerunning destructive sizing. |
| 18 | Expanded resident TX storage from 8 to 32 packet slots inside owned RAM. |
| 19 | Audited the full linked queue extent and remaining 61,232-byte tail. |
| 20 | Tested actual 8-slot and 32-slot queue functions with ASan/UBSan. |
| 21 | Extended resident-only deadline admission and configurable traffic rounds. |
| 22 | Preserved the failed longer run exposing RX-busy handling. |
| 23 | Implemented retention/retry of explicitly rejected pending RX packets. |
| 24 | Tested repeated busy replies and non-retryable uncertain errors. |
| 25 | Ran three IPv4/IPv6 UDP/TCP/HTTP rounds with MTU-sized UDP. |
| 26 | Dropped a TCP data packet in each family and verified recovery. |
| 27 | Verified 12,000-tick deadline, drained IRQs and post-park rejection. |
| 28 | Replayed 247 packets and rejected 19 corrupted snapshots; tested contradictory decode evidence. |
| 29 | Passed the full native RTEMS suite, restored public HTTP 200, and verified the subsequent clean shutdown by another experiment. |
| 30 | Collected exact binaries/sources/traces, documented the failure and limits, and updated Git's artifact inventory. |
