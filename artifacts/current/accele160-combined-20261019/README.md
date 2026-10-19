# Accele160 combined service — 2026-10-19

The card now runs lwIP IPv4/IPv6/HTTP, two bounded bundled applications and an
independent diagnostic console together. The applications are a counter and an
uppercase text service. This is not arbitrary concurrent segmented loading,
Doom beside networking, or unrestricted RTEMS task cancellation.

## Identity and live state

- Host `mit@192.168.2.75`, PCI `0000:37:09.1`, Accele160 `1069:0050 / 1069:0054`.
- Boot `8cdab7ff-48a3-481f-bb54-0924025016c0`; PCI-owner PID 2849 unchanged.
- Actual kernel/owner bundle `/home/mit/i960-reclaim-ipv6-20261019/bundle`,
  session `20261019T175819Z`.
- Kernel SHA256 `26b916dfd1c85a986d24b4bac17c7972b8b5108fed5bb56e9d0028afbed6bc80`.
- New module/operational root `/home/mit/i960-combined-20261019`.
- Combined module SHA256 `0838b698ba78c1b58a578f46137d1e11adb5e25d1bcbb0da22c370aa627757bf`.
- Firmware remains `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
- Four final services active: `i960-doom`, `i960-combined`, `i960-rtems-ip`,
  `i960-doom-stream`. The first is the only PCI owner.

`~/rtems-console` supports `net`, `app list`, `app start/stop counter/echo`,
`app echo TEXT` and existing diagnostics. `quit` only disconnects. The previous
wrapper is `~/rtems-console.before-combined-20261019`.

The broker front is `/run/i960-combined.sock`; select it with
`I960_RUNTIME_SOCKET`. The original runtime and diagnostic sockets remain
separate. Use root-level `public_ipv6.py` in the combined root for route cleanup;
the frozen bundle has earlier helper versions. HTTP at
`http://[2a02:8106:40:9000::960]/` was fetched from the Mac after restoration.
This is a routed LAN test of a global address, not proof of Internet ingress.

## Results

The final test ran 601.417 seconds with 4,837 events and no errors: 3,132 console
exchanges, 536 counter queries, 536 echo exchanges, 290 HTTP requests, 290 UDP
exchanges and 53 counter restart/stale-STOP cases. HTTP and UDP alternate IPv4
and IPv6. Maximum HTTP/UDP/console/echo round trips were respectively
2379.350/732.615/236.244/1657.962 ms. Network drops were zero before the recovery
reload as well as afterward; reloading did not conceal an endurance drop count.

Concurrent memory qualification wrote and verified 6,291,424 bytes in 192 steps.
Cancellation with two pins retained the allocation, module close was refused,
and final drained release passed. Maximum loan RPC was 829.627 ms. These are
host observations, not interrupt-latency bounds.

Recovery passed on the same boot/owner: abandoned client reconnect, occupied
upload refusal, relay pause with UDP timeout while console/apps kept working,
relay SIGKILL/TUN destruction, cleanup without TUN, broker SIGKILL/restart, and
restored HTTP. A first-chunk-only upload could not execute (status 10), remained
LOADING with zero calls, aborted without a reservation, then reloaded fully with
fresh application BSS. Both applications and routed networking were restored.

Failures are retained. `failed-direct/` records one HTTP timeout after roughly
eight minutes; later HTTP recovered and card drops were zero. The precise cause
is unproved. `broker-first/` is an early-stopped prototype, not a pass: it accepted
one peer then dispatched immediately, bypassing queue classification. The final
broker classifies already-arrived peers before 3:1 arbitration, with a native
socket test for that order. `recovery-first*` records unsupported systemctl
`--kill-whom`; the corrected `--kill-who` passed. An initial capture unit lacked
permission after tcpdump dropped privileges; final capture used `-Z mit`.

## DMA boundary and remaining work

`dma-evidence.json` independently replays eight existing hardware archives:
active-DMA fault/NMI, stalled-DMA timeout retention, controlled CE resume and
refused resume, profiles 6–13. `current-kernel-dma-baseline.json` replays the
current kernel's preceding 64 DMA frames and 32 paired PIO comparisons. These
are historical capture verification, not fresh combined-runtime injections.
Native production DMA tests passed under ASan/UBSan.

Packets still use PIO. Packet DMA performance, input DMA, frame/packet
arbitration and direct NIC DMA remain unqualified. The owner's 100 ms idle sleep
is a service-latency candidate; qualify a faster pump separately from slower
ownership audits before matched packet PIO/DMA measurements. Do not replace the
live owner in place. One-hour/eight-hour endurance, bounded owner journals,
arbitrary application task contexts and generalized cancellation remain open.

## Evidence and replay

`tested-live.tar.xz` contains the immutable build bundle and binary manifests,
root operational sources, sliced actual-owner application/console journals,
packet captures, broker scheduling records, endurance/loan/recovery replies,
failed attempts and final status. Sources at the root reflect the tested broker,
client, service, recovery and routing tools; bundle copies may predate fixes.
The archive was taken with the relay stopped after route removal, then the link
was restarted. `final-restoration.txt` and `global-http-final.*` verify afterward.

```sh
python3 rtems/accele160/runtime/verify_combined.py artifacts/current/accele160-combined-20261019/tested-live.tar.xz
python3 rtems/accele160/runtime/test_broker.py
python3 rtems/accele160/runtime/test_public_ipv6.py
python3 rtems/accele160/runtime/qualify_dma_evidence.py
```

See `rtems/accele160/runtime/COMBINED-SERVICE.md` for protocol, bounds and next
qualification gates. `SHA256SUMS` and the global artifact inventory cover this
batch, including its binary archive. No private keys or external credentials
are part of the capture.
