# Player height and frame-delivery checkpoints — 2026-10-13

**Physical diagnostic run completed; N3 remains unaccepted.** Player height
calculation is consistent with the selected floor, but the card selects the wrong
spawn subsector/sector. A model of a captured compare/branch/test ordering exactly
reproduces that wrong selection, and a separate bounded on-card probe confirms
the optimized function miscompilation. No Doom/compiler fix has been deployed. Frame delivery
still failed, and the new post-render records were not retrieved before control
was lost. All three evidence archives are local and hash-verified. After reboot and 27 clean scalar probes, public IPv6 HTTP was restored
and independently returned 200. Exclusive reservation released.

## Experiment

The prior checkpoint run observed camera height −31 on i960 versus +41 on host,
then lost control after masked rendering but before `DG_DrawFrame`. This build
adds observations, not a camera correction or a relaxation of any acceptance gate.

New records cover decoded sector-height fingerprints; the player's mapthing,
selected subsector/sector, spawn z/floor/ceiling and initial viewheight; each height
calculation's input, ground/cheat/state flags, bob/momentum, height sum and ceiling
clamp. They then bracket return from player rendering, HUD/background/border,
menu/network update, wipe buffers and clock wait, screen wipe, video dimensions,
framebuffer copy, and existing frame/hash/exit/cleanup checkpoints.

No logging occurs inside the pixel-copy loops or clock-wait loop. No executable
pointers are sent. The same 144-byte callback ABI, immutable read-only channel,
512-record log, 16,400-byte arena allocation, guards and per-command/per-engine
limits remain. Native normal startup now produces 199 records; two normal starts
plus the five expected early STOP records fit the 512-record log (403 total).

## Offline checks

Actual engine/private Newlib native normal/STOP/deadline/read-error/repeat passed.
Pixels, palette, results (apart from the already-accounted log allocation) and
all 4,747 WAD requests remain identical to the preceding N3 host baseline.
Normal checkpoint streams repeat byte-for-byte. The 99 ABI constants include player/node/subsector sizes and alignments
and 34 relevant field offsets; all
match the private i960 build, and RTEMS callback offsets remain unchanged.

Native heap peak remains 6,646,255 bytes; conservative image reservation and target
staging bring the modeled sum to 7,550,607 within the existing 8 MiB arena.
Admission storage is 801,624 bytes, below the unchanged 900,000-byte reservation.
Three independent relocated links, zero unresolved cross imports, admission-core
refusal tests and the full target placement audit pass. These are not physical
Doom acceptance. See `host-check.json`, `layout.json`, `ram-audit.json`, and the
exact build recipe `i960-height-build-final.sh`.

The live invocation is the same audited normal/partial-read STOP/normal plan as
[the previous checkpoint run](../doom-checkpoints-20261013/README.md), with the
new workspace paths. The existing production relay was stopped with SIGTERM and
its module unloaded cleanly before this exclusive session began. No flash write.

N2 remains the accepted milestone until every N3 gate passes.

## Physical findings

Run: PID 33787 in `/home/mit/i960-doom-height-20261013`, boot
`5e697ec6-a2e7-488d-95b3-4262e31f9b7f`. The same full audited
normal/partial-read STOP/normal plan was used, without changing deadlines or
interrupting the test. It failed during the first actual startup (generation 4).

The first **49** checkpoints match. This includes all 395 sectors' decoded
floor/ceiling fingerprint (`3146200641`), side texture-ID fingerprint, map counts
and player mapthing `(0, −160, 90°)`. The first difference, record 50 / stage 63,
is at WAD request **4,670**, earlier than the previously observed camera value:

| Recorded quantity | Native host | Card |
| --- | --- | --- |
| Spawn subsector | 226 | 1394 |
| Spawn sector | 0 | 82 |
| Spawn z and floor | 0 | −72 |
| Ceiling | 192 | 96 |
| Initial viewheight | 41 | 41 |
| Height delta / bob / momentum | 0 | 0 |
| Ground flag / cheats / live state | 1 / 0 / 0 | 1 / 0 / 0 |
| Resulting viewz, both recorded height calls | 41 | −31 |

The recorded height calculation does what its inputs require: −72 + 41 = −31.
A height correction would mask the earlier wrong sector selection. The independent
pinned-WAD geometry walk agrees with native. Modeling the captured axis-aligned
comparison ordering instead agrees with the physical values in every row above.
See [the disassembly lead and its limits](COMPILER-LEAD.md).

BSP rendering completed at request 4,721; planes completed at 4,760. The last
retrieved record is stage 43, record **188**. There is no retrieved stage 44,
`D_Display` continuation (81), HUD/menu/wipe/video marker (82–98), frame (50), or
owned exit/cleanup. The native trace has 199 records. The prior run captured masked
completion (44), so this run does **not** establish a narrower exact hang location;
checkpoint retrieval latency is now an explicit diagnostic gap. It also does not
prove the hang shares the comparison defect. No clean frame or startup STOP/repeat
and final drain is accepted.

The complete WAD request sequence is identical to the previous failed checkpoint
run: **4,764 requests**, first differing from native at request **4,675**. All
**27,725 fragments / 14,194,884 bytes** match the pinned WAD, with exact order,
lengths, payload, padding and CRC checked. The full request/response wire evidence
is preserved, not replaced with these summaries.

Failure replay validates **279 complete snapshot/RAM pairs**, the complete heap
pages and initial immutable image/paired ROM audit. The last full snapshot was at
**2,217.839 seconds**, tick **217,295**. The final heap page (page 1) contains only
**60 words** and remains explicitly partial. There were **37 completed network
rounds**. Captured fault markers are zero, but final PC/state remain unknown.
An upload query (op 2) timed out after **2,864.938 ms**; the next audit received
EBUSY and the existing guard retained DMA/module resources until reboot.

