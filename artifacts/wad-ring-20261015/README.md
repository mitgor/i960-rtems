# Pipelined WAD loading — 2026-10-15

Status: bounded physical acceptance passed. Startup improves, warm restart
regresses, and the ring remains opt-in. All closed archives have passed local replay, and public IPv6 HTTP is restored.

## Candidate

`--wad-ring` is opt-in and requires the bounded Doom ping-pong DMA profile.
Two retained 40 KiB coherent host slots each contain a 32 KiB payload and
independent request, response and completion records. A 64 KiB aligned cache
miss publishes up to two requests before consuming either response. The host
serves immutable WAD bytes through RAM-only ioctls; per-block mailbox metadata,
submit and ACK exchanges are eliminated. DMA1 remains task-owned and serialized
with framebuffer DMA. No firmware or memory-map change.

All existing full system/RAM audits remain at the three-second requested cadence.
Generation, geometry, guards, descriptor identity, DMA quiescence, borrow/return,
STOP and timeout checks remain. Payload CRC stays off. Source bytes and all ring
records are saved for independent replay. The final completion of both slots is
explicitly captured, not inferred from a later reuse. Host mappings remain
pinned until reboot. A stopped/timed-out ring cannot silently resume a partially
completed batch. Uncertain DMA faults quarantine allocations.

A response read may straddle host publication: after observing the committed
generation, the card rereads the immutable response before validating it.
Request/completion commit words are separate final DMA writes. No consumer may
accept a partially written record.

## Native findings

- Actual ring target tests: two slots, reuse, EOF, active isolation, all 256
  descriptor bit mutations, stale geometry, hardware timeout quarantine,
  five-second stalled-host timeout and STOP during the host wait.
- Actual host ioctl tests: RAM-only service after registration, prior completion
  required before reuse, guard corruption, stale geometry, registration faults
  and copyout uncertainty with mappings retained.
- Actual Python client and independent replay reject 97 damaged-evidence cases.
- Cache sanitizer tests check 30,000 reads across 512-byte, 4 KiB and 64 KiB
  modes, including conflicts, adjacent hits, multi-window reads and EOF.
- Actual native Doom runs: 120 matching frame hashes between old and read-ahead
  APIs, interactive input, repeat determinism, STOP and complete heap drain.
- In the first native 40-frame input run, API reads fall **5,045 → 878**.
  Bytes fetched rise **15,024,836 → 57,499,844** due to read-ahead; this is a real
  tradeoff, not a raw-bandwidth improvement. Each 64 KiB API read normally
  becomes two 32 KiB ring requests; do not equate these two request counts.
- Native heap peak including an extra modeled 41,216-byte staging allocation:
  **6,646,255 → 6,798,063 bytes**, +151,808 bytes. The separate admitted-image
  reservation and other arena occupants still require the full ownership audit.
- Code remains inside existing protected windows. The protection table grows
  from 145 to 146 pages; tests mutate each protected page. No bounds are widened.

Remote workspace: `/home/mit/i960-wad-ring-20261015`.
The public relay was stopped normally and released its module before testing.
The following sections record the physical results, exact final hashes, matched
comparison, independent replay and final restoration status.

## Initial physical candidate: byte-oriented staging

The initial candidate completed 100 frames, **162 full audit pairs**, level
restart, both-framebuffer-slot stall/resume, held-buffer STOP and global drain.
All 1,805 WAD generations have exact source bytes and final completion evidence.
The first 52 frames retain exactly the four known native/card pixel differences;
all palettes match. The Mac observed 98 of 100 HTTP frames; every observed payload
matches its card capture. The browser displayed the game; its saved screenshot
was taken just after the bounded server closed, hence its “Failed to fetch” text.

First frame after engine preparation: **456.109 seconds**. This is slower than
the prior approximately 291-second 4 KiB bulk path. Successful ring ioctls total
only **0.823 seconds**; that figure excludes unsuccessful polls and Python work,
and must not be presented as total transport time. Read-ahead increases payload
traffic to **59,146,240 DMA bytes** across startup, play and warm restart.

The next candidate changes guard scans, staging clear/fill and staging copies to
aligned word operations. It checks every guard byte at exactly the same points;
no guard scan, full audit or ownership test is removed. Native tests additionally
flip every one of the 8,192 guard bytes and exercise copy alignments/tails.

`candidate-byte-v1.tar.gz` and `card-byte-v1.tar.gz` contain the exact initial
sources, kernel/module/engine, native oracle and complete captures. Hashes are in
`byte-archives.sha256`. System/frame/WAD replays pass on Linux and the Mac;
frame evidence tamper tests also pass. These files preserve a successful safety
qualification with a performance regression, not a claimed optimization win.
Normal reboot was requested only after the archives were verified and replayed
locally, to release the retained mappings for the word-oriented comparison.

## Matched physical comparison

The final word ring and 4 KiB bulk baseline use the **same kernel, module and
admitted engine**, the same WAD, low-detail scene, frame pipeline, controls and
full audit policy. Only `--wad-ring` differs. Each runs in a fresh boot. The
sequence was initial byte ring, optimized word ring, then matched bulk baseline;
this is one bounded run per profile, not a statistical or reversed-order study.

