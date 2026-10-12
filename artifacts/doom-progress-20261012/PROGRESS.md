# Doom follow-up — accepted physical baseline

## Diagnosed dispatcher window

The diagnostic-only batch first failed because host page-wide snapshot locking
starved WAD response 6 past the unchanged five-second loan deadline. Snapshot
reading now freezes the same 64 words, serializes short four-word groups and
lets the independently buffered WAD/UPL controls run between them. Every word
and paired audit remains. The actual host reader passes a concurrent test;
the old page-wide lock fails that test's service budget.

With that scheduling fix, the next card batch captured the previously ambiguous
bit 64 at tick 31,926: reason 2, executing TCB `c027e768` (worker 0), active slots
`[1,0]`, interrupt FP `c02b35e0` on worker 1's `c02b0210..c02c0210` stack,
PC `00142002` (priority 20), AC `00009002`, vector `f2`. The task identity had
changed while the outgoing stack remained in use. RTEMS's original dispatcher
publishes `_Thread_Executing = heir`, then enables interrupts before switching
contexts. The native interposition test reproduces this exact identity/stack
window in the actual upstream source.

The opt-in build-local `--dispatch-atomic` patch keeps masking through context
transfer. It also removes the subsequent level recapture, preserving the
original caller's level instead of accidentally replacing it with masked 31.
The native test proves restoration of levels 20 and 31. Upstream source files
are not edited, and patch hashes are recorded in build metadata. No ISR rejection
is relaxed; no idle owner is admitted. The fixed on-card batch passed at tick 100,085, including full final drain.

## WAD control polling

`--wad-poll` is an optional preemptible service of the existing serialized PIO
control channel during WAD waits, with periodic RTEMS yields. The previous wait
slept one tick before servicing each new condition. The new path checks owner,
briefly masks only the existing control dispatch and restores prior PC. Sequence,
CRC, EOF, exact destination loan, owner/STOP checks and five-second deadline stay
unchanged. The native owned/STOP/WAD-loan test passes with polling enabled.
The two normal cache probes took 0.405030272 and 1.218149970 seconds, versus
2.020082381 and 3.654042538 seconds in the prior fair-snapshot batch. These
combined changes across different boots give a 3.50× ratio of means, not an
isolated polling speedup or Doom frame rate. The timeout case still took 5.133 s.

## First-frame transfer budget

The accepted **older 32-bit host cache profile**, not the new private Newlib port,
was run through one rendered `demo1` frame with the pinned Freedoom phase-1 WAD.
It completed with hash `4000963876`, 13,804,084 logical read bytes in 2,183 reads,
27,648 cache misses and 14,155,460 wire bytes. Peak arena allocation was 6,461,029
bytes, plus the existing separate 1 MiB image reservation. This is not card Doom.

Independent cache replay matches every cache counter. Grouping only adjacent
misses within one logical read, without speculative read-ahead or extra bytes,
would reduce 27,648 requests to 4,747 at 4 KiB (82.83%), or 2,437 at 16 KiB.
This is a framing-count model, not a measured speedup or deployed batch protocol.
PIO data volume remains 14,155,460 bytes. Actual batching must add a negotiated
owned API, bounded fragment sequencing and CRCs, exact full-bounce loans, staged
commit without partial destination publication, STOP/error drain, and paired
audits. The old 512-byte ABI remains unchanged in the polling prototype.

Physical clean engine entry, normal / STOP / normal, code revalidation and final
drain passed. The test entry is
still the diagnostic preflight, not `doomgeneric_Create`.
