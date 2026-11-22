# TLS and certificates

Read this when: issuing, renewing or debugging certificates, choosing protocol versions and ciphers, turning on HSTS, deciding where TLS terminates, or setting up certificate authentication between services.

## Issuance and renewal with ACME

A certificate that a person renews by hand will expire in production. Every certificate is issued and renewed by software from day one, because public certificate lifetimes are shrinking on an industry schedule and manual processes get worse every year.
The CA/Browser Forum caps lifetimes at 200 days since March 2026, 100 days from March 2027 and 47 days from March 2029; Let's Encrypt has announced 64 days from February 2027 and 45 days from February 2028. Confirm the CA's current schedule before quoting a number.

Pick the least work that fits:

| Situation | Use | Notes |
|---|---|---|
| PaaS, CDN or managed load balancer in front | The platform's managed certificates | Nothing to run. Verify the custom domain shows "active", and that CAA allows the platform's CAs |
| One self-managed server | Caddy (automatic HTTPS built in), or nginx with certbot or acme.sh | Caddy needs only the site address in the Caddyfile and ports 80/443 reachable |
| Several servers behind a load balancer | Terminate at the load balancer; or DNS-01 issuance in one place with distribution through a secret store | HTTP-01 fails when the challenge request lands on a node that did not ask for it |
| Wildcard (`*.example.com`) | DNS-01 only | HTTP-01 and TLS-ALPN-01 cannot issue wildcards |
| Internal hosts not reachable from the internet | DNS-01 | The CA never has to reach the host |

Challenge types:

- **HTTP-01**: the CA fetches `http://<name>/.well-known/acme-challenge/<token>` on port 80. Port 80 must be open, and the path must not be blocked by auth, a WAF or bot challenge, a country block (CAs validate from several networks around the world), or a redirect to a host that cannot answer the challenge. A redirect to HTTPS on the same name is followed.
- **TLS-ALPN-01**: validation on port 443 only; used by Caddy when port 80 is unavailable.
- **DNS-01**: a `TXT` record at `_acme-challenge.<name>`. The DNS API token is powerful: scope it to the one zone, or delegate just the challenge label by `CNAME` to a throwaway zone and give the client credentials for that zone only.

Failure modes that recur:

