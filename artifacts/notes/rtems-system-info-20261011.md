> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Live RTEMS web system information — 2026-10-11

The IPv6 Vader page now renders live card uptime and HTTP/network counters,
RTEMS/lwIP versions, CPU identity and memory configuration. CPU load and
temperature are explicitly unavailable; timer-bus frequency is distinguished
from unmeasured CPU frequency. [Implementation and limits](../../rtems/net/SYSTEM-INFO.md).

- Full native RTEMS suite, including ASan/UBSan network/formatter checks, passed.
- 24 on-card HTTP requests passed, including fragmented and invalid/oversize requests.
- Public IPv6 snapshots showed uptime 5 → 40 s, page responses 1 → 24,
  RX 36 → 248, TX 31 → 213, and zero drops.
- The new runtime stopped and restored all paired borrowed RAM successfully.
  Its module unloaded; the final production restart returned HTTP 200.
- No reboot or flash programming. Visitor logging remains enabled on the host.

## Preserved files

`live.tar.xz` includes target ELF/bin/map/disassembly, generated headers and
module/source, build log, source snapshot, pinned request identity, 24-request
acceptance, and full autonomous close captures. The build log includes a rejected
attempt to reuse a module output directory; the final module was built in a fresh
directory and checked against the final image. No failed module was deployed.

`source.tar.xz` preserves final local net sources, tests, build/launch scripts
and documentation. `native-tests.txt` / `network-tests.txt` record native checks.
`http-tests.json` records live HTTP checks; `dynamic-check.json` and `http*.txt`
record growing uptime/counters; `production-http.txt` is the final restarted
page. `verification.txt` records exact binary identity and complete cleanup.
Raw live traffic traces and visitor address logs are excluded.

```sh
python3 rtems/net/verify_system_info.py artifacts/rtems-system-info-20261011/live.tar.xz
```

The artifact inventory and SHA256SUMS cover these files. This changes the bounded
production `autonet` page; it does not enable experimental unrestricted preemption.
