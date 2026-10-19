## Accele160 faster polling / reply DMA — 2026-10-19 (one-hour qualification passed)

Current owner is now `/home/mit/i960-packet-dma-20261019/bundle`, boot
`724cee4d-a331-4cbb-840b-7b5bb5541ccc`. The preceding combined owner closed its
module and shut down cleanly before reset. The new normal profile-5 kernel is
`a3d6722a907ed59dab707d5715d1cb4b476b7dd192662e319e2656b001188503`.
It passed the ordinary 64-frame baseline and loaded the combined module. Do not
start a second owner or modify the frozen live bundle.

The owner now pumps services every 5 ms; full ownership/fault audits remain at
100 ms and heartbeat at 500 ms. Opt-in reply DMA borrows the existing DMA0 and
pinned host slot only after game retirement. It copies the 4 KiB runtime reply
page followed by an exact epoch/sequence marker, drains with a finite observer,
and retains all resources on uncertainty. Upload/request traffic stays PIO.
Native finite-chain, timeout/error, stale-marker, full-page comparison and
quarantine tests pass. See `rtems/accele160/runtime/PACKET-DMA.md`.

The raw hardware trial passed 32 full-page DMA/PIO comparisons, 320 alternating
UDP reply transactions (64/256/1024/1400-byte payloads), and one final full-page
query comparison. Another 200 full-page comparisons passed under mixed load.
Measured DMA speed varied by size; no uniform acceleration is proved. Routed
HTTP medians were about 150 ms for both PIO and DMA. PIO remains the intended
final default. The 3,603-second DMA endurance run passed 78,344 workload events
with zero errors/drops and intact guards. Maximum HTTP/console times were
621/107 ms. Sixty status queries after the run had a 38.5 ms median (old
100 ms polling: 205.6 ms); this is host round-trip latency, not an IRQ bound.
Relay pause/death, broker restart, abandoned client, partial-upload refusal and
module reload passed without changing boot or PCI owner. DMA/PIO comparisons
before and after two epoch transitions bring the full-page total to 235.
The prompt, PIO relay, IPv6 HTTP and browser gateway are active. Evidence and
replay commands: `artifacts/current/accele160-packet-dma-20261019/README.md`.
Eight-hour endurance and fresh packet-DMA hardware fault injection remain open.

Root operational tools are in `/home/mit/i960-packet-dma-20261019`.
`~/rtems-console` points there, via `/run/i960-combined.sock`; `quit` disconnects
only. The previous wrapper is `~/rtems-console.before-packet-dma-20261019`.
Public card HTTP remains `http://[2a02:8106:40:9000::960]/` and was fetched from
the Mac during the DMA run. Internet ingress remains unverified.

IPv4 SSH began retransmitting during connection setup after the raw benchmark;
ICMP and the browser status endpoint still responded. IPv6 SSH works:
`ssh -6 -o HostKeyAlias=192.168.2.75 mit@2a02:8106:40:9000:f662:19ee:dbad:1f1e`.
This uses the existing verified host key. The cause of the IPv4 path issue is
not established; do not attribute it to the card or change unrelated network
settings without evidence. The final IPv4 SSH check succeeded without a network
configuration change. The PC did return from reset without another manual
power cycle being reported.

## Combined networking, console and applications — 2026-10-19

Current operational tools/module: `/home/mit/i960-combined-20261019`.
The hardware owner and kernel remain the earlier reclamation session
`/home/mit/i960-reclaim-ipv6-20261019`, session `20261019T175819Z`;
boot `8cdab7ff-48a3-481f-bb54-0924025016c0`. Do not start a second PCI owner.
The new root-only broker `/run/i960-combined.sock` serializes network/application
RPCs with bounded queues and a 3:1 policy when both classes are queued. Set
`I960_RUNTIME_SOCKET=/run/i960-combined.sock` for the combined client and relay.
The independent diagnostic socket still works without the broker.

The combined lwIP module adds two bounded bundled applications (counter and
uppercase echo). `~/rtems-console` now supports `net`, `app list`,
`app start/stop counter/echo`, and `app echo TEXT`, plus existing diagnostics.
Its previous wrapper is backed up as `~/rtems-console.before-combined-20261019`.
These are callbacks inside Init, not arbitrary concurrent segmented applications
or unrestricted RTEMS task cancellation. Generation tokens apply within one
loaded module instance and must be discarded across unload/reload.

The final mixed run passed **601.417 seconds / 4,837 events / zero errors**.
Maximum observed HTTP/console/echo round trips were 2379.350/236.244/1657.962 ms.
The concurrent full-zone loan wrote/read **6,291,424 bytes in 192 steps**, retained
two cancelled references safely and refused close until release; maximum RPC
was 829.627 ms under load. These are observed host latencies, not IRQ bounds.
The first direct-client run had one HTTP timeout and is retained as failed
evidence; the first broker prototype was stopped early to fix ingress batching.
The precise cause of the initial HTTP timeout is not established.

Use the **root-level** `i960-combined-20261019/public_ipv6.py` for routing
removal/reapply: it handles a missing TUN after relay death. Earlier frozen
bundle helpers predate that correction. Card HTTP remains
`http://[2a02:8106:40:9000::960]/`; LAN access is tested, Internet ingress is not.

DMA archives for profiles 6–13 and the current kernel's prior 64-frame baseline
were replayed, and native DMA ownership tests passed. No fresh DMA fault/NMI was
injected in this combined run. **Packet transport is still PIO; packet DMA
acceleration is unqualified.** The current owner sleeps 100 ms in its idle loop;
qualify fast service polling independently of slower ownership audits before
comparing packet DMA and PIO under identical scheduling. This needs a fresh
owner baseline, not modification of the live process. One-hour/eight-hour
endurance and bounded underlying owner journals remain open.

Recovery passed on the same boot and PCI-owner PID: abandoned client, occupied
upload refusal, relay pause/resume and death, broker death/restart, and interrupted
upload rejection/abort followed by a pristine module reload. Both apps, the
prompt and routed HTTP were restored. This tests host service/module recovery,
not new PCI-owner death, hardware reset or DMA fault injections. The first
recovery attempt stopped before injection on unsupported systemctl spelling;
`--kill-who=main` corrected it. P8 is bounded integration; P9 packet acceleration
is open; P10 has these recovery cases; P11 has the ten-minute stage only.

