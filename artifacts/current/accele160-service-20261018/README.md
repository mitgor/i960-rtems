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
being duplicated. Nothing in the archive is a substitute for pending reset checks.

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

At this checkpoint the first physical kernel test and replay passed; the host
corrections still require their follow-up physical test. The PC refused SSH
after the acceptance reset. Post-reset flash checks and installation of the
corrected live prompt are pending recovery. Do not advertise the prompt as
currently available on the basis of the first archive alone.

This is a read-only diagnostic interpreter, not Bash, the full RTEMS shell,
networking, arbitrary task control, an independent watchdog or measured maximum
IRQ-gap qualification. `mem` reports fixed capacities and a zone-loan flag,
not general free-heap statistics. Global STOP still retains resources until
reset; a client disconnect cannot adopt or free the card session.

Replay:

```sh
python3 artifacts/current/accele160-service-20261018/verify.py
```

## Resume after recovery

1. Verify a fresh boot and no existing driver session/daemon owner. The isolated
   remote workspace is `/home/mit/i960-service-20261018`; `acceptance-1.tar.xz`
   preserves the original first-run bundle even after its working copy changes.
2. Overlay the corrected repository `service/` files and `doom_dma/run_bridge.py`
   onto that bundle's project. The card kernel remains byte-identical to the
   SHA above. Regenerate `persistent-manifest.json` with `write_manifest.py`,
   then regenerate the explicit bundle file hashes. Do not silently modify an
   installed ordinary Doom or CHIP-8 bundle.
3. Use the existing launcher with this bundle, `--max-frames 64`,
   `--restart-cycles 0`, `--paired-frames 32`, `--capture-all`, and port 8087.
   Its two fresh guarded READIMAGE prechecks also provide the pending post-reset
   pair for the first run; copy those to this ledger's `post-0`/`post-1`.
4. Run `service/accept_client.py` over SSH through loading/rendering and idle,
   preserving all replies/errors. Verify oversized-line error/EOF, disconnects,
   slow clients, actual older-sequence rejection and renewed prompt access.
   Exercise another game through the existing owner if needed. Record revised
   latency rather than assuming page-group pumping removes target-side waits.
5. Archive and replay that follow-up separately. Leave the corrected prompt
   available in audited reusable idle if all gates pass; document that this
   still-running session's eventual global shutdown/post-reset pair is separate.
   If it fails, retain resources and evidence rather than adopting or unloading
   the uncertain owner. Update all pending status notes only from new evidence.

## Repository inventory check

The batch's own staged blobs and SHA-256 manifest were verified. The repository-
wide `host/audit/artifacts.py --tracked-only --index-bytes` command rejects an
existing mode-120000 entry at
`artifacts/current/accele160-flat-20261018/post-0/data.bin`, before inspecting
this batch. That unrelated symlink was left unchanged. The global inventory
was extended only with this batch's staged regular files, preserving existing
entries; full-repository audit success is not claimed.
