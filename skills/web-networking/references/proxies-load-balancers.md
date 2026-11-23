# Reverse proxies and load balancers

Read this when: configuring nginx, Caddy, an ingress or a cloud load balancer in front of the app, routing several backends, deploying without dropped requests, proxying WebSockets or streams, or chasing 502, 503 and 504 errors.

On a PaaS the platform is the proxy: there is nothing to configure except the health check path, the app's graceful shutdown and its timeouts, and those three sections still apply. On a single self-managed server, default to Caddy (automatic HTTPS, safe defaults); keep nginx when the project already uses it.
If the deploy tool brings its own proxy (Kamal's kamal-proxy, Coolify's built-in one), use that and do not put Caddy in front of it (`0x:cloud-infrastructure`, `docker-images.md`).

## Health checks

Two different questions, two endpoints. Mixing them causes outages.

| | Readiness (`/readyz`) | Liveness (`/livez`) |
|---|---|---|
| Question | Can this instance serve a request right now? | Is this process beyond recovery? |
| Consumer | Load balancer, deploy orchestration | Process supervisor or orchestrator (restarts on failure) |
| Checks | Startup finished, config loaded, a database connection can be acquired (cheap query, short timeout) | The event loop answers. No dependencies |
| On failure | Traffic stops going there | The process is killed |

- **Only dependencies without which every request fails belong in readiness.** Include the primary database; exclude the cache, the email provider, a third-party API and anything the app degrades without. The trap is the shared dependency: when it blips, every instance fails readiness at the same moment, the load balancer has no targets, and a partial degradation becomes a total outage.
- **Liveness never checks a dependency.** If it checks the database, a database outage restart-loops every app instance and delays recovery.
- Use an HTTP check, not a TCP check: a deadlocked process still accepts connections.
- The endpoint returns 200 or 503 directly: no auth, no redirect (a redirect to HTTPS or to a canonical host fails many checkers), no rate limit, the right `Host` handling, and a response in milliseconds. Cache the dependency result for a second or two so checks from many proxies do not become load.
- Starting values: interval 5 to 10 s, timeout 2 to 5 s, 2 to 3 failures to mark unhealthy, 2 successes to mark healthy. Detection time is interval × failure threshold; that number is reused in the draining section.
- During startup, readiness fails until the app is warm. During shutdown, readiness fails first, before the listener closes.
- External uptime monitoring is a separate, deeper check from outside (`0x:site-reliability`, `dashboards-alerting.md`); do not point the load balancer at it.

## Which hop produced the 502, 503 or 504

The status code names the failure; the response's shape names the hop that emitted it.

| Code | Emitted by a proxy when | Usual root causes |
|---|---|---|
| 502 | The upstream refused, reset, or answered with something invalid | App crashed or restarting; not listening on the expected address or port; killed mid-request (out of memory); upstream closed an idle keep-alive connection as the proxy reused it; response headers larger than the proxy's buffer; HTTPS sent to a plain-HTTP port |
| 503 | No healthy upstream, or a deliberate refusal | All targets failing health checks; deploy with zero ready instances; connection or concurrency limit reached; maintenance mode |
| 504 | The upstream accepted the request and did not answer within the proxy's timeout | Slow query, lock wait, exhausted connection pool, a slow third-party call; a timeout shorter than legitimate work |

Find the emitter:

1. **Read the response itself.** `curl -sv` and look at the `server` header and the body. A CDN-branded error page, a bare `502 Bad Gateway` page with `nginx` in it, a cloud load balancer's minimal HTML, and the app's own JSON error format are all distinguishable.
   Some CDNs use their own codes in the 52x range to separate "origin refused", "origin timed out connecting", "origin did not answer in time" and "origin TLS failed": look the code up in the CDN's documentation before guessing.
