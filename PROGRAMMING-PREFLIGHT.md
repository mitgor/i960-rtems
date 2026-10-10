# Programming preflight and live CPU staging test — 2026-10-10

**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Latest: [one-shot programming harness](ONE-SHOT-PROGRAMMING.md) is implemented in `host/program/`
(repository-root relative). Native transport/failure tests and a 105-command live
RAM-only rehearsal passed. Wrong activation token rejected before driver
registration; no programming doorbell issued. Full stock RAM restored and probe
unloaded. Exact binaries/captures are in `artifacts/one-shot-harness-20261010/`.
Actual flash programming, post-program physical readback and patched boot remain
untested. Recovery testing remains excluded.


**CPU-side candidate visibility passed.** The running i960 read all 524,288 bytes
through the programmer's `C1F2C000` source address and returned success for the
candidate CRC32 `2012D01F`. The complete stock staging image, dispatch table and
temporary RAM code were restored. The probe was unloaded. No flash programming,
reboot or recovery test occurred.

## Live evidence and its limits

The [archive](artifacts/programming-preflight-20261010/) contains six complete
image captures, RAM/table captures, exact source and `.ko`/`.bin` binaries,
transaction and kernel logs, [validation](artifacts/programming-preflight-20261010/validation.json),
and the final driverless PCI state. All 105 commands completed with matched
transaction IDs and unchanged DMA guards. The three execution statuses were
`017E` (baseline RAM handler), `017F` (candidate CPU CRC matched), and `0104`
(restored stock dispatch). All dirty/pending flags ended at zero.

This extends [STAGING-REHEARSAL.md](STAGING-REHEARSAL.md): paired full DMA
readbacks first established the exact candidate SHA256
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
The CPU callback then read every byte, computed reflected CRC32 using polynomial
`EDB88320`, initial/final XOR `FFFFFFFF`, and compared it with `2012D01F`.
CRC32 is a hardware visibility check, not a cryptographic identity check; the
separate full-image SHA256 checks establish the candidate identity.

The baseline callback executes `dcctl 2,0,g2` before the CPU probe runs. Therefore
this demonstrates a working sequence **with explicit cache invalidation**. It
does not establish that the alias is intrinsically uncached, or that omitting
cache maintenance works. The future programming transaction must preserve the
validated ordering. The CRC probe also invalidates D-cache before returning,
so dispatch-table restoration is visible on the next command.

The 128-byte probe resides at `C0FAC180..C0FAC1FF`; the baseline observation
window is `C0FAC100..C0FAC17F`. These windows do not overlap and both belong to
the existing extra staging block. They are temporary and must be restored
before any programming command that frees that allocation.

Sources: [loader/staging-cpu](loader/staging-cpu/). `build_probe.py` creates a
fixed variant of the existing harness; the ordinary host harness is unchanged.
The variant only accepts `stage_check=1` with its required pointer/runtime
checks, and still permits only opcodes `1C`, `20`, `21`, and `6F`. Inherited
`exec-flash-*` capture names refer to the second RAM slot in this experiment;
this probe does not call flash. Its command timeout is ten seconds to accommodate
the bytewise CRC loop. Both the target and Linux module compiled successfully.
The remote build directory is `/home/mit/i960-cpu-stage.1dGG7Y/`.

## Programming-path findings

Pinned source ranges and hashes are in
[programming-audit.dis](artifacts/programming-preflight-20261010/programming-audit.dis).
The exact machine-readable design is
[program-plan.json](artifacts/programming-preflight-20261010/program-plan.json).

1. `C004CFDC` calls staging accessor `C004D230`. At `C004CFE0..C004CFE8`, the
   programmer ORs the returned staging pointer with the word at `C011E230`.
   Live values `C0F2C000 | C1000000` yield **C1F2C000**. Program helper
   `C00507B0` reads source bytes with `ldob` at `C00507EC`; source increments
   once per programmed byte. This is the address and access width tested above.
