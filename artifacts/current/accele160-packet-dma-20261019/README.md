# Accele160 host polling and packet-reply DMA — 2026-10-19

Implemented and tested on Accele160 `0000:37:09.1`, on boot
`724cee4d-a331-4cbb-840b-7b5bb5541ccc`, PCI owner PID 3298. The prompt,
PIO network relay, public IPv6 HTTP page and browser gateway were left running.
The previous owner closed cleanly; this candidate required one host reset.
Recovery tests below did not replace the PCI owner or reboot.

## Results

- Idle host pump: 100 ms → 5 ms; ownership/fault audits remain 100 ms and heartbeat 500 ms.
- Sixty status-query round trips: old median 205.638 ms/max 410.856 ms;
  new post-endurance median 38.506 ms/max 44.708 ms (about 81% lower median).
  These are service measurements across separate sessions, not IRQ latency bounds.
  The separate `fast-poll-baseline.json` sample was under load (median 43.279 ms).
- Fresh normal profile-5 baseline: 64 frame-DMA transfers, first 32 compared with
  PIO, 5,045 WAD reads, owned vectors/interrupt stack and guards verified.
- 235 complete 4 KiB packet-reply DMA/PIO comparisons: 33 benchmark,
  200 under mixed load, two bracketing recovery and module epoch changes.
- Raw packet replay: 352 UDP exchanges, exact payloads, addresses, ports and checksums.
- DMA endurance: 3,603.059 seconds, 78,344 workload events, zero errors,
  zero packet drops, intact guards. Owner journal contains 151,739 successful
  DMA replies within the endurance interval. Workload events and RPC replies
  are different counts.
- Events: 34,560 console, 9,682 counter, 9,682 echo, 11,726 HTTP,
  11,726 UDP and 968 application restart cycles.
- Maximum endurance round trips: HTTP 620.577 ms, UDP 218.518 ms,
  console 106.607 ms, counter 163.613 ms, echo 314.639 ms, restart 740.270 ms.
  The baseline verifier also includes earlier active-Doom console activity;
  its whole-session maximum is 4,827.905 ms, not the idle endurance maximum.
- Concurrent loan: 6,291,424 bytes written and verified in 192 steps;
  two pins retained on cancellation, close refused with status 12, then drained
  release succeeded. Maximum RPC 161.796 ms. This loan was not a DMA target.
- Recovery: relay STOP/CONT and KILL/TUN loss, broker KILL/restart,
  abandoned client, occupied upload refusal, partial upload START refusal,
  abort, full reload and fresh application BSS all passed. Same boot/owner;
  reply DMA still worked after two epoch transitions.
- Final interactive `stats`/`net` succeeded, global IPv6 HTTP returned 200,
  browser gateway returned 200. IPv4 SSH recovered without configuration changes.
  IPv6 SSH remained usable during the temporary IPv4 handshake problem;
  its root cause is unproved. See `ssh-path-note.txt`.

## Performance decision

Forty trials per transport and payload, alternating order, same 5 ms pump:

| UDP payload bytes | PIO median ms | DMA median ms |
|---:|---:|---:|
| 64 | 24.293 | 21.168 |
| 256 | 21.948 | 20.963 |
| 1024 | 21.974 | 22.025 |
| 1400 | 22.555 | 33.712 |

Twenty routed HTTP requests per transport had medians 150.431 ms PIO and
150.167 ms DMA. No consistent DMA acceleration was established; **PIO remains
the production default**, DMA is opt-in. Polling improvement is not a DMA gain.
Packet DMA moves the fixed 4 KiB reply page and marker using the existing DMA0
and pinned slot, only after Doom retirement. Inputs stay PIO. No direct NIC DMA,
simultaneous frame/packet DMA or new shared allocation ownership is claimed.

Native tests cover bounded chains, timeout/error retention, stale and malformed
markers, no fallback, full-page corruption, epoch changes, broker arbitration,
production idle-loop cadence and retained-memory rules. They supplement the
hardware run; no fresh packet-DMA fault/NMI/stall injection was performed.
Eight-hour endurance, bounded long-term journals, Internet-side ingress and
unrestricted task cancellation remain open. The conservative marker reader
quarantines partially matching/torn markers rather than promising all possible
interleavings work. Host filesystem had 192 GiB free at final restoration.

## Reproduction and evidence

`tested-live.tar.xz` (23,528,788 bytes) SHA-256:
`2136e2ff4b5430b46effaf0006c0b9ec7279959a1cfc64498b21d77592b7736f`.
It contains the exact frozen bundle, kernel/module binaries, source manifests,
build dependencies, root operational tools, native test, raw owner/session
journals, benchmark/recovery/endurance data and HTTP capture. Live logs were
copied into a snapshot and every JSONL line parsed before archiving, without
stopping the PCI owner. This is a point-in-time snapshot; final prompt/gateway
checks are also saved separately. The superseded preparatory archive was removed
once this exact tested archive passed replay.

Kernel SHA-256:
`a3d6722a907ed59dab707d5715d1cb4b476b7dd192662e319e2656b001188503`.
Network module:
`0838b698ba78c1b58a578f46137d1e11adb5e25d1bcbb0da22c370aa627757bf`.
Firmware unchanged:
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

From repository root:

```sh
python3 rtems/accele160/runtime/verify_packet_dma.py artifacts/current/accele160-packet-dma-20261019/tested-live.tar.xz
python3 rtems/accele160/fault/verify_runtime.py artifacts/current/accele160-packet-dma-20261019/tested-live.tar.xz --live
python3 rtems/accele160/runtime/test_host.py
python3 rtems/accele160/runtime/test_broker.py
python3 rtems/accele160/service/test_idle_poll.py
```

Both archive replays passed; outputs are saved here. Native test captures include
runtime/card adapter sanitizers and remote 32-bit packet-DMA sanitizers.
See [design and operation](../../../rtems/accele160/runtime/PACKET-DMA.md).

Current tools: `/home/mit/i960-packet-dma-20261019`; immutable live bundle beneath
`bundle/`. Do not launch a second PCI owner or edit that bundle. `~/rtems-console`
uses the combined broker; `quit` only disconnects. The old wrapper is saved as
`~/rtems-console.before-packet-dma-20261019`. Use normal SSH to `mit@192.168.2.75`,
or the verified-key IPv6 fallback:

```sh
ssh -6 -o HostKeyAlias=192.168.2.75 mit@2a02:8106:40:9000:f662:19ee:dbad:1f1e
./rtems-console
```

Card HTTP: `http://[2a02:8106:40:9000::960]/` (tested from the Mac on the LAN;
not an external-Internet test). Browser gateway: host port 8088.
