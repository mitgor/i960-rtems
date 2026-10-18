# AcceleRAID RTEMS diagnostic service (P1/P2)

This opt-in candidate extends the existing persistent/reusable Doom kernel.
Physical acceptance status and exact binaries belong in
[the dated evidence ledger](../../../artifacts/current/accele160-service-20261018/README.md).
The corrected isolated service passed its physical follow-up and was left in
audited idle on 2026-10-18. Use the access command below while that owner is
running. The ordinary installed Doom/CHIP-8 bundles do not contain this code.

## Access

On a running **service-enabled** owner, run `./rtems-console` from the Mac
repository. The equivalent explicit command is:

```sh
ssh -t mit@192.168.2.75 'sudo python3 /home/mit/i960-service-20261018/bundle/project/rtems/accele160/service/console.py'
```

The prompt supports `help`, `version`, `uptime`, `tasks`, `mem`, `apps`, and
`stats`. `quit`/Ctrl-D disconnects only the client. A one-shot command is:

```sh
ssh mit@192.168.2.75 'sudo python3 /home/mit/i960-service-20261018/bundle/project/rtems/accele160/service/console.py uptime'
```

This is card-produced diagnostic text, transported by the owning Linux daemon.
It is not a Linux shell, a standard RTEMS shell, or arbitrary memory access.
The client opens only a mode-0600 Unix socket. No direct PCI session, extra
mapping, DMA descriptor, card reset or firmware call is issued by the client.
`mem` reports fixed workspace/arena capacity and the zone-loan flag; it does
not claim allocator free-space statistics or walk live heap metadata.

## Baseline and ownership

Build `doom_dma/build.sh` with `ACCELE_SERVICE=1`, `DOOM_PERSISTENT=1`,
`DOOM_REUSABLE=1`, `DOOM_FPS_FRAMES=32`, and the selected keyboard/cache options.
Generate the exact runtime manifest with `doom_dma/write_manifest.py`.
Its service schema pins protocol, card adapter and host transport sources.
Default builds leave service support disabled.

The kernel/entry/IRQ stacks retain their accepted placement. The RTEMS
workspace is `c0730000..c0760000`, full-bank scratch is
`c0760000..c0763000`, and interrupted-PC samples start at `c0772000`.
The service reserves **one page at `c0775000..c0776000`**, inside the already
owned 512 KiB grant and outside these ranges. A linker NOLOAD reservation
keeps the existing 29-page admission image format. Host access uses the odd
aperture with selector `c0774000`; upload and reply pages remain `c078b000`
and `c078d000`, staging `c078f000`. No upper-bank RAM grant changes.

Existing worker 0 handles the console in task context using its existing
stack/IRQ continuation. It returns immediately if no new request exists. It
never traverses heap metadata, accesses side-effecting registers, masks IRQs,
or launches/deletes tasks. Snapshots are observational scalar values; they
are not an atomic global scheduler/heap census. Global STOP still drains the
same workers and IRQ owners. Engine idle/rearm retains the same service epoch.

## SVC1 wire format and bounds

One outstanding request. The supervisor initializes a random nonzero 32-bit
session epoch before admission; the card latches it and clears the mailbox.
The grant is uncached in the accepted map. The host publishes request sequence
last; the card executes `syncf` and publishes reply ACK last.

| Word | Writer | Meaning |
| --- | --- | --- |
| 0 | Host | Request sequence, nonzero, monotonically increasing |
| 1–4 | Host | Version 1, session epoch, opcode 1–7, payload length (must be zero) |
| 5–15 | Host | Reserved, must be zero |
| 16–20 | Card | ACK sequence, status, echoed epoch, output byte count, sampled tick |
| 21–24 | Card | Accepted/rejected counts, consumed sequence, SVC1 magic |
| 32 onward | Card | At most 768 ASCII output bytes; one complete bounded chunk |

Status 1 rejects version/epoch, 2 sequence, 3 length/reserved, 4 opcode.
Duplicate current sequence preserves its response and counters. An invalid
request with the correct next sequence/version/epoch consumes that sequence;
wrong epoch or out-of-order sequence does not. Sequence exhaustion refuses
reuse. Epoch is a stale-session guard, not cryptographic authentication.

The host accepts at most eight clients, 128 input bytes/client and one bounded
reply each. Incomplete/slow clients expire after five seconds. The owner
thread alone pumps PCI requests among normal frame/WAD/idle work; socket clients
cannot move the aperture selector. Unknown commands and excessive input are
rejected before touching the card. An uncertain/malformed card reply disables
the console without retrying the write or releasing hardware resources.
Final owner shutdown closes the socket; a new client cannot adopt its pins.

## Verification

```sh
cc -Wall -Wextra -Werror -fsanitize=address,undefined \
  rtems/accele160/service/test_protocol.c -o /tmp/service-test
/tmp/service-test
python3 rtems/accele160/service/test_host.py
python3 rtems/accele160/service/test_pump.py
python3 rtems/accele160/service/verify.py PATH_TO_CAPTURE/console.jsonl
```

The physical owner self-test runs all seven commands and duplicates, bad epoch,
sequence, length, reserved words and opcode before engine admission and at each
verified game-idle boundary. It saves full raw replies. The external SSH client
exercise tests real commands, malformed/oversized input, abandoned connections,
slow clients and reconnects during application activity. Existing complete
frame/WAD/owner/cache/STOP and post-reset stock-flash gates remain required.
No independent watchdog or maximum hardware IRQ-gap claim follows from this
prompt. Record host command latency separately from RTEMS ticks and frame rate.
