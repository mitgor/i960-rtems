# Reversible live RAM upload verified — 2026-10-10

**A fixed 16-byte RAM upload succeeded and its original bytes were restored.**
Paired reads verified the test pattern, unchanged surrounding bytes and complete
restoration of the saved 64-byte region. No flash command, custom instruction
execution, recovery transition or reboot occurred.

## Scratch ownership and target

The successful allocator reserves floor(80000 / 2000)+1 = 65 blocks, each 2000
bytes. The verified allocation starts at C0F2C000 and ends at C0FAE000 exclusive.
Its first 80000 bytes hold the flash staging image; the additional block begins
at C0FAC000. This experiment used C0FAC010–C0FAC01F inside that additional block.
The choice is specific to the validated allocator/profile, not generally unused
DRAM. See STAGING-ALLOCATION.md for the code-derived extent.

The saved surrounding region was C0FAC000–C0FAC03F, 64 bytes. It was zero-filled
in both initial reads. The upload did not overwrite the staged ROM image,
controller code, callback pointers or the boot record. The addresses are local
DRAM addresses, not physical flash locations.

## Upload path and gate

The observed board +E4 callback C004CED0 reads mailbox count/offset/host address,
adds the offset to the staging pointer and invokes C004C010 with DMA control 14.
Its scheduler goes through the stock quiescence check. Programming is a separate
callback and was never invoked. This test establishes data transfer in both
directions at this RAM location; it does not establish CPU cache or instruction
fetch behavior after DMA.

`host/dump/dac960dump.c` adds opt-in `scratch_check=1`, requiring both
`pointer_check=1` and `runtime_check=1`. Those checks validate the exact profile,
staging pointer, known code and board callbacks before the scratch gate is armed.

The command issuer permits opcode 21 only for count 16 at staging-relative offset
80010, only with an internally supplied buffer and the scratch gate armed.
There is no user-supplied upload address or payload. The test payload is fixed;
the restoration payload comes from the saved baseline. The only extra read range
is count 64 at offset 80000. The ordinary image-read bounds remain unchanged.

## Actual sequence and result

The thirteen read-only prerequisite commands were followed by:

| IDs | Operation | Result |
|---|---|---|
| 14/15 | Paired 64-byte baseline reads | Both zero-filled and equal |
| 16 | Upload 16-byte fixed pattern at offset 80010 | Status zero |
| 17/18 | Paired 64-byte readback | Pattern present; remaining 48 bytes unchanged |
| 19 | Upload saved original 16 bytes | Status zero |
| 20/21 | Paired 64-byte restoration reads | Both match all 64 original bytes |
| 22 | Enquiry2 | Same firmware/profile |

Pattern: `49 39 36 30 52 41 4D 21 10 32 54 76 98 BA DC FE`.

Every completion ID matched, every status was zero, and every DMA guard remained
unchanged. Final experiment-result=0, pending=0 and scratch-dirty=0. Captures were
collected before module removal; final checks confirmed the module absent and the
card driverless. Mailbox, doorbell and DMA transport writes occurred as part of
these commands. No request to erase or program flash was sent.

The test marks scratch dirty before attempting the upload. After any known-complete
write attempt it tries restoration even if pattern validation failed. If DMA
completion becomes uncertain, it stops and retains resources. If restoration
cannot be verified, scratch stays dirty and the module is pinned pending recovery;
it does not advertise success or silently remove the evidence. The successful
run did not exercise those error paths on hardware.

## Artifacts and validation

`artifacts/ram-scratch-20261010/` contains the 22-command transcript, all 20 capture
blobs, exact executed source and headers, the kernel-specific module, and
verification.json. A host upload-buffer capture alone is not proof of a controller
write; the separate card-to-host paired readback and restoration are the evidence.

Kernel build with W=1 passed. Two native guard/check tests passed, and 20 Python
tests passed. New tests reject altered surrounding/restored bytes, dirty/pending
state, and unexpected upload addresses. Validate with:

```sh
make -C host/dump test-guards test-scratch
python3 -m unittest discover -s host/dump -p 'test_*.py'
python3 host/dump/validate_scratch.py artifacts/ram-scratch-20261010
```

## Next step toward running software

The card now has verified RAM read and reversible data upload at an owned scratch
location. The next substantive work is a minimal execution-handoff design:
identify a stock callback that can return normally, prepare a returning proof-of-life
stub, verify CPU/data/instruction-cache visibility and preserve all original bytes
and callback state. Do not jump directly into the recovery monitor: it requires
setup beyond copying its bytes. A stalled stub may still require a power cycle;
serial entry and independent flash recovery remain separate, untested capabilities.

Keep the first execution experiment RAM-only and make its completion observable.
A broader upload interface or firmware flash is not justified by this data test.
