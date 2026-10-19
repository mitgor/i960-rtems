# Accele160 zone-loan, cancellation and routed IPv6 qualification

Kernel `26b916dfd1c85a986d24b4bac17c7972b8b5108fed5bb56e9d0028afbed6bc80`,
boot `8cdab7ff-48a3-481f-bb54-0924025016c0`, session `20261019T175819Z`.

`tested-live.tar.xz` preserves the immutable bundle (kernel/module binaries,
source, manifests, accepted host modules), full 64-frame baseline, console and
application journals, three module loads, loan replies, routing setup and HTTP
captures. Replay with `rtems/accele160/runtime/verify_reclamation.py`.

The loan wrote/verified 6,291,424 bytes within the existing 6 MiB Doom zone,
cancelled with two outstanding pins, refused access/close/free until completion,
and returned the parent loan after 192 bounded steps. Native tests additionally
cover wrong/stale owner tokens and guard-corruption retention. Hardware guard
corruption and arbitrary task cancellation were not injected in this run.
949 external console exchanges passed; maximum loan RPC was 206.356 ms.

The archive's **root** `public_ipv6.py` is the corrected and tested routing
helper. The helper frozen inside `bundle/project` is the initial version that
set only per-interface forwarding. It passed host-local HTTP but LAN SYNs did
not reach TUN. The correction enables global forwarding and global proxy NDP,
saves/restores all interface forwarding settings, and limits IPv6 forwarding to
the card. The source reason is Linux's
[ip6_forward global-forwarding check and proxy handling](https://raw.githubusercontent.com/torvalds/linux/v6.1/net/ipv6/ip6_output.c).
Do not substitute the old bundle helper for the root script.

`global-lan.*` was fetched on the Mac over the LAN; `lan-endurance.json` records
20 successful HTTP connections and a blocked diagnostic TCP/9600 connection.
`routing-removal.txt` records the restored zero forwarding/proxy settings, absent
/128 route and absent nftables table. `restoration.txt` records the final reapply
and service state. The card URL is `http://[2a02:8106:40:9000::960]/`.

Internet reachability is unverified. The external fetch tool rejected the IPv6
literal without performing a usable network test. Router firewall admission
from the Internet may still be required. This archive proves the routed LAN
path to the global address, not reachability from an external network.

`prior-final.tar.xz` holds the previous service's final result and owned report;
`prior-quiescent-page.bin` is the separate persist-page capture containing QUIE,
zero failure mask and STOP ACK. An initial local check mistakenly used the owned
report page for these offsets; the correct persist page was retrieved and checked.
The previous service itself reported a clean retained STOP before reset.

No new stock RAM, increased RTEMS workspace, module heap imports or unrestricted
non-cooperative task termination is claimed. See the repository's
`rtems/accele160/runtime/RECLAMATION-CANCELLATION.md` for the remaining gates.
