# Host-side web visitor statistics

The autonomous launcher enables `relay.py --visitor-log <directory>`. Current
remote directory: `/home/mit/i960-rtems-web-20261011/visitor-statistics`.

- `visitor-log.sqlite3`: durable SQLite event log, one row per observed successful
  card response, with UTC time, client IP and retransmission identity.
- `statistics.json`: atomic readable summary containing `unique_visitors`,
  `successful_page_responses`, and per-address response count/first/last seen.

Read it over SSH:

```sh
ssh mit@192.168.2.75 'sudo cat /home/mit/i960-rtems-web-20261011/visitor-statistics/statistics.json'
```

The directory persists across relay restarts. SQLite transactions are authoritative;
the JSON summary is regenerated at startup and after each new event. Files are
root-readable and are not served over HTTP or copied into Git. No cookies, request
contents or user agents are recorded. Counting begins at deployment, not from
historical packet captures. Verification requests are included in the totals.

The observer runs on outgoing card packets after writing them to the host TUN.
It recognizes the HTTP/1.0 200 status line from card TCP port 80 for both IP
families. Non-200 replies, SYNs, echo traffic and card-originated Internet fetches
are excluded. The card closes after one response per connection. The identity
uses address family, client address/port and server TCP sequence; retransmitted
status packets are ignored, including after a logger restart. Exact tuple/sequence
reuse can undercount. IPv6 extension headers and fragmented IP packets are ignored;
the current card emits plain TCP packets.

These are unique IPs, not unique people. Shared addresses undercount people;
IPv6 privacy addresses can count the same person more than once. A 200 response
being emitted does not prove the browser received the entire page. Requests for
other paths also count because the current card serves the same page for all
GET paths. Database growth is currently unbounded; no automatic retention policy
is applied.

Validation: `python3 rtems/transport/test_visitors.py` tests repeat/retransmitted
responses, persistence, IPv4/IPv6, the relay's bytearray packets, unrelated traffic
and malformed/truncated packets. The first live attempt exposed bytes/bytearray
conversion in address decoding; the fix was verified before final deployment.

Final live verification on 2026-10-11: two consecutive Mac GETs both returned
successfully and added two responses for one address. The observed total was
four responses across two addresses (including other requests during deployment).
The service remained active. Actual visitor addresses stay on the host.
