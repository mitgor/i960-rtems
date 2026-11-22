# Native updater offline recovery and readback candidate

The card-specific [image](native-updater-verified-slot5-10112502260.bin) for
Slot 5 serial `10112502260` has SHA-256
`2aa1d5a8dfbfc99be8d9b1c302a6adaf30ad9f569a6b3ff2a620289a3dab9fe2`.
It was packed from that card's own stock read. The reset block, x86 option
ROM, and descriptor are unchanged. The [manifest](update-manifest.json) from
the currently installed passive image changes only the 64 KiB block at
`0x40000`; the [offline host review](host-offline-review.json) checked the
complete base and target bytes.

UPD1 protocol version 2 keeps base and target SHA-256 at control page byte
offsets 128 and 160, separate from its state and version words. ABORT (4)
clears an acknowledged RAM-only session so staging can restart with the next
sequence number. It refuses a partial flash-write state, and the host refuses
an unacknowledged command. The separate
`host/accele160/flash/abort_native_update.py` tool makes recovery explicit.

The dormant `accele160_update_apply` path now independently reads back every
byte of each changed 64 KiB block after its writer callback. A simulated
writer that reports success after copying only 1,024 bytes produces
`ACCELE160_UPDATE_VERIFY_FAILED`, leaves state 4, and cannot be aborted.
This is a block-level fault test, **not** an E28F008S3 bus or timing emulator.
The Intel [28F008S3 family datasheet](https://netwinder.osuosl.org/pub/netwinder/docs/nw/flash/29059805.pdf)
describes the sixteen 64 KiB blocks and command/status behavior; voltage,
locking, erase, timing, and reset interactions still need a qualified writer.

The [compiled interpreter gate](interpreter-updater-gate.json) submitted all
256 chunks, sealed, and aborted the session. The
[QEMU POST gate](qemu-post-gate.json) reached its boot marker after PCI
configuration retry was released. C admission/service tests passed with
AddressSanitizer and UndefinedBehaviorSanitizer; the Python host tests
passed. These are offline model results.

The later [Linux guest gate](../accele160-upd1-linux-guest-20261120/README.md)
also passed a full transfer with the production Python staging class through
virtual PCI BAR0, including recovery from an interrupted process and stale
PIATVR mapping.
The later [Linux guest fault gate](../accele160-upd1-linux-faults-20261120/README.md)
passed pending-ack rejection, corrupt-chunk rejection, and fresh-process
recovery after an accepted chunk. The independent
[S3 command-model replay](../accele160-s3-model-20261120/README.md) reached the
reviewed image through one modeled block erase and byte programming, with full
array readback. Neither result qualifies physical flash access.

The installed passive card has no UPD1 endpoint, and this service has no
linked flash writer. No live card was touched. This image is **not cleared for
flashing**. The prior `accele160-native-updater-recovery-20261120` image was
built before the independent readback check and is superseded here.
