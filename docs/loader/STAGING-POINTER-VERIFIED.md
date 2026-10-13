# Live staging-pointer verification — 2026-10-10

Latest: [RUNTIME-READ-VERIFIED.md](RUNTIME-READ-VERIFIED.md). Paired live reads verified entry bytes, board C0110780, alias C1000000 and 512 KiB callbacks. Hardened exact read allowlist passed; no upload/execution/recovery/flash.

**The pointer at controller RAM C0112A70 was read twice as C0F2C000.** This matches
the allocator prediction and establishes a working four-byte read outside the
normal 512 KiB staging window. It does not demonstrate arbitrary RAM writes,
code execution or entry into recovery.

## Fixed-purpose probe

`host/dump/dac960dump.c` adds opt-in `pointer_check=1`. The normal image-read bounds
remain unchanged. The command issuer itself now enforces the bounds, allowing
one exception only when internally armed: count 4, offset FF1E6A70.
There is no user-supplied target address, arbitrary opcode or upload support.

Before arming, the probe checks firmware 4.07-0-29, DRAM 01000000, pool bytes
00E72000, flash size 00080000 and unit field 0010. It then reads offset zero twice
with different host sentinels, requires identical 512-byte results, and checks
the known 16-byte stock ZIP header. Only then does it read the predicted pointer.
The first unexpected pointer value prevents the second read. After both match,
it disarms and validates Enquiry2 again. Errors stop the experiment; uncertain
completions retain the module/DMA resources as in the existing harness.

This gate is specific to the archived card/profile. The prefix and version check
are not a cryptographic authentication of the running firmware. Do not generalize
this exception to other boards or broaden it into arbitrary offsets.

## Observed result

Host mit@192.168.2.75, card 0000:37:09.1, kernel 6.8.0-138-generic:

| Transaction | Opcode | Count | Offset | Result |
|---|---|---|---|---|
| 1 | 1C | Enquiry2 | 0 | Matching profile |
| 2 / 3 | 20 | 512 | 0 | Matching ordinary staging reads |
| 4 / 5 | 20 | 4 | FF1E6A70 | `00 C0 F2 C0` both times |
| 6 | 1C | Enquiry2 | 0 | Matching profile afterward |

All six completion IDs matched; every status was zero and every DMA guard was
unchanged. Final result was 0 with pending=0. Captures were read with `cat`, then
the module was removed. Final checks confirmed both driverless controller and
module absence. No reboot, recovery command, firmware upload or flash occurred.
Normal command transport does write mailbox/doorbell registers and uses DMA;
this was not a passive PCI-config inspection.

The arithmetic is `(C0F2C000 + FF1E6A70) mod 2^32 = C0112A70`.
Combined with static handler dataflow and the returned pointer, the observation
supports the staging-relative wraparound interpretation. It does not validate
all possible local addresses or the upload direction outside staging.

## Reproducibility and tests

`artifacts/staging-pointer-20261010/` contains all seven debugfs files, a verification
manifest, exact executed source/header and the kernel module built for this kernel.
The captured result includes the exact mailbox words, IDs, DMA address and guards.
Do not reuse that module on another kernel.

The native guard test exercises the exact profile/address gate used by the module,
including mutated profile fields, unarmed access, wrong length/address, overflow,
and image-window boundaries. Kernel build with W=1 passed; 14 existing Python
capture/unpack/symbol tests passed. Run the native check with
`make -C host/dump test-guards`.

The live invocation used `pointer_check=1` with default `attempt=0`, length=512
and offset=0. Conflicting parameters are rejected. Existing normal-mode capture
validators do not validate this six-command experiment; its dedicated report and
raw transcript must be used instead.

## Next step toward execution

A useful next read-only experiment is to verify a small known instruction sequence
in the running firmware and read the board descriptor pointer/memory-alias value.
That would establish the actual callback table and address interpretation before
selecting a RAM payload location or modifying any callback. Keep such reads on a
small explicit allowlist, using this pointer check as a prerequisite.

RAM upload, cache synchronization, DMA quiescence and a correctly initialized
recovery handoff still require review. The preserved boot-block recovery monitor
and serial instructions remain relevant, but this result does not yet make a
failed custom-loader execution recoverable over SSH.
