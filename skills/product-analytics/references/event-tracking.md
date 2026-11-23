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
- **No variable data and no UI elements in names.** Not `project_42_exported`, and not
  `button_clicked {button: "export_csv"}` either: name the user's action (`report_exported`
  with `format: "csv"`). UI names change with every redesign; actions survive.
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
  B2B product answer the wrong question. In some suites (PostHog among them) it is a paid
  add-on with a free allowance, and enabling it can change what every identified event costs:
  check the current terms before designing around it.
- Check that raw events can be **exported** in bulk. Without export, switching tools later
  means losing history.
- Pricing is per event or per tracked user and changes often: check current pricing against the
  expected event volume, and note that session replay and autocapture multiply volume.
- Do not run two product-analytics SDKs "to compare". They never agree and the reconciliation
  consumes weeks. Warehouse pipelines belong to `0x:data-stores`.

## Setting up a product suite

For PostHog and its equivalents, in this order:

1. **Region, projects, keys.** Choose the data region when the account is created (PostHog's US
   and EU clouds are separate instances; moving later is a data migration into a new project)
   and sign the DPA. One project each for development, staging and production. The project
   (capture) key is public by design; personal or admin API keys can read and delete data and
   stay server-side.
2. **Client init from the vendor's current framework guide, not from memory**: the init
   location and recommended options change between SDK versions (for recent Next.js, PostHog
   currently uses `instrumentation-client.ts` and a `defaults` option whose value is a date:
   copy the current date from the docs, because an old one pins old behavior). Then check
   that each client-side route change produces exactly one page view.
3. **Consent mode before the first capture**, a reverse proxy, profiles only for identified
   users, then `identify`, `reset` and `group` (sections below).
4. **Autocapture and replay.** Keep autocapture as a safety net; build official metrics only on
   named events. Enable replay with input masking and sampling, because it is billed separately.
