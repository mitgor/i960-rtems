> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Larger exact-build admission and owned engine preflight — 2026-10-12

**Later acceptance:** [the dispatcher/polling follow-up](../doom-progress-20261012/README.md)
diagnosed the failure retained below and accepted the diagnostic preflight with
full audits and cleanup. This archive remains the original failed-batch record.

**Not physically accepted for execution.** Native admission and private-libc
preflight tests pass. The card refused both CRC-valid modified images, but the
batch hit interrupt/drain fault bit 64 while uploading the clean image, before
its entry ran. No Doom initialization, game tic or browser frame is claimed.
The production IPv6 HTTP service was restored after reboot and returned HTTP 200.

## Candidate and protection

The engine + private Newlib/port has zero unresolved imports. Three independent
links match the canonical relocation recipe. It has 432,164 initialized bytes,
322,272 BSS bytes, a 754,448-byte span and 13,175 internal R_960_32 sites.
The 52,700-byte relocation-offset list is uploaded as a fourth segment. Image,
metadata and immutable text SHA256 identities and exact geometry/entry/result
bounds are compiled into the kernel; host CRCs remain transport checks only.

- Template SHA256: `d99d07de1c6740a1b44214bb68f54616b773790d8d5f419dff76cf810bc54fa5`.
- Object SHA256: `e0512f7b73c23cb109f80ca73ff7cd42ca55db0204c61da78aaeff2ac0adacc7`.
- Metadata SHA256: `1f63930bb648a883290dc0537bf441eed8fce4a90603182d2ac4e85cbee97cee`.
- Admission allocation: 807,148 requested bytes, 807,184 including arena guards/alignment.
- Physical kernel SHA256: `b9e2a03d414f67586605c4658ac84563598f242121e885607f437bbdd9bfbe42`.
- Physical module SHA256: `9cf9a281305711e1a7737393f4e3d722944c94d5c005a73fd68c54d5045ecc67`.

SHA/admission code uses 3,232 bytes at `c0f8c000..c0f8cca0` in the existing
bootstrap grant. BSS ended at `c0f8ba50`, leaving 1,456 bytes before that window.
Upper upload code used 30,192 bytes. Both windows remain protected by full
paired host audits and target page hashes; the physical report shows 142
protected pages. No grant or mutable audit exclusion was enlarged.
`link-engine.ld` now makes this reservation specific to the opt-in engine build;
its contents match the tested linker layout. A final source rebuild, including
automatic installation of the host admission files, produced the identical
physical kernel SHA256 above. The standard upload linker remains
unchanged. The physical archive retains the exact earlier filename/layout.

## Native execution and RAM layout

The actual 32-bit private Newlib preflight, guarded heap and WAD backend pass
ASan/UBSan for normal / STOP / normal and owned sleep termination (exit 210).
It verifies real `%lld`, float and `%lln`, allocates/checks 6 MiB, emits the
known frame/palette through the port, reads an IWAD header and cleans up.
Independent byte oracles give frame hash **1352365901** and palette hash
**1637009093**. The native port's peak is **6,356,596 bytes / 6 blocks**;
this excludes the backend's direct 16,896-byte cache/bounce allocation and
arena guards. It is not a card memory/performance measurement or a Doom frame.

A second native layout experiment reproduces the old retained-proof placement:
a 320 KiB initial image followed by a 6 MiB temporary proof puts retained
buffers where they split the free span needed after the 807 KiB engine arrives.
Aggregate free bytes are insufficient evidence of a contiguous zone. Reserving
**1 MiB** during proof setup places those buffers beyond the future image/zone;
the native preflight then succeeds with both retained buffers still present.
The engine host harness now uses that reservation. This host-only correction
was made after the failed physical batch and remains pending physical acceptance.
Allow about 1 MiB remaining before allocator guards/other consumers, rather
than claiming all the 8 MiB arena is available to Doom. Actual startup allocations
and lifetime are still unmeasured with this port.

## Physical failure, exact boundary

`failed-live.tar.gz` contains exact tested sources, target/module, logs and
full raw captures. Previous runtime/cache/relocated/owned proofs completed.
UPL1 command 18 replies were no-image refusal 1, altered-code refusal 2 and
altered-metadata refusal 2. No successful command 18 occurred.

