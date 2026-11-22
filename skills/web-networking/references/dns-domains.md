# DNS and domains

Read this when: registering or moving a domain, adding or changing records, switching DNS provider or registrar, or debugging a name that does not resolve or resolves to the wrong place.

## The domain is the root of everything

Whoever controls the registrar account controls the website, the email, every password reset sent to that email, and certificate issuance. Losing a domain is the one infrastructure failure a company may not recover from. Set this up at Prototype, not later:

| Control | Setting | Why |
|---|---|---|
| Ownership | Account belongs to the company with a founder as contact; never a contractor's, agency's or ex-employee's personal account | Disputes over a domain held by someone else take months |
| Account email | A mailbox on a different domain than the one being registered | If the domain lapses or DNS breaks, mail to it stops and recovery emails cannot arrive |
| MFA | Hardware key or TOTP; no SMS fallback; recovery codes stored offline | Registrar account takeover is a full company takeover |
| Transfer lock | Registrar lock on (`clientTransferProhibited` in WHOIS/RDAP status) | Blocks an unauthorized transfer out |
| Auto-renew | On, with a card that does not expire soon and a backup payment method; renew the primary domain for several years | Most domain losses are an expired card, not an attack |
| Expiry alert | Independent of the registrar's emails (see `tls-certificates.md`) | Registrar notices go to spam or to a departed person |
| Registry lock | Only for a high-value domain at Scale; requires out-of-band verification for changes | Costly and slow by design |

After expiry a domain typically stops resolving at once or within days, passes through a grace period, then a redemption period with a steep recovery fee, then release to the public where drop-catchers take it within seconds. Periods differ by TLD. Country-code TLDs carry their own rules (residency requirements, different transfer and dispute procedures); check them before building a brand on one.

Keeping the registrar and the DNS host as separate companies is fine and often better: a registrar is chosen for account security, a DNS host for its API, anycast network and uptime.

## Records for a production domain

| Need | Record | Rules and traps |
|---|---|---|
| Apex (`example.com`) to a server IP | `A` and, if IPv6 works end to end, `AAAA` | Publish `AAAA` only when the path is verified (`ip-transport.md`) |
| Apex to a hostname (PaaS, CDN, load balancer) | `ALIAS` / `ANAME` / CNAME flattening | Not a standard record type: the DNS provider resolves the target and answers with `A`/`AAAA`. A real `CNAME` at the apex is invalid because the apex already holds `SOA` and `NS` |
| `www` or any subdomain to a hostname | `CNAME` | A name with a `CNAME` can hold no other record: no `MX`, no `TXT` beside it. Verification `TXT` records for a CNAME'd name therefore go on a different label (`_acme-challenge.`, `_vendor.`) |
| Receive mail | `MX` with priority, pointing to hostnames | The target must be a name with `A`/`AAAA`, never an IP and never a `CNAME` |
| No mail on this domain | Null MX: `MX 0 .`, plus a reject-all SPF and DMARC policy | Stops spoofing of parked and secondary domains; details in `0x:email-notifications` |
| Verification, SPF, DKIM, DMARC | `TXT` | One SPF record per name; several `v=spf1` records make SPF fail. A string longer than 255 bytes must be split into quoted chunks (most UIs do it). SPF/DKIM/DMARC content: `0x:email-notifications`, `deliverability.md` |
| Restrict certificate issuance | `CAA` | `tls-certificates.md` |
| Advertise HTTP/3 or ECH | `HTTPS` | `http.md` |

Decisions to make once:

- **Canonical host.** Pick apex or `www`, serve the site on one, and 301 the other to it. `www` keeps a plain `CNAME` available, which every DNS host and CDN supports; apex is shorter. If the DNS provider has no `ALIAS`-style record and the host gives only a hostname, `www` is the only correct choice.
- **Wildcards.** `*.example.com` answers for every name that has no record of its own, including typos and names an attacker invents. Use one only when the product needs it (per-tenant subdomains), and never point it at third-party infrastructure.
- **Zone file syntax.** In a raw zone file a target without a trailing dot is relative to the zone: `CNAME target.example.net` becomes `target.example.net.example.com`. Most web UIs hide this; Terraform and BIND do not.
- **Keep the zone in code** (Terraform/OpenTofu or DNSControl) from Launch. It gives history, review, and a rebuildable zone when changing providers.