## Exact evidence

- `card-evidence.tar.gz`: actual compiled project/live harness sources, kernel and
  generated module/binary, complete capture and terminal log, final dmesg/boot ID,
  placement and build logs. Kernel SHA256
  `42b0f74c1092159d3874c4ea377aa0a316a2a8745cc91f6facea49493d619c78`;
  module SHA256 `4ef37b43d42d5b9bf3239178ec1c5e509ca0eb4efbab38359ae174432474f045`.
- `build-evidence.tar.gz`: exact patched Doom sources, host/cross engine and private
  library objects, native tests/results/frame/request/checkpoint streams, packed
  engine and admission identity, 99-constant ABI proof and corrected build recipe.
- `failure-analysis.json`: full completed audit/WAD replay and partial-page details.
- `checkpoint-comparison.json`: strict raw wire/sequence/padding replay, first
  mismatch and last retrieved record, explicitly diagnostic and `accepted:false`.
- `height-comparison.json`: decoded signed 16.16 height values and delivery markers
  for native and card, after the same strict checkpoint validation.
- `spawn-map-reference.json`, `spawn-map-compiled-cc.json`, `r-main-disassembly.txt`:
  independent geometry walk and captured-instruction-order model, both clearly
  distinguished from hardware execution.
- `comparison-to-previous.json`: exact complete request-sequence equality.
- `host-check.json`, `native.log`, `layout.json`, `ram-audit.json`,
  `checkpoint-tests.log`: native, ABI, placement and strict malformed-record tests.

The build archive SHA256 is
`6b3b528a401d769606aa3201f628af38f4fe5b073ae4d96c00f3407cf095e124`;
card archive SHA256 is
`64e3af563bb2ce6e3cba84be16b1a12ee839cc6b2e1de2baf405389fa7317032`.
Both matched the remote archive before reboot. Upstream dependencies/WAD remain
in earlier Git artifact history; source symlinks are not standalone dependency
archives. Final Git also contains read-only analysis added after the physical
build; the archived project records what actually ran. No visitor logs or flash
writes are included.

Extract both tarballs into the same `CAPTURE_ROOT`, then run:

```sh
python3 game/doom/runtime/startup/inspect_failure.py CAPTURE_ROOT \
  --wad "$WAD" --output failure-analysis.json
python3 rtems/residentnet/checkpoint_replay.py CAPTURE_ROOT/live \
  --build CAPTURE_ROOT/admission --wad "$WAD" --output checkpoint-comparison.json
python3 game/doom/runtime/startup/inspect_height.py CAPTURE_ROOT \
  --output height-comparison.json
python3 game/doom/runtime/startup/inspect_spawn_map.py "$WAD" \
  --output spawn-map-reference.json
python3 game/doom/runtime/startup/inspect_spawn_map.py "$WAD" \
  --compiled-axis-cc --output spawn-map-compiled-cc.json
```

Success-only N3 replay and its normal/STOP/normal acceptance mutations cannot pass
on this incomplete capture and are not reported as passing. The existing log/client
and 11 malformed-wire mutations pass; the previous 170-record physical capture
still validates under the extended decoder. The focused on-card comparison proof is now complete. Next: an inspected compiler
or narrow implementation correction and full startup revalidation; separately make
selected hang checkpoints host-confirmed with bounded waits.

## Confirmatory branch probe and restored service

The bounded probe ran nine vectors under three builds outside RTEMS, in boot
`e7e1bcd3-0421-4d31-8fa9-9d6748d7110e`. Original optimized code fails cases 0 and 5;
disabling both scheduling passes still fails case 0; `-O0` passes all nine.
The exact optimized function body matches the Doom object before ordinary linking.
See [COMPILER-LEAD.md](COMPILER-LEAD.md) for the instruction sequence and limits.
No replacement compiler or changed full Doom/kernel image was deployed.

All 27 scalar transactions restored RAM and unloaded cleanly. The independent
replay validates 2,970 firmware commands, 81 complete paired staging phases,
request/module/payload identity and result captures. Semantic failures remain
explicit; successful transport does not turn the bad return values into passes.

`branch-probe-evidence.tar.xz` includes all three binaries, actual generated source,
objects/ELFs/disassemblies, module source/binary, complete transaction captures and
the run script. Its SHA256 is
`f7e3a7b4301a2ecb33425d3cfdb90548f730e25fa5e216f67b60dcdd004de635`.
The probe archive was losslessly recompressed from gzip to xz;
`branch-probe-archive.json` records both archive hashes and the verified identical
uncompressed tar hash. Extract it with `tar -xf`.
`branch-probe-results.json` records raw case outcomes; `branch-probe-replay.json`
records independent audit replay. To replay after extraction:

```sh
python3 game/doom/runtime/startup/verify_branch_probe.py CAPTURE_ROOT/branch-probe \
  --output branch-probe-replay.json
```

Rebuild the probe with `branch_probe.py --engine ENGINE_CROSS_ROOT --project REPO
--out NEW_PROBE --cross CROSS_PREFIX`. The archived `branch-run.py` uses the
existing full `host/loadrun/loadrun.py` transaction for each variant/case; use a
fresh output root and exclusive card ownership when reproducing it. The build
script itself never accesses hardware.

Production relay PID **19965** was restored in the above boot, output
`/home/mit/i960-rtems-web-20261011/http-after-doom-height-20261013`. Independent Mac
IPv6 curl returned **HTTP 200**; details are in `restoration.json`. The parallel
RTEMS chat was given the hardware release and confirmed compiler finding. Future
card work must coordinate with the production relay and stop it cleanly first.
