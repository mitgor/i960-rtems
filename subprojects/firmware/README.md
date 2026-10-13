# Firmware: preserve, patch, boot

The accepted patch extends the existing firmware with a returning opcode 0x6F
handler. It does not strap the card into reset mode 0. RAM programs and RTEMS
then load after Linux starts, without reflashing for each application.

| Step | Implementation / instructions | Evidence |
| --- | --- | --- |
| Identify and dump stock | [dump module](../../host/dump/README.md), [snapshot recovery](../../docs/firmware/SNAPSHOT-RECOVERY.md) | [original/vendor/full ROM inventory](../../artifacts/ROM-INVENTORY.md) |
| Understand the boot and mailbox | [protocol](../../docs/firmware/FIRMWARE-PROTOCOL.md), [ROM hook](../../loader/romhook/README.md) | [flash-fetch experiment](../../docs/loader/ROM-FETCH-LIVE.md) |
| Build and rehearse candidate | [programming preflight](../../docs/firmware/PROGRAMMING-PREFLIGHT.md), [one-shot harness](../../docs/firmware/ONE-SHOT-PROGRAMMING.md) | [preflight artifacts](../../artifacts/programming-preflight-20261010) |
| Program once and verify | [harness](../../host/program/README.md), [accepted result](../../docs/firmware/FIRMWARE-PROGRAMMED.md) | [programmed ROM](../../artifacts/programmed-rom-20261010) |
| Load applications | [runtime loader](../loader/README.md) | [software-loader artifacts](../../artifacts/software-loader-20261010) |

The programmed full-image SHA256 is
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
The 16 KiB boot block remains stock. Firmware/version, exact preimage and board
checks belong to the programming contract; an image from another card is not
interchangeable merely because its CPU says i960.

Recovery remains untested. Keep [serial setup](../../docs/firmware/SERIAL-RECOVERY-SETUP.md),
[boot recovery](../../docs/firmware/BOOT-RECOVERY.md) and the
[coexistence research index](../../docs/research.md) with the historical evidence.
A currently patched card must use postboot validation, not a stock-only rehearsal.
