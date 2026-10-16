> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Doom startup checkpoints — 2026-10-13

**Diagnostic run completed; N3 is not accepted.** First mismatch: checkpoint 51,
player viewing height **−31 on the card versus +41 map units on the host**.
The first 50 records agree. Exact card/build artifacts are archived below; all
completed full audits remain intact. The public IPv6 server was restored and
independently returned HTTP 200 after reboot. The exclusive reservation is released.

## Purpose and contract

The preceding N3 attempts diverged at WAD request 4,675 and did not return a
frame. This opt-in build records startup stages and scalar fingerprints without
accepting those previous failures. The expected native path finishes level setup
at request 4,671, so the selected patch/composite and camera checkpoints cover the
first differing texture request during rendering.

The private owned ABI is extended from 128 to 144 bytes with version `0x20001`,
features 15, a four-scalar checkpoint callback and three zero reserved words.
Old APIs stay unchanged. The callback validates application ownership and publishes
an eight-word record under the existing short runtime lock. No allocation, wait
or application pointer is accepted by the callback. Records contain magic,
monotonic sequence, invocation generation, stage, three scalar values and the
invocation-relative WAD request count.

The log holds 512 records without overwriting. A registered 16,400-byte allocation
inside the existing 8 MiB Doom arena holds it from runtime binding through the
acceptance session. Publication is disabled before controller heap drain; an
uncertain hardware session still retains everything until reboot. Exhaustion
refuses publication and exits through the existing owned error boundary, rather
than silently dropping records. Host polling retains raw requests/replies and
checks contiguous sequence, padding, epoch and overflow status.

The new read-only upload ioctl operation 7 freezes one selected record, then
reads its eight words through control tokens `0x7d/0x7e`. It uses its own frozen
buffer and the existing session mutex/epoch/state guards. It neither replaces
nor skips snapshot, RAM, heap, WAD, code, owner or final-drain audits.

Only `--checkpoints` engine/platform builds and a `--startup-checkpoints` admission
manifest enable this ABI. The compiled kernel/module carry `I960_DOOM_CHECKPOINTS`.
Checkpoint records and the host trace are diagnostic evidence, not a new trust
exception for executable admission or a way to accept a mismatching Doom frame.

## Memory placement

A static log was rejected by the existing linker overlap assertion before card
use. The final design allocates it inside the guarded arena. The expanded runtime
code also exceeded its old upper window; its complete object now resides in the
existing protected engine-code window, without moving any boundary. Final ends:
BSS `0xc0f8bbf0`, engine code `0xc0f8e4b0`, upload code `0xc0f9ada0`.
The full placement audit passes (`ram-audit.json`).

## Host validation

The actual engine with private Newlib passes first frame, STOP, deadline, read
failure and repeat under ASan/UBSan for the port and ASan for the engine. The
checkpointed pixels and all 4,747 WAD requests match the preceding native baseline.
A normal start records 162 checkpoints; each injected failure records eight;
fresh normal starts have identical checkpoint bytes. The baseline first frame
is still the initial wipe, not visible gameplay.

The native allocation proof includes the retained checkpoint buffer before the
900,000-byte image reservation and contiguous 6 MiB zone. It retires the checkpoint
allocation and verifies complete drain. Actual target placement and runtime guards
remain mandatory. `test_checkpoints.py` exercises invalid indexes, generations,
selection, immutable frozen records, owner refusal and overflow. Existing RTEMS
regressions pass. The independent N2 replay still passes all 7,949 commands (`n2-regression.json`).
The actual host record drain and 11 malformed wire/sequence/padding mutations
pass (`checkpoint-tests.log`). Physical results and exact archives are recorded below.

The final native peak is 6,646,255 heap bytes, including the 16,400-byte log;
image reservation and target staging bring the conservative sum to 7,550,607
bytes, within 8,388,608. Admission storage is 799,852 bytes. `host-check.json`
is reproduced with `game/doom/runtime/startup/verify_checkpoints_host.py`, using
the extracted previous N3 native platform as `--baseline`. Both actual normal
checkpoint streams have SHA256
`056174436196069e670341b46751dd1a2ade2f349a6db86b14716719c95eb59c`.

Inside the armed engine call, a refused checkpoint uses exit code 214. An
unexpected refusal outside that boundary retains the existing conservative
fail-stop behavior; it is not a promise to recover from arbitrary corruption.
The reviewed native normal/STOP/normal event count fits the 512-record budget.

