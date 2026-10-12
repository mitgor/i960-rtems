# Owned application runtime and real i960 exit context — 2026-10-12

The accepted `live2` batch executes the pinned Newlib i960 setjmp/longjmp
assembly on the card, through the shared arena's worker-1 ownership contract.
This is a 1,872-byte code/data/BSS proof, not the Doom engine.

`accepted-live2.tar.gz` contains exact sources, target, module, build logs and
captures. Kernel SHA256:
`7481c79fcc31bc6f9a37aac8066f9351402a8b33e4c99be7e8b32cbb5ef62a48`.
Probe template SHA256:
`ce65aa2634f9a90fbfa53a7ce8a0b87d83c6d05307de111ad68a5b811ec00173`.
The unchanged pinned setjmp source SHA256 is
`985670ef149136309d06a65a982467ffbd7a3606ec470f1d382e0f07d2132237`.
The proof has 1,668 file bytes, 192 BSS bytes and 46 R_960_32 relocations.

## Results

Normal / invocation STOP / normal returned `2070639194`, `2070639178`,
`2070639194`. Each preserved the six-level stack-canary walk, made two nonlocal
jumps, released its 512-byte buffer, and ended the application scope.
Normal durations were 11.40 and 11.25 seconds including readback; cancellation
completed in 4.71 seconds. The live result codes were 37 / 53 / 37; flags 3
confirm the invalid 1,001 ms wait and priority-31 refusal checks.
Five stale generation requests were refused without poisoning the session.
Global STOP drained both workers, IRQ, image and heap at tick 21,511.

The ABI is a 128-byte i960 envelope with the unchanged 96-byte runtime prefix,
owned identity/version/features, and owner/wait/stopping hooks. Generations
never wrap or repeat. Allocation and WAD reads refuse STOP; releases remain
allowed for the active owner during cleanup. Wait is bounded to 1,000 ms and
uses actual RTEMS yields. A peer holding the arena mutex does not invalidate
this worker's scope; this worker holding it does.

Full native C command replay passed 677 commands / 1,723 PIO ioctls. Network
replay (803 packets / six rounds) and full paired audits passed. Nine owned, eight WAD, nine cache and
seven relocation evidence mutations are rejected, in addition to the existing
snapshot checks. Native ASan/UBSan ownership/exit tests and shared-arena TSan
passed. Native replay models the i960 ISA probe's arithmetic/context behavior;
the physical captures establish actual i960 jumps.

## The failed first attempt matters

`failed-live.tar.gz` preserves the initial refusal and retained-session failure.
No valid nonlocal proof execution was established in that attempt. The historical
RTEMS `_CPU_ISR_Get_level` restores the prior PC using an output operand that
then receives priority 31; its return value is therefore misleading. The new
ownership predicate reads PC directly with `modpc 0,0`, requires priority 20,
and independently rejects ISR/dispatch-critical/caller-held-mutex contexts.
The global historical getter is **not repaired** here. Both failed and accepted
exclusive sessions were followed by reboot; no retained module was force-unloaded.

## Reproduce

Extract the accepted archive. Use `rtems/residentnet/verify.py --root ROOT
ROOT/live2` for network/snapshot evidence and `verify_upload.py ROOT/live2
--doom-heap --doom-shared --doom-runtime --wad FREEDOOM1 --entry
ROOT/residentnet/entry/runtime-probe.bin --output RESULT` for the native core.
Use the four `test_*_evidence.py` tools beside those verifiers for mutation checks.
The required Freedoom WAD is pinned by SHA in the capture and prior artifacts.
Public IPv6 HTTP was restored and returned HTTP 200 before the following engine
admission test claimed the card again. The final handoff is recorded separately.

Final handoff: production PID **10459**, boot
`fb571026-a145-4e76-a30c-240e3953dfe3`, bound `dac960auto`; public IPv6 HTTP
returned 200. The exclusive test resources were released by reboot.
