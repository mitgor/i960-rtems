# Exclusive-takeover research

User authorization (2026-10-11): RAID/SCSI need not operate during RTEMS;
reboot/power cycle may restore stock service. Preserve the cooperative approach
as a separate future option. No flash modification is needed.

## Documented controls

Primary source: Intel **i960 Rx Developer's Manual, 272736-002**,
[manufacturer document mirror](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF).
Local research copy SHA256 is in the artifact source manifest.

- Tables 20-3/4: CCR bit 0 disables DMA; CSR bit 10 identifies active channels.
  Disabling an active channel suspends it; PCI buffering can remain. The prototype
  therefore rejects any nonzero DMA control/status word before changing controls.
- ATU command bit 2 controls bus mastering: local 1204 for primary/DMA0/1,
  1298 for secondary/DMA2. Preserve memory decoding and use 16-bit accesses.
- Tables 18-2/9: SACR 104C bits 13:2 control six external secondary masters;
  priority value 3 disables grants. Require the internal-arbiter enable bit 16.
- Table 18-6 forbids disabling the external local-bus master. Do not write that
  LBACR field or assume it can isolate the cache coprocessor.
- Table 15-35: secondary reset (BCR bit 6) resets queues/secondary ATU and makes
  bridge transactions retry. It is a researched fallback, **not exercised** here.

## Related-chip lead

[Linux v6.8 FlashPoint.c](https://github.com/torvalds/linux/blob/v6.8/drivers/scsi/FlashPoint.c)
contains Harpoon-family halt/reset code (`hp_sys_ctrl`, `DRVR_RST`,
`FPT_hostDataXferAbort`). This is a lead for the BA-81C15, not proof that its
register layout, BAR or revision matches our board. No FlashPoint sequence was
copied into target MMIO code, and no guessed SCSI address was accessed.

## What the card established

The internal secondary arbiter is enabled. During isolation the primary command
changed 6→2, secondary command 0x16→0x12, and SACR 0x11558→0x13ffc. All DMA
control/status words stayed zero. The host message channel continued working.
The bounded experiments restored every captured word and normal loader cleanup.

This establishes a tested CPU/bus-isolation mode for the uploaded allocation.
It does not establish an active-DMA abort, prove an already-issued secondary
transaction drained, or document the MYL-86138 cache engine's internal completion.
No arbitrary DRAM reclamation, physical SCSI traffic or disk data operation was
tested. Keep the existing RAM allocation and reject active/error DMA at entry.
