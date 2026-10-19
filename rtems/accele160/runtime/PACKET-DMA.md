# Faster owner polling and packet-reply DMA

The owner services the independent console and application runtime every 5 ms
while idle. Full ownership/status audits remain at 100 ms and heartbeat writes
at 500 ms. This is an observed scheduling interval, not an interrupt-latency or
maximum Linux scheduling bound. `service/test_idle_poll.py` exercises the actual
production loop under a virtual clock, including a fault between audits.

## Ownership and publication

Packet replies borrow the existing DMA0 descriptor storage and existing guarded,
coherent host slot 0 only after Doom's verified retirement. No new PCI target,
DMA mapping, SCSI resource, kernel task or forced release is introduced. The
reply source is the fixed 4 KiB kernel application page at `c077b000`. Request
uploads remain PIO. The channel transfers that complete page, then a 32-byte
completion marker at the existing frame marker offset. The marker includes a
distinct magic, service epoch, exact request sequence, source, length and inverse
identity words. Frame counters remain frame counters; DMA log words 17–20 record
packet completions, pending phase, request sequence and final observer polls.

Init checks the retired-game gate, channel drain and peer channels before
starting. After publication it observes at most 1,000,000 register polls. Error,
timeout or failed drain enters existing terminal containment with sources,
descriptors and host targets retained. Normal completion disables CE only after
CDAR/NDAR/count/CSR prove the finite chain drained, then rechecks peers. There is
no abort, retry, uncertain fallback or host-buffer release.

The host validates capability word 427 (`31414d44`), publishes reserved request
word 5 as one, and reads the coherent marker instead of polling a full PCI page.
It requires exact epoch/sequence and stable marker around the 4 KiB host-memory
read. An old marker is ignored until the existing finite request timeout; an
uncertain request quarantines the runtime. A partially matching or unstable
marker also fails closed; this conservative policy may quarantine on a torn
read rather than retrying it. Native tests document that boundary; a passed
endurance run does not prove all possible marker-read interleavings. Only reply operations 5 and 7 accept
DMA. A successful CLOSE legitimately increments the service epoch; other replies
must preserve it. The independent diagnostic console remains available.

Root-only JSON clients select `transport: pio`, `dma`, or `dma-check`. The last
also reads the entire reply through PIO and compares all 4096 bytes; it is a
qualification mode whose additional cost is excluded from speed measurements.
`Client.call(..., transport=...)` selects explicitly; `I960_REPLY_TRANSPORT` sets
the default for reply operations only. PIO remains the default until measurements
justify a production change. A kernel without the capability refuses DMA before
publication. Marker contents never authorize a new owner to adopt resources.

## Qualification sequence

1. Record old polling latency, close the module and shut down the owner cleanly.
2. Reset the host; retain all old targets until reset. Start a fresh frozen bundle.
3. Pass the ordinary 64-frame baseline, 32 paired frame comparisons, guarded
   ownership/vector checks and 5,045 WAD reads before application admission.
4. Upload the combined network/application module. With TUN stopped,
   `benchmark_dma.py` first compares 32 complete DMA/PIO reply pages, then
   alternates PIO/DMA order for 64/256/1024/1400-byte UDP echo payloads. Payload
   nonce, packet length, addresses, ports and IPv4 checksum are checked without
   retries. A final query gives one further complete-page comparison.
5. Compare host round trips under the same 5 ms owner cadence; retain all samples
   and CPU ticks. Do not call the old-to-new polling gain a DMA gain. The measured
   result concerns a 4 KiB reply transport, not input DMA or direct NIC access.
6. Restore routed HTTP and prompt, then run an extended mixed workload using the
   selected transport. Keep predetermined HTTP/console/UDP/application limits.
   Exercise cancellation retention concurrently and check DMA guards afterward.
7. Archive exact kernel/module/tool sources, manifests, native tests, raw replies,
   benchmark/endurance summaries and restoration evidence.

`endurance.py` now checkpoints every five seconds rather than rewriting its
entire growing result several times a second. It always saves a final snapshot.
Underlying owner journals remain unbounded; disk availability must be recorded
for longer tests. The one-hour run passed on 2026-10-19; eight hours remains
a separate qualification. See the dated artifact README for actual completion;
this design document does not claim hardware results by itself.

## Commands after a fresh reset

```sh
sudo python3 start_packet_service.py --root /home/mit/i960-packet-dma-20261019
sudo env I960_RUNTIME_SOCKET=/run/i960-combined.sock python3 benchmark_dma.py --out benchmark.json
sudo bash start_link.sh /home/mit/i960-packet-dma-20261019 pio
sudo env I960_RUNTIME_SOCKET=/run/i960-combined.sock I960_REPLY_TRANSPORT=pio \
 python3 endurance.py --seconds 3600 --out endurance.json
```

Do not run the start script on a retained owner. It refuses loaded reservation
modules. Do not rerun an uncertain DMA operation; inspect retained state and
recover by reset before a new owner. Freeze and verify all candidate sources
before launch; use root operational tools for live controls so the frozen bundle
remains unchanged.
