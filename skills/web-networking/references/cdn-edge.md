# CDN setup and edge protection

Read this when: putting a CDN in front of an origin, working out the real client IP, locking the origin, writing edge functions, tuning a WAF or rate limits, setting a policy for AI crawlers and scrapers, or preparing for and responding to a DDoS.

## What goes through the CDN, and how

Default from Launch: one CDN in front of everything served over HTTP, with DNS for the proxied names on the same provider. It supplies TLS at the edge, HTTP/3, caching, DDoS absorption and a place to block traffic before it costs anything.
If the PaaS already includes a CDN, use that one; stacking a second CDN in front doubles the purging, hides client IPs twice and creates conflicting cache rules, so add one only for a capability the first lacks.

Decide per class of traffic, not for the site as a whole:

| Traffic | Treatment | Notes |
|---|---|---|
| Fingerprinted assets | Cache long | `http-caching.md` |
| Public HTML and public `GET` API | Cache with a CDN lifetime and purging | Bypass when a session cookie is present |
| Logged-in HTML and private API | Proxy, never cache | Still gains TLS, connection reuse and protection |
| Inbound webhooks from providers | Proxy; exempt from challenges and bot rules | Senders cannot solve a challenge; verify signatures in the app (`0x:api-design`, `webhooks.md`) |
| WebSocket and SSE | Proxy; confirm the plan supports them and note the idle limit | `proxies-load-balancers.md` |
| Large uploads and downloads | Bypass the proxy: direct to object storage with signed URLs | CDNs cap request body size and bill egress (`0x:backend-architecture`, `file-uploads.md`) |
| Requests that run longer than the edge's origin timeout | Redesign as a background job with polling | Every CDN cuts off a silent origin after a fixed time |
| Admin and internal tools | Proxy behind an access gate, or keep off the public internet | |
| Mail (`MX` targets), SSH and other non-HTTP services | DNS-only records, not proxied | An HTTP proxy does not carry them, and proxying a mail host breaks delivery |

Cutover sequence:

1. Origin serves valid HTTPS on its own hostname or IP.
2. Configure the CDN: strict TLS to the origin (`tls-certificates.md`), cache rules, real-client-IP handling in the app and proxy (below).
3. Test through the CDN before moving DNS: `curl -sv --resolve example.com:443:<cdn-edge-ip> https://example.com/`.
4. Lower the DNS TTL a full old TTL in advance, switch the record, watch error rate and cache status.
5. Lock the origin (below) and, if its address was ever in public DNS, move it to a new address.

## The real client IP

Behind a CDN the TCP peer is the CDN. The client address arrives in a header, and headers are whatever the sender wrote. The only unforgeable fact is the peer address of each connection; everything else is trusted hop by hop.

- `X-Forwarded-For` is a list that each proxy appends to. A client can send its own `X-Forwarded-For: 1.2.3.4` and the first proxy appends the true address after it. **Leftmost is attacker-controlled. The trustworthy entry is the rightmost one that was appended by a proxy the product operates or trusts**: count known hops from the right.
- A CDN's single-value header (`CF-Connecting-IP`, `True-Client-IP`, `Fastly-Client-IP`) is simpler, but it is trustworthy only when the request provably came from the CDN. If the origin is reachable directly, anyone can send that header.
- Configure the trust explicitly:
  - Express: `app.set('trust proxy', 2)` with the real number of proxy hops, or a list of proxy subnets. `true` trusts every hop and returns the spoofable leftmost value.
  - nginx: `set_real_ip_from <each CDN or load balancer range>;` with `real_ip_header X-Forwarded-For;` and `real_ip_recursive on;` (or `real_ip_header CF-Connecting-IP;`).
  - Layer-4 load balancers carry the address in PROXY protocol, which both ends must enable together.
- CDN address ranges change; generate the allow-list from the provider's published list on a schedule.

Getting it wrong fails in two directions: trusting too much lets anyone evade rate limits and bans and forge audit logs by sending a header; trusting too little makes every user appear as a handful of CDN addresses, so one abuser's limit blocks everyone.

Check: `curl -sS -H 'X-Forwarded-For: 203.0.113.99' https://example.com/<endpoint-that-echoes-ip>` must report the caller's real address, never `203.0.113.99`; and app logs for normal traffic must show many distinct addresses.

## Lock the origin

Protection at the edge is optional for an attacker who can reach the origin directly. Methods, strongest first; combine a network control with an authentication control:

| Method | Strength | Notes |
|---|---|---|
| Outbound tunnel or private link from origin to CDN | Origin has no public inbound port at all | Best where available; one more daemon to keep running |
| Firewall allow-list of the CDN's ranges | Blocks the open internet | The ranges are shared by every customer of that CDN, so another customer can still proxy to the origin. Not sufficient alone |
| mTLS from CDN to origin (authenticated origin pulls) | Proves the request came through this account when a per-account certificate is used | The CDN-wide shared certificate proves only "some customer" |
| Secret header added at the edge and verified at the origin | Simple, works on a PaaS origin with no firewall | Treat as a credential: rotate it, compare in constant time, strip it from anything logged |

