# Doom presentation profiling — 2026-10-14

**Accepted bounded card test: 1.965 → 2.474 FPS (+25.94%).** User requested render,
presentation and DMA profiling, optional FNV, removal of the extra framebuffer
copy, full audits/ownership, physical comparison and documentation.

## Scope and measurement

The persistent `I_VideoBuffer` remains unchanged: Doom keeps partial redraws and
cached drawing pointers there. The optimized path directs `I_FinishUpdate` into
an available admitted delivery slot, eliminating the second `DG_ScreenBuffer` →
delivery-slot copy. This is not a zero-copy renderer. The previous slot remains
immutable until exact host ACK; the adapter rotates its output pointer only after
successful owned publication. Timeout/STOP cannot rotate into a pinned slot.

Build options on `game/doom/play/build.py`: `--pipeline --frame-profile`, with
optional `--no-fnv` and `--direct-frame`. Default image admission, CRC policy,
frame guards, ownership and full system audits are unchanged. FNV absence is
explicit; zero is recorded for omitted pixel/palette hashes. These optional hashes
are distinct from engine admission and the separately optional DMA CRC.

`--presentation-test` builds one instrumented engine with four 12-frame blocks:
frames 5–16 hash+copy, 17–28 no-hash+copy, 29–40 no-hash+direct, 41–52 hash+copy.
Frames 1–4 retain exact paired DMA/mailbox reads. Frame DMA CRC is disabled for
this comparison throughout, avoiding a CRC confound. Full 73,728-byte guarded
captures, all 52 immutable frame packets, ownership/refusal/ACK checks and full
periodic system/RAM audits remain. No menu or movement inputs in this experiment.
All engine modes advance the same virtual game clock and use the same WAD.

The 16-word PFR1 trailer starts at byte 64,768, after 64,000 pixels and 768 palette
bytes; all following padding must remain zero. Timings include renderer/BSP/
planes/sprites, persistent-screen presentation, adapter copy/hash/palette, and the
preceding publication wait. `display_ms` overlaps render and must not be added to
it. Renderer timings can include preemption and WAD service, not only CPU cycles.
The existing owned clock has **10 ms resolution**. A zero duration means below
that measurement resolution, not zero cost. Hardware DMA timing includes enable,
descriptor launch and completion polling; preparation/cleanup are separate.

Read-only control index 7 exposes five frozen DMA timing words (generation,
preparation, hardware interval, cleanup, total), only after completion and before
ACK, only for the current owned frame. No address or DMA submission is accepted
through this control. Host capture timing also separates submit, completion wait
and guarded readback. Profile query cost is recorded separately.

## Previous interactive session preserved

The earlier Doom session had already finished and returned owned STOP/global
drain before this task accessed the card. Its retained module was not unloaded.
`interactive-full-closed.tar.gz` SHA-256:
`529cb58f3e334309f3eab3650e6e3b14d12c78762714a88df431792071fc222a`.
It includes every guarded DMA capture, journals and full audits. The archive was
copied and hash-verified locally; `prior-play-system.json` confirms full replay
before reboot. Original binaries are pinned by the preceding WAD batch.

## Implementation checks

The actual adapter plus actual two-slot ownership code is exercised across copy,
direct and FNV transitions; delayed ACK service verifies the old slot remains
unchanged. Actual DMA tests cover frozen timing reads before completion, after
ACK, invalid index, and phase durations alongside existing STOP/timeout/guard
faults. Metadata tests independently verify sequence, modes, timing sums, hashes
and reserved padding. Full native engine tests cover input, deterministic repeat,
STOP and heap drain. Native 52-frame output is compared independently of the
explicit timing trailer; paired physical reads still compare all 65,536 bytes.

The kernel RAM audit passes with **400 bytes** of mutable-tail space remaining.
Remote workspace: `/home/mit/i960-present-20261014`.

## Failed selector run and final candidate