5. **Filters and limits.** Define the internal and test-user filter in project settings, and
   set the vendor's billing limit so a bot or traffic spike cannot run up a bill.

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
const posthog = new PostHog(process.env.POSTHOG_KEY!, {
  host: process.env.POSTHOG_HOST, // the region's ingestion host
  flushAt: 1,       // serverless: send at once instead of batching;
  flushInterval: 0, // on a long-lived server omit both options
});
posthog.capture({
  distinctId: user.id,
  event: "subscription_started",
  properties: { plan: "pro", interval: "month", mrr_minor: 2900, currency: "usd" },
  groups: { company: account.id },
});
await posthog.flush(); // serverless: the send must finish before the handler returns
```

Traps:

- **Serverless drops events** unless the send completes before the handler returns
  (`await posthog.flush()`, the SDK's awaitable `captureImmediate` where the installed
  version has it, or the platform's run-after-response hook such as Next.js `after()` or
  `waitUntil`). `shutdown()` also flushes but ends the client, and the SDK does not support
  reusing an instance afterward: on a module-level client that a warm function reuses, later
  events are at risk. On long-lived servers create one client, keep batching, and call
  `shutdown()` once on SIGTERM.
- **Webhook retries double-count.** Emit from the idempotent branch of the webhook handler
  (after the "already processed this event ID" check), not at the top.
- **Emit after commit.** An event sent inside a transaction that rolls back is a phantom.
  At Scale, write events to an outbox table and send from a job.
- **Analytics must not break the request.** Wrap sends so a vendor outage degrades tracking,
  not checkout.
- **Revenue numbers in analytics are for segmentation, not accounting.** The payment provider
  and ledger remain the source for MRR (`0x:startup-finance`, `0x:payments-billing`).
- To reduce client loss, serve the SDK and ingestion through a reverse proxy on the product's
  own domain, following the vendor's proxy guide. Pick a neutral path or subdomain: names
  containing `analytics`, `tracking`, `telemetry` or the vendor's name are on blocklists. This
  recovers part of the loss, not all of it, and does not remove the need for consent.

## Identity: anonymous, user, account

Three IDs, each with one job:

| ID | Set when | Rule |
|---|---|---|
| Anonymous ID | first page view, generated by the SDK | lives in first-party storage on that device |
| User ID | signup or login | the database primary key; never email (it changes and is personal data) |
| Account/group ID | when the user acts within a workspace | attached to every event of a B2B product |

Sequence that gets it right:

1. On signup and on every login, call `identify(user.id)` on the client. The tool links the
   anonymous history on that device to the user, so pre-signup page views join the funnel.
2. Server-side events use the same `user.id` as `distinctId`.
3. On logout call `reset()`. Without it, the next person on a shared browser is recorded under
   the previous identity: PostHog refuses to merge or re-identify an already identified user
   under a different ID (it logs an ingestion warning instead), and history mixed this way
   cannot be cleanly separated afterward.
4. Call `group("company", account.id)` after login and whenever the active workspace changes.

```ts
posthog.identify(user.id, { plan: account.plan }, { first_seen_app_version: version });
posthog.group("company", account.id, { name: account.name, plan: account.plan });
posthog.reset(); // on logout
```

Traps: a placeholder ID such as `"null"`, `"undefined"`, `"anonymous"` or `"0"` (usually an
unset variable turned into a string) lumps unrelated users into one person, or, in tools that
block known placeholders as PostHog does, silently fails to link the identity. Guard both the
client `identify` and the server `distinctId`: send nothing unless the value is a real
database ID. A server event emitted before the client ever called `identify` (for example
signup through an OAuth callback) must use the final user ID. The pre-signup history joins when the client next calls `identify`
on that device; if the client may never load after signup (API or mobile handoff), pass the
SDK's anonymous ID to the server at signup and link it with the server SDK's `alias` call.
Cross-device history joins only after login on each device; anonymous visits on a device that
never logs in stay separate, and no compliant technique fixes that.

## Consent and data minimization

The legal rules belong to `0x:privacy-compliance` (`consent-cookies.md`); the instrumentation
must make whatever the banner says true.

- **Gate on the consent state, not on the banner being shown.** Initialize the SDK opted out
  and switch on only after an opt-in where opt-in is required (posthog-js at the time of
  writing: `opt_out_capturing_by_default: true`, then `opt_in_capturing()`; check current
  docs). Verify in the browser that nothing is stored or sent before the choice.
- **Counting visitors who refuse, without cookies, is a legal choice.** posthog-js
  `cookieless_mode: "on_reject"` (plus a project setting) keeps sending their events with no
  device storage. Whether that needs consent differs by country and regulator
  (`0x:privacy-compliance`). Default: off; visitors who refuse are not tracked.
- **Server-side events are still personal data.** Cookie rules attach to reading or writing
  the device; data-protection law attaches to the processing wherever it runs. Keep the facts
  in the product's own database regardless, but have the server wrapper check the consent or
  opt-out flag on the user record before copying events to the analytics vendor. The legal
  basis for server-side analytics is settled in `0x:privacy-compliance`; until it is, honor
  the same choice as the client.
- **Send IDs, not identity.** No emails, names, phone numbers, free-text fields, search
  queries, or full URLs with tokens in properties. Scrub query strings in page URLs
  (`?token=`, `?email=`, reset links).
- **Session replay**: mask all inputs by default and block elements showing customer data;
  enterprise buyers ask about it. It records personal data: same consent gate, named in the
  privacy policy. Undisclosed replay has drawn wiretap-style claims in some jurisdictions,
  several US states among them (`0x:privacy-compliance`).
- **Minimize person profiles.** Create identified profiles only for logged-in users; keep
  marketing-site traffic anonymous and aggregate.
- **Deletion must reach the vendor.** The account-deletion job calls the analytics tool's
  person-deletion API; add it to the data-subject-request runbook.
- Exclude internal users, test accounts and impersonation sessions by a property
  (`is_internal: true`) set at identify time, and filter it in every saved insight.

## Validate events so tracking does not silently break

Tracking fails silently, so types and tests must guard it. Put every call behind one typed
wrapper, which also applies the ID guard, the analytics opt-out and the `is_internal` flag;
forbid direct SDK calls with a lint rule.

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
  // reportError: the project's error tracker. A bad payload is reported, never thrown.
  if (!parsed.success) return reportError(new Error(`bad analytics event: ${event}`));
  client.capture({ distinctId, event, properties: parsed.data });
}
```

Checks, in order of value (1, 4 and 5 from the first event; 2 and 3 from Launch):

1. **Types**: a renamed property fails compilation at every call site.
2. **Integration tests on fact events**: inject a fake client and assert that the signup
   handler and the payment webhook emit exactly one event with the right payload, and none when
   the webhook is replayed.
3. **One end-to-end test of the critical funnel**: in Playwright, intercept requests to the
   ingestion host with `page.route` and assert the funnel events fire once, in order.
4. **Production monitor**: alert when the daily count of a fact event falls to zero or deviates
   sharply from the database (`signed_up` events vs new `users` rows). For a server-side event
   the ratio of events to rows should sit close to 1.0; as a rule of thumb, under about 0.95
   means loss and anything over 1.0 means duplication.
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
- Deprecate deliberately: mark the event deprecated in the plan, hide it in the tool, delete
  the call a release later. Quarterly, remove events nobody queried in the last 6 months.
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
