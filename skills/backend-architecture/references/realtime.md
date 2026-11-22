# Realtime features

Read this when: the UI must update without a refresh (job progress, notifications, live
dashboards, chat, presence, typing indicators, shared cursors, collaborative editing, audio or
video calls), or a live feature loses messages, floods the server or fails across instances.

## Choosing the transport

| Transport | Fits | Limits |
|---|---|---|
| Polling every 5-30 s, with a `since` cursor or ETag | Job status, badges, dashboards; anything where a few seconds of delay is invisible | Wasteful below a few seconds; pause when the tab is hidden |
| Server-Sent Events (SSE) | Server-to-client streams: progress, notifications, feeds, LLM output | One direction, text only; needs HTTP/2 or later to avoid the browser's per-origin connection cap |
| WebSocket | Low-latency traffic in both directions: collaborative editing, multiplayer, cursors, high-rate chat | Stateful long-lived connections on a long-running server; reconnect, heartbeat and auth are yours to build |
| WebRTC | Audio, video and screen sharing between participants | A media stack of its own (last section); not a transport for application data |

Rules that settle most cases:

- Start with polling. It works on every host including serverless, survives every proxy and
  needs no new infrastructure. Upgrade when the delay is a product problem, not before.
- Client-to-server messages can stay ordinary HTTP requests. "SSE down, POST up" covers
  notifications, most chat and LLM streaming without a WebSocket.
- Serverless functions end every connection at their duration limit, and many cannot accept a
  WebSocket upgrade at all (some hosts now can; check current documentation). Either way an
  invocation sees only its own connections: use streaming responses with client resume, or a
  hosted realtime service, and never keep room state in the function.
- The live channel is an optimization. The database holds the truth, and every screen must be
  correct after a plain reload.

## Reconnects, missed messages and ordering

Connections drop on deploys, network changes, sleep and proxy idle timeouts. The protocol has to
assume a gap after every connect.

1. **Catch up on connect**: fetch current state over normal HTTP, then apply live events. Or send
   the last seen sequence number and let the server replay from a bounded log (Redis Stream,
   outbox table); if the gap is older than the log, the server answers "resync" and the client
   refetches.
2. **Server-assigned order**: every event carries a sequence that increases per channel or a
   version per entity, assigned at write time. Client clocks never order anything.
3. **Idempotent apply**: the client ignores an event whose ID it has seen or whose version is
   not newer than what it holds.
4. **Client-generated IDs for sends**: a message carries an ID created on the client, so a retry
   after a lost acknowledgment is deduplicated and the echo matches the optimistic entry.
5. **Backoff with jitter on reconnect**: base about 1 s, cap about 30 s, random spread. A deploy
   disconnects every client at once; without jitter they return in the same second and refetch
   together. Reset the backoff only after the connection has stayed up for some seconds.
6. **Heartbeats**: a ping every 20-30 s detects half-open connections and stays under proxy idle
   timeouts (commonly 60 s). Browsers cannot send WebSocket ping frames from script: ping from
   the server, or use an application-level message.

The simplest robust design sends invalidations, not data: `{ type: "project.updated", id,
version }`, and the client refetches through its normal data layer. Ordering, merging and
payload authorization disappear; the cost is one request per event, which only matters at high
rates.

Reconnect promptly on `online` and `visibilitychange`: mobile browsers suspend background tabs
and the socket is dead on return. On the server, watch per-connection send buffers
(`bufferedAmount`): a client that cannot keep up is disconnected, or memory grows until the
process dies.

## Authenticating, authorizing and limiting connections

- **WebSocket handshake**: the browser API cannot set headers. Cookies are sent, and WebSockets
  are not covered by the same-origin policy, so a cookie-authenticated endpoint must check the
  `Origin` header against an allowlist or any site can open a socket as the logged-in user
  (cross-site WebSocket hijacking).
- **Tickets for cross-origin or token-based setups**: the client calls an authenticated HTTP
  endpoint, receives a single-use ticket valid for under a minute, and presents it in the
  connect URL or the first message. Query strings are logged, which is why the ticket must be
  short-lived and single-use, never the session token.
- **Authorize every subscription** on the server against tenant and resource. A channel name is
  not a secret.
- **Connections outlive permissions**: on logout, role change, removal from an organization or
  account suspension, close that user's connections (publish a control message every instance
  acts on), and force periodic re-authentication.
