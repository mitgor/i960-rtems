# Project review: in-system firmware dump

Reviewed 2026-10-10. Primary objective: read the installed DAC960PG firmware while
it remains in the computer, without an external flash programmer or first replacing
its firmware. This is a review and improvement list, not a working dump implementation.
No firmware commands, resets, flashes, driver changes, or new BAR mappings were
performed during this review. Remote access read existing vendor files and PCI
configuration/sysfs metadata, and ran existing emulator self-check executables.

## Current conclusion

**An in-system i960 firmware dump has not been achieved. It is not established
that every software route is impossible.** The failed StoreImage attempts are
useful observations, but their transport, command semantics, and maintenance-state
prerequisites need better evidence. Replacing the flash loader cannot solve the
problem of backing up the original firmware before that replacement.

The most promising next work is a trustworthy read-only kernel transport plus a
complete reconstruction of the vendor **RoadRunner** image-read call path. If that
path is boot-block-only, investigate its documented entry/exit conditions offline
before considering any recovery-mode experiment.

## Evidence checked

- Local sources: host tools and kernel probe, firmware image/decoder/stub tools,
  loader, emulator, game, build/toolchain scripts, and all project Markdown notes.
- Existing remote decoded `DAC960FL.EXE` is 377,472 bytes; SHA-256:
  `1be1c11f5e030be80cd55b5c9215734f472daf4ee651abd1da57284e4888c552`.
  Its symbol strings include `_StoreRoadRunnerImage`, `_ProgramRoadRunnerImage`,
  `_ReadFlashDescTbl`, and `_DACPVX_IssueCommand`. Symbol presence alone does not
  establish reachability, arguments, transfer direction, or controller-family dispatch.
- Read-only current PCI snapshot: controller `0000:37:09.1`, `1069:0010`, no bound
  driver; BAR0 `0xee000000..0xee001fff`; PIALR `0xffffe000`; PIATVR `0xc0000000`;
  ERLR `0xffff8000`; ERTVR `0xfefa8000`. Bridge EBCR low word remains `0x0018`.
  No remapping writes were attempted.
- Existing remote CPU self-check and native reference both print `RESULT=-135781`;
  line-clear equivalents both print `RESULT=200110`.
- A locally generated malformed ELF (`filesz=4`, `memsz=1`) causes an AddressSanitizer
  global-buffer-overflow in `host/emu.c:143`, with a 4,294,967,293-byte memset.
- UndefinedBehaviorSanitizer reports signed-left-shift undefined behavior in
  `host/ref.c:3`. Matching outputs therefore do not prove architectural correctness.
- No raw transcripts of the earlier StoreImage attempts were recovered from the
  current remote dmesg. Their reported results are in project notes; distinguish
  those historical reports from independently reproduced hardware outcomes.

## Prioritized improvements for dumping

### 1. Replace the categorical impossibility verdict with an evidence ledger

Priority: high. FINDINGS.md and FIRMWARE-PROTOCOL.md declare the route closed, while
other notes still describe it as feasible or awaiting parameters. Maintain one
current status page, with dated experiments and separate fields for observations,
inferences, and untested prerequisites. The defensible statement is currently:
“no transfer using the tested field-firmware command sequence; no direct flash
window in the current configuration.”

A command acknowledged with zero transferred bytes does not by itself prove the
opcode is read-only, implemented as a no-op, or unavailable in every boot state.
Likewise, a symbol-family census cannot prove that no relevant indirect call exists.

### 2. Repair mailbox completion handling before trusting another result

Priority: critical. `host/kmod/dac960probe.c:34–47`:

- Waits for MailboxFull to clear, but submits anyway if that wait expires.
- Does not account for a stale outbound completion before issuing a new command.
- Never reads or matches the status command identifier at BAR0+0x1018.
- Reuses identifier 1 for every command, making late completions harder to distinguish.
- Uses byte doorbell/mask accesses where the maintained PG driver uses 32-bit accesses.
  Match the supported access widths and acknowledgment sequence deliberately.