Design and reproduction: `rtems/accele160/runtime/COMBINED-SERVICE.md`.
Evidence: `artifacts/current/accele160-combined-20261019/README.md`.

## Accele160 idle-zone reclamation and global IPv6 — 2026-10-19

Live bundle: `/home/mit/i960-reclaim-ipv6-20261019/bundle`, session
`20261019T175819Z`, boot `8cdab7ff-48a3-481f-bb54-0924025016c0`.
Kernel SHA256 `26b916dfd1c85a986d24b4bac17c7972b8b5108fed5bb56e9d0028afbed6bc80`.
The original prompt and card-side network service remain the intended final state.

The idle Doom zone now has a guarded, generation-owned loan API. The hardware
qualification wrote and verified **6,291,424 bytes** inside the existing 6 MiB
parent allocation, over 192 bounded calls. It cancelled while two pins remained,
refused new access, premature release and module close, then drained both pins
and returned the loan. Maximum observed RPC was **206.356 ms**, not an interrupt
latency bound. Networking timer calls advanced from 178 to 1666 through the test.
The ordinary baseline passed 64 frames / 5,045 WAD reads; 949 external prompt
exchanges passed. Hello plus two network loads and the existing heap proofs passed.

This makes the retired zone available through a kernel loan API and test wire,
not yet through module imports or RTEMS malloc/workspace. The qualification
returns the loan at the end. No new stock memory was taken, and 10–12 MiB total
ownership is still gated on SXP/DMA exclusion and firmware allocation analysis.
See `rtems/accele160/runtime/RECLAMATION-CANCELLATION.md`.

**Unrestricted task cancellation remains unimplemented.** The module still runs
inside Init and the ISR has exactly four owned contexts. The new cancellation
code revokes allocation access and retains outstanding references; it does not
kill arbitrary tasks, release held RTEMS locks or invent DMA completion. The
contract records the separate application-task/context, supervisor channel,
dependency tracking and fault-test gates required next.

Card global address: **`2a02:8106:40:9000::960`**, HTTP port 80. The global-address
module preserves `10.196.0.2` and `fd96:196:960::2`. Host routing/proxy NDP is
implemented by the corrected **root-level** script
`/home/mit/i960-reclaim-ipv6-20261019/public_ipv6.py`; use it for removal/reapply,
not the earlier helper frozen inside the bundle. The first helper enabled only
interface forwarding; LAN SYNs reached the host but were not forwarded. Linux's
IPv6 forwarding path also requires the global switch. The corrected helper
saves/restores global and interface settings, preserves unrelated interfaces,
and restricts newly enabled IPv6 forwarding to the card. It also enables global
proxy NDP for unicast neighbor refresh. IPv4 forwarding policy is untouched.

Twenty HTTP requests from the Mac passed against the global address; public
TCP/9600 was blocked. Host IPv4/IPv6 ping and HTTP passed. No host HTTP proxy is
involved. Internet reachability is **unverified**: the external fetch tool could
not test an IPv6-literal URL. The upstream router may need an inbound IPv6 HTTP
rule for the card address. Do not call LAN success an Internet test. Routing is
explicit, temporary and prefix-specific; remove it before stopping the TUN relay.

Evidence: `artifacts/current/accele160-reclaim-ipv6-20261019/`. Earlier immutable
runtime bundles and the stock/coexistence option remain preserved.

# DAC960PG → AcceleRAID 160 RTEMS feature port

## Latest checkpoint — P3o and initial P5/P6/P7 integration (2026-10-19)

[Profile 19](../../rtems/accele160/ownership/PROFILE19.md) qualified paused DMA-bank
inspection and unconditional, verified CONF1 restoration before HCCR release.
Both passes reported command `1/8/0`, data `8/8/0` (config/status/FIFO).
64 frames, 5,045 WAD reads and 709 external console exchanges passed; final STOP
retained resources. Terminal count is observed, but SCSI/DMA exclusion and new
stock-RAM ownership are still unproved.

The [resident application extension](../../rtems/accele160/runtime/README.md)
now runs on Accele160 with the existing 192 KiB workspace and owned IRQ stacks.
It reserves 512 KiB inside the already qualified upper arena: 384 KiB for a
segmented module, 128 KiB for a separate general heap. The card loaded hello,
unloaded it to zero reservation, loaded networking, unloaded it, and loaded
networking again without resetting between applications. All three on-card heap
proofs passed. Network file data is 84,944 bytes, total code/data/BSS 198,688 bytes.

Card-side lwIP now passes IPv4/IPv6 UDP and TCP HTTP through the owner channel,
plus real TUN ICMP, UDP/TCP echo and HTTP. Both ping tests received 5/5 packets.
A deliberate abandoned query and relay reconnect passed; 109 module timer
calls occurred during two seconds without host packets. Baseline RTEMS passed
64 frames, 5,045 WAD reads, 721 external console exchanges; an additional
245 console exchanges during networking had zero errors.
This is a bounded single-owner module ABI, not completion of every P4–P7 gate.

Current service: `/home/mit/i960-runtime-port-v4-20261019/bundle`,
session `20261019T140746Z`, boot `2433f02b-0e55-4467-a072-0b2c70c8fb48`.
Kernel SHA256 `d3865059b0c54b1f77dbbe434cd710be83431254b9cfbafd5bd857e21db54e40`.
`~/rtems-console` works; the module is running with no poison/busy indication,
Doom idle and zone loan zero. `i960-doom`, `i960-doom-stream` (8088), and
`i960-rtems-ip` are active. Card HTTP: `10.196.0.2:80` and
`[fd96:196:960::2]:80` on the private host TUN link. Public routing is unchanged.
The original normal profile remains at `/home/mit/i960-owned-runtime-20261018/bundle`.

Next work, in order:

1. Add bounded allocator/reallocation and shared-reference APIs for applications;
   measure allocation and interrupt latency. Convert the retained 6 MiB Doom
   zone into an explicit loan before offering that space to general services.
   Expand workspace/stacks only with a placement manifest and bootstrap guards.
