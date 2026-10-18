# Owned exception runtime qualification

## Card result

The corrected worker-0 implementation passed two-game acceptance on boot
`a076f35d-c5ef-48b5-90fa-947ab4f53f8d`, kernel
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`.
All 128 guarded DMA frames, 64 paired PIO comparisons, 10,090 WAD reads and
both idle/rearm boundaries passed. There were 965 external console exchanges
with no connection errors, and 964 validated card replies. Expected invalid
commands were rejected locally. Worst recorded card reply latency was
4938.153 ms, close to the unchanged 5-second deadline; no tighter latency bound
is claimed.

The six live ownership captures (ready, each frame 32, each idle, final QUIE)
all passed. Task handoffs grew from 8 to 16,595 and ticks from 8 to 18,922.
The final snapshot retained owned NMI/table/ISP and intact guards after worker
and ISR drain. Raw QUIE/ACK and pending admission/pins confirm reset-only
shutdown. This is bounded normal-operation qualification; it does not claim
active-DMA fault containment, broad engine exclusion or indefinite endurance.

Evidence: `artifacts/current/accele160-owned-runtime-20261018/acceptance.tar.xz`
and `acceptance-replay.json`. Reset recovery and live prompt restoration also passed on boot
`b0732f10-debf-4bb3-8adc-e7e0bdc0fa91`, with the same kernel, another 64-frame
game and 525 error-free external exchanges. The accepted ownership profile is
left live in idle; the previous two-game acceptance session itself is stopped.
The existing stream gateway was restored without replacing the owner. This
live restoration snapshot does not claim its own global STOP or later reset.

`ACCELE_TERMINAL=1 ACCELE_TERMINAL_TEST=5` is the no-injection runtime profile.
The historical build key is named `terminal_test`, but 5 means normal operation
with owned fault/NMI vectors and ISP. It is distinct from tests 1–4. The shared
`at_request()` deliberately excludes 5, including the old injection token.
Modes 0–4 retain their prior meaning.

The profile installs the same verified 32-entry local fault table, cached NMI
entry and guarded architectural interrupt-entry stack as the tested mode-3/4
paths. Normal RTEMS timer entries use this ISP; the existing per-task ISR
continuation stacks remain separate. On ordinary global STOP, the existing
borrowed timer restoration runs; fault/NMI/ISP ownership remains installed
through the final reset-only QUIE park. No stock-firmware return or command
completion is claimed.

## Fresh runtime evidence

Host words 3/4 contain an authenticated snapshot nonce and sequence. During
normal worker-0 polling (the same independent task that services the console), a new sequence causes an actual MMIO/table and
guard snapshot. Card words 167/168 record ticks/handoffs; 169 records IRQ faults;
170 ownership validity; 171 phase (running 0, drained 1). Word 166 acknowledges
last after `syncf`. Samples are immutable until the next request, so the host
can read them without requiring a broad interrupt-masked copy. Reads of safe
DMA CCR/NDAR/BCR remain observational; active transfers are allowed.

The host checks actual table entries, ISP, cached vector, guards, no terminal
entry, no NMI-test arm, and exact request/phase. The sample is saved before
validation so a failed check preserves evidence. A second read checks stability.
The ready, frame-32 and game-idle checkpoints require live task progress.
At STOP, after worker/ISR drain and borrowed-timer restoration, the kernel
captures phase 1 before publishing QUIE/ACK. The host validates that final
sample without sending another request to the parked processor.

These are point-in-time ownership checks, not a continuous watchdog or an
atomic snapshot of all concurrently changing hardware. An invalid ownership
check parks with software code `7d019`; it does not free buffers. The profile
does not inject an exception while DMA is active or prove SCSI/cache exclusion.

## Reproduction and evidence

Use an isolated copy of the accepted shutdown-safe service bundle:
`/home/mit/i960-owned-runtime-20261018/bundle`. Preserve the corrected admission
module and its exact source; this change does not edit that independently
qualified module. Pass `inputs/admit_command.ko` as the optional final argument
to `write_manifest.py` so its source/module pins remain explicit.

Build with terminal profile 5, service, persistent/reusable Doom, 32-frame paired
capture support and keyboard FIFO. Refresh bundle file hashes. Launch two
64-frame games with `--restart-cycles 2 --capture-all --paired-frames 32` and
exercise the console concurrently. Archive the complete session and exact
bundle before reboot. Replay with `verify_runtime.py ARCHIVE`. After paired
fresh firmware reads, restore a live profile-5 prompt and retain a separate
`verify_runtime.py --live ARCHIVE` receipt. A live prompt snapshot is not its
own global STOP receipt.

Native `test.sh` covers profile-5 injection refusal, stale snapshot nonce,
immutable acknowledged samples, new sequences, final phase, corrupted ownership
containment and host field tamper rejection. Native tests do not qualify the
physical interrupt stack; only the actual game/runtime and recovery captures do.

## Sampling correction found on the card

The first candidate polled snapshot requests from Init. Startup passed, but a
frame-32 request timed out: Init stays inside `bridge_poll()`'s Doom callback
for the game, while the independent workers continue running. The failure path
completed global QUIE with no fault code and kept admission/pins retained.
That capture is `failed-controller-poll.tar.xz`, not acceptance evidence.

The corrected image polls from worker 0 only, alongside the bounded console
service. Init no longer polls profile 5, preventing two simultaneous report
writers. After both workers and ISR continuations drain, Init alone takes the
final phase-1 sample. Snapshot stability is still verified by the host.