The preliminary run on boot `753c9a2a-606a-49d6-af92-129147713e7a`, supervisor
5023, failed the first-frame profile check: frame 1 reported mode 2 (no-FNV/direct)
instead of mode 1 (FNV/copy). Host/native tests had returned mode 1. The pinned
i960 compiler generated an unsigned-range selector with a comparison, another
comparison/branch, and a later condition-code test. The physical result disagreed
with the source. No FPS claim is accepted from this run.

A separate disassembly review also found a per-pixel mode test inside the copy
loop. The corrected adapter selects copy/hash behavior outside the loop, retaining
the original combined copy/FNV loop in baseline mode. Benchmark mode selection
now uses a 64-byte table indexed by `generation & 63`; the bounded benchmark stops
at frame 52. Disassembly confirms a mask and byte load, with no range comparison.
Initialization checks generations 1, 17, 29 and 41 before loading a level.

The failed run's exact sources/binaries and evidence were copied and hash-verified
locally before reboot:

- `failed-selector-build.tar.gz`: `a9bfd475ad6eef1314824e0728e2d13d36eda50f4236ae4a4833b9e2de33d1ca`
- `failed-selector-card.tar.gz`: `922aeb9daf3464c4a35a4dc5281ecfbdafa8c95bde89cbc29d481898a1cd2302`

`replay_failed.py` verifies eight full paired audits and one additional unpaired
monitor page captured at failure. The first 73,728-byte guarded DMA capture has
intact guards and matches the complete mailbox frame. Native comparison retains
exactly the known seven pixel differences; palette bytes match. The wrong mode
is explicitly recorded. STOP/drain and complete session acceptance are **not**
proven. The complete verifier rejects this failed run; prefix replay does not
change that status. Archives remain unchanged.

The corrected candidate passes the native engine's deterministic 52-frame repeat,
input/STOP/heap tests and 320-frame actual-adapter/ownership tests. Tests now also
check publication failure without pointer rotation and five bounded read-only
DMA timing indices. Candidate identities:

- kernel: `fa106571c4a03ac8635e908cb05f3f8608cc91ab0d7389152681cbc2cfa7fc99`
- driver: `8f15d6d59da2b1d815b2e376e08ad4fd63580e080abbedb77fc4c0f743452d4d`
- admitted engine: `e7d865bacfbf5b16ee8ab14a88ff1178ac4b66d14f68bd9a994d6ee101ad6600`

A reused driver output directory initially prevented regeneration. It was preserved
and a new directory generated. The first module compilation was interrupted by
reboot before hardware use; the completed repeat is logged in `module-repeat.log`.
Neither incomplete module build was used on the card. The final build completed
before reboot. Final physical acceptance passed in capture `repeat`.

## Accepted physical result

Capture `repeat` on boot `6a2add11-5684-47ad-8986-37c44d185bcc` passed all
52 frames, 14 complete paired monitor/RAM audits, exact ACK/ownership checks,
owned STOP and global allocation drain. All four initial complete DMA/mailbox
frames match. All 52 pixel/palette payloads match the prior accepted card run
exactly; the known seven native/card pixel differences per frame remain unchanged.
The native 52-frame repeat is deterministic. All 35 journal tamper cases reject.

| Mode | Frames | FPS | Mean interval |
|---|---:|---:|---:|
| FNV + second copy, before | 5–16 | 1.950 | 512.9 ms |
| No FNV, second copy | 17–28 | 2.235 | 447.4 ms |
| No FNV, direct delivery slot | 29–40 | 2.474 | 404.1 ms |
| FNV + second copy, after | 41–52 | 1.980 | 505.0 ms |

Each FPS uses the eleven within-block intervals; the pooled before/after baseline
uses twenty-two intervals and is **1.964771 FPS**. Optimized throughput is
**2.474457 FPS**, **1.2594× / +25.94%**. Baseline drift is about 1.6%.
All CRCs were off throughout. This is one bounded, no-input scene, not a promise
for other maps, interactive play, or an uninstrumented build.

