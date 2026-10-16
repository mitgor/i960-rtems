> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Narrow BSP workaround and acknowledged checkpoints — 2026-10-13

**Partial success, failed full batch: first startup/frame and STOP passed; repeat
refused checkpoint ACK 272 because its wire index was truncated.** This experiment
follows the confirmed optimized `R_PointOnSide` comparison defect in
[the height investigation](../doom-height-20261013/README.md).

## Changes under test

`game/doom/build.py --point-side-o0` extracts the original function unchanged into
`r_point_side.c`, retaining the original license header and actual Doom types.
Only this translation unit is compiled with `-O0`; the rest keeps its original
flags. The switch requires the experimental startup profile. The workaround does not change the compiler backend or RTEMS compiler flags. The build records the extraction and every
compiler command. Disabling scheduling alone remains an invalid workaround.

The expanded scalar proof uses 25 cases: the previous nine plus both axes,
both direction signs, equality and either side of the node. Its `-O0` function
text must equal the actual new engine object byte-for-byte before linking.
The matching function is 416 bytes. All 25 passed on the card, with 2,750 firmware commands, 75 full paired 512 KiB
staging phases, RAM restoration and clean unload. This validates this bounded
function corpus, not the full compiler or Doom image.

Admission `--checkpoint-barriers` separately enables the kernel and module flag
`I960_DOOM_CHECKPOINT_BARRIERS`. The 144-byte application callback ABI and
512-record immutable log remain unchanged. Selected stages (spawn 63, display
80, render completion 42–44, frame 50–51 and delivery 81–98) publish a record,
then wait outside the runtime lock for the host to save and acknowledge it.

Host ioctl 8 carries only record index and invocation generation. Packet 0x7f
checks the active session, pending record, current generation, frozen record and
all eight words having been read. Duplicate, stale, wrong-record and incomplete
reads refuse. The client validates and fsyncs the decoded row before ACK; raw
read/ACK exchanges remain in the checkpoint journal. No pointers cross the channel.

Each barrier has a 3,000-tick (30-second) deadline and 10,000,000-iteration
secondary bound if the clock stops. It services the existing control path and
periodically yields; STOP returns through the owner-local boundary. Timeout is
checkpoint failure 214, never a successful frame. None of the WAD, whole-image,
paired RAM, ownership, executable authentication or final-drain checks is removed.

Native tests exercise missing/partial/stale/duplicate acknowledgements, STOP,
elapsed and stalled-clock bounds. Ten ACK evidence mutations reject. Existing
checkpoint log/client tests and eleven wire mutations still pass. The replayer
requires each barrier ACK before reading another record and reports pending ACKs;
full startup acceptance requires no pending or uncertain acknowledgement.

## Native build and hardware reservation

Workspace: `/home/mit/i960-doom-sidefix-20261013`.
Only `r_point_side.c` receives the overriding `-O0` flag. Native ASan engine and
ASan/UBSan private-library normal/STOP/deadline/read-error/repeat tests preserve
the exact reference pixels, palette, results and all 4,747 WAD requests.
The 99-constant ABI proof, three-link relocation proof, admission refusals,
zero unresolved imports and target RAM audit passed. Admission uses 801,920 bytes
(296 bytes above the prior instrumented image) of the unchanged 900,000-byte reservation; dynamic modeled heap remains unchanged.

Candidate kernel SHA256:
`a78d699f32b06545e472434d50ca43dbb832b6a7b61462c45b3856cd4762d6eb`.
Candidate module SHA256:
`054b6f41b75872bc91b2ab2cca13c06d5523128d80ed975f9e6c45c1e2130b58`.

The public relay was stopped cleanly and its module unloaded. The parallel RTEMS
chat was notified of the exclusive reservation. The full-audit normal/partial-transfer STOP/normal plan ran with unchanged
command, per-read, engine and aggregate limits. The scalar proof does not accept
the full batch. After archiving this failure, the retained module was released
by reboot. A corrected batch is tracked separately below.

## Evidence already saved

- `build-evidence.tar.gz` contains exact patched source, engine and private-library
  objects, native reference captures, independent links, admission and ABI proof.
  SHA256: `8b5a2b9401bb750e66f6fa2211463ab243dd9f6aa937ee1402526255951cfece`.
- `branch-probe-evidence.tar.xz` contains generated probes, exact code comparison,
  binaries/module, all 25 raw full-audit transactions and their replay.
  SHA256: `1ed2796bb554e0f94fed4ee49239f5e63c70d2c867b34f1b189ecb4a01450778`.
- `sidefix-build-check.json` ties the unchanged source and only-file flag override
  to both native and i960 builds, and the probe text to the engine object.
- `host-check.json`, `ram-audit.json`, `branch-probe-replay.json` and checkpoint
  test logs record their respective checks. All five native checkpoint streams
  also match the preceding height experiment exactly.

Both archives match their remote SHA256 values. Read-only analysis files added
later do not change the compiled binaries. Upstream dependencies and the pinned
WAD remain in the earlier Git artifact corpus. No flash write is involved.

## First physical startup

The card selected subsector **226**, sector **0**, floor **0**, ceiling **192**
and view height **+41**, matching native. All **199** checkpoint records match
the native stream, with **25** successful host acknowledgements. Render, HUD,
menu, wipe, video copy, `DG_DrawFrame`, owned exit and cleanup all completed.
Pixel FNV **4000963876**, palette FNV **1611003811**, outcome **0**, retired **1**,
boundary **213**. The first command returned in **1579.379 seconds** under the
full concurrent audit/network workload. On-card peak private bytes: **6445487**,
13 peak blocks. This remains inside the unchanged reservation model.

The frame is the initial mostly black wipe presentation, not visible gameplay.
The original render-to-delivery hang did not recur in this combined workaround
and acknowledgement build; this does not isolate its original cause. The spawn
comparison defect is independently confirmed and corrected by the scalar proof.
Normal/partial-transfer STOP/normal, final drain and full evidence replay remain
the acceptance requirements; a single successful frame does not replace them.

## STOP and repeat failure

STOP after 1,536 bytes of the second WAD request returned through owned boundary
210 in 28.702 seconds. The second normal invocation again selected the correct
sector and camera height. Its first 68 checkpoint records match the native
reference. ACK 254 succeeded; ACK 272 at display entry refused with ESTALE.
The original packet stored the record index in an eight-bit token field, so
272 arrived as 16. This is a host protocol bug, separate from the comparison
workaround. The final repeat outcome was not retrieved and remains unknown.

`card-evidence.tar.gz` (SHA256
`02dfec892bcb3f00e446b68f8b7778ec8003dfdaef308863d8c59a334a74028c`)
preserves exact sources, binaries and failed capture. `failure-analysis.json`
records 605 full snapshot/RAM pairs plus one unpaired failure snapshot, 75
completed network rounds, 9,420 WAD requests, 54,890 fragments / 28,103,048
verified bytes, 272 checkpoints and 26 successful acknowledgements. The sole
partial WAD request is the intended STOP. This is diagnostic validation, not
full positive network/native-upload acceptance. No evidence is relabelled.

The primary five-case native harness sources are saved as
`primary-native-source.c` and `primary-native-test.py` in the card archive. Later
host-only callback failure tests are under `callback-host`; they verify real
private-library unwinding for STOP 210 and checkpoint failure 214. They did not
change this card image.

The [corrected ACK batch](../doom-sidefix-ack-20261013/README.md) uses two packets
with full-width index and generation payloads. It preserves the same engine
image, reference output, full audits and deadlines. Its outcome must be checked
separately before accepting N3.
