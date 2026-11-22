# Feature flags

Read this when: merging unfinished work without exposing it, choosing between a flag service and
a small table, opening a feature to a beta group or a plan, adding a kill switch, rolling out by
percentage, cleaning up old flags, or users report seeing a feature appear and disappear.

## Four kinds of flag, four lifetimes

Most flag mess comes from treating these alike. Decide the kind when the flag is created and put
it in the flag's name or metadata.

| Kind | Purpose | Lifetime | Who flips it |
|---|---|---|---|
| Release | hide unfinished work; roll out gradually | days to a few weeks, then deleted | developer |
| Operational (kill switch, load shedding) | turn a path off in an incident | permanent, documented in a runbook | whoever is on call |
| Experiment | compare variants | until the result is read, then deleted | product owner (`0x:product-analytics`, `experiments.md`) |
| Entitlement | what a plan or customer has paid for | permanent | billing system, not a flag tool |

Entitlements are product data: they belong in the subscription model with billing as the source of
truth (`0x:payments-billing`, `subscriptions.md`). A flag tool may target by plan for a beta, but
"Pro customers get exports" must not live only in a flag dashboard, where a cleanup or a
misclick changes what customers paid for.

## Hide unfinished work behind a flag

A flag replaces the long-lived feature branch: merge small pieces to main daily, off by default.
Branching model: `0x:git-collaboration` (`branching-workflow.md`).

- **One decision point.** Check the flag where the feature is entered (route, navigation item, API
  handler), not in twenty components. Scattered checks are what makes removal expensive.
- **Enforce on the server.** A client-side check hides a button; the endpoint behind it still
  answers and the code still ships in the bundle. Gate the route handler or server action, and
  render the entry point from the same server-side decision.
- **Off means the old behavior, untouched.** Keep the old path working until the flag is removed.
- **Schema changes are not flagged.** Additive migrations ship ahead of the feature, unflagged;
  the flag gates the code that uses them.
- **Test both states** in CI for as long as the flag exists: default off for the suite, plus tests
  that force it on. Force values through a test helper, not by calling the flag service.
- **Cached and static pages** bake in the flag value at render time. Evaluate flags in the dynamic
  part of the page or in middleware (`proxy.ts` in current Next.js), and make sure a cached response is not shared between
  users with different values.

Do not add a flag for a trivial change, a bug fix or a pure refactor; each flag doubles the paths
to reason about. At Prototype a constant or an environment variable is enough, with the cost that
changing it needs a deploy.

## Service or a table

| Situation | Choice |
|---|---|
| Prototype; a handful of on/off flags | environment variable or constant |
| Launch; release flags, a few kill switches, allowlists, simple percentages | a table in Postgres (below), or the flag feature of the analytics tool already installed |
| Non-developers flip flags; experiments with metrics; several services or mobile clients; audit trail needed | a flag service |

When product analytics is already in place, use its flags (PostHog-style) so rollouts and metrics
share one identity. Dedicated services (LaunchDarkly, GrowthBook, Unleash, Flagsmith and others)
add workflow and scale. Wrap whichever is chosen in one module, or use the OpenFeature API, so the
vendor can change without touching call sites. Pricing models differ (seats, monthly users,
requests); check them against expected traffic before committing.

Questions that decide whether a service is safe to depend on:

- **Where is the flag evaluated?** Server SDKs that download the rules and evaluate in process add
  no latency per check and keep working from the last known rules. A network call per evaluation
  adds latency to every request and makes the flag vendor a dependency of every page.
- **What happens when it is unreachable?** Every call site passes a default, and that default is
  the safe state. Serverless functions initialize the SDK on each cold start; bound that with a
  short timeout and fall back to defaults.
- **How fast does a change propagate?** Polling interval or streaming. This bounds how fast a kill
  switch works.

Minimal table-backed implementation:

```sql
CREATE TABLE feature_flags (
  key             text PRIMARY KEY,
  kind            text NOT NULL CHECK (kind IN ('release', 'ops')),
  enabled         boolean NOT NULL DEFAULT false,      -- master switch
  rollout_percent integer NOT NULL DEFAULT 0 CHECK (rollout_percent BETWEEN 0 AND 100),
  allow_ids       text[] NOT NULL DEFAULT '{}',        -- account or user IDs always on
  owner           text NOT NULL,
  expires_on      date,                                -- required for release flags
  updated_at      timestamptz NOT NULL DEFAULT now()
);
```

