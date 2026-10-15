# One bulk guarded capture per Doom frame

Accepted on the DAC960PG on 2026-10-15: **100 frames, 51 full paired audits**,
three-second held-destination test, held-frame STOP, global shared-heap drain,
full mailbox comparisons and exact HTTP payload checks. Maximum IRQ gap was
**10.488 ms**. No firmware flash write.

## Result

Same accepted RTEMS kernel and Doom engine as `irq-drain-20261015/fixed`;
only the Linux capture handler and Python reader changed. Frames 21–50 are the
predeclared steady comparison window, including every interval and audit delay.

| Measurement | Previous 72-read path | Bulk capture |
| --- | ---: | ---: |
| Capture reads per steady frame | 72 | **1** |
| Sum of capture ioctl times per frame | 43.178 ms | **0.278 ms** |
| Observed completion → capture/check/log/release | 61.398 ms | **26.405 ms** |
| Release ioctl mean | 4.264 ms | 22.330 ms |
| Delivered FPS, frames 21–50 | 5.192 | **4.802** |
| Renderer elapsed mean | 188.333 ms | 189.667 ms |
| First-frame engine execution | 104.133 s | 103.693 s |
| Separate engine upload | 81.349 s | 81.143 s |
| Warm restart, frames 66–68 | 2.420 s | 2.370 s |

**Capture ioctl cost fell 99.36%; completion-to-release fell 56.99%. Overall
FPS fell 7.52% in this comparison. This is not an FPS improvement claim.**
Rendering remains around 190 ms and the earlier release now encounters longer
control-command waits. Audit/scheduling phase also differs between these two
runs. These measurements do not establish that bulk capture causes the FPS
regression; repeated interleaved runs would be needed to separate those effects.
No delayed ACK or relaxed audit was introduced to improve the score. The remaining
release/control wait is a separate investigation, not hidden inside this change.

95 HTTP frames matched saved payloads exactly. HTTP receipt is not browser paint
latency. All first 52 card frames and palettes match the prior card baseline;
the native oracle retains only the four already documented pixel differences at
29260, 29261, 29580 and 29581. WAD request counts match (1755 startup, 1805 total,
38 warm restart). There are no new pixel differences.

## Implementation and safety

See `rtems/dma/pingpong/README.md` for operation-8 ABI. One 73,728-byte copy includes
both guards, all 65,536 payload bytes and the complete completion record. Exact
session/generation checks, coherent-memory ordering, guard validation, slot
pinning and separate release remain. Full successful copyout grants release
credit; a partial copy grants none. The legacy chunk path received the same
copyout-credit correction. The raw bulk request and response remain in the journal.

The initial 16 host-started comparison frames deliberately retain the old frame
DMA capture path. Steady ping-pong frames each use one bulk read; deliberate
stall/STOP recaptures each also use one. Polling and RELEASE remain separate
operations. No RTEMS RAM/layout, card DMA setup, renderer, CRC/FNV policy or
full-audit cadence changed. Ping-pong and peer-yield remain opt-in profiles.
An older module rejects operation 8; rebuild the matching module and client.

## Tests and evidence

- Actual handler under ASan/UBSan: partial bulk and chunk copyout faults cannot
  enable release; invalid length, stale generation, damaged guards/metadata,
  exchange timeout and retained mapping behavior pass.
- Actual Python ABI test: exactly one ioctl, 73,760-byte buffer, exact full journal.
- Existing client flow, Linux 32-bit target/ownership/protection fixtures pass.
  The 32-bit fixtures cannot link on this ARM Mac; they ran on the Linux host.
- Full Linux system/frame/WAD/profile/STOP replay passes. Mutation checks reject
  4 drain, 8 WAD-profile, 3 WAD, 24 frame and 6 bulk-journal mutations: **45 total**.
- Historical 72-read Doom and synthetic captures still replay. New bulk records
  are checked byte-for-byte against the complete captures and frame payloads.

`candidate.tar.gz`: exact tested project sources, accepted card image/engine,
new generated Linux module and build inputs. `card.tar.gz`: complete bounded
capture, run log, replay and mutation results. `archives.sha256` authenticates
both local copies. `measurements.json` contains transport costs;
`comparison.json` contains native/baseline frame, WAD and renderer comparisons.
`http-observations.jsonl` records exact HTTP receipts.

Hashes:

- kernel: `1dce227e130d144187cfd0577ca333da09d20d62baf6617db30bc29b137a2c08`
- module: `e97e8bd9eeb7da15bfb19d62625bb928c2b393e4357cec1bc903abe0f48111d9`
- Doom image: `e9e43e211d1abf31da7d6a29d9a2c7c42f09ada8e7255af4ec2a2a93d32813dd`

## Reproduce

Extract with `python3 artifacts/bulk-capture-20261015/extract.py /tmp/bulk-replay`.
Then run the extracted `project/rtems/residentnet/verify.py --root
/tmp/bulk-replay/build /tmp/bulk-replay/live`, frame verifier and mutation scripts
listed in `verify.sh`. The WAD remains the unchanged Freedoom input from the
prior accepted build; its SHA-256 is
`7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d`.
The 52-frame native oracle is in `artifacts/peer-yield-20261015/card-owned.tar.gz`.

For a new hardware run, inspect the current owner first. `build.sh` rebuilds
only the module against the copied accepted image; `run.sh` requires an unbound
card and runs the finite full-audit acceptance. Never force-unload retained
exclusive mappings. Save, hash-check and replay evidence before rebooting.
`restore.sh` restores the public IPv6 service after reboot; it is not a test run.

## Restored state

Evidence was copied and SHA-256 verified locally before normal reboot. The host
returned automatically. Public IPv6 HTTP is restored and independently returned
200 / 2890 bytes containing RTEMS. Boot
`27cc6b32-2d2f-4701-ba88-1c6d34484a42`; relay PID 1555, supervisor 1552 owns
`dac960auto`. Doom port 8087 is closed after the bounded test. Inspect current
ownership before any future run; these PIDs are historical observations.
