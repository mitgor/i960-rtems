# DAC960PG controlled response experiment

This kernel capture harness recovered a validated 512 KiB image on our DAC960PG.
Read [SNAPSHOT-RECOVERY.md](../../SNAPSHOT-RECOVERY.md) for saved files, layout,
validation and the limits of a firmware staging snapshot.

Default mode issues only Enquiry2 (0x1C). `attempt=1` performs two bounded
LoadImage (0x20) reads. Direction is verified by vendor dataflow and live DMA,
but source identity is not: the buffer can contain previously staged host bytes.
Opcode 0x21 is no longer allowed. There is no arbitrary-opcode interface,
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

See [FIRMWARE-HANDLERS.md](../../FIRMWARE-HANDLERS.md) for the unpacked reference
handler analysis. `unpack_firmware.py` verifies and extracts the embedded method-6
ZIP offline; it requires Info-ZIP unzip. The kernel probe rejects reads past
0x80000, the PG profile supported by the fresh live capture. The prior 0x40000
limit applied a different startup profile. Main firmware and boot-block identity
are now verified; see SNAPSHOT-RECOVERY.md.
