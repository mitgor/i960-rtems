# Live execution probe sources

Read [ROM-FETCH-LIVE.md](../../ROM-FETCH-LIVE.md) before using these files.
The final successful RAM callback is `flash_ret_probe.s` /
`flash-ret-probe.bin`: it calls a stock `RET` at physical flash address
`FEFB022C` and returns status `017F`. `ram_status.s` is the first-stage
status `017E` handler. `icctl_control.s` and `ram_call_control.s` are the
successful controls from attempts 3 and 4.

`start.s` / `romfetch.bin` are preserved **only** for the failed attempt 2.
Their `FEFC8208` target came from a disassembly base that did not match the
full card image's physical address. It timed out and is excluded from the
default Makefile target. Do not run that binary on hardware.

All binaries are 64 bytes or smaller, built for `-mrp` at fixed external
DRAM addresses. They are not a firmware update. The exact live module and
source for each run are archived separately under
`artifacts/romfetch-live-20261010/`.