2. Extend the single absolute-address module ABI: declared imports/relocations,
   more application lifetimes, and on-card interrupted/bad-checksum upload tests.
   Qualify fault/NMI containment while module code is executing. Arbitrary
   non-cooperative module cancellation is not yet established.
3. Add outbound fetch/DNS controls, host forwarding and separately approved
   public IPv6 routing; qualify reconnect/loss/backpressure and long endurance.
   Bound/rotate the packet transport journal before continuous heavy use.
4. Continue ISP10160 SXP/DMA stop/drain and firmware dependency work before
   reclaiming stock allocations toward 10–12 MiB. This port claims no new RAM.

Evidence: [DMA batch](../../artifacts/current/accele160-qlogic-dma-bank-20261019/README.md)
and [application/network batch](../../artifacts/current/accele160-runtime-port-20261019/README.md).
Both preserve failed attempts as well as passing captures. Earlier checkpoints
below are historical; their “next” and live-session statements are superseded.

## Accele160 P3n — one-shot QLogic RISC pause/release qualified

Profile 18 passed 64 frames, 5045 WAD reads and 713 external console
exchanges after one gated pause/release transaction. HCCR changed
**`0000 → 0020 → 0000`**, with 1 read for pause acknowledgement and
1 for release. CONF1 stayed `0074`, ICR `0006`, ISR zero,
semaphore 2 and chip indices 37/22. Ready/frame32/idle/STOP preserve the same
transaction payload; no second attempt occurs. Final STOP retains resources.

This establishes RISC control on the observed quiet workload, **not SXP/DMA
shutdown or RAM ownership**. Native tests cover both 10,000-poll timeout paths,
initial-state refusals, changed-state failures and retry blocking. A stalled bus
transaction still has no guaranteed wall-clock bound. Uncertainty retains
buffers, descriptors and the pending firmware callback for reset.

[Profile and protocol](../../rtems/accele160/ownership/PROFILE18.md),
[stop/isolation contract](../../rtems/accele160/ownership/STOP-CONTRACT.md),
[complete evidence](../../artifacts/current/accele160-qlogic-pause-20261019/README.md).
Next: qualify a minimal paused, banked command/data-DMA read-only snapshot and
unconditional CONF1 restoration. HCCR aliases a DMA register in the DMA bank;
restore the normal bank before release. Establish SXP/DMA active/FIFO/status
semantics before a drain or disable experiment. Keep all stock ranges reserved.

Normal profile 5 is restored at `/home/mit/i960-owned-runtime-20261018/bundle`,
session `20261019T131711Z`, boot `4cdd0e35-4d6a-4430-bbe9-be167070673e`. Paired full
flash reads, 64 frames, 5045 WAD reads and 709 external exchanges
passed. `~/rtems-console` is working at idle, zone loan zero; gateway 8088 returns
HTTP 200. No physical intervention was needed. Earlier session claims are historical.


## Accele160 P3m — actual chip indices resolve the stale cache

Profile 17 passed 64 frames, 5045 WAD reads and 709 external console
exchanges without errors. Ready/frame32/idle/STOP each contain two identical
16-bit chip samples: ISR 0, semaphore 2, request consumer **37**, response
producer **22**. Software producer/cached consumer remain **37/0**, and response
producer/consumer **22/22**. The chip has caught up to the producer at these
observations; the cached request consumer is stale. The firmware refreshes it
on the queue-space path. This does not prove SCSI/DMA stop or hardware isolation.

The semaphore STATUS bit is set; LOCK is clear. The decoder deliberately reports
`status_zero=false`. The probe writes no chip register and does not acknowledge
interrupts or issue mailbox commands. PCI identity/BAR/memory-decode and checked
RAM context gate twelve fixed halfword reads. It retains all firmware memory.

[Protocol and access evidence](../../rtems/accele160/ownership/PROFILE17.md),
[complete artifacts and replays](../../artifacts/current/accele160-qlogic-chip-20261019/README.md).
Next: establish a board-specific stop/isolation contract covering ISP RISC,
SXP/DMA, pending mailbox work and stock callbacks before any disable/reset test
or memory reclamation. Equal ring indices alone are insufficient. Preserve the
host ATU/MU path and keep DMA1/firmware queues reserved.

Normal profile 5 is restored at `/home/mit/i960-owned-runtime-20261018/bundle`,
session `20261019T105649Z`, boot `417ae821-f1d1-4305-9e91-614598e4a5cb`. Paired full
firmware reads, 64 frames, 5045 WAD reads and 713 external exchanges
passed. `~/rtems-console` is working at verified idle, zone loan zero; gateway
8088 returns HTTP 200. No physical intervention was needed. Earlier running
session claims below are historical and superseded here.


## Accele160 P3l — checked QLogic software queue state

Profile 16 passed 64 frames, 5045 WAD reads and 709 external console
exchanges, with matching ready/frame32/idle/STOP snapshots and retained resources.
It adds at most 18 fixed RAM reads, verifies the exact context pointer, and does
not follow pointers or perform new PCI/chip accesses.

Physical context corrects the prior static ring-size inference: **256 request
entries (16 KiB), 128 response entries (8 KiB)**. Pending head/tail and active
exchanges are zero; request producer/cached consumer are **37/0**, response
producer/consumer **22/22**. The mailbox resource word is 578, not an active-work
count. All four samples agree. This is not hardware-drain or reclaim evidence.
The original test bundle preserves the smaller analysis hypothesis; corrected
offline decoding and both source hashes make the correction explicit.

[Protocol, correction and observations](../../rtems/accele160/ownership/PROFILE16.md)
and [artifacts/replays](../../artifacts/current/accele160-qlogic-queue-20261019/README.md).
Next: review chip register access semantics and implement a bounded read-only
device-state snapshot to compare real queue indices with cached software state.
Then complete the stop/isolation contract; retain all firmware ranges meanwhile.

Normal profile 5 is restored at `/home/mit/i960-owned-runtime-20261018/bundle`,
session `20261019T101634Z`, boot `9086e6f3-5eb2-424e-a210-d4dee54608dd`. Paired
full firmware reads, 64 frames, 5045 WAD reads and 709 external exchanges
passed. `~/rtems-console` works at verified idle with no zone loan; gateway 8088
returns HTTP 200. No physical recovery was needed. Earlier checkpoint sizes and
running-session claims below are historical and superseded here.


