# Callback-free monitor entry and DMA/SCSI ownership gate

The `handoff` profile proves **bounded timer-interrupt monitor entry after the
ARM firmware callback has returned**. It does not transfer the controller to
RTEMS. This small bare monitor uses the existing owned interrupt stack; no RTEMS
scheduler runs in this profile. Production remains `autonet`.

Five final hardware sessions passed 20 entries, including five omitted-RELEASE
expiries, ten denied full-transfer requests, five stale-epoch rejections and
five HALTs. All restored RAM, timer/vector/MU state and unloaded normally.
[Batch and limitations](BATCH.md), [preserved evidence](../../artifacts/rtems-handoff-20261011/README.md).

## Contract

A single BIO ARM callback installs the timer and returns. While host sequence
remains 1, ioctl `0xc0204d04` accepts eight uint32 words: action, epoch, hold_ms,
then five zero words. Actions: 0 observe/release, 1 request ownership transfer,
2 observe without release, 3 halt timer. Host admission requires no pending
command, no unread callback result and no uncertain execution. It serializes
against callback/close and rejects stale epochs. Each live exchange records
sequence=1, pending=0, uncertain=0 and firmware completion bit=0.

Message 1 carries ENTER/PARKED/RELEASE/RETURNED/EXPIRED and HALT tokens. ENTER is
consumed before PARKED, preventing repeated entry after timeout. The ISR parks
only its original firmware interrupt continuation, checks the saved PC/AC/vector,
and returns through the existing owned-stack assembly. The loop is bounded by
1,000,000 iterations, **not a calibrated real-time deadline**. No host firmware
command is submitted during this interval. HALT precedes a second diagnostic
callback; close then verifies STOP before restoring RAM.

Full-transfer requests always receive DENIED. Target proof bits are literal
zero, never supplied by the host or inferred from idle registers. The required
0x7f mask represents DMA0, DMA1, DMA2, all SCSI channels, cache coprocessor,
watchdog/pending firmware work, and permanent RAM reservation. The only DMA
accesses are reads of control/status at 1400/1404, 1440/1444 and 1480/1484.
There are no DMA, SCSI or PCI-configuration writes in this monitor.

Uncertain control completion pins resources: the handle rejects further writes and close refuses to issue another
firmware callback or reclaim the allocation. Never force-unload that state.
The original failed test required a recovery reboot and physical intervention.

## Hardware ownership findings

The exact installed unpacked 4.07-0-29 image uses both primary DMA channels:
DMA0 descriptor/start/completion around C004BF68/C004BF90, DMA1 around
C004C0D0/C004C12C. `audit.py` checks disassembly bytes against the image before
emitting excerpts. Linear disassembly is not an exhaustive computed-reference
analysis. Absence of a DMA2 reference does not make DMA2 available.

The manufacturer's [DAC960PG Installation Guide](https://manualzilla.com/doc/7409909/mylex-dac960pg-installation-guide)
identifies up to three BA-81C15 SCSI ASICs behind secondary PCI and a MYL-86138
RAID/cache coprocessor. A usable programming/quiescence contract for these parts
has not been established. Host enumeration showing no functions on bus 38 does
not prove the internal devices are absent. A0000000/A1000000 descriptor values
are not a verified SCSI register map.

## Reproduction

Build on the established remote toolchain:

```sh
python3 project/rtems/build.py --work . --profile handoff
python3 project/rtems/handoff/build_transport.py --out handoff-module-v5 --payload handoff/kernel.bin
make -C /lib/modules/$(uname -r)/build M=$PWD/handoff-module-v5 CC=gcc-12 modules
# Requires production cleanly stopped, original RAM restored and card unbound.
sudo python3 project/rtems/handoff/live.py --payload handoff/kernel.bin --module handoff-module-v5/dac960auto.ko --output NEW-DIRECTORY --sessions 4
```

Offline: `python3 rtems/handoff/test_native.py`; extract `handoff-final.tar.xz` and `handoff-guard-final.tar.xz`
into a scratch directory and run `python3 rtems/handoff/verify.py --root DIR`.
The verifier checks pinned images/modules, raw traces, command-free monitor log,
report invariants, restoration and 25 corrupt report variants per session.
These are offline validation checks, not a new runtime C report gate.

## Remaining work

1. Recover BA-81C15/MYL-86138 register and firmware queue ownership, including
   abort/drain, posted writes, interrupts, watchdog and error paths.
2. Establish target-verifiable release contracts and a permanent RAM reservation.
   Keep full transfer denied until every required contract has evidence.
3. Integrate an RTEMS dispatcher into the bounded callback-free monitor while
   preserving the firmware continuation and checked return. This is a separate
   test from permanent takeover or concurrent disk I/O.
4. Only then design DMA buffer mapping and host-RAM/NIC integration. No channel
   or SCSI engine is presently granted to uploaded software.