How origin addresses leak, to check before relying on secrecy: historical DNS records for the domain; a non-proxied subdomain (`direct.`, `origin.`, `staging.`) on the same IP;
`MX` or SPF entries pointing at the same server; internet-wide scans that match the certificate served on the bare IP; outbound requests and emails sent from the origin's address. Make the origin's default virtual host return nothing identifying, and rotate the address after the CDN goes in.

Check from a machine outside the CDN: `curl -sv --max-time 10 --resolve example.com:443:<origin-ip> https://example.com/` must time out or be rejected.

## Edge functions

Use an edge function when the decision needs only the request itself and must happen before cache or origin:

- Redirect maps, canonical host and locale routing.
- Request and response header rewrites; cache-key normalization.
- Assigning an experiment bucket or reading geolocation into a header.
- A coarse auth gate: verify a signed session cookie or JWT and reject or redirect unauthenticated requests before they reach the origin.

Keep out of the edge: anything that queries a regional database on every request (the function runs near the user, the data does not, so it adds latency), CPU-heavy work, business rules, and code that needs full Node.js APIs. Runtime limits and platform choice: `0x:cloud-infrastructure`, `serverless-edge.md`.

Rules:

- **Prefer a declarative rule over code** when the CDN has one (redirect rules, header transforms, cache rules). It cannot throw and costs nothing per request.
- **An edge auth check is a filter, not authorization.** Checking that a cookie exists is not verification; verify the signature and expiry. The origin still enforces who may do what, because the edge can be bypassed by a routing mistake and does not know resource ownership.
- **Decide failure behavior explicitly.** A function that throws either fails open (request continues to origin) or closed (error). Auth gates fail closed; cosmetic rewrites fail open. Know the platform's default.
- **Scope the matcher.** A function on every request, including assets, adds latency and billable invocations to all of them.
- Deploy edge code from the repository with the app, with secrets in the edge platform's secret store, and make sure its errors reach the same error tracker.
- A function that changes the response by a request property must put that property in the cache key (`http-caching.md`), or it poisons the cache.

## WAF tuning

A managed WAF ruleset buys time against mass scanning and newly published exploits. It does not fix vulnerable code (`0x:web-security`), and enabled carelessly it blocks paying customers who never tell anyone.

Rollout:

1. Enable the managed ruleset in log-only (count) mode.
2. Run one to two weeks across normal activity, including billing runs, imports and admin work.
3. Review the matches. For each false positive, add the narrowest exception: that rule ID, on that path or parameter. Do not disable a whole category or the WAF for a hostname.
4. Switch to block. Alert on a sudden rise in blocked requests, which is either an attack or a release that started tripping a rule.
5. Repeat the log-first step for every new ruleset version or sensitivity change.

Where false positives come from: fields that legitimately contain markup or code (rich-text editors, support tickets, a SQL or snippet feature), JSON bodies with unusual characters, file uploads, and server-to-server traffic.

- **Never present an interactive or JavaScript challenge to non-browsers.** API clients, mobile apps, webhook senders, payment callbacks, uptime monitors and health checks cannot solve one; they see failures. On those paths the actions are allow, rate limit or block.
- The block page should show a request ID and a support contact, so support can find the exact rule that fired.
- WAFs inspect only the first part of a large body; do not assume a big upload was scanned.
- Country blocking is blunt: travelers, VPN users and customers in the blocked country are locked out. Use it as a temporary attack measure, or where trade rules require it (`0x:privacy-compliance`, `sector-consumer-rules.md`).

## Rate limits and challenges at the edge

The edge is the right place for coarse limits because the request is refused before it consumes origin capacity. Fine-grained per-account and per-key quotas stay in the application (`0x:api-design`, `idempotency-rate-limits.md`); login, signup and credential-stuffing defenses belong to `0x:auth-identity`, `abuse-defense.md`.

| Decision | Guidance |
|---|---|
| Counting key | API key or session where present; otherwise IP, with IPv6 aggregated to /64. Shared carrier and office addresses mean per-IP limits must be generous |
| Scope | A loose site-wide limit plus tight limits on expensive endpoints: search, exports, report generation, anything that calls a paid API or sends email |
| What to count | Requests that reach the origin; cached hits are nearly free |
| Action ladder | Log, then non-interactive challenge (browser paths only), then `429` with `Retry-After`, then a timed block |
| Thresholds | From measurement: take the busiest legitimate client over a normal week and set the limit at several times that. Guessing produces either blocked customers or no protection |

