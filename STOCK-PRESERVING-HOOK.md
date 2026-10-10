# Stock firmware command hook — offline candidate, 2026-10-10

Successor: [ROM-HANDLER-STEP3.md](ROM-HANDLER-STEP3.md) keeps the PING handler
in verified firmware flash padding, avoiding this candidate's unowned DRAM
window. This page preserves the first build for comparison.

Latest: [DRAM-HOOK-AUDIT.md](DRAM-HOOK-AUDIT.md) checked the matching bootstrap,
allocator and live `C0120000` bytes. The 64-byte read was zero, but exclusive
ownership remains unproved. This candidate is still **not flash-ready**.

The first stock-preserving candidate is built. It retains the original
4.07-0-29 firmware startup and adds one small command handler. It has **not**
been installed or run on the card. The candidate's manifest explicitly says
`flash_ready: false`.

## What the image does

The installed boot block copies and runs the normal bootstrap, which
decompresses the stock program into DRAM. Its metadata then selects the program
entry. The candidate changes only the metadata entry from `C004A2E0` to
`FEFE0000` and adjusts the metadata sum. An 84-byte hook occupies verified zero
padding at full-image offset `0x60000`, local address `FEFE0000`.

The hook copies its 20-byte `PING` handler from local flash to candidate DRAM
`C0120000`, invalidates the instruction cache, changes dispatcher table word
`C001F9BC` from `C001FE98` to `C0120000`, restores the normal zero value of
`g14`, and branches to the original stock entry `C004A2E0`. The stock command
table at `C001F804` indexes `(opcode & 0x7F) - 1`; `0x6F` selects `C001F9BC`.
That entry originally goes to the unsupported-command handler, which reports
`0x0104`. The high-bit alias `0xEF` also selects it, so a future host interface
must treat both values as reserved for this experiment.

When the new handler receives a normal request pointer in `g0`, it stores
`0x017E` at request offset `+0x18`, then tail-branches to the stock completion
function `C004BAD0`. That function owns the normal host mailbox completion.
Thus a future `PING` can prove both custom instruction execution and return to
stock firmware by observing completion ID plus status `0x017E`. The handler
does not install `UPLOAD` or `GO`; those are later steps.

## Exact build and preservation

Sources and build instructions are in [loader/stockhook/](loader/stockhook/README.md).
The target-built ELF, raw hook, disassembly, map, image, manifest and exact build
inputs are in [artifacts/stockhook-20261010/](artifacts/stockhook-20261010/README.md).

The hook SHA-256 is
`2a96bc45edd69b665dbd42b4dd17bd6594817ba64b34525c2e88e4e1faf0d16a`.
The candidate image SHA-256 is
`25dd3cc627096b9e66889d67451edbba199d881084058656bd41ca5ef6778e4b`.
Exactly 76 bytes differ from the pinned stock image. The builder checks the
donor image hash, unpacked program hash, firmware descriptor, bootstrap and
metadata sums, exact original command-table word, stock entry bytes and exact
target hook hash. It rejects unexpected changes outside the padding and two
metadata words. The original compressed program, boot block, BIOS, reset record
and descriptor remain byte-identical.

The i960 target build completed with the archived GCC 3.3.6/binutils 2.27
toolchain. Two offline image tests passed, including rejection of mutated input.
The disassembler has trouble decoding the final `bx (g1)` at this high address;
the raw final instruction is `00 50 04 84`, inspected in the binary.

## Remaining conditions

`C0120000` is a candidate placement, supported by the matching bootstrap clear
of `C0000000–C013FFFF`, the stock allocator's `C0140000` lower bound, and a
paired live read of 64 zero bytes. It is **not reserved from indirect stock
users, DMA or later firmware activity**. See [DRAM-HOOK-AUDIT.md](DRAM-HOOK-AUDIT.md).
Handler storage needs lifetime ownership or another location. CPU cache and
flash mapping after normal startup also remain untested. The code currently
copies the handler and invalidates the instruction cache before stock entry;
this is an offline control-flow design, not hardware proof.

The next work is a firmware-owned handler placement. Before any flash test,
serial recovery and the vendor programming route still need independent live
validation. The host at `192.168.2.75` was used only to compile target code;
the card stayed driverless, with no probe module, reboot or firmware write.
