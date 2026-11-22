# IP, TCP, UDP and QUIC

Read this when: reasoning about how packets reach the server (addressing, ports, NAT, firewalls), counting handshake round trips, or explaining slowness, timeouts and regional failures below the HTTP layer.

## The path of one request

Every "it does not load" report is a failure at exactly one of these stages. Name the stage before changing anything.

| Stage | What happens | Typical cost | Fails as |
|---|---|---|---|
| 1. DNS | Browser cache, OS cache, recursive resolver, authoritative servers | 0 ms cached; one resolver round trip otherwise; several if the resolver is cold | `NXDOMAIN`, `SERVFAIL`, wrong or stale IP |
| 2. TCP connect (or QUIC) | SYN, SYN-ACK, ACK to the IP on port 443 | 1 RTT | refused (RST), timeout (dropped), no route |
| 3. TLS | ClientHello with SNI and ALPN, certificate, key exchange | 1 RTT (TLS 1.3), 2 RTT (TLS 1.2) | handshake alert, certificate error, stall mid-handshake |
| 4. HTTP request | Request out, first byte back | 1 RTT plus server think time | 4xx, 5xx, hang until a timeout |
| 5. Body | Limited by congestion window, bandwidth and loss | size dependent | truncated body, stalls, resets |

Between the browser and the app there are usually more TCP connections than one: browser to CDN, CDN to load balancer, load balancer to app. Each has its own handshake, timeouts and failure mode; `proxies-load-balancers.md` covers telling the hops apart.

## Round trips: count them, then remove them

RTT to first response byte on a new connection, excluding DNS:

| Stack | New connection | Resumed |
|---|---|---|
| TCP + TLS 1.2 | 4 (1 TCP, 2 TLS, 1 HTTP) | 3 |
| TCP + TLS 1.3 | 3 (1 TCP, 1 TLS, 1 HTTP) | 3, or 2 with 0-RTT early data |
| QUIC (HTTP/3) | 2 (1 combined transport and TLS, 1 HTTP) | 1 with 0-RTT |

At 150 ms RTT (intercontinental or a poor mobile link), TCP + TLS 1.3 is 450 ms before the first byte with zero server time. The fixes, in order of payoff:

1. **Terminate near the user.** A CDN edge turns a 150 ms RTT into 10 to 30 ms for the handshakes; the long leg runs over a warm, reused connection. This beats every protocol tweak.
2. **Reuse connections.** Keep-alive at every hop (see `proxies-load-balancers.md`); a reused connection pays 1 RTT per request. Server-to-server HTTP clients that open a new connection per call pay the full handshake every time: use a pooled agent.
3. **Remove hostnames.** Every extra origin (`api.`, `static.`, third-party scripts) is a new DNS lookup plus handshake. Same-origin serving through one CDN hostname removes them. `<link rel="preconnect">` hides the cost for origins that must stay.
4. **Remove redirects.** `http://example.com` → `https://example.com` → `https://www.example.com` is two extra connection setups; see `http.md`.
5. **Keep the certificate chain small.** A server's first flight is limited by the initial congestion window (commonly 10 segments, about 14 KB) and, in QUIC, by the anti-amplification limit of three times the bytes the client has sent.
   A chain with redundant intermediates or a large RSA key can spill into another round trip. Send leaf plus required intermediates only, never the root; prefer ECDSA certificates.
6. **Enable TLS 1.3 and HTTP/3.** Free where the CDN or proxy offers it. 0-RTT is a separate decision with replay risk: `http.md`.

TCP Fast Open is not a usable optimization on the public internet: middleboxes break it and browsers do not use it.

## Slowness: latency, bandwidth, loss or jitter

Ask what is slow before measuring anything. The four quantities fail differently:

| Report | Dominant quantity | Why | First check |
|---|---|---|---|
| Every click feels laggy, small API calls take 500 ms+ | Latency (RTT) times the number of round trips | Small exchanges are bound by round trips, not throughput | `curl -w` timing split (`network-debugging.md`); `ping`/`mtr` for RTT |
| Large downloads or uploads slow, small requests fine | Bandwidth, or loss holding the congestion window down | Bulk transfer is bound by min(link rate, congestion window / RTT) | Transfer rate of a large file; retransmit counters |
| Fast, then stalls for a second or more, then resumes | Loss | A lost packet waits for retransmission; a lost tail packet waits for a timeout | `mtr` loss at the final hop; `nstat TcpRetransSegs` |
| Calls and video choppy while pages load fine | Jitter (variance of delay) | Realtime media cannot buffer long; pages do not care | WebRTC stats, `mtr` standard deviation |

