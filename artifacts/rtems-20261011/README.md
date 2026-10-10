# RTEMS / lwIP hardware work — 2026-10-11

The DAC960PG now runs actual RTEMS 4.6.6 Classic tasks and lwIP 2.1.3 on its
Intel i960RP, after normal PC startup. Linux carries complete IPv4 packets
between the card and a TUN interface; its routing/NAT gives the card Internet
access. DNS resolution, TCP connection setup and HTTP processing happen on the
card. [Maintained implementation and commands](../../rtems/README.md).

This is a cooperative RTEMS port, with persistent state between bounded calls.
It is not an autonomous/preemptive BSP: host polling supplies elapsed time,
RTEMS stays interrupt-masked, and the original firmware retains vectors/timers.
There was no reboot, flash write, recovery test or storage I/O test in this work.

## Identity and provenance

- Remote host: `mit@192.168.2.75`, Ubuntu 22.04.5, kernel `6.8.0-138-generic`.
- Card: `0000:37:09.1`, DAC960PG, i960RP, 16 MiB, firmware 4.07-0-29.
- Boot ID throughout: `a9429ca4-0144-452d-8a80-7189608ce99b`.
- Installed patched ROM / restored full staging SHA256:
  `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
- Tested network target SHA256:
  `a56aedbb32d211dd5dccc2f7a6258c47acf1f11b3fb906f464258abcaf0a504d`.
  Raw image 310,772 bytes; RIO1 prepared upload 471,136 bytes. This is a RAM
  payload, **not a firmware flash image**.
- Final acceptance module SHA256:
  `54096e78033a6fed2e1b42c3b77a2d81a8cba2e1634e3d948daeb4df39fcf50c`.
- Main-run module SHA256:
  `ab64cf53cefc4046206b55b081baa969a8916b4c904b6b1b87a55072b0d7c43a`.
- Original bounded tests used the already-tested `dac960loadrun.ko`, SHA256
  `e738bd6c3f023a4f4a7b67dd23e899869496e73df399b95d9a13a6f103b28745`.
- GCC 3.3.6/binutils 2.27 binaries and original sources were already preserved
  in `../toolchain-20261011/`. Commands retain the historical `i960-coff-`
  prefix but produce ELF.

`sources/` contains complete original RTEMS, Newlib, matching RTEMS Newlib patch
and lwIP packages. [sources.json](../../rtems/sources.json) pins their URLs,
SHA256 values and sizes. The builder verifies them before extraction. Newlib
provides headers; the linked runtime is the explicitly supplied small libc.

## What the experiments established

The initial one-shot image booted RTEMS and returned through its shutdown path.
Separate tests verified the 48-byte CPU context ABI and explicit fatal escape.
Two worker tasks then performed 200 iterations each with task switching and
local-register/stack cookies. Further tests exercised semaphore signalling,
200 message-queue values and a sleeping task that woke on the fifth injected
RTEMS tick. These are actual kernel operations, not a host simulation.

The persistent-session image retained RTEMS state across 1,000 callbacks.
Every response contained the expected callback count, worker count and tick
count. Mean checked-call latency was 51.274 ms. Full staging, borrowed runner,
command-table and result bytes were restored, and the module unloaded.

The first complete network test passed four ICMP echo requests, UDP payloads
of 1/31/500/1,400 bytes and a 16,000-byte TCP echo with exact SHA256 comparison.
The following Internet test resolved `example.com` using the card's lwIP DNS
client and fetched an HTTP 200 response through the host's TUN/NAT gateway.
Its 891 response bytes had SHA256
`ec206ac89a078703181d46346395bd4e36a37bc5220621b7b6e94450ad4a318d`.
The packet capture independently contains the DNS request/replies and complete
card-originated HTTP TCP streams; their bytes match the response returned by
the card. The DNS server was `192.168.2.3`; that run used `104.20.23.154:80`.
These are observations of this run, not permanent DNS mappings.

A separate loss/backpressure test deliberately discarded the first card TCP
data packet and used a small host receive buffer with a two-second read delay.
TCP recovered, the 16,000-byte echo matched, and DNS/HTTP still completed.
`deliberate-loss.json` and the PCAP preserve the injected packet and retransmits.

The half-hour guarded-stack run completed **29,352 callbacks** and **4,430 TCP
exchanges**, echoing **18,896,608 bytes** exactly in 1,801.028 seconds of the
stress phase. The final target counters reported zero TX queue drops. Mean
checked-call latency was 57.209 ms (54.100–101.424 ms); this includes transport
and readback, not just CPU execution time. Both reconstructed stress TCP streams
have SHA256 `a70d94d52849ebb24762bfce19551f4354799dcbfb3ae7ce4494d460c7026cc3`.

Independent offline verification checked all 29,352 request/response records,
918 saved RAM audits and 45,267 captured IP packets, including seven duplicated/
retransmitted data segments. All stack guards remained intact. The maximum
observed stack-use lower bounds were 28/1,106/256 bytes in 2,048/8,192/4,096-byte
allocations. Full staging and borrowed runner/table/result restoration passed;
the module unloaded and the card was left driverless.

The final rebuild then passed all seven one-shot modes (boot/shutdown, fatal
escape, ABI, task switching, simple semaphore signalling, queues and software
ticks). SIGTERM cleanup restored RAM and networking. SIGKILL of an established
session triggered clean kernel file-release restoration; the explicit journal
cleanup then removed the module and scoped routing rules and restored forwarding.
A malformed application operation returned explicit fatal `F0050002` through
the runner, was rejected with `ENODATA`, and still restored cleanly. These tests
did not force a command timeout, hardware fault, hot unbind or recovery.

The current persistent-session build passed another 1,000 exact callbacks
(mean 51.589 ms), with full restoration and unload. The original Tetris SSH
launcher then passed a 10-second regression: all **204 frames** matched the
native C reference, terminal settings were restored, all RAM was restored and
the Tetris module unloaded.

The foreground service mode also passed twelve sequential TCP connections and
a separate UDP exchange from another host client, followed by full restoration.
The final Internet/loss test fetched 892 HTTP bytes with SHA256
`1260ffa335a01e1064c89f3e09fe8047a92ad33ad061f7382c35d2b5b3716b21`;
HTTP headers can change between runs, so this is a separate observed response
from the earlier 891-byte capture. That final PCAP also records one 1,200-byte
Linux TCP retransmission from a connection left by the earlier process-kill
test (host port 49240), followed by a card RST. The new session correctly
rejected this old connection. The packet validator explicitly reports streams
without a captured opening SYN only when a reverse RST is present; all newly
opened echo connections still require matching complete byte streams.

Offline tests cover 348 command-boundary failures, stale/malformed requests,
six output corruptions, C/Python wire validation and 10,000 mixed malformed/
valid network packets under address/undefined-behavior sanitizers. These tests
exercise the generated transport and real lwIP code. They do not establish
behavior under all physical DMA failures or i960 exceptions.

## Early failures and their fixes

- `run-abi` returned `46600030`; the initial host expectation `4660002C` was
  wrong. `Context_Control` is 48 bytes because of aggregate alignment. Assembly
  field offsets were correct. The assertion was after successful restoration.
- `session-smoke` returned without advancing the worker. RTEMS's binary
  semaphore was being used as a signal, but this historical API gives it
  recursive-owner mutex semantics. Simple binary semaphores fixed the exchange.
- `net-local` returned explicit fatal `F0060147`: lwIP's DNS answer-size assertion
  at `dns.c:327`. The i960 aggregate ABI padded a ten-byte wire structure to
  sixteen bytes. A narrow packed-structure fix solved it. The fatal value is
  retained in the runner/result capture even though the final close log replaced
  the earlier command log.
- `net-local2` stalled after 9,600 echoed bytes. The 1,500-byte scratch limit
  rejected combined/refused pbuf chains. A static buffer sized to `TCP_WND`
  (4,800), atomic `tcp_write` and send-space checks fixed it. The PCAP preserves
  the zero-window/retry behavior. The host timeout still restored all RAM.

A final source-sync rehearsal also exposed macOS AppleDouble `._*.c` metadata
from an ad-hoc `tar` copy. GCC correctly rejected it before linking. Those
metadata files were removed, build/deployment filters now exclude them, and
the network image rebuilt to the same SHA256. This was a packaging failure,
not a card execution failure; its diagnostic log is preserved.

Failed experiments are retained with their actual outcomes. A clean close
summary proves cleanup, not that the application test passed.

## Artifact map

| Path | Contents |
| --- | --- |
| `sources/` | Original upstream source packages and RTEMS Newlib patch |
| `bounded-initial/`, `bounded-tests/` | Exact early target ELF/bin/map/disassembly and source snapshots |
| `session/`, `final-session/` | Original persistent echo target and final rebuild with the current CPU-header policy |
| `net-first-success/` | Exact first working ICMP/UDP/TCP/DNS/HTTP target |
| `net-guarded/` | Exact guarded-stack target used in the long test |
| `final-net/` | Independent final rebuild; target bytes match the long-test image; generated headers and static libraries |
| `final-bounded/` | Final one-shot API test image, including simple semaphore signalling |
| `final-module/` | Independently rebuilt Linux module and generated-source archive |
| `module-session/` | Exact main-run Linux module and generated sources |
| `source-snapshots/stress-start-source.tar.xz` | Exact remote project sources when the long test started |
| `source-snapshots/final-build-source.tar.xz` | Final maintained source and build dependencies installed remotely |
| `captures/completed-captures.tar.xz` | Original one-shot, persistent, initial networking and loss-test captures |
| `captures/stress-captures.tar.xz` | Complete 30-minute trace, RAM audits, PCAP and close captures |
| `captures/final-captures.tar.xz` | Rebuilt API/session tests, kill/fatal cleanup, foreground service, launcher and final Internet/loss captures |
| `captures/tetris-regression.tar.xz`, `tetris-regression/` | Final Tetris card captures and real-SSH transcript |
| `prepared-images.tar.xz` | Original cached RIO1 prepared images, named by SHA256 |
| `recovered-payloads/` | Exact original payloads recovered from prepared images and verified against each request's pre-recorded SHA256 |
| `validation/` | Independent trace, packet, immutability and restoration reports |
| `logs/` | Build and native test logs |

Prepared-image recovery removed only the injected lower guard and selected the
four-byte-aligned prefix whose SHA256 equals the original request metadata.
It does not reconstruct a missing ELF or imply that intermediate sources were
identical to the final port. `recovered-payloads/index.json` maps runs to binaries.

Run `python3 rtems/verify_artifacts.py` from the repository root to recheck
the archived experiments together. Alternatively, extract captures into a temporary directory and use the validators in
`rtems/transport/`. `validate_run.py` expects a successful complete trace;
negative tests and SIGKILL captures require their specific outcome/close checks.
`validate_packets.py` checks IP/transport checksums, duplicate segment identity
and byte-for-byte equality of both TCP echo directions. Two early host IPv6
packets are recorded separately; the target is IPv4 only, and later runs disable
IPv6 on the private TUN before bringing it up.

## Remaining work

A hardware-clock/preemptive RTEMS BSP still needs verified timer frequency,
interrupt-vector/stack ownership, a correct nesting-safe ISR implementation,
independent host transport and a demonstrated exit/reset path. The old RP BSP
contains board assumptions and defects and must not simply be enabled.

The current application uses lwIP's raw API in one RTEMS task (`NO_SYS=1`),
fixed private addresses/DNS, small bounded buffers and a deterministic PRNG.
It has no TLS, cryptographic entropy, full socket/POSIX layer or general libc.
HTTP response storage is limited to 8 KiB even though total received bytes and
the rolling hash continue to count; the host rejects an incomplete capture.
No memory protection separates tasks. Stack high-water readings are lower
bounds from untouched canary bytes, not a mathematical worst-case stack proof.

The host cannot preempt a runaway callback. Recovery remains untested, and
none of these tests establishes RAID disk-I/O coexistence or production safety.


## Final state and replay

`host-final.json` records the same boot ID, no DAC960 test module or bound card
driver, no `i960rt0`, IPv4 forwarding restored to 0 and no project firewall rules.
The installed foreground launcher is
`/home/mit/i960-rtems-final-20261011/serve.sh`. It passed a real-SSH smoke run
with a bounded service interval and clean restoration. Nothing is left running
on the card; starting the launcher creates a fresh RTEMS RAM session.

The collective offline verifier passed **30 RTEMS experiment captures**; the
separate Tetris validator passed all 204 regression frames. Source and binaries
are preserved in Git; compressed capture archives retain their original files.
