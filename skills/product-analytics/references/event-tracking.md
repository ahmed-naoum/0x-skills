# Event taxonomy and tracking

Read this when: choosing an analytics tool, writing or changing the tracking plan, wiring
`identify` and group calls, moving events server-side, or working out why a number is wrong
because tracking broke.

## Start from questions, not events

Write the five to ten questions the founder needs answered this quarter (where signups drop,
who activates, who retains, which channel pays), then list the events those questions need. A
tracking plan built by "track everything" produces hundreds of events nobody trusts; autocapture
is a safety net for retroactive questions, not the plan.

Stage sizing, as a rule of thumb:

| Stage | Custom events | What they are |
|---|---|---|
| Prototype | 5–10 | signup, the one or two core value actions, the activation milestone |
| Launch | 15–30 | plus full signup-to-paid funnel steps, billing lifecycle, invites, key features |
| Scale | 50–150, governed | per-feature events with owners; anything unqueried for 6 months is removed |

## Naming and property rules

Pick one convention and enforce it in code; mixed conventions are the main reason a tracking
plan dies. If the project already has one, keep it. Greenfield default:

- **Event name**: `object_action`, snake_case, past tense, product language:
  `project_created`, `invite_sent`, `subscription_started`. Past tense because an event records
  something that happened, not an intent.
- **No variable data in names.** `button_clicked` with `button: "export_csv"` is wrong in the
  other direction too: name the user's action (`report_exported` with `format: "csv"`), not the
  UI element. UI names change with every redesign; actions survive.
- **One event per action, variants as properties.** `report_exported {format}` not
  `csv_exported` + `pdf_exported`. The test: would the two ever be summed in one chart? Then
  they are one event.
- **Attempt vs success.** Client events describe attempts (`checkout_started`); the success
  event is emitted where the outcome is known (`subscription_started`, server-side). Never fire
  a success event from a button's click handler.
- **Properties**: snake_case, stable types (never a string in one place and a number in
  another), IDs as strings, money as integer minor units plus `currency`, timestamps ISO 8601
  UTC, booleans prefixed `is_`/`has_`. Enumerations are a closed list in code.
- **Context on every event**: `account_id`, `plan`, `role`, `platform`
  (`web`/`ios`/`api`), `app_version`. Set them once as super properties or in the wrapper.
  Missing `plan` at event time cannot be reconstructed later, because the person property holds
  only the current plan.
- **Event properties vs person properties**: an event property is the value at the time of the
  event; a person property is the latest value. Segmenting historical funnels by a person
  property silently uses today's value unless the tool stores person properties per event.

The tracking plan is a table kept in the repository next to the code that emits it:

| Event | Trigger (exact) | Source | Properties | Owner | Question it answers |
|---|---|---|---|---|---|
| `signed_up` | user row committed | server | `method`, `initial_utm_source` | founder | funnel top |
| `project_created` | project row committed | server | `project_id`, `template` | founder | activation step 1 |
| `subscription_started` | payment provider webhook, first successful payment | server | `plan`, `interval`, `mrr_minor`, `currency` | founder | paid conversion |

"Trigger (exact)" is the column that prevents two definitions of the same event.

## Choosing the tool

| Situation | Choice | Why |
|---|---|---|
| Prototype or Launch, one product, no data person | A product suite (PostHog-style: events, funnels, retention, replay, flags, experiments in one) | One SDK, one identity model, experiments read the same events as the funnels |
| Content or marketing site only, no logged-in product | A cookieless page-analytics tool (Plausible-style) | Fewer consent problems, answers "which pages and sources"; cannot do per-user funnels |
| Events must join billing, CRM and support data; or analytics SQL is already the habit | Warehouse-first: events land in a warehouse, BI on top | Any join is possible; cost is modeling work and slower answers to simple funnel questions |
| Scale, a suite already in place | Both: suite for self-serve product questions, warehouse export for finance-grade and cross-system numbers | The suite's batch export feeds the warehouse; revenue truth stays in the warehouse |
| Google Ads is the main channel | Add GA4 only as the ads-side measurement, not the product analytics tool | GA4's model suits ad audiences, not account-level product questions |

Decision rules that matter more than the vendor:

- Choose a tool with **group (account) analytics** if the product is B2B. Per-user funnels on a
  B2B product answer the wrong question.