The profile itself adds work. In particular, FNV-on decoding independently
recomputes both hashes on the host; profile query/decode averages 24.0/23.5 ms
in the baseline blocks versus 2.5/4.7 ms without FNV. The measured gain therefore
includes this host validation saving, not only card CPU savings. It should not
be extrapolated directly to an unprofiled build. Prior unprofiled 2.070 FPS is
not the denominator for the same-run improvement.

| Optimized phase | Mean wall time |
|---|---:|
| Renderer total | 316.7 ms |
| BSP/setup | 193.3 ms |
| Planes | 83.3 ms |
| Sprites | 40.0 ms |
| Persistent screen → delivery slot | 46.7 ms |
| Adapter palette/metadata work | below 10 ms per sampled frame |
| DMA preparation / cleanup | below 10 ms per sampled frame |
| DMA hardware interval | 3.3 ms (quantized mean) |
| Host submit | 12.5 ms |
| Host completion wait | 248.0 ms |
| Full guarded host readback | 13.1 ms |

These fields overlap; do not add them. The 248 ms host completion wait is mostly
waiting for task service, not measured PCI bus time. The renderer intervals can
also include preemption and service stalls. The retained screen copy is about
47 ms; only the redundant delivery-slot copy was removed. The adapter went from
88–98 ms with FNV/copy to 63 ms without FNV and below one clock tick with direct
presentation. A 10 FPS target needs a 100 ms frame budget, already far below the
measured renderer alone. Next work should separate renderer CPU time from task
scheduling and profile BSP/column/span loops, then consider reduced rendering
resolution/detail. More DMA bandwidth alone cannot explain the needed gain.

The read-only HTTP receiver fetched all **52 binary frames**, each payload SHA-256
matching its audited capture. Mean HTTP fetch was **51.74 ms** on the observer.
This proves delivery through the browser endpoint, not browser paint FPS or
interactive input latency. Existing browser decoder regression passed.

## Reproduction and preserved evidence

- `repeat-build.tar.gz`: `17b7ade6e89cb8755bfc47f4ead93c1f8f178e9fd4fa78fc334a628736fa9234`
- `repeat-card.tar.gz`: `10c3663049eba2d8218e1a8e1ad78abc5c77ad1f5b26c864159b127629bb4b3b`

The build archive contains exact candidate sources, admitted/packed engine,
kernel/module, host and cross objects, native frames, RAM audit, disassembly,
build scripts and test logs. The card archive contains every guarded frame,
full audits, control/transfer journals, STOP/drain and replay/tamper results.
Both archives were copied, SHA-256 checked and independently replayed locally
before reboot. `local-{system,frames,wad,measurements}.json` and
`http-verification.json` contain the local checks. Failed-selector archives stay
separate and are never counted as acceptance.

After extracting both archives into one directory, replay with:

```sh
python3 project-final/rtems/residentnet/verify.py --root build-final repeat
python3 project-final/rtems/residentnet/verify_play_pipeline.py repeat
python3 project-final/rtems/dma/verify_wad.py repeat --wad /path/to/freedoom1.wad
python3 project-final/rtems/residentnet/tamper_play_pipeline.py repeat
python3 analyze.py repeat --native native-frames-final
```

Use the WAD identity recorded in the capture and pinned prior WAD build. The
`--previous` analysis additionally compares against frames extracted from
`artifacts/doom-pipeline-20261014/card-evidence.tar.gz`. The closure script's first
attempt referenced a missing archive symlink; the original archive was supplied
explicitly and closure rerun. No capture was edited.

Features remain opt-in; the mixed benchmark engine is refused for interactive
launch. See [build and play instructions](../../game/doom/play/PRESENTATION.md).
The hardware acceptance covers all three modes and their transitions in the
benchmark, not a separate long-duration production build.

## Final hardware state

The accepted test closed cleanly and all evidence was verified locally before
a normal reboot. SSH has not returned (`No route to host`); user power-cycle
requested. Public IPv6 HTTP restoration is pending. `restore.sh` contains the
exact established relay command with a fresh output directory and refuses to
start while the PCI function is bound. See `restoration.json`. No force-unload
was attempted.