## Trace delegation with dig

Resolution walks root → TLD → authoritative. Each debugging command asks one layer directly so caches cannot lie.

```bash
dig +trace example.com A                      # walk from the root; shows which servers each level delegates to
dig NS example.com @a.gtld-servers.net +norecurse   # what the .com registry says the nameservers are
dig example.com A @ns1.provider.net +norecurse      # what the authoritative server answers (look for flag "aa")
dig example.com A @1.1.1.1 +short             # what a public resolver has cached
dig example.com A @8.8.8.8 +short
dig +nssearch example.com                     # SOA from every listed nameserver: serials should agree
```

Read the status in the header before the answer:

| Status | Meaning | Look at |
|---|---|---|
| `NOERROR` with answer | Works | Is it the expected value, and from which server |
| `NOERROR`, empty answer | The name exists but has no record of that type | Wrong type queried, or `AAAA` missing; a `CNAME` chain that ends in nothing |
| `NXDOMAIN` | The name does not exist | Typo, record in the wrong zone, the zone is not the one being served |
| `SERVFAIL` | The resolver could not get a valid answer | Broken DNSSEC (retry with `dig +cd`: if that works, it is DNSSEC), nameservers unreachable, lame delegation |
| `REFUSED` | That server does not serve the zone | Registrar points at nameservers where the zone was never created or was deleted |

The most common real fault: the registrar's nameserver list and the place where records are edited are different providers. Editing records in a zone nobody is delegated to has no effect. Compare the registry's `NS` answer with the provider whose dashboard is open.

## "It has not propagated"

DNS does not propagate; caches expire. A change is visible at the authoritative servers within seconds, and each resolver keeps its old answer until the TTL it cached runs out. So the wait is bounded by the **old** TTL, and any report beyond that has another cause.

Diagnose in this order:

1. Query the authoritative server directly. Wrong there: the change was not saved, or it was made at the wrong provider.
2. Query public resolvers. Old answer with a decreasing TTL (run `dig` twice and watch the number fall): wait it out. Google and Cloudflare offer public cache-flush pages for their resolvers.
3. Right everywhere but wrong on one machine: local caches. Browser (Chrome keeps its own short-lived cache, visible at `chrome://net-internals/#dns`), OS (`sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` on macOS, `ipconfig /flushdns` on Windows, `resolvectl flush-caches` on systemd Linux), `/etc/hosts` entries left from testing, a VPN or corporate resolver with split DNS.
4. Right in DNS but traffic still reaches the old server: established keep-alive connections and connection pools never re-resolve. Long-running services hold old addresses until restarted or until their pool recycles. Keep the old target serving for hours after a cutover.

**Negative caching** is the trap that explains "the record exists but my laptop says it does not". An `NXDOMAIN` or empty answer is cached for the lesser of the SOA record's TTL and its `MINIMUM` field (read both with `dig SOA example.com`): minutes at some providers, hours at others. Checking a name before creating it caches the absence. Create the record first, then test; or test against the authoritative server only.

Nameserver changes are slower than record changes: the delegation's TTL is set by the TLD registry (two days for `.com`) and cannot be lowered.

## TTL choices

| Record | TTL | Reason |
|---|---|---|
| App `A`/`AAAA`/`CNAME`/`ALIAS` that may need to move | 300 s | Five-minute worst case to repoint; negligible cost |
| Records used for DNS failover | 60 s | Lower values are ignored by some resolvers and multiply query volume |
| `MX`, `TXT`, `CAA`, verification records | 3600 s | Rarely change; a longer cache rides through a short DNS-provider outage |
| `NS` inside the zone | 86400 s | Changing them is a planned migration anyway |