- Check that raw events can be **exported** in bulk. Without export, switching tools later
  means losing history.
- Pricing is per event or per tracked user and changes often: check current pricing against the
  expected event volume, and note that session replay and autocapture multiply volume.
- Do not run two product-analytics SDKs "to compare". They never agree and the reconciliation
  consumes weeks. Warehouse pipelines belong to `0x:data-stores`.

## Server-side for facts

An event is a fact when the server or a payment provider is the authority on whether it
happened. Emit those server-side, in the same code path that commits the state change:
`signed_up`, the activation milestone, `subscription_started`, `subscription_canceled`,
`payment_failed`, `invite_accepted`, anything that feeds revenue or a board number.

Why: ad blockers and privacy browsers drop a meaningful share of client events (the share
varies widely by audience and is highest for developer audiences), tabs close before a request
is sent, and client events can be forged or double-fired by retries. Client-side stays right
for what only the browser knows: page views, UI interactions, funnel steps before signup.

```ts
// Server: emit after the transaction commits, with the same distinct ID the client uses.
import { PostHog } from "posthog-node";
const posthog = new PostHog(process.env.POSTHOG_KEY!, { host: process.env.POSTHOG_HOST });

posthog.capture({
  distinctId: user.id,
  event: "subscription_started",
  properties: { plan: "pro", interval: "month", mrr_minor: 2900, currency: "usd" },
  groups: { company: account.id },
});
await posthog.shutdown(); // serverless: flush before the function freezes
```

Traps:

- **Serverless drops events** unless the client is flushed before the handler returns. On
  long-lived servers create one client and flush on shutdown instead.
- **Webhook retries double-count.** Emit from the idempotent branch of the webhook handler
  (after the "already processed this event ID" check), not at the top.
- **Emit after commit.** An event sent inside a transaction that rolls back is a phantom.
  At Scale, write events to an outbox table and send from a job.
- **Analytics must not break the request.** Wrap sends so a vendor outage degrades tracking,
  not checkout.
- **Revenue numbers in analytics are for segmentation, not accounting.** The payment provider
  and ledger remain the source for MRR (`0x:startup-finance`, `0x:payments-billing`).
- To reduce client loss, serve the SDK and ingestion through a reverse proxy on the product's
  own domain, following the vendor's proxy guide. Avoid paths such as `/analytics` or `/track`
  that blocklists match. This does not remove the need for consent.

## Identity: anonymous, user, account

Three IDs, each with one job:

| ID | Set when | Rule |
|---|---|---|
| Anonymous ID | first page view, generated by the SDK | lives in first-party storage on that device |
| User ID | signup or login | the database primary key; never email (it changes and is personal data) |
| Account/group ID | when the user acts within a workspace | attached to every event of a B2B product |

Sequence that gets it right:

1. Before login, the SDK tracks under the anonymous ID.
2. On signup and on every login, call `identify(user.id)` on the client. The tool links the
   anonymous history on that device to the user, so pre-signup page views join the funnel.
3. Server-side events use the same `user.id` as `distinctId`.
4. On logout call `reset()`. Without it, the next person on a shared browser inherits the
   previous identity and the two users are merged, which is usually irreversible.
5. Call `group("company", account.id)` after login and whenever the active workspace changes.

```ts
posthog.identify(user.id, { plan: account.plan }, { first_seen_app_version: version });
posthog.group("company", account.id, { name: account.name, plan: account.plan });
// logout:
posthog.reset();
```

Traps: identifying with a placeholder such as `"null"`, `"undefined"` or `"anonymous"` merges
every such user into one person; guard the call. A server event emitted before the client ever
called `identify` (for example signup through OAuth callback) is attributed correctly only if
it uses the final user ID; pass the client's anonymous ID to the server at signup when the
pre-signup journey must be linked from the server side. Cross-device history joins only after
login on each device; anonymous visits on a device that never logs in stay separate, and no
compliant technique fixes that.

## Consent and data minimization

The legal rules belong to `0x:privacy-compliance` (`consent-cookies.md`); the instrumentation
must make whatever the banner says true.

- **Gate on the consent state, not on the banner being shown.** Initialize the SDK in a
  no-storage or opted-out mode and switch on only after an opt-in where opt-in is required.
  Check the tool's current options for cookieless or memory-only operation.
