# AcceleRAID 160 controller emulator, first executable slice

This runs the actual 1 MiB stock or candidate flash image in a bounded i960
interpreter. It is a diagnostic harness, **not yet a validated 80303 emulator or
a clearance to flash**. The [QEMU PCI probe](qemu/README.md) presents the
measured host identity and BAR and can forward the first host mailbox to the
i960 interpreter. Its interrupt routing and command completion remain open.

The interpreter is a modified source copy of [sim5](https://github.com/DrItanium/sim5)
at commit `8fef7ba932aaa4902f70f11a3c3c0157f15d00d1`; retain its BSD license
at `third_party/sim5/LICENSE.txt`. The changes expose IP/fault state, use the
card's flash and 16 MiB RAM execution maps, stop on unsupported instructions,
implement register `cmpob`/`cmpib`, the observed `intdis` and D-cache-enable
operations, and repair call/return tracking and 16-byte Jx frame alignment
for the observed reset and RTEMS context-switch paths. The Jx `modpc`
src/dst operand now supplies the replacement PC bits, and reset fetches ICON
and IMAP0-2 from the PRCB control table. These changes have not passed a
standalone i960 ISA conformance suite.

On Linux x86-64 with g++ supporting GNU C++20:

```sh
sh build.sh
python3 test_isa.py
python3 stock_loader_gate.py /path/to/original-card-stock-1MiB.bin
python3 candidate_scheduler_gate.py /path/to/original-card-candidate-1MiB.bin
python3 compare.py /path/to/saved-stock-1MiB.bin /path/to/candidate-1MiB.bin
python3 compare.py /path/to/saved-stock-1MiB.bin /path/to/candidate-1MiB.bin --explore
python3 compare.py /path/to/saved-stock-1MiB.bin /path/to/candidate-1MiB.bin --explore --board-id 11
python3 qemu_option_rom_smoke.py /path/to/saved-stock-1MiB.bin /path/to/candidate-1MiB.bin
```

On Apple Silicon macOS, the same `build.sh` cross-builds this interpreter as
x86_64 Mach-O and runs it under Rosetta. The copied sim5 core needs x86
extended-real representation. The local 2026-11-15 stock/candidate and QEMU
results are recorded in
[the Mac simulation artifact](../../../artifacts/current/accele160-local-mac-emulation-20261115/README.md).

The default comparison stops at the first unmodeled peripheral access.
`--explore` continues with zero-backed placeholders and exposes a longer,
**speculative** trace. The copied sim5 memory backend allocates a 4 GiB
address-space array. Use a machine with sufficient virtual memory. The two
images are read-only inputs; the commands do not access the PCI card. The
command exits nonzero while the gate is incomplete.
`test_isa.py` runs a synthetic reset ROM that distinguishes clear/set bit
conditions, signed/unsigned byte/short comparisons, most-significant
set/clear bit scans, and `modpc` operand/readback behavior. `stock_loader_gate.py`
pins the original and spare stock images and checks their two ZIP1 tables, expanded CRC and
first runtime entry. Its pass means only that the loader milestone was reached.
`candidate_scheduler_gate.py` pins both candidate images and checks their
bounded RTEMS worker report and zero-code park. Its pass is an offline CPU-path
result under the exploratory initial board byte, not a physical boot result.
`--board-id` supplies an exploratory initial low-five-bit response for
`0xe0400000` and is allowed only with `--explore`. Later firmware writes to
that address replace the initial value. The original card returned `0x0b`
in two [post-boot RAM calls](../../../artifacts/current/accele160-board-id-20261025/README.md),
but reset-time behavior and the other card remain unmeasured. The override
does not convert a trace into a validated hardware boot.
An [exact failed-spare sweep](../../../artifacts/current/accele160-reset-selector-sweep-20261025/README.md)
reached the RTEMS worker report under 30 of 32 possible initial low-five-bit
selector values. Selectors 8 and 9 take a special stock reset path that
polls an unmodeled hardware-ready bit; stock and candidate both remain there
in the model. This does not identify the physical POST failure.
The generic QEMU command loads the common 28 KiB x86 option ROM with QEMU's generic
`-option-rom` path and confirms that its entry executes under SeaBIOS. It does
not provide the AcceleRAID PCI function, BAR, mailbox, or i960 controller, so it
cannot determine whether the physical host would complete POST with either
full firmware image.
The newer QEMU PCI probe confirms that SeaBIOS executes the same ROM on a
device with the measured PCI identity. Its bounded run does not access BAR0 or
extended configuration and cannot compare controller firmware behavior.
Separate qtest workloads now reach the interpreter's RAM through PIATVR and
submit the first LP hardware mailbox through guest DMA. The interpreter logs
the exact 64-byte request but does not yet execute or complete it; see the
[mailbox transport record](../../../artifacts/current/accele160-qemu-mailbox-20261025/README.md).

Current evidence on the remote Linux x86-64 host: both images perform the same
documented 80303 core and flash-bank configuration writes, then strict mode
stops at cycle 56 on an unmodeled read from `0xe0400000`. The later post-boot
capture establishes `0x0b` on the original card, but not its power-on value.

The first exploratory run exposed an interpreter error: `chkbit` inverted the
condition code for a clear bit. That made stock attempt a 256-entry literal
tree even though the ZIP1 flag calls for 64 entries. Correcting it and adding
the missing Jx short comparisons let stock build both 64-entry tables, match
the expanded CRC `d93addd1`, and reach runtime entry `c004cf70` at cycle
48,565,709 with the exploratory initial board byte `0x0b`. It ran to the
100-million-instruction budget without another CPU fault. Peripheral accesses
remain unmodeled, so this is not a validated board boot. The candidate reaches
its RTEMS entry, executes its Init and Worker tasks, and writes PASS after 64
worker iterations. A corrected most-significant `scanbit`/`spanbit` result
allowed RTEMS to select Init instead of idle. The [run record](EVIDENCE.md)
has the exact results.

The model hardcodes an absent UART response at `0xe0600007`, matching the saved
live observation that the startup console probe failed. Recognized reset writes
to core memory-control and interrupt registers and flash-bank registers are
stored, but their side effects have not been fully modeled. Other registers
are plain storage in exploratory mode. The 16 MiB RAM execution range is a
documented hardware hypothesis.
The optional `--explore-timer-clock` models one 80303 bus clock per executed
instruction, including timer-0 divide, countdown, auto-reload, and TINT0's
pending bit in IPND. This clock ratio is an explicit simulation assumption,
not a measured board timing. `test_timer0.py` checks the register behavior.
The separate `--explore-timer-interrupt` mode also delivers an eligible TINT0
vector to the i960 core and models interrupt-frame return. `test_interrupt.py`
checks a synthetic vector `0x82` handler and exact return IP. In the coupled
stock replay, vector `0x82` reaches `0xc0000418` and returns after nested
calls. The 450-million-instruction gate delivers 55 timer interrupts with no
CPU fault. An extended 900-million-instruction gate delivers 235 interrupts
and reaches the stock startup monitor and scan callback once each; the Linux
mailbox remains pending. See the [interrupt gate](EVIDENCE.md) for the bounded
result and the exact-runtime disassembly correction.
The bridge's diagnostic `Q` command reads `IISR & ~IIMR`, the inbound MU
status sources currently exposed past the local mask. It does not assert an
80303 XINT input or enter an i960 interrupt handler. A pending doorbell with
`IIMR=0xffffffff` reports zero unmasked sources in the stock replay.

The optional `--explore-qlogic-pci` exposes the five secondary-PCI dwords
captured from the installed ISP10160 at slot 16. Stock then discovers one
channel and enters ISP setup. With that option alone, the first QLogic mailbox
waits because no ISP processor exists in the emulator. The separate
`--explore-isp-mailbox` experiment implements the observed register test,
single-word RISC RAM access, bounded DMA load/dump, and firmware checksum
using a 64K-word model. It returns success only for in-range DMA and a zero
checksum over the loaded range. Stock passes those gates and reaches command
`0x0002` to execute the uploaded ISP firmware; no ISP processor is yet
emulated, so the Linux mailbox remains pending. `test_isp_mailbox.py` checks
the handshake, DMA round-trip, checksum rejection, and invalid-bus hold.
`qemu/test_mailbox_submit.py --dump-isp-risc` saves the exact uploaded image
from the bounded replay. `qemu/inspect_isp_risc.py` checks its declared word
length, 16-bit checksum, address bounds, and embedded QLogic header. The
captured image identifies itself as ISP1216 firmware version 10.01. The
opening `0804 1041` words also appear in QLogic's published ISP12160 firmware,
but their execution semantics have not been established; the execute-firmware
mailbox remains a hold. This is a trace aid, not a physical boot result.

For host-flow discovery only, `--explore-isp-execute-ack` acknowledges
`0x0002` after the captured image passes its address, length, header-word,
checksum, and byte-stream fingerprint guards. `--explore-isp-about-ack`
additionally answers `0x0008`
with major/minor `10.01` from that image's text. Neither option runs an ISP
instruction. The coupled stock replay then reaches `0x0010` (initialize
request queue) and waits there; see the
[bounded run](../../../artifacts/current/accele160-timer-interrupt-20261025/README.md).
The further `--explore-isp-queue-ack` experiment records bounded request and
response ring registrations after the version response. Stock registers 256
request entries at `0xfe600df0` and 128 response entries at `0xfe604df0`,
then waits at `0x0032` (set retry count). It does not process IOCBs or
complete the host mailbox.
The newer [configuration probe](../../../artifacts/current/accele160-isp-config-20261025/README.md)
accepts only the observed, ordered `0x0032`, `0x003a`, and `0x0035` commands.
Stock then waits at `0x004a` (set firmware features). A coupled run of the
actual x86 option ROM submits a `GET_CTLR_INFO` request; after 900 million
modeled i960 instructions with timer interrupts, MU setup and receive remain
unvisited. There is still no command completion, so this is not a flash gate.
The later [feature/status diagnostic replay](../../../artifacts/current/accele160-isp-feature-status-20261025/README.md)
acknowledges the exact `0x004a` request and reaches `0x001f` GET FIRMWARE
STATUS. A separately gated zero-output hypothesis and initiator-ID ACK reach
`0x0018` BUS RESET. Those fabricated ISP responses are branch-discovery tools,
not measured behavior; SCSI reset and the host mailbox completion remain
unmodeled.
The [local scan continuation](../../../artifacts/current/accele160-isp-bus-reset-20261115/README.md)
adds opt-in, exact BUS RESET and ordered target-parameter acknowledgements.
With timer interrupts enabled, stock completes target setup for 0–15 and
advances to scan state 3 after a billion instructions. MU setup/receive and
the host mailbox completion remain absent.

We must validate register-frame/context-switch semantics more broadly, model
the 80303 devices, and make stock firmware consume the submitted mailbox
before treating candidate behavior as a boot result. The identical reset
prefix does not explain the candidate's physical POST failure.

Intel's [Jx instruction reference](https://www.bitsavers.org/components/intel/i960/272483-001_Intel_i960_Jx_Microprocessor_Users_Manual_Sep94.pdf)
defines `intdis` and the `dcctl` function used here. The adapter currently
models their state transitions without cache timing or external interrupts.
The [80303 initialization guide](https://www.bitsavers.org/components/intel/i960/80303/273395-005_80303_IO_Processor_Prog_Guide_and_Initialization_200104.pdf)
names the reset register addresses used in the write audit.
