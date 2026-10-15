# Doom ping-pong DMA integration — 2026-10-15

Status: bounded physical acceptance passed in two runs. This is opt-in; it is
not a long-duration interactive or default-transport qualification.

## Design

The admitted Doom engine retains two owned source slots. Two driver-allocated
73,728-byte coherent host destinations contain the 65,536-byte framebuffer,
guards, and a chained completion record. The task starts DMA; the host observes
completion in coherent RAM, captures every allocation byte, and explicitly
releases the exact generation. No caller-selected DMA address, cyclic descriptor
list, or unbounded overwrite is allowed.

WAD and frame transfers share DMA1. Before publishing a WAD request, the same
owned task drains any outstanding framebuffer DMA and records its source ACK.
The WAD routine then owns DMA1 synchronously through completion and host ACK.
It returns to rendering only after the WAD mapping and buffer lease are safe.
Full system snapshots accept only an exact frame or WAD lease; unknown activity
remains an error. Native ASan/UBSan tests execute both actual DMA implementations
in this order, along with existing STOP, stalls and timeout quarantine tests.

The main fixed code window was too small by 64 bytes in the first link attempt.
The audit wrapper is now a separate object in the existing protected engine
window. No RAM boundary or guard moved. The candidate uses 145 protected pages
and leaves 304 bytes of mutable reserve. The old COFF compiler does not support
section attributes, so the linker places the entire helper object explicitly.
Renderer timing/CPU trailers remain enabled. Legacy per-frame DMA timing queries
are omitted in both comparison phases; completion-record timing is used instead.

## Bounded acceptance protocol

`--pipeline --pipeline-test --wad-dma --pingpong --debug-audits` is opt-in.
Frames 1–16 use host-triggered DMA; frames 17 onward use card-triggered ping-pong.
CRC/FNV are off in both phases; guards, generation/source ownership, full captured
bytes, first four full mailbox comparisons and full paired system/RAM audits
remain. Both host destinations are held for three seconds at frames 17/18, then
released; the final two frames remain held across owned STOP and are recaptured afterward.
The controlled run continues to 100 frames and automatically restarts the level
at frames 60/62/64/66, after the input-free measurement window.
The host checks unrelated Upload command completion at most once a second,
immediately after STOP. It does not remove any system audit.

Measure baseline intervals 5–15 and steady ping-pong intervals 21–50. Exclude only
the declared setup/stall/STOP phases, retaining all steady-state audit outliers.
These are delivered frame rates, not display refresh rates. Raw card time is
10 ms resolution and bracketed host clock samples bound latency estimates.

## Third-buffer design considerations

A third destination cannot increase DMA1 bandwidth or renderer throughput.
It can absorb a host scheduling pause longer than the slack of two buffers.
Our destination capture is copied into immutable HTTP bytes before release;
a slow browser therefore does not hold a DMA destination. A third host buffer
costs another 73,728 bytes and can queue one additional old frame. Three card
render slots are a separate change (another 65,536 bytes plus ownership work).
The useful evidence is destination stalls and render/consumer timing, not the
synthetic producer's earlier 79.8% gain. Final estimates follow measured Doom
results below.


## First physical run: interactive transport acceptance

The initial 52-frame run completed with **104 full paired audits**, four full
same-frame DMA/mailbox comparisons, 5,045 WAD DMA reads (one after ping-pong
activation), a 3.062-second both-slot stall, resumed delivery, held-buffer STOP,
and global drain. All HTTP-observed frame payloads match the saved card captures.
The browser screenshot is `browser-frame52.png`.

The browser supplied seven key events during this run. Its FPS values are
therefore **not a controlled comparison**: the scene changed. The first ten
frames match the independent native pixel oracle except for the four previously
known pixels at (140,91), (141,91), (140,92), (141,92); their palettes match.
Later input-driven frames are retained without inventing a deterministic oracle.
The controlled repeat rejects keyboard events during acceptance.

Linux and Mac system/frame/WAD replay pass. All 24 evidence mutations are rejected.
An initial tamper test exposed a verifier gap: deleting the final chunk of the
post-STOP recapture went unnoticed because a complete earlier capture existed.
Replay now requires every ordered full capture cycle, including repeated and
post-STOP reads. This was a replay gap, not an observed DMA corruption.

The full-snapshot active-frame-lease counter is zero in this run; snapshots did
not catch that short interval. Full audits still ran unchanged. The prior v10
synthetic acceptance and current native tests exercise active-lease recognition;
do not claim this Doom run independently repeated that overlap coverage.

Archives `build-evidence-v1.tar.gz` and `card-evidence-v1.tar.gz` were copied,
hash-verified, extracted and replayed locally before the normal reboot. Their
hashes are in `archives-v1.sha256`. The controlled run uses the same kernel,
module and engine binaries, with a revised bounded host runner.


## Controlled 100-frame acceptance

Same exact kernel/module/engine as the first run; host keyboard input disabled.
The eight accepted key transitions are the automatic level-restart sequence at
frames 60/62/64/66, after the comparison window.

| Metric | Host-triggered DMA | Card-triggered ping-pong |
| --- | ---: | ---: |
| Delivered FPS | 3.503080 | 3.887065 |
| Mean host transfer/capture | 212.524 ms | 41.270 ms |
| Mean complete host readback handling | 216.411 ms | 45.167 ms |
| Renderer wall time | 211.0 ms | 207.586 ms |
| Retained screen-copy wall time | 44.0 ms | 44.138 ms |
| Previous-publication wait | 81.0 ms | 0 ms |
| Timer-sampled renderer CPU | 107.0 ms | 103.793 ms |

