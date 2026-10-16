> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Bounded visible Doom frames — 2026-10-13

**Accepted:** physical startup/STOP/repeat/global drain, all full audits, independent native replay and evidence mutation tests pass. Both archives are locally hash-verified; the public RTEMS service and static frame gallery are restored after reboot.

The opt-in visible build skips the cosmetic opening wipe and exits after two presentations. Native checkpoints show gametics 2 and 3; these first two scene images are byte-identical. Neither animation nor interactive gameplay is claimed.

The engine exports two 65,536-byte slots (64,000 indexed pixels, 768 palette bytes, zero padding). The admitted engine must match the compiled reference SHA256 before its immutable 131,072-byte archive is published. Raw arena storage is allocated after private engine cleanup and released before the next engine attempt or global drain. Generation/offset/word reads use the existing resident session and uncertainty handling. Host capture and replay compare every byte against the independent native oracle before publishing PNGs.

Host proofs: sanitizer-backed startup/STOP/deadline/read-failure/repeat; 218 checkpoints per normal run; gametics 2/3; admission 867,808 bytes within 900,000; RAM audit passed. Native heap peak 6,646,255 bytes already includes the checkpoint allocation; adding the 900,000-byte image reservation and 4,352-byte target staging allowance gives 7,550,607 bytes within the 8 MiB arena. Protocol tests reject generation/range errors and model failure at every one of 258 mailbox exchanges. Thirteen frame-evidence mutations are rejected. The previous single-frame admission gate regression also passes.

Workspace: `/home/mit/i960-doom-visible-20261013`. Full physical recipe: `live.sh`, unchanged 75 network rounds with full paired audits, startup/STOP/startup and final global drain. Production relay PID 4359 stopped cleanly and unloaded before exclusive admission. The physical run began in boot `c76b2f32-a14d-4c03-952f-cbfa6b254cb9`, supervisor PID 59894; the read-only LAN preview server is PID 69666 on port 8086. Exact candidate and accepted evidence are archived below.

## Exact candidate and unchanged safety gates

Kernel SHA256 `13b79220700ebbcf8e76c6cd3c78d79873b5ef9e27f237369b10a34e1a6ce57b`;
module SHA256 `9d73781380ac039a57391b20f2573196c1381a2a4010b59053657b09cfefbc14`.
The candidate uses the existing 12 MiB owned region and 8 MiB Doom arena.
The image has 431,900 file bytes, 814,352 memory bytes, 867,808 admission bytes;
frame slots begin at manifest-relative offset 683,232. No broader RAM claim is
made. The upload code uses 28,144 bytes, engine gate 10,880 bytes, and mutable
layout retains 976 bytes at its tail. Executable identity, relocations, BSS,
post-execution code digest, owned runtime cleanup and the worker-stop barrier
remain mandatory.

Native frame pixels SHA256
`5e140cae4e89eaf3d661951b7dc4908a1677aea5c575529f22ccd35843f41620`;
palette SHA256
`12bafa34214682ae20c2cb6f4e38f21575564de88c4599f3410661e9b7a5c6d3`.
Full two-slot archive SHA256
`5b2d7d65263f56a32175a21f8fd30f0cdc2aa78ff8a6e63c426e4fa35d831d1c`.
Each scene contains 127 distinct palette indices. The native reference is not
card evidence; physical readback must independently match every byte. The target
gate embeds only the expected SHA256, not the reference pixel array. Frame slots
are admitted zeroed BSS beyond the image file bytes and populated by the renderer.

The admitted build retains `--point-side-o0`. Skipping the wipe is an explicit
`--visible` source variant, not a general Doom or compiler fix. It remains opt-in.
The normal source path and old single-frame gate regression are preserved.

## Frame archive protocol

UPL1 ioctl operation 9 accepts exactly eight payload bytes: archive generation
and 1,024-byte-aligned offset. The existing session epoch, mutex, pending-command,
uncertainty and retained-resource checks apply. Mailbox operations `0x6c`, `0x6d`
and `0x6e` select the published generation, select the window, and read 256 words.
A read takes 258 exchanges. An uncertain exchange retains the session; it is not
retried as if successful. The target refuses reads while an upload command is
pending, during STOP, before publication or after invalidation. It never accepts
an address from the host.

