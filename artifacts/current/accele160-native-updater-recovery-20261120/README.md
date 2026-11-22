# Native updater recovery candidate, 2026-11-20

This is an offline-built, card-specific image for Slot 5 serial `10112502260`.
The complete [candidate](native-updater-recovery-slot5-10112502260.bin) has
SHA-256 `6499d2c75cc640ef5d40c0399205fe238cbaa059ed339c544a3331261e283576`.
It was packed from that card's own stock read, and the reset block, x86 option
ROM, and descriptor are preserved. The [manifest](update-manifest.json) from
the currently installed passive image changes one 64 KiB block, `0x40000`.
The [host review](host-offline-review.json) checked the full base and target
bytes against that manifest without contacting the card.

UPD1 protocol **version 2** places the base and target SHA-256 at control
page byte offsets 128 and 160. Version 1 put them over the state, next-chunk,
and version words, making session restart unreliable. The host tool rejects
version 1. Commands are BEGIN=1, CHUNK=2, SEAL=3, ABORT=4. ABORT clears a
RAM-only session, including an interrupted transfer or a failed final hash,
and leaves the monotonically increasing command sequence intact. It refuses
state 4 (partial flash write). The host refuses to abort while a command is
unacknowledged, because the result is uncertain. The separate
`host/accele160/flash/abort_native_update.py --live --receipt ...` tool
provides explicit recovery. The stage tool now accepts an idle service whose
last acknowledged sequence is nonzero.

The [compiled i960 interpreter gate](interpreter-updater-gate.json) passed:
RTEMS reached `PASS`, rejected malformed and out-of-order chunks, admitted all
256 correct chunks, sealed the target, and acknowledged ABORT with state 0 and
next chunk 0. The [QEMU POST gate](qemu-post-gate.json) passed: SeaBIOS reached
the marker boot sector after the virtual card released configuration retry.
The C admission and service tests passed under AddressSanitizer and
UndefinedBehaviorSanitizer; seven Python host tests passed.

No flash writer is linked to this service. The installed passive image has no
UPD1 endpoint, so this candidate cannot be uploaded through UPD1 on the
current card. No live flash operation was performed. The interpreter and QEMU
results do not establish a safe in-system E28F008S3 programming path.

The earlier `accele160-native-updater-20261120` image uses protocol version 1
and is superseded by this candidate.
