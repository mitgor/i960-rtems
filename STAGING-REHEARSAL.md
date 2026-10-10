# Live staging rehearsal — 2026-10-10

Latest (2026-10-10): [programming preflight and live CPU verification](PROGRAMMING-PREFLIGHT.md)
passed. The CPU read all 512 KiB of the candidate through programmer alias
C1F2C000 with explicit cache invalidation and matched CRC32 2012D01F. All 105
commands completed cleanly; original staging/table/code restored, probe unloaded.
The descriptor policy and bytewise post-program flash-readback route are now
documented. Next implement the one-shot programming state machine and its
failure tests. No flash programming or recovery test occurred. Exact evidence
is in `artifacts/programming-preflight-20261010/` from the repository root.


**Passed; full stock staging restored and probe unloaded.** The DAC960PG
remained installed at `0000:37:09.1` on `mit@192.168.2.75`. This experiment
uploaded the exact ROM candidate to staging RAM, verified it, and restored
stock. It did not program flash, execute the new handler, reboot, or test recovery.

## Evidence

[Captures and exact module/source snapshot](artifacts/staging-rehearsal-20261010/)
include six complete 524,288-byte images, all transaction results, the kernel
log, the capture tar, and [independent validation](artifacts/staging-rehearsal-20261010/validation.json).
The two reads of each phase used different DMA sentinels (`A5` and `5A`).

| Phase | Both captures' SHA256 |
| --- | --- |
| Original stock | `43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93` |
| Staged candidate | `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0` |
| Restored stock | `43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93` |

The three uploads were exactly the offline pinned plan: 48 bytes at `0x60000`,
four at `0x67F68`, and four at `0x67FDC`, all relative to staging `C0F2C000`.
They total 56 bytes and produce 48 differing bytes in the full image. Three
corresponding uploads restored the original bytes. Before the first upload,
the complete stock image and each patch preimage were verified.

All 74 commands completed with matching tags, status zero, and unchanged
DMA guards. The transcript ends with `experiment-result=0 pending=0`,
`stage-dirty=0`, `exec-dirty=0`, and `scratch-dirty=0`. Final Enquiry2 matched
the original profile. After local capture validation, `rmmod dac960dump`
succeeded; both the module and its debugfs directory were absent, and the
card remained driverless with PCI identity `1069:0010`.

## Implementation and reproducibility

`host/dump/dac960dump.c` has a mutually exclusive `stage_check=1` mode requiring
both `pointer_check=1` and `runtime_check=1`. `stage_data.h` pins upload offsets,
lengths, bytes, and full-image hashes. `stage_rehearsal.h` reads full images in
nine chunks per pass, hashes them with kernel SHA256, and restores every
possibly touched patch on known-complete errors. Dirty state is cleared only
by complete stock readback verification. Uncertain completion stops commands
and retains the module/DMA; unverified restoration also pins the module.
There is no flash programming opcode in the harness's command allowlist.

The remote build directory is `/home/mit/i960-stage.iCb9od/`; its source and
`.ko` are archived locally. It built with `W=1` on kernel `6.8.0-138-generic`.
The test model exercises the production transaction code with all 122
known-error/timeout combinations at its 61 command boundaries, plus corrupt
preimage and candidate reads. The mock substitutes full-image comparison for
kernel hashing; the live run exercised the real kernel hashing path.

Revalidate archived evidence without hardware:

```sh
python3 host/dump/validate_stage.py
python3 -m unittest discover -s host/dump -p 'test_*.py' -q
```

The live invocation used the three opt-in parameters above. Debugfs files
were copied with `cat` into ordinary files before archiving: directly tarring
these dynamic blobs can silently preserve zero-length files. Other capture
slots remain present for harness compatibility; only slots exercised in the
transcript are evidence. The six `stage-*.bin` files are all fully populated.

## Next engineering step

Finalize the programming procedure before performing the flash test:

1. Establish that the stock CPU programming path sees the modified staging
   bytes. DMA readback alone does not establish CPU cache visibility; earlier
   table experiments demonstrated stale CPU reads. Audit cache maintenance
   in the `2B/1` route and add a bounded verification if needed.
2. Resolve exact updater/descriptor inputs and update-time handler behavior.
   `2B/1` erases/reprograms the lower 496 KiB, including the proposed handler's
   sector. The boot-block flag must remain clear. `0x22` is the wrong route.
3. Define fresh physical flash readback that handles the 8-bit bus, then test
   the programmed image's boot hook and opcode `0x6F` status `017E`.

The candidate remains `flash_ready: false`; FEFE001C is still unflashed and
unexecuted. The original staging plan JSON records its offline generation
provenance; this document records the subsequent live verification. Recovery
testing remains excluded at the user's request. This milestone establishes
staging preparation, not a completed mode-0 loader or permanent firmware change.