The first normal engine return publishes frame-archive generation 1. These
archive generations are separate from owned-engine generations 4/5/6. Starting the intervening
STOP attempt invalidates and frees that archive. A completed repeat publishes
generation 2. Global drain releases the final archive after workers and IRQ
contexts are quiescent. Readback deliberately re-reads the first completed chunk
and checks stale generation, out-of-range offset and post-STOP refusal.

Replay requires both complete raw archives, all 263 journal events in order,
the session epoch matching the owned-control journal, exact response headers,
all 258 successful payloads and five refusals, and all four derived PNGs. Native
upload replay models the gate/archive lifecycle using separately verified native
frame bytes; it does not emulate the Doom i960 instructions. Physical checkpoint
and byte comparisons supply that independent execution check.

## Reproduction

`build.sh` records the candidate build commands against the existing pinned
DoomGeneric, Newlib, RTEMS and cross-toolchain dependencies. `live.sh` records the
75-round physical batch, and `postrun.sh` the default full upload replay, network
and paired-memory verifier, checkpoint comparison, 24 startup evidence mutations
and 13 framebuffer evidence mutations applied to the actual capture.

## First physical capture

The first normal return passed all 218 native checkpoints, 33 host-confirmed
barrier ACKs, the full archive digest and exact host readback. Startup returned
in 1,541.382 seconds. Its first 129 successful 1 KiB reads (including the deliberate
re-read) took 15.339815 seconds, mean 118.913293 ms per ioctl. This is about
8.4 KiB/s during this validation workload, not a gameplay FPS measurement.
The client timer includes its shared gate and kernel session waits behind full
audits; it is not an isolated mailbox bandwidth ceiling.

`visible-1.bin` and `browser/card-1-{0,1}.png` are actual card readbacks, not native
preview images. Both slots match native byte for byte. The two 33,982-byte PNGs
were delivered to the Mac with exact-byte verification, ten requests averaging
19.683804 ms (maximum 23.304208 ms). Same-host requests averaged 1.381049 ms.
These HTTP timings exclude the preceding card readback and Doom startup.

Browser inspection verified Next, Previous wrapping, Refresh and natural image
size 320×200. It caught an initial CSS stretch: the explicit image height did
not scale with its width. Adding `height:auto` restores 960×600 in the inspected
viewport. `browser-first.jpg` records that initial layout; the corrected result
is `browser-first-corrected.jpg` and `browser-ui-first.json`. This host-only style
fix does not change the tested engine, kernel, module or raw framebuffer bytes.
The build archive predates that CSS correction; final source/capture evidence
will include it separately.

The intervening STOP returned in 26.718452 seconds with the expected cleanup,
and reading the invalidated generation was refused. The repeat startup and
final system drain subsequently passed, as recorded below.

Build archive SHA256:
`052789166b6c0d7a80a7e5e99158623f31b3b38b9f569212de498547a70a01d0`.
The local copy matches the remote checksum.

## Repeat and browser delivery

The repeat returns normally in **1,537.298524 seconds**, produces the same complete
131,072 bytes, and passes its 218-record checkpoint reference. Across normal /
STOP / normal: **441 records and 66 successful barrier ACKs**. Both actual raw
captures, all 263 frame-journal events and all four PNGs pass independent replay.
The five refused requests include stale generation, out-of-range offset and
post-STOP access. Successful reads total 264,192 bytes including the two deliberate
1 KiB re-reads, taking **33.426929 seconds** combined; the second capture accounts
for **18.087114 seconds**. Mean observed ioctl time is **129.561740 ms**, including
audit contention.

The second capture's ten exact PNG responses average **19.230771 ms** from the
Mac (maximum **24.702083 ms**), or **1.366385 ms** on the serving Linux host.
`browser-final.jpg` shows capture 2 in the actual browser; Refresh selected the
new capture and Next selected its second frame. Both early demo ticks remain
pixel-identical, so these tests prove visible rendering and delivery, not motion
or interactive controls. Global drain and complete batch acceptance also pass, as recorded below.

## Viewing the captured frames

