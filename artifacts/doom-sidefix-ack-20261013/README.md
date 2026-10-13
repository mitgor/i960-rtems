# Full-width checkpoint ACK repeat — 2026-10-13

**Both Doom first-frame runs and in-engine STOP passed; full batch acceptance
failed during global shutdown. Keep startup opt-in.**
This repeats the [narrow comparison workaround](../doom-sidefix-20261013/README.md)
without changing its 801,920-byte admitted engine or its native reference output.
The previous batch completed the first frame and STOP, then refused ACK 272
because an eight-bit token field truncated the record index to 16.

## Correction

Host ioctl 8 still carries record index and invocation generation. The driver
now sends two control payloads: token `0x7f000000 | epoch` with the full 32-bit
record index, then `0x7f010000 | epoch` with the full 32-bit generation. The first
only stages intent after validating the active owner, frozen pending record and
all eight words having been read. The second consumes that intent and validates
the generation before releasing the barrier. Missing intent, invalid phase,
duplicates, partial reads, wrong index and stale generation refuse. No uncertain
write is retried. The 30-second and stalled-clock bounds remain unchanged.

Native tests compile the actual runtime and actual host packet-building branch,
decode the real eight-bit token field, and exercise indices 254 through 512,
refusals, STOP and both timeout paths. Existing checkpoint and wire-evidence
regressions also pass. Physical acceptance additionally requires both complete
normal invocations, partial-WAD STOP, all paired audits, final drain, independent
network/native replay and capture mutation rejection.

## Exact candidate

Remote workspace: `/home/mit/i960-doom-sidefix-ack-20261013`.
Boot: `0ef3253f-01b7-4e1b-974f-e7ab5cea2f6b`.
Live supervisor PID: `10490`.

- Kernel SHA256: `92ead37b5dde5fae5a0378f3e42526669a2143167e5fad4b8c7ab06ac8112ac6`.
- Module SHA256: `3b2760096dd25e13c8dc529c4427f6588fe8fedb39a98f9b82b71849e6fc5533`.
- Kernel sections: text 168,576, data 512, BSS 260,592 bytes.
- Engine/admission and dependencies come from the preceding build archive;
  the corrected build only changes the kernel/transport acknowledgement protocol.

The capture was archived and hash-verified before reboot. After a physical
power-cycle, public IPv6 HTTP returned 200 from the Mac. Reservation released;
production relay supervisor 2998 / Python 3017 owns the card in boot
`f1aa723f-2de3-44bc-8841-c48f888d6bbf`. Coordinate and stop it cleanly before
future exclusive work. See `http-restoration.json`.
The launch recipe retains all full audits and 75 network rounds. Its duration
is roughly 75 minutes, including two approximately 26-minute audited startups.

First-wipe hashes are not a screenshot or visible gameplay. Even a successful
batch will not establish the original hang's sole cause: comparison correction
and acknowledged checkpoints are tested together.

## Reproduction and evidence layout

Extract the preceding `build-evidence.tar.gz` into a clean analysis directory;
then extract this batch's `card-evidence.tar.gz` there. It supplies the corrected
`project`, `residentnet`, `residentnet-module` and `live` directories. The engine
admission and native reference remain the ones in the preceding build archive.
The archives use relative member paths; remote absolute paths recorded in build
logs are provenance, not extraction destinations. Pinned dependencies and WAD
are already in the earlier repository artifact corpus.

`i960-sidefix-ack-build.sh` records the exact corrected build command.
`i960-sidefix-ack-live.sh` records the full hardware invocation.
`i960-sidefix-ack-postrun.sh` preserves the intended postprocessing recipe. It
stopped at the live-error gate; it did not run or pass its positive acceptance
commands. Its IRQ-mutation command targets a first-rejection capture, which this
run is not; do not reuse that command as a clean-run gate. The failed card archive
was collected separately without changing its capture. Use the diagnostic
commands below for this evidence.

## Physical commands completed

