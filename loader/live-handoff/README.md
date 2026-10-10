# Offline live-handoff proof stub

`return_status.s` is the smallest useful proof-of-execution callback for the
currently recovered 4.07-0-29 runtime.  If it is entered with the standard
mailbox request pointer in `g0`, it writes completion status `0x017e` into the
request and tail-branches to the stock completion function at `C004BAD0`.
The normal host completion is therefore the observable result; the stub does
not depend on an MMR marker, a loop, a reset, or flash.

It is linked at `C0FAC100`, inside the same extra allocation block where a
separate 16-byte slot was proven writable and restored.  This 20-byte code
image has not itself been transferred, so the placement is an allocator-derived
candidate, not a completed upload validation.  The present stock mailbox API
has no path to change the live board callback table or branch to that RAM
address, so this binary must not be uploaded as an experiment.  Its immediate
purpose is to fix the ABI and completion contract for the patched-boot loader
route.

Build with the archived i960 GNU toolchain:

```sh
make CROSS=/home/mit/i960/tools/bin/i960-coff-
```

The generated artifacts are copied to `artifacts/live-handoff-20261010/` only
after inspection.  `LIVE-EXECUTION-HANDOFF.md` records the firmware evidence,
the missing live handoff primitive, and the conditions required before testing
this stub.
