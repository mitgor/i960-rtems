# Working Firmware injection v1 card returned to Slot 5

On 2026-11-22 the user removed an as-yet unidentified spare that stopped the
HP Z400 before the normal beep, then installed a known working card. The
unidentified spare was not accessed or flashed during this session. Its
firmware contents and reason for stopping POST are unknown.

The HP then booted Linux. On boot ID
`4b10bf1b-7fcb-4d07-b52d-88c62a334a3c`, exactly one AcceleRAID 160 was
present at `0000:37:09.1`, PCI device `1069:0050`, subsystem `1069:0054`,
revision `02`. The pinned read-only `myrsread.ko` first bind passed; the peer
slot `0000:37:04.1` was absent. Two independent full selector-9 READIMAGE
captures completed with status, residual and guard changes all zero. They
were byte-identical, 1,048,576 bytes each, SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
This is the exact [accepted October Firmware injection v1 image](../accele160-ram-admit-20261017/README.md).
The card descriptor at `0xe0384` contains serial **`10112500320`**.
Its archived October preflash stock image was
`93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094`.

Full `read0/` and `read1/` captures, including the bytes, are retained
locally and on the remote at `/home/mit/i960-working-injection-20261122-4b10/`.
Only the small receipts need to be tracked in Git. No STOREIMAGE,
FLASHIMAGE, RAM injection, or firmware modification was performed.

The card is a useful known-good baseline. It is not the previously failing
stock card serial `10112504772`; that card's two FLASHIMAGE attempts returned
`80/16` and left stock flash unchanged. The unidentified no-beep spare should
be labeled and its flash read twice with the external programmer before
assigning it a candidate or treating it as a blank stock card.