## Reproduction

Use the pinned Doom source and RTEMS/Newlib/lwIP source archives already recorded
in the repository's artifact history. In a fresh remote workspace, build the
engine with `game/doom/build.py --arena-runtime --wad-cache --platform-runtime
--startup --checkpoints` for `host32` (with `--sanitize`) and `i960`. Build the
private runtime with `runtime/platform/build.py --startup --checkpoints` for each,
then run `runtime/startup/test_native.py` and `verify_checkpoints_host.py`.
The original N3 `host-oracle.json` still supplies the pixel/palette reference.

Pack the cross image with `runtime/platform/pack_engine.py`, then admit it with
`runtime/engine/admit.py --startup-oracle ... --startup-requests
platform-host/startup-0.requests.bin --startup-checkpoints
platform-host/startup-0.checkpoints.bin`. Run `runtime/startup/test_abi.py` and
`rtems/residentnet/test_engine_gate.py` against that admission. Native builds
are comparisons, not hardware acceptance.

The RTEMS build uses `--profile residentnet --secondary-reset --fault-owner
--extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12
--resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine admission
--wad-batch --wad-poll --dispatch-atomic`. Check `ram_audit.py`, generate the
module with `residentnet/build_transport.py`, then build it with the host kernel
headers. All code and guards remain covered by the existing full image audit.

The actual card invocation, with absolute workspace paths substituted, is:

```sh
sudo python3 project/rtems/residentnet/live.py \
  --payload "$WORK/residentnet/kernel.bin" \
  --module "$WORK/residentnet-module/dac960auto.ko" --output "$WORK/live" \
  --resident-upload --doom-heap --doom-shared --doom-runtime --wad "$WAD" \
  --upload-concurrent --owned-mib 12 --heap-shared --queue-reclaim \
  --general-heap --extra-ram --fault-owner --secondary-reset --parallel \
  --ticks 540000 --rounds 75 --round-interval 60 --drop-data
```

Read-only checkpoint comparison (also works on an incomplete captured session):

```sh
python3 rtems/residentnet/checkpoint_replay.py CAPTURE \
  --build ADMISSION --wad "$WAD" --output checkpoint-comparison.json
```

A successful diagnostic-channel comparison alone never replaces full network,
upload/native, WAD and final-drain replay. Preserve uncertain captures before
reboot, never force-unload retained resources, and restore the established public
IPv6 relay after testing. Do not archive visitor logs.

## Physical result and limits

The test ran in `/home/mit/i960-doom-checkpoints-20261013`, PID 48740, boot
`0679efe6-990e-420c-a930-b502ea84df40`. No manual early stop or audit reduction was
used. Kernel SHA256:
`a7c1118d338a9d9e75064e89cac0528acb6bacdeb0c7d68af35fac089144c011`.
Module SHA256:
`da20c1bd021db2c65134a3567a37a03c6ced3a350fed42364b00bbae5deaf6c6`.

The preliminary runtime/cache/relocation/owned-entry proofs and deliberately
altered code/metadata refusals completed before actual engine generation 4.
The diagnostic reader validated 170 immutable records; the native normal trace
has 162. These are different paths, not a successful matching first frame.

| Checkpoint | Card | Host | Interpretation |
| --- | --- | --- | --- |
| 1–50 | Match | Match | Startup stages, level counts, side texture-ID fingerprint and player position/angle agree |
| 51, stage 38 | `viewz=0xffe10000`, −31 | `viewz=0x00290000`, +41 | First observed scalar difference, after WAD request 4,674 |
| 52, stage 40 | x=0, y=−160, angle=90° | Same | Horizontal camera position and angle agree |
| 53, stage 41 | cosine=−25, sine=65,535, z=−31 | Same cosine/sine, z=+41 | Wrong height reaches renderer setup |
| Stage 42 | BSP finished at request 4,721 | At 4,698 | Both reach end of BSP rendering |
| Stage 43 | Planes finished at 4,760 | At 4,743 | Both reach end of plane rendering |
| Stage 44 | Masked finished at 4,764 | At 4,747 | Last captured physical checkpoint |
| Stage 50 and owned exit | Not captured | Present | Frame callback, result and retirement remain unproven |