Build a serialized transaction state machine, refuse submission when busy, drain
only understood old completions, assign and match IDs, and report mailbox bytes,
ID, status, DMA address, and completion transitions. Compare against the production
PG implementation rather than deriving the interface solely from register names.
See the [Linux myrb PG implementation](https://github.com/torvalds/linux/blob/master/drivers/scsi/myrb.c).

### 3. Close the opcode interlock bypass and use an allowlist

Priority: critical. The module blocks integer `op == 0x22`, but `issue()` accepts
`u8`. For example `op=0x122` bypasses the check and truncates to `0x22` at submission.
Other potentially mutating opcodes are unrestricted. Validate the full numeric
range before conversion and permit only positively understood read operations.
Keep diagnostic/maintenance/register-write operations outside the default dumper.
Select one explicit BDF so module insertion cannot probe every matching controller.

This follows directly from the source; no bypass command was sent to the card.

### 4. Resolve the 0x2B interpretation before further experiments

Priority: high. The probe calls `0x2B/02` a flash-descriptor read. The maintained
V1 header instead names `0x2B` `MYRB_CMD_BGI_CONTROL` (background initialization).
This does not rule out a boot-block-specific reuse; it invalidates treating the
field-firmware interpretation as established. Reconstruct the vendor function's
actual opcode, subcommand, family dispatch, and firmware state first. The header
also explicitly names LoadImage/StoreImage/ProgramImage at 0x20/0x21/0x22, so notes
claiming there is no ProgramImage opcode must be qualified by family and path.
See [Linux myrb command definitions](https://github.com/torvalds/linux/blob/master/drivers/scsi/myrb.h).

### 5. Reconstruct the complete RoadRunner read transaction offline

Priority: highest research value. The decoded vendor binary is available; another
round of guessed mailbox parameters is unnecessary. Recover the symbol/overlay
format and map `_StoreRoadRunnerImage` to executable code. Trace its callers,
controller initialization, `_DACPVX_IssueCommand`, and `_ReadFlashDescTbl`:

- Confirm that this code is selected for DAC960PG rather than another family.
- Identify whether the argument selects an image, a chip-relative offset, or a local address.
- Confirm length units, chunk maximum, mailbox byte 12 meaning, and DMA direction.
- Identify any mode switch, controller-open handshake, or diagnostic precondition.
- Determine whether the operation returns a logical image, a staged RAM copy, or raw flash.
- Recover the exact reverse/exit sequence and the failures that leave the controller changed.

Commit annotated disassembly excerpts, binary hashes, and a field-by-field command
construction script. Separate RoadRunner mailbox code from FootBridge memory-mapped
flash code; do not generalize evidence across those families.

### 6. Examine boot-block and deployed firmware dispatchers

Priority: high, after item 5. The repository itself leaves boot-block-only handling
as an untested possibility. Analyze the decoded boot-block image and an exact
4.07-0-29 reference if available. Locate handlers for 0x21 and related state checks;
identify their image layout and execution architecture before disassembling them.
For compressed components, recover the decompressor and output-address map first.

A useful deliverable is an offline table of command availability by controller
family and boot state. Only consider a live recovery-mode transition if its entry,
exit, and persistence behavior are understood. Do not deliberately corrupt flash
checksums or program a different image merely to trigger recovery.

### 7. Make DMA lifetime and cleanup correct

Priority: critical. The probe frees its coherent buffer after a timeout, although
completion is unknown and the device may still DMA into it. A timeout is not DMA
cancellation. Preserve the buffer until completion or a hardware-supported
quiescence path proves the transfer stopped. Do not treat clearing bus mastering
alone as proof that all outstanding transactions drained.

Keep state in a per-device object, request/release PCI regions, restore saved IRQ
mask state, disable/restore device state on every failure path, and make remove
handle unresolved transactions. Replace multi-second busy-waits with bounded
polling appropriate to the register interface. These changes are necessary for
reliable measurements, independently of whether StoreImage eventually works.

### 8. Stop publishing sentinel data as a successful firmware dump

Priority: high. `dac960probe.c:64–85` copies every status-zero chunk even when its
0xA5 sentinel is unchanged, writes `/tmp/fwdump.bin`, ignores short `kernel_write`
results, and normally returns success even after command/file errors.

Separate raw experiment captures from validated dumps. For each experiment record
changed-byte counts, sentinel/guard checks, statuses and IDs, expected lengths,
checksums, and transport errors. Repeat a candidate read with different sentinel
patterns: genuine 0xA5/erased data must not be rejected merely because one pattern
matches. Any partial or uncertain result must remain explicitly unverified.

Prefer a device read/ioctl interface with userspace file writing, explicit output
paths, temporary-file plus atomic rename, checked writes, and an adjacent JSON
manifest. Validate `dumpmax` for negative values, overflow, and supported caps.

### 9. Define exactly what “firmware dump” means

Priority: high. Keep these separate:

1. x86 option ROM: already read through the ROM aperture; not i960 firmware.
2. Logical vendor firmware payload: may omit boot block, configuration, or unused sectors.
3. Boot block and other logical images: require their own selectors/validation.
4. Physical flash backup: every chip byte, bank, persistent configuration and sector.

The vendor firmware payload is 0x38000 bytes; that is not evidence that the flash
chip is that size. A 512-KB all-sentinel capture is not a chip image. A downloaded
4.07-0-39 package is not a backup of the installed 4.07-0-29 contents.

For a genuine backup, determine the bank/sector layout, read twice with matching
hashes, verify expected boot structures in the correct component, and account for
all regions. Hash equality alone is insufficient: two untouched sentinel buffers
also match.

### 10. Audit the current address map; deprioritize blind remapping

Priority: medium. Intel's manual reserves BAR0's first 4 KB for messaging; the
remaining inbound region follows ATU translation. The current PIATVR points to
DRAM, not flash. PIATVR/PIALR are PCI-read-only, though locally writable. Failed
host configuration writes are therefore consistent with the documented interface.
Record function, register, stepping, and access mode rather than assuming fn0's
EBCR and fn1's ATU are interchangeable. See Intel manual §§16.4, 16.7.20–21 and
[the RP/RD specification update](https://mark-ogden.uk/files/intel/publications/272918-019%20i960%20RP%2CRD%20IO%20Processor%20Specification%20Update-Jun98.pdf).

The on-chip DMA engine is only an alternative if its registers and local chain
descriptor memory can be reached without replacing firmware. No such access is
established in the current window. Treat DMA, ROM banking, and diagnostic memory
read paths as conditional feasibility studies, not ready-made dump procedures.
The ROM aperture's current mapping does not become a full-flash mapping merely by
reading beyond the option ROM file.

### 11. Use paired controls and preserve reproducible evidence

Priority: high. Each supported test should have an Enquiry2 control before/after,
unique completion IDs, full mailbox captures, DMA guard bytes, transfer timing,
firmware version, BDF, PCI configuration, kernel/module version and source hash.
Keep captures under an experiment directory instead of temporary dmesg-only notes.
Re-run only one evidence-derived parameter/state change at a time. Lack of DMA in
a well-instrumented test narrows hypotheses; it does not justify trying unrelated
opcodes blindly.

## Other project improvements

### 12. Correct the loader's impossible internal-RAM execution milestone

Priority: critical for hardware work. Intel manual §4.1 expressly forbids fetching
instructions from internal data RAM at 0x000..0x3ff. The current hello link address
0x200 and GO allowlist cannot execute on this CPU. Native dispatcher tests do not
model this fault. Withdraw that milestone, retain internal RAM for data/stack, and
move payload execution to verified external executable memory with proper startup.
The correction also applies to documentation added in the previous loader change.
See [Intel i960 Rx manual](https://mark-ogden.uk/files/intel/publications/272736-002%20i960%20Rx%20IO%20Microprocessor%20Developers%20Manual-Apr97.pdf), §4.1, printed page 4-1.

The loader also currently refuses flash READ addresses, so it cannot dump flash
even after installation. More fundamentally, flashing it first destroys the
original-backup premise. Keep it as a later code-execution project.

### 13. Harden the emulator before using it for firmware analysis

Priority: high. Validate ELF class, endianness, machine, entry, file bounds,
program-header sizes, `filesz <= memsz`, and overflow-safe RAM ranges; check all
reads/seeks. Add checked memory accesses and register-frame bounds. Unsupported
instructions, budget exhaustion, or faults must exit nonzero rather than reaching
`done` and reporting success. Fix signed arithmetic/shift undefined behavior and
architectural edge cases. Add sparse flash/MMIO modeling only if firmware analysis
needs it; the current game interpreter cannot validate peripheral behavior.

### 14. Make self-checks defined and independent

Priority: medium. The arithmetic reference and target test both left-shift signed
integers into overflow. Use explicit uint32_t wraparound and a defined signed
interpretation. Tests copied from the same line-clear algorithm share possible
mistakes; add independent fixtures and property checks. Document the supported
instruction subset rather than claiming two output matches prove the entire ISA.

### 15. Make builds reproducible and component-specific

Priority: medium. `build.sh` uses `scp host/*`, which now includes the `host/kmod`
directory and fails without recursive handling. It only builds the game target,
but later consumes pre-existing test ELF files rather than rebuilding them. It
also omits loader syncing and suppresses emulator warnings with `-w`.

Use explicit file manifests or rsync, clean target builds for both self-checks,
a root check target for host/game/loader, and a separate opt-in kernel/hardware
workflow. Record toolchain versions and source download hashes. The remote
cross-toolchain is available even though it is not on the local machine; loader
target validation can be done in an isolated remote build directory without
flashing or deploying a module.

### 16. Harden image tools and normalize artifact names

Priority: medium. `mkimage.py` preserves only the starting address of each table,
so writing inside a table after its first byte can evade its guard. Reject invalid,
negative, unaligned and empty placement; protect table intervals; reject non-filler
unless explicitly intended; validate header/trailer/IBR before patching. A failed
`--selftest` must exit nonzero.

`globalflash_decode.py --strip-header` removes 512 bytes but retains the ten-byte
trailer. Confirmed remote `407t39b0.bin` is 0x3800a bytes, not 0x38000; similarly,
`FWPJBBLK.bin` is 0x400a. Provide separate encoded-container, decoded-container,
and raw-payload outputs with explicit names, length checks, hashes and manifests.
Add tests for the transform and every extraction stage.

## Recommended order

1. Correct documentation and archive the existing evidence.
2. Harden the kernel transport, opcode policy, DMA lifetime, and capture validation.
3. Reverse the complete PG/RoadRunner read path and boot-state preconditions offline.
4. Reproduce an identified read operation with controls and full captures.
5. Validate logical-image coverage; only call the result a physical backup once every
   required region is accounted for.
6. Proceed with loader/code-execution work separately, after correcting its memory model.

There is currently no verified no-programmer procedure for the full flash backup.
There is enough unresolved protocol/state evidence to justify focused reverse
engineering rather than declaring the objective impossible.
