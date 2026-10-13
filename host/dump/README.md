# DAC960PG controlled response experiment

## Full staging rehearsal

`stage_check=1 pointer_check=1 runtime_check=1` selects the fixed RAM-only
rehearsal, exclusive of all other experiments. It verifies the full stock
SHA256 before uploading three pinned patches, verifies the full candidate,
and restores and verifies stock. Unknown completion or unverified restoration
retains DMA/module state. The live run passed; see
[STAGING-REHEARSAL.md](../../docs/loader/STAGING-REHEARSAL.md). Use `validate_stage.py` to
revalidate the archived six full images and transaction transcript offline.


This kernel capture harness recovered a validated 512 KiB image on our DAC960PG.
Read [SNAPSHOT-RECOVERY.md](../../docs/firmware/SNAPSHOT-RECOVERY.md) for saved files, layout,
validation and the limits of a firmware staging snapshot.

Default mode issues only Enquiry2 (0x1C). `attempt=1` performs two bounded
LoadImage (0x20) reads. Direction is verified by vendor dataflow and live DMA,
but source identity is not: the buffer can contain previously staged host bytes.
Opcode 0x21 is available only in separately gated fixed-purpose scratch and
RAM-dispatch tests. The latter also uses a fixed `0x6F` completion. See
[ROM-FETCH-LIVE.md](../../docs/loader/ROM-FETCH-LIVE.md): the final probe successfully
called a stock flash `RET` after startup and restored all RAM. There is no
arbitrary-opcode interface,
program command, reset, or maintenance-mode action.

The harness selects one full PCI BDF, requests PCI regions, uses coherent 32-bit
DMA, validates fresh completion IDs, uses 32-bit PG doorbell/mask accesses, and
checks for transfer outside the requested region. It refuses an unknown pending
status, busy mailbox, or unvalidated Enquiry2. It exports copied captures through
root-readable debugfs blobs; userspace writes the files.

On an uncertain completion, the DMA allocation, mapping, regions and module
reference are retained. **Do not unload/unbind or reuse the controller then; a
reboot is required to reclaim the retained state.** Timeout is not DMA cancellation.
Normal removal restores saved interrupt-mask and PCI-command state. A negative
experiment can still bind successfully so its result can be read; inspect
`experiment-result` and `pending`, not just insmod's exit status.

## Build and control probe

Requires Linux headers for the running kernel and an already driverless controller:

```sh
make -C host/dump
sudo insmod host/dump/dac960dump.ko bdf=0000:37:09.1
sudo cat /sys/kernel/debug/dac960dump/result.txt
# Only if the result says pending=0, collect captures before removal:
sudo rmmod dac960dump
```

The repository's myrb unbind has previously wedged; do not use this harness on a
bound card or automatically unbind/rebind drivers to make it available.

For `rom_exec_check=1`, read ROM-FETCH-LIVE.md and the exact pinned
`rom_exec.h` bytes first. An earlier archived build called the wrong
physical flash address and timed out; the current build calls `FEFB022C`.
Use the live capture validator to inspect successful restoration:

```sh
python3 host/dump/validate_rom_fetch.py
```

The optional `flash_map_check=1` is read-only and fixed to three 64-byte
windows. It demonstrates the 8-bit flash bus: each 32-bit DMA word has one
ROM byte in its low lane and the address in its upper lanes. Do not interpret
those words as four consecutive ROM bytes.

## Captures and classification

For each attempted transfer, debugfs supplies `result.txt`,
`enquiry-before.bin`, `read-a5.bin`, `read-5a.bin`, and `enquiry-after.bin`.
Names beginning with read are experiment labels, not proof of direction or contents.
The original 0x21 captures are in ../../artifacts/dump-attempt-20261010/.
The working 0x20 captures are in ../../artifacts/dump-load20-20261010/.

```sh
python3 host/dump/validate_capture.py artifacts/dump-attempt-20261010
python3 -m unittest discover -s host/dump -p 'test_*.py'
```

The validator checks complete matched transaction IDs/statuses, guards, lengths,
firmware version, and sentinel behavior. It never automatically declares a physical
flash backup, even if two captures match. The live result was `no_host_buffer_update`. This detects lack of card-to-host
output; it cannot detect DMA reads by the card from host memory.

A small read uses `attempt=1 length=512 flash_offset=0`. Despite the historical
parameter name, `flash_offset` is an **image-buffer offset**, not a verified flash
address. Inspect and collect the result before removal, and do not expand reads
on the assumption that successful transfer means firmware. Historical captures contained a previous 0x5A upload pattern; the fresh-boot
capture begins with a valid EZAssist archive.

## Firmware-side evidence

See [FIRMWARE-HANDLERS.md](../../docs/firmware/FIRMWARE-HANDLERS.md) for the unpacked reference
handler analysis. `unpack_firmware.py` verifies and extracts the embedded method-6
ZIP offline; it requires Info-ZIP unzip. The kernel probe rejects reads past
0x80000, the PG profile supported by the fresh live capture. The prior 0x40000
limit applied a different startup profile. Main firmware and boot-block identity
are now verified; see SNAPSHOT-RECOVERY.md.

## Fixed staging-pointer verification

See [STAGING-POINTER-VERIFIED.md](../../docs/loader/STAGING-POINTER-VERIFIED.md). Opt-in `pointer_check=1` validates the exact profile and ordinary reads before permitting one fixed four-byte offset. Normal read bounds remain unchanged. `make test-guards` tests the shared address/profile gate. Existing capture validators do not classify the six-command pointer experiment.

## Fixed runtime read audit

`pointer_check=1 runtime_check=1` additionally verifies three exact code/globals/board regions after the pointer gate. See [RUNTIME-READ-VERIFIED.md](../../docs/loader/RUNTIME-READ-VERIFIED.md) and validate captures with `validate_runtime.py`. No upload opcode is supported.

## Fixed handler-site read

`pointer_check=1 runtime_check=1 dram_hook_check=1` performs the existing
profile/pointer/runtime checks, then reads exactly 64 bytes at local C0120000
twice with different DMA sentinels. It cannot be combined with `scratch_check`.
The exact offset and size are pinned in `staging_pointer.h`; it is read-only.
Validate with `validate_dram_hook.py`. See [DRAM-HOOK-AUDIT.md](../../docs/loader/DRAM-HOOK-AUDIT.md)
for the 2026-10-10 result and the unresolved lifetime-ownership question.

## Fixed ROM-hook dispatch-word read

`pointer_check=1 runtime_check=1 rom_table_check=1` performs the same profile,
pointer and runtime checks, then reads exactly four bytes at `C001F9BC`
twice. It cannot be combined with scratch or DRAM-hook modes. Validate the
15-command capture with `validate_rom_table.py`. The 2026-10-10 live value
was stock `C001FE98`; see [ROM-HANDLER-STEP4.md](../../docs/loader/ROM-HANDLER-STEP4.md).
This is a read-only preimage check, not proof of table-write visibility or
flash instruction fetch.

## Fixed reversible RAM scratch test

`scratch_check=1` additionally requires `pointer_check=1 runtime_check=1`. It allows only a fixed 16-byte test upload and restoration at offset 80010, plus 64-byte surrounding reads at 80000. See [RAM-WRITE-VERIFIED.md](../../docs/loader/RAM-WRITE-VERIFIED.md). Use `validate_scratch.py` for this 22-command capture; the runtime-only validator expects 13 commands. Dirty/unrestored scratch pins the module just as uncertain DMA does.