All 4,764 request offsets and lengths exactly reproduce the previous N3
compatibility failure (`comparison-to-previous.json`). The first 4,674 match
native. Request 4,675 selects the TSCRN8/TTALL1_2 region instead of the host's
WALL02 region. All 27,725 completed fragments, totaling 14,194,884 bytes, match
the pinned WAD, including fragment order, lengths, padding and CRC. This locates
the observed scalar discrepancy before the differing read, not in host delivery.
It does not prove all loaded geometry matches: counts and a side-texture
fingerprint are narrower checks than full geometry fingerprints.

Read-only failure inspection reconstructs and validates 274 complete snapshot/RAM
pairs, 275 complete snapshots, complete heap pages and the initial image/paired
ROM audit. The final RAM page contains only 40 words and is preserved as partial,
never counted as a complete pair. The last full snapshot was at 2,221.286 seconds,
tick 217,658. There were 37 completed network rounds. All captured fault markers
are zero, which does not identify the final fault PC or exclude a later fault.

An upload query (op 2) timed out after 2,814.425 ms. The next audit operation
received EBUSY; the existing uncertain-session guard retained DMA/module resources.
The checkpoint journal itself has no timeout. No final engine result exists;
normal/STOP/normal, final owner drain and complete N3 acceptance were not reached.
The fail-closed behavior was retained. Do not run success-only replay or its
20 acceptance mutations on this incomplete capture and report them as passing.

## Evidence and reproduction

- `card-evidence.tar.gz`: exact compiled project sources, admission and packed
  engine, kernel/module and generated module sources, ABI proof, complete raw
  live capture, terminal log, final dmesg, boot ID and build/placement logs.
- `build-evidence.tar.gz`: exact patched pinned Doom sources, host/cross objects,
  private Newlib outputs, manifests, native executable/results/frames/WAD traces
  and checkpoint traces, plus build logs. Original upstream source archives and
  the pinned Freedoom WAD remain in the earlier Git artifact history; source
  symlinks in the compiled project snapshot are not standalone upstream archives.
- `failure-analysis.json`: full completed audit/WAD diagnosis, explicitly
  `accepted:false`, with partial final page and timeout identity.
- `checkpoint-comparison.json`: strict raw checkpoint wire/sequence/padding replay
  and first mismatch, explicitly diagnostic and unaccepted.
- `comparison-to-previous.json`: complete WAD request-sequence comparison with the
  prior compatibility failure; not a timing or correctness acceptance claim.
- `host-check.json`, `native.log`, `layout.json`, `ram-audit.json`: native comparison,
  59 ABI constants and target placement proofs.
- `offline-tests.log`, `checkpoint-tests.log`, `n2-regression.json/log`: offline
  regressions, log/client and malformed-evidence tests, accepted N2 native replay.
- `restoration.json`: post-reboot owner and independent public HTTP verification.

Both tarballs were copied to this working folder and their SHA256 values matched
remote before reboot. They are included in the repository artifact inventory.
The compiled source snapshot intentionally precedes later read-only replay and
documentation refinements; it preserves exactly what ran. No visitor logs are
included. No flash was programmed by this experiment.

Extract the card archive into `CAPTURE_ROOT`, then run from the repository:

```sh
python3 game/doom/runtime/startup/inspect_failure.py CAPTURE_ROOT \
  --wad "$WAD" --output failure-analysis.json
python3 rtems/residentnet/checkpoint_replay.py CAPTURE_ROOT/live \
  --build CAPTURE_ROOT/admission --wad "$WAD" --output checkpoint-comparison.json
python3 rtems/residentnet/test_checkpoints.py
python3 rtems/residentnet/test_checkpoint_evidence.py
```

## Next experiment

Instrument `P_SpawnMobj`/`P_SpawnPlayer` and `P_CalcHeight` before changing game
semantics. Record selected subsector/sector index, decoded floor/ceiling heights,
`mo->z`, `floorz`, `ceilingz`, viewheight/delta, bob and resulting viewz. Compare
actual relevant `player_t`/`mobj_t`/sector field offsets as well as sizes, then
check signed fixed-point operations and BSP sector selection against host data.
The −72-unit difference suggests concrete height inputs to inspect; it does not
establish whether geometry, field access, arithmetic or earlier state caused it.

Separately bracket `D_Display` after `R_RenderPlayerView` through HUD/status/wipe
and `I_FinishUpdate`/`DG_DrawFrame`. Reaching masked-render completion narrows the
hang interval, but no captured PC links that hang to the height discrepancy.
Keep full audits, pinned WAD, owned STOP/repeat/drain gates and the existing
per-command/per-engine limits. N2 remains the last accepted milestone.