| Metric | Matched 4 KiB bulk | Word ring | Initial byte ring |
| --- | ---: | ---: | ---: |
| First frame after engine preparation | 290.0869 s | **186.5660 s** | 456.1091 s |
| Engine upload, measured separately | 80.4957 s | 80.5819 s | 79.5711 s |
| First-frame transfer requests | 5,043 | 1,755 | 1,755 |
| Warm restart, frame 66 → 68 | **2.8419 s** | 4.2415 s | 10.2032 s |
| Requests in that restart interval | 32 | 38 | 38 |
| Full paired audits | 108 | 88 | 162 |
| Delivered frames | 100 | 100 | 100 |
| Fixed-scene delivery FPS, frames 21 → 50 | 3.8375 | 3.9484 | 3.8233 |

Startup improves **35.69%**, or **1.555×**. This excludes approximately 80 seconds
of engine upload and earlier RTEMS/network setup; it includes Doom initialization
and first-frame work, not just DMA. Warm restart is **49.25% slower**. The same
first level is reloaded; this is not a measurement of arbitrary later maps.
The restart window includes two delivered frames and game initialization.

The modest FPS difference is a short-run observation, not proof of a sustained
renderer improvement. No intervals were trimmed. All 52 controlled frames
before asynchronous menu activity have identical pixels/palettes across all
three card runs, and retain exactly the four known differences from the native
oracle. All 100 frames in each run pass transport, ownership and STOP replay.
There are **358 full paired audits and 300 delivered frames** in total.

Both ring runs complete **1,805 transfers / 59,146,240 DMA payload bytes**, versus
**5,100 / 20,889,600 bytes** in the bulk baseline. Speculative 64 KiB fills cause
more copying and rereads. This explains why the new path is useful for startup
but is not an unconditional replacement. Word-ring successful ioctls total
0.159 seconds; 96,289 pending polls total 3.715 seconds in the kernel call.
These exclude Python processing and card execution and are not end-to-end time.
The matched baseline spent **180.606 seconds in 12,361 WAD metadata queries**.
The ring eliminates those mailbox queries, but its extra card-side work means
that the full startup gain is smaller than that saved query time.
See `comparison-summary.json` for the exact accounting.

The final candidate preserves full scans at the same points and adds a complete
post-transfer descriptor check. Native tests cover a response fetch straddling
publication, corrupted EOF padding, descriptor corruption after completion,
all 8,192 guard-byte mutations, alignment/tail copies, STOP while waiting and
hardware timeout quarantine. Physical WAD-host stall/timeout injection remains
future work; the physical stalled-host tests here hold **framebuffer** slots.
No new physical active-WAD-lease overlap count is claimed.

Final binary identities:

- Kernel: `6cd2af58964a52a618f9d27c191b7ef1c44cc5be8c116f381eb7660be04edb64`
- Module: `e24d0abf5e1dddba714a705d52d2480be62d78f3977d3c52b0436133d5c21419`
- Engine: `f0866827e8d40471df376dfcad668a8c6c52d8ec311386ba41c9dda859035a2e`

`candidate-word-v2.tar.gz` has exact final source/binaries; `card-word-v2.tar.gz`
and `card-baseline-v2.tar.gz` preserve the successful matched captures. Archive
SHA-256 lists are separate files. `replay.sh` runs the system, frame and WAD
verifiers plus the independent native comparison. `local-*.json` records Mac
verification. `http-verification.json` checks every observed HTTP payload; browser
receipt is not browser paint time. The browser screenshots show actual card
output. The bounded server closes after STOP; it is not left running for play.

## Next optimization and limits

Keep `--wad-ring` explicit and retain the 4 KiB fallback. The next useful change
is **adaptive, smaller read-ahead for small/repeated level reads**, with variable
bounded ring payload lengths. Merely enlarging the cache is unlikely to fix the
warm-restart regression: replaying the observed full-window miss stream with
four direct-mapped windows predicts 18 restart windows instead of 19, while
costing another 192 KiB of cache RAM. This is a trace-based estimate, not another
physical cache benchmark; `cache_trace.py` reproduces this estimate.

Long interactive sessions, physical WAD timeout injection, a general unaligned
read API and other i960 cards are not qualified by this batch. Full audits,
generation ownership, quiescence and replay remain required for follow-ups.

## Final service state

All five archives were copied, SHA-256 verified and replayed on the Mac before
normal reboot released their retained DMA mappings. Public IPv6 HTTP is restored
and returned **200 / 2,891 bytes** containing RTEMS output from the Mac.
Boot `cf670f3e-d97f-4bf3-8649-04e1fc937e49`; supervisor **2721**, relay **2723**
owns `dac960auto`. The bounded Doom server is closed. See `restoration.json` and
`restore.sh`. Inspect actual ownership before future card work; stop the public
relay normally and never force-unload retained resources.

The Mac observed 98 byte-ring, 98 word-ring and 99 baseline HTTP frames; every
observed payload matches its card capture. Frame drops at the observer are not
silently filled in. All 300 card captures pass their complete transport replay.
Each physical capture rejects 24 frame-journal mutations. The word ring also
rejects three mutations of its actual WAD evidence; the synthetic client/replay
suite rejects 97 cases. `accepted-source-check.json` verifies that the current
runtime/build files exactly match the accepted word-source archive.
