# Layer 1: Network

Read this when: the user asks what there is to know about network, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

How does a request travel from a browser to my server and back?

Competencies: 73 (27 ● / 29 ◐ / 17 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## web-networking

Configure and debug everything between the browser and the app: IP and transport, DNS and domains, TLS, HTTP and its caching, CDN and edge protection, reverse proxies and load balancers.

**IP, TCP, UDP and QUIC** (`references/ip-transport.md`)

- ● Trace a request from browser through DNS, TCP, TLS and HTTP to the server
- ● Distinguish latency, bandwidth, loss and jitter when someone reports slowness
- ● Diagnose a refused or timed-out connection through ports, NAT and firewall rules
- ◐ Serve dual-stack IPv6 end to end, including IPv6-only mobile networks
- ◐ Survive a Wi-Fi to cellular switch with QUIC connection migration and safe client retries
- ◐ Allow and debug UDP traffic for QUIC, DNS and WebRTC through firewalls
- ○ Count round trips for TCP plus TLS 1.3 versus QUIC and remove extras
- ○ Tell congestion-control backoff from head-of-line blocking when latency spikes on a lossy link
- ○ Diagnose MTU black holes, carrier NAT and proxy interference
- ○ Interpret a regional outage using BGP and anycast routing data

**DNS and domains** (`references/dns-domains.md`)

- ● Register a domain with registrar lock, auto-renew and MFA
- ● Configure A, AAAA, CNAME, ALIAS, MX and TXT records for a production domain
- ● Trace delegation from root to authoritative servers with dig
- ● Diagnose stale caches, negative caching and propagation complaints
- ◐ Choose TTLs balancing failover speed against cache efficiency
- ◐ Move a domain between registrars or DNS providers without downtime
- ◐ Remove dangling records to prevent subdomain takeover
- ○ Configure health-checked failover and latency-based DNS routing
- ○ Enable DNSSEC and roll keys without breaking resolution
- ○ Run authoritative DNS across two providers

**TLS and certificates** (`references/tls-certificates.md`)

- ● Automate certificate issuance and renewal with ACME
- ● Alert on certificate and domain expiry before it breaks the site
- ● Enable HSTS with a staged max-age; preload only once every subdomain serves HTTPS
- ◐ Serve TLS 1.3 with a TLS 1.2 fallback and disable everything older
- ◐ Debug handshake, chain and SNI failures with openssl s_client
- ◐ Restrict certificate issuance with CAA records
- ◐ Decide where TLS terminates and whether to re-encrypt to backends
- ○ Monitor Certificate Transparency logs for unexpected issuance
- ○ Deploy mutual TLS between internal services
- ○ Enable hybrid post-quantum key exchange and test client compatibility

**HTTP semantics and versions** (`references/http.md`)

- ● Choose the HTTP method and status code each endpoint and error should use
- ● Reproduce any request with curl, including headers, cookies and timing
- ● Choose 301, 302, 307 or 308 redirects and avoid redirect chains
- ● Compress text with Brotli or zstd, never already-compressed bodies
- ◐ Serve conditional and range requests so clients revalidate and resume instead of refetching
- ◐ Enable HTTP/3 with HTTP/2 fallback and verify negotiation with curl
- ◐ Send 103 Early Hints and preload instead of HTTP/2 push or domain sharding
- ○ Publish HTTPS/SVCB records to advertise HTTP/3 and ECH
- ○ Decide whether 0-RTT is safe given replay risk on non-idempotent requests

**HTTP and CDN caching** (`references/http-caching.md`)

- ● Set Cache-Control, ETag and Vary so browsers and CDNs cache safely
- ● Serve static assets from immutable, fingerprinted URLs
- ● Mark private and sensitive responses no-store so nothing caches them
- ● Design cache keys and Vary so no user sees another user's page
- ● Purge or revalidate cached content safely on deploy
- ◐ Invalidate content instantly using cache tags or surrogate keys
- ◐ Serve stale on origin error with stale-while-revalidate and stale-if-error
- ◐ Measure cache hit ratio and fix the top misses
- ○ Prevent cache poisoning and web cache deception

**CDN setup and edge protection** (`references/cdn-edge.md`)

- ● Put a CDN before the origin and decide what it caches, proxies and bypasses
- ● Derive the real client IP without trusting spoofable headers
- ◐ Lock the origin so only the CDN can reach it
- ◐ Run redirects, header rewrites and simple auth checks in edge functions
- ◐ Tune WAF rules without blocking real customers
- ◐ Rate-limit and challenge abusive traffic at the edge
- ◐ Set an AI-crawler and scraper policy: allow, block or charge
- ○ Rehearse the DDoS response: who flips which control and how to reach the provider

**Reverse proxies and load balancers** (`references/proxies-load-balancers.md`)

- ● Write health checks that reflect real readiness
- ● Identify which hop produced a 502, 503 or 504
- ◐ Configure a reverse proxy with upstreams, timeouts, compression and forwarded headers
- ◐ Route by host and path to several backends from one proxy or load balancer
- ◐ Drain connections from the load balancer gracefully during deploys
- ◐ Align timeouts across client, CDN, load balancer, app and database
- ◐ Proxy WebSockets and long-lived streams through load balancers without drops
- ○ Choose layer-4 or layer-7 load balancing for a workload
- ○ Tune keep-alive and idle timeouts so connections are reused at every hop

**Network debugging tools and method** (`references/network-debugging.md`)

- ● Debug connectivity step by step with dig, curl and traceroute
- ● Find the slow phase in a DevTools waterfall or HAR file
- ● Tell a client, network or server fault apart from timing data
- ● Emulate slow 4G, packet loss and high latency against a critical flow
- ◐ Locate a lossy hop with mtr
- ◐ Test from several regions and networks to localize a fault
- ◐ Capture and read packets with tcpdump and Wireshark
- ○ Diagnose retransmits, resets and congestion-window limits from a capture