Both normal invocations returned pixel FNV **4000963876**, palette FNV
**1611003811**, one frame, outcome 0, retired 1 and boundary 213. Their elapsed
command times were **1549.424** and **1529.928 seconds**, respectively. These
include the full concurrent audit/network workload and are not rendering FPS.
Both peaked at **6,445,487 private bytes / 13 blocks**. STOP after three 512-byte
fragments of the second WAD request returned outcome 2, retired 1 and boundary
210 in **25.627 seconds**, with no claimed frame.

The strict checkpoint wire replay matches all **199 + 199** normal records to
the native reference. The STOP invocation contributes five records; total **403**.
All **50** ACKs validate with no pending or uncertain acknowledgement. Repeat ACK
254, formerly failing ACK 272, and the subsequent ACKs through 400 succeeded.
Both spawns select subsector 226 / sector 0, floor 0, ceiling 192 and view +41.
All 75 network rounds completed, but final global drain failed as described below.
No complete N3 acceptance is claimed.

## Terminal STOP failure and replay limits

After host global STOP, the card deliberately entered its terminal abort handler:
`NMF1`, kind **4**, shared-heap `SHCHECK` error **10**. This is not a captured
processor-fault PC. The worker-1 stack contains the recorded abort frame, but the
specific failing assertion is not yet isolated. General-heap allocations and
frees both read **307548**, live bytes zero; those counters alone do not prove
successful ownership or final drain. Fault-owner, exception guards and held SCSI
reset diagnostics are valid. RAM rejection words remain zero.

The capture includes **613 valid full EXR1/RAM pairs**, then one complete read
whose EXR1 header is followed by terminal NMF1 fields because the terminal handler
replaced the monitor during retrieval. A subsequent independent read is complete
NMF1. The original stack validator rejected the mixed page. Do not reinterpret it
as a valid EXR1 page or bypass the shutdown failure.

`failure-analysis.json`, produced by `inspect_stop_failure.py`, reconstructs all
frozen pages and validates immutable binary/module identity and initial paired
ROM audit. Both normal WAD traces match the 4,747-request reference, with two
additional requests for STOP: **9,496 total**, **55,300 fragments / 28,312,968 bytes**.
The only incomplete request is the intended 1,536-byte STOP transfer. It also
reconstructs and validates **7,076 IP packets** and their TCP streams across
75 rounds. The last clean snapshot counters lag the final packet journal; no
valid final counter page exists, so full final-counter agreement is not claimed.

All **24 startup evidence mutations** reject after the completed engine evidence
passes its oracle/wire checks, including missing/duplicate/wrong-index/generation
ACKs. This accepts those completed command records, not global shutdown.
The native full-upload replay is still unresolved: a diagnostic attempt aborted
inside `doom_shared_peer_step` on both macOS and Linux. The experimental verifier
copy and both logs are retained as `upload-diagnostic-attempt.py` and
`upload-diagnostic-{macos,linux}.log`; it is not installed as an acceptance bypass.
No successful native full-upload replay report or final parked reply is present.
Do not assume the native abort and physical SHCHECK share one cause.

Read-only reproduction after extracting the two archives:

```sh
python3 game/doom/runtime/startup/inspect_stop_failure.py EXTRACTED_ROOT \
  --wad PINNED_FREEDOOM_WAD --output failure-analysis.json
python3 rtems/residentnet/test_startup_evidence.py EXTRACTED_ROOT/live \
  --build EXTRACTED_ROOT/admission --wad PINNED_FREEDOOM_WAD \
  --output startup-evidence-mutations.json
```

Card archive SHA256: `fb705c3f00c97ffe15d056871546903db9cd59f1875c3ed2a256a9f09c63c728`.
It contains exact sources/binaries as tested, raw captures and the stopped
postprocessor log. Later read-only analysis lives in repository source and the
adjacent reports; it does not change the recorded engine identity. No flash write
was made. Visitor logs are not included.

## Next gate

Reproduce and pinpoint the shared-heap shutdown assertion with a short bounded
STOP test, resolve the native shared-peer replay abort, then repeat the full
normal/STOP/normal/drain gates. Only then extend to bounded visible frames and
pixel readback/browser delivery. The two matching outputs here remain the initial
mostly black wipe frame, not a screenshot or playable Doom. The comparison fix
and acknowledged checkpoints ran together, so the original render/delivery hang's
sole cause remains unproven.
