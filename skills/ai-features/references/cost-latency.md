# Cost, latency and provider resilience

Read this when: an AI feature is too slow or too expensive; setting timeouts, quotas or spend
limits; the feature must survive provider outages, rate limits or a model retirement; or
deciding what to cache, batch or route to a cheaper model.

Prices, rate limits, cache rules and model lifetimes change. Take current values from the
`claude-api` skill and the provider's documentation; the mechanisms below are stable.

## Where time and money go

- **Latency** is roughly: time to first token (queueing plus input processing; grows with input
  size, shrinks with cache hits) plus output tokens divided by the model's generation speed.
  Output length and model tier dominate total time. Reasoning tokens are output tokens.
- **Cost** is input tokens, output tokens (priced several times higher per token than input)
  and, for agents, the same context re-sent at every step. In RAG and agent features input
  volume usually dominates the bill; in drafting features output does.
- An agent run of N steps re-reads its growing history N times, so input cost grows roughly
  with the square of the number of steps. Caching the prefix cuts the price of each re-read;
  only compacting or trimming the history bounds the growth.

Measure before optimizing: from traces, get tokens in, cached tokens, tokens out, time to first
token and total time per call site, at p50 and p95.

## Latency budgets

| Interaction | Target | Design consequence |
|---|---|---|
| Inline autocomplete, as-you-type | Under about 300 to 500 ms total | Smallest model, tiny prompt, debounce, cancel stale requests; often precompute |
| Click a button, get a result in place | First visible output within about 1 s, done in a few seconds | Stream; small or mid model; short output |
| Chat answer | First token within 1 to 2 s; steady stream | Always stream; show retrieval or tool status before tokens arrive |
| Agent task | Acknowledge in under 1 s; progress events every few seconds | Background job with a visible step log (`ai-ux.md`) |
| Batch, enrichment, nightly work | Minutes to hours | Asynchronous batch interface at a discount |

These are rules of thumb for perceived speed; set the product's own from user testing.

Levers, most effective first: stream the response; shorten the output (ask for less, cap
`max_tokens`, return IDs or diffs instead of rewritten text); use a smaller model for the step;
cache the stable prefix; trim input; run independent calls and tool calls in parallel; remove a
model hop (two chained calls cost two first-token waits); precompute. Turning on extended
reasoning moves in the other direction: use it only where evals show it pays.

**Timeouts.** Set three, per call site:

| Timeout | Meaning | Starting point |
|---|---|---|
| First token | Nothing arrived yet | 10 to 15 s interactive, then retry or fall back |
| Idle | Gap between stream chunks | 15 to 30 s, then abort and keep the partial |
| Total | Whole call | From the budget above; long calls belong in a job |

Start the first-token clock at the request and stop it at the first stream event of any kind.
With extended reasoning on, visible text can start many seconds after that event: show a
working state and budget for it instead of timing out a healthy call.

A single total timeout either kills healthy long generations or waits a minute on a dead
connection. Long non-streamed requests are also cut by proxies and platform function limits:
stream, or run as a background job. Pass an abort signal from the client disconnect through to
the provider call so abandoned requests stop generating billable tokens. Check the hosting
platform's maximum function duration against the total budget.

## Metering and quotas

Every model call must be attributable to a user and tenant, and limited, before Launch. One
heavy or abusive account can otherwise erase the margin of a hundred normal ones.

