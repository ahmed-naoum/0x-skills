# Network debugging tools and method

Read this when: something between the client and the server is slow, flaky or failing and the faulty layer is not yet known; or a flow must be tested under bad network conditions.

## Method

Network debugging is bisection. Two questions cut the problem before any tool runs:

1. **Who is affected?** Everyone → origin, DNS or CDN configuration. One region or ISP → routing, a CDN location, or a geography rule. One kind of network (corporate, mobile) → a middlebox, IPv6, or MTU. One user or device → client side.
2. **What changed, and when?** A deploy, a DNS edit, a certificate renewal, a firewall or WAF rule, a provider incident. Most network faults are configuration changes with a delay.

Then walk the layers in order and stop at the first that fails. Do not change anything until a stage has been named; restarts destroy the evidence.

## The ladder: dig, curl, traceroute

```bash
dig +short example.com A; dig +short example.com AAAA      # 1. does the name resolve, to what
dig +short example.com A @<authoritative-ns>               #    does the authority agree with the cache
curl -sv --connect-timeout 5 -o /dev/null https://example.com/   # 2. where does the exchange stop
curl -4 -sv -o /dev/null https://example.com/              # 3. one address family at a time
curl -6 -sv -o /dev/null https://example.com/
curl -sv --resolve example.com:443:<ip> -o /dev/null https://example.com/   # 4. one specific hop or server
traceroute -T -p 443 example.com                           # 5. path, only if connect fails or is slow
```

`curl -v` narrates the stages; the last line printed before the failure names the layer:

| Last thing curl shows | curl exit code | Layer | Next |
|---|---|---|---|
| `Could not resolve host` | 6 | DNS | `dns-domains.md` |
| `Trying <ip>...` then refused or failed | 7 | TCP: nothing listening or rejected | `ip-transport.md` |
| `Trying <ip>...` then timeout | 28 | TCP: dropped by a firewall or route | `ip-transport.md`, traceroute |
| `Connected`, then a TLS error | 35 | Handshake: version, cipher, SNI, MTU | `tls-certificates.md` |
| Certificate problem | 60 | Chain, name or expiry | `tls-certificates.md` |
| Request sent, `Empty reply from server` | 52 | Server or proxy closed without answering | proxy and app logs |
| `Recv failure: Connection reset` | 56 | Reset mid-exchange | capture; `proxies-load-balancers.md` |
| A 4xx/5xx status | 0 (22 with `-f`) | HTTP: find the emitting hop | `proxies-load-balancers.md` |

Notes on traceroute: default probes are UDP or ICMP, which firewalls treat differently from the traffic in question; `-T -p 443` sends TCP SYNs to the real port (Linux, needs root). Rows of `* * *` in the middle are routers that do not answer and mean nothing by themselves. The useful facts are where the path stops, and whether it leaves the expected network.

## Timing: find the slow phase

```bash
curl -sS -o /dev/null -w 'dns %{time_namelookup}\ntcp %{time_connect}\ntls %{time_appconnect}\nttfb %{time_starttransfer}\ntotal %{time_total}\n' https://example.com/
```

The values are cumulative. Subtract neighbors to get phases:

| Phase | Compute | Should be | Large means |
|---|---|---|---|
| DNS | `dns` | A few ms when cached | Slow or failing resolver; a value near 5 s is a resolver timeout followed by a retry |
| TCP connect | `tcp − dns` | One RTT. This is the RTT measurement | Distance, or SYN loss: about 1 s, 3 s or 7 s is one, two or three retransmitted SYNs |
| TLS | `tls − tcp` | One RTT (TLS 1.3), two (TLS 1.2), plus CPU | Old protocol, oversized chain, overloaded terminator |
| Server | `ttfb − tls − one RTT` | The app's own processing time | Origin or backend slowness; a cache miss at the CDN |
| Download | `total − ttfb` | Size ÷ throughput | Large body, missing compression, loss, slow client link |

Run it five times: the first run is cold (DNS, new session), later runs show the steady state. Report medians, and note outliers separately, because intermittent faults hide in averages.

## The DevTools waterfall and HAR files