## Accele160 P3k — direct QLogic identity and queue dependency trace

Opt-in profile 15 passed 64 frames, 5045 WAD reads and 697 external console
exchanges without errors. Ready/frame32/idle/STOP configuration snapshots agree:
physical `1077:1016`, revision **6**, memory BAR `fff00000`, command `0006`
(memory decode and bus mastering enabled). SOCCAR returned exactly to `1000c`
after every sample. The earlier firmware revision word was zero; it is not an
authoritative hardware revision. Only the selector register is written; no
configuration data writes, chip MMIO, engine reset or extra RAM claim occurred.

The pinned queue trace identifies channel context `c0600d00`, request storage
`c0600df0` (8 KiB), response storage `c0604df0` (4 KiB), software pending lists,
mailbox/interrupt callbacks and queue-index publication. These remain reserved.
The next step is a checked fixed RAM snapshot of context fields, indices,
pending head/tail and active counters, followed by completing the stop/isolation
contract. Do not traverse unknown pointers or infer isolation from quiet fields.

[Protocol and findings](../../rtems/accele160/ownership/PROFILE15.md) and
[artifacts and replays](../../artifacts/current/accele160-qlogic-config-20261019/README.md).

After clean STOP with callback/pins retained, reset recovery passed paired full
firmware reads. Normal profile 5 is restored at
`/home/mit/i960-owned-runtime-20261018/bundle`, session `20261019T092824Z`,
boot `96907303-fe0a-4c0f-a7bd-558d044f44c6`. It passed 64 frames, 5045 WAD reads and
681 external exchanges with no errors. The user-facing prompt is live at
verified idle with no zone loan; gateway 8088 returns HTTP 200. No physical
intervention was needed. Prior checkpoints and their running-session claims
below are historical.


## Accele160 P3j — core inventory and QLogic firmware dependencies qualified

Opt-in profile 14 passed two fresh-boot 64-frame runs, each with 5045 WAD reads
and 709 external console exchanges. The final repeat's live and STOP captures
pass owned vectors/ISP/guards, report identity/stability and retained callback/pins.
The inventory uses 48 fixed reads within the existing report page; no CSR/ASR,
private configuration transaction or chip-control write. A source guard now
keeps profile 14 out of diagnostic exception-entry CSR reads; its compiled entry
object matches normal profile 5 exactly, including explicit profile compilation.

DMA1 retains DAR `c0611320`, LADR `c0790000`, DCR `3f` despite zero
CCR/NDAR/BCR. IACR is 0 and SACR 1554: grants are not excluded. Sampled AAU
control/descriptor/count and software queue words are zero, not proof of drain.
Firmware channel-0 metadata identifies `1077:1016` (QLogic ISP10160), mapping
`8bf00000`, PCI BAR `fff00000`, selector `10`; SCRIPT fields are zero. The
pinned firmware dispatch selects the QLogic callback setup, not the alternate
Symbios path. Stock DMA1 and AAU submission/callback dependencies are traced.

[Protocol, dependencies and next step](../../rtems/accele160/ownership/PROFILE14.md)
and [raw artifacts/replays](../../artifacts/current/accele160-engine-inventory-20261019/README.md).
Next: corroborate this one secondary device by bounded configuration reads;
audit QLogic request/response queues and mailbox/interrupt callbacks, then design
identity-gated stop/isolation. No extra RAM or permanent engine ownership granted.

Normal profile 5 is restored at `/home/mit/i960-owned-runtime-20261018/bundle`,
session `20261019T075249Z`, boot `49c4d3c5-df8d-438f-810a-82a343636e52`. Fresh paired firmware reads,
64 frames, 5045 WAD reads and 717 external console exchanges passed. Leave
this prompt owner live at verified idle; gateway 8088 is active. Earlier session
and next-step statements below are historical.


## Accele160 P3i — stock engine isolation is not established

The new fixed-device, read-only PCI/console audit found BCR=0x202 (secondary
reset deasserted), SACR=0x1554 (all six external arbitration slots enabled),
and secondary/subordinate bus 0x38. These are permissions for bus activity,
not proof of populated devices or current transfers. The AAU and DMA1 stock
dependencies remain unowned. Prior zero CCR/NDAR/BCR snapshots omit descriptor
and accelerator state and cannot justify reclaiming firmware cache RAM.

[Ownership matrix and next implementation](../../rtems/accele160/ownership/README.md);
[evidence](../../artifacts/current/accele160-engine-audit-20261019/README.md).
Collector/decoder run passed on the card, with identity/boot/health rejection
and no-promotion tests. No register writes, new firmware callback, kernel change
or reboot. Normal profile 5 remains live in session `20261019T041732Z`, boot
`bbefd6d3-016a-4c9e-8388-36a164e78fd4`, with prompt idle, no zone loan and
HTTP 200 from gateway 8088.

Next: an opt-in non-status core-engine inventory and offline SCSI metadata audit,
then board-specific drain/isolation. Preserve primary ATU/MU, DMA0 and BIU.
Do not copy the DAC960PG secondary-reset sequence or promote quiet samples into
ownership. P4 task cancellation and new RAM reclamation remain gated.


## Historical P3h checkpoint — controlled DMA exception matrix qualified

Profiles 6/7 drain active DMA through fault/NMI; 8/9 retain suspended transfers
through bounded observers; 10/11 permit one gated resume; 12/13 refuse invalid
saved evidence and a corrected retry through the one-shot latch. Profile 13
now has real NMI evidence, independent MU acknowledgement reads, unchanged
suspended state, post-owner-exit retention and verified reset recovery.
[Evidence and limits](../../artifacts/current/accele160-nmi-dma-refusal-20261019/README.md).

Normal profile 5 is restored in session `20261019T041732Z`, boot
`bbefd6d3-016a-4c9e-8388-36a164e78fd4`, with 64 frames, 5045 WAD reads and 709 external
console exchanges passing. Leave the prompt owner running at verified idle.

P3 is not complete: permanent stock SCSI/cache-engine exclusion, unknown fault
sources and stronger latency/endurance bounds remain separate. Next consolidate
the matrix and audit hardware ownership before P4 task/resource cancellation.
Preserve stock-firmware coexistence and the DAC960PG implementation as future
options. All checkpoint/live-session statements below are historical.