Rules that hold across cases:

- Adding bandwidth does not fix latency. A page that needs 20 sequential round trips at 100 ms takes 2 s on any link.
- For loss-based congestion control (Reno, CUBIC), throughput falls roughly with 1/(RTT × √loss): 1% loss on a long path can cut bulk throughput by an order of magnitude while `ping` still looks acceptable.
- Rough RTT expectations (rules of thumb, not guarantees): same region under 5 ms; same continent 20 to 60 ms; transatlantic 70 to 100 ms; transpacific 120 to 200 ms; cellular adds tens of ms and large variance; geostationary satellite 500 ms or more.
- Measure from where the user is. A test from a datacenter in the server's region says nothing about a user on hotel Wi-Fi.

## Refused, timed out, unreachable

The error type identifies the layer. Do not skip this step.

| Client sees | Meaning | Usual causes |
|---|---|---|
| `Connection refused` immediately | The host answered with RST: reachable, nothing accepting on that port | Process down or crashed; listening on `127.0.0.1` instead of `0.0.0.0`/`::`; wrong port; container port not published; firewall configured to reject |
| Timeout after seconds | The SYN was dropped silently | Cloud security group or network ACL; host firewall with DROP policy; wrong IP (stale DNS, released address); instance stopped; no return route; outbound blocked on the client side |
| `No route to host` / `Network is unreachable` | ICMP unreachable from a router or local stack | Missing route, host firewall rejecting with ICMP, IPv6 attempted with no IPv6 connectivity |
| Connects, then hangs or resets | Transport is fine; the fault is above | TLS mismatch, proxy timeout, MTU black hole (below), app accepting but not responding |

Work from the server outward, because each step halves the search space:

```bash
ss -tlnp                                   # is it listening, and on which address?
curl -sv http://127.0.0.1:3000/health      # does it answer locally?
sudo nft list ruleset                      # host firewall (or: iptables -S, ufw status)
nc -vz -w 5 203.0.113.10 443               # from outside: refused vs timeout
sudo tcpdump -ni any 'tcp port 443 and tcp[tcpflags] & tcp-syn != 0'   # do SYNs arrive?
```

The `tcp[tcpflags]` test matches IPv4 packets only; for IPv6 clients capture with `ip6 and tcp port 443` and read the flags column.
If SYNs arrive in `tcpdump` but nothing answers, the host firewall or the listener is at fault. If no SYN arrives, the block is upstream: security group, network ACL, load balancer listener, or DNS pointing elsewhere.

Traps:

- **Bind address.** Dev servers default to `localhost`. Inside a container the app must listen on `0.0.0.0`, or the published port answers with a reset.
- **Docker and host firewalls.** Docker publishes ports by writing its own netfilter rules, which are evaluated before `ufw`'s. A port published with `-p 5432:5432` is reachable from the internet even when `ufw` says denied. Publish to loopback (`-p 127.0.0.1:5432:5432`) and expose only the proxy, or enforce in the cloud firewall.
- **Two firewalls.** Cloud security group and host firewall both have to allow the port; fixing one and testing proves nothing about the other.
- **IPv4 open, IPv6 closed (or the reverse).** Rules are per address family. A client that prefers IPv6 times out while `curl -4` works.
- **NAT hairpin.** A server calling its own public IP from behind NAT may fail though outside clients succeed; use the private address or internal DNS name.
- **Outbound NAT port exhaustion.** Many short connections from one NAT IP to one destination IP and port run out of source ports; symptoms are intermittent connect timeouts under load. Fix with connection pooling first, more NAT addresses second.

Security groups, subnets and NAT gateways as cloud design belong to `0x:cloud-infrastructure`.

## IPv6 and dual stack

Default: serve dual stack at the public edge. A CDN or managed load balancer gives IPv6 to clients even when the origin is IPv4-only, which is enough for almost every small product. Run IPv6 to the origin only when the host makes it easy.

- Publish `AAAA` only when the whole path works: listener on `::`, security group and host firewall rules for IPv6, and a route. A published but broken `AAAA` does not fail cleanly: clients race both families (Happy Eyeballs) and usually recover, but some clients and server-side HTTP libraries wait for the IPv6 attempt to time out first. The symptom is "slow for some users, fine for others".
- Never block all ICMPv6. Neighbor discovery and Packet Too Big messages are ICMPv6; dropping them breaks connectivity and path MTU discovery outright.
- **IPv6-only mobile networks** reach IPv4 servers through NAT64 with DNS64, which synthesizes `AAAA` records from `A` records. This works only when the client connects by hostname. Hard-coded IPv4 literals in an app, an SDK config or a WebSocket URL fail on those carriers, and app-store review tests for it. Use hostnames everywhere.
- Application code: store addresses in a type that holds both families (`inet` in Postgres, not `varchar(15)`); parse `X-Forwarded-For` without assuming dotted quads; rate-limit and ban IPv6 by `/64` prefix, because one subscriber controls at least a /64 and rotating within it is free.
- Check: `curl -6 -sv https://example.com/ -o /dev/null` and `curl -4 ...` must both succeed and return the same thing; `dig AAAA example.com +short`.

