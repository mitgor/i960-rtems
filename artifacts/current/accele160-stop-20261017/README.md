# AcceleRAID 160 independently writable STOP gate: accepted

Status, 2026-10-17: operation 11 proves that the host can signal a pending
card callback through the saved loader-page PCI aperture while the stock
direct-command mutex is held. A wrong STOP word did not complete the
callback; the exact STOP returned success and an ACK. With no STOP, the
card's fixed loop returned stock unsupported status 2 after 10.26 s.
This is a control-channel and bounded-timeout result, not timer/interrupt
ownership, unrestricted RTEMS STOP, or a DMA drain.

The [source and procedure](../../../host/accele160/stop_gate/README.md)
preserve operations 1–10. The new linked handler is 3,392 bytes, SHA-256
`0a9c5f9deaae6f01d943c90a065a31de377ebbcf388a28b3e73b0ba96b6192e8`,
with no relocations. [Candidate](candidate.bin) SHA-256 is
`ef5635d38bf397ff13fa1140ef6265de0b300c70ad8b157c17427013a1d2abb5`.
The [offline audit](../../../host/accele160/stop_gate/audit.py) found 2,853
changed bytes confined to the retained loader cave and two checksum words;
the decompressed runtime, boot block and loader return hook were unchanged.
Five one-byte input mutations were rejected. Exact command module SHA-256
is `cfad41dfd8465f51243467234fd71ae0f658aa778ed318dc674257ff38720a59`;
[ELF, module and build header](build/) are archived.

The preceding firmware was SHA-256
`9d5d4da2c283d10e1dee9c71ceb477f36e389cd0d0548764a3cc5f8a41a24c49`.
Its [complete preflash read](live/preflash-read/result.json) matched. The
[STOREIMAGE stage](live/stage/result.json) and [independent complete staged
readback](live/staged-readback/result.json) matched the candidate with zero
residual and zero DMA-guard changes. [FLASHIMAGE](live/flash/result.json)
completed in 37.04 s with status/residual zero. The host boot ID changed
from `82ee0014-ad02-429d-ac1f-597b546afd3d` to
`76a93df2-6deb-4cea-a704-c9ae152a5f5f`; two independent
[postboot](live/persistent-0/result.json) [full reads](live/persistent-1/result.json)
matched the candidate byte for byte, with zero residual/guard changes.

The [live sideband test](live/stop-run/result.json) saved an all-FF 4 KiB
loader page and the complete owner page. It preloaded magic, nonce
`0x161610b1`, epoch 1 and zero command in `c000f960..f96f`. Firmware wrote
READY at `f970`. The host wrote stale `0xdeadbeef` at `f96c`, observed the
callback still pending, then wrote exact STOP `0x504f5453`. The callback
returned status/residual `0/0`, READY and ACK `0x214b4341` with matching
nonce/epoch echoes. Host-observed elapsed time was 21.9 ms, including host
polling. In a second fresh call, with no STOP, the 20-million-poll limit
returned status/residual `2/0`, TIME `0x454d4954`, and no ACK after 10.26 s.
The control record is the only changed part of the saved loader page. After
each completed command, the host restored the entire page and PIATVR and
released the one-shot module. All 512 allocator count/owner records in
`0x2a0..0xa9f` matched; two stock-active bytes `0xaa0..0xaa1` outside that
range changed, as in the preceding inventory gate. No module was retained.

The [post-call full flash read](live/postcall-flash/result.json) again
matched the candidate with zero residual/guard changes. The [final host
state](live/final-state.txt) confirms PIATVR `c0000000`, idle stock
descriptor, only new-card `myrsread` bound, and old DAC960PG `37:04.1`
unbound. [Independent replay](../../../host/accele160/stop_gate/verify_live.py)
passed all five complete reads, stage/flash receipts, two sideband calls,
bounded page and owner checks; it rejected mutations to ACK, a loader-page
byte outside the record, and an owner word.

The parallel driver review established why this path was needed: `myrs`
serializes the one-shot direct command with `dcmd_mutex`, so a second
ordinary direct mailbox command cannot reliably STOP it. Its command-ring
publication and completion ordering remain a reference for a later
persistent request/completion transport. Next, read the live cached-vector
word and qualify timer-1 mode's read-clear side effect, then design an
owned-stack timer test that uses this independent STOP path to quiesce its
RTEMS task before restoring the borrowed interrupt state. This gate alone
does not make an uncooperative task preemptible or prove an IRQ can be safely
cancelled.
