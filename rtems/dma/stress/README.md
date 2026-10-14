# Finite pinned-frame DMA stress

This producer isolates the real admitted-image, task-owned frame pin, asynchronous
DMA ioctl, guarded host buffer, ACK and owned STOP paths from Doom's lengthy WAD
startup. It is a diagnostic target, not a Doom performance benchmark.

Build `build_engine.py --out <workspace>/stress-engine` on the cross-toolchain
host, then pass its `admission/` directory to the residentnet build's
`--doom-engine` option with the same ownership/runtime/DMA flags as playable Doom.
Use `residentnet/live.py --frame-dma-stress 512` with full audits enabled. The
runner checks the admission manifest before touching hardware. Never use this
producer with the interactive Doom runner.

Each 65,536-byte frame has an independently reproducible byte pattern depending
on its generation and offset. A bounded delay changes the producer's phase
relative to the timer; this does not prove interruption at every DMA instruction.
Every frame retains all 73,728 coherent bytes, validates both 4 KiB guards,
checks the target's before/after CRC and re-reads the first payload window.
Frames 1–4, multiples of 32 and the last frame also receive complete paired
mailbox readback. ACK follows validation. The final frame is followed by owned
STOP and the existing global shutdown and full monitor/RAM audits.

Run `test_engine.py`, `test_replay.py` and `test_counter.py` locally.
`test_gate.py <admission>` additionally exercises real SHA/relocation/arena
admission and rejection with a modeled entry; run it on the Linux 32-bit native
test toolchain. It does not emulate i960 instructions.
The counter query must read zero before entry and a positive value before STOP,
proving that scheduled isolation checks actually observed an owned transaction. After a closed card run, both
`verify.py <capture>` and `../../residentnet/verify.py --root <workspace> <capture>`
must pass. Keep sources, admission, kernel/module, all journals and raw captures.
A timeout is negative evidence: retain ownership, archive before reboot, and do
not retry uncertain writes or release the coherent buffer.