A distributed attack spreads below any per-IP threshold. The next keys are the bot score or TLS/HTTP fingerprint the CDN provides, the network (ASN) for hosting-provider traffic that no customer uses, and the specific path under attack. Verified crawlers and monitoring should be allow-listed by verified identity, not by `User-Agent`, which anyone can copy.

## AI crawlers and scrapers

The policy is a business decision with a network implementation. Separate four kinds of automated client, because the right answer differs:

| Kind | Examples | Usual policy |
|---|---|---|
| Search engine indexing | Googlebot, Bingbot | Allow |
| AI model-training crawlers | GPTBot, ClaudeBot, CCBot; `Google-Extended` is a robots.txt token rather than a separate crawler | Owner's choice: allow, block or license |
| AI search and user-triggered fetchers (retrieve a page to answer a question, often with a citation) | The vendors' separate search and user agents | Usually allow for marketing and documentation: this is how the product appears in AI answers |
| Undeclared scrapers imitating browsers | Arbitrary | Not a policy question; they ignore policy. Rate limits and bot detection |

- `robots.txt` is a request, honored by declared crawlers and ignored by the rest. Enforcement is an edge rule keyed on verified bot identity (the operator's published address ranges or the CDN's verified-bot classification). Vendor crawler names and roles change; read each vendor's current documentation instead of copying an old list.

```text
User-agent: GPTBot
Disallow: /
```

- Typical SaaS: allow search and AI retrieval on the marketing site and docs; disallow everything on the app and API hostnames, which require login anyway.
- Typical content business, where the pages are the product: block training crawlers, decide retrieval case by case, and consider the CDN's pay-per-crawl or a licensing deal at Scale.
- Often the real complaint is cost, not content: crawlers walk the uncached long tail and every faceted URL. Fix that with caching, canonical URLs, `Disallow` on infinite spaces (search results, filters, calendars) and a per-bot rate limit before reaching for a block.
- Terms of service language about automated access: `0x:privacy-compliance`, `terms-policies.md`.

## DDoS response, rehearsed

Volumetric network floods are absorbed by the CDN without action, provided the origin cannot be reached around it. What needs a human is an application-layer flood: plausible HTTP requests aimed at expensive, uncacheable endpoints.

Prepare at Launch (an hour of work):

- Origin locked; public pages cached with `stale-if-error`.
- Rate-limit and challenge rules for the expensive endpoints written and left disabled or in log mode, so turning them on is one click.
- Location of the CDN's emergency mode (challenge all visitors) known and tried once.
- Two people who can log in to the CDN and DNS accounts, with MFA devices that work, and the steps written where both can find them without the site being up.
- The provider's support channel and what the current plan includes during an attack. Find out now, not during one.
- Spend caps and billing alerts on anything that autoscales or bills per request or per byte: an attack on serverless functions or egress is a denial-of-wallet attack.
- A status page hosted off the main infrastructure.

During:

1. **Confirm it is an attack.** A launch spike, a crawler, or the product's own client retrying in a loop after a bad release look similar. Break traffic down by path, ASN, country, `User-Agent` and cache status.
2. Challenge or rate-limit the targeted paths; widen to the whole site only if needed. Keep APIs and webhooks on rate limits, not challenges.
3. Make the target cheap: cache it, serve a static version, or switch the feature off with a flag.
4. Block the clearly irrelevant sources (hosting ASNs, countries with no customers) as a temporary rule with an expiry.
5. Protect the database: lower concurrency limits, shed load with 503 and `Retry-After` rather than letting queues grow.
6. Post a status update; contact the provider with the request IDs and patterns seen.

After: rotate the origin address if it was hit directly, keep the rules that worked in log mode, and write up the timeline (`0x:site-reliability`, `incident-response.md`). Do not pay extortion demands that precede or accompany an attack.
Rehearse as a 30-minute tabletop at Launch and a real drill at Scale; load-testing a production site through a CDN needs the provider's permission (`0x:web-performance`, `load-testing.md`).

## Ask the user

- **Should AI companies be able to train on, or retrieve and cite, the site's content?** It trades visibility in AI answers against control of the content. Default: allow search and AI retrieval on marketing and docs, block training crawlers only if the content is the product, disallow all on the app.
- **Which countries and networks do real customers come from?** Decides what can be blocked or challenged aggressively during an attack. Default: block nothing by geography in normal operation.
- **What is the maximum acceptable bill for a traffic spike?** Sets spend caps and how hard to rate-limit. Default: billing alerts at a few multiples of normal spend and hard caps where the platform offers them.
- **Who besides the founder can operate the CDN account in an emergency?** Default: add one trusted person with their own MFA before Launch.
- **Do customers post content that looks like code or markup?** Predicts WAF false positives. Default: assume yes for any rich-text, support or developer-facing field and exempt those parameters from injection rules after review.
- **Is being behind one CDN vendor acceptable?** Default: yes before Scale; keep DNS and cache configuration in code so a move is days, not months.