The first failing snapshot was **tick 46,462**, state 1/reason 0, with
`switch_fault = 64`. The task ISR sets this bit at `slot_bad` when `_Thread_Executing` is
unregistered or its saved ISR continuation is still active. The controller also
uses bit 64 for final large-RAM/drain failure. Active state/reason 0, unfinished
workers and clean RAM/protection diagnostics favor the ISR rejection path; this
is an inference, not a captured branch identifier. The two ISR rejection paths
also share the bit. Add a first-rejection reason snapshot before claiming its
exact cause. At that snapshot code/upper-window protection and RAM guards
reported no errors. Do not infer a hardware fault, an executed engine failure,
idle-task admission, or a clean STOP drain from these values.

The host thread subsequently encountered **EPROTO (71)** on the next uncertain
upload. It retained the exclusive resources and did not retry/reclaim.
After archiving, reboot released the session. The accepted owned exit proof
in the preceding batch remains separate and valid.

`partial-replay.json` replays **3,580 completed commands / 8,355 logged PIO
ioctls** through the actual native upload/arena/heap/WAD/owned/SHA admission core.
The uncertain write is explicitly excluded. It verifies both authenticated
refusals and 328,352 known bytes of the partial clean image. Native final cleanup
is modeled; it does not establish physical drain. Seven altered-prefix evidence
cases are rejected. Packet replay validates **525 packets / six IPv4+IPv6 rounds**
before failure. It does not promote the failed batch to acceptance.

The separate positive native gate test verifies digest/metadata/BSS/STOP refusal,
modeled normal/cancel teardown and quarantine after changed code or failed scope.
It does not execute i960 code. The eleven-case positive capture mutation suite
is prepared but **not run**: there is no accepted engine capture yet.

## Artifacts and reproduction

`engine-build-native.tar.gz` contains exact final engine/port/library binaries,
source inputs, build hashes/patch, three linker oracles and sanitized native
preflight binary/results. `admission/` exposes the template, relocation offsets,
manifest and small trusted header. `failed-live.tar.gz` preserves the rejected
physical batch. Other JSON/log files are independently derived verification.
The upstream Doom/Newlib/WAD inputs remain pinned by the earlier artifacts.
No visitor statistics were copied into Git.

Extract the failed archive and run:

```
python3 rtems/residentnet/verify_upload.py ROOT/live --doom-heap --doom-shared --doom-runtime --partial-engine --wad FREEDOOM1 --entry ROOT/residentnet/entry/runtime-probe.bin --output partial.json
python3 rtems/residentnet/verify_engine_failure.py ROOT/live --output network-prefix.json
python3 rtems/residentnet/test_engine_partial_evidence.py ROOT/live --build ROOT/residentnet/entry/engine --wad FREEDOOM1 --output tamper.json
```

The native private-libc/layout test uses `engine/test_native.py` with the pinned
32-bit private host library. The gate test uses `residentnet/test_engine_gate.py
ADMISSION` on Linux with 32-bit sanitizers. Portable SHA/protection regressions
are included in `make -C rtems test`.

## Next physical acceptance

1. Coordinate with the RTEMS interrupt audit. Capture separate unregistered-task
   and active-continuation reasons without relaxing the rejection or allowing
   new ISR owners. Resolve that path before another full engine batch.
2. Use the corrected 1 MiB proof reservation and at least a 1,200-second bounded
   batch budget: earlier audited regressions plus five large uploads outgrow
   a short ten-minute test. Keep all paired audits, control and WAD checks.
3. Require normal / STOP / normal preflight, canonical text revalidation, exact
   frame/palette oracles, complete image/heap/IRQ drain, positive capture replay
   and eleven mutation checks. Reboot and restore production.
4. Only then advance to WAD batching, separately reviewed Doom initialization
   and engine allocation cleanup, first real frame comparison and browser input.

No further card retry was made after the timer-path rejection. The preflight
stays opt-in; production uses its unchanged accepted autonet payload/module.

Final handoff: production PID **10459**, boot
`fb571026-a145-4e76-a30c-240e3953dfe3`, bound `dac960auto`; public IPv6 HTTP
returned 200. The exclusive test resources were released by reboot.
