# Returning i960RP programs

**New consumer:** [T2 Tetris step payload](../../docs/games/TETRIS-STEP.md) is implemented and hardware validated; it returns serialized game state plus framebuffer through BIO1.

See [BUFFER-IO.md](../../docs/loader/BUFFER-IO.md) for the tested BIO1 buffer ABI and text/framebuffer demo. Scalar calls remain supported.

This is the hardware-tested runtime loader target, distinct from the historical
internal-RAM/MU loader in the parent directory. See
[SOFTWARE-LOADER.md](../../docs/loader/SOFTWARE-LOADER.md) for the complete workflow.

Implement `unsigned payload(unsigned argument)` as in `demo.c` or `mix.c`.
Compile with the existing i960 GCC using `-mrp -O2 -ffreestanding -fno-builtin`,
link with `payload.ld`, and extract a raw binary using `objcopy -O binary`.
The linker expects `_payload` at `C0F2C000`, rejects BSS and caps size at 64 KiB.
Preserve the normal ABI, use small stack frames and return promptly. No startup
code, libc, interrupt setup or asynchronous execution is provided.

`runner.s` is the fixed call gate at `C0FAC180`. Its 32-bit argument and entry
literal words at offsets 16 and 24 are patched by the host. It invalidates
instruction/data caches, preserves the firmware command context in r4 across
`callx`, records the result through alias `C1FAC280`, self-disarms dispatch back
to ROM PING and completes via `C004BAD0`. Its target binary is SHA-pinned by
`host/loadrun/build.py`; do not silently substitute a different runner.
