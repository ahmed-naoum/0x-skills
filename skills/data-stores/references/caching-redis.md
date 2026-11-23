# Application caching with Redis

Read this when: adding, debugging or removing an application-level cache, or using Redis or
Valkey for counters, locks and rate limits. HTTP and CDN caching is `0x:web-networking`; try it
first, because a response served by the CDN never reaches the application at all.

## Before adding a cache

A cache hides a slow read; it does not fix it, and it adds a consistency problem that lasts as
long as the cache does. Work down this list and stop at the first step that meets the target.

1. Read the query plan. A missing index or an N+1 pattern is the usual cause (`0x:postgres-database`).
2. Precompute in Postgres: a summary table or a materialized view.
3. Cache at the HTTP layer for responses that are the same for many users.
4. Memoize within one request (the same lookup repeated in one render).
5. In-process memory cache for small, slow-changing data (feature configuration, plan
   definitions) with a TTL of seconds to a minute. Each instance holds its own copy, so
   instances disagree for up to one TTL.
6. Redis, when the value is expensive, read far more often than written, shared by all instances,
   and allowed to be stale.

Frameworks with a built-in data cache (Next.js) follow the same rules below; the mechanics are in
`0x:react-nextjs`.

## What must never be cached

The rule: **cache what is displayed, not what is decided.** A stale value on screen is a
cosmetic bug. A stale value used to authorize, charge or grant is a financial or security bug.

| Never serve from cache when deciding | Why | Do instead |
|---|---|---|
| Account balance, credits, wallet | Stale read permits double spend | Read and update in one database transaction with a row lock or a conditional `UPDATE` |
| Entitlements and plan limits at enforcement | A downgraded or cancelled customer keeps access; an upgraded one is blocked after paying | Read from the database; if it must be cached, invalidate on every billing webhook and keep TTL under a minute |
| Payment and order state | "Paid" shown or acted on before or after it is true | Database, updated by verified provider webhooks |
| Authorization decisions, roles, membership | A removed member keeps access for the TTL | Database read per request, or a short TTL plus explicit invalidation on change |
| Inventory at checkout | Overselling | Conditional decrement in the database |
| One-time tokens, password-reset and verification state | Replay | Database with atomic consume |

Two further invariants. A cache key for per-user or per-tenant data contains the user or tenant
ID; a shared key for personalized data leaks one customer's data to another, and that is the
most damaging cache bug there is. And responses containing personal data are not placed in a
shared HTTP cache at all.

## Pattern choice

| Pattern | How it works | Use when | Trap |
|---|---|---|---|
| **Cache-aside** (default) | Read: get from cache; on miss, load from the database, set with TTL. Write: update the database, then delete the key. | Almost always | The refill race below |
| **Read-through** | The same, hidden inside a wrapper such as `cached(key, ttl, loader)` | Many call sites; gives one place for metrics, stampede protection and versioning | Call sites forget it is a cache and use it for decisions |
| **Write-through** | The write path updates the database and sets the new value in the cache | The value is read immediately after nearly every write and is costly to recompute | Two concurrent writers can set the cache in the opposite order from the database commits; the cache then holds the older value until TTL |
| **Write-behind** | Write to the cache, flush to the database later | Lossy aggregates only (view counts) | The cache becomes the source of truth; a restart loses data. Not for anything that matters. |
| **Refresh-ahead** | A job recomputes hot keys before they expire | A small known set of expensive keys (home feed, pricing table) | Recomputes keys nobody reads |

Rules that make cache-aside correct enough:

- **Delete on write, do not set.** Deleting is idempotent and order-independent; setting is not.
- **Invalidate after the transaction commits**, never inside it. A delete before commit lets a
  concurrent reader refill the key with the old row.
- **Every key has a TTL**, even with explicit invalidation. Invalidation code has gaps (a script
  that edits the table, a new write path, a failed delete); the TTL bounds the damage. Pick the
  TTL by asking how long a wrong value may be shown, not how long the data usually stays valid.
- **The refill race:** a reader misses and loads the old row; a writer commits and deletes the
  key; the reader then sets the old value. The window is small and the TTL closes it. Where that
  is not acceptable, the data belongs in the never-cache table.
- **Replica lag:** if the loader reads from a replica, a refill right after invalidation can
  re-cache the pre-write row. Load cache refills from the primary, or delete the key a second
  time after a delay longer than the replica lag.
- Cache negative results (not found) with a short TTL, or repeated lookups of missing IDs
  bypass the cache entirely.
- Treat every cache error as a miss. Set a short command timeout (tens of milliseconds on the
  same network) so a slow Redis does not become a slow product.

