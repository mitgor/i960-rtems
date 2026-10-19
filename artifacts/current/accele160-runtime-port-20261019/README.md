# Accele160 application runtime and network port — 2026-10-19

This batch records the new opt-in segmented application service, partitioned
general heap, and IPv4/IPv6/HTTP module. Native results and actual hardware
results are kept separate. See [implementation and memory map](../../../rtems/accele160/runtime/README.md).

The first wire attempt (`first-wire-refusal.tar.xz`) passed normal RTEMS with
owned fault/NMI/IRQ-stack handling, then refused BEGIN before allocating memory.
i960 GCC uses a 32-byte segment structure and 272-byte manifest, whereas the
host had sent tightly packed fields. The corrected wire decoder reads each
little-endian field explicitly from its 184-byte protocol record. The refused
run's final archive and JSON prove QUIE/ACK, unchanged guards, and retained
pending callback/pins before reset.

`native-runtime.txt` covers allocation lifetime, cancellation while pinned,
stale handles, guard-failure retention, repeated segmented load/BSS clearing,
actual card-adapter state transitions and owner-channel timeout quarantine.
`segmented-tests.txt` adds fragmentation, slot exhaustion and 10,000 allocator
operations. `native-network.json` records UDP and complete TCP/HTTP for both IP
families through the real application entry; `network-regression.txt` records
the shared stack's sanitizer, malformed-packet, checksum and backpressure tests.
Cross-build logs accompany the actual archived binaries; a successful build is
not treated as hardware evidence.


`idle-race.tar.xz` preserves the second run. The corrected decoder loaded and
executed the hello app, all eight on-card heap proof bits passed, and close
returned to zero reservation. Beginning the subsequent network upload raced
with the host's last Doom rearm audit: card idle preceded host qualification.
The rearm gate correctly refused (status 45); failure STOP reached QUIE and kept
the callback pending. The final host now publishes the application socket only
after all idle audits, and owns the idle lease until shutdown. The hardware
replayer checks that the first application request follows the final idle
console selftest, not merely the card's idle flag.

`network-qualified-before-reconnect.tar.xz` contains the third run's successful
hello/load/unload/heap tests, two network loads, raw IPv4/IPv6 UDP+HTTP, and Linux
TUN ping/curl captures. Stopping the relay then exposed a completed-reply peer
cleanup bug in the host socket server. The diagnostic prompt stayed healthy;
`relay-stop-final.tar.xz`/JSON prove clean global STOP and retained pins/callback.
The live tar reported its changing application journal during capture; preserve
it as historical evidence, not the final stable replay. The final host closes a
broken peer after completed I/O and accepts reconnect, while uncertain I/O stays
quarantined. A native socket test covers disconnect after publication/completion.


## Final qualified run and restored service

`tested-live.tar.xz` is the stable final capture, replayed by
`rtems/accele160/runtime/verify.py` into `tested-replay.json`. Session
`20261019T140746Z`, boot `2433f02b-0e55-4467-a072-0b2c70c8fb48`;
kernel `d3865059b0c54b1f77dbbe434cd710be83431254b9cfbafd5bd857e21db54e40`. It includes the exact immutable bundle,
card binaries/maps/objects/module manifests, paired firmware reads, owned
snapshots, console and application journals, all qualification scripts, raw/TUN
traffic results, and deliberate disconnect/reconnect evidence.

- 64 frames / 5,045 WAD reads / 721 external baseline console exchanges;
  245 more during networking, zero external errors.
- Hello text, two zero-reservation closes, three passing heap proofs, three
  module loads; both network loads pass IPv4/IPv6 UDP and complete TCP HTTP.
- TUN: 5/5 IPv4 and IPv6 pings, UDP/TCP socket echo, HTTP 200 for both families.
- Deliberate abandoned client reconnects; 109 module calls during two
  seconds without host packets. No poison/busy indication.
- `restoration.json` confirms the prompt, both card HTTP addresses and gateway
  8088 after restarting the relay. All three services are active. The module
  stays loaded; its reservation is intentional, not a leak.

The relay was stopped briefly to capture a stable journal, then restored with
`--seconds 0` (service lifetime). It does not install public routes or NAT.
The IPs are private to the Linux TUN link; SSH forwarding can expose the page
locally: `ssh -L 8080:10.196.0.2:80 mit@192.168.2.75`, then browse localhost:8080.
The original immutable normal bundle remains available for reboot-based rollback.
This is an initial bounded service port: unrestricted task cancellation, larger
workspace, general malloc/realloc/shared references, outbound DNS/Internet,
public IPv6 and endurance/journal rotation remain explicit follow-up work.