Open the Network panel, enable "Disable cache" and "Preserve log", add the Protocol and Connection ID columns, reload. Click a request and read the Timing tab:

| Phase | Long means |
|---|---|
| Queueing / Stalled | Waiting for a connection slot (six per origin on HTTP/1.1), for higher-priority requests, or for a busy browser. Many requests stalled together on HTTP/1.1 is the case for HTTP/2 |
| DNS Lookup | Resolver; many distinct hostnames each pay this |
| Initial connection | RTT or SYN loss. Appears only on the first request of a connection: if most requests show it, connections are not reused |
| SSL | Handshake cost, included in initial connection |
| Request sent | Almost always negligible; large only for uploads |
| Waiting for server response | Time to first byte: one RTT plus edge and origin time. Compare with the cache status header and with `Server-Timing` if the app emits it |
| Content Download | Body size against bandwidth, a streamed response, or a main thread too busy to read |

Patterns worth recognizing: a staircase of requests each starting when the previous ends is a dependency chain (not a network fault; `0x:web-performance`, `loading-delivery.md`); requests marked from disk or memory cache explain "works for me" against a user's fresh load; a different Protocol value for one host shows where HTTP/3 or HTTP/2 is not negotiated.

**HAR files** make a user's session inspectable. Ask for one when the fault cannot be reproduced: the Network panel's export button after reproducing with "Preserve log" on. A HAR can contain cookies, tokens and request bodies.
Prefer the browser's sanitized export (Chrome's default export omits cookie and authorization headers, but tokens in URLs and bodies remain), tell the user to log out afterward so captured sessions die, and delete the file when done. In the file, each entry's `timings` holds `blocked`, `dns`, `connect`, `ssl`, `send`, `wait`, `receive` in milliseconds;
`-1` means the phase did not happen (a reused connection), and `serverIPAddress` shows which address the user actually reached.

## Client, network or server

Compare the same request as measured at both ends, joined by request ID.

| Evidence | Fault is in |
|---|---|
| Server log duration matches what the client saw; slow from every location, including a machine in the same datacenter | Server: app, database, dependency (`0x:web-performance`, `backend-latency.md`) |
| Server log duration is short, client total is long; connect time large or varying by location; loss visible in `mtr` | Network path |
| No server or CDN log entry at all for the failing request | Before the server: DNS, routing, firewall, or a middlebox on the client side |
| curl from the same machine is fast while the browser is slow; "Stalled" dominates; only one device or browser profile | Client: extensions, a service worker, security software, main-thread work |
| Fast when cached, slow on a miss | Origin behind a CDN: fix hit ratio or origin time (`http-caching.md`) |
| Slow only on the first request after idle | Cold connection, cold function start, or congestion window reset after idle |

Latency signatures that identify a cause by their number alone:

- **1 s, 3 s, 7 s added to connect:** retransmitted SYNs. Packet loss, or the server's accept queue overflowing under load.
- **About 5 s on some requests, often from inside containers:** DNS resolver timeout and retry.
- **About 40 ms or 200 ms steps on small writes:** delayed acknowledgments interacting with send coalescing, or minimum retransmission timers.
- **A duration that is exactly 30 s, 60 s or 100 s:** somebody's timeout, not real work. Find the hop configured with that number (`proxies-load-balancers.md`).

## Testing under bad networks

Test the flows where a failure costs money or data: signup, login, checkout, upload, any form that creates something. The bugs found this way are not about speed; they are duplicate submissions, spinners that never end and state lost on a dropped response.

| Tool | What it does | Limits |
|---|---|---|
| DevTools throttling presets (Slow 4G and similar), offline toggle | Delays and rate-limits requests in that tab | No real packet loss; fine for UX and timeout behavior |
| Playwright with a Chromium CDP session | The same emulation, automated in an end-to-end test | Chromium only |
| `tc netem` on a Linux test host or container | Real delay, jitter and loss at the packet level | Affects everything leaving that interface, including the SSH session; never on production |
| OS-level conditioners (Network Link Conditioner on macOS) | System-wide profiles for manual testing on real devices | Manual |
| A fault-injecting TCP proxy (Toxiproxy) between app and dependencies | Latency, resets and timeouts on the database or third-party hop | Server-side paths only |

