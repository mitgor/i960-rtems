# Runtime software loader — hardware validated 2026-10-10

**T4 complete (2026-10-10): [play Tetris over SSH](TETRIS-TERMINAL.md).** The terminal client passed a 30-minute real-SSH test: 35,846 native-matching frames, 68 restarts, 19.91 Hz. Quit, Ctrl-C, connection loss/reconnect and resize cleanup passed. Use `ssh -t mit@192.168.2.75 /home/mit/i960-tetris-t4/play.sh`. Full RAM restored, module unloaded; no reboot or flash.


**T5 complete (2026-10-10): [persistent BIO1 sessions](PERSISTENT-SESSION.md).** 1,000 frames matched native output at 41.1 ms median; a separate 400-frame run sustained 20 Hz. Process-kill/ownership cleanup and full final RAM restoration passed. `host/session/` keeps paired code/payload checks every frame and full staging audits every 32 frames and close. The subsequently completed T4 terminal client uses this transport; no reboot or flash.


**T3 passed:** [1,000-call hardware replay and latency](TETRIS-REPLAY.md), plus a separate 64-call repeat. The full conservative loader runs at roughly 3.26 updates/s; the subsequently completed T4 terminal client uses the faster T5 session transport.

**New consumer:** [T2 Tetris step payload](TETRIS-STEP.md) is implemented and hardware validated; it returns serialized game state plus framebuffer through BIO1.

**Extension:** [BUFFER-IO.md](BUFFER-IO.md) records completed T1: bounded input/output, card-generated text and 24×80 framebuffer, with repeated live validation. The original scalar milestone below remains valid.

The patched DAC960PG can now load and execute C software after Linux is up,
without rebooting or programming flash again. This is a transient, cooperative
RAM loader using the installed ROM PING hook. It does not change the hardware
boot mode to mode 0 or implement the older MU loader protocol.

## Live results

All three runs used boot ID `a9429ca4-0144-452d-8a80-7189608ce99b` on
`mit@192.168.2.75`, PCI `0000:37:09.1`, firmware 4.07-0-29, 16 MiB DRAM.

| Uploaded program | Input | Returned | Result |
| --- | --- | --- | --- |
| Fibonacci, 64 bytes | 10 | 55 | passed |
| Same program, new input | 20 | 6765 | passed |
| Different rotate/XOR program | `12345678` hex | `8c2f3b20` hex | passed |

Each run completed 110 firmware commands, verified paired full 512 KiB staging
captures before upload, after upload and after restoration, restored dispatch,
code and result RAM, and passed Enquiry2. All probes unloaded. The device is
left driverless. These health checks are not a SCSI disk-I/O qualification.
No flash erase/program command or reboot was issued during this work.
Recovery remains untested, as requested.

Evidence and exact module: [artifacts/software-loader-20261010](artifacts/software-loader-20261010/).
The restored RAM image SHA256 is
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`,
the previously boot-validated patched firmware. These new staging captures are
RAM snapshots, not fresh physical-flash dumps; physical-flash evidence remains
in [FIRMWARE-PROGRAMMED.md](FIRMWARE-PROGRAMMED.md).

## Build and run

Target sources and ABI: [loader/runtime](loader/runtime/README.md).
Host source, generator and CLI: [host/loadrun](host/loadrun/README.md).
From the repository root, build target programs using the existing remote toolchain:

```sh
make -C loader/runtime CROSS=/home/mit/i960/tools/bin/i960-coff-
python3 host/loadrun/build.py --out /tmp/i960-loadrun-module
make -C /lib/modules/$(uname -r)/build M=/tmp/i960-loadrun-module W=1 modules
sudo python3 host/loadrun/loadrun.py loader/runtime/demo.bin \
  --module /tmp/i960-loadrun-module/dac960loadrun.ko \
  --argument 20 --expect 6765 --output /tmp/i960-fibonacci-new-run
```

Run kernel build and load commands on the Linux PC containing the card. The
output directory must be new. The generator uses the pinned, archived runner
binary; changing runner assembly requires rebuilding, inspecting and updating
that pin and its literal offsets. The kernel module is tied to its build kernel.
The already deployed working CLI is `/home/mit/i960-runtime-loader/loadrun.py`,
module `module/dac960loadrun.ko`, programs `target/demo.bin` and `target/mix.bin`
under the same remote directory. The CLI archives all captures before unloading,
prints the return value and optionally checks `--expect`. It never unbinds a
storage driver automatically.

## Execution contract and limits

A program is a raw little-endian i960RP binary linked at `C0F2C000`, at most
64 KiB and a multiple of four bytes. Entry defaults to offset zero. The ABI is
`unsigned payload(unsigned argument)`; result is one 32-bit value. Programs
must obey the compiler ABI and return promptly, well within the two-second
command timeout. This is trusted native execution with firmware privileges,
not isolation. Do not use it for untrusted code, infinite loops, interrupt
replacement, flash programming or concurrent storage operation.

The function uses the firmware's existing call stack/register windows. Keep
stack usage small; no additional stack capacity has been established. No OS,
libc, startup runtime or automatic BSS initialization is provided. The supplied
linker script rejects BSS; explicitly initialized writable data can reside in
the uploaded image. Returning programs may modify their own image, whose
original firmware bytes are restored afterwards. The BIO1 extension now provides bounded buffer results; streaming I/O and a
resident task scheduler are still absent.

## Transaction and failure handling

The host checks the exact board/profile, staging pointer and installed-image
hash, saves touched RAM, and uploads with stock opcode 21. Paired opcode 20
reads verify the image. A temporary cache-control callback establishes cache
visibility; a 104-byte runner invalidates caches and calls the entry with g0
holding the argument. It stores g0 and the `RUN1` marker at `C0FAC280` through
the C1 alias, restores table `C001F9BC` to ROM PING `FEFE001C`, then completes
with status `017F`. The host submits the user execution command exactly once.

The host restores temporary code, result storage and uploaded staging bytes,
verifies paired readbacks and the original hash, then checks firmware health.
Only benign cache-control/PING callbacks may be retried. An uncertain execution,
DMA timeout or failed restoration retains the module and buffers. Do not force
unload or replay a payload after uncertainty; preserve captures and recover by
reboot/power cycle as appropriate. A host timeout cannot preempt i960 code.

Native ASan/UBSan tests exercise 194 command-boundary failure cases and the
64 KiB limit. CLI bounds/cleanup gates and all three live capture sets pass.
The generated module compiled with `W=1`; legacy loader tests also pass.
