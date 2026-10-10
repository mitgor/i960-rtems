# RTEMS working guidance

**Current development roadmap:** [loader memory extension, RTEMS and remaining gaps](../DEVELOPMENT-PLAN.md). Next: M1, generalize the proven larger RAM profile; preserve scalar/BIO1 compatibility.


Read [README.md](README.md) and the dated artifact report before changing this
port. It already runs real RTEMS Classic tasks and lwIP on the i960RP, with
card-originated DNS/TCP/HTTP through the Linux host.

Preserve the cooperative contract: firmware owns its interrupt vectors/timers,
RTEMS stays at priority 31 during each bounded call, and the outer entry restores
firmware priority. The host supplies elapsed time. A standalone/preemptive BSP
or independent mailbox transport has not been validated.

Only the known staging allocation is borrowed. Keep RIO1 workspace limits,
immutable guards, paired readbacks, sequence/no-retry rules, failure pinning,
exclusive ownership and full close restoration. Do not alter Tetris's BIO1
layout to fit RTEMS. Do not force-unload a pending/uncertain module.

The old RTEMS BSP's interrupt/clock code contains board assumptions and defects;
never enable it just because it compiles. Current Newlib use is headers plus a
small freestanding runtime, and lwIP uses the raw API from one RTEMS task.

`make -C rtems test` is offline. `deploy.py` builds in a new remote directory and
does not touch hardware. `transport/relay.py` is an explicit live test which may
also change routing when `--internet` is provided; it saves a cleanup journal.
Use fresh output directories and retain exact target/module/source hashes.
Artifact source snapshots are historical evidence and must not be modernized.
