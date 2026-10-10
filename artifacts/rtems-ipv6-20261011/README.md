# IPv6 on cooperative RTEMS — 2026-10-11

IPv6 is implemented and runs on the physical DAC960PG/i960RP alongside IPv4.
The card itself executes lwIP ICMPv6, UDP, TCP, AAAA resolution and HTTP. Linux
relays raw IP packets through TUN and routes/NATs them. This extends the
[previous RTEMS milestone](../rtems-20261011/README.md) without flash programming,
reboot, or expanding the existing borrowed RAM allocation.

## Tested implementation

- RTEMS 4.6.6, lwIP 2.1.3, GCC 3.3.6, binutils 2.27; same preserved upstream
  packages and compiler as the prior milestone.
- Static host `fd96:196:960::1/64`, card `fd96:196:960::2/64`, card link-local
  `fe80::960:2`; existing IPv4 addresses and echo ports remain available.
- `--ipv6` enables local dual-stack tests/services. `--internet6` adds scoped
  NAT66, AAAA lookup and IPv6 HTTP; it **also enables IPv4 forwarding/NAT for
  the current DNS server `192.168.2.3`**. No application socket proxy.
- Operation 1 accepts either IP family. Operation 2 remains IPv4 DNS/HTTP;
  new operation 5 selects AAAA/IPv6, with the same port/hostname body.
- Shared build/native patches preserve the ten-byte DNS answer ABI and reject
  zero-checksum IPv6 UDP. The pinned UDP receive path otherwise skips checksum
  validation when that field is zero; a native regression exposed this before
  the final target was tested on the card. IPv4 zero-checksum behavior remains.
- IPv6 gateway rule intent is journaled atomically before installation. Saved
  forwarding and uplink `accept_ra` values are restored on cleanup, including
  explicit journal cleanup following client SIGKILL.

The target is **315,108 bytes**, SHA256
`739d896aec015febf8cb81f4dd6f59b7838846ce25a9f31ae884dc1c2e3d076d`.
ELF section sizes: text 99,840, data 484, BSS 183,536 bytes. The flat image
includes the gap to private data. It fits the existing 128 KiB immutable text
region and 327,648-byte writable reservation; the prepared upload is still
471,136 bytes. The independent rebuild produces exactly the same target hash.
Kernel-module hashes can vary with build paths/debug metadata; the exact used
module and generated source are preserved.

## Live results

| Capture | Result |
| --- | --- |
| `local-dual` | IPv4/IPv6 ping: 4/4 each; UDP 1/31/500/1400 bytes; TCP 16,000 bytes each; 190 callbacks |
| `internet6-loss` | Both families recovered from one deliberately dropped echo TCP data packet and slow readers; AAAA answer, IPv6 HTTP 200, 892 response bytes; 436 callbacks |
| `ipv6-stress` | 180.199 seconds, 441 iterations, 1,876,865 IPv6 TCP bytes echoed exactly; subsequent IPv6 HTTP; 3,118 callbacks, 98 RAM audits |
| `cleanup6-tests` | SIGTERM automatic cleanup, SIGKILL plus explicit journal cleanup, and invalid operation 99 returning fatal `F0050002`; RAM restored and module unloaded |
| `launcher6-smoke` | Actual SSH foreground launcher, both families and bounded service interval; 222 callbacks; clean close |
| `ipv4-regression` | Dual-stack echo plus IPv4 A lookup/HTTP regression using the same target |

Stress SHA256: `b01f852eee377c804f71bde3304051f0133940bc5eb536dba8f67d79fa527e29`.
Its callback latency was 54.122–102.753 ms, mean 56.984 ms. Stack canary
high-water lower bounds were 28/1298/256 bytes for 2048/8192/4096-byte stacks;
these observations are not worst-case stack proofs.

The loss-test HTTP response hash is
`698bcf6abfea7c3a92107832c2f6f7025d0706a36713085460b9d368d5505149`.
The packet validator independently reconstructs the response from IPv6 TCP
from `2606:4700:10::ac42:93f3` to the card and matches the returned bytes/hash.
The DNS capture shows an AAAA question and answer carried over IPv4 UDP.
This distinguishes IPv6 card traffic from a host-side fetch.

Native ASan/UBSan tests cover IPv6 UDP payloads 0/1/31/500/1400/1452 bytes,
corrupt/zero checksum rejection, ICMPv6 and truncated inputs, plus existing
10,000-packet mixed-input tests. Gateway mocks cover each of four rule-install
failure boundaries, idempotent cleanup and foreign journal command rejection.
The existing wire/transaction fault tests also pass. These tests complement
hardware evidence rather than emulating i960 hardware faults.

## Preserved files and verification

- `target/`: exact binary, ELF, disassembly, map, symbols and pinned build metadata.
- `module/`: exact loaded kernel module; `build-products.tar.xz` additionally
  contains generated module source/headers, target libraries/headers and launcher.
- `build-project.tar.xz`: remote project source snapshot used for the target;
  final maintained tests/docs and evidence verifier are in the repository.
- `captures/`: original run directories, including packet/trace captures,
  RAM before/after images, close evidence and host gateway journals.
- `validation/`: independent packet/RAM reports and identical rebuild hashes.
- `logs/`: native test, build and live session output.
- `host-final.json`: post-test boot/module/interface/routing state.

The two earliest runs captured `ipv6-routes-after.json` before closing the TUN
file descriptor, so those route snapshots can still show `i960rt0`. Their
`cleanup.json` was recorded after descriptor close and confirms no interface.
Later captures take the final IPv6 route snapshot after closing TUN.

```sh
make -C rtems test
python3 rtems/verify_ipv6_artifacts.py
python3 rtems/verify_artifacts.py
python3 host/audit/artifacts.py --check-git
```

The dedicated verifier checks all eight run captures, including three expected
interrupted/invalid runs, full RAM restoration, stack guards, IP and transport
checksums, equal echo streams, DNS query family and the HTTP response against
its captured TCP stream. It does not contact the remote machine.

## Usage and remaining limits

```sh
ssh -t mit@192.168.2.75 '/home/mit/i960-rtems-ipv6-20261011/serve.sh --ipv6'
```

From another terminal on the PC: `ping -6 fd96:196:960::2` or
`nc -6 fd96:196:960::2 9600`. Add `--internet6` to the launcher for IPv6 Internet
routing; Ctrl-C closes the session and restores the host/card. See
[full usage](../../rtems/README.md#ipv6-usage-and-scope).

The raw-IP TUN profile uses static addressing, with SLAAC/router solicitation,
DAD, MLD and IPv6 fragmentation/reassembly disabled. MTU is 1500, TCP MSS 1200.
IPv6-only DNS transport and general IPv6 conformance are not demonstrated.
Internet access requires host IPv6 connectivity and ip6tables NAT support.
HTTP capture is still limited to 8 KiB; no TLS, sockets/POSIX layer or general
libc was added. Scheduling and clock ticks remain cooperative and depend on
host polling. No autonomous execution, recovery, arbitrary extra DRAM ownership
or RAID disk-I/O coexistence is established by these tests.
