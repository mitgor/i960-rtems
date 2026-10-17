# Finite timer-driven exclusive RAM acceptance

Boot `ed14ddb9-6cf2-4dbc-8645-1383eda72c2d`, new AcceleRAID 160
`0000:37:09.1`, old DAC960PG `0000:37:04.1` unbound. The RAM-only 27-page
image SHA-256 is `126b26bbf76d8e7a782d2be4659fecab5664bb57726647a21803e7010fc73825`;
kernel SHA-256 `440673cae52c0e7a4c07f9cbba4e54111f977a28bd566f3b115313a02377032e`,
whole-image FNV `0x63af0065`. The unchanged firmware was
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

The card admitted the image inside its exact owner-tagged 512 KiB grant. On
its owned entry stack at priority 31 it observed CCR/NDAR/BCR zero on all
three DMA channels, saved four words each on zero upper page `c0f01000`
and nonzero stock expanded-runtime page `c0011000`, and wrote different
patterns. The host captured the **complete held pages** after RTEMS READY
and checked that both remained unchanged across a further 25 ms of timer
preemption. Card-side restore and complete-page hashes passed before the
firmware callback returned. Host `upper-before/after.bin` and
`stock-before/after.bin` match byte for byte on each path.

| Path | Elapsed | Hardware ticks / handoffs | Result |
| --- | ---: | ---: | --- |
| Exact STOP after stale token | 165.129 ms | 10 / 10 | ACK, full drain and restore |
| No-host deadline | 1,267.623 ms | 120 / 120 | finite TIME, full drain and restore |

Both runs checked the card report, worker ISR continuation entry/return
counts, 64-byte stack guards, timer/vector/mask restoration, firmware SP
`c0002100`, loader page, stage, all 512 allocator count/owner records, every
page-copy receipt and the whole-image digest. The two complete guarded flash
reads immediately before are the prior [occupied-page batch](../accele160-occupied-probe-20261017/README.md)'s
post reads; `post-0/1` are this batch's two matching guarded full reads.
All four report status/residual/guard changes zero. `myrsread` remained bound,
PIATVR restored to `c0000000`, stock descriptor returned idle and no one-shot
module remained. No firmware flash write or reboot occurred.

`build/` contains exact accepted image, kernel, map and symbols. `live-0/`
contains the full page/owner/stack/command evidence. The four flash metadata
records omit duplicate 1 MiB `data.bin` copies; the remote complete reads
were validated byte-for-byte by the guarded reader before release. Replay:

```sh
python3 rtems/accele160/exclusive_timer/verify_live.py
python3 rtems/accele160/exclusive_timer/test_verify_live.py
```

Replay accepts the baseline and rejects changes to the image, held stock
page, card restore report or owner table. Source and bounded host harness
are [here](../../../rtems/accele160/exclusive_timer/README.md). A separate
stock-inventory helper rejected the current firmware hash **before issuing
any card command**, so this batch relies on the exact card-side timer trace,
direct PIATVR/descriptor inspection and full flash/owner audits for its
post-run stock-state checks.

This is a finite, returning callback. It does not establish persistent
RTEMS ownership, a complete 8 MiB upper-bank arena or Doom on this card.