| Symptom | Cause | Fix |
|---|---|---|
| Renewal succeeded, site still serves the old certificate until it expires | Server never reloaded | `certbot renew --deploy-hook "systemctl reload nginx"`; verify the served certificate, not the file |
| Validation fails though the site works in a browser | A stale `AAAA` record: Let's Encrypt validates over IPv6 first when one exists and retries over IPv4 only when the IPv6 connection times out, so an `AAAA` that points at some other live server fails outright | Fix or remove the `AAAA` |
| Issuance refused | `CAA` record does not list the CA | Add the CA (below) |
| Rate limited during setup | Repeated attempts against the production CA endpoint | Develop against the CA's staging endpoint (`certbot --staging`), then switch |
| Works for months, then fails | Port 80 closed later, DNS token revoked, config drift | Alert on expiry from outside (next section) |
| New container requests a certificate on every start | Certificate storage not persisted | Persist the ACME data directory (Caddy's `/data`) on a volume |

Use a client that supports ACME Renewal Information (ARI), so the CA can ask for early renewal during a mass-revocation event. Run the client at least daily and let it decide when to renew; a fixed schedule such as "every 60 days" breaks the first time lifetimes shorten. Prefer ECDSA P-256 keys: smaller handshakes, universally supported.

## Alert on certificate and domain expiry

Automation fails silently, so the monitor must look at what clients actually receive, from outside, and must not depend on emails from the CA or registrar (Let's Encrypt has ended its expiry notification emails).

```bash
# exit status 1 if the served certificate expires within 14 days (1209600 s), or if none could be fetched;
# size the window with the threshold rule below
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -checkend 1209600

echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -enddate -issuer -ext subjectAltName
```

- **Threshold follows the renewal schedule.** Clients renew with about a third of the lifetime left (30 days for a 90-day certificate), or earlier when ARI says so. Alert when remaining life drops clearly below that point (under 20 days of 90 means renewal has been failing for over a week) and escalate at 7 days.
  Scale both numbers with the lifetime: for a 45-day certificate, alert under about 10 days and escalate at 5. A threshold copied from the 90-day era either fires on healthy certificates or gets muted.
- **Cover every name and endpoint**: apex and `www`, API, per-tenant custom domains, mail and other non-HTTP TLS ports, and each origin behind the CDN (the CDN's certificate being fine says nothing about the origin's, and with strict origin validation an expired origin certificate takes the site down).
- **Domain expiry**: alert at 60, 30 and 7 days from the registry's RDAP/WHOIS expiry date, to someone other than the registrar's contact mailbox. Auto-renew fails on an expired card.
- At Launch, a hosted uptime monitor that checks both certificate and domain expiry is enough. Add it to the same alert channel as downtime.

## HSTS

`Strict-Transport-Security` tells a browser to refuse plain HTTP for the host for `max-age` seconds. It removes the insecure first hop and the redirect, and it is hard to undo: a browser that has seen it will not connect over HTTP until the time runs out, whatever the server does.

Stage it:

1. Confirm HTTPS works on the host and HTTP redirects to it.
2. `Strict-Transport-Security: max-age=300`. Watch for a day.
3. Raise to one week (`604800`), then one month (`2592000`).
4. Final: `max-age=31536000`.
5. Add `includeSubDomains` only after listing every subdomain in DNS and confirming each serves valid HTTPS: internal tools, vendor-hosted names such as status or docs pages, old marketing sites, device endpoints. One HTTP-only subdomain becomes unreachable for every browser that visited the apex.
6. `preload` last, and only as a deliberate decision. The preload list requires a one-year `max-age`, `includeSubDomains`, the `preload` token, and a redirect from HTTP on the apex; it ships inside browsers, and removal takes months to reach users.

Rules: the header counts only on HTTPS responses, and a browser learns it only for hosts it actually visits over HTTPS. When `www` is canonical, a direct `http://example.com` → `https://www.example.com` redirect never shows the browser the apex's header.
To protect the apex, and to qualify for preload, which requires it, redirect `http://example.com` → `https://example.com` first and send the header on that HTTPS response, accepting one extra hop on first visits.
Emergency rollback is `max-age=0`, which works only for browsers that return over HTTPS. Never enable HSTS on a host that might need plain HTTP again, and never on `localhost`-style development hostnames shared with other projects.

Default: Prototype none or short; Launch one year without `includeSubDomains` until the inventory is done; preload only when asked.

## Protocol versions and ciphers

Serve TLS 1.3 and TLS 1.2. Disable SSLv3, TLS 1.0 and TLS 1.1: no supported browser needs them and compliance scans fail on them. Keep TLS 1.2 because older Android devices, embedded clients, corporate proxies and some webhook senders still use it; dropping it is a decision to make from handshake-version logs, not by default.

On a CDN or managed load balancer this is a dropdown: choose the modern or recommended policy whose minimum is TLS 1.2. Self-managed, copy from the Mozilla SSL Configuration Generator ("intermediate" profile) instead of composing cipher strings by hand. The generator's current output wins over the block below, which shows the shape:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers off;
ssl_session_tickets off;
```

The principle behind that list: for TLS 1.2 allow only ECDHE key exchange (forward secrecy) with AEAD ciphers; no CBC, no RSA key exchange, no 3DES or RC4. TLS 1.3 suites are all acceptable and are not configured through `ssl_ciphers`. Session tickets stay off unless the ticket keys are rotated, because a long-lived ticket key undoes forward secrecy.

Check: `openssl s_client -connect example.com:443 -tls1_1 </dev/null` must fail (a recent local OpenSSL may refuse to offer it, which proves nothing; use `testssl.sh` or an online scanner such as SSL Labs for the full matrix).

## Debugging with openssl s_client

```bash
openssl s_client -connect example.com:443 -servername example.com -showcerts </dev/null
```

Read three things: the certificate chain as sent, `Verify return code`, and the negotiated protocol and cipher.
Useful variants: `-tls1_2` / `-tls1_3` to force a version, `-alpn h2` to test ALPN, `-noservername` to see the default certificate, `-connect 203.0.113.10:443 -servername example.com` to test one specific server behind DNS or a load balancer (or `curl --resolve example.com:443:203.0.113.10 -v https://example.com/`).

| Output | Cause | Fix |
|---|---|---|
| `Verify return code: 21 (unable to verify the first certificate)` or `20 (unable to get local issuer certificate)` | Server sends the leaf without its intermediate | Serve the full chain file (`fullchain.pem`), not the leaf alone |
| Works in Chrome, fails in curl, Node, Python, mobile apps, webhook senders | Same missing intermediate: browsers fetch or cache intermediates, other clients do not | Same fix. This is the most common chain bug |
| `certificate has expired` | Expired leaf or intermediate, or the client's clock is wrong | Renew and reload; check `date` on the client |
| Hostname mismatch | Name absent from the SAN list, or the request hit the default virtual host | Compare with and without `-servername`; reissue with the name |
| `tlsv1 unrecognized name` | The server has no site for that SNI | Add the hostname to the server or CDN configuration |
| `alert handshake failure` / `no protocols available` | No shared version or cipher | Compare client capability with server policy |
| `wrong version number` | The port speaks plain HTTP (or another protocol), not TLS | Wrong port, or TLS not enabled on that listener; common when a proxy sends `https://` to an HTTP backend |
| `self-signed certificate in certificate chain` | A TLS-inspecting proxy on the client's network, or a private CA the client does not trust | Add the CA to the client trust store (`NODE_EXTRA_CA_CERTS` for Node) |
| Handshake stalls after ClientHello | MTU black hole or a middlebox dropping large handshakes | `ip-transport.md` |

Never ship `curl -k`, `NODE_TLS_REJECT_UNAUTHORIZED=0` or `rejectUnauthorized: false` as the fix. They remove authentication entirely, and they tend to stay.

## CAA records

`CAA` lists the CAs allowed to issue for a name. CAs must check it before issuing; browsers do not. It narrows who can be tricked into mis-issuing.

```text
example.com.  CAA 0 issue "letsencrypt.org"
example.com.  CAA 0 issuewild ";"
example.com.  CAA 0 iodef "mailto:security@example.com"
```

- Lookup climbs the tree: a record at the apex covers every subdomain without its own `CAA` set. `issuewild` governs wildcards; without it, `issue` applies to them too. `issue ";"` forbids all issuance.
- **The trap:** platforms issue from several CAs and switch between them. Before adding CAA, list every party that issues for the domain (CDN, PaaS, email or status-page vendors with custom domains) and include all the CAs each one documents. A too-narrow CAA does not break anything today; it breaks the next renewal, weeks later.
- For tighter control, some CAs honor `accounturi` and `validationmethods` parameters that bind issuance to one ACME account.
- Check: `dig CAA example.com +short`.

Default: add at Launch once the issuing CAs are known.

## Where TLS terminates

| Topology | Use when | Watch for |
|---|---|---|
| Terminate at CDN, **re-encrypt to origin with certificate validation** | Default with any CDN | The CDN-to-origin leg crosses the public internet. Choose the strict mode that validates the origin certificate. A mode that sends plain HTTP to the origin makes the browser padlock a lie and produces redirect loops when the origin redirects HTTP to HTTPS |
| Terminate at load balancer or proxy, plain HTTP to the app | The hop stays on the same host or a private network the product alone controls | Acceptable through Launch. Tell the app the original scheme (`X-Forwarded-Proto`) or it generates `http://` URLs, drops `Secure` cookies, and loops on redirects |
| Terminate at load balancer, re-encrypt to backends | Shared or multi-tenant networks, regulated data, a customer or auditor requiring encryption in transit everywhere | Backends need certificates (a private CA or the platform's origin certificates) and the proxy must verify them, or the encryption authenticates nobody |
| TLS passthrough (layer 4) | The app must see the client certificate itself, or true end-to-end encryption is required | The proxy cannot route by path, add headers or cache; client IP needs PROXY protocol |

Each termination point holds private keys: fewer points, fewer places to patch and rotate.

nginx as the re-encrypting proxy neither verifies the upstream certificate nor sends SNI unless told to: `proxy_pass https://...` alone encrypts to whoever answers. Add `proxy_ssl_verify on;`, `proxy_ssl_trusted_certificate <ca-bundle>;`, `proxy_ssl_server_name on;` and `proxy_ssl_name <expected-name>;`.

## Certificate Transparency monitoring

Every publicly trusted certificate is published to CT logs, which makes them a free detector for mis-issuance and for shadow infrastructure.

- Subscribe to a CT monitor for the registered domain (crt.sh for manual search; Cert Spotter or the CDN's CT alerting for notifications).
- An unexpected certificate is usually a vendor issuing on the product's behalf, or a teammate's experiment. Verify against the CAA list and the vendor inventory. If nobody can explain it: treat DNS or a hosting account as compromised, ask the issuing CA to revoke, rotate DNS and registrar credentials, tighten CAA.
- Side effect to plan for: CT logs publish every hostname on every certificate. `admin-internal.example.com` is public the moment it gets a certificate. Use a wildcard certificate for names that should not be enumerable, and never rely on an unguessable hostname as protection.

Skip until Launch; then it is a five-minute subscription.

## Mutual TLS between services

mTLS makes both sides present certificates. It fits service-to-service calls across networks that are not trusted, and B2B APIs where a customer demands it.
For a small product inside one private network, signed tokens or a private overlay network give most of the benefit with far less machinery; choose mTLS when a requirement names it or a platform (service mesh, managed ingress) provides it nearly free.

If it is built:

- **Private CA**, never public certificates: browser root programs are phasing the client-authentication usage out of publicly trusted server certificates (several CAs have already stopped issuing it), and trusting a public CA for client auth means trusting everyone that CA issues to. Use a managed private CA, `step-ca`, or cert-manager.
- **Short lifetimes with automatic rotation** (hours to days) instead of revocation lists, which nobody operates well.
- **Authorize the identity, not the chain.** "Signed by our CA" proves membership, not permission. Check the SAN (a DNS name or SPIFFE URI) against an allow-list per endpoint.
- nginx, server side: `ssl_client_certificate /etc/ssl/internal-ca.pem; ssl_verify_client on;`. As a client to an upstream: `proxy_ssl_certificate`, `proxy_ssl_certificate_key`, `proxy_ssl_trusted_certificate`, `proxy_ssl_verify on;`, `proxy_ssl_server_name on;` and `proxy_ssl_name`.
- **Traps:** load balancer health checks carry no client certificate, so give them a separate listener or path; rotating the CA requires distributing a bundle with old and new roots before any leaf switches; the private root's own expiry, years out, is an outage with a date on it and belongs in the expiry monitor; short-lived certificates fail on hosts with clock drift.

## Hybrid post-quantum key exchange

Recorded traffic can be decrypted later by an attacker with a quantum computer unless the key exchange was quantum-resistant. The deployed answer is a hybrid group that combines X25519 with ML-KEM (`X25519MLKEM768`) in TLS 1.3. Major browsers offer it by default and large CDNs accept it, so a site behind such a CDN is likely already using it on the browser leg.

- **Action for most products:** none beyond keeping TLS 1.3 on and confirming in the CDN's analytics or the browser's security panel that the hybrid group is negotiated. Then check the CDN-to-origin leg, which is separately configured.
- **Self-managed:** it requires a TLS library that implements the group (OpenSSL 3.5 or later, recent BoringSSL and Go). Offer the hybrid first and keep classical groups as fallback; never offer hybrid only.
- **Compatibility risk:** the hybrid key share makes the ClientHello larger than one packet. Old middleboxes and a few server stacks mishandle a split ClientHello and reset the connection. Symptom: handshake failures only from the newest browsers, or only on one corporate network.
- **Test:** `openssl s_client -connect example.com:443 -groups X25519MLKEM768 </dev/null` with OpenSSL 3.5 or later and read the negotiated group in the output (an older OpenSSL rejects the group name, which says nothing about the server); test outbound integrations (webhooks, payment APIs) after upgrading the client library, since the server on the other end may be the fragile one.
- Certificates with post-quantum signatures are not yet part of the public web PKI; nothing to do there.

## Ask the user

- **Is there any subdomain that cannot serve HTTPS, now or soon?** Decides `includeSubDomains` and preload. Default: no `includeSubDomains` until every DNS name is verified; no preload.
- **Which vendors serve content on the domain's subdomains?** They issue certificates too, which shapes CAA and HSTS. Default: inventory from DNS records before adding CAA.
- **Does a customer, auditor or regulation require encryption on internal hops or mTLS?** Default: TLS to the edge and strict re-encryption on any hop that crosses a public network; plain HTTP only on a private hop.
- **Do old clients matter (embedded devices, legacy enterprise proxies, old Android)?** Decides whether TLS 1.2 can ever be dropped. Default: keep TLS 1.2 and 1.3.
- **Who receives expiry alerts when the founder is unavailable?** Default: the shared on-call channel plus one other person's phone.