## Network changes: QUIC migration and safe retries

When a phone moves from Wi-Fi to cellular its IP changes. Every TCP connection is bound to the old address and is dead, but neither side is told: in-flight requests hang until a timeout.
QUIC identifies a connection by connection ID instead of the address tuple, so a client can migrate to the new path without a new handshake.
Whether that happens depends on the client implementing it and on the server side supporting it: load balancers must route QUIC by connection ID, and some stacks and CDNs disable migration. Treat migration as a bonus the CDN may provide, never as the mechanism the product relies on.

What the product relies on is the client:

- Set a timeout on every request (`AbortSignal.timeout(ms)` on `fetch`); the platform default is far too long for a user staring at a spinner.
- Retry automatically only what is safe to repeat: `GET`, `HEAD`, `PUT`, `DELETE` by definition, and `POST` only with an idempotency key the server honors (`0x:api-design`, `idempotency-rate-limits.md`). A request that timed out may have been executed.
- Back off exponentially with jitter and cap the attempts (two or three), otherwise a recovering server meets a synchronized retry wave.
- Long-lived streams (WebSocket, SSE) need application heartbeats to detect the dead path within seconds, then reconnect with backoff and resume from a last-seen ID (`0x:backend-architecture`, `realtime.md`).
- Uploads over mobile links should be resumable rather than restarted.

## UDP: QUIC, DNS and WebRTC through firewalls

Firewall rules written for "web traffic" usually mean TCP. Each UDP use needs its own rule and its own test, and UDP has no handshake, so `nc -u` reporting "open" proves nothing.

| Use | Open | Failure when blocked | Test |
|---|---|---|---|
| HTTP/3 | UDP 443 inbound to whatever terminates QUIC | Silent fallback to HTTP/2; nobody notices except the metrics | `curl --http3-only -sI https://example.com` |
| DNS (authoritative or resolver) | UDP 53 and TCP 53 | With TCP 53 closed, answers larger than the UDP limit (DNSSEC, big TXT sets) are truncated and the retry over TCP fails | `dig +notcp example.com` and `dig +tcp example.com` |
| WebRTC | STUN and TURN on UDP 3478, TURN over TLS on TCP 443 or 5349, plus the media relay port range | Calls connect on home networks and fail on corporate or symmetric-NAT networks | A trickle-ICE test page forcing relay-only candidates |

- Because clients fall back, HTTP/3 must never be the only path, and "is HTTP/3 working" has to be measured (share of requests by protocol in CDN or proxy logs), not assumed.
- Some corporate and guest networks drop UDP 443 entirely. That is their policy; the HTTP/2 fallback is the fix.
- A self-hosted QUIC server on Linux may log a warning about UDP buffer sizes; raise `net.core.rmem_max` and `net.core.wmem_max` to the value the server's documentation asks for.
- WebRTC without a TURN relay fails for a meaningful minority of users behind symmetric NAT or strict firewalls. Budget for TURN (it relays media, so it costs bandwidth) or use a provider that includes it.
- Capture to confirm arrival: `sudo tcpdump -ni any udp port 443`.

## Latency spikes on a lossy link: congestion backoff or head-of-line blocking

Both show up as "fine on fiber, terrible on the train". They need different fixes.

| | Congestion-control backoff | Head-of-line blocking |
|---|---|---|
| Mechanism | Sender shrinks its congestion window after loss and regrows it slowly | One lost TCP segment holds back all later bytes, and HTTP/2 puts every stream on that one connection |
| Signature | Sustained low throughput on bulk transfers; single request also slow | Many concurrent requests freeze together and complete in a burst; a single request alone is fine |
| Evidence | `ss -ti` on the server shows small `cwnd`, rising `retrans` | Waterfall shows parallel HTTP/2 requests stalling in lockstep; same page over HTTP/3 does not |
| Fix | BBR on the sending host; terminate closer to the user; send fewer bytes | HTTP/3, where a lost packet stalls only its own stream |

