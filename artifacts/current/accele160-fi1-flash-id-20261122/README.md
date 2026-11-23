# FI1 RAM flash-ID attempt, 2026-11-22

On card `10112500320`, boot `725fcfca-e805-493b-8987-80d981674be3`,
two complete baseline reads matched Firmware injection v1 SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The first FI1 operation-13 ID probe image `400a2696…f6634` issued only Intel
`FF`, `90`, `FF` commands. The host report contained `RUN1`, the expected
nonce, `ONE1`, and payload result zero; the command completed with status
zero. However, the host's subsequent BAR read of the grant page did not
contain the ID record written there by the payload. The record therefore
cannot be interpreted as a chip-ID mismatch. Card data-cache visibility is
one possible explanation, not an established cause.

The launcher stopped before releasing the admission command and grant. A
follow-up `READIMAGE` returned status 2 and full residual while those
resources remained held. This refused read does not establish a persistent
flash change. The PC was sent a power-off request, which made it unreachable.
No erase, program, FLASHIMAGE, gate-hold or native APPLY command was issued.
The [small diagnostic captures](first-attempt/) are archived here; complete
remote captures remain under `/home/mit/i960-writer-stage-20261122/fi1-id-725f/`.
After the next boot, take two independent full reads before another RAM run.

The revised ID payload `048e32f7…ca72c` writes its record beside the
host-visible operation-13 report and restores that region before releasing
the grant. On boot `389400bd-0a35-4695-adc8-cdb65d5e9b3a`, after two
independent baseline full reads, this revision ran successfully. It reported
Intel manufacturer `0x89`, device `0xa6`, master lock 0, block-lock mask 0,
and array byte `0x50`. The operation-13 command returned status 0; the host
audited and restored the RAM page, owner table, staging page and BAR mapping,
then unloaded its command modules. Two further independent full `READIMAGE`
requests returned the unchanged Firmware injection v1 SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`,
each with status/residual/guard changes zero. Compact [receipts](live-v2/)
are committed; complete image data remains on the remote under
`/home/mit/i960-writer-stage-20261122/`.

This establishes the live Intel read-command path and lock state on this
card. It does not test VPP, erase/program, the native writer, or native
cold boot.
