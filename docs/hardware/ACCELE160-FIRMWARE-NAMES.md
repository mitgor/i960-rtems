# AcceleRAID 160 firmware experiment names

Use these names in new plans, test records, and status updates. Existing file
names and SHA-256 identities remain unchanged.

| Name | Meaning | Persistence and boot path |
| --- | --- | --- |
| **Firmware injection v1** | The October 2026 stock Mylex image with the added `0x8f` RAM admission handler. The host uploads RTEMS and Doom into card RAM through that handler. The current spare's candidate is the same accepted October image except for four serial-number bytes. | Handler is flashed and survives a cold boot; stock Mylex reset, x86 option ROM, and RAID runtime remain. RTEMS and Doom are uploaded into RAM for each session. |
| **Ram injection v1** | The November 2026 flashless installation of that same handler through the stock `0x8f` entry, followed by RAM uploads of RTEMS and Doom. | Handler, RTEMS, and Doom are volatile. The card's stock flash is left intact; a cold boot removes the handler. |
| **native firmware handler v1** | The earlier native RTEMS firmware with a host-facing RAM staging/handler path and no on-card flash writer. | Native RTEMS replaces the stock RAID runtime at boot. The handler can receive RAM data, but this version cannot reflash itself. |
| **native firmware with flash tool** | The planned native RTEMS firmware with the host-facing handler plus an on-card Intel S3 flash writer and update protocol. | Intended to boot native RTEMS and accept later firmware updates from the host. The writer remains experimental until its electrical write path and recovery behavior pass on hardware. |

The word *handler* refers to different command paths in these families:
Firmware injection v1 and Ram injection v1 use the **stock firmware's modified
`0x8f` dispatch**. The native images use the **native RTEMS host interface**.
Neither kind of RAM upload by itself implies an on-card flash writer.

Evidence: [October handler acceptance](../../artifacts/current/accele160-ram-admit-20261017/README.md),
[October Doom acceptance](../../artifacts/current/doom-persistent-20261018/README.md),
[Ram injection v1 live test](../../artifacts/current/accele160-volatile-stock-20261121/README.md),
[native firmware implementation](../../rtems/accele160/native_rom/README.md), and
[Firmware injection v1 candidate for the current spare](../../artifacts/current/accele160-october-handler-current-spare-20261121/README.md).