## Historical P3b checkpoint — normal owned runtime passed

[Profile 5](../../rtems/accele160/fault/OWNED-RUNTIME.md) passed two-game normal
operation, rearm, console traffic, owned table/NMI/ISP/guard checks and final
QUIE. All 128 frames and 10,090 WAD reads replay. Reset recovery is closed by
fresh boot `b0732f10-debf-4bb3-8adc-e7e0bdc0fa91` and both guarded firmware
reads. The same no-injection profile restores the prompt. Active-DMA exception
containment, SCSI/cache exclusion, stronger latency bounds and long endurance
remain separate. See the new evidence batch; earlier checkpoints are historical.

## Historical P3b checkpoint — recovery complete, prompt restored

Both hardware exception tests and both post-reset firmware pairs passed.
Normal mode 0 is restored on boot `aea81f51-24ce-493b-a7d2-114195611d5b`,
with one 64-frame game, verified idle and 577 successful console exchanges.
Leave this owner live for the user's prompt. Next is normal runtime with owned
vectors/ISP; mode 0 remains software-only. Active-DMA fault containment and
engine exclusion are still separate open gates. Earlier entries are historical.

## Historical P3b checkpoint — both hardware exception tests passed

Actual `faulte` and actual MU-doorbell NMI passed with stable raw terminal
records, owned table/NMI/ISP, guards and retained resources. Mode 3 reset
recovery is closed; mode 4 recovery and normal prompt restoration follow its
final reset. The accepted mode-0 prompt remains software-only. Normal runtime
with owned ISP, active-DMA containment and engine exclusion remain open.
See [current evidence](../../artifacts/current/accele160-exceptions-20261018/README.md).
Earlier checkpoints below are historical.

## Historical P3b checkpoint — actual fault test passed

Mode 3 passed on Accele160: exact hardware fault/IP, owned vectors/table/ISP,
guards, stable record and STOP resource retention. Paired guarded firmware reads
close the prior normal-runtime reset. Mode 3 recovery and real NMI mode 4 are
still open; mode 4 is built and archived for the next fresh boot. Prompt offline.
See [current evidence](../../artifacts/current/accele160-exceptions-20261018/README.md).
The earlier checkpoints below are retained as history.

## Historical P3b checkpoint — awaiting physical recovery

The owned fault/NMI candidate is implemented and passes native tests; on-card
qualification has not begun. The previous normal prompt was shut down cleanly,
its raw STOP evidence saved, and the subsequent reset left SSH unavailable.
Rebuild current source after recovery: the archived first mode-3 build predates
additional checks and the real-NMI host path. Modes 3 and 4 install ownership;
mode 0 remains software-only and must not be described as owned-fault coverage.
See [owned exception design and exact resume sequence](../../rtems/accele160/fault/OWNED-EXCEPTIONS.md)
and [evidence](../../artifacts/current/accele160-exceptions-20261018/README.md).
Earlier live-session status below is historical.

Planning baseline: 2026-10-18. The original review used existing evidence;
the checkpoints below record subsequent implementation and physical tests.

## P1/P2 implementation checkpoint

[The service batch](../../artifacts/current/accele160-service-20261018/README.md)
now contains an opt-in kernel and host prompt. Two 64-frame games, rearm,
card protocol tests and global STOP passed; the accepted kernel and complete
captures are archived. The corrected host then passed a fresh-boot physical
follow-up through startup, 64 frames and audited idle, with clean oversized-line
EOF and bounded abandoned/slow clients. The first run's post-reset firmware pair
matches. P1/P2 diagnostic service acceptance is complete. Its follow-up owner
later shut down and passed reset checks during P3; the current prompt is the
mode-0 owner described below. The default installed Doom/CHIP-8 bundle is not
promoted.

## P3a checkpoint — both terminal tests passed

[Software terminal diagnostics](../../rtems/accele160/fault/README.md) passed
both physical tests: explicit fatal and deliberately corrupted private guard,
with stable records, stale-trigger refusal and retained resources after STOP.
Both terminal tests' post-reset firmware pairs are now closed. The mode-0
normal profile ran two 64-frame games, audited idle/rearm and console traffic;
the prompt is restored and its owner left running in verified idle. The live
mode-0 session's global STOP/reset qualification is still separate.
[Evidence](../../artifacts/current/accele160-fault-20261018/README.md).
Hardware fault/NMI ownership and engine exclusion remain further P3 gates.

## Goal and current evidence

Turn the AcceleRAID's application-specific, reusable RTEMS runtime into a
multi-service platform with a host-accessible prompt, general application
loading, owned shared memory and card-side IPv4/IPv6. Preserve the accepted
Doom path and the DAC960PG implementation as independent build profiles.
Exclusive, reboot-only ownership is the initial target. Stock/RTEMS coexistence
remains a separate future track, not a prerequisite.

The old introductory new-board notes are historical. The new card already has
hardware ticks, preempted tasks, a qualified upper-bank arena, DMA frames,
persistent Doom and engine-only stop/reload. Do not repeat initial bring-up or
claim those features are absent. Conversely, a Doom-specific success does not
qualify an arbitrary task, allocator or network service.

| Capability | DAC960PG reference | AcceleRAID baseline / remaining port |
| --- | --- | --- |
| RTEMS core and clock | RTEMS 4.6.6, owned interrupt continuations | Already present; generalize task/ISR ownership beyond fixed Doom owners |
| Persistent application lifecycle | Resident workers, upload and cancellation | Persistent Doom plus audited idle/rearm exist; general application lifecycle is missing |
| RAM | Validated exclusive 12 MiB layout; 8 MiB application arena | Verified 8 MiB upper bank, with guarded application interval `c0810000..c0ff0000`; do not copy PG's 12 MiB grant |
| Allocation | Guarded general heap, shared references/pins and cancellation | Engine/zone/frame allocation exists; general shared-service heap and cancellation need integration |
| Loader | Segmented image core, resident upload and versioned runtime ABI | Operation-13 bootstrap and relocated Doom admission exist; general resident upload/service ABI remains |
| DMA | Frame and WAD transports with ownership gates | Channel-0 frame DMA, held-host and finite drain gates exist; generic packet/input DMA remains |
| Network | lwIP 2.1.3 raw API, host-backed IPv4/IPv6, HTTP | Browser HTTP currently runs on Linux; card-side IP stack/packet relay is a port |
| Fault containment | Exclusive NMI/fault records and resource retention | Local fatal/guard paths exist; comprehensive board-specific fault ownership needs audit and qualification |
| Command prompt | No general interactive shell established | New shared feature for both boards, not a finished PG component to copy |

