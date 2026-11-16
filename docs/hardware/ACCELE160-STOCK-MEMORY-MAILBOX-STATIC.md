# Stock memory-mailbox transition: static evidence

This note uses the **installed AcceleRAID 160 runtime** captured after its stock loader in [`stock-runtime-c004d000.dis`](../../artifacts/current/accele160-timer-interrupt-20261025/stock-runtime-c004d000.dis). Its paired binary is `stock-runtime-c004d000.bin` (SHA-256 `9c6722ef6d77e69dfd28f88c29f8700b0ddc10c7a90111ab18946515287821be`). Addresses below are local i960 addresses. The older `artifacts/private-dumps/remote-analysis/firmware-unpacked.dis` is **not** interchangeable with this runtime: it does not contain this code at `c004e660`.

## Observed host boundary

The [Debian `myrs` guest receipt](../../artifacts/current/accele160-myrs-guest-20261116/README.md) records hardware-mailbox IOCTL `0x8e` (`SET_MEM_MBOX`), command ring 32 KiB, status ring 4 KiB, and health buffer 1 KiB. In the opt-in stock trace, the i960 completed `0x8e` with OMR0 `0x00000001` and outbound doorbell bit 0. After QEMU exposed that *observed* completion to the guest, `myrs` acknowledged it and wrote host IDB `0x10` (`MMBOX_NEW_CMD`). The saved first 64-byte guest ring slot held ID 1, opcode `0x20`, control `0x50`, and `GET_CTLR_INFO` (`0x01`). The current QEMU bridge only observed the slot; it did not deliver IDB `0x10` to the i960 or observe a ring response.

## Local MU doorbell path

`c004e870` reads local inbound doorbell register `0x1320` into `r5`. The dispatcher handles bits 0–3 first. At `c004e900`, `bbc 4,r5,c004e914` skips if bit 4 is clear. Otherwise `c004e904` loads the mailbox object pointer from `c03e5bd0`, `c004e90c` loads its `+0x50` callback, and `c004e910` branches through that pointer. There is no direct `0x10` host BAR decode in this code; the host-to-local mapping remains a model question.

Stock MU initialization at `c004e510..c004e5b4` stores object pointer `c048e700` into `c03e5bd0`. It installs `c004e660` at object `+0x4c`, `c004fcb0` at `+0x50`, `c004fcf0` at `+0x54`, and `c004fcd0` at `+0x58`. The `+0x50` default (`c004fcb0..c004fcc4`) returns without scanning a ring. A later callback replacement is necessary for bit 4 to process memory commands, but its write site and the post-`0x8e` callback value are absent from this saved disassembly window.

## Ring consumer and completion paths

Two installed-runtime loops, `c004fa50` and `c004fb20`, read the current entry pointer from mailbox object `+0x0c`, then test the entry's first word. The `c004fa50` loop calls `c0050480` with the entry pointer and length 4 at `c004fa7c..c004fa84`; the `c004fb20` loop calls `c000d920` with the entry pointer at `c004fb68..c004fb6c`. Both clear the entry first word, advance the current pointer by 0x40 with wrap using object `+0x14/+0x18`, pass the returned command object to `c004fd50`, and continue while the next entry is nonzero. `c004fd50` writes object `+0x58` into command object `+0x98`, then branches to the general request path `c004e380`. On the empty-entry path, both loops write `0x10` to local inbound doorbell `0x1320` (`c004fb00` or `c004fbe8`) and recheck the current slot, closing a possible arrival race. These are **static code paths**, not an observed handling of the saved Debian ring slot. The exact callback selection and the memory/DMA meaning of object `+0x0c` still need a post-`0x8e` stock object snapshot.

Stock completion code exposes both hardware and memory paths. The hardware mailbox completion routine `c004e7b0..c004e808` writes OMR1 at `0x131c`, OMR0 at `0x1318`, then outbound doorbell bit 0 at `0x132c`. Separately, `c004ec60..c004ed30` formats a completion in the memory status entry at object `+0x1c`: it stores an ID/status word at entry `+0`, a data/residual word at `+4`, advances the status pointer by eight bytes with object `+0x24/+0x28` wrapping, and calls `c004fa50`; it writes outbound doorbell `0x2` when its notification condition is met. Similar status-entry code appears at `c004ed40` and `c004ee50`. This shows a stock **status-ring construction path**, but does not establish that the saved `GET_CTLR_INFO` reached it.

## Evidence needed for a precise model

1. Capture the mailbox object at `c048e700` immediately after stock `0x8e` completion: at least offsets `+0x00..+0x68`, especially `+0x0c`, `+0x14`, `+0x18`, `+0x1c`, `+0x24`, `+0x28`, and `+0x50`. Preserve a before/after snapshot and hashes. This distinguishes callback and ring-address assignments.
2. In an opt-in stock emulator trace, deliver host IDB `0x10` to the **observed** local MU signal only after verifying the BAR-to-local mapping. Trace local `0x1320`, mask `0x1324`, vector dispatch, callback target, first ring read, and local `0x132c`. Do not synthesize status data.
3. Capture the guest status ring before and after a bounded stock step, plus output buffer for the `GET_CTLR_INFO` slot. A matching command ID and stock-written status entry would prove the full handoff.

Until these observations exist, `0x8e` completion and host `0x10` issuance are proven, but stock consumption of that command ring slot and a corresponding status write are not.
