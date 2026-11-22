---
name: web-networking
description: "Configures and debugs everything between the browser and the app: DNS and domains, TLS certificates, HTTP and its caching, CDN and edge protection, reverse proxies, load balancers and transport. Use when a domain does not resolve, a certificate fails or expires, a 502, 503 or 504 appears, nginx, Caddy or a CDN needs setup, cache headers or purging misbehave, bots or a DDoS hit, or connections are slow."
---

# Web networking: DNS, TLS, HTTP, CDN and proxies

## Stance

A request crosses a chain of independent systems: resolver, network path, CDN, load balancer, proxy, app. Each one caches, times out, retries and fails by its own rules, and each one is configured somewhere different.
Expert work here is naming the hop and the layer before touching anything, and preferring a managed edge with a few well-understood settings over machinery a small team has to operate.

1. **Name the stage first.** DNS, TCP, TLS, HTTP and the app fail with different, recognizable signatures (refused is not timeout; 502 is not 504). A fix applied before the stage is identified usually destroys the evidence.
2. **Measure from where the user is.** A check from the server's own region proves nothing about a phone on a carrier network. Localize by where the fault does not occur.
3. **Caches expire; they do not propagate, and browsers cannot be purged.** Every DNS TTL, `max-age` and permanent redirect is a promise that cannot be withdrawn early. Lower the TTL one full old TTL before a change, and give long lifetimes only to URLs whose content never changes.
4. **Leaking beats staleness as a risk.** A stale page is an annoyance; one user's page served to another is a breach. Public content opts in to shared caching; anything that depends on who is asking is `no-store` and out of the CDN cache.
5. **Only the peer address is unforgeable.** Forwarded headers are trustworthy hop by hop, counted from the right, and only when the origin cannot be reached around the CDN. Edge protection that can be bypassed is decoration.
6. **Timeouts are one budget.** Request timeouts shrink toward the inside, idle timeouts grow toward the inside, and retries happen at one layer. Most 502s and 504s are a violation of one of the three.
7. **Automate every expiry and alert from outside.** Certificates and domains expire on schedule; renewal automation fails silently. The monitor looks at what clients actually receive.
8. **The registrar account is the root of trust.** It controls the site, the mail and certificate issuance. Lock, MFA, auto-renew and company ownership come before any other hardening.
9. **Fallbacks are part of the design.** HTTP/3 falls back to HTTP/2, IPv6 to IPv4, WebSocket to polling, the origin to stale cache. A feature whose fallback was never tested is an outage for some network.

## Route

| If the task is | Read |
|---|---|
| Users cannot connect, connection refused or timed out, ports and firewalls, IPv6, mobile-network oddities, QUIC and UDP, round-trip counting, a regional or single-ISP outage | `references/ip-transport.md` |
| Registering or securing a domain, adding or changing records, "DNS has not propagated", moving DNS provider or registrar, subdomain takeover, DNS failover, DNSSEC | `references/dns-domains.md` |
| Getting or renewing a certificate, a browser TLS error, expiry alerts, HSTS, TLS versions, CAA, where TLS terminates, mTLS, post-quantum key exchange | `references/tls-certificates.md` |
| Which method or status code, reproducing a request with curl, redirects, compression, 304 and range requests, enabling or verifying HTTP/2 and HTTP/3, Early Hints, HTTPS DNS records, 0-RTT | `references/http.md` |
| Setting `Cache-Control`, a user saw stale or someone else's content, cache keys and `Vary`, purging on deploy, cache tags, serving stale when the origin is down, hit ratio, cache poisoning | `references/http-caching.md` |
| Putting a CDN in front of the site, the real client IP, locking the origin, edge functions, WAF false positives, rate limiting, AI crawlers and scrapers, DDoS preparation and response | `references/cdn-edge.md` |
| Configuring nginx, Caddy or a load balancer, health checks, a 502, 503 or 504, dropped requests during deploys, timeouts, WebSocket or SSE through a proxy, keep-alive | `references/proxies-load-balancers.md` |
| "It is slow" or "it fails sometimes" with no known cause, reading a waterfall or HAR, mtr, testing from other regions, emulating a bad network, packet captures | `references/network-debugging.md` |

When the faulty layer is unknown, start with `network-debugging.md`; it routes to the others.

## Defaults at a glance

Follow what the project and its host already use; these apply to greenfield choices.