## Keys and versions

```text
<app>:<env>:<entity>:v<schema>:<tenant>:<id>[:<variant>]
myapp:prod:project-summary:v3:t_812:p_4471:en
```

- **Schema version in the key.** During a rolling deploy, old and new code run together. If both
  read one key, one of them reads a shape it does not understand. With the version in the key,
  each reads and writes its own, and the old keys expire. Bump the version in the same commit
  that changes the cached shape.
- **Validate on read.** Parse cached values with the same schema validator used at other trust
  boundaries and treat a failed parse as a miss. JSON loses `Date`, `BigInt`, `Map` and
  `undefined`; a value typed as `Date` comes back as a string unless the parse step restores it.
- **Environment in the key or a separate instance per environment.** Staging sharing production
  keys is a real incident pattern.
- **Hash long or user-supplied parts** (search parameters) into a digest, after normalizing
  order and case, so equivalent requests share a key.
- **Group invalidation by namespace version**, not by pattern delete. Store a counter such as
  `myapp:prod:project-ver:t_812`, include its value in dependent keys, and `INCR` it to
  invalidate everything for that tenant at once. `KEYS pattern` blocks the server while it walks
  the whole keyspace; never run it in production. `SCAN` is the non-blocking tool for inspection.
- **Keep values small.** Redis executes commands on one thread, so reading or deleting a value
  of several megabytes stalls every other client. Rule of thumb: under about 100 kB per value;
  cache IDs or pages, not whole collections. Delete large keys with `UNLINK`.

## Stampedes

When a hot key expires, every concurrent request misses and runs the expensive loader at once,
which can take down the database the cache was protecting. Defenses, cheapest first:

1. **TTL jitter.** Add a random 10 to 20 percent to each TTL so keys written together do not
   expire together (after a deploy or a cache flush).
2. **Single flight per process.** Keep a map of in-flight loader promises by key; concurrent
   callers in one instance await the same promise.
3. **Serve stale while revalidating.** Store `{ value, freshUntil }` with a physical TTL well
   beyond `freshUntil`. After `freshUntil`, one caller takes a short lock and recomputes; all
   others return the stale value immediately. This is the default for expensive hot keys.
4. **Refill lock.** `SET lock:<key> <token> NX PX 10000` before loading; callers that lose the
   lock wait briefly and re-read, or serve stale. The lock TTL must exceed the loader's worst case.
5. **Refresh-ahead** for the handful of keys whose miss is unaffordable.

A cold start is a stampede on every key. After a flush, a failover to an empty replica or a
version bump of a hot key family, expect database load at uncached levels; make sure the database
survives that, or warm the critical keys before shifting traffic.

## Memory, eviction and persistence

- **Set `maxmemory`** (managed plans set it by tier). The default eviction policy is
  `noeviction`: when memory is full, writes fail with an out-of-memory error.
- **Pure cache:** `allkeys-lru` or `allkeys-lfu`. Redis then drops the least useful keys under
  pressure, which is the desired behavior.
- **Queues, locks, rate-limit state, sessions:** `noeviction`. An evicted job or lock is data
  loss. BullMQ requires this policy.
- **Therefore do not share one instance between a cache and a job queue.** The two need opposite
  eviction policies, and a cache surge must not be able to fail job writes. Two small instances
  beat one large one. If they must share, `volatile-lru` evicts only keys with a TTL, which
  holds only as long as every cache key has a TTL and no queue key does.
- **Sizing:** sample real values with `MEMORY USAGE <key>`, multiply by the expected key count,
  and leave headroom for per-key overhead, fragmentation and replication buffers; plan for peak
  use around two thirds of the limit (rule of thumb). Watch `used_memory`, `evicted_keys` and
  `mem_fragmentation_ratio` in `INFO`.
- **Persistence:** a pure cache needs none; loss means a cold start. State whose loss hurts
  (rate-limit counters, queues, sessions) wants append-only-file persistence with per-second
  fsync, which still loses up to about a second on a crash. Replication is asynchronous, so a
  failover can drop acknowledged writes. This is why Redis is never the only copy of anything
  that matters.
- **Redis or Valkey:** Valkey is the open-source fork created after Redis changed its license
  in 2024, and several cloud providers offer it as their managed option. For caching, counters
  and locks the commands used here are the same on both; choose by what the host offers and
  what the client library supports.
- **Serverless and edge runtimes** open a connection per invocation and exhaust the connection
  limit. Use a provider with an HTTP API or a pooled client there, and reuse the client across
  invocations where the runtime allows.

## Counters, locks and rate limits

Redis is the right tool for these because the operations are atomic and fast. It is still not the
record: assume any of this state can vanish, and design so that loss is tolerable.