2. **Bypass hops one at a time** with `curl --resolve` or direct addresses: through the CDN, straight to the load balancer, straight to the proxy, straight to the app on its port. The error disappears at the hop below the one causing it.
3. **Follow one request ID through the logs** (the CDN's ray or trace ID, `X-Request-ID`). The hop that has no log line for the request never received it.
4. **Read the proxy's error log**, which states the reason:

| nginx `error.log` | Meaning |
|---|---|
| `connect() failed (111: Connection refused) while connecting to upstream` | Nothing listening: app down or wrong port |
| `upstream prematurely closed connection` | App closed or died mid-request, or the keep-alive race |
| `upstream timed out (110: Connection timed out) while reading response header` | 504: app too slow for `proxy_read_timeout` |
| `no live upstreams` | Every upstream marked failed |
| `upstream sent too big header` | Large cookies or headers: raise `proxy_buffer_size` |

Log `$upstream_addr $upstream_status $request_time $upstream_response_time $upstream_connect_time` in the access log from the start; without them this analysis is guesswork. Status `499` in nginx means the client gave up before the answer, which points at a client or outer-hop timeout shorter than the server's work.

Timing patterns: 502s only during deploys are a draining problem; sporadic 502s at low traffic are the idle keep-alive race (both below); 504s at a suspiciously round duration are a timeout value somewhere.

## A reverse proxy that is correct by default

```nginx
upstream app {
    server 127.0.0.1:3000;
    keepalive 32;
}

server {
    listen 443 ssl;
    http2 on;                      # nginx 1.25.1+; older versions: listen 443 ssl http2;
    server_name example.com;
    client_max_body_size 10m;

    location / {
        proxy_pass http://app;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
        proxy_send_timeout 30s;
    }
}
```

```caddyfile
example.com {
    encode zstd gzip
    reverse_proxy 127.0.0.1:3000
}
```

Caddy obtains certificates, sets the forwarded headers, reuses upstream connections and serves HTTP/3 without further configuration.

What each part prevents:

- **Forwarded headers.** Without `Host` and `X-Forwarded-Proto` the app builds wrong absolute URLs, drops `Secure` cookies and redirects in loops. The app must be told to trust the proxy (`trust proxy` in Express, the framework's equivalent).
  `$proxy_add_x_forwarded_for` appends to whatever arrived; on the outermost, internet-facing proxy overwrite instead (`proxy_set_header X-Forwarded-For $remote_addr;`) so client-supplied values are discarded. Trust rules: `cdn-edge.md`.
- **Body size.** nginx rejects bodies over 1 MB with 413 unless `client_max_body_size` is raised. Set it deliberately per route; do not set it to unlimited.
- **Timeouts.** `proxy_connect_timeout` short (a healthy local upstream connects in milliseconds); read and send timeouts from the budget in the timeout section.
- **Buffering.** Leave `proxy_buffering` on for normal responses: the proxy absorbs slow clients so app workers are freed quickly. Turn it off only for streams.
- **Compression** at exactly one layer: here if no CDN compresses, otherwise at the CDN (`http.md`).
- **Unknown hosts.** Add a default server that refuses requests for names not served (`listen 443 ssl default_server; ssl_reject_handshake on;`), so scanners hitting the IP learn nothing and stray hostnames do not land on the app.
- **Bind the app to loopback** or a private interface so the proxy is the only way in.
- Validate before reloading: `nginx -t && systemctl reload nginx`, or `caddy validate` then `caddy reload`. Reload, never restart, to keep connections.

## Routing by host and path

- **Path or host?** For one product, route by path under one origin (`/api`, `/app`): no CORS, one certificate, shared cookies. Split by host (`api.example.com`) when the backends need different caching, scaling, access rules or cookie isolation, or when one is a third party.
- nginx `location` precedence: an exact match (`=`) wins; otherwise nginx finds the longest matching prefix and uses it at once if it is marked `^~`; otherwise the first regular expression that matches, in file order, wins; only when none matches is that longest prefix used. Prefer prefixes; a stray regex location silently captures paths.
- **The trailing-slash trap.** `location /api/ { proxy_pass http://api; }` forwards `/api/users` unchanged. `proxy_pass http://api/;` (with a URI part) replaces the matched prefix and forwards `/users`. In Caddy, `handle /api/*` keeps the prefix and `handle_path /api/*` strips it. Decide whether the backend expects the prefix and test one deep URL.
- A backend mounted under a prefix must generate links, redirects and cookie paths with that prefix (the framework's base-path setting).
- Cloud load balancer rules are evaluated by priority; put specific rules first and make the default action a fixed 404, not the first backend.
- Avoid sticky sessions. Keep session state in a store so any instance can serve any request; stickiness breaks balance and makes deploys lossy.
- Kubernetes ingress specifics: `0x:cloud-infrastructure`, `kubernetes.md`.

## Draining during deploys

Dropped requests at deploy time come from one race: the process exits while the load balancer still believes it is healthy.

Correct sequence for removing an instance:

1. New instances pass readiness and receive traffic.
2. The old instance is marked for removal: deregistered from the load balancer, or its readiness starts failing.
3. It keeps serving while the load balancer notices (interval × failure threshold, or the deregistration step).
4. It stops accepting new connections, finishes in-flight requests and closes idle keep-alive connections.
5. It exits before the supervisor's kill deadline.

```ts
let ready = true; // the /readyz handler returns 503 when false

process.on('SIGTERM', async () => {
  ready = false;
  await new Promise((r) => setTimeout(r, 10_000)); // window for the load balancer to stop sending
  server.close(() => process.exit(0));             // stop accepting, finish in-flight requests
  server.closeIdleConnections();
  setTimeout(() => process.exit(1), 15_000).unref(); // hard stop: 10 s + 15 s must end before the platform's kill
});
```

- Budget: detection window + longest normal request < the platform's grace period (Docker's stop timeout defaults to 10 s and Kubernetes' termination grace period to 30 s; both are configurable, and PaaS limits vary). The snippet's 25 s total fits a 30 s grace period and not a 10 s one. Raise the grace period or shorten the numbers; never let the platform's SIGKILL do the draining.
- A cloud load balancer's deregistration delay is often minutes by default. For short HTTP requests, 30 s is plenty and makes deploys faster.
- **The signal must reach the app.** In a container, start the server as the main process (`CMD ["node", "server.js"]`); a shell or package-manager wrapper as PID 1 often does not forward SIGTERM, and the process is killed at the deadline with requests in flight.
- Long-lived connections do not drain on their own: close WebSockets and streams deliberately and rely on client reconnect.
- Deploy strategies and rollback: `0x:ci-cd-release`, `deploy-rollback.md`.

Check: run a steady request loop (`while true; do curl -s -o /dev/null -w '%{http_code}\n' https://example.com/readyz; sleep 0.1; done`) through a deploy; any non-200 is a draining bug.

## Timeouts across the chain

Two kinds of timeout, with opposite ordering rules.

**Request timeouts shrink toward the inside.** Each hop gives up slightly after the hop it calls, so the innermost failure surfaces as a meaningful error and nobody keeps working for a caller that has left.

| Hop | Example budget | Setting |
|---|---|---|
| Browser or API client | 35 s | `AbortSignal.timeout` |
| CDN waiting for origin | Fixed or plan-dependent; find the number | Provider setting |
| Load balancer / nginx read timeout | 30 s | `proxy_read_timeout` |
| App request handler | 25 s | Framework or middleware timeout |
| Database statement | 10 s | `statement_timeout` |
| Outbound call to a third party | 1-5 s on the request path (jobs: 10-30 s) | Client timeout on every call |
| Connection pool acquire | 3 s | Pool setting |

The inner three values are owned by `0x:postgres-database` (`transactions-concurrency.md`) and `0x:backend-architecture` (`integrations-resilience.md`).

Work that cannot fit moves to a background job with a 202 and polling (`0x:backend-architecture`, `background-jobs.md`); raising every timeout to accommodate one slow export leaves the whole system unable to shed load.

**Idle (keep-alive) timeouts grow toward the inside.** The side that receives connections must keep idle ones open longer than the side that reuses them, so the reuser is always the one to close. Otherwise the upstream closes a connection at the instant the proxy sends a request on it, and the proxy reports a 502.

- The classic case: a load balancer or nginx upstream pool with a 60 s idle timeout in front of Node.js, whose `server.keepAliveTimeout` defaulted to 5 s for years (Node raised it to 65 s in 2026; which release line first ships that varies, so print it on the pinned runtime).
  Do not depend on the default: log `server.keepAliveTimeout` at startup and set it above the idle timeout in front, for example `server.keepAliveTimeout = 65_000; server.headersTimeout = 66_000;` behind a 60 s proxy (`next start --keepAliveTimeout 65000` for Next.js).
- Apply the same rule to every pair: CDN → load balancer → proxy → app.

**Retries multiply.** Three layers that each retry three times turn one failure into 27 attempts against a struggling backend. Retry at one layer only, with a cap and backoff, and only idempotent requests.

## WebSockets and long-lived streams

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

location /ws {
    proxy_pass http://app;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header Host $host;
    proxy_read_timeout 3600s;
}
```

- **Idle timeouts kill quiet connections at every hop** (CDN, load balancer, proxy, NAT). Send an application heartbeat (WebSocket ping, or an SSE comment line) every 20 to 30 s, below the smallest idle timeout on the path.
- **SSE needs buffering and compression off** for that route: `proxy_buffering off;` or the response header `X-Accel-Buffering: no`, and no compression on `text/event-stream`. Buffered SSE looks like "nothing arrives, then everything at once".
- **Every deploy disconnects everyone.** Clients must reconnect with jittered backoff, or all of them return in the same second, and must resume from a last-seen ID (`Last-Event-ID` for SSE).
- **Balance long-lived connections by least connections.** Round robin leaves a newly added instance nearly empty, because existing connections never move.
- Each connection holds a file descriptor and memory; raise the open-file limit for the proxy and the app (`0x:linux-server`, `processes-systemd.md`) and check the load balancer's connection limits.
- Over HTTP/1.1 a browser allows about six connections per origin, so several SSE streams starve other requests; serve them over HTTP/2 or HTTP/3.
- Protocols that span several HTTP requests before upgrading (long-polling fallbacks) need stickiness or should be configured for WebSocket only.
- Feature design: `0x:backend-architecture`, `realtime.md`.

## Layer 4 or layer 7

| | Layer 7 (HTTP) | Layer 4 (TCP/UDP) |
|---|---|---|
| Sees | Requests: host, path, headers | Connections and bytes |
| Can | Route by host and path, terminate TLS, add headers, retry, cache, apply WAF | Pass anything through at very high throughput, keep TLS end to end, offer static IPs |
| Balances | Per request | Per connection |
| Choose for | Web apps and APIs: the default | Non-HTTP protocols (databases, MQTT, SMTP, game traffic), TLS passthrough when the app needs the client certificate, QUIC passthrough |

Traps of layer 4: one HTTP/2 or gRPC connection carries all of a client's requests to a single backend, so load is uneven and gRPC needs a layer-7 balancer; the client address is lost unless PROXY protocol or source-address preservation is enabled on both ends; there are no forwarded headers; health checks default to TCP and must be switched to HTTP.

## Connection reuse at every hop

A new connection per request costs a handshake each time and, under load, exhausts ephemeral ports. Verify reuse hop by hop:

- **Client to edge:** HTTP/2 and HTTP/3 multiplex on one connection.
- **nginx to upstream:** before nginx 1.29.7 (stable 1.30), reuse requires all three of `keepalive N;` in the `upstream` block, `proxy_http_version 1.1;` and `proxy_set_header Connection "";`; without them nginx speaks HTTP/1.0 to the upstream and opens a connection per request.
  Newer versions keep upstream connections alive by default and the explicit lines stay harmless, so keep them and check `nginx -v` before assuming either behavior. `keepalive` is the number of idle connections kept per worker, not a cap on concurrency.
  With reuse on, the app's keep-alive timeout must exceed nginx's upstream `keepalive_timeout` (60 s by default), per the idle-ordering rule.
- **App to database and to other services:** pooled connections and keep-alive HTTP agents; create clients once per process, not per request.
- **Idle ordering** as in the timeout section, at every pair.

Evidence of reuse: `$upstream_connect_time` logged as `0.000` on most requests; `curl -sv https://example.com/a https://example.com/b` printing a re-use line for the second URL; a low count from `ss -tan state time-wait | wc -l` on the proxy under load.

## Ask the user

- **What is the longest request the product legitimately makes** (uploads, exports, AI responses)? It sets every timeout and decides what becomes a background job. Default: 30 s at the proxy, anything longer is a job or a stream.
- **How large can an upload be?** Sets the body limit, or moves uploads direct to storage. Default: 10 MB through the proxy, larger files direct to object storage.
- **Are a few seconds of errors during a deploy acceptable right now?** Default: at Prototype yes; from Launch, drain properly and verify with a request loop.
- **Does anything hold long-lived connections (chat, live updates, streaming AI output)?** Brings in heartbeats, reconnect logic and platform limits. Default: none assumed; check the plan's connection and duration limits before promising it.
- **One origin with path routing, or separate API hostname?** Affects CORS, cookies and certificates. Default: one origin with paths.