```ts
import { createHash } from 'node:crypto';

function bucket(flagKey: string, unitId: string): number {       // 0..9999, stable
  return createHash('sha256').update(`${flagKey}:${unitId}`).digest().readUInt32BE(0) % 10_000;
}

export function isEnabled(flag: Flag | undefined, unitId: string, fallback = false): boolean {
  if (!flag) return fallback;                    // unknown or unloaded flag: the caller's default
  if (!flag.enabled) return false;
  if (flag.allowIds.includes(unitId)) return true;
  return bucket(flag.key, unitId) < flag.rolloutPercent * 100;
}
```

Load all flags into process memory and refresh on a short interval (15 to 30 seconds is a workable
rule of thumb; it bounds how fast a kill switch acts); on a refresh error keep the last good copy.
On serverless there is no long-lived timer: load on cold start and re-read when the copy is older
than the interval. Do not query per check. Hashing the flag key with the ID gives each flag its own
ordering of users, so the same accounts are not first in every rollout, and raising the percentage
only adds users. Record every change (who, when, old and new value): an audit table or the
service's log. A flag flip changes production like a deploy does and belongs on the same timeline.

## Targeting

Choose the unit before the rule:

| Unit | Use for |
|---|---|
| Account (organization, workspace) | B2B products: everyone in a company must see the same thing. The default for anything collaborative. |
| User | consumer products; personal settings and UI |
| Anonymous or device ID | logged-out pages; flips at login unless carried over (see consistency) |

Evaluate rules in a fixed order and stop at the first match: master switch off → explicit deny
list → explicit allow list → segment (staff, beta opt-in, plan, region) → percentage → default.

Staged access that works for a small product: staff only in production (the cheapest staging
there is), then named design partners by account ID, then accounts that opted into a beta setting,
then a percentage, then everyone. Store beta opt-in in the product's own database, not only in the
flag tool. Send the flag service IDs and coarse attributes (plan, signup date), not emails or
names; it is a third-party processor like any other (`0x:privacy-compliance`, `vendors-dpas.md`).

## Kill switches

Put a kill switch on changes whose failure is expensive and whose rollback is slow or impossible:
a rewritten checkout or billing path, a new third-party integration, anything with per-call cost
(LLM calls, SMS), a new background job that touches many rows, a heavy query on a hot page.

- The switch selects between the new path and a path known to work: the old code, a degraded
  response, or a clear "temporarily unavailable". Decide which before shipping.
- When the flag system is unreachable, the default is the safe path.
- It takes effect within about a minute, without a deploy. Know the propagation time.
- Jobs and loops check it per iteration or per batch, not once at start, or a runaway job cannot
  be stopped.
- Flip it once in production before depending on it. An untested switch often guards half the
  code path.
- List it in the runbook: name, what turns off, what users see, who may flip it
  (`0x:site-reliability`, `postmortems-runbooks.md`).
- Name flags for the enabled state (`new_checkout_enabled`); negated names (`disable_x = false`)
  get flipped the wrong way under stress.

A kill switch stops new damage. It does not repair data the new path already wrote; design the old
path to tolerate rows created by the new one.

## Percentage rollouts with guardrails

A typical schedule: staff → 5% → 25% → 50% → 100%. Hold each step long enough to cover real use of
the feature: at least an hour or two for request-level risk, a full day when usage follows a daily
pattern, through a billing or weekly cycle when the feature depends on one.

Before starting, write down the guardrails and the number at which the rollout returns to 0:

- Technical: error rate and p95 latency for requests with the flag on versus off, new error types.
- Product: the conversion or completion step the feature sits in, support contacts.

To compare, attach flag state to telemetry: a tag on error-tracker events and a property on
analytics events. Without it, a 5% cohort's errors disappear in the total.

Limits at small scale: 5% of 400 accounts is 20 accounts. That detects crashes and exceptions, not
a conversion difference. Use the rollout to find breakage and do not read product conclusions from
it; proper experiment design is `0x:product-analytics` (`experiments.md`).

Rules that keep a rollout from confusing users: assignment is sticky; raising the percentage only
adds; lowering it removes the most recently added; do not change the hashing salt mid-rollout. For
features that create data (a new editor, a new document type), turning the flag off leaves that
data behind: the off state must still display or preserve it.