Evidence: [persistent Doom](../../artifacts/current/doom-persistent-20261018/README.md),
[rearm](../../artifacts/current/doom-rearm-20261018/README.md),
[current launcher](../../game/doom/play/accele160/README.md),
[DMA contract](../../rtems/accele160/doom_dma/README.md),
[arena](../../rtems/accele160/ARENA.md),
[PG shared heap](../../rtems/residentnet/SHARED-HEAP.md),
[PG upload](../../rtems/residentnet/UPLOAD.md), and
[PG fault ownership](../../rtems/residentnet/FAULT-OWNERSHIP.md).
The closed 1,058-frame persistent gate includes its post-reset flash pair;
newer bundles must retain their own explicit pending/closed status.

## Architecture and boundaries

Reuse algorithms and protocols, not register constants, old-board binaries,
linker maps or Linux ioctl numbers. Keep board operations explicit: clock,
interrupt entry/exit, cache maintenance, admitted ranges, sideband exchange,
DMA submit/completion and terminal retention. Do not refactor every historical
experiment; extract only code exercised by the new service profile.

Keep one Linux hardware owner. SSH terminal clients, network relay and browser
clients connect to that supervisor; they do not open competing card sessions.
Control/STOP and heartbeat must remain serviceable during upload, network load,
frame ACK waits and full audits. Snapshot reads remain serialized consistently.

The current kernel map starts at `c0710000`, bounds text/data/BSS below
`c0724000`, reserves four IRQ stacks through `c072c000`, and places the entry
stack next. Staging starts at `c078f000`. These are constraints to re-budget,
not permission to place a larger kernel into apparent padding. Keep the active
bootstrap, ISR/entry stacks, descriptors and control pages out of reclaimed RAM.
The accepted private cache template covers the upper 8 MiB; all CPU/host/DMA
producer-consumer transitions must retain the appropriate invalidation and
visibility rules. Pins establish lifetime, not cache coherence or mutual exclusion.

## Ordered implementation gates

### P1 — Freeze the service baseline and ownership map

Create an opt-in AcceleRAID service build from the accepted reusable runtime.
Record source revision, firmware/engine/kernel/module hashes, exact board identity,
link map, all task/IRQ owners, callbacks, DMA channels, cache mappings and RAM
ranges. Confirm the current live owner before any physical work. The old card
may be physically absent; preserve strict target selection rather than requiring
its presence or assuming both cards can run together.

Acceptance: reproduce the selected baseline, run existing native validators,
and repeat idle → application → idle → application → global STOP with its full
paired audits. Keep installed Doom unchanged until this candidate passes.

### P2 — General control channel and minimal command prompt

Add a versioned, length-bounded request/reply channel using the independently
accessible sideband, with epoch, sequence, operation, status and output chunks.
Add a bounded RTEMS command worker and a host terminal client, multiplexed by
the existing supervisor. Start with `help`, `version`, `uptime`, `tasks`, `mem`,
`apps` and `stats`. Read-only snapshots come first; no arbitrary memory writes,
jump command or forced task deletion. This is a small diagnostic interpreter,
not Bash or a claim that RTEMS's standard shell/POSIX I/O is already ported.

Acceptance: actual card-produced output over SSH while idle and while Doom
runs; stale/duplicate/oversized requests, slow readers, disconnect/reconnect,
output overflow and simultaneous STOP. Bound per-command work and queue space;
measure response latency and maximum IRQ gap under full audits. A lost terminal
client must not kill the supervisor or change ownership.

### P3 — Board fault and hardware ownership coverage

Audit every enabled timer/interrupt/fault/NMI path against the 80303 board and
current stock handler. Port the PG terminal-record/retention policy only after
mapping the new board's vectors, registers and live stacks. Account for all
three DMA channels and SCSI/cache/other bus masters; an idle snapshot alone is
not proof of permanent engine exclusion. Add deterministic terminal diagnostics
outside reclaimable memory, readable without calling failed application code.

Acceptance: controlled faults and guard corruption in isolated runs, full
surviving record validation, no return into overwritten stock state, no unsafe
unpin, then verified reset recovery. Interrupt-enabled deadlines do not prove
recovery from permanently masked interrupts; independent watchdog recovery
remains a separate hardware research gate.

### P4 — General task ownership and cancellation

Replace fixed application assumptions with bounded task records containing
identity/generation, stack/IRQ lifetime and resources. Reuse PG cancellation and
resource-dependency policy, including the worker-arrival barrier from
`rtems/exclusive/worker_stop.h`. Separate application STOP, service shutdown,
terminal containment and engine rearm. Preserve old IRQ owners until their
saved continuations drain; never suspend a resource holder and free its objects.

Acceptance: two synthetic apps plus the controller; STOP during nested critical
sections, shared-resource use and IRQ preemption; stale STOP, deadline, final
close and failed-control paths. Prove either complete drain or explicit retained
ownership. Start with bounded task counts; unrestricted arbitrary task creation
is not implied by this gate.

### P5 — General heap, workspace and stack budget

Port the board-independent arena/heap policy and shared handle/ref/pin contract
from `loader/segmented` and `rtems/residentnet`. Assign separate budgets for
kernel workspace, task/IRQ stacks, packet queues, console and applications.
Derive addresses from the new linker manifest; keep Doom's contiguous zone
requirement and the upper-bank exclusions. Expand kernel placement only after
protecting the bootstrap and proving all newly used intervals. Do not promise
10–12 MiB of new-board ownership based on PG evidence.

