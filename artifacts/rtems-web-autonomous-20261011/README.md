# IPv6 web server and hardware-clock RTEMS — 2026-10-11

The card serves HTTP and runs bounded RTEMS work from timer interrupts between
host commands. No flash programming was performed. Three failed experiments
required host reboots; their evidence is retained alongside successful runs.

## Public test endpoint

`http://[2a02:8106:40:9000:f662:19ee:dbad:1f1e]:8080/`

This is the Linux host's assigned global IPv6 address, DNATed to card address
`fd96:196:960::2`, TCP 80. The card produces the page. A Mac GET succeeded;
access from outside the LAN has not been verified and depends on upstream
IPv6 routing/firewall policy. This address may change with the host prefix.
`http-autonomous-response.html` is the returned body; `http-autonomous-tests.json`
records 24 successful requests, including fragmented headers, invalid methods,
oversized headers and repeated connections.

The transient `i960-http6` service is deliberately left running for user testing.
It uses `/home/mit/i960-rtems-web-20261011/serve-autonomous.sh`, `autonet/kernel.bin`
and its exact SHA256-pinned `autonet-module5/dac960auto.ko`. Its active output is
`http-autonomous-public-final`; `live-service.txt` records status, boot ID,
publication and binary hashes. Stop with `sudo systemctl stop i960-http6`.
This is not a reboot-persistent service. While it runs, the module, borrowed RAM,
TUN interface and journaled gateway rules are intentionally active.

## Established results

| Experiment | Evidence |
|---|---|
| Observational inventory | Two reads; timer 0 active, timer 1 count/reload/mask/pending clear; PRCB/vector-cache layout recorded in `inventory.json`. Mode registers were not read by the inventory because those reads clear terminal status. |
| Bounded IRQ preemption | Eight ticks and eight higher-priority task wakeups while a lower-priority busy loop advanced; timer/vector/masks and RAM restored. |
| Background RTEMS | 2,009 ticks and 2,009 timed task wakeups during 20 host-silent seconds; about 100.024 Hz, clean stop/restore/unload. |
| Background networking | 509 ticks in five host-silent seconds; dual-stack ping/UDP/TCP, loss recovery and IPv6 Internet HTTP passed. |
| IPv6 stress | 60.393 seconds, 130 iterations, 554,528 bytes, SHA256 `a6a6f75f57946c33e03c4e2309faa705fc1260ff54c35226fb308b6529ab3bf2`. |
| Final target cleanup | Live SIGTERM, SIGKILL with manual gateway cleanup, and rejected operation 99 all stopped/restored/unloaded. `logs/autonet-cleanup-final.log`. |
| Final target HTTP | Global-address Mac GET plus 24 request tests passed. Final service startup also passed IPv4/IPv6 echoes and an IPv6 Internet fetch. |
| Native checks | `make -C rtems test` passed, including ASan/UBSan network tests, gateway rollback and 344 fault boundaries for each autonomous transport variant. `logs/native-final.log`. |

The background timer uses reload 41667 and divide-by-eight, approximately
100 Hz on the measured 33.333 MHz bus. Timer 0 remains stock-owned. The runtime
borrows cached vector F2 at internal RAM 0x3C, preserving the original mask plus
timer 1. Each interrupt saves global registers on its own interrupt stack frame,
resumes bounded RTEMS work and returns to stock firmware. The network profile
advances RTEMS/lwIP time from this hardware event, not elapsed host polling time.

## Failed trials and corrections

1. `auto-failure1.tar.xz`: a timer-only interrupt mask blocked stock command
   service. Corrected by retaining the stock interrupt sources.
2. `auto-failure2.tar.xz`: background ticks worked, but STOP timed out because
   the `modpc` helper had an uninitialized input. Corrected with an explicit
   read/write operand. The tick reload was also adjusted from 20000 to 41667.
3. `autonet-cleanup-first.tar.xz`: signal cleanup passed, but a completed invalid
   application request set the generic session-ready flag false and blocked
   STOP. No timer was armed in that case; ownership was nevertheless retained.
   The final module permits only the independent verified STOP path after such
   a completed error. Pending/uncertain execution still prevents restoration.

Each failure retained resources instead of overwriting a potentially live
handler. Reboots recovered command service. None establishes general recovery
from arbitrary target faults. An early final HTTP test was interrupted by this
session stopping its service to archive it; the complete 24-request test was
rerun successfully on the persistent final service.

## Preservation and verification

Each archive preserves its own build and capture versions; do not overlay their
same-named build directories. `preboot-successes` contains the cooperative HTTP,
inventory and bounded IRQ runs. `auto-success3` contains the 20-second silent
run. `autonet-first` contains the five-second silent and minute-long network
runs. `autonet-final` contains the final target/module/source, final cleanup
suite and a closed public HTTP session. Successful earlier experiments used
those archived earlier binaries; do not present them as executions of the final
binary. The final target separately passed cleanup, HTTP and dual-stack echoes.

Run `python3 rtems/autonomous/verify_artifacts.py --output <report.json>` from the
repository root. `validation.json` records 18 checked captures, preserving
failed outcomes explicitly. The verifier checks binary/image hashes, guard
frames, paired response data, packet checksums and RAM restoration where
applicable. A SIGTERM can leave one submitted command without a trace record;
a killed gzip stream can lack its footer. Neither is represented as a complete
normal trace. Top-level artifact manifests cover all files and archives.

## Limits

This is a stock-coexisting bounded IRQ runtime, not an exclusive standalone BSP.
Linux still owns the relay and moves packets through firmware commands. Arbitrary
long-running tasks, nested interrupt support, general hardware fault recovery,
RAID disk I/O compatibility, and long-duration autonomous stability are unproven.
The web service is plain HTTP with four connection slots and a 512-byte header
limit. IPv6 uses a static card ULA and host NAT66/DNAT; SLAAC and native card-global
addressing are not implemented. The independent transport and exclusive handoff
gates remain in `DEVELOPMENT-PLAN.md`.
