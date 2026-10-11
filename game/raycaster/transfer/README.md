# Framebuffer transport profiling and exact validation acceleration

**Card accepted:** five 421-request sessions, 2,105 native-matching replies and
five full restorations. Detailed profiles cover 43,904 STEP commands. Full-frame
kernel transaction median fell from 57.83 to 55.74 ms (3.61%); the readback/audit
phase fell from 12.22 to 10.61 ms (13.15%). The final build without detailed command
logging measured 55.64 ms. [Full evidence](../../../artifacts/transfer-20261011/README.md).

## Use

Keep the existing bounded word-memory target. Build the optimized host module:

```sh
python3 game/raycaster/transfer/build.py --out /path/to/FRESH-module --fast --coarse
make -C /lib/modules/$(uname -r)/build M=/path/to/FRESH-module CC=gcc-12 modules
```

`--coarse` keeps the existing five RAYPROFILE transaction phases and normal
command diagnostics, omitting extra CMDPROFILE lines. Omit it for detailed
profiling; omit `--fast` for the reference validator/counter. The older
`game/raycaster/build_transport.py` remains the unoptimized reference builder.
Production autonet and the parallel exclusive-RTEMS profile are unchanged.

For a detailed run, use the module built without `--coarse` and:

```sh
python3 game/raycaster/check_card.py --payload KERNEL --module MODULE \
  --output FRESH-CAPTURE --command-profile
python3 game/raycaster/transfer/profile.py FRESH-CAPTURE
```

Use the same module with `server.py --backend card` to display frames. Observe
exclusive card ownership, normal HTTP shutdown, original-image verification,
full close validation and HTTP restoration. No flash operation or reboot is
needed. Never run alongside another card experiment.

## What is optimized

Only two host-side computations change:

1. `count.h` counts bytes different from the DMA fill pattern eight at a time.
   It preserves the **exact count**, including any guard corruption, with a byte
   tail. `memcpy` loads full eight-byte words without alignment/aliasing casts.
   The per-byte high-bit arithmetic cannot carry between bytes; a horizontal sum
   counts nonzero XOR bytes. This avoids the borrow ambiguity of subtract-based
   zero detection. There is no SIMD or read past the requested interval.
2. `validate.h` compares the exact immutable RIO1 ranges using `memcmp` rather
   than classifying each byte in the entire image. Mutable private workspace,
   status/result words and declared output are the same as before. Output lengths
   above the fixed capacity maximum are also explicitly rejected before address
   arithmetic. The caller still validates the request first.

No framebuffer compression, new DMA engine, partial audit, checksum shortcut or
sampling is introduced. Both full response snapshots still compare byte for byte,
including private workspace. Immutable code, both workspace guards, header/input,
output tail/guards and periodic full-allocation suffix remain covered. Table and
result reads, request sequence checks, poison patterns, barriers, status/ID gates,
command timeout, uncertain-state retention and final restoration are unchanged.
The target payload and wire protocol do not change.

The ordinary transaction still uploads 12,384 request bytes, 16 sentinel bytes
and the four-byte table word, invokes the callback once, and makes all 22 reads:
four table reads, two result reads and sixteen staging reads. Every 32nd callback
adds two reads for the full allocation. First entry retains its cache handshake.

## What the profiler measures

Each successful `issue()` records monotonic host intervals for admission/stale
checks, input readiness, DMA fill/preparation, submission logging, mailbox writes,
completion polling, completion consumption/barriers, DMA byte scans, completion
logging/capture copy and final status validation. The ten intervals sum exactly
to total. Failed commands retain the original error/retention path and emit
CMDFAIL, which is not accepted as a performance sample.

`check_card.py --command-profile` saves every complete per-step log and parsed
row in `commands.jsonl.gz`, outside its Board.step timing. `profile.py` requires
the exact opcode/count/offset sequence and full paired read volume on every
transaction. It reconciles timing sums and reports full-render medians. The
unattributed kernel remainder includes CMDPROFILE logging, session-level
copying/validation and other work outside `issue()`; it is not isolated validator
CPU time. Completion waits include firmware work, Linux polling and scheduling.

## Validation and replay

```sh
make -C game/raycaster test-transfer
python3 game/raycaster/transfer/verify.py artifacts/transfer-20261011
```

ASan/UBSan runs on Mac/Linux cover every immutable byte of a 512 KiB image,
every output boundary 0–8192, metadata and random mutations, and differential
prefix/full checks against the original validator. The byte counter is compared
with an independent scalar loop across 528,384 pattern/offset/length cases,
65,536 adjacent-byte combinations and guard pages. All three generated variants
pass the inherited 348 command-failure/timeout injections, stale/malformed
requests and six output-corruption cases each.

Archived replay checks exact module/payload identities, every native reply, all
periodic/full-close captures, and every profiled command. It verifies that the
optimized detailed module differs from the detailed baseline only in these two
computations, and reproduces the final release module's generated source. Build-
generated `.mod.c` symbol/version stubs are preserved but excluded from that
source comparison. Derived timing arithmetic permits 1e-12 floating rounding
differences between host Python versions; raw replies and captures remain exact.