Acceptance: allocation/reallocation/alignment/exhaustion, fragmentation, stale
handles, shared cancellation while pinned, deliberate metadata/redzone failure,
repeated app reload and final zero-live-object accounting. Measure allocation
latency and maximum IRQ masking. If Doom + services do not fit, reduce explicit
budgets or qualify more RAM as a separate experiment; never silently overlap.

### P6 — General resident segmented upload and application ABI

Reuse the PG segmented loader's validation and the new card's exact admission,
relocation and cache handling. Define board/ABI versions, declared segments,
entry/BSS/stack bounds, imports and capabilities. Add bounded begin/chunk/verify/
commit/query/abort operations through the single supervisor. Keep the currently
running service and loader outside upload destinations. Reload from pristine
image bytes with zero BSS after retired references/IRQ contexts are gone.

Acceptance: load two different small apps without flash or reset, get text
output, cancel one and reload; reject overlaps, wrong-board images, unsupported
imports/relocations, bad checksums and stale epochs. Test interrupted uploads,
STOP at each phase and no jump into a partially admitted image. Retain resources
on uncertain completion. Application code remains trusted in one address space.

### P7 — Card-side IPv4/IPv6 over bounded PIO

Port `rtems/net` and the resident packet queue behind a new-board transport.
Start with one task owning lwIP and its timers. Current settings are `NO_SYS=1`,
with sockets/netconn disabled: preserve the raw API instead of assuming BSD
sockets or calling lwIP concurrently from multiple tasks. Add a Linux TUN relay
inside/coordinated with the hardware owner, with bounded queues and explicit
packet ownership. Use static test addresses and routes first.

Acceptance: IPv4/IPv6 ping, UDP, TCP HTTP served by the card, outbound traffic
and DNS as supported by the existing stack; malformed/oversized packets, queue
pressure, packet loss and relay reconnect. Compare response bodies with card
counters to distinguish RTEMS HTTP from the host browser server. Full snapshots,
console and application STOP must remain responsive under traffic. Internet
routing and public IPv6 reachability are separate host/router configuration gates.

### P8 — Multiplex networking, console and applications

Integrate fair per-service budgets, bounded audit groups, packet draining and
upload/frame progress in the supervisor. Keep the stack's single-owner model;
other tasks exchange messages instead of directly entering lwIP. Expose queue
drops, high-water marks, deadlines, task progress and IRQ latency via the prompt.

Acceptance: Doom plus dual-stack HTTP/UDP plus console commands and attempted
upload/cancellation. Reject incompatible operations explicitly. Record baseline
and stressed frame latency, network latency, command latency and IRQ gaps.
Set numerical pass limits from P2/P7 measurements before the acceptance run;
do not extend deadlines merely to hide starvation.

### P9 — DMA packet/input acceleration, after PIO correctness

Adapt channel-0 ownership to packet or WAD input only when its direction,
descriptors and coherent host windows are separately validated. Arbitrate with
frame output; channels 1/2 are not free just because unused by this application.
Use epoch/generation completions, bounded descriptors, guard regions and explicit
source/destination reuse rules. Preserve a PIO comparison path.

Acceptance: byte-exact PIO/DMA comparison, stale completion, backpressure, STOP
while active, owner death and finite timeout. A genuinely stalled/erroring DMA
transaction retains pins until proven reset/drain. Measure actual throughput and
CPU/IRQ cost before enabling by default. Direct Mylex↔NIC DMA is separate research.

### P10 — Persistent service lifecycle and recovery qualification

Generalize accepted engine idle/rearm to the qualified app set. Keep a single
session epoch and distinguish client reconnect from adopting a dead hardware
owner. Test idle and active heartbeat loss, SIGTERM, SIGKILL, browser/terminal
loss, failed control during teardown and blocked DMA completion. Global STOP
remains terminal/reset-only unless a separate return-to-stock proof is accepted.

Acceptance: resources are demonstrably drained or retained, never accidentally
reused. Collect evidence before reset; verify paired post-reset stock flash and
fresh boot ownership. A missing SSH return requires physical recovery, not an
automatic claim that reset succeeded. Preserve the PG coexistence route separately.

### P11 — Endurance and release bundle

Run staged 10-minute, one-hour, then eight-hour mixed workloads only after prior
gates pass, with periodic full audits, repeated app stop/reload and bounded log
retention. Track allocation/reference/stack/queue trends and packet/frame losses.
Archive exact binaries, linker maps, source manifest, module/firmware identities,
raw captures, replay/tamper results and reset evidence under a fresh dated artifact.

Acceptance: no unexplained resource growth, guard change, lost ownership or
missed control bound; native replay and on-card checks both pass. Update current
findings, agent guidance and reproduction docs with exact limits before promoting
an installed bundle. Historical captures remain immutable.

### P12 — Optional OS facilities after core parity

Consider a richer shell, host-backed read-only files/VFS, standard descriptors,
wall-clock synchronization and socket/POSIX adapters based on application needs.
These are additional features, not existing PG parity requirements. First audit
which RTEMS 4.6.6 components are actually built and supported by the pinned i960
Newlib port. A modern RTEMS upgrade, writable block filesystem, audio, independent
watchdog, arbitrary process isolation and direct NIC driving are separate projects.

## Dependencies and recommended first batch

Critical path: **P1 → P2 → P3/P4 → P5 → P6/P7 → P8 → P10 → P11**.
P9 is optional acceleration after P7/P8; P12 follows a usable service baseline.
P3 and P4 can be prepared independently, but hardware work remains serialized.
Full P6 upload is not required to statically link the first P7 network prototype.

Start with P1 and P2: freeze the current reusable image, inventory its owners,
add read-only command/reply messages, and prove `help`, `uptime`, `tasks`, `mem`
and `stats` during real Doom play without degrading STOP or audits. This gives
the requested RTEMS prompt early and instrumentation for the remaining ports.
Do not start by reflashing, replacing the working kernel wholesale, or extending
RAM ownership. Subsequent batches should close one ownership/transport gate at
a time rather than treating all eleven implementation stages as one card run.

## P3c — active-DMA exception containment

