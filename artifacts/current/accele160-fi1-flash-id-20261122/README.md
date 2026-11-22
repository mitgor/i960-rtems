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
the grant. This revision is built and statically audited, but not yet run on
the card.
