# AcceleRAID 160 reusable RAM admission acceptance

Accepted on 2026-10-17 on new card `0000:37:09.1`, with exact `myrsread`
bound and old DAC960PG `0000:37:04.1` unbound. Operation 13 adds
manifest-checked entry for a reviewed, returning image in the stock-owned
512 KiB grant. Operations 1–12 are preserved. Its full 1 MiB firmware SHA-256
is `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`;
handler SHA-256 is
`8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34`.
See [source, manifest contract and limits](../../../host/accele160/ram_admit/README.md).

The exact [candidate](../../../host/accele160/ram_admit/candidate.bin),
[handler](../../../host/accele160/ram_admit/handler.bin), two probe binaries,
source and test harness are kept once in the source subproject. This directory
holds the exact compiled Linux [command module](admit_command.ko) and the
[live captures](ram-admit/). Identical 1 MiB read data appears in several
capture directories because each read was a distinct full hardware audit;
Git stores identical content only once.

The first boot, `d88a2742-e903-4513-94a1-13e534b5e2cd`, produced two
current-image full reads, a complete `STOREIMAGE` readback of the candidate,
and `FLASHIMAGE` status/residual `0/0` in 36.84 s. The next boot,
`a73c4744-6f78-49a0-b6b3-e281c03c6cd0`, produced two matching full
persistent reads before any RAM call. All image reads had status/residual/
DMA-guard changes `0/0/0`.

Under one audited grant at `c0710000`, two different 48-byte returning
probes were each padded to one 4 KiB page, uploaded from the separate last
staging page, read back, independently hashed on card, and called through
the same operation 13 without a firmware write. Probe 1 took 20.94 ms and
returned `0x16010001`; probe 2 took 20.66 ms and returned `0x16010002`.
For each probe, wrong FNV, out-of-range entry and wrong nonce all returned
stock unsupported status 2 with the sentinel report untouched. The host
checked the entire saved loader page around every operation, all 512
allocator count/owner records, the stage restoration, and no old-card bind.
A complete post-call read still matched the candidate.

Operation-11 compatibility passed on the same firmware: a wrong STOP token
left the callback pending, the correct token returned ACK in 21.5 ms, and
the no-host deadline returned status 2 after 10.26 s. The fixed 15-page
operation-9 RTEMS image still uploaded and ran: transfer 1.14 s, card digest
`0x648486da`, bounded RTEMS task result, staging/page/owner restoration.
The final complete flash read still matched. No one-shot test module remains
loaded. This is an accepted reusable **returning-code** gate; it does not
yet give an unbounded RTEMS task a wall-clock lease, task-aware STOP,
hardware timer or owned interrupt stack.

Replay from the repository root:

```sh
python3 host/accele160/ram_admit/verify_live.py artifacts/current/accele160-ram-admit-20261017
python3 host/accele160/ram_admit/test_verify_live.py artifacts/current/accele160-ram-admit-20261017
```

The first command validates the complete read receipts and bytes, boot
transition, stage/flash command receipts, exact code tail, both reports,
six negative admissions, all recorded owner/page transitions, STOP and
fixed RTEMS compatibility. The second rejects mutated flash, accepted
report, rejected report and allocator-owner captures. The artifact does not
claim segmented ELF loading, an independent payload stack or bounded
preemption of a hung image.