- **Validate every inbound message** with a schema. It is a trust boundary like any request body.
- **Limits**: connections per user and per IP, subscriptions per connection, messages per second
  per connection (token bucket, disconnect on repeat offense), maximum message size (set it; the
  `ws` library's default `maxPayload` is far larger than any chat message needs), idle timeout.
- **SSE**: same-origin cookies work with `EventSource`; for an `Authorization` header use `fetch`
  with a streamed body instead.

## Server-Sent Events

```ts
export async function GET(req: Request) {
  const lastId = req.headers.get('last-event-id');
  const enc = new TextEncoder();
  let cleanup = () => {};
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const send = (id: string, data: unknown) =>
        controller.enqueue(enc.encode(`id: ${id}\ndata: ${JSON.stringify(data)}\n\n`));
      const ping = setInterval(() => controller.enqueue(enc.encode(': ping\n\n')), 20_000);
      const unsubscribe = subscribe(lastId, send); // replays events after lastId, then live
      cleanup = () => { clearInterval(ping); unsubscribe(); };
      req.signal.addEventListener('abort', cleanup);
    },
    cancel() { cleanup(); },
  });
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'X-Accel-Buffering': 'no',
    },
  });
}
```

- An event is `id:`, optional `event:`, one `data:` line per line of payload, then a blank line.
  A line starting with `:` is a comment; use it as the heartbeat.
- `EventSource` reconnects by itself and sends the last received `id` as `Last-Event-ID`. The
  server must replay from there; without `id` lines, every reconnect loses the gap.
- `retry: 5000` sets the client's reconnect delay in milliseconds. `EventSource` reconnects only
  after a dropped connection: a `204`, any other non-200 status or a wrong content type ends it
  for good. One 502 or 503 from the proxy during a deploy therefore kills the stream silently.
  In `onerror`, when `readyState` is `CLOSED`, create a new `EventSource` after a jittered delay.
- Buffering proxies are the usual reason "nothing arrives until the end": disable proxy
  buffering (`X-Accel-Buffering: no` for nginx) and exclude the route from response compression.
- Under HTTP/1.1 a browser allows about six connections per origin across all tabs; a few open
  tabs with one stream each freeze the app. Serve over HTTP/2 or later.
- Clean up on disconnect (the abort signal), or every closed tab leaks a subscription.
- For LLM output use `fetch` with a streamed body: it allows POST and headers. Resuming after a
  drop then needs a server-side buffer keyed by a stream ID (`0x:ai-features`, `ai-ux.md`).

## Presence, typing indicators and cursors

This state is ephemeral: keep it in memory or in Redis keys with a TTL, never in the primary
database, and never replay it after a reconnect.

| Feature | Client sends | Server and receivers |
|---|---|---|
| Presence | Heartbeat every 20-30 s | Key with TTL of two to three heartbeats; broadcast join and leave diffs, not full lists; delay "left" by 5-10 s so a reload does not flicker; count a user once across tabs and devices |
| Typing | "typing" at most every 2-3 s while keys are pressed | Indicator expires about 5 s after the last signal; an explicit "stopped" message is an optimization, not a requirement |
| Cursors, selections | Position throttled to 10-30 per second, in document coordinates | Latest value wins: drop queued updates when behind, interpolate between samples on screen |

- Fan-out in a room is quadratic: 200 people each moving a cursor is 200 x 200 deliveries per
  tick. Cap room size for cursor-level presence; above the cap show a count and the first few
  avatars.
- Put ephemeral traffic on its own channel so a cursor flood cannot delay chat messages.
- Rate-limit these messages on the server; the client throttle is a courtesy, not a control.

## Hosted service or your own

| Situation | Choice |
|---|---|
| Serverless or PaaS without long-lived processes | Hosted (Pusher, Ably, Supabase Realtime, Liveblocks, PartyKit-style edge rooms are examples) |
| Prototype or Launch, live updates and presence, modest volume | Hosted, or SSE from the existing app |
| A long-running server exists and connections are in the low tens of thousands | Own WebSocket or SSE endpoint with Redis pub/sub |
| Custom protocol, strict data-residency, or the hosted bill dominates | Own, or a self-hosted server such as Centrifugo |

- Hosted pricing follows peak concurrent connections and delivered messages. Fan-out is billed
  per delivery: one message to a 1,000-member channel is 1,000 messages. Model the bill with real
  room sizes before committing.
- Keep the provider behind a two-function interface: `publish(channel, event)` on the server and
  a subscription hook on the client, with tokens minted by an endpoint in the app that performs
  the authorization.
- Payloads pass through a third party. Send IDs and let clients fetch sensitive data; list the
  provider as a subprocessor.

## Scaling WebSockets across instances

The connection lives on instance A; the event happens on instance B. Every instance subscribes
to a backplane and forwards to its own connections.

- **Backplane**: Redis Pub/Sub is the default. Postgres `LISTEN/NOTIFY` works at small scale
  (payload limit about 8 kB, needs a direct connection, not a transaction-mode pooler).
- Redis Pub/Sub is at-most-once with no history: an instance that is reconnecting misses
  messages. That is acceptable only because clients resume by sequence; keep the replay log in a
  Redis Stream or a table.
- **Load balancer**: upgrade support enabled, idle timeout longer than the heartbeat interval.
  Sticky sessions are needed only for libraries that fall back to HTTP long-polling (Socket.IO).
- **Deploys**: on shutdown send a close frame (code 1001, going away) so clients reconnect at
  once with jitter instead of waiting for a timeout. Roll instances gradually.
- **Capacity**: the limits are memory per connection and file descriptors (`ulimit -n`), not CPU.
  Set a per-instance connection cap and autoscale on connection count. Heartbeats alone are
  connections divided by interval messages per second.
- Large channels need sharding or a provider; one publish that fans out to 100,000 sockets
  blocks an event loop.

## Collaboration and offline: sync engines and CRDTs

| Need | Approach |
|---|---|
| Several people edit the same records, rarely the same field | Last write wins per field with server ordering, plus presence so people see each other. No CRDT |
| Concurrent editing of the same text or rich document, or offline edits merged later | A CRDT library (Yjs, Automerge) with a maintained sync server or hosted provider. Never a hand-written merge algorithm |
| The whole app should feel instant and work offline over the user's data | A sync engine that replicates a subset of the database to the client (Zero, ElectricSQL, PowerSync, Replicache-style) |

CRDT documents:

- Persist the document as binary updates plus periodic snapshots; compact, because history and
  tombstones grow without bound.
- The server authorizes who may connect to a document, but a connected client can submit any
  update. Keep permissions, billing and other authoritative data out of the shared document.
- Search, APIs and reports need rows: project the document into the database asynchronously.

Sync engines and offline-first:

- Authorization becomes "which rows may this client replicate" and must be enforced by the sync
  layer, not by the UI.
- Mutations queued offline replay hours or days later against changed data. Express them as
  intent ("move card after X", "add 1"), validate them on the server at replay time and let the
  server reject them.
- Old clients hold old schemas: migrations must stay compatible with every client version still
  in the field.
- Adopt one only when instant, offline-capable interaction is the core of the product; the
  tooling is younger than the rest of the stack. Not at Prototype.

## WebRTC

- **Signaling** is application code: peers exchange session descriptions and ICE candidates
  through your server (a WebSocket). WebRTC does not define it.
- **STUN** lets a peer learn its public address; it is cheap. **TURN** relays media when a
  direct path fails (symmetric NAT, corporate firewalls). A meaningful minority of calls need it,
  so a product without TURN fails for those users, typically the ones in offices. TURN carries
  all the media: budget bandwidth, offer TURN over TLS on port 443, and issue short-lived
  credentials from the server; static TURN credentials in client code are an open relay.
- **Topology**: peer-to-peer mesh holds up to about three or four participants, since each peer
  uploads to every other one. Beyond that a selective forwarding unit (SFU) is required.
- **Decision**: use a managed media platform (LiveKit, Daily, Cloudflare Realtime are examples)
  from the first call feature. Self-host an SFU only at Scale with someone to run it.
- What stays with the application: room authorization (the server mints short-lived room tokens
  with identity and grants), recording consent, device-permission and reconnection UX.

## Ask the user

- **How fresh must each live element be: seconds or under a second?** Seconds means polling or
  SSE and no new infrastructure. Assume a few seconds unless people interact with each other
  live.
- **Do several people edit the same content at the same moment, or only see each other's saved
  changes?** Only the first needs a CRDT. Assume saved changes with presence.
- **Must it work offline?** It changes the whole client architecture. Assume no.
- **How many people are in one room or document at peak?** Fan-out cost and presence design
  depend on it. Assume under fifty.
- **May message content pass through a third-party realtime provider?** Sensitive data pushes
  toward ID-only events or self-hosting. Assume IDs only through a hosted provider.
- **Are calls recorded?** Recording needs participants' consent, and who must consent and how
  differs by jurisdiction (`0x:privacy-compliance`), plus storage and retention rules. Assume not.
