> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Step-4 read-only dispatch observation

`live/` contains the transaction log and all active debugfs captures from the fixed `rom_table_check=1`
probe on `mit@192.168.2.75`, DAC960PG `0000:37:09.1`, 2026-10-10.
`live-validation.json` records the independent local validation. See
[ROM-HANDLER-STEP4.md](../../docs/loader/ROM-HANDLER-STEP4.md) for interpretation.
Unused scratch and DRAM-hook blobs were omitted. The exact probe
`dac960dump.ko` and its four build inputs are also archived.
The module was removed after capture; the controller remained driverless.