Open **http://192.168.2.75:8086/** on the LAN. **Previous frame**, **Next frame**
and **Refresh capture** operate the verified gallery. There are no movement,
shooting or game-input controls yet. The page uses saved card captures, so viewing
it does not take ownership of the card or interfere with the public RTEMS server.
The actual 320×200 PNG files also live in `browser/` beside this README.

If using an SSH tunnel, run:

```sh
ssh -N -L 8096:192.168.2.75:8086 mit@192.168.2.75
```

Then open http://localhost:8096/. `serve-browser.sh` is the restart recipe on the
Linux host; it exposes only `live/browser` and never opens the card. It is a
foreground server unless launched with `nohup` by its caller.

## Complete physical and replay acceptance

The run completes in **4,491.161699 seconds**, with **604 full snapshot/RAM pairs**
and **75 dual-stack network rounds**. Global STOP parks at tick **444,556**.
The default verifier accepts guards, worker/IRQ drain and ownership checks,
**322,731 allocations freed**, and **9,917 shared handles created and retired**.
There are no large-workload allocation refusals. All 24 snapshot corruptions are
rejected. The final frame archive is released before the controller heap drain.
No shared-heap shutdown assertion recurs.

Default full native upload replay accepts **8,152 command replies / 22,137 upload
PIO records**, with `commands_only=false`, `native_cleanup_modeled=false` and
`stop_cancelled_partial_image=true`. The physical parked query remains required.
The separately validated frame journal adds 258 successful reads and five
refusals; it is not silently mixed into the command replay. The WAD evidence
covers **9,496 requests / 55,300 fragments**. Both 218-record normal streams
match native; the five-record STOP stream has its expected early exit.

All **24 startup evidence mutations** and **13 framebuffer evidence mutations**
are rejected against the actual capture. The checkpoint comparison JSON remains
diagnostic-only: its STOP divergence is expected, and the full engine verifier
validates that STOP separately. No native replay abort recurs.

The startup times above end after the result/control reports. Including frame
readback and publication, the two normal attempts take **1,558.731368 /
1,556.050516 seconds**; STOP plus archive-refusal check takes **27.029814 seconds**.
These include the audit and host-confirmed checkpoint overhead, not just Doom CPU
execution. No real-time performance claim is made.

`card-evidence.tar.gz` SHA256:
`6207cbaa30473583a23178b80839bae084c0d1040fdd4bd89192eefb635101b5`.
It contains the complete live capture, exact final host sources (including the
CSS correction), replay and mutation results, diagnostics and run/restore scripts.
The separately hashed build archive contains exact candidate kernel/module,
engine/native binaries, admission files, patched sources and build proofs.
Standalone JSONs and PNGs beside this README are convenient copies. Production
visitor statistics are not included.

The next engine milestone is bounded visible motion while retaining the same
reference and audit gates. Persistent engine/frame ownership, host backpressure,
input and faster framebuffer transfer remain future work. Simply increasing the
static frame array would consume the small remaining admission reservation and
is not the proposed streaming design.

## Restoration and released hardware

Both archive copies passed local SHA256 verification before the host reboot.
Linux returned in boot **`083c2956-4f85-49e6-abb9-3d485c4d7422`** with no bound
card driver or competing relay. `restore.sh` launched the unchanged public
production profile: supervisor **1745**, Python **1843**, output directory
`/home/mit/i960-rtems-web-20261011/http-after-doom-visible-20261013`.
It owns `0000:37:09.1` through `dac960auto`.

The Mac receives **HTTP/1.0 200 OK** and the RTEMS system-info/Vader page at the
existing public IPv6 URL. The card's outbound IPv6 fetch of example.com also
passes. These are local-Mac-to-public-address and card-outbound checks, not a new
external-network reachability claim. Headers, body and metadata are saved here;
raw CRLF headers are compressed, with a normalized readable copy beside them.
Visitor statistics continue in the existing host directory and are not archived.

Gallery PID **1746** serves the saved capture at **http://192.168.2.75:8086/**.
Its exact PNG responses and browser display were checked again after reboot.
It never opens the card; the new production session need not run Doom to show
these saved frames. The test reservation is released. Stop the production relay
cleanly before future exclusive card work; never unload retained exclusive
resources by force.
