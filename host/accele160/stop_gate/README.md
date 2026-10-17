# AcceleRAID 160 sideband STOP gate

The stock `myrsread` direct-command companion holds `dcmd_mutex` until its
callback returns. A second ordinary mailbox command therefore cannot be
assumed to stop a pending RTEMS callback. This gate tests a separate host
write through the saved loader-page PCI aperture. It is an operation-11
addition to the accepted operations 1–10, not a persistent RTEMS supervisor.

The fixed command checks its exact nonce `0x161610b1`, epoch 1, magic, and
zero command word at `c000f960..f96f`. It writes READY at `f970` and polls
`f96c` after D-cache invalidation. Only `0x504f5453` is STOP. A matching
STOP writes ACK and nonce/epoch echoes at `f974..f97c`, then returns through
the stock success path. Exhaustion of the fixed 20-million-iteration budget
writes TIME at `f970` and returns through the stock unsupported path. The
command changes no timer, interrupt, vector, DMA, or allocator register.
The host saves and restores the complete erased loader page, checks all 512
allocator owner/count records, and leaves the command pinned if its
completion or state is uncertain. This is a bounded control-channel proof;
it does not stop an uncooperative RTEMS task, drain DMA, or establish timer
ownership.

`handler.S` is linked at `c000e1d8` with `handler.ld`. The flat image is
3,392 bytes and has no relocation entries. `audit.py` requires the stock
firmware, the accepted inventory image and handler, and the exact new
handler/prefix; it permits only loader-cave and two checksum-word changes.
The candidate SHA-256 is
`ef5635d38bf397ff13fa1140ef6265de0b300c70ad8b157c17427013a1d2abb5`.
Five one-byte mutations of its inputs were rejected offline. The Linux
companion is `stop_command.c`, built as `stop_command.ko`; an unfinished
command pins itself and `myrsread`, so never force-unload it.

On 2026-10-17 the guarded preflash read exactly matched inventory SHA-256
`9d5d4da2c283d10e1dee9c71ceb477f36e389cd0d0548764a3cc5f8a41a24c49`.
`STOREIMAGE` and an independent guarded staged read matched the candidate,
with zero residual and zero DMA-guard changes. The one-shot `FLASHIMAGE`
completed in 37.04 s with status/residual zero. After a new boot, two
independent guarded 1 MiB READIMAGE calls matched the candidate exactly.
`run_stop.py` then passed one stale-token → valid-STOP call and one no-STOP
deadline call. The valid STOP returned status 0 with exact ACK and echo;
host-observed cycle time was 21.9 ms. The missing-host case returned stock
status 2 after 10.26 s. A complete post-call flash read still matched.
The host restored the whole saved loader page and PIATVR `c0000000`; all
512 owner/count records matched. The stock owner page's two changing bytes
at `0xaa0..0xaa1` are outside those records. No companion remained loaded,
the stock descriptor was idle, and old DAC960PG `37:04.1` stayed unbound.
The [accepted evidence](../../../artifacts/current/accele160-stop-20261017/README.md)
includes all five guarded 1 MiB captures, stage/flash receipts, exact
command status, owner/page snapshots, module binary, linked ELF, and replay.

The isolated remote workspace is `/home/mit/i960-accele160-stop-20261017`.
For reproduction, bind only new-card `myrsread`, perform two guarded
selector-9 1 MiB reads, then run `run_stop.py` with the exact candidate,
command module, and both read directories. The harness tests wrong STOP
followed by correct STOP, then a missing-host deadline; it restores the
loader page and aperture after each completed run. Finish with another
guarded full-flash read and run `verify_live.py` with `--tamper-test` on
the archived captures. The replay passed and rejected three altered captures.

The parallel design review [Find i960MC board design guidance] identified
the `dcmd_mutex` serialization and recommended this independent nonce/epoch
aperture path before a timer experiment. It also traced `myrs`'s word-zero-
last command publication and ring completion handling. Those rules inform a
future persistent, pinned request/completion transport; operation 11 does
not change the driver's mailbox or establish a frame-rate gain.
