# RAM-only owned-stack and cooperative STOP probe

This is the next AcceleRAID 160 step after accepted manifest operation 13.
It uses the existing firmware SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`;
**no flash command or firmware revision was needed**. The 448-byte
[assembly payload](probe.S) is padded into a two-page image at `c0710000`.
Page 0 holds code and a saved firmware register/stack pair. Page 1 is
pre-filled with `0xa5` and is the owned stack. The retained handler checks
the complete 8 KiB image FNV before calling it. The host pins exact
SHA-256 `66c11b9cc5907ed8296240e37fa150ce34883ca798111f3670cb209a6a78082f`.

The accepted cross-build used `i960-coff-gcc -mrp -c probe.S`,
`i960-coff-ld -T probe.ld`, and `i960-coff-objcopy -O binary`. The linker
asserts that the 448-byte code and saved context stay in page 0. The host
appends zeros through 4 KiB, then one `0xa5`-filled 4 KiB stack page;
[run_lease.py](run_lease.py) pins the resulting binary hashes and FNV.

The payload saves the caller PFP/SP and `g8..g15`, switches SP to
`c0711f80`, calls a worker, and restores the saved context before returning
through operation 13. The worker writes its observed SP to the saved loader
page. It checks a separately host-writable nonce/epoch/STOP record at
`c000fa40..fa5f`, announces READY, then invalidates D-cache while polling
the STOP word. A valid token causes ACK and normal return; a fixed
2,000,000-iteration budget causes a TIME report and normal return. The host
saves/restores `fa00..fa6f`, the staging page and the complete loader page,
checks all 512 allocator count/owner records, and never asks the old PG card
to bind.

The first host attempt stopped before execution: the new harness tried to
read even grant page 0 through BAR0. The aperture exposes odd pages, so that
read was not a valid copy oracle. The card's copy command had completed and
reported the expected FNV. [The bounded recovery](recover_preflight.py)
checked its page and owner records, restored staging and loader bytes,
released the grant and unloaded the one-shot modules. The corrected harness
uses card-side copy and whole-image digests for even page 0, and independent
PCI readback for odd stack page 1. This is consistent with the prior
[page-copy finding](../../../artifacts/current/accele160-pagecopy-20261016/README.md).

[The accepted run](../../../artifacts/current/accele160-lease-20261017/README.md)
used one grant for two calls, re-uploading both pages between them because
the first call changes the code's saved-context data and stack. In the
no-host case the worker returned TIME after 1,036.7 ms. With STOP, a stale
token remained pending and the exact token returned ACK in 23.4 ms. Firmware
SP was `c0002100` before and after; worker SP was `c0711fc0` in the owned
second page. That page changed by 16 and 4 bytes respectively while its
bottom 256-byte guard stayed intact. The owner table, stage, loader page and
PCI aperture restored, all one-shot modules unloaded, and a complete
post-call flash read matched the accepted firmware.

This proves a **cooperative, loop-bounded payload** and an owned stack for
this returning worker. The loop count is not a wall-clock timer, and the
host cannot forcibly stop arbitrary code that does not poll. It does not
yet prove RTEMS task quiescence, task preemption, interrupt-stack ownership,
hardware timer use, DMA drain, or resident application lifecycle. The next
RAM-only experiment should put the same STOP/epoch poll into a bounded RTEMS
task, capture task-level quiescence and keep the same audit boundary.