- **Server-side events are still personal data.** Moving tracking to the server does not
  bypass consent or the user's opt-out; carry the consent flag on the user record and honor it
  in the server wrapper.
- **Send IDs, not identity.** No emails, names, phone numbers, free-text fields, search
  queries, or full URLs with tokens in properties. Scrub query strings in page URLs
  (`?token=`, `?email=`, reset links).
- **Session replay**: mask all inputs by default and block elements showing customer data;
  replay of a B2B customer's data is their data, and enterprise buyers ask about it.
- **Minimize person profiles.** Create identified profiles only for logged-in users; keep
  marketing-site traffic anonymous and aggregate.
- **Deletion must reach the vendor.** The account-deletion job calls the analytics tool's
  person-deletion API; add it to the data-subject-request runbook.
- **Region and DPA**: pick the vendor's EU region for EU customers at project creation
  (migrating regions later is painful) and sign the DPA.
- Exclude internal users, test accounts and impersonation sessions by a property
  (`is_internal: true`) set at identify time, and filter it in every saved insight. Separate
  projects (keys) for development, staging and production.

## Validate events so tracking does not silently break

Tracking has no user-visible failure, so it rots unless types and tests guard it. Put every
call behind one typed wrapper; forbid direct SDK calls with a lint rule.

```ts
import { z } from "zod";

export const events = {
  project_created: z.object({ project_id: z.string(), template: z.string().nullable() }),
  subscription_started: z.object({
    plan: z.enum(["pro", "team"]),
    interval: z.enum(["month", "year"]),
    mrr_minor: z.number().int().nonnegative(),
    currency: z.string().length(3),
  }),
} as const;

export type EventName = keyof typeof events;
type Props<E extends EventName> = z.infer<(typeof events)[E]>;

export function track<E extends EventName>(distinctId: string, event: E, props: Props<E>) {
  const parsed = events[event].safeParse(props);
  if (!parsed.success) return reportError(new Error(`bad analytics event: ${event}`));
  client.capture({ distinctId, event, properties: parsed.data });
}
```

Checks, in order of value:

1. **Types**: a renamed property fails compilation at every call site.
2. **Integration tests on fact events**: inject a fake client and assert that the signup
   handler and the payment webhook emit exactly one event with the right payload, and none when
   the webhook is replayed.
3. **One end-to-end test of the critical funnel**: in Playwright, intercept requests to the
   ingestion host with `page.route` and assert the funnel events fire once, in order.
4. **Production monitor**: alert when the daily count of a fact event falls to zero or deviates
   sharply from the database (`signed_up` events vs new `users` rows). A ratio under about 0.95
   or over 1.0 for a server-side event means loss or duplication. This reconciliation is the
   single most valuable tracking check.
5. Before trusting a new event, watch it arrive in the tool's live event view from a real
   session and check each property's type.

## Versioning and governance

- The plan and the schema map live in the repository; a change to events is a pull request.
  At Scale add a required reviewer for the events file.
- **Never change the meaning of an existing event.** If the trigger or a property's meaning
  changes, add a new event or property (`checkout_completed_v2`, or a `schema_version`
  property), run both for one full reporting cycle, then remove the old one. A silent meaning
  change produces a step in every chart that looks like a product change.
- Adding an optional property is safe. Renaming, retyping or removing one is breaking.
- Record instrumentation changes as annotations on the dashboards on the day they ship.
- Deprecate deliberately: mark an event deprecated in the plan, hide it in the tool, delete the
  call a release later. Quarterly, list events with no queries and remove them.
- Mobile and other long-lived clients keep sending old event shapes for months; keep the old
  definitions documented until those versions fall below a negligible share.

## Ask the user

- **Which questions must the data answer this quarter?** The plan is derived from them.
  Default: signup-to-paid funnel, activation rate, weekly retention, signups by channel.
- **Is the customer a person or an account?** Decides whether group analytics is required and
  what the unit of every metric is. Default: account for B2B, user for consumer.
- **Where are the customers, and is there an EU audience?** Decides consent gating and data
  region. Default: assume EU visitors exist; opt-in gating and the EU region.
- **Is session replay acceptable for the customers' data?** Regulated or enterprise customers
  may forbid it. Default: off inside the authenticated product for sensitive domains, on with
  full input masking elsewhere.
- **Is there already a warehouse or a person who writes SQL weekly?** Default: no; start with
  a product suite and enable export later.