```ts
const cdp = await page.context().newCDPSession(page);
await cdp.send('Network.emulateNetworkConditions', {
  offline: false,
  latency: 150,                               // ms added per request
  downloadThroughput: (1.6 * 1024 * 1024) / 8, // bytes per second
  uploadThroughput: (750 * 1024) / 8,
});
```

```bash
sudo tc qdisc add dev eth0 root netem delay 150ms 30ms loss 2%   # add latency, jitter, loss on egress
sudo tc qdisc del dev eth0 root                                   # remove
```

What to assert on each critical flow:

- It completes at slow-4G speed with a few percent loss, with visible progress and no dead spinner.
- Going offline after the request is sent but before the response arrives, then retrying, does not create a second order, charge or record (idempotency: `0x:api-design`, `idempotency-rate-limits.md`).
- The submit control cannot fire twice while a request is pending.
- Every request has a timeout and a recoverable error state; typed input survives the failure.
- A large upload resumes or fails cleanly.

Test-suite placement: `0x:code-quality`, `e2e-contract-visual.md`.

## mtr: locating loss

`mtr` combines traceroute and ping and reports loss and latency per hop over many cycles.

```bash
mtr -rwbzc 100 example.com          # report mode, wide, names and IPs, AS numbers, 100 cycles
mtr -rwbzc 100 -T -P 443 example.com   # TCP probes to the real port
```

Reading rules, which prevent the standard misdiagnosis:

- **Loss that appears at a middle hop and is absent at later hops is not loss.** That router is rate-limiting its own ICMP replies while forwarding traffic normally. Real loss starts at some hop and continues through every later hop to the destination.
- **Only the final hop's loss and latency describe the user's experience.** If the last hop shows loss with ICMP, repeat with TCP probes, because the destination may deprioritize ICMP.
- A latency step that persists to the end marks the slow link; whether it is a fault depends on geography (an ocean crossing adds tens of ms legitimately).
- **Paths are asymmetric.** The return route can differ and can be the broken half. Collect a report from the client toward the server and one from the server toward the client's address.
- For a provider ticket, send both directions, timestamps, source and destination addresses, and the AS column.

## Testing from several regions and networks

A fault is localized by where it does not occur. Build the smallest matrix that separates the hypotheses:

