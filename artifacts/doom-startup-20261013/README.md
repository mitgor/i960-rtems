# N3 actual Doom startup — 2026-10-13

**N3 is implemented but has not passed physical acceptance.** Two real card
attempts timed out before returning the first-frame report. Both exact builds,
raw captures and independent failure analyses are preserved. Host and exploratory
instruction-model success do not replace card acceptance. The session has ended;
its retained resources require reboot, never forced module unload.

## What the host proves

The actual private-Newlib Doom engine initializes Freedoom Phase 1 and exits
at its first presented frame. Normal / STOP / deadline / read failure / repeat
cases pass with private-library ASan/UBSan; a second build additionally
instruments engine memory with ASan. All ten cases cleanly retire the private
library and drain the guarded heap.

The normal 64,000 indexed pixels and 768 palette bytes match the prior corpus
byte for byte (`host-oracle.json`, `host-verification.json`).
`host-first-frame.png` is that **host reference**, a mostly black initial wipe
transition. It is neither a card pixel readback nor a completed visible level
frame. The reference uses 4,747 WAD requests / 14,155,460 data bytes.

Peak private allocation: 6,445,535 bytes in 13 blocks. Native heap peak including
the retained 64 KiB / 96 KiB proof buffers and direct cache allocations:
6,629,855 bytes. The proof reserves another 900,000 bytes for the image and
allows 4,352 bytes for target staging, inside the existing 8 MiB arena.
The temporary 1 MiB layout reservation must be released before final engine
admission; retaining it fragments the native contiguous 6 MiB allocation.

`host-proof.tar.gz` preserves these native builds/captures and the **initial**
default-alignment cross build, not the current compatibility candidate.
The current code still replays the N2 accepted capture: all 7,949 native
commands pass (`n2-regression.json`, with its compiler/replay log).

## First physical attempt: preserved failure

`failed-first-card.tar.gz` contains the exact first kernel, module/generated
source, repository source snapshot, admission image, raw capture, live log,
final kernel log and RAM placement audit. Boot
`53f5aaac-03ad-405a-8ad8-6657a19e728b`; kernel SHA256
`2f77665a40613b63edf43ab0608ef8e5dab68584055b7b88b978cd94a037982a`.
It is a failed test, not a derived successful replay view.

The engine completed 4,769 WAD requests / 27,743 fragments / 14,204,100 bytes.
Every completed fragment has the correct file bytes, sequence, offset, length,
padding and CRC. Its first 4,674 requests agree with the host trace. The next
texture request differs; the host requested the WALL02 region while the card
requested the TSCRN8/TTALL1_2 region. No first-frame report was accepted.

The final upload query timed out after 2,882.425 ms; the later audit freeze
received EBUSY because the driver retained the uncertain session. There were
347 complete captured snapshot/RAM pairs, with zero captured fault markers;
the last was at tick 230,080, 2,345.082 seconds into the run. This does not
establish the state after the timeout, a fault PC, or final drain. The extended
network test also stopped advancing after six complete dual-stack rounds.
Partial packet checksums and TCP reassembly pass, but later HTTP SYN-ACKs are
not acknowledged. Do not label that a complete network acceptance run.

`failed-first-analysis.json` is reproduced read-only with:

```sh
mkdir -p /tmp/i960-n3-first
tar -xzf artifacts/doom-startup-20261013/failed-first-card.tar.gz -C /tmp/i960-n3-first
python3 game/doom/runtime/startup/inspect_failure.py /tmp/i960-n3-first \
  --wad /path/to/freedoom1.wad --output /tmp/n3-failure.json
```

The archive was copied locally and its SHA256 checked before reboot. The PC
returned on its own with boot `b0252251-ca4e-4f5a-9f35-edb0e34da379`.

## Investigated differences and current candidate

Default GCC i960 layout makes ordinary records larger/more aligned than on the
32-bit host: `side_t` 32 rather than 20 bytes, `sector_t` 112 rather than 88,
zone block header 32/alignment 16 rather than 24/alignment four. Packed on-disk
WAD records match. Doom's zone allocator only rounds to pointer size (four),
so the default target record alignment exceeds that promise. Its different
record sizes also change the memory/cache conditions; a different read trace
alone cannot identify corrupted WAD data.

For startup only, both the engine and its private Newlib use the compiler's
`-mold-align` compatibility layout. `test_abi.py` compiles actual definitions
and checks 55 size/alignment/API offset constants against the host. All match;
the RTEMS table remains 96/128 bytes with unchanged callback offsets
(`abi-layouts.json`). RTEMS itself retains its existing ABI.
This is an independently established portability correction, not a proven
explanation of the physical hang, whose final PC was not captured.

The host packet pump now runs between four-word frozen audit groups. Every
snapshot, RAM and heap word and check remains present. The pump is inactive
before traffic and during parked audits; EAGAIN-only retry is preserved.
Regression tests exercise slow full pages, WAD exclusion, retained RX and
inactive-pump behavior. The original main thread could wait for WAD service
between groups while leaving TUN forwarding idle for seconds.

The startup profile alone also permits a 540,000-tick/90-minute aggregate
acceptance budget. Two complete starts plus uploads exceed the previous one-hour
budget at the measured transfer speed. Per-engine 30-minute and per-read
five-second deadlines are unchanged. The shared firmware limit header is tested
for old limits, ARM encoding and invalid configurations.

Second physical candidate:

- Engine span 744,608 bytes; initialized bytes 428,460; 13,231 relocations.
- Admission storage 797,532 bytes; zero unresolved imports; three matching links.
- Template SHA256 `5cdd3f0c528fce2e22e6bd380b7d06c1f5f3b1ec243c18c43f45c0fd88d160de`.
- Kernel SHA256 `25dd26bc206cec40f77e55a9a7666adb6df1f85cf7c6d662d1c301fed1bec4a5`.
- Full placement audit passes; no new RAM grant or moved guard boundary.
- Live plan: normal / partial-read STOP / normal, with 75 parallel dual-stack
  rounds, all full audits, independent replay and evidence mutation tests.

`instruction-exploration.tar.gz` preserves a diagnostic extension of the small
repository instruction interpreter, its linked images, exact sources, logs and
modeled RAM/request outputs. It reproduces the host request trace and full
initial-wipe pixels/palette with the compatibility image. Allocation, I/O,
setjmp/longjmp and time are explicitly modeled; there is no RTEMS/IRQ/register
cache emulation or ISA conformance suite. It is not an acceptance verifier or
proof of the physical hang's cause. Both model executions pass host ASan/UBSan.

The intermediate v2 kernel only added the aggregate limit; it was built but
never run on the card. The v3 candidate includes the private layout correction.
Keep the feature opt-in: both physical attempts failed. Browser output, later
visible frames, persistent gameplay and a gameplay FPS measurement remain later
milestones. See the [startup contract](../../game/doom/runtime/startup/README.md).

## Compatibility retry: physical failure, 36 network rounds

`failed-compatibility-card.tar.gz` contains the exact v3 project source,
resident kernel, generated module/source, admission and packed engine, ABI proof,
raw live capture, build logs, RAM audit and final kernel log. The archived source
is the source actually run; later local replay/diagnostic corrections are in Git.
Its `project/artifacts` symlink refers to previously preserved dependencies;
it is not a self-contained copy of the entire artifact history.
Archive SHA256: `ef3f3caa78a67e9c9cca8140d190df61108567ddc9d4f02874b3a508de03d2fc`.
Workspace `/home/mit/i960-doom-startup-v3-20261013`; boot
`b0252251-ca4e-4f5a-9f35-edb0e34da379`.

The first initialization completed 4,764 WAD requests / 27,725 fragments /
14,194,884 data bytes. Every completed payload, sequence, length, offset, padding
and CRC checks against the pinned WAD. The matching host prefix is still 4,674
requests; request 4,675 selects the same TSCRN8/TTALL1_2 region instead of the
host WALL02 region. Correcting private structure layout did not eliminate the
physical discrepancy or hang. No fault PC was captured; neither interrupt
preservation nor the first-frame exit is established as the cause.

There are 275 complete snapshot/RAM pairs, 276 complete snapshots, 158 complete
heap pages and a final RAM page truncated after 44 words. The last snapshot is
at tick 213,613 / elapsed 2,180.839 s with zero fault markers. The incomplete page
is preserved and explicitly reported, never counted as a complete audit.
Upload query timeout: 2,772.949 ms; subsequent monitor read: EBUSY. The module
recorded uncertain completion and retained DMA. There is no accepted engine
return, startup STOP/restart test, final drain, full network acceptance or FPS.

The revised packet pump completed 36 dual-stack rounds before failure (versus
six in the first attempt). This supports improved concurrent forwarding but does
not establish the requested 75-round acceptance. No audit words were removed.

Reproduce the read-only failure analysis, which always reports `accepted:false`:

```sh
mkdir -p /tmp/i960-n3-compat
tar -xzf artifacts/doom-startup-20261013/failed-compatibility-card.tar.gz -C /tmp/i960-n3-compat
python3 game/doom/runtime/startup/inspect_failure.py /tmp/i960-n3-compat \
  --wad /path/to/freedoom1.wad --output /tmp/n3-compat-failure.json
```

`failed-compatibility-analysis.json` and `failed-first-analysis.json` reconstruct
the complete frozen pages and validate their guards, original firmware and
payload identities. They deliberately do not run successful-session replay on
incomplete captures. `test_startup_evidence.py` is prepared but has no completed
physical startup baseline yet; do not claim its 20 mutations passed on hardware
evidence. N2 full network and 7,949-command native regressions still pass.

Next diagnostic milestone: publish bounded stage IDs and state fingerprints
through the independent control channel before/after level setup, texture
precache, draw and the owned exit. Compare native and actual i960 state at the
first differing request; preserve interrupt/owner/loan guards. After fixing the
located issue, repeat both normal starts, partial-transfer STOP, all full audits,
independent replay/tampering and final drain. Later milestones are full pixel
readback, a visible level frame and browser delivery, then interactive gameplay.

## Service restoration and ownership

After both failure archives were copied and hash-checked locally, reboot cleared
the retained v3 session. Boot `0679efe6-990e-420c-a930-b502ea84df40`; public
production relay PID 2667, `dac960auto` bound, output
`/home/mit/i960-rtems-web-20261011/http-after-doom-startup-20261013`.
The established production payload/module are unchanged. Its dual-stack ping,
UDP and TCP self-checks passed, and an independent Mac IPv6 request returned HTTP
200. `service-restoration.json` preserves the check without visitor logs.
The parallel RTEMS chat received an explicit release of this test reservation;
the public relay is now the card owner. Coordinate before interrupting it.