## Removing stale flags

A release flag at 100% is dead code with a remote control. Process that keeps the count down:

1. At creation: owner, kind and an expiry date. Removal is part of the feature's definition of
   done, tracked as a task created together with the flag.
2. When the flag has been at 100% (or 0%, abandoned) for one to two weeks: delete the losing code
   path, the check, and its tests.
3. Order matters: remove the code references and deploy, then delete the flag from the table or
   service. Deleting the flag first makes running code fall back to its default, which for a
   launched feature is usually "off".
4. Keep the working set small. Rule of thumb for a solo founder: at most 5 to 10 release flags
   alive at once; past that, clean up before adding.

Make staleness visible mechanically: define all keys in one typed registry so that deleting a key
makes the compiler list every reference, and add a CI check that fails when a release flag is past
its expiry date. Flag services also report flags that have returned one value to everyone for
weeks.

Two traps. Do not reuse a retired key for a new purpose: an old binary, mobile app or forgotten
service still holding the old meaning will act on it. And do not make flags depend on other flags;
nested conditions produce states nobody tested.

## Consistent evaluation

A user who sees a feature on one request and not on the next files a bug report. Sources of
inconsistency and the fix:

| Source | Fix |
|---|---|
| Evaluated separately in several places within one request | evaluate once at the start of the request, pass the result down |
| Several services each evaluating | evaluate at the edge or first service and propagate the decisions (header, context, job payload); or identical SDK, rules and unit ID everywhere |
| Server render and client disagree (flicker, hydration mismatch) | the server evaluates and sends the values as bootstrap data; the client does not re-fetch before first paint |
| Anonymous ID before login, user ID after | carry the anonymous assignment into the account at signup, or restrict the rollout to logged-in users |
| Different devices | bucket on user or account ID, never on a device cookie, for logged-in features |
| Percentage changed during a multi-step flow (checkout, onboarding) | read the flag at the first step and store the result with the flow |
| Background job runs after the flag changed | snapshot the decision into the job payload for user-visible behavior; re-evaluate at run time for kill switches |
| CDN or page cache | vary the cache key on the variant, or keep flagged content out of shared caches |
| Instances refresh rules at different moments | accept a short window, or use a streaming SDK; never rely on instant global consistency |

The job-payload row holds the general rule: experience flags are snapshotted so a flow stays
coherent, operational flags are always read fresh so they act immediately.

## Operational flags for shedding load

Prepare the levers before the incident, ranked by how little users miss them: for example
recommendations and activity feeds, search-as-you-type, exports and heavy reports, LLM-backed
features, non-essential background jobs, live-update polling frequency, then signups or writes as
a last resort (read-only mode).

- Each lever is a permanent operational flag with a tested degraded state: the page renders
  without the widget, the export button says when it will be back.
- Record for each one roughly how much load it removes and what the user sees, in the runbook.
- The flag read must not depend on what is overloaded. Table-backed flags live in the database
  that is probably the one struggling: serve from the in-memory copy, keep it on refresh failure,
  and keep an environment-variable override as the last-resort path.
- Start with manual flips. Automatic shedding (a flag driven by queue depth or latency) comes
  after the manual lever has been used and understood; an automatic lever with a wrong threshold
  creates its own outages.
- Exercise each lever a few times a year in production at a quiet moment.

Related mechanisms: rate limits and circuit breakers per dependency (`0x:backend-architecture`,
`integrations-resilience.md`), capacity planning (`0x:site-reliability`, `capacity-scaling.md`).

## Ask the user

- **Who needs to turn features on and off: only developers, or also non-technical teammates?**
  Decides table versus service. Default: developers only, table or the analytics tool's flags.
- **Is the product sold to companies or to individuals?** Decides the targeting unit. Default:
  account for B2B, user for consumer.
- **Which features may be switched off under load or in an incident, and in what order?** A
  business choice about what customers tolerate. Default: non-core, costly features first; never
  login, billing or core reads.
- **Are there customers who must get, or must not get, early features** (design partners,
  enterprise accounts with change-control terms)? Default: staff first, then opt-in beta accounts;
  contract customers last.
- **Is a paid capability being gated?** Then it is an entitlement, not a flag. Default: plan
  limits live in the billing model.
