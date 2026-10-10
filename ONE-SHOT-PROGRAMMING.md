# One-shot programming harness — 2026-10-10

**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


**Implemented; native fault tests and the live non-programming rehearsal pass.**
The card's flash remains unchanged. Original staging RAM, command dispatch and
temporary code were restored; the module was unloaded after capture validation.

Implementation and operator instructions: [host/program/README.md](host/program/README.md).
The exact built module, generated sources, six complete image captures, RAM/table
captures, kernel/transaction logs and final state are archived in
[artifacts/one-shot-harness-20261010](artifacts/one-shot-harness-20261010/).
[validation.json](artifacts/one-shot-harness-20261010/validation.json) confirms
105 clean commands, full candidate CPU CRC `2012D01F`, complete stock restoration,
and zero programming doorbells. The remote build is
`/home/mit/i960-one-shot.niGXKl/` on kernel `6.8.0-138-generic`.

## Implementation

`one_shot.h` contains the exact fixed mailbox transport and shared state machine.
The command is `2B`, fresh transaction ID, subcommand 1, boot-block flag zero,
with mailbox bytes 4–12 zero. The irreversible boundary is recorded before the
MMIO doorbell. The state machine rejects duplicate attempts, distinguishes a
pre-submission refusal from uncertain/matched failure, and never retries.

`program_kernel.h` connects that state machine to MMIO and the existing paired
full-image readback. `build.py` generates a fixed module variant containing the
validated CPU CRC probe. It preserves the preflight sequence and restores the
stock command-table entry and both RAM code sites before the programming gate.
Before submission, failures can take the existing staging rollback path. After
submission, that path is prohibited because stock programming may have freed
staging. The normal command interface also refuses uploads/custom dispatches
once submission has happened.

Programming is disabled by default. Enabling it additionally requires the exact
candidate hash as an activation token. A wrong token was tested on the PC and
rejected before driver registration; the module and debugfs directory remained
absent. This was an intentional parameter-validation test, not an approval error.
The enabled path runs asynchronously and remains pinned until reboot even if
preflight fails. Its timeout retains resources; it never resets/reboots the card.
The operator guide describes progress reporting and final-state interpretation.

## Tests and results

- Shared transport/state code: all 64 combinations of stale completion, busy
  input timeout, programming timeout, wrong completion ID, device error and bad
  readback; plus duplicate rejection, invalid tags, readiness gates and default
  dry-run. Exact mailbox bytes and the before-doorbell state boundary are checked.
- Generated transaction: 122 scenarios exercise dry-run and modeled success,
  CPU verification failure, dirty dispatch, refusal, uncertainty, device failure,
  bad readback, and known/uncertain failures at all 57 data-command boundaries.
  Assertions enforce no rollback after submission and a fresh-allocation model
  for successful readback. These tests substitute hardware/CPU/hash models;
  they do not emulate physical flash timing or prove actual programming.
- Native tests ran with AddressSanitizer and UndefinedBehaviorSanitizer.
- The Linux module compiled with `W=1`; only the existing compiler-name/BTF
  informational messages appeared.
- The exact generated module ran on the real card with programming disabled.
  All 105 commands completed with matching IDs and intact DMA guards. Full DMA
  SHA256 checks and the CPU CRC passed. State 2 (`DRY_RUN`) had `submitted=0`.
  All stock RAM was restored and the module unloaded successfully.

## What remains

The real `2B/1` command, enabled worker's complete hardware transaction, flash
readback after programming, and patched boot hook have not been exercised.
The fresh-readback contract is based on the pinned stock firmware's traced
free/clear/reallocate/byte-copy path; simulation covers its host-side handling.
No recovery test was performed or added.

The next hardware milestone is one explicitly enabled programming run, preserve
its captures, require verified full flash readback, then reboot and check stock
firmware health plus `0x6F -> 017E` from the new `FEFE001C` handler. Do not describe
a successful rehearsal or native test as successful flashing. Existing candidate
manifests remain `flash_ready: false` and preserve their creation-time provenance.