Diagnostic profiles 6/7 now exercise real processor fault / host-doorbell NMI
with a finite 64 MiB repeated-source DMA chain. Both accepted entries captured
CSR=0x400 before the C terminal snapshot. Bounded on-card observation then
confirmed inactive/error-free DMA at the last descriptor; the command remained
`done=0 released=0`, and ordinary DMA-buffer module removal was refused.
Both stack guards, both host guards, peer-register and owner-table checks
passed; the unused target stayed untouched. Full post-drain source/chain
fingerprints and independent visible-page checks supplement the complete host
payload comparison. The failed first aperture read is preserved as evidence.

[Design and limits](../../rtems/accele160/fault/ACTIVE-DMA.md) and
[exact artifacts](../../artifacts/current/accele160-active-dma-exceptions-20261018/README.md).
Profile 5 remains the normal service. Hardware stalled-DMA/abort qualification,
reclaim without reboot, SCSI/cache exclusion and faulted-task resumption are
still open. Native timeout simulation does not close those hardware gates.

Both P3c reset gates are now closed by fresh paired firmware reads. The normal
profile-5 prompt is restored on boot `b92db15d-de4d-4a57-9997-f6236dafa06a`
after 64 frames and 541 error-free external console exchanges. It remains live
at verified idle with gateway 8088 restored; the test profiles are not defaults.

## P3d — deliberate DMA suspension and timeout

Profiles 8/9 now test the terminal path with DMA0 deliberately suspended via
CCR.CE=0 after hardware activity is established. Both actual `faulte` and
host-doorbell NMI exhaust all 10000000 CSR polls with unchanged nonzero
outstanding descriptor/count, CSR=0x400 and CCR=0. Disabled does not mean
completed. Neither marker appears; guards, source/chain checks and frozen
partial host payloads pass. STOP, refused buffer unload and clean owner-process
exit leave `done=0 released=0` and pins retained. A separate post-exit audit
confirms that result. Native tests cover forged completion/progress and damaged
payload/marker/guard rejection. [Design](../../rtems/accele160/fault/STALLED-DMA.md)
and [evidence](../../artifacts/current/accele160-stalled-dma-20261018/README.md).

Remaining: an unresponsive PCI target / indefinite retry, blocked MMIO reads,
resume/abort and reclamation without reboot, broader SCSI/cache exclusion.
The loop bound counts completed MMIO reads; the observed ~2.49 s trigger-to-report
latency is not a general wall-clock guarantee. Normal service stays profile 5.

Both P3d reset gates are closed by fresh paired firmware reads. Normal profile 5
is restored on boot `a320a74a-d22e-4bdc-83f9-ef2649e30e2f`, session `20261018T221116Z`,
after 64 frames and 529 error-free external console exchanges. The prompt
and gateway 8088 remain live at verified idle. The diagnostic profiles are not
defaults; recovery used reboot, not DMA resume or memory reclamation.

### P3e — controlled DMA resume after deliberate suspension (2026-10-19)

Profile 10 now preserves a real fault-path 10000000-poll timeout, revalidates
ownership and the exact suspended transfer, and enables DMA0 CE once. The card
completed the existing finite chain after 1843705 further polls; source and
chain fingerprints, final payload/marker, stack and host guards, peer registers,
allocator owner table and post-owner-exit retention all passed. It remains a
reset-only diagnostic. Normal profile 5 is the service baseline.

[Design](../../rtems/accele160/fault/DMA-RESUME.md) and
[evidence](../../artifacts/current/accele160-dma-resume-20261019/README.md).
Native tests cover rejected gates, no retry, and a second bounded timeout;
only successful controlled resume after real `faulte` was tested on hardware.

The next bounded extension is the same controlled resume through the actual
NMI entry, preserving its source acknowledgement and original timeout record.
After that, qualify hardware gate rejection without changing CE and retain the
reset-only ownership policy. Generic PCI errors/retries, abort, arbitrary task
restart, SCSI/cache exclusion and memory reclamation remain separate gaps.

### P3f — controlled DMA resume through real NMI (2026-10-19)

Profile 11 extends P3e with the actual PCI doorbell NMI, owned vector 248 and
an additional source/acknowledgement gate before DMA0 CE. Core snapshots and
independent PCI MU reads agree that the injected doorbell was cleared and
masked. The original 10000000-poll suspended timeout remains intact beside the
new finite-chain completion evidence. Host payload, marker, guards, ownership,
peer-register and post-owner-exit retention checks pass on the card.

[Evidence](../../artifacts/current/accele160-nmi-dma-resume-20261019/README.md)
and [implementation](../../rtems/accele160/fault/DMA-RESUME.md). The normal
service remains the original profile 5; reset is still required to release the
diagnostic's resources. Native tests also cover invalid NMI sources, vector,
arm state, acknowledgement/mask, retry rejection and a second timeout.

Next is hardware qualification of a refused resume gate: deliberately invalidate
only diagnostic evidence after suspension, confirm CE remains clear and the
same outstanding transfer stays retained through timeout and host exit, then
reset and restore normal service. Generic PCI retry/error recovery, arbitrary
NMI/task recovery, abort, memory reclamation and broader stock-engine exclusion
remain separate work.

### P3g — refused resume and corrected retry (2026-10-19)

Profile 12 now exercises the refusal side of the actual resume gate on the card.
After deliberate suspension, real fault entry and the first 10000000-poll timeout,
it flips only the expected source fingerprint in diagnostic evidence. The gate
refuses. Restoring that fingerprint and calling again also refuses because the
attempt stays latched. A second 10000000-poll observer confirms the same active,
disabled DMA state, outstanding descriptor and remaining bytes. Host payload
stays partial, no marker appears, and source/chain, guards, peers, allocator
ownership and post-owner-exit retention checks pass.

[Design](../../rtems/accele160/fault/DMA-REFUSAL.md) and
[evidence](../../artifacts/current/accele160-dma-refusal-20261019/README.md).
The record is 240 words within its existing 4 KiB page; earlier profiles retain
their field meanings and modes 6–11 still replay. No live DMA memory is corrupted
and no resources are reclaimed. Normal service remains original profile 5.

Next: qualify an NMI-specific refusal (invalid recorded source/acknowledgement
evidence after a real NMI), preserving the actual MU acknowledgement and disabled
DMA, then reset and restore normal service. Generic corruption recovery, arbitrary
PCI retry/errors, DMA abort, task restart, release without reset and broader
stock SCSI/cache exclusion remain separate gaps.
