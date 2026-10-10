# i960 flash loader

**Current index (2026-10-11): [findings, evidence and unresolved questions](../CURRENT-FINDINGS.md).** Earlier milestone notes below retain their historical context.

**T4 complete (2026-10-10): [play Tetris over SSH](../TETRIS-TERMINAL.md).** The terminal client passed a 30-minute real-SSH test: 35,846 native-matching frames, 68 restarts, 19.91 Hz. Quit, Ctrl-C, connection loss/reconnect and resize cleanup passed. Use `ssh -t mit@192.168.2.75 /home/mit/i960-tetris-t4/play.sh`. Full RAM restored, module unloaded; no reboot or flash.


**T5 complete (2026-10-10): [persistent BIO1 sessions](../PERSISTENT-SESSION.md).** 1,000 frames matched native output at 41.1 ms median; a separate 400-frame run sustained 20 Hz. Process-kill/ownership cleanup and full final RAM restoration passed. `host/session/` keeps paired code/payload checks every frame and full staging audits every 32 frames and close. The subsequently completed T4 terminal client uses this transport; no reboot or flash.


**T3 complete (2026-10-10): [long Tetris hardware replay](../TETRIS-REPLAY.md).** 1,000-call main replay plus 64 repeat calls matched native state/frame bytes; all RAM restored and probes unloaded. Median full CLI latency 306 ms (~3.26 updates/s), payload-command interval ~6.18 ms. This baseline motivated the now-completed T5 session optimization; T4 terminal play is now complete; see the latest milestone above. No reboot or flash.

**T2 complete (2026-10-10): [bounded Tetris steps](../TETRIS-STEP.md) run on the card.** Explicit 240-byte state, 20-tick bound, 24×80 rendering; 1,024 native/interpreted transitions agree, and nine live transactions match the native reference byte for byte. RAM restored; no reboot/flash. T3 replay, T5 persistent sessions and T4 terminal play subsequently passed.

**T1 complete (2026-10-10): [bounded text/framebuffer I/O](../BUFFER-IO.md) is hardware validated.** BIO1 supports 4 KiB input / 8 KiB output; live text, 24×80 frame, capacity rejection and repeat/scalar regression passed with RAM restored. T2 subsequently converted the blocking game into hardware-tested returning steps.

**Latest hardware milestone (2026-10-10): [runtime software loader](../SOFTWARE-LOADER.md) works after PC startup.** Three live executions (two C programs) passed without reboot or another flash write. Use `host/loadrun/` and `loader/runtime/` from the repository root; earlier internal-RAM and pre-programming plans below are historical. Supports cooperative returning functions up to 64 KiB, with one argument and a 32-bit result. RAM restored and module unloaded after each run. Recovery remains untested.


> **2026-10-10 architecture correction:** Intel i960 Rx manual §4.1 forbids
> instruction fetch from internal data RAM (0x000..0x3ff). The hello-at-0x200 /
> GO milestone described below is invalid on hardware. Current C tests check
> software behavior only. See [PROJECT-REVIEW.md](../PROJECT-REVIEW.md), item 12.
> Executable payloads need verified external memory; code has not yet been fixed.

Stage 1 runs from the DAC960PG boot flash. Stage 2 is uploaded through the i960
Messaging Unit (MU). This implementation supports the **no-DRAM bring-up**:
word-aligned payloads in internal RAM `[0x200, 0x400)`, at most 512 padded bytes.
The lower RAM is reserved for startup and loader register frames. Larger programs
require verified board-specific DRAM initialization and an explicit range extension.

The protocol and demo changed on **2026-10-10**. Build the sender, firmware, and
demo together. Old `loadctl` binaries and old demos are incompatible with the new
hand-off convention. See [PROTOCOL.md](PROTOCOL.md) for the contract and
[REVIEW.md](REVIEW.md) for implemented fixes, tests, and remaining hardware gates.
Claude Code guidance is in [CLAUDE.md](CLAUDE.md).

## Build and test

Native checks work without the i960 toolchain or card:

```sh
make -C loader test
# Compatibility entry point also runs the same tests:
python3 loader/test_protocol.py
```

On the Linux development box with the cross-toolchain on PATH:

```sh
cd loader
make all
make check
# Inspect loader.dis, hello.dis, and the linker maps before flashing.
make image STOCK=/absolute/path/to/decoded/stock.bin
```

