# AcceleRAID RAM-only owned-stack/STOP acceptance

On 2026-10-17, the AcceleRAID 160 at `0000:37:09.1` ran a new 8 KiB image
through the existing operation-13 firmware. The old PG at `0000:37:04.1`
remained unbound. Firmware SHA-256 was
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`
before and after. No `STOREIMAGE` or `FLASHIMAGE` command was issued.

The first [preflight attempt](accept-0/) caught an invalid direct read of
even destination page 0 and stopped before execution. Its completed card
copy reported the correct FNV. [Recovery](../../../../host/accele160/lease_probe/recover_preflight.py)
verified the copy/page/owner records, restored stage and loader bytes,
released the grant and unloaded the modules. The second [complete run](accept-1/)
used card-side digests for the even code page and PCI readback for the odd
stack page.

| Mode | Host-observed call | Card result | Stack bytes changed |
| --- | ---: | --- | ---: |
| No STOP | 1,036.7 ms | TIME after fixed 2,000,000 polls | 16 |
| Valid STOP after stale token | 23.4 ms | ACK with nonce/epoch | 4 |

The worker ran at SP `c0711fc0` inside the owned second page, and the
firmware SP returned to `c0002100`. The stack's bottom 256 bytes stayed
`0xa5`. Each call returned normally, restored the loader page and staging
source, and left all 512 allocator count/owner records unchanged. The grant
was then released, no one-shot module remained loaded, and the
[post-call 1 MiB read](postcall-flash/) matched the exact firmware with
status/residual/DMA-guard changes `0/0/0`.

Exact source, image, host harness and boundaries are in the
[lease subproject](../../../host/accele160/lease_probe/README.md). Replay:

```sh
python3 host/accele160/lease_probe/verify_live.py artifacts/current/accele160-lease-20261017 artifacts/current/accele160-ram-admit-20261017
python3 host/accele160/lease_probe/test_verify_live.py artifacts/current/accele160-lease-20261017 artifacts/current/accele160-ram-admit-20261017
```

Replay checks the prior two same-boot full reads, the post-call full read,
both upload/digest sequences, STOP and timeout reports, stack bounds,
allocator ownership and page restoration. Four altered flash, STOP,
restored-SP and owner captures are rejected. The result is a cooperative
returning-worker proof, not an independently enforced execution deadline or
RTEMS task-level STOP.
