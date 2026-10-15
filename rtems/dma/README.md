# Exclusive card-to-host DMA proof

For the newer card-initiated two-host-buffer producer, see
[ping-pong DMA](pingpong/README.md) and its
[acceptance record](../../artifacts/dma-pingpong-20261015/README.md).
Doom integration and DMA1 WAD coordination are accepted in a bounded browser
run: [Doom ping-pong results](../../artifacts/doom-pingpong-20261015/README.md)
(**3.503 → 3.887 FPS**, full audits retained).
The historical proof below uses individually submitted transfers.

Task-owned asynchronous physical acceptance passed in two runs: 48 exact
transfers, 124 full audit pairs, explicit STOP and session-deadline cancellation.
Maximum IRQ gap is 10.710–10.990 ms, down from 111.481 ms. Opt-in `--dma-proof`;
not used by normal Doom play or public HTTP. The separate
[pinned-frame comparison](FRAME-DMA.md) is opt-in; four frame comparisons passed but the full batch failed on a
completion timeout. No Doom DMA FPS acceptance. See the [asynchronous batch](../../artifacts/dma-async-20261014/README.md).

Worker 1 prepares, launches, polls and validates with interrupts enabled, using
its existing audited IRQ stack. Control handlers only stage/publish jobs and
read reports. Phase word 31 is 1 while pending and 2 when terminal. Argument
mutation is refused while pending. Linux op 1 submits; op 3 checks completion
(EAGAIN while pending); op 2 reads validated data. The session mutex is released
between calls. Full byte/guard validation remains mandatory before readback.
STOP before launch returns error 10 without writes; STOP after launch permits
bounded completion before retirement. Known prelaunch cancellation remains
readable but forbids new jobs. No timeout authorizes recycling resources.

The October 14 user request permits exclusive DMA ownership, remapping and
firmware changes if necessary. This prototype changes neither flash nor ATU
windows. Firmware bootstraps the existing owned RTEMS profile and remains parked.

The accepted secondary reset, fault ownership, queue reclamation, 12 MiB RAM
ownership and atomic dispatch profiles precede DMA. DMA1 is used because it is
a primary-bus channel without DMA0's demand-mode interface. Entry refuses any
nonzero DMA0/1/2 control/status and requires primary command 2, secondary command
0 and SACR 0x13ffc. Only primary bus mastering is temporarily enabled. Each
single descriptor specifies Memory Write (7), no interrupt, no DAC and no next
link. No stock firmware continuation or second DMA producer is allowed.

Linux allocates 73,728 coherent bytes against the actual PCI device using its
32-bit DMA mask. Userspace supplies only length, offset, seed and sequence; it
cannot supply a host physical/DMA address or card source pointer. The target's
fixed source and descriptor live inside the audited mutable image. COFF limits
object alignment to 16 bytes, so an oversized descriptor array is explicitly
rounded to a 32-byte boundary. The unchanged 128 KiB immutable code boundary is retained; normal profiles
are unchanged.

The target generates a deterministic pattern, publishes a six-word descriptor,
and polls at most 200,000 times. Completion requires inactive/no-error CSR,
consumed NDAR, matching DAR and zero remaining count. CCR1 is then disabled and
primary bus mastering cleared; all-channel isolation and source bytes/guards are
checked again. A zero count alone is never sufficient. This is a polling bound,
not a measured wall-clock deadline. The host additionally bounds each transaction
by ten seconds and verifies every destination byte, including all guard space.

Each run transfers lengths 1–65,536 at aligned and unaligned offsets, repeats
with new seeds, and captures the entire coherent allocation after every transfer.
Full existing monitor/RAM audit pairs surround every transfer. Bad size/offset,
stale epoch/sequence and stale readback are refused. Normal STOP and full heap
retirement are checked by the existing resident harness and independent replay. Hardware also tests a
3,000-tick RTEMS deadline canceling a pending job before launch.
Native tests execute the actual target and host C, including error/timeout and
copyout failures. Physical fault injection and an active DMA abort are not claimed.

Uncertainty disables further requests and retains the mapping/module/device.
Clearing CCR only suspends a channel; it is not an abort or quiescence proof.
Even successful runs retain the coherent allocation until reboot, matching the
resident session's lifetime. No forced unload/unmap is permitted. Archive and
verify evidence locally before reboot. This conservative prototype does not yet
support a reusable DMA buffer pool or production disconnect/restart lifetime.

Primary reference: Intel i960 Rx Developer's Manual 272736-002, §4.4.4
(write-through CPU data cache), §20.3.1–2 (descriptor format and submission),
§20.7.1–2 (enable/status/error semantics), §20.7.8–9 (count/control). DMA uses
direct PCI addresses; no host physical-address guess or borrowed NIC mapping.

Tests: `python3 rtems/dma/test_target.py`, `python3 rtems/dma/test_host.py`,
`python3 rtems/dma/test_replay.py`. Replay error numbers are the Linux ioctl ABI,
independent of the machine running the offline verifier.
Physical evidence and exact commands: [October 14 batch](../../artifacts/dma-owned-20261014/README.md).