| Vary | How |
|---|---|
| Region | Multi-location HTTP and DNS probe services (Globalping, RIPE Atlas, an uptime monitor's regional checks), a CI runner or short-lived VM in another region |
| Network type | Home broadband, a phone hotspot, a corporate network, a datacenter address |
| Address family | `curl -4` and `curl -6` |
| Resolver | `dig @1.1.1.1`, `@8.8.8.8`, and the user's ISP resolver |
| CDN location | The POP identifier in response headers (`ip-transport.md`) |

Reading the matrix: fails everywhere → origin, DNS or certificate; one region → CDN location, routing, a geography or WAF rule; one ISP → peering, that ISP's resolver, or a block of the site's address; corporate only → proxy or firewall; **datacenter addresses only** → the site's own bot rules blocking the monitors, a frequent cause of false alarms; mobile only → IPv6, MTU or carrier NAT.

From Launch, run synthetic checks from at least three regions and alert when two or more fail, so a single probe's network trouble does not page anyone (`0x:site-reliability`, `dashboards-alerting.md`).

## Packet capture: tcpdump and Wireshark

Capture when the logs at two hops disagree, or when a failure leaves no log at all. Capture narrowly: packets contain user data, so filter to one host and port, keep it short, and delete the file afterward.

```bash
sudo tcpdump -ni any -s 0 -w /tmp/cap.pcap 'host 203.0.113.5 and tcp port 443'
sudo tcpdump -ni any 'tcp port 3000 and tcp[tcpflags] & (tcp-syn|tcp-rst|tcp-fin) != 0'   # connection events only
sudo tcpdump -ni lo -A 'tcp port 3000'     # plaintext hop between proxy and app, readable HTTP
```

- `tcp[tcpflags]` expressions match IPv4 packets only; for IPv6 traffic filter with `ip6 and tcp port 3000` and read the flags in the output.
- **Capture where the traffic is plaintext** when the question is about HTTP: the loopback hop between the proxy and the app. To decrypt TLS from a client, export session keys (`SSLKEYLOGFILE=/tmp/keys.log curl ...`, or the same variable for a browser) and point Wireshark's TLS preferences at the key log file. The server's private key cannot decrypt modern forward-secret sessions.
- Capture at both ends when possible; a packet seen leaving one side and never arriving at the other localizes the loss without inference.
- In Wireshark, start from Statistics → Conversations to pick the stream, then "Follow TCP Stream". Useful display filters: `tcp.analysis.flags` (everything Wireshark considers abnormal), `tcp.analysis.retransmission`, `tcp.flags.reset == 1`, `tcp.analysis.zero_window`, `tls.handshake.type == 1` (ClientHello), `dns.flags.rcode != 0`, `tcp.stream eq 7`.

## Reading retransmits, resets and window limits

| Seen in the capture | Meaning | Where to look |
|---|---|---|
| SYN repeated after gaps of 1 s, 2 s, 4 s with no SYN-ACK | Dropped SYN: firewall, route, or a full accept queue on the server | `nstat -az \| grep -i listen` for `ListenOverflows`/`ListenDrops`; firewall rules |
| SYN answered by RST | Nothing listening on that port | `ss -tlnp` |
| Retransmission after three duplicate ACKs, small gap | Fast retransmit of an isolated loss; harmless when rare | Rate: well under 1% is ordinary on the internet, several percent hurts (rule of thumb) |
| Retransmission after a gap of 200 ms or more | Timeout retransmit: tail loss or heavy loss; this is what users feel as stalls | `mtr` on the path; congestion control choice (`ip-transport.md`) |
| Zero window or "window full" from the receiver | The receiving application is not reading: slow consumer, busy client. Not a network fault | The receiving process |
| Sender pauses with data to send while the receiver's window is open | Congestion-window limited: loss or a fresh connection in slow start | `ss -ti` on the sender: `cwnd`, `retrans`, `rtt` |
| Advertised window stuck near 64 KB on a fast path | Window scaling missing or stripped by a middlebox; throughput capped at window ÷ RTT | SYN options in the first two packets |
| RST arriving mid-stream | Either the peer's process died or closed with unread data, an idle timeout at a load balancer or NAT expired and the next packet was rejected, or a middlebox injected it | Who sent it: compare the IP TTL of the RST with other packets from that address; a different TTL means an injecting middlebox |
| First response after an idle period on a kept-alive connection is slow | Congestion window reset after idle | `net.ipv4.tcp_slow_start_after_idle=0` on servers that send bursts over long-lived connections |

On a live Linux server, `ss -ti dst <client-ip>` shows the kernel's view per connection (congestion window, smoothed RTT, retransmits, whether sending is limited by the receiver window or the send buffer), and `nstat -az | grep -iE 'retrans|timeouts|listen'` shows host-wide counters without a capture.
A fresh connection can send only about ten segments (roughly 14 KB) before waiting for acknowledgments, which is why a critical response that fits in that budget arrives one round trip sooner.

## Ask the user

- **Who is affected, where are they, on what network, and since when?** This decides the whole search. Default if unknown: assume everyone, and verify from three regions before believing it.
- **Can an affected user send a HAR file and an `mtr` or traceroute report?** One report from the failing side is worth more than any test from a healthy one. Default: ask, with exact steps, and explain that the HAR contains session data.
- **What changed in the last day: deploys, DNS, certificates, firewall or CDN rules, a new provider?** Default: check the deploy log and DNS history before any deeper tool.
- **May packets be captured on the production server?** Captures include user data, which can be a privacy and contractual matter. Default: capture only headers or only the plaintext health-check path, for minutes, and delete afterward.
- **Which regions and network types matter commercially?** Decides where synthetic checks run and which reports are urgent. Default: the regions where paying customers are today.