Before a planned change, lower the TTL to 60 to 300 s at least one full **old** TTL in advance, make the change, verify, then raise it again. A 24-hour TTL lowered five minutes before a migration is still a 24-hour TTL in every cache.
Low TTLs do not make an outage shorter if the DNS provider itself is down; they make it start sooner, which is the argument for not putting 60 s on everything. With per-query billing, TTL also sets the bill.

## Moving DNS provider or registrar

These are two different moves. Do them separately, DNS first.

**Changing DNS provider (nameservers):**

1. Inventory every record. Providers rarely allow zone transfer, and exports omit proprietary types. Cross-check against the list of subdomains in certificate transparency logs and in the app's config. A forgotten `MX` or DKIM record is the classic casualty.
2. Recreate the zone at the new provider. Translate proprietary records (`ALIAS`, health-checked or geo answers) by hand.
3. Verify before switching: for every name and type, compare `dig @old-ns` with `dig @new-ns`.
4. If DNSSEC is on: remove the `DS` record at the registrar and wait out its TTL before changing nameservers, then re-enable signing afterward. Switching nameservers with a `DS` that points at the old provider's keys makes the domain fail for every validating resolver.
5. Change the nameservers at the registrar.
6. Keep the old zone live and identical for at least the longer of the delegation TTL and the old zone's own `NS` TTL, plus a margin (three days for `.com`). Resolvers use both sets during that window, so any record edit must be made in both.
7. Delete the old zone last.

**Transferring registrar:**

- A transfer moves the registration, not the DNS. If the losing registrar is also the DNS host, its nameservers may stop answering when the transfer completes. Move DNS to an independent provider first and let it settle.
- Sequence: unlock, obtain the authorization (EPP) code, start the transfer at the gaining registrar, approve the confirmation. gTLD transfers can take several days unless the losing registrar releases early, usually add a year to the term, and are blocked for a period after registration or a previous transfer (60 days for many years; ICANN's revised transfer policy shortens it, so read the registrar's current rule). Country-code TLDs each have their own procedure.
- Do not start within a few weeks of expiry, and do not change registrant contact details just before: either can trigger a lock or a lapse mid-transfer.
- Afterward re-check lock, auto-renew, MFA, and the `DS` record if DNSSEC is in use.

## Dangling records and subdomain takeover

A record that points at a resource that no longer exists hands the subdomain to whoever claims that resource next.
Typical cases: a `CNAME` to a deleted PaaS app, storage bucket, static site or CDN distribution whose name can be re-registered by anyone; an `A` record to a released cloud IP; an `NS` delegation of a subdomain to a deleted hosted zone, which is the worst case because it gives full control of everything under that name.

With the subdomain an attacker serves content on a trusted origin: obtains a valid certificate for it, reads cookies scoped to the parent domain, receives OAuth redirects and password-reset links that were allow-listed for it, and phishes with a real URL.

- **Order of operations.** Tear down: delete the DNS record, wait the TTL, then delete the resource. Bring up: create the resource, then the record.
- **Tie them together.** A record and its target in the same Terraform module are destroyed together; hand-made records for "temporary" demos and campaign sites are the ones that dangle.
- **Audit** at Launch and after every decommission: list every `CNAME`, `ALIAS`, `NS` and third-party `A` record, resolve each target, and treat `NXDOMAIN` or a provider's "no such app/bucket" page as dangling. Remove records for vendors no longer used, including their verification `TXT` records.
- Prefer providers that require domain-ownership verification before a custom hostname attaches; it closes the hole on their side.

## Health-checked failover and latency routing

DNS-level traffic steering returns different answers depending on health checks or the resolver's location. Know its limits before choosing it:

