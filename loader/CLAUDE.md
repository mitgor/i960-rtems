# Loader guidance for Claude Code

> **2026-10-10 architecture correction:** Intel i960 Rx manual §4.1 forbids
> instruction fetch from internal data RAM (0x000..0x3ff). The hello-at-0x200 /
> GO milestone described below is invalid on hardware. Current C tests check
> software behavior only. See [PROJECT-REVIEW.md](../PROJECT-REVIEW.md), item 12.
> Executable payloads need verified external memory; code has not yet been fixed.

Read README.md, PROTOCOL.md, and REVIEW.md before editing this subproject. They
record the 2026-10-10 review, implemented fixes, validation, and unresolved hardware
assumptions. The root CLAUDE.md points here for discoverability.

- Run `make -C loader test` from the repository root after software changes.
  Tests compile and exercise the actual C sender and firmware dispatcher.
- Protocol constants and address policy belong in mu.h. Keep sender, dispatcher,
  tests, README, and PROTOCOL.md consistent when changing the contract.
- Never reset the host sequence to zero without synchronization. Never accept a
  matching old acknowledgment or retry an unacknowledged WRITE automatically.
- Keep OMR0's HANDOFF acknowledgment stable. The demo's execution marker belongs
  in OMR1. Matching source builds are required; old binaries are incompatible.
- Payload RAM is `[0x200,0x400)`. Lower RAM is reserved. Do not widen the range to
  DRAM without verified board initialization/address evidence and revised tests.
- Register access must stay explicit and must not overwrite protocol registers.
  Do not fabricate DRAM timing values or treat the allowed policy window as a
  verified register map.
- Firmware has no data/BSS initialization. Preserve linker/image gates. Inspect
  target disassembly and frame usage whenever target code changes.
- `make all check` and `make image STOCK=...` need the real i960 toolchain. Local
  native test success does not establish hardware safety or target compilation.
- No flashing, remote box access, or hardware bring-up has been performed in this
  implementation session. Record measured results in REVIEW.md. Follow the
  existing backup requirement in ../REFLASH.md before flash replacement.
- Linux PCI ownership checks and advisory locking coordinate loadctl instances;
  they do not prevent unrelated tools or concurrent driver binding.
