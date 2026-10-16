# Web server: HTTP on the card

The accepted autonomous RTEMS/lwIP profile serves HTTP on the i960. Linux
moves IP packets through a TUN gateway and publishes IPv6 port 8080. Browser
HTTP handling remains on the card; visitor statistics are recorded on Linux.

| Area | Entry point |
| --- | --- |
| Build/profile and packet relay | [RTEMS autonomous](../../rtems/autonomous/README.md), [network usage](../../rtems/README.md#ipv6-usage-and-scope) |
| Deployment wrapper | [serve-autonomous.sh](../../rtems/serve-autonomous.sh) |
| Initial HTTP acceptance | [web evidence](../../artifacts/rtems-web-autonomous-20261011/README.md) |
| Vader page | [Vader evidence](../../artifacts/notes/rtems-vader-20261011.md) |
| System information | [system-info evidence](../../artifacts/notes/rtems-system-info-20261011.md) |

The existing deployment uses `/home/mit/i960-rtems-web-20261011`, its matching
`autonet/kernel.bin` and `autonet-module-system-info/dac960auto.ko`, and host
visitor logs in `visitor-statistics/`. The launcher is installed beside these
build directories; running the source-tree shell script in place is not a
complete deployment.

The known published endpoint is
[IPv6 HTTP](http://[2a02:8106:40:9000:f662:19ee:dbad:1f1e]:8080/).
Its availability depends on the host's current address, routing, firewall and
card ownership. A Doom session may require releasing this profile; do not run
both exclusive owners or mistake a static Doom gallery for this card server.

Keep private visitor records out of source/evidence commits. Preserve aggregate
validation and the implementation, not users' browsing histories.
