# Accele160 P3g: refuse DMA resume and a corrected retry

Profile 12 deliberately invalidates only the recorded expected source fingerprint
after the original suspended-DMA timeout. It calls the actual resume gate,
restores the expected fingerprint, and calls again with the attempt still latched.
A second bounded observer checks that the same transfer remains suspended.
Source bytes, descriptors and actual ownership are not deliberately damaged.

## Artifacts

- `prepared.tar.xz`: exact diagnostic kernel, source, inputs and manifest.
- `build.txt`, `native-tests*.txt`: build and native validation, including the
  actual refusal C path with simulated MMIO and host evidence rejection tests.
- `previous-modes-replay.json`: previous modes 6–11 replay successfully.
- `refusal-disassembly.txt`, `entry-and-loop-audit.json`: compiled evidence flip,
  restore, both gate calls and the second 10000000-poll observer.
- `previous-final.tar.xz`: previous normal session `20261019T033558Z` clean
  shutdown; `previous-final-replay.json` checks final STOP/retention evidence.
  Full live replay for it is in `accele160-nmi-dma-resume-20261019`.

[Implementation and layout](../../../rtems/accele160/fault/DMA-REFUSAL.md).
The diagnostic preserves reset-only resource ownership. It does not establish
arbitrary corruption recovery, NMI-path refusal, hardware DMA abort, release
without reset or a wall-clock deadline if the bus stops answering MMIO reads.

## Hardware result

Profile 12 passed in session `20261019T034552Z`, boot
`9348292a-bc72-4b93-b53d-a8f4a7fcaeb3`, under
`/home/mit/i960-dma-refusal-20261019`. Diagnostic kernel SHA-256:
`8b92560af53f7b4a7b88e5d0bc8cd9c88230df14cc322992c45498626c3cb05a`.
Exact Accele160 BDF: `0000:37:09.1`. Both pre-test firmware reads match
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

Real fault entry and the first 10000000-poll timeout recorded CSR=0x400, CCR=0,
DAR=0xc0821000, NDAR=0xc0821020, BCR=64872, DCR=7. The diagnostic changed the
expected source fingerprint from 0xdb369dc5 to 0xdb369dc4. The actual gate
returned with attempt=1. Restoring 0xdb369dc5 and calling again left attempt=1;
all resume/enable observation fields stayed zero. The second observer exhausted
10000000 polls with the exact same outstanding DMA state. Trigger-to-record
time was about 4.976 s, not a guaranteed wall-clock timeout.

The host retained a 664-byte exact source prefix followed by untouched initial
bytes, no marker, and an untouched second target. Guard, full core fingerprint,
independently visible odd-page, peer-register and allocator ownership checks
passed. STOP and denied ordinary unload preserved the record. After host-owner
exit, pins were still retained, host buffers matched byte-for-byte, and admission
was `done=0 released=0 submitted=1`. No flash was written or DMA memory freed.

`tested.tar.xz` contains the exact bundle, raw captures and post-owner-exit audit.
`tested-replay.json` and `hardware-state.json` summarize the evidence. Replay:

```sh
python3 rtems/accele160/fault/verify_dma.py artifacts/current/accele160-dma-refusal-20261019/tested.tar.xz
```

## Recovery and normal prompt

Both resets returned without physical intervention. `recovery.json` links the
diagnostic to normal session `20261019T035012Z`, boot `9cbbb969-28b2-4bd2-94c7-eb266f112a87`,
and two fresh complete firmware reads with the same expected hash. Original
normal kernel SHA-256 remains
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`,
from `/home/mit/i960-owned-runtime-20261018/bundle`.

Restoration passed 64 frames, 5045 WAD reads and 709 external console exchanges
with zero errors, plus three owned-state snapshots. Maximum recorded console
reply latency was 2562.796 ms. `restored-live.tar.xz` contains that bundle,
session and `restored-console.json`; `restored-replay.json` validates them.
The prompt is at verified idle, the zone loan is returned, and gateway 8088 is
active with HTTP 200; see `restored-prompt.txt` and `restored-services.txt`.

```sh
python3 rtems/accele160/fault/verify_runtime.py --live artifacts/current/accele160-dma-refusal-20261019/restored-live.tar.xz
```

Use `./rtems-console` from the Mac project or `~/rtems-console` on Linux.
Next is NMI-specific refusal using invalid recorded source/acknowledgement
evidence while preserving the actual acknowledgement and suspended DMA.
