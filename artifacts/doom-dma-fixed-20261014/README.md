# Doom DMA comparison after the isolation fix — 2026-10-14

Status: fixed physical comparison accepted. All full audits, STOP and global
drain passed; DMA remains opt-in pending longer interactive acceptance.

This repeats the finite 28-frame Doom comparison using the ownership-aware
isolation fix accepted by the [512-frame stress test](../frame-dma-stress-20261014/README.md).
The admitted engine, WAD, scripted inputs, full audits and timing protocol are
unchanged. DMA remains opt-in.

## Reproduction and exact inputs

Remote workspace: `/home/mit/i960-doom-dma-fixed-20261014`.
Source baseline: `c0fae35`; no new runtime changes in this experiment.
`build.sh` rebuilds the RTEMS image and Linux transport, checks the RAM layout
and generated counter allowlist, and runs two deterministic native 28-frame
Doom instances. `live.sh` runs the finite physical comparison. The engine is
copied unchanged from the earlier accepted admission directory.

- Kernel SHA-256: `6b90e9787ccb4b8360b8c0fc77a83cd76018d1cd8b9a5f1f98223d5ab9580013`
- Module SHA-256: `a96d64a7a086105bee9c61f14bb1d5416ffdebde800eed1cd648d82d4ad35d57`
- Engine SHA-256: `9f2472c900bb724e7a69b2490e083c4c633520e1d525623398db2e36f2c1e173`
- Boot: `5ae888c7-143b-400b-80ea-5e2a24392de6`; supervisor 10752, Python 10754.

## Protocol

Frames 1–4 use both transports and require identical full buffers. Frames 5–10
use mailbox, 11–16 DMA, 17–22 DMA and 23–28 mailbox. Forward input at frame 2
and release at frame 4 match the native oracle. Every DMA capture includes the
complete 73,728-byte destination, both guards, source CRC, report/generation
checks and first-window reread. Full monitor/RAM audits run every 60 seconds
and at lifecycle boundaries. Owned STOP and global drain must pass.

`close_capture.sh` requires successful termination, runs independent system and
DMA replays, capture tamper checks, previous-card/native comparisons and command
cost analysis, then archives exact sources, binaries and evidence. Local hash
verification and full replay precede the recovery reboot; retained exclusive
resources must never be force-unloaded.

`observe_http.py` reads status and PNGs from the Mac without sending controls.
`http_summary.py` verifies received PNG hashes against named capture files.
Its timings measure HTTP receipt with 250 ms polling, not browser paint FPS.
Known native/card rendering differences remain explicitly measured; matching
previous physical buffers distinguishes those from transport corruption.

## Measured result

| Metric | Mailbox | DMA |
| --- | ---: | ---: |
| Delivered FPS | 0.972816 | 1.376781 |
| Mean transfer | 503.489 ms | 228.797 ms |
| First six-frame block | 0.943832 FPS | 1.381332 FPS |
| Second six-frame block | 1.003636 FPS | 1.372259 FPS |

DMA increased delivered FPS by **41.525%** and made the measured transfer
**2.2006× faster**. Each six-frame block uses five intervals; pooled FPS uses
only within-block intervals, excluding paired comparisons and block boundaries.
These are bounded, scripted scene measurements, not general gameplay or browser
paint-rate claims. Mean PNG encoding took 43.087 ms.

All 28 frames passed, with four byte-exact mailbox/DMA pairs, sixteen complete
guarded DMA captures (1,179,648 bytes including guards), 1,040 mailbox reads,
three malformed/stale refusals, planned input/ACK order, owned STOP and global
heap drain. All **29 full monitor/RAM audit pairs** passed, including post-DMA
and terminal snapshots. No timeout occurred; no checks or timeout bounds changed.
The twenty-eight buffers match the previous physical mailbox capture exactly.
Native runs are deterministic; the previously recorded 6–8 differing pixels
per frame remain unchanged, as do all padding bytes. This is not a claim of
bit-identical native/card rendering.

The Mac observer fetched all 28 PNGs with matching hashes, averaging 64.463 ms
per fetch. HTTP receipt block rates were 0.8994 / 1.4611 / 1.4460 / 1.0256 FPS.
Polling quantization affects these short blocks; use server delivery timings
above for the FPS comparison. No browser paint measurement was made.

Command costs are separate from wall-clock capture time: DMA submit averaged
0.991 ms; 720 pending polls averaged 3.197 ms; sixteen final reports averaged
9.877 ms; 1,168 coherent-buffer reads averaged 0.01134 ms. Mailbox reads averaged
7.506 ms. These figures include ioctl service, not only bus transfer, and do not
remove CRC, guard, generation or first-window checks from the benchmark.

## Evidence and validation

- `build-evidence.tar.gz` SHA-256:
  `e952ec8c797f841d2a824d2424c3feeebfebf4c8d177bdf7f6b604aeb01bf9d4`
- `card-evidence.tar.gz` SHA-256:
  `429f6cd80c05f92328f07034ba6ae31c641409572d1dbfb1b2a704210905c5ae`

Both archives were copied, hash-verified, extracted and fully replayed locally
before reboot. Full system and DMA replay passed on Linux and macOS. Thirty
frame/journal corruptions and twenty-four snapshot corruptions were rejected
on both hosts. Standalone JSON files retain measurements, command costs,
HTTP observations and both replay results. `frame-28.png` is a captured card
frame, not a screenshot of a browser. Native output and exact source/build
outputs are preserved in the build archive. Existing source/newlib dependencies
remain pinned through the earlier artifact set; the project artifact link is
archived as a symlink, not recursively duplicated.

## Scope and next step

This applies the reproduced peer-heap isolation fix to real Doom successfully;
it does not by itself establish long-session or every-scene reliability. The
512-frame synthetic stress acceptance and this 28-frame Doom acceptance are
complementary. No new runtime change or firmware reflash was required here.
Keep the default mailbox path and opt-in DMA until longer interactive input,
STOP/disconnect, and mapping lifecycle acceptance are complete. Initial WAD
startup remains roughly 23 minutes and is a separate bottleneck.

## Restoration

After local replay, reboot released the retained exclusive mapping. Public IPv6
HTTP returned 200 from the Mac with the RTEMS page, and relay IPv4/IPv6 startup
checks passed. Final owner is public relay supervisor 2120 / Python 2122,
boot `36938147-8109-4114-b7c8-9dc9dcdaf09d`, bound `dac960auto`.
See `restoration.json` and compressed HTTP evidence. The finite Doom endpoint
is closed; the public web service is restored. Stop its relay normally before
new card work; never force-unload retained exclusive resources.
