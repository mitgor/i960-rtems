# Interactive browser Doom and repository organization — 2026-10-13

Status: corrected six-frame movement/STOP run passed on the card. A fresh
interactive session is loading for the user. The preliminary run is not playable
acceptance.
The accepted two-frame baseline remains
[doom-visible-20261013](../doom-visible-20261013/README.md).

## Scope

The user's priority changed to playing Doom now and debugging/optimizing from
actual use. The opt-in interactive build retains the real Doom engine and
private libc state across frames, starts Freedoom Phase 1 E1M1 at skill 3, polls
browser keys through its owned API, and publishes a stable 320×200 indexed
frame. It blocks until readback/ACK. No repeated startup per frame, arbitrary
address access, flash write, additional RAM grant or replacement renderer.

Normal mode keeps paired snapshot/RAM checks at startup and every 60 seconds;
`--audit-interval 3` restores frequent checks. Identity, ownership, bounds,
guards, epoch and uncertainty behavior remain enforced. Verbose per-event
checkpoint/native replay is retained in the separate accepted test profile.
Interactive frames are not claimed to match a fixed prerecorded demo.

See [controls and build/run guide](../../game/doom/play/README.md).
`build.sh` and `live.sh` describe the corrected isolated lab workspace
`/home/mit/i960-doom-play-20261013b`; the earlier workspace without `b` is the
preserved preliminary run. The newer convenience `build.py` / `run.py` removes
the need to reconstruct old lab paths, but is separate from those exact scripts.

## Native and channel verification

The actual sanitized 32-bit DoomGeneric/private Newlib engine ran 40 frames
with held forward/release input, repeated deterministically, and ran without
input. Input changes the rendered trace. The two input runs each produced
39 distinct frame hashes, returned through owned STOP and fully drained the
8 MiB arena. Peak heap use was 6,646,255 bytes including the checkpoint allocation;
private engine allocation peak was 6,445,535 bytes. The target continues to use
a separately admitted image within the 900,000-byte reservation.

The actual frame-channel code passed synthetic host/clock tests for immutable
readback, wrong generation, bounds, stale ACK, all 31 usable key queue entries,
queue overflow, STOP, timeout and final release. The existing 258-exchange
frame ioctl and uncertainty injection tests and checkpoint-barrier tests passed.

## Preliminary card run: evidence and limits

Boot `083c2956-4f85-49e6-abb9-3d485c4d7422`. The previous public IPv6 relay
(Python 1843) was terminated normally; its summary confirmed restoration,
unload and no bound driver before the new session. No force unload occurred.

The first interactive candidate passed initial paired checks and entered Doom
startup. Browser STOP while loading returned exit 210 and fully retired the
owned image with zero presented frames. The host then began its automatic
repeat. A second STOP exposed a host race: after requesting cancellation,
the host still attempted a WAD reply, which the cancelled runtime rejected
with EAGAIN. Captures were retained, copied and hash-checked before reboot.
No visible frame or movement acceptance is claimed for this preliminary batch.
Its log's automatic `Input/STOP test passed` wording was too broad for a manually
stopped zero-frame run; the session result is the authoritative evidence.

The corrected host stops all WAD/frame/input traffic after owned STOP and only
polls completion. Requests made during upload wait until entry has serviced its
first WAD request, avoiding cancellation before owned binding. Other fixes:

- Play time receives a new 30-minute deadline at the first frame; loading has
  its own 30-minute allowance. Host completion allowance is 3,660 seconds.
- Menu Quit follows owned STOP. The private framebuffer accessor uses slot 0
  in the persistent build, regardless of total frame count.
- A disconnected browser's input heartbeat expires; held keys are released at
  the next frame. Host queue exhaustion requests STOP rather than dropping a
  release and leaving a key pressed.
- Finished network test traffic no longer causes endless empty packet polling.
- Saved options identify play mode, port, acceptance length and audit interval.

Preliminary identities (superseded candidate, preserved for diagnosis):

| Item | SHA-256 |
| --- | --- |
| Kernel | `1bc900a439b83079b2a9406c6df569618810341217b39505904d1841a55845a0` |
| Linux module | `d2ba3870e39f1ef4b303b70424b1cea062cfa4a2021e849e23cde1f05456208a` |
| Engine template | `5a12da48faf777c700bc2c90c7685016c7053545c76ea474e470fa24c4d223cd` |

`preliminary-build.tar.gz` preserves the candidate source, binaries and native
proofs; `preliminary-card.tar.gz` preserves the card run, journals, failure,
readbacks and kernel log. Adjacent checksum files were verified locally.
No visitor statistics are included.

## Repository layout