`HOSTCC` and `HOSTCFLAGS` configure the native build; `CC`, `LD`, `OC`, `NM`,
`OBJDUMP`, and `CFLAGS` configure the target build through make command-line
assignments. `PYTHON` defaults to `python3`.

The image gate requires the known decoded MIMG stock layout with a `0x38000`-byte
payload, valid IBR checksum, expected PRCB pointer, and matching header length.
The ELF entry, flat binary, and image placement must agree at `0xFEFCCD44`.
This checks layout consistency; it does not identify a compatible board or prove
that inherited firmware tables and startup code work on the card.

## Device ownership and sender

Run on Linux as a user allowed to map PCI sysfs resources, usually root. Unbind
**every driver** from the controller first (including `myrb` and `dac960probe`),
and prevent automatic rebinding while using the loader. Do not run another
controller tool concurrently.

The preferred selector is a full PCI BDF. The historical physical BAR0 selector
is retained, but it must resolve to exactly one `1069:0010` controller. Both use
that device's sysfs `resource0`; arbitrary `/dev/mem` mappings are removed.
Each sender takes a nonblocking advisory lock on the device's `config` inode,
checks that no driver is bound, and checks BAR0 type and size. This coordinates
loadctl processes, not independent tools or concurrent driver binding.

Example for the controller recorded in this repository:

```sh
sudo ./loadctl 0000:37:09.1 status
sudo ./loadctl 0000:37:09.1 ping
sudo ./loadctl 0000:37:09.1 load 0x200 hello.bin
sudo ./loadctl 0000:37:09.1 go 0x200
sudo ./loadctl 0000:37:09.1 status
# Legacy selector, if BAR0 is still at this address:
sudo ./loadctl 0xee000000 status
```

`status` prints both OMR0 and OMR1 without issuing a command. Before hand-off,
OMR0's low half is `ST_READY=0x600D` or a completed command status. After `go`,
OMR0 remains `(ackseq << 16) | ST_HANDOFF=0x600E`. The hello payload writes
`PAYLOAD_MAGIC=0xBEEF00EE` to **OMR1**, proving payload execution while preserving
the acknowledgment. A GO acknowledgment alone does not prove payload execution.
Only `status` is available after hand-off; resetting the card restarts the loader.

`load` reads the file completely before issuing upload commands, checks bounds,
zero-pads its final word, and verifies every transmitted word through `READ`.
It reports original and padded lengths separately. Any error returns nonzero;
a failed or partial upload must not be followed by `go`.

For diagnostics, `read ADDR` reads an allowed payload word. Explicit
`reg-read ADDR` and `reg-write ADDR WORD` access aligned addresses in the policy
window `[0x1000, 0x2000)`, excluding the four protocol registers at
`0x1310..0x131c`. This window is an access policy, not a declaration that every
address is a valid register. Register writes can affect the controller and must
come from verified hardware documentation; no DRAM timing values are supplied.

## Files

| File | Purpose |
| --- | --- |
| `mu.h` | Shared opcodes, statuses, register offsets, and address policy |
| `start.s`, `loader.c`, `loader.ld` | Flash entry, command dispatcher, link layout |
| `hello.c`, `payload.ld` | Internal-RAM demo and link layout |
| `loadctl.c` | Linux PCI sender, synchronization, upload/readback |
| `test_protocol.c` | Actual C sender/dispatcher tests with fake hardware |
| `test_build.py` | ELF/image gate and CLI validation regression tests |
| `test_protocol.py` | Compatibility wrapper for `make test` |
| `check_build.py` | ELF/binary and donor-image consistency gates |

## Hardware gates

**Target build and hardware execution are unverified.** Native tests exercise
software behavior only; they do not verify MMIO ordering, the MU mapping, internal
RAM instruction fetch, or register-cache behavior. Review `start.s` and generated
code against the i960 documentation before flashing. The stack initialization and
`flushreg` sequence retain the previous implementation and require validation.

Follow [REFLASH.md](../REFLASH.md): obtain an external-programmer flash backup
before replacing firmware. Milestone 1 is READY plus a working ping. Milestone 2
is a verified hello upload followed by the OMR1 payload marker. Record actual
results and toolchain versions in [REVIEW.md](REVIEW.md).
