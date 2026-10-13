# RTEMS and host networking: roadmap entry point

Updated 2026-10-11. The authoritative current roadmap is
[DEVELOPMENT-PLAN.md](DEVELOPMENT-PLAN.md). It integrates loader memory extension,
cooperative RTEMS, autonomous execution and all gaps in
[CURRENT-FINDINGS.md](../../CURRENT-FINDINGS.md).

The October 10 proposal assumed exclusive firmware takeover before RTEMS could
run. The implementation subsequently established a cooperative alternative:
RTEMS 4.6.6 tasks and lwIP 2.1.3 execute in bounded callbacks, retain private state
and exchange complete IPv4 and IPv6 packets through Linux TUN/NAT. Card-side DNS and HTTP
and a half-hour TCP test passed. See [implementation](../../rtems/README.md) and
[hardware evidence](../../artifacts/rtems-20261011/README.md).

| Original milestone | Current status / successor |
| --- | --- |
| R1: historical kernel/toolchain | Implemented and preserved; continue runtime/API work in integrated R1/R2 |
| R2: independent transport and monitor | Still unimplemented; integrated A1/A2 |
| R3: loading and BSP | Larger staging-backed image and cooperative kernel work; integrated M1/M2 generalize them, M3 investigates new RAM, A3 provides an autonomous BSP |
| R4: card network stack | Raw lwIP works; integrated R1 improves configuration/diagnostics, R2 adds OS adaptation if needed |
| R5: gateway and Internet | TUN/NAT, DNS/HTTP, packet validation and established-session cleanup work; remaining failure-boundary and API work is in integrated R1/R2 |

Next is **M1**, a supported general loader profile beyond 64 KiB using the
already-proven allocation. Independent transport, hardware preemption and
multi-megabyte RAM ownership are separate gates, not prerequisites for this
first extension. Retain TUN rather than restarting with TAP/ARP without a need.
Do not reselect the network stack or treat RTEMS as unimplemented.

The original detailed proposal remains in Git history at `4eb6133` and earlier;
its future-tense instructions are superseded by the integrated roadmap.

IPv6 is now live-tested: [implementation](../../rtems/README.md#ipv6-usage-and-scope),
[artifacts](../../artifacts/rtems-ipv6-20261011/README.md). This fits the current RIO1
reservation and does not depend on M1 or autonomous execution.
