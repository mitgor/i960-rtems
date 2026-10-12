# Doom engine preflight: accepted baseline — 2026-10-12

The opt-in engine-linked **diagnostic preflight** passed physically with full
paired audits, normal / STOP / normal, exact image admission, post-execution
code revalidation and complete global STOP drain at tick **100,085**. Actual
Doom initialization, a rendered Doom frame and browser gameplay remain untested.

## Evidence and exact build

- `accepted-atomic.tar.gz`: dereferenced exact source tree, generated dispatcher,
  build metadata, kernel binaries, kernel module, engine image/relocations,
  journals, full audits, test output and cleanup evidence. Extract into an empty
  directory; the run is `live-atomic/`, build is `residentnet/`.
- `failed-diag.tar.gz`: snapshot-lock starvation of WAD response 6; no IRQ marker.
- `failed-fair.tar.gz`: full failed batch proving the dispatch identity/stack gap.
- `archive-sha256.json`: archive hashes. `request.json`: physical payload,
  loader-image and module hashes plus boot identity. No visitor logs are included.
- `irq-rejection.json`, `irq-tamper.json`: decoded first rejection and seven
  mutations rejected. `dispatch-native.log`: original dispatcher reproduces the
  gap; patched dispatcher preserves caller levels 20 and 31.
- `network-replay.json`: accepted network, ownership, RAM/stack and drain audit.
- `upload-replay.json`: **7,853 commands / 18,212 PIO ioctls** reconstructed,
  byte-compared against the real native C upload/runtime core; exact captured
  replies retained except established address/asynchronous-counter normalization.
- `*-tamper.json`: runtime 8, cache 9, relocation 7, owned 9 and engine 11
  evidence mutations rejected (44 total), in addition to the seven IRQ cases.
- `offline-final.log`: complete RTEMS offline regression suite, exit 0. Earlier
  `offline-before-fixes.log` / `offline-current.log` retain intermediate results;
  the final log supersedes them. `replay-before-clock-fix.log` preserves the
  exact failing comparison and successful WAD read trace before the model fix.

The kernel SHA256 is
`a64e9b77983094d889b3a4c077b85e2210aeb1d91695050a9f59dc8701e3a5a8`;
module SHA256 is
`e2757206a7bfc9b5638001cc51f2bd62a690ba462be69a0e1764bc7694ac9114`.
The accepted archive SHA256 is
`30f5a0086d17232a5a2081fc7fed8bc1fa48f9f93aea77ca77723df42fc520ad`.

## What ran on the card

The candidate spans 754,448 bytes, has 13,175 relocations and requires 807,148
bytes of admission storage. A conservative 1 MiB initial image reservation keeps
a contiguous 6 MiB zone available despite retained proof buffers. All earlier
runtime, cache, relocation and owned-context probes remain in the batch.
Changed code and changed metadata with valid transport CRCs are refused.

The full-engine-linked preflight exercises private Newlib integer/float/%lln
formatting, the 6 MiB allocation, known framebuffer/palette patterns, immutable
WAD header access, application STOP and scope teardown. Three runs took
31.654065441 / 32.031896194 / 32.049854316 seconds, including loader validation,
audits and queries. These are **not Doom render times**. Framebuffer hash is
1352365901 and palette hash 1637009093. Port allocation peak is 6,356,612 bytes
in six blocks; this excludes the separate cache/bounce allocation (16,896 bytes),
image/admission storage, retained proofs, arena guards and RTEMS stacks.
`engine-results.json` preserves the exact reports. All rejection markers stayed
zero; image bytes were checked again after return; all consumers drained.

`--doom-engine`, `--dispatch-atomic` and `--wad-poll` remain explicit opt-ins.
No idle-owner, arbitrary task, extension or FPU admission is added. Full paired
audits, exact identities, loans, generation/STOP checks, CRC, five-second timeout
and both protected bootstrap windows remain mandatory. See
[dispatcher design](../../rtems/residentnet/README-DOOM-DISPATCH.md).

## Replay discrepancy: cause and repair

The physical first normal runtime probe returned 2710325741; native replay
returned 3. All three WAD reads and bytes were correct. The actual probe also
requires `ticks_ms()` to advance between entry and completion. The new native
polling service supplied all replies immediately, sometimes within the same
10 ms clock tick. Its correctly failing clock-liveness check caused the mismatch.

Only the native replay transport model changed: after supplying a recorded
reply, it waits 10 ms (retrying interrupted sleep). No-reply cases still take the
real unchanged five-second timeout. This is a transport-time model, **not a
measurement of physical latency**, and it is not used for performance claims.
The physical probe, firmware and expected return value were not changed.
`test_replay_clock.py` compiles the real probe and replay service with a modeled
clock: instant replies must fail; transport-delayed replies must produce the
exact oracle. Full capture replay then passes with ASan/UBSan.

A second verifier correction ties engine WAD rejection counts and sequence IDs
to the preceding validated cache report: earlier deliberate error tests left
four rejections, so zero was an incorrect initial assumption. Engine sequences
must continue exactly as 29, 30, 31. Full replay independently validates the
cache baseline; mutation tests continue to reject altered evidence.

Replay is not an i960 emulator: native engine entry models already independently
validated physical reports and exercises real C gate/WAD/ownership code. Physical
execution supplies the private Newlib/preflight evidence. These proofs do not
claim host/card Doom frame equivalence.

## Reproduce the accepted replay

After extracting `accepted-atomic.tar.gz` into `$capture_root`, supply the pinned
Freedoom phase-1 WAD (SHA256
`7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d`):

```sh
python3 rtems/residentnet/verify_upload.py "$capture_root/live-atomic" \
  --doom-heap --doom-shared --doom-runtime --wad-poll \
  --wad "$wad_path" --entry "$capture_root/residentnet/entry/runtime-probe.bin" \
  --output /tmp/doom-upload-replay.json
make -C rtems test
```

Use the current committed verifier for replay; the archive intentionally retains
exact physical-run sources from before the replay-only corrections.

## Performance and remaining work

`performance-notes.json` contains exact matched-probe timings and limitations.
The ratio of means is about 3.50× from two normal samples per profile on different
boots with combined dispatcher/polling changes; it is not an isolated speedup.
The timeout probe remains 5.133 seconds. `first-frame/` profiles the older 32-bit
host engine/cache, not the new private Newlib engine on the card. Grouped cache
miss analysis predicts fewer requests without fewer data bytes; no batching
protocol has been deployed.

Step 1 is closed: diagnose, accept, replay and record the baseline. Next is a
bounded negotiated WAD batching prototype with the same validation and STOP
contracts, followed by actual bounded Doom initialization, first-frame capture,
deterministic comparisons and browser input/output. Those are separate steps.
The accepted production autonet/IPv6 service was restored after reboot;
`service-restored.txt` records its read-only recheck. Do not unload its retained
exclusive module to start another test; coordinate ownership first.
