# Current card native flash attempt, 2026-11-23

The user elected to risk the working Slot 5 card `10112500320` while other
spares await restoration. Its installed Firmware injection v1 image is
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The corrected native firmware with UPD1 and the Intel S3 writer is the exact
1 MiB candidate `b35b1e8312336532fae9175fdc3d0d0be7b80b14281434f42af1db294662c695`.
The card's stock FLASHIMAGE path previously succeeded when Firmware
injection v1 was installed, but this native candidate has never cold booted
or self-programmed on hardware. The complete installed image is archived for
external-programmer recovery if the new image does not boot.

The one-shot `flash_native_spare.py` path now pins this exact installed and
candidate pair, Slot 5, the previously used FLASHIMAGE module, same-boot
full reads, STOREIMAGE and independent full staged readback. It creates a
persistent attempt marker before issuing the physical command. The marker
prevents an accidental second call through this wrapper; it cannot make a
partial erase recoverable. On failure the module and command storage are
retained for inspection. On success, a cold power cycle and two full reads
are required before treating the write as persistent.

On boot `3937ce9f-bdeb-4f8a-8787-a77cc0f6ba8b`, two guarded full reads
matched the installed Firmware injection v1 image. STOREIMAGE completed
status 0 and an independent full staged READIMAGE matched the native
candidate byte for byte. The single FLASHIMAGE request then completed in
34.324 seconds with host status 0 and residual 0; the flash module was
released and unloaded. The [compact preboot receipts](preboot/) are archived
here, while complete 1 MiB reads remain on the remote under
`/home/mit/i960-writer-stage-20261122/fi1-native-3937/`. The PC was sent a
power-off request to force the next test to start from a cold boot. The
candidate's persistent flash bytes, native startup and updater are **not yet
verified** by this command status alone.
