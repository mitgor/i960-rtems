# AcceleRAID RTEMS service baseline and command prompt

Work date: 2026-10-18. P1/P2 use an opt-in service-enabled reusable Doom
kernel. No firmware was programmed and no RAM ownership was expanded.
[Source, protocol, bounds and command access](../../../rtems/accele160/service/README.md).

## Closed pre-reset kernel test

On boot `f7ddb4e1-7115-44ef-958d-ab86cb2f3ee7`, the AcceleRAID at
`0000:37:09.1` ran two fresh Doom games, each with 64 frames. Both per-game
idle audits, the intermediate image reload, stale rearm rejection and global
STOP passed. The prior CHIP-8 session had first shut down normally; its
result is retained here as `previous-chip8-shutdown.json`.

The kernel is SHA-256
`e19f3e9435e971a663591ad27e92e9a4ad886fb289307dda2f5c4f94ba675635`.
The admission image is
`690a3d311e327183b427a4bc9d1a2101a522a35747a9e8a4691e5287644cd2ee`.
It fits the unchanged executable/IRQ/entry-stack limits. A matched source
build with service disabled has 38,976 text bytes; enabled has 41,216.
The service adds 16 bytes of ordinary BSS and explicitly reserves a 4 KiB
NOLOAD mailbox in the existing 512 KiB grant. The disabled comparison was
built, not executed as a new matched performance benchmark.

Independent replay checks:

- All 128 guarded DMA captures, markers and native-host hashes; 64 paired PIO
  frames. Both games' 64 pixel/palette frames are byte-identical to each other.
- All 10,090 engine WAD reads against the pinned Freedoom bytes and native
  startup request sequence. Existing full ownership/cache/heap/IRQ audits remain.
- Three card console self-test gates (before admission and after each game),
  including all seven commands, duplicates, wrong epoch, sequence gap, length,
  opcode and reserved-word rejection. The follow-up host gate additionally
  exercises a specifically older sequence.
- 172 real host console replies, including live task, memory and application
  values while loading/rendering. Host-observed card reply latency: median
  3.278 ms, maximum 4,728.132 ms, minimum 0.412 ms. This includes host scheduling
  and work around reload/audits; it is not ISR latency or a hard real-time bound.
- Per-game no-live-zone state and balanced engine IRQ lifetime; retained fixed
  allocations and DMA buffers; global STOP acknowledgement and terminal QUIE.
- Deliberately changed DMA guards/data/markers and console sequence/epoch/
  length/magic/text are rejected by replay.

`acceptance-1.tar.xz` is SHA-256
`2c7c14fd506ced7a60bfc7760cdd12ce586ffa8b7c61b32577333d1c1e2b0453`.
It contains exact kernel/engine/host source and binaries, matching baseline
build, modules/firmware, bundle identities, both pre-run flash reads, full
captures, the console journal and host logs. Freedoom bytes are referenced
from the existing `artifacts/doom-m1-20261011/freedoom-0.13.0.zip` instead of
being duplicated. The separate `post-0`/`post-1` records now close its reset checks: both
guarded 1 MiB reads match the firmware above on fresh boot
`97e816ae-5c7f-467e-a59a-4235ef11c519`, with zero status, residual and guard changes.

## Host issues found and correction

The first external malformed-input test found a Unix socket close issue:
a 129-character line plus newline left an unread byte when the daemon closed,
so the client could see connection reset instead of a clean error/EOF. The
owner and RTEMS stayed healthy. The corrected host half-closes its response
and drains/discards input in bounded pieces until EOF or the existing timeout.
The native test now includes the exact 130-byte wire input and verifies EOF.

The initial endpoint was also visible during card startup before the owner
could pump it. The corrected endpoint is published only after card protocol
self-tests. Host console pumping now occurs between audit-page reads, with
an explicit recursion guard and a self-test exclusion/drain gate. Full audits
are preserved. These host corrections do not change the accepted kernel.

