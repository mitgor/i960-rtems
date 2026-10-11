# Current findings and evidence — 2026-10-11

**MU echo milestone (2026-10-11):** a timer ISR echoed an IMR1 word through OMR1
in 11.02 ms while firmware sequence stayed 1 → 1. Full timer/RAM/MU restoration
and module unload passed. The first trial retained resources after an incorrect
local OISR acknowledgement; a host reboot and host-side acknowledgement fix
preceded the successful retry. [Implementation](rtems/control/MU-ECHO.md),
[evidence](artifacts/mu-echo-20261011/README.md). Independent STOP and unrestricted
preemption remain unproven; next is framed control plus independent STOP.


The current implementation backlog is [the integrated development plan](DEVELOPMENT-PLAN.md),
including a gap ledger G01–G12 and the next loader milestone M1.

This is the current-state index. Earlier reports and artifact source snapshots
record the state at their own milestone; their future-tense plans are historical.
The earlier preservation audit was read-only. The subsequent RTEMS work loaded
RAM payloads and exercised the card. The later MU cleanup trial required a host
reboot; no additional flash programming or recovery testing occurred.

## Established on this card

| Finding | Evidence and usable implementation |
| --- | --- |
| A complete 512 KiB ROM can be recovered while the card is installed, without an external programmer. | [ROM inventory](artifacts/ROM-INVENTORY.md), original dumps and Fujitsu packages in `artifacts/private-dumps/` and `artifacts/vendor-fujitsu/`. |
| Stock DRAM initialization has been traced, including two candidate board-register profiles; decoded timings in nanoseconds have not been established. | [DRAM analysis](DRAM-ANALYSIS.md). Stock initialization is retained. |
| A stock-preserving patch has been programmed once and validated after reboot. | [Programming result](FIRMWARE-PROGRAMMED.md), paired full readbacks and postboot PING in `artifacts/programmed-rom-20261010/`. |
| The boot-installed `0x6F` dispatch target is `FEFE001C`; PING returns `017E`. Boot straps remain Mode 3. | Postboot paired table reads and calls; this is software extension of stock firmware, not Mode 0 boot. |
| Returning i960 programs can be uploaded and executed after the PC has booted, without further flash writes. | [Software loader](SOFTWARE-LOADER.md), `host/loadrun/`, `loader/runtime/`. Cache invalidation and restoration are part of the protocol. |
| The 64 KiB scalar limit is policy, and a larger RAM profile is already proven. | The initial RTEMS profile uses a 310,772-byte image (the dual-stack revision uses 315,108 bytes) and 471,136-byte prepared upload inside the existing 512 KiB staging window. [Memory limits and extension stages](DEVELOPMENT-PLAN.md#what-can-be-extended-now). This does not establish ownership of the rest of the card's 16 MiB DRAM. |
| BIO1 returns bounded text/frame data; Tetris has an explicit bounded update/render ABI. | [Buffer I/O](BUFFER-IO.md), [Tetris step](TETRIS-STEP.md), `game/`. 4 KiB input, 8 KiB output; Tetris uses 256-byte requests and 2,160-byte responses. |
| Repeated execution and persistent sessions are hardware-tested. | [T3 replay](TETRIS-REPLAY.md): 1,000 + 64 calls. [T5 session](PERSISTENT-SESSION.md): 1,000 frames and a separate 400-frame cadence test. |
| A card-hosted IPv6 HTTP server works. | GET from the Mac to the host global IPv6 port 8080 reached the card through DNAT; bounded HTTP request tests passed. The autonomous service is running for user testing. [Current report](artifacts/rtems-web-autonomous-20261011/README.md). |
| Hardware timer interrupts can wake RTEMS tasks. | Eight interrupts/eight higher-priority task wakeups during a bounded busy-loop experiment; timer/vector/mask and RAM restored. Background execution passed 2,009 ticks/wakes in 20 host-silent seconds; networking advanced 509 ticks in five silent seconds. SIGTERM/SIGKILL/error cleanup passed. |
| IPv6 networking works on the current cooperative RTEMS port. | [Dual-stack implementation and live evidence](artifacts/rtems-ipv6-20261011/README.md): ICMPv6, UDP/TCP, AAAA and IPv6 Internet HTTP through NAT66. Static addressing; DNS transport remains IPv4; fragmentation, SLAAC, sockets and TLS remain gaps. |
| RTEMS Classic tasks and card TCP/IP execute after PC startup. | [Cooperative RTEMS port](rtems/README.md), [exact artifacts](artifacts/rtems-20261011/README.md). Persistent tasks, lwIP ICMP/UDP/TCP, DNS and HTTP through Linux TUN/NAT; clock/progress depend on host polling. |
| Tetris is playable over SSH. | [Terminal instructions](TETRIS-TERMINAL.md), `host/session/`. T4's five automated SSH runs validated 36,380 frames; the 30-minute run contributed 35,846 at 19.91 Hz. |

Original full-ROM SHA256:
`43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93`.
Installed patched candidate SHA256:
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
The unchanged final 16 KiB boot block is part of the programming validation.
The known card is `0000:37:09.1`, `1069:0010`, firmware 4.07-0-29, 16 MiB DRAM.

These hashes identify validated images, not every file called `stage-*` or
`candidate-*`: runtime captures also contain transient RAM overlays. Those
files must not be used as flash images. Historical stock-preimage rehearsals
are expected to reject the now-patched card; do not bypass their pinned hashes.

## Limits and unresolved questions

- General scalar loading is still capped at 64 KiB; BIO1 has a separate 32 KiB
  code boundary. RIO1 supports larger images but is not yet a shared general
  loader profile. Memory outside the staging allocation is unowned for application
  purposes until proved otherwise. See M1–M3 / G12 in the integrated plan.
- Recovery has not been demonstrated. The user excluded recovery testing;
  serial wiring/photos and adapter work remain future work. A spare card does
  not establish that this card is recoverable.
- SSH returned late after programming/reboot. The user reported the PC back,
  but did not confirm a power cycle or explain the delay. Its cause is unknown.
- No RAID disk-I/O compatibility or general production-stability validation was
  performed. Tests used an otherwise idle card with its storage driver unbound.
- DRAM register component identity, bit meanings, clock and timing units remain
  unresolved. Recovered register literals are not a complete timing specification.
- Payloads must return cooperatively; the host cannot preempt a runaway call.
  The RTEMS profile adds explicit BSS initialization, private persistent state
  and three guarded task stacks. The autonomous profiles additionally borrow timer 1 with verified restoration;
  full Newlib/POSIX support and memory isolation are not established.
- Persistent sessions check the full payload/code/input/output region every
  frame, and the entire 512 KiB staging image every 32 calls and at close.
  Corruption outside the per-frame region can remain undetected for 31 calls.
  Uncertain execution/restoration retains resources rather than retrying code.
- SIGKILL cleanup, ownership and many command failures were tested, but real
  hardware command-failure injection and hot unbind were not. Native fault
  simulation is not evidence of every physical failure mode.
- T4's half-hour acceptance run used scripted keys, with game-over periods and
  68 restarts. It is not a human gameplay or uninterrupted-running-game claim.
- RTEMS tasks and host-routed TCP/IP now work in the [cooperative profile](rtems/README.md).
  Bounded background RTEMS and its hardware clock now pass live tests;
  independent host transport and exclusive takeover remain unvalidated. The [integrated plan](DEVELOPMENT-PLAN.md) describes
  those additional gates in A1–A3; a working cooperative session does not satisfy them.

## Preservation and current host observation

The [preservation audit](artifacts/preservation-audit-20261011/README.md) maps
remote files to local files or archive members by SHA256. It preserves missing
historical builds without replacing current source. The exact Linux cross tools
and original source packages are in [the toolchain archive](artifacts/toolchain-20261011/README.md).
Root `toolchain.sh` remains the build recipe. Kernel modules are specific to
`6.8.0-138-generic`; historical binaries are evidence, not automatically safe
programs to run on a different card or kernel.

At the start of the October 11 audit a separate terminal session was running
under `/home/mit/i960-tetris-t4/sessions/20261011-000116/`, PID 17974, on the
same boot `a9429ca4-0144-452d-8a80-7189608ce99b`. It was left untouched.
The previous test's “driverless/module unloaded” result describes its cleanup,
not the machine while this new session is active. See the audit for collection
status; unfinished traces do not prove final restoration or module unload.

That session subsequently exited normally during the audit. Its complete archive
and independent validation are now preserved: 2,224 native-matching frames,
111.387 seconds, successful RAM restoration and unload. The final host snapshot
again showed no DAC960 module or bound controller driver, on the same boot.
This session is additional to the five scripted T4 acceptance runs.


The subsequent [RTEMS implementation](rtems/README.md) completed a separate
half-hour TCP test: 29,352 callbacks, 4,430 exchanges and 18,896,608 exact echoed
bytes. Independent checks covered 918 saved RAM audits and 45,267 IP packets.
Task-stack guards and full close restoration passed. Final rebuild tests also
covered explicit fatal return, SIGTERM and established-session SIGKILL cleanup.
The original firmware's vectors/timers and flash remain unchanged by this work.

A final Tetris SSH regression after RTEMS matched all 204 frames against native
C and restored terminal settings/RAM before unloading. The RTEMS foreground
service also passed twelve sequential TCP connections and UDP.

## Preemption and DMA roadmap (2026-10-11)

See the [staged preemption and DMA plan](RTEMS-PREEMPTION-DMA-PLAN.md). Order: independent control
and ownership prerequisites → arbitrary application-task preemption → host-RAM
DMA networking → gated direct peer experiments. Read-only direct-DMA research
has started; current NIC and Mylex occupy separate PCI branches. This is a plan
and initial inventory, not implemented preemption or verified peer DMA. Keep
the active web service on the existing bounded runtime.

## P0/P1 audit and prototype checkpoint (2026-10-11)

The [interrupt audit](rtems/control/INTERRUPT-AUDIT.md) is written. The
[control protocol prototype](rtems/control/README.md) passes native tests
and a two-process shared-memory demo, and cross-compiles for i960. Read-only
PCI configuration confirms PIATVR=C0000000 and the existing 8 KiB window.
No live independent control writes are enabled: the MU overlay/index interrupt
side effects and stock mailbox/stack ownership still require a proven reservation.
This completes the offline prototype, not P1 physical validation or preemption.

## Control ownership follow-up (2026-10-11)

The [matching-firmware ownership trace](rtems/control/OWNERSHIP.md) identifies active handler/fault
data and mailbox/interrupt-stack uses in the BAR window. No RAM slot is reserved.
Three read-only MU samples found IMR1/OMR1 zero with message interrupts masked.
These are selected for a separate, driver-serialized bounded echo experiment;
no live sideband writes have occurred. Use the pinned 4.07-0-29 evidence, not the
older 4.07-0-39 `remote-analysis` reference.
