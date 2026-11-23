# Current card native flash attempt, 2026-11-23

The user elected to risk the working Slot 5 card `10112500320` while other
spares await restoration. Its installed Firmware injection v1 image is
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The corrected native firmware with UPD1 and the Intel S3 writer is the exact
1 MiB candidate `b35b1e8312336532fae9175fdc3d0d0be7b80b14281434f42af1db294662c695`.
The card's stock FLASHIMAGE path previously succeeded when Firmware
injection v1 was installed. The complete previous image is archived for
external-programmer recovery.

The one-shot `flash_native_spare.py` path now pins this exact installed and
candidate pair, Slot 5, the previously used FLASHIMAGE module, same-boot
full reads, STOREIMAGE and independent full staged readback. It creates a
persistent attempt marker before issuing the physical command. The marker
prevents an accidental second call through this wrapper; it cannot make a
partial erase recoverable. On failure the module and command storage are
retained for inspection. On success, a cold power cycle and independent full
readback would be the strongest persistence check. Native RTEMS does not
answer the stock READIMAGE mailbox, so its own UPD1 BEGIN hash is used as a
narrower check below.

On boot `3937ce9f-bdeb-4f8a-8787-a77cc0f6ba8b`, two guarded full reads
matched the installed Firmware injection v1 image. STOREIMAGE completed
status 0 and an independent full staged READIMAGE matched the native
candidate byte for byte. The single FLASHIMAGE request then completed in
34.324 seconds with host status 0 and residual 0; the flash module was
released and unloaded. The [compact preboot receipts](preboot/) are archived
here, while complete 1 MiB reads remain on the remote under
`/home/mit/i960-writer-stage-20261122/fi1-native-3937/`. The PC was sent a
power-off request to force the next test to start from a cold boot. The
command status alone did not verify persistent bytes or native startup.

## First cold boot of the native updater image

The user powered on the same sole Slot 5 card. Linux boot ID
`9c7104a9-660d-4db9-8b41-3308111f06d5` enumerated RAID function
`1069:0050` at `37:09.1`; no driver was bound. At uptime 180 seconds, one
separate 32-byte `PCI0` BAR read reported bridge EBCR `0x0348` (PCI retry
released), option ROM hidden, and the expected PCI function identities.
Its following 46 one-second PCI samples retained the same response. At
uptime 235 seconds, a separate 64-byte status read reported stage-two result
`0x2000` and RTEMS `PASS`; its following 46 PCI samples were also stable.
The offline [native boot review](postcold-9c71/native-boot-review.json) passed
all six checks.

At uptime 302 seconds, the read-only UPD1 control probe found magic `UPD1`,
protocol version 2, and idle state. It restored PIATVR to `0xc0000000` and
the RAID function still responded. The [on-card digest probe](../../../host/accele160/flash/probe_native_digest.py)
then sent only UPD1 `BEGIN` with the candidate SHA-256 as its expected base.
`BEGIN` returned result 0/state 1, meaning the native firmware copied and
hashed the full 1 MiB flash and accepted that digest. `ABORT` returned
result 0/state 0; PIATVR and PCI identity were restored. The complete
[postcold receipts](postcold-9c71/) include the device probes and the
review. No updater `APPLY`, erase, or program operation was requested.

This proves a cold-booted native RTEMS runtime and a responding updater
service on card `10112500320`. The card-computed whole-image digest is strong
evidence that the candidate persisted, but it is not an independent bytewise
host readback. The on-card Intel S3 writer remains untested on physical flash;
the next physical update must be separately qualified before sending APPLY.