Native protocol tests run under ASan/UBSan. Host tests exercise malformed and
oversized commands, partial disconnects, queue limits, reconnects, bad replies,
startup publication and timeout quarantine without retry. Existing browser,
rearm, keyboard producer and 32-bit DMA policy tests also passed on Linux.

## Status and limits

P1/P2 diagnostic service acceptance is complete. The fresh-boot follow-up passed
with the corrected host and byte-identical kernel. The isolated service is left
running in audited reusable idle; run `./rtems-console` from the Mac repository.
The ordinary Doom/CHIP-8 installed bundles were not promoted. The first run's
global STOP and paired post-reset checks are closed; the live follow-up's eventual
global shutdown/reset remain separate, and retained resources must stay owned.

This is a read-only diagnostic interpreter, not Bash, the full RTEMS shell,
networking, arbitrary task control, an independent watchdog or measured maximum
IRQ-gap qualification. `mem` reports fixed capacities and a zone-loan flag,
not general free-heap statistics. Global STOP still retains resources until
reset; a client disconnect cannot adopt or free the card session.

Replay:

```sh
python3 artifacts/current/accele160-service-20261018/verify.py
```

## Completed recovery and corrected-host follow-up

Fresh boot `97e816ae-5c7f-467e-a59a-4235ef11c519` had no active service or
retained DMA/admission driver. The corrected sources were overlaid only into
`/home/mit/i960-service-20261018/bundle`, with manifest and bundle identities
regenerated. No kernel rebuild or firmware write was needed. The original
`acceptance-1.tar.xz` remains unchanged.

Session `20261018T191527Z` used port 8087, 64 frames, 32 paired PIO frames,
full captures, and unlimited reusable idle (`--restart-cycles 0`). Its two
prechecks also supply `post-0`/`post-1` for the earlier acceptance run.

The 160-second external client test completed 809 exchanges with no client
errors. It covered all seven commands, unknown and oversized lines, abandoned
partial/full requests, eight slow clients, expiry and reconnects, through
loading, rendering and idle. The exact 130-byte oversized wire input returned
`error: command too long` followed by clean EOF. Two full card protocol gates
passed, including explicit older-sequence rejection. The journal contains 810
card replies: the external test's valid requests, an abandoned complete request,
and two additional manual diagnostic requests. Host-rejected commands do not
become card requests.

Independent replay validates all 64 guarded DMA frames, 32 paired PIO flags,
5,045 WAD reads, native startup order, exact pixel/palette agreement with the
first acceptance, and the per-game idle/heap/IRQ/DMA receipts. Host-observed
reply latency was median **15.547 ms**, maximum **2,559.823 ms**, minimum
0.687 ms. This workload includes the idle loop's polling cadence and startup
work; it is not a controlled performance comparison or an interrupt bound.

`followup.tar.xz` (SHA-256
`fea950cf4c46938aae4ebee6969b7175df0eb86a85434ff334e535b0e9bc4d1e`)
contains the corrected exact bundle, complete new session, external client
results and service log. It omits the same already archived Freedoom WAD.
All 237 included bundle file hashes verify. It is a snapshot of a still-running
idle owner, not a global STOP receipt. `final-access.txt` separately records
successful access through the repository wrapper after archiving, `apps` idle,
advancing uptime availability, the active service and boot identity.

```sh
python3 artifacts/current/accele160-service-20261018/verify_followup.py
./rtems-console
```

Leave the single owner and retained modules intact. After a future shutdown or
reset, use the documented isolated launcher and its full readback/admission
gates; the console client never starts or adopts a hardware session itself.

## Repository inventory check

The batch's own staged blobs and SHA-256 manifest were verified. The repository-
wide `host/audit/artifacts.py --tracked-only --index-bytes` command rejects an
existing mode-120000 entry at
`artifacts/current/accele160-flat-20261018/post-0/data.bin`, before inspecting
this batch. That unrelated symlink was left unchanged. The global inventory
was extended only with this batch's staged regular files, preserving existing
entries; full-repository audit success is not claimed.
