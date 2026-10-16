> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Offline returning-callback artifact — 2026-10-10

This directory preserves an i960 target build of the proposed returning
proof-of-execution callback.  It is an offline artifact only: none of its bytes
were uploaded to the card, and no custom instruction executed on hardware.

`return-status.bin` is exactly 20 bytes, SHA-256
`fa0a45d65af0ad92110474b08b18ac07f20aa6323d7f07fbea24f62ab3865578`.
It writes request status `0x017e`, loads the verified stock completion address
`C004BAD0`, and tail-branches there.  The ELF/map/disassembly, exact input
sources and verifier are included for reproducibility.  The i960 build ran on
the SSH host with GCC 3.3.6/binutils 2.27:

```sh
make CROSS=/home/mit/i960/tools/bin/i960-coff-
python3 test_return_status.py return-status.bin
```

`objdump` disassembles the final `bx (g1)` poorly at this high linked address,
but the raw final word is `00 50 04 84`, verified by `test_return_status.py`.
See [LIVE-EXECUTION-HANDOFF.md](../../docs/loader/LIVE-EXECUTION-HANDOFF.md) for the
firmware evidence and the reason this cannot be used as a live SSH upload.