| Area | Prototype | Launch | Scale |
|---|---|---|---|
| Domain | Registrar lock, auto-renew, MFA, company-owned account | Independent expiry alerts; zone in Terraform/OpenTofu | Registry lock for the primary domain |
| DNS | One anycast provider; TTL 300 s on app records | CAA records; dangling-record audit; null MX on unused domains | Second provider or DNS failover only if the outage budget demands it |
| TLS | Platform-managed or Caddy automatic certificates | TLS 1.2 + 1.3 only; HSTS staged to one year; external certificate expiry alert; CT monitoring | `includeSubDomains`/preload after a full inventory; mTLS where required |
| Edge | The PaaS's built-in CDN | One CDN in front of everything, strict TLS to origin, origin locked, HTTP/3 on | WAF in block mode after log-mode tuning; rehearsed DDoS runbook |
| Caching | Fingerprinted assets `immutable` for a year; everything else uncached | Public HTML at the CDN with purge on deploy; authenticated routes `no-store` by default; `stale-if-error` on public pages | Tag-based purging; hit-ratio review; tiered caching |
| Proxy | The platform's router | Readiness and liveness endpoints; graceful shutdown; aligned timeouts | Connection-reuse tuning; least-connections for long-lived streams |
| Bots | Nothing | Edge rate limits on expensive endpoints; explicit AI-crawler policy | Bot management; per-bot limits or paid access |
| Monitoring | None | Synthetic checks from three regions | Per-protocol and per-region latency tracking |

Fixed choices at every stage:

- Self-managed proxy: Caddy on a new single server; nginx where it is already in use.
- Canonical host chosen once, the other 301-redirected in a single hop; HTTP to HTTPS in the same hop, except on an HSTS-preloaded apex, which must first redirect to HTTPS on itself.
- Compression at one layer: Brotli or zstd with gzip fallback, text only.
- IPv6 at the CDN edge; `AAAA` at the origin only when the whole path is verified.
- 0-RTT off; HTTP/2 push and domain sharding removed.
- App bound to loopback or a private interface; real client IP from a configured trusted-hop count, never `trust proxy = true`.
- Request timeout budget: client 35 s > proxy 30 s > app 25 s > database statement 20 s > outbound call 10 s; longer work becomes a job.
- App keep-alive idle timeout longer than the load balancer's idle timeout.

## Before you call it done

1. `dig +short` for every hostname returns the intended target from the authoritative server and from two public resolvers; no record points at a deleted resource.
2. `curl -sS -o /dev/null -L -w '%{num_redirects} %{url_effective}\n'` from `http://` on both apex and `www` reaches the canonical HTTPS URL in one hop (two from an HSTS-preloaded apex).
3. `openssl s_client -connect host:443 -servername host </dev/null` shows `Verify return code: 0 (ok)` with the full chain, for the edge and for the origin.
4. TLS 1.0 and 1.1 are refused (per `testssl.sh` or an online scanner; a modern local OpenSSL cannot offer them, so its failure proves nothing); HSTS is present on HTTPS responses with a deliberate `max-age`.
5. An external monitor alerts on certificate expiry and domain expiry, to more than one person.
6. Every response class carries an explicit `Cache-Control`; fingerprinted assets are `immutable`; authenticated responses are `no-store` and show a non-hit cache status.
7. A private URL with `.css` appended returns 404 or an uncached, `no-store` response; the same URL without cookies returns nothing private.
8. A request with a forged `X-Forwarded-For` does not change the client IP the app records.
9. The origin refuses a direct request that bypasses the CDN (`curl --resolve` to the origin address from outside).
10. Readiness fails when the database is unreachable and passes when an optional dependency is down; liveness depends on nothing external.
11. A request loop through a deploy shows no 5xx; SIGTERM reaches the app process and it drains.
12. Timeouts are written down per hop and follow the two ordering rules; the app server's keep-alive timeout is set explicitly and exceeds the idle timeout of the proxy or load balancer in front of it.
13. Compression is on for text and off for images and streams; `Vary: Accept-Encoding` is present.
14. HTTP/3 negotiates (`curl --http3-only`) and the site still works with UDP 443 blocked; `curl -4` and `curl -6` both succeed where `AAAA` is published.
15. Webhook, API and health-check paths are exempt from browser challenges; WAF changes went through log mode first.

## Not this skill

- CORS errors, Content Security Policy and other security headers → `0x:web-security`
- SPF, DKIM, DMARC and email landing in spam → `0x:email-notifications`
- Building WebSocket, SSE or WebRTC features → `0x:backend-architecture`
- VPCs, subnets, security groups and private cloud networking → `0x:cloud-infrastructure`
- Page-load speed, Core Web Vitals and image delivery → `0x:web-performance`
- Login rate limits, credential stuffing and signup bots → `0x:auth-identity`
