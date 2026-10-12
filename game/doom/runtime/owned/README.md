# Owned application runtime and non-local exit proof

**Current checkpoint — 2026-10-12:** the full-engine-linked diagnostic preflight
is physically accepted, including normal / STOP / normal, exact admission and
post-return code checks, contiguous 6 MiB allocation and complete drain at tick
100,085. Full capture replay now passes. This supersedes the earlier pending
entry/dispatcher gates below, retained as development history. Doom itself has
not initialized on-card. Next: validated WAD batching, bounded initialization,
first-frame verification and browser controls. [Evidence](../../../../artifacts/doom-progress-20261012/README.md).

The extension preserves ABI v1 as an unchanged prefix. A separate 128-byte i960
`doom_runtime_owned` table adds an `ODR2` envelope and owner/wait/STOP functions.
Its prefix points to scope-checked allocation, release, clock and read wrappers;
ordinary v1 proofs keep their original table and behavior.

## Admission and lifetime

Only existing worker 1 may enter a scope. ISR/dispatch-critical callers, masked
interrupt priority, controller/peer tasks, quiesced tasks and an arena mutex held
by this caller refuse owner admission. The established runnable priority is 20;
priority 31 is masked and cannot wait. Processor control is read without
modification; the historical RTEMS getter overwrites its saved value during
restore and incorrectly reports 31, so it is not used for this admission gate. A mutex held by the other worker is not
misclassified as a caller-held critical section. Native holder metadata is
atomic; target holder reads are volatile aligned words.

Begin requires the bound file, a valid owner, no previous active invocation,
no WAD loans and an idle mailbox. Generation IDs increment without reuse and
refuse wrap. End requires the same owner, no loan and an idle mailbox. The image
pin and registered task/IRQ owner remain live until execution, validation and
completion finish. End does not grant heap/image reclamation; final STOP still
requires both task/IRQ drains.

The scoped prefix refuses new allocation/read work after STOP. Release remains
available to the active owner for cleanup. Inactive/wrong-context clock returns
zero; read/allocation/wait refuse. A wrong-context release is fatal and retains
ownership rather than pretending to free. These are trusted-code interfaces,
not a sandbox or permission to call application libc from an ISR.

`wait_ms` is limited to 1,000 ms per call, in at most 100 one-tick RTEMS waits.
Zero requests one tick. Each wait checks owner and STOP before/after yielding;
worker 0 remains runnable. No idle IRQ owner or extra task is admitted.
STOP observed in a pending scoped WAD read cancels staging and returns the exact
loan before the function returns. The per-read 500-tick deadline is unchanged.

## Independent control channel

An application STOP differs from global RTEMS shutdown: it asks the current
application to stop at a safe point, allowing its owner to release allocations
and return while networking/control remain alive. It never forces a jump from
an ISR or interrupts a critical operation.

The existing session/epoch-checked UPL1 ioctl adds operation 5 (eight-word frozen
owned status) and operation 6 (32-byte `ODR2`, generation, six zero words request).
Control tokens `7b/7c` freeze/read status and `7a` requests STOP. Only an active,
matching nonzero generation accepts it. Stale IDs cannot cancel a later entry;
known refusal returns ESTALE without poisoning the session. Protocol uncertainty
retains resources and disallows write retry, as before. Host requests/replies
have their own `owned-journal.jsonl`, separate from UPL1 and WAD streams.

Status is `[ODR2, generation, running, requested, yields, completed,
invalid_waits, observed_stops]`. Counters are bounded unsigned diagnostics.
Frozen status is consistent across its eight control reads.

## Reviewed execution proof

UPL1 command 16 admits only the exact generated text/data/BSS geometry and byte
whitelist. It starts the pinned image under the shared metadata mutex, begins
an owned scope, applies only compiled trusted internal relocations and
synchronizes caches. The probe uses unmodified pinned Newlib i960 setjmp/longjmp.

It checks a six-level nested call chain with volatile stack canaries across
RTEMS yields; a first four-level non-local return; masked-priority and invalid
wait refusal; a bounded ten-second owner/yield loop; then a second five-level
exit with code 37 or cooperative STOP code 53. Its allocated 512-byte pattern
must remain intact, be released, and the initialized seed/code remain unchanged.
Eight stable result words are copied before mutable image state is restored.
Command 17 reports these scalars; saved jump-buffer register/stack pointers are
opaque and never become host-supplied destination permissions.

After postconditions, scope end, template/BSS restoration and cache sync, the
image completes under the mutex. A repeat must pass fresh admission. Unexpected
postconditions quarantine the image and abort the exclusive session.

The native test runs real C runtime/heap/loader logic under ASan/UBSan, modeling
processor priority explicitly while using native setjmp. It tests wrong task,
ISR/mutex/masked refusal, stale IDs, cancellation and normal recovery, plus
STOP during a scoped WAD read with no copy/remaining loan. This is separate from
physical i960 instruction/context acceptance. Run:

```
python3 rtems/residentnet/test_owned.py --entry BUILD/residentnet/entry
```

The physical harness keeps all earlier WAD/cache/relocation proofs and full
paired audits, then runs normal / application STOP / normal entries. Global
STOP follows those entries; it is not a separately timed global STOP-in-exit
injection. Reboot, never forced unload, releases the exclusive batch.

## Engine follow-up

This interface and small exit proof do not by themselves admit the larger engine.
See the separate [exact-build larger-image/preflight gate](../engine/README.md). The private
Doom port must bind the owned envelope and use its bounded waits/STOP safe
points, with cleanup before scope end. The larger exact image/relocation plan,
real initialization budget, first-frame comparison and frame/input lifecycle
remain separate gates. Never force non-local termination from a critical
section or return while any read/frame/allocator reference remains live.