2. The program mailbox is opcode `2B`, a fresh transaction ID, subcommand `01`
   at byte 2, **zero at byte 3**, and zeros at bytes 4–12. Byte 3 gates the
   additional boot-block erase/program operation. No DMA payload is consumed
   by this command; it programs the already populated local staging allocation.
   The dispatcher schedules `C004CDA0`, which calls the live board callback
   `C004CF80`. Normal scheduler readiness must still be satisfied.
3. The six unconditional erase/program ranges cover `[0,0x7C000)` (496 KiB).
   All six erase calls precede programming. The last 16 KiB boot block is
   omitted when byte 3 is zero. The helpers have no observed bounded device
   polling timeout; uncertain host completion must never trigger a retry.
4. The vendor updater reads the 352-byte descriptor (`2B/2`), increments the
   16-bit word at descriptor offset 8, writes the descriptor (`2B/3`), then
   programs (`2B/1`). Component storage also updates lengths/version/date fields.
   Our chosen custom full-image route preserves the descriptor byte-for-byte:
   the type-2 offset/length remain `30000/38000`, the version is unchanged, and
   the original descriptor is already included in the validated full image.
   The inspected programming callback does not test the update counter or require
   a preceding descriptor-write command. Preserving it is a deliberate departure
   from vendor bookkeeping, not a claim that the vendor updater accepted the MIMG.
5. At `C004D1EC..C004D200`, after programming, stock firmware frees staging and
   clears `C0112A70`. A subsequent `20` read invokes `C004D230`; when that pointer
   is zero, it allocates staging and copies the physical flash source from board
   field `+0C` using `ldob`/`stob` at `C004D284..C004D2A8`. This is a fresh physical
   source, unlike a reread of the pre-programming allocation. The bytewise copy
   also avoids the 32-bit DMA flash-bus low-lane artifact.

## Concrete programming/readback sequence

The following is the design for a dedicated one-shot programming harness; the
current probe cannot issue the programming command.

1. Repeat exact stock/profile/pointer/callback checks, stage the three patches,
   and verify both full candidate SHA256 readbacks.
2. Run the validated CPU CRC sequence. Restore stock dispatch and both temporary
   RAM code sites, confirming `6F` returns `0104`. Preserve the candidate staging
   image at this point (the rehearsal instead restores stock). No temporary
   callback may remain installed across programming or staging deallocation.
3. Submit `2B/1` once with boot-block byte zero. Use a dedicated state machine
   that distinguishes pre-submission refusal, known completion, and uncertainty.
   After submission, do not attempt the rehearsal's stock-RAM rollback: staging
   may already be freed. Retain DMA/module state on uncertainty; no automatic
   retry, reset or unload. Poll asynchronously and archive progress.
4. On matched success, trigger the normal `20` read path to obtain the newly
   allocated bytewise physical-flash snapshot, then capture the complete 512 KiB
   twice. Require the full candidate hash and unchanged boot-block bytes. A
   successful command status alone is insufficient. This post-program rebuild
   path is statically traced; it has not yet been exercised after a flash write.
5. Only after successful fresh readback, reboot to execute the metadata hook.
   Verify stock firmware health and that `6F` now returns `017E` from the new
   `FEFE001C` handler. Runtime RAM firmware/table state before reboot still
   belongs to the old boot, so the new handler is not expected to be installed yet.

The next implementation task is that one-shot state machine and its failure-path
tests. Keep `flash_ready: false` until the programming implementation is reviewed
and its preflight is complete. This turn resolves the live CPU visibility test
and specifies the descriptor/readback route; it does not establish successful
programming, boot-hook execution, or mode-0 functionality. Recovery testing
remains excluded at the user's request.

## Offline checks

```sh
python3 loader/staging-cpu/validate_live.py
python3 loader/staging-cpu/program_plan.py
python3 -m unittest discover -s loader/staging-cpu -p 'test_*.py' -q
```