**Counters.** `INCR` is atomic. The bug is the expiry: `INCR` followed by a separate `EXPIRE`
leaves an immortal key if the process dies between the two. Set the expiry atomically:

```text
SET rl:login:203.0.113.7 0 EX 60 NX
INCR rl:login:203.0.113.7
```

Send both in one `MULTI` transaction or a Lua script. Counters whose total matters (billable
usage, quota consumed) are written to Postgres; Redis may hold a fast approximate copy for
display or pre-checks, reconciled from the database.

**Rate limits.**

| Algorithm | Behavior | Use |
|---|---|---|
| Fixed window | Allows up to twice the limit across a window boundary | Coarse abuse limits |
| Sliding window counter | Weighted blend of current and previous window; smooth, two keys | Default for API limits |
| Token bucket | Steady rate plus a bounded burst; needs a script for atomicity | Public APIs with burst allowance |

Use a maintained library rather than hand-written scripts. Decide the failure mode explicitly:
when Redis is unreachable, general API limits fail open (availability wins), while limits that
guard login, password reset, signup and expensive or paid operations fail closed or fall back
to a stricter in-process limit. Policy for what to limit belongs to `0x:auth-identity` (abuse
defense) and `0x:api-design`.

**Locks.** Acquire with a random token and a TTL; release only if the token still matches:

```text
SET lock:invoice-run:2026-11 9f3c1e... NX PX 30000
```

```lua
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
else
  return 0
end
```

A plain `DEL` on release deletes a lock that expired and was re-acquired by someone else. More
important: a Redis lock is an efficiency device that usually prevents duplicate work. It cannot
guarantee mutual exclusion, because the holder can pause (garbage collection, a slow network
call) past the TTL and continue while a second holder runs. Multi-node algorithms such as
Redlock do not remove that problem. Where two holders would corrupt data or charge twice,
correctness comes from the database: a unique constraint, a conditional `UPDATE ... WHERE
status = 'pending'`, `SELECT ... FOR UPDATE`, or an idempotency key. See
`0x:backend-architecture` for consistency under concurrency.

## Prove the cache earns its place

- Record p50 and p95 latency of the endpoint and database load before adding the cache. Without
  a baseline there is no evidence for keeping it.
- Emit hit, miss, error and load-duration metrics per key family from the wrapper. The
  server-wide ratio from `keyspace_hits` and `keyspace_misses` in `INFO stats` mixes every use
  of the instance and hides a useless cache behind a good one.
- Reading the numbers (rules of thumb): a hit rate under about 80 percent on a read meant to be
  hot means the key is too specific, the TTL too short or the data not actually hot. A high hit
  rate with no change in p95 means the read was not the bottleneck.
- Keep a kill switch: an environment flag that makes the wrapper call the loader directly. It is
  the fastest way to settle "is this a caching bug" during an incident.
- Test with Redis stopped. The application must serve requests, slower.
- Remove a cache that does not move latency or database load. Every cache left in place is a
  staleness bug waiting for a new write path.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| User edits, then sees old data | Invalidation missing on one write path, or refill from a lagging replica | One write module that owns invalidation; refill from primary; TTL as backstop |
| Errors or crashes right after a deploy | New code reading old cached shape | Version in key; parse on read |
| One customer sees another's data | Key lacks tenant or user ID, or personalized response cached in a shared layer | Fix the key; flush; treat as a security incident |
| Database load spikes on the minute | Synchronized expiry, stampede | Jitter; stale-while-revalidate |
| Writes fail with out-of-memory errors | `noeviction` with a full instance | Correct policy for the workload; TTL on every cache key; separate instances |
| Jobs disappear | Queue shares an evicting cache instance | Separate instance with `noeviction` |
| Latency spikes across all commands | Large values, `KEYS`, long Lua scripts on the single thread | Smaller values, `SCAN`, `UNLINK`; check the slow log |
| Connection errors under load | Per-request clients, serverless fan-out | One shared client per process; HTTP-based or pooled access |

## Ask the user

- **How stale may this data be shown, in seconds?** This sets the TTL and whether explicit
  invalidation is needed. Default: 60 seconds for shared, non-critical data; no caching for
  anything in the never-cache table.
- **If the rate limiter's store is down, block or allow?** Default: allow general traffic,
  block authentication and paid operations.
- **Is losing counters or sessions on a Redis failure acceptable?** If not, that state belongs
  in Postgres. Default: Redis holds only what can be lost.
- **What is the monthly budget for the cache?** Memory is the price driver; a smaller instance
  with the right eviction policy often serves as well as a large one.
