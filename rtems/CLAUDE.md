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

## IPv6 milestone (2026-10-11)

The current net target is dual-stack. See [usage](README.md#ipv6-usage-and-scope)
and [evidence](../artifacts/rtems-ipv6-20261011/README.md). Installed launcher:
`/home/mit/i960-rtems-ipv6-20261011/serve.sh --ipv6`; `--internet6` enables NAT66
and IPv4 DNS routing. Raw IP input is operation 1; operation 5 selects AAAA/IPv6
HTTP, while operation 2 remains IPv4. Static ULA, MTU 1500, no fragmentation,
SLAAC or autonomous polling. Keep shared `lwip_patches.py` DNS packing and
mandatory IPv6 UDP checksum adaptation in native and target builds. Preserve
IPv6 forwarding/accept_ra journal rollback and verify both IP families.

## Web and hardware-interrupt checkpoint

See [current report](../artifacts/rtems-web-autonomous-20261011/README.md).
The `net` profile serves bounded HTTP on port 80. `--publish-http6 <host-global>`
with `--internet6` explicitly publishes it through DNAT (default port 8080).
Only four clients and 512-byte headers are supported.

The separate `irq` profile proved eight hardware interrupts/eight RTEMS task
wakeups and restored timer/vector/mask state. `auto` and `autonet` now pass
host-silent progression tests (20 and five seconds respectively). Use only the
exact image-pinned `dac960auto` transport from `autonomous/build_transport.py`
(`--network` for autonet: STOP operation 6; auto uses STOP 2). Kernel release
verifies STOP before RAM restoration, including SIGKILL and a completed
application error. Live cleanup passed for both signals and invalid operation.
Never load an autonomous image with the cooperative transport. Retain stock
interrupt sources, preserve timer 0, and keep IRQ work bounded. This does not
establish nested IRQ support, unrestricted preemption or independent transport.