46 historical root documents moved physically to topic folders under `docs/`.
The root now keeps only five project-wide Markdown files. Live links and 61
links in 12 artifact navigation documents use canonical topic paths; captured
source trees and binary evidence were not rewritten. Of 1,434 relative links
checked, there were no new failures; 41 pre-existing missing links inside
partial historical snapshots remain unchanged. See
[the move ledger](../../docs/reorganization-20261013.md).

`subprojects/` provides firmware, loader, RTEMS, Tetris, Doom and web entrypoints.
The new root README and reproduction/research/porting guides replace obsolete
status claims. Sources remain in `loader/`, `host/`, `rtems/`, `game/` to preserve
existing import and build contracts. No duplicate source tree was created.
Only two ignored `.DS_Store` files were removed; the unclassified flash USB image
and all firmware/execution evidence were retained.

Tetris sources now live in `game/tetris/`, with six compatibility links for
existing build callers. Native ASan/UBSan tests passed through both Makefiles
with result 1161671136; both replay entrypoints verified the same nine saved
physical runs. Shared ABI/linker files have explicit relative links.

## Fresh-workspace reproduction

The new `game/doom/play/build.py` completed in a fresh Linux workspace, using
only preserved upstream inputs, a configured cross compiler and system build
dependencies. Native deterministic input/no-input, owned STOP/drain, ABI,
frame channel, transport uncertainty and checkpoint tests passed. This is a
build proof, separate from the physical candidate below. Doom assertion strings
include absolute build paths, making this admission 32 bytes larger; different
workspace identities are expected, not silently accepted as old hashes.

| Build | Kernel SHA-256 | Engine SHA-256 |
| --- | --- | --- |
| Corrected physical candidate | `5e9b6277038ebc96a8d4d2d5c788af98383a99c0dcdafcc70e0f55e0213841e8` | `9f2472c900bb724e7a69b2490e083c4c633520e1d525623398db2e36f2c1e173` |
| Fresh-workspace proof | `269e88528a5b0b2f7d2a4d494247bedaf1f2207f68b6cb626c8dd5af3e2d1099` | `d6699f82d6ad8590e1dcb415be4d0da0caf4b8cc8d607740e95d25d114c85fd9` |

The corrected admission uses 867,792 bytes, including 53,472 bytes of metadata;
the engine span is 814,320 bytes. The fresh build uses 867,824 bytes.
`build-evidence.tar.gz` preserves the corrected candidate and
`reproducibility.tar.gz` the independent wrapper proof. Both checksum files
were verified after copying to this repository.

Review identified two input limitations retained for this first play profile: short
press/release pairs can land in one game tick, so hold keys across a frame; Y/N
menu confirmation and weapon digits are unmapped, so use the page Stop button.
These are usability follow-ups, not evidence of faster or complete gameplay.

## Corrected physical movement and STOP

Boot `83ecfee3-b3a2-47bf-a415-2ce0b7d0602f`, supervisor 2999 / Python 3001,
exclusive `dac960auto`. Six 320×200 frames were fully read through the checked
window protocol and its repeated first-window check. Forward was pressed after
frame 2 and released after frame 4. Frames 1/2 match each other; frames 3–6
change visibly. The result reports six frames, private peak 6,445,487 bytes,
owned reason 2, STOP flag 1, exit 210, and successful image retirement. The
second upload then began normally; no EAGAIN cancellation race recurred.

First-frame delivery took 1,369.364 seconds from the engine session's start
(including its upload/loading). Readback averaged 5.473 seconds per complete
frame (range 5.436–5.550). Frame 1→6 delivery averaged **0.169 frames/s**, about
one frame every 5.92 seconds. This is experimental interaction, not smooth Doom.

The acceptance prefix has **26 complete snapshot/RAM pairs**, all passing,
and one dual-stack test round. The resident program is deliberately left alive
for the second session: no global shutdown, final heap drain, module unload or
public HTTP restoration is claimed for this still-active batch. The owned engine
STOP result is distinct from global resident shutdown.

A host-only six-frame comparison repeats exactly the card test's forward/release
schedule with the same engine/private runtime. All six palettes and padding match;
**7, 7, 7, 8, 8, 8 pixel bytes differ** in a small 3×3 region (x 139–141,
y 90–92). Thus these interactive frames are not byte-exact native acceptance.
The difference remains a documented rendering follow-up, per the user's choice
to try the game before more optimization/debugging. Native source, executable,
raw frames and offset-level differences are preserved alongside the physical
capture. Deterministic native repeat and this cross-architecture comparison are
separate claims.

`acceptance-prefix.tar.gz` is a point-in-time copy made while the second session
loads. Its `capture.json` records the copy interval and per-file identities.
Open gzip streams can lack a footer and append-only journal tails can be partial;
do not treat this prefix as a completed full replay or final restoration record.
The live originals remain on the host. Its adjacent SHA-256 file was verified
locally. The six raw card frames and PNGs are also directly browsable here.