**FPS improvement: 10.96%.** Frame interval is about **257.26 ms**. All steady
intervals are retained (ping-pong range 44.5–441.1 ms); there is no outlier trim.
The comparison is sequential A/B with 10 baseline and 29 steady ping-pong
intervals, not a long statistical or reversed-order qualification.

Card start-marker → host completion observation has a bracketed mean estimate
of **17.15–44.24 ms**. Completion observation → validated capture/release averages
**47.28 ms**, giving roughly **64.43–91.52 ms** from the start marker to release.
These include scheduling/audits/host work; they are not pure DMA duration,
render-to-photon latency, or input latency. Card timestamps resolve 10 ms.
All 100 HTTP frame payloads match captures; mean Mac fetch time is **45.61 ms**.
The actual browser displayed the controlled scene (`browser-controlled.png`).
HTTP fetching is not a measurement of browser paint time.

- **100 delivered frames**, 7,372,800 unique guarded allocation bytes, four exact
  65,536-byte DMA/mailbox pairs; repeated stall and post-STOP captures also pass.
- **108 full paired system/RAM audits**, unchanged three-second requested cadence;
  owned STOP, retained-source cleanup and global allocation drain pass.
- Both destinations remained byte-identical during a **3.037-second stall**;
  delivery resumed. Frames **99/100** stayed held and unchanged across STOP.
- **5,100 WAD DMA reads**, including **56 after activation**. The level restart
  adds 55 reads after the fixed scene; delivery resumes through frame 100.
- First **52 controlled frames** match the independent native oracle except
  exactly the four existing pixel differences; all 52 palettes match. Menu and
  reloaded-game frames are retained and transport-validated, without claiming
  a deterministic native timing oracle for the asynchronous menu transitions.
- Linux and Mac system/frame/WAD replay and **24 tamper cases** pass. Native sanitizer
  tests cover DMA1 handoff, active-transfer STOP, stuck DMA quarantine, stalls,
  stale/duplicate releases, descriptor mutations and protected-page mutations.
- The active-frame full-snapshot counter is again zero: this batch does not add
  physical overlap coverage beyond the earlier accepted v10 producer proof.

## Would three buffers help?

**Expect little or no sustained FPS gain in this scene—roughly 0–2%, not another
large speedup.** This is an engineering estimate, not a triple-buffer benchmark.
Rendering plus the retained screen copy and adapter already cost about 252.4 ms,
corresponding to a rough 3.96 FPS budget at this scheduling share. Measured output
is 3.89 FPS and the producer's previous-publication wait is zero. The third slot
cannot shorten that work or make the same DMA1 engine transfer two directions
simultaneously.

A third host destination could absorb longer audit/scheduling pauses and improve
jitter. It costs another **72 KiB host RAM** and, if allowed to queue, can add
about **257 ms** of stale-frame latency. Host destinations and card render slots
need not have the same count: another host destination does not inherently need
another card framebuffer. A third render slot would separately cost **64 KiB**
and require extending the admitted ownership contract. Keep two buffers for now;
renderer/screen-copy optimization or a carefully tested CPU scheduling policy
has substantially more headroom. No three-buffer implementation is claimed.

## Binary identities and reproduction

- Kernel: `13dc18948520e463f7312f77eacc1a51b52e23e7b46eb1f2b9b668f5f4d68261`
- Module: `951f9261a16d177070311644d1169422f445c21fbd769e3d31cf161b9dacd7d4`
- Engine: `b451038ef172713a8992cd72e1a452ea98c88a380008b65b666c712d60eadb5b`
- Engine span **815,792 bytes**; admission **869,668 bytes**.
- Remote workspace: `/home/mit/i960-doom-pingpong-20261015`.

`build.sh` records construction with the pre-existing pinned RTEMS/newlib
workspace; the fresh-checkout route is `game/doom/play/build.py --pipeline
--pingpong --frame-profile --cpu-profile --no-fnv --direct-frame --low-detail`.
See `game/doom/play/PLAY.md` for the complete launch arguments. `run.sh` is the
52-frame transport test; `run-level.sh` runs the controlled 100-frame test.
`build-evidence-v1.tar.gz` contains exact binaries and native oracle artifacts;
`source-level.tar.gz` overlays the revised host runner/verifiers, and
`card-evidence-level.tar.gz` contains the complete controlled capture. Archive
hashes are recorded in `archives-level.sha256`. No flash changes were made.

`replay.sh` verifies both extracted captures, all transport journals, full system
audits, WAD content and the native comparison. `local-*.json` contains Mac replay
results; `*-level.json` records the controlled Linux run.


## Final service state

Both exact archive batches were hash-verified and replayed on the Mac before
normal reboot. Public IPv6 HTTP is restored and returned **200 / 2,891 bytes**
with RTEMS content from the Mac. Boot `a7e3490e-127d-4a0c-9f62-bb9466b03d05`,
supervisor **4012**, relay **4014** owns `dac960auto`; see `restoration.json` and
`restore-relay.log`. The bounded Doom server is closed. Inspect current ownership
before another run; stop the public relay normally, never force-unload mappings.

Next: qualify a longer interactive ping-pong session (including browser
reconnect/input release and early STOP), then optimize renderer/copy CPU work.
A third buffer is lower priority given the measured zero publication wait.