- **Failover time** = detection (check interval × failure threshold) + record TTL + clients that ignore TTL or hold connections. With 30 s checks, three failures and a 60 s TTL that is two to three minutes for most users and longer for a tail. It is a disaster-recovery tool, not high availability.
- **Location is the resolver's**, not the user's, unless the resolver forwards EDNS Client Subnet, and some large public resolvers deliberately do not. Latency routing is approximate.
- Health checks must probe a real readiness endpoint over HTTPS from several locations (`proxies-load-balancers.md`), and the policy must fail open: if every target looks unhealthy, answer with all of them, because the checker is more likely wrong than every region is down.
- The standby must be able to take the traffic: same certificate, enough capacity, and a data story. Failing over the web tier to a region whose database is a stale replica converts an outage into data divergence; that decision belongs to `0x:site-reliability`, `disaster-recovery.md`.
- Guard against flapping with a higher threshold to return than to fail.

Default: skip before Scale. A CDN or load balancer with several origins fails over in seconds without touching DNS.

## DNSSEC

DNSSEC signs answers so resolvers can detect forgery. For a small product the benefit is modest and the failure mode is total: a mismatch between the `DS` record at the registry and the keys the zone serves returns `SERVFAIL` to every validating resolver, which includes the major public ones.
Enable it when a customer or a compliance regime asks, or when the DNS provider makes it one switch with automatic key management.

- **Enable:** turn on signing at the DNS provider → confirm `dig DNSKEY example.com +short` answers from every nameserver → add the `DS` record at the registrar (automatic when registrar and DNS host are the same company).
- **Disable or migrate:** remove the `DS` at the registrar → wait the `DS` TTL (commonly a day) → only then stop signing or change nameservers. Reversing these two steps is the standard DNSSEC outage.
- **Key rollover:** let the provider roll zone-signing keys. For the key-signing key, publish the new `DNSKEY`, add the new `DS` beside the old one, wait both TTLs, remove the old `DS`, wait the `DS` TTL again, then retire the old key. Never replace a `DS` in one step.
- Prefer ECDSA P-256 (algorithm 13): small signatures keep answers inside one UDP packet.
- **Check:** `delv example.com` or `dig +dnssec example.com` (the `ad` flag from a validating resolver), a visual chain validator such as DNSViz, and `dig +cd` to prove a `SERVFAIL` is validation.

## Two authoritative providers

A DNS provider outage takes down everything that depends on the name, including services that are themselves healthy. Running two providers removes that single point at the price of constant synchronization. This is a Scale decision.

- **Models.** Primary/secondary: one provider holds the zone and the other pulls it by zone transfer. Dual primary: a tool (OctoDNS, DNSControl, Terraform with two providers) pushes the same records to both. Dual primary is the practical choice when neither provider supports transfers.
- **Delegation.** List nameservers from both providers at the registrar and in the `NS` set of both zones.
- **Lowest common denominator.** Only standard record types survive. `ALIAS`, geo and health-checked answers behave differently or not at all across providers; the apex must resolve consistently on both.
- **DNSSEC** across two signing providers needs multi-signer coordination, which few providers support. In practice: two providers or DNSSEC, rarely both.
- **Monitor** that both answer and agree: compare SOA serials or a record digest on a schedule, and alert on drift.

Default before Scale: one reputable anycast DNS provider with the zone in code, so a second can be stood up in an hour.

## Ask the user

- **Who owns the registrar account, and where do its recovery emails go?** If the answer is a contractor or a mailbox on the same domain, fix that first. Default: move it to a company account with a founder's separate-domain email and hardware-key MFA.
- **Apex or `www` as the canonical address?** Affects DNS record choice, cookies and every printed URL. Default: follow what is already live; for greenfield, apex if the DNS provider has `ALIAS`-style records, otherwise `www`.
- **Does this domain send or receive email, and through which providers?** A DNS move that drops `MX` or DKIM silently breaks mail. Default: assume yes and inventory mail records before any change.
- **Is there a requirement for DNSSEC** from a customer, tender or regulator? Default: off until required or until the provider automates it fully.
- **How long may the site be unreachable if the DNS provider or one region fails?** Decides whether DNS failover or a second provider is worth the upkeep. Default: accept provider-level risk before Scale.
- **Are other domains (typos, other TLDs, old brands) registered anywhere?** They need the same lock, renewal and null-mail setup. Default: consolidate them into the same account.
