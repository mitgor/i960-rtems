# Profile 17: chip queue indices versus firmware cache

This opt-in normal-runtime profile combines the profile-14 core inventory,
profile-15 physical PCI identity and profile-16 fixed RAM snapshot with twelve
16-bit reads from the ISP10160. It does not stop the SCSI processor, acknowledge
interrupts, publish queue indices, issue mailbox commands or grant memory.

## Access contract

The pinned firmware reads request-consumer mailbox 4 at chip `+0x78` in
`c0070614..c0070660`; the cached consumer at context `+0x4e` is refreshed on the
queue-space path. Request producer is `+0x4c`. The response callback at
`c006ef80` reads mailbox 5 at `+0x7a`, stores response producer at context `+0x50`,
and processes completions against consumer `+0x52`. Its unbounded debounce loop
is not copied. Mailbox commands also use these registers, so values need status
context and must not independently authorize reclaim.

FreeBSD releng/12.4 `sys/dev/isp/isp.c` selects OUTMAILBOX4/5 as request-out and
response-in for the pre-2300 family. `ispreg.h` places PCI mailboxes at `0x70`,
ISR at `0x0a` (read-only) and semaphore at `0x0c` (read/write). `isp_pci.c` reads
these with `bus_read_2`; clearing/acknowledging uses separate writes. These four
registers do not require bank selection or a paused RISC. Provenance and source
hashes are preserved with the test artifacts:

- https://raw.githubusercontent.com/freebsd/freebsd-src/releng/12.4/sys/dev/isp/isp.c
- https://raw.githubusercontent.com/freebsd/freebsd-src/releng/12.4/sys/dev/isp/ispreg.h
- https://raw.githubusercontent.com/freebsd/freebsd-src/releng/12.4/sys/dev/isp/isp_pci.c

The chip extension refuses access unless the preceding physical config capture
completed, PCI identity is `1077:1016`, memory decoding is enabled, BAR1 is
`fff00000`, and the RAM snapshot verified context `c0600d00` with chip mapping
`8bf00000`. The earlier config helper restores SOCCAR on normal return. It
writes only the selector, never device config. A transaction fault can prevent
restoration; owned fault containment retains resources for reset. A fixed read
count does not promise a wall-clock timeout on a stalled bus transaction.

Each of two passes reads **ISR, semaphore, mailbox4, mailbox5, ISR, semaphore**.
There are exactly twelve volatile halfword loads; no retries or chip writes.
The decoder preserves both passes, checks width/envelope, reports stability,
requires all status words zero for `status_zero`, and compares chip indices to
both relevant software producer/consumer values. Changes and nonzero statuses
remain observations, not acceptance failures or proof of ownership. The complete
RAM/config/chip sequence is not atomic. No worker-side cache flush was added.

## Report and validation

The existing report and extensions remain unchanged. Words 384..415 contain
`QCP1, version=1, nonce, sequence, phase, result, read_count, reserved`, twelve
zero-extended register values, then twelve reserved zeros. Result 1 means a
refused prerequisite; result 0 and count 12 mean all reads returned. Shared ack
166 publishes last. Worker 0 captures ready/frame32/idle; Init captures final
STOP. Diagnostic injection remains limited to profiles 1..4 and 6..13.

Native tests exercise exact addresses/order, all nine prerequisite refusals,
report boundaries, malformed records, changing indices and nonzero semaphore.
Mac and Linux sanitizer suites run the existing containment tests too. The
actual i960 exception object must match normal profile 5 byte-for-byte; the
compiled chip access is `ldos`, not a dword load. Source/binary identities and
full captures accompany replayable live/STOP/recovery verification.

Hardware results and restored-session details are recorded in
[the artifact report](../../../artifacts/current/accele160-qlogic-chip-20261019/README.md).

All four physical samples resolve the cached-index discrepancy: chip request
consumer 37 equals software producer 37, while cached consumer is 0. Response
producer/consumer are 22. Both chip passes report `(ISR, SEMA, MBOX4, MBOX5,
ISR, SEMA) = (0, 2, 37, 22, 0, 2)`. FreeBSD names semaphore bit `0x0002`
STATUS and bit `0x0001` LOCK; the observed lock bit is clear. The decoder's
conservative `status_zero` is therefore false, despite ISR zero. Neither equal
indices nor a clear lock bit proves all mailbox, SXP or DMA activity stopped.

## Physical acceptance and restoration

Test session `20261019T105126Z`, boot `91c44f87-bf3e-4d82-a94a-9731e978ba81`, kernel
`8a428f6cf3b83569f39c1e3adf3274f2782f00290a83653bdab404ba8aca494e` passed 64 frames, 5045 WAD reads and
709 external console exchanges with no errors. Maximum observed console reply
latency was 3249.679 ms (an observation, not a bound). All four phases/eight
passes agree. Owned tables/stacks/guards and stable report rereads passed. Final
STOP acknowledged QUIE/ACK and retained the pending callback and DMA pins with
no guard changes. No chip register or PCI device configuration was written.

The restored profile-5 session is `20261019T105649Z`, on fresh boot
`417ae821-f1d1-4305-9e91-614598e4a5cb`. Paired full flash reads match the accepted SHA,
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
Normal kernel `55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002` passed
64 frames, 5045 WAD reads and 713 external exchanges. Prompt idle,
zero zone loan and HTTP 200 on gateway 8088 were checked. Leave this owner running.