- **Record per call**: tenant, user, feature, model, input, cached and output tokens, computed
  cost, trace ID. Take token counts from the API response's usage data, never from estimates.
  Sum every counter: cache writes and cache reads are reported separately from plain input and
  priced differently (Anthropic's input count excludes them), reasoning tokens bill as output,
  and provider-run tools such as web search carry per-use fees. Write the record even when the
  stream is cancelled or fails partway, from the last usage figures the stream delivered,
  flagged as partial.
- **Check before, settle after.** Before the call, verify remaining allowance and reserve an
  estimate (input tokens plus the output cap); after it, settle to actual usage. A check only
  after the call lets parallel requests overshoot without bound.
- **Limit in cost or tokens**, per period, with separate concurrency and per-minute limits.
  Request counts are the wrong unit: requests differ in size by orders of magnitude.
- **Layers**: per-user, per-tenant, per-feature, and a global daily ceiling with an alert, plus
  the spend limit in the provider account as the last line.
- **At the limit**: say what happened and when it resets, offer the upgrade or top-up, and
  degrade where sensible (smaller model, shorter context) instead of failing. Warn at around
  80% of the allowance.
- **Storage**: a usage table in Postgres is enough to start; a Redis counter in front when the
  check itself becomes hot. Keep the event rows: they feed billing, attribution and disputes.

Charging customers for usage and designing credit packs: `0x:payments-billing`
(`usage-billing.md`) and `0x:pricing-monetization`.

## Cost attribution

Tag every call with feature, tenant, user, model and prompt version, and compute cost at write
time from a price table kept in configuration (prices change; store the computed amount and the
price version). Then answer, weekly:

- Cost per feature, and per successful outcome (per resolved ticket, per accepted draft), not
  only per call.
- Cost per tenant against that tenant's revenue: gross margin per customer. A plan whose top
  decile of users costs more than they pay needs a quota or a price change.
- The distribution, not the mean: usage is heavy-tailed, and the p95 and p99 accounts decide
  the margin.
- Cost per call site over time, by prompt version: a prompt change that doubled input tokens
  shows here before the invoice.

Reconcile the internal total against the provider's bill monthly; a gap means unmetered calls
(evals, background jobs, retries, a forgotten script). Give development, CI and production
separate API keys or workspaces so each line of the bill has an owner.

## Cutting token cost

In order of return for effort:

1. **Prompt caching.** Providers bill a cached prompt prefix at a small fraction of the normal
   input price, and it is processed faster. The cache matches an exact prefix, so structure
   every prompt as stable content first (tool definitions, system prompt, examples, shared
   documents), volatile content last. Anything that varies per request (a timestamp, a user
   name, a request ID, reordered tools) placed early invalidates everything after it. Cache
   entries expire after a short idle time (minutes by default; a longer lifetime may be sold at
   a higher write price) and writes may cost a premium, so caching pays when the same prefix
   recurs within that window. Caches are per model, and a prefix under a minimum token length
   is not cached at all. Verify with the cached-token counts in the usage data: a hit rate near
   zero means the prefix is not stable, too short, or too rarely reused.
2. **Trim the context.** Fewer and better retrieved chunks (rerank, then cut), bounded history
   with summarization, tool results reduced to needed fields, stale tool results dropped, no
   documents "just in case". This often improves quality as well.
3. **Shorten the output.** Ask for the answer without preamble; structured output with short
   field names; return edits or IDs rather than regenerated text; set a real `max_tokens`.
4. **Right-size the model** per call site (routing, below).
5. **Batch the non-urgent.** Work that can wait hours (enrichment, classification backfills,
   evals, nightly summaries) goes through the provider's asynchronous batch interface, which is
   billed at a substantial discount (about half price at the major providers when this was
   written; check). Design for results arriving up to a day later and partially failing.
6. **Do not call.** Deterministic pre-checks (empty input, exact duplicates, known answers),
   response caching and precomputation, below.

Trap: optimizing tokens without the eval set. Every item above can lower quality; gate each
change on an eval run.

## Routing and escalation

| Pattern | How | Use when |
|---|---|---|
| Static per call site | Each step has its model in configuration | Always; this is the default and captures most savings |
| Classify, then route | A small model or rules label the request easy or hard | Request difficulty varies widely and is recognizable up front |
| Cascade | Try the small model; escalate when a check fails | A cheap, reliable check exists: schema validity, a verifier, a retrieval score, a code test |
| Plan big, execute small | Large model writes the plan; small models do the steps | Agent work with many routine steps |

Rules: the escalation signal must be a check in code or a separate grader; a model's stated
confidence is not a reliable signal. A cascade pays twice in latency and cost for every
escalated request, so it wins only when most requests stop at the first tier; compute the
blended cost from measured escalation rates. Changing model mid-conversation discards that
conversation's prompt cache. Evaluate each route separately: the aggregate hides a small model
failing its share.

## Fallbacks for outages and rate limits

| Failure | Response |
|---|---|
| Rate limited (HTTP 429) | Honor the retry-after header; exponential backoff with jitter; queue non-interactive work. Shape traffic with a client-side concurrency limit so bursts do not start |
| Provider overloaded or 5xx (Anthropic signals overload with 529) | Retry two or three times with backoff, then fall back |
| Timeout before first token | One retry, then fall back |
| Stream dies midway | Keep the partial, offer continue or retry; do not silently restart and duplicate side effects |
| Invalid request (4xx other than 429) | Do not retry; it is a bug or an oversized input |
| Content refusal (a stop reason on a successful response, not an HTTP error) | Do not resend the same request to the same model. If the provider documents a fallback model for refusals (Anthropic does; details in `claude-api`), make that one attempt; if it also declines, show the designed state. Track the refusal rate on legitimate traffic: a rising rate is a prompt or scope bug |

Fallback order for interactive features: retry, then a second model from the same provider
(different capacity pool), then the same model family through another platform (a cloud
provider's hosted offering), then a different provider, then graceful degradation: the feature
is disabled with a clear message while the rest of the product works.

- A cross-provider fallback is a second product: its own prompt adjustments, tool-format
  differences, eval run, data-processing agreement and privacy disclosure. Add it at Scale or
  when a contract demands uptime; at Launch, degradation plus a status message is acceptable.
- Check SDK defaults before adding retries: SDK retries multiplied by application retries
  multiplied by queue retries produce a retry storm during an incident. Retry at one layer.
- Put a circuit breaker on the provider: after a run of failures, stop calling for a short
  period and go straight to the fallback (`0x:backend-architecture`,
  `integrations-resilience.md`).
- Keep interactive and background traffic on separate keys or priorities so a batch job cannot
  consume the rate limit that users need. Request limit increases before a launch, not during it.
- Never retry a call that has already triggered tool side effects without idempotency keys.

## Model deprecation

Hosted models are retired on a published schedule. The notice period is set by the provider's
policy and can be as short as about two months, cloud platforms that resell a model set their
own dates, and aliases that track "latest" change behavior without a deploy.

- Pin a dated or explicit version identifier in configuration for each call site. Do not use a
  floating alias in production: behavior should change when the team changes it.
- Keep an inventory: call site, model, prompt version, owner. One grep must find every model ID.
- Subscribe to the provider's deprecation notices and put retirement dates in the calendar.
- Migration sequence: run the full eval set on the new model with the unchanged prompt; read
  the per-case flips; adjust prompts (newer models often need less emphasis and fewer
  workarounds); re-check latency, cost, token counts (tokenizers can differ between
  generations) and rate limits; roll out behind a flag by percentage; keep the old model as
  the rollback until its retirement.
- Re-validate everything coupled to model behavior: output parsers, judge calibration, token
  budgets, caches keyed by model.
- Fine-tuned and self-hosted models do not escape this: base models are retired as well.

## Response caching and precomputation

| Technique | Fits | Trap |
|---|---|---|
| Exact-match response cache: key is a hash of model, prompt version, parameters and full input | Classification, extraction, repeated documents, eval runs, idempotent retries | Key must include tenant and permission scope when the context does |
| Precompute on write: generate when the source changes, store in the database | Summaries, tags, embeddings, suggested replies for content read many times | Invalidate on source change; do not precompute what is rarely read |
| Precompute on a schedule, via batch | Digests, reports, enrichment | Staleness must be acceptable and shown |
| Semantic cache: return a stored answer for a similar question | Public FAQ-style questions with no personalization | Similar is not identical: wrong answers for near-miss questions, and cross-user leakage if personalized content is cached. Skip unless measured and safe |

Cache the expensive intermediate steps too: parsed documents, embeddings by content hash,
retrieval results for a short time, tool results that are safe to reuse. Include the prompt
version and model in every key so a deploy invalidates stale outputs. Do not cache where users
expect variety (regenerate must bypass the cache).

## Ask the user

- **What may one user cost per month on each plan?** Sets quotas and model tier. Default: cap
  model cost at a modest fraction of plan price, with a hard per-user ceiling and an alert.
- **What happens at the limit: block, degrade or charge more?** A pricing decision. Default:
  warn at 80%, then block with a reset time and an upgrade path.
- **How fast must it feel?** Default: streamed, first token within 2 seconds for chat.
- **Is the feature allowed to be unavailable when the provider is down?** Default at Launch:
  yes, with a clear message; multi-provider fallback waits for a contractual need.
- **Which work can wait hours?** Anything that can goes to batch at lower cost. Default:
  enrichment, backfills, digests and evals.
- **What is the monthly spend ceiling at which everything should stop?** Default: set a hard
  limit in the provider account at a level the founder would rather hit than exceed.