- Enable BBR on self-managed Linux senders: `sysctl -w net.ipv4.tcp_congestion_control=bbr` (persist in `/etc/sysctl.d/`; if `sysctl net.ipv4.tcp_available_congestion_control` does not list it, `modprobe tcp_bbr` first). It tolerates random loss far better than CUBIC. Behind a CDN this matters only for the CDN-to-origin leg; the CDN chooses its own algorithm toward users.
- On a badly lossy link, HTTP/2 can be slower than HTTP/1.1 with six connections, because loss on one connection no longer stalls the others. This is the practical argument for HTTP/3 for mobile-heavy audiences.

## MTU black holes, carrier NAT and interfering proxies

**MTU black hole.** Signature: the TCP handshake and small requests work, anything large hangs. Typically the TLS handshake stalls when the server sends its certificate, or small API calls succeed while uploads and big responses freeze.
It appears on paths with a smaller MTU (VPNs, tunnels, PPPoE, some cellular) where a firewall drops the ICMP "fragmentation needed" messages that path MTU discovery depends on.

```bash
ping -M do -s 1472 example.com    # Linux: 1472 + 28 header bytes = 1500; lower -s until it passes
ping -D -s 1472 example.com       # macOS equivalent
```

Fixes: allow ICMP type 3 code 4 and ICMPv6 Packet Too Big through every firewall you control; set `net.ipv4.tcp_mtu_probing=1` on the server; clamp MSS on tunnel and VPN gateways (`iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu`).

**Carrier-grade NAT.** Thousands of mobile or ISP subscribers share one public IPv4 address (the shared range is `100.64.0.0/10` on the carrier side).
Consequences: an IP-based rate limit or ban hits strangers, so limits on shared ranges must be generous and keyed on session or account where possible; NAT mappings for idle flows expire quickly (UDP in tens of seconds, TCP in minutes), so an idle WebSocket dies silently.
Send a ping at a 20 to 30 s interval (rule of thumb) on long-lived connections.

**Interfering middleboxes.** Corporate TLS-inspecting proxies, antivirus, captive portals and some mobile "optimizers" re-terminate or alter traffic. Signs: the certificate issuer the user sees is not the real CA;
WebSocket upgrades or SSE streams fail on one network only; responses are buffered until complete; HTTP/3 is never negotiated. Confirm by asking for the same test on a phone hotspot and for a HAR file.
The fixes are on the product side: everything over 443 with TLS, WebSocket with a long-polling or SSE fallback, no dependence on HTTP/3, streams that tolerate buffering.

## Regional outages: BGP and anycast

When users in one country or on one ISP cannot connect and everything looks healthy from the server, the fault is usually routing between networks, which the product cannot fix but can identify and route around.

1. **Establish the shape.** Collect from affected users: public IP (gives the ASN), a traceroute or `mtr` report, and the time. One ASN affected means a peering or routing problem at that ISP; one geography across ISPs means a CDN point of presence or a cable; everyone means the origin.
2. **Check outside views.** Provider status pages, a public internet-health dashboard (Cloudflare Radar, RIPEstat, bgp.tools) for route withdrawals or leaks affecting the prefix, and probes from many networks (RIPE Atlas, a multi-region HTTP checker).
3. **Know which edge served the request.** With anycast, one IP is announced from many locations and BGP picks the path, which is the shortest route by policy, not by distance. Users can land on a distant or degraded POP. CDNs expose the POP: Cloudflare in the `cf-ray` suffix and at `/cdn-cgi/trace`, CloudFront in `x-amz-cf-pop`, Fastly in `x-served-by`. Ask an affected user for those values.
4. **Act on what is controllable.** Open a ticket with the CDN or host with the ASN, POP and traceroutes; post a status update naming the affected region; if a second CDN or region exists, steer the affected geography with DNS. Do not restart or redeploy healthy services to "do something".

A route change in the middle of a TCP connection sends its packets to another anycast site, which resets it. Occasional resets clustered on one network are this, not an application bug.

## Ask the user

- **Where are the users?** Region and share on mobile networks decide whether an edge network and HTTP/3 are priorities. Default if unknown: one region near the founder, a CDN in front, HTTP/3 on.
- **Does the product need realtime media or long-lived connections?** That brings in UDP rules, TURN cost and heartbeat design. Default: none; plain HTTPS on 443 only.
- **Is IPv6 to the origin required by a customer or a hosting constraint?** Default: IPv6 at the CDN edge only, IPv4 to the origin.
- **How strict should IP-based limits be, given shared carrier addresses?** Blocking a carrier NAT address blocks real customers. Default: generous per-IP limits, strict limits per account or session.
- **Is a second CDN or region worth paying for to survive regional routing failures?** Default: no before Scale; communicate through a status page instead.
