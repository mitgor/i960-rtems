# Profile 15: QLogic configuration identity and queue dependencies

This opt-in runtime extends profile 14 with five single-dword secondary PCI
configuration reads at the firmware's known selector `1 << 16`. It preserves
normal owned fault/NMI handling, the interrupt stack, console, Doom and STOP.
It does not accept fault injection. Profile 5 remains the normal service.

Before issuing a transaction, the card checks channel-0 metadata: `1077:1016`,
selector 16, register mapping `8bf00000`, BAR `fff00000`. It saves SOCCAR
`12a8`, selects offset 0 and reads SOCCDR `12b0`. Only matching physical
identity permits offsets 4, 8, 10 and 14 (hex): command/status, class/revision,
I/O BAR and memory BAR. It restores SOCCAR and reads it back. The only writes
are to SOCCAR; there are no configuration data writes, BAR sizing, unknown
selector scans, chip MMIO reads, SCSI requests or resets.

This runs from the owned worker while the stock firmware callback remains
suspended and stock interrupt handlers have been replaced. It is not a helper
for concurrent stock firmware use. The transaction count is fixed; bus response
time is not bounded by software. Intel manual 273353-001 sections 15.2.3 and
15.7.46/48 explicitly say that SOCCDR reads issue real delayed PCI cycles and
master aborts propagate to the internal bus. An exception or bus stall must
retain resources and require reset. Restoration is verified on normal return;
it cannot be promised after an exception or loss of bus progress. No status
register is cleared to disguise an error.

The old report and profile-14 extension remain unchanged. Words 320–339 hold:
magic `PCI1`, schema 1, nonce, sequence, phase, result, saved selector, restored
selector, completed read count, reserved zero, five configuration values, and
five reserved zeros. Results: 0 success, 1 metadata refusal, 2 in progress,
3 identity mismatch, 4 restoration mismatch. A mismatch still restores the
selector before returning. Host acceptance rejects all nonzero results, stale
identity/phase/sequence, incomplete reads, changed selector, unexpected memory
BAR, and nonzero reserved words. The shared acknowledgement is published last.

Both source files are included in the manifest's exact inventory source set.
Native tests execute the actual C probe with a simulated register interface,
check the read/write whitelist, metadata refusal, identity mismatch, restore
failure and report boundaries. The owned-runtime C harness tests profile 15's
request/acknowledgement path; assembly preprocessing must equal profile 5.

## Firmware queue trace

`qlogic_firmware.py` checks the expanded runtime SHA and ten machine-code
anchors. `qlogic-dependencies.dis` preserves the relevant disassembly. These
are static dependencies, not observations of the current queue state.

For channel 0, firmware stores a context pointer at `c03e5bc8`; its setup at
`c006ad40` chooses `c0600d00`. The chip mapping from `c0384b8c` becomes context
field `+28`. Setup at `c006ae18` assigns the request ring at `c0600df0`, and
`c006ae38` assigns the response ring at `c0604df0`. For the `1016` branch,
capacities are 128 and 64 entries, with 64-byte entries in the consumer/producer
code: 8 KiB request storage and 4 KiB response storage. These ranges remain
reserved; static locations alone do not establish safe reuse or DMA translation.

| Context field | Evidence and interpretation |
| --- | --- |
| `+28` | Register mapping used for 16-bit chip accesses |
| `+2c/+30` | Pending linked-list head/tail; enqueue `c0070ac8`, unlink `c0070b08`, node link `+10` |
| `+34/+38/+44` | Request base, capacity, current entry pointer |
| `+3c/+40/+48` | Response base, capacity, current entry pointer |
| `+4c/+4e` | Request producer and cached chip consumer; full check `c0070614` reads chip `+78` if needed |
| `+50/+52` | Response producer/consumer; interrupt callback copies chip `+7a` into `+50`, consumer compares indices |

Submission at `c00705c0` builds request entries, updates accounting and publishes
`+4c` through chip `+78` at `c0070aa8`. Callback `c006ef80` checks chip interrupt
status `+0a` bit 2, writes `7000` to `+c0`, handles mailbox state, stabilizes a
read of `+7a`, processes responses through `c006f8f0`, then tries pending work.
Its repeated-read loop is not a bounded shutdown primitive.

The mailbox transaction routine `c006bc30` uses channel field `c0384b68`, saves
and masks chip interrupt control `+08`, writes 16-bit mailboxes `+70..+7e`,
publishes through host-command register `+c0`, polls interrupt/semaphore state,
and restores state on its various exits. Its command-dependent rules for
mailboxes `+78/+7a` overlap queue index use. Calling it blindly from exclusive
RTEMS would re-enter firmware synchronization and completion dependencies.

[FreeBSD's ISP register definitions](https://raw.githubusercontent.com/freebsd/freebsd-src/releng/12.4/sys/dev/isp/ispreg.h)
corroborate the PCI mailbox block at `70`, interrupt control/status at `08/0a`,
and the need to distinguish register banks. Names and semantic interpretations
above are derived from this comparison and the pinned firmware control flow;
no FreeBSD reset sequence has been transplanted to this board.

## Next gate

After physical configuration corroboration, add a fixed **RAM-only** snapshot
of the context pointer, known context fields, queue indices, pending head/tail
and active counters. Validate the pointer against the exact static context;
do not traverse arbitrary linked lists. Then trace the remaining completion
callbacks and chip reset/bus-master isolation order. Quiet queue samples alone
will not permit RAM reclamation. No additional RAM ownership is granted here.

## On-card result

Kernel `61d0b051b536a6dc9598144a9386644140841cde74020b86b08fe1f1428c109e` passed on boot
`bffdea91-6d77-4864-9ca3-d9ceea40bf94`, session `20261019T092238Z`. The live replay verifies
64 frames, 5045 WAD reads, 697 external exchanges and no errors.
Worst observed card reply latency was 1950.706 ms;
this is an observation, not a guaranteed limit. Owned vectors/ISP/guards and
ready/frame32/idle reports passed. Clean STOP produced the fourth matching
configuration snapshot, QUIE/ACK and retained callback/pin evidence.

All four snapshots agree:

| Configuration offset | Value | Interpretation |
| --- | --- | --- |
| `00` | `10161077` | Direct identity 1077:1016, QLogic ISP10160 |
| `04` | `02b00006` | Command 0006: memory decode and bus mastering enabled; I/O decode disabled |
| `08` | `01000006` | SCSI class 010000, physical revision 6 |
| `10` | `00000001` | I/O BAR type bit set, base zero; no sizing write performed |
| `14` | `fff00000` | Memory BAR agrees with firmware mapping 8bf00000 |

SOCCAR was `1000c` before and after every probe. The actual revision is 6,
although earlier firmware metadata at `c0384e7c` was zero. Treat the direct
configuration value as physical revision evidence; do not promote that metadata
word to an authoritative revision. Bus mastering is still enabled, so this
result does not establish isolation or authorize reclaiming the queue RAM.

[Captures, replays and recovery](../../../artifacts/current/accele160-qlogic-config-20261019/README.md).

Recovery completed without physical intervention on boot `96907303-fe0a-4c0f-a7bd-558d044f44c6`.
The accepted normal kernel `55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002` completed 64 frames,
5045 WAD reads and 681 external exchanges. Paired full firmware reads,
owned guards, idle/loan return and gateway HTTP 200 passed. Leave normal session
`20261019T092824Z` running; `~/rtems-console` is the user-facing prompt.
