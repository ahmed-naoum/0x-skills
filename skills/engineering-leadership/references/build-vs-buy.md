# Build versus buy and vendor decisions

Read this when: deciding whether to build a capability, adopt open source or pay a vendor;
comparing self-hosting with a managed service; evaluating or negotiating with a vendor; or
leaving one, especially under a deadline.

## The decision in three questions

1. **Does it differentiate?** Would a customer choose the product because of how this part
   works? If not, buy or adopt, and spend the saved time on the part that does.
2. **What does each option cost per year to own,** at the volume expected in 12 to 24 months,
   not at today's volume?
3. **What does leaving cost?** An option with a cheap exit can be chosen fast; an expensive exit
   makes it a one-way door that deserves a spike and a decision record.

| Capability | Default | Build or self-host when |
|---|---|---|
| Auth, sessions, MFA, SSO | Provider or maintained library | Never hand-roll crypto or session code |
| Payments, subscriptions, tax | Stripe, or a merchant of record | Never build card handling |
| Email delivery | Transactional email provider | Never run your own mail server for product email |
| Errors, logs, traces | Hosted backends | Bill exceeds a meaningful share of an engineer and someone can run it |
| Analytics, flags, experiments | One PostHog-style tool | Data must stay on your infrastructure |
| Search | Postgres full-text search | Relevance tuning, typo tolerance or facets at scale are the product (`0x:data-stores`) |
| Internal admin | Simple internal pages plus a database GUI | Many operations staff with complex workflows → buy an internal-tool builder |
| Editable marketing content | Headless CMS if non-developers edit | Only developers edit → files in the repo |
| Notification routing | Small in-house module | Many channels, digests and preferences → buy (`0x:email-notifications`) |
| Core domain workflow | Build | It is the product |

## Yearly ownership cost

Compare per year, over the same horizon:

```text
Build = initial effort / expected life in years
      + upkeep (rule of thumb: 15-25% of the initial effort, every year)
      + hosting + on-call and incident time + security patching
Buy   = price at the volume expected in 12-24 months
      + integration effort / expected life + integration upkeep (API version changes)
      + vendor management (contracts, reviews, renewals)
```

Price founder and engineer hours at their opportunity cost, with the market rate for a fully
loaded engineer as the floor. For a solo founder the real cost of building a commodity is the
revenue work not done.

Traps:

- **Build estimate versus first-month vendor price.** Compare at future volume and include
  upkeep. Built things need on-call; that is the line most often missing.
- **Vendor price at today's volume.** Plot price at 1x, 10x and 100x usage. Per-event,
  per-active-user and per-seat prices that look trivial now can dominate the bill at Scale.
- **"We will wrap it so we can switch."** Abstractions over a vendor leak and double the code.
  Put one seam where an exit is plausible (a module that owns all calls to the vendor); do not
  build a generic layer over every vendor.
- **Buying something that needs as much integration as building.** If the integration is most of
  the work and the vendor covers only the easy part, build.

## Evaluating a vendor

| Dimension | Question | Red flag |
|---|---|---|
| Fit | Did a spike prove the hardest case with real data? | Only the demo was tried |
| Data export | Can all data, with IDs and relations, be exported self-serve in a documented format? | Export only by support ticket, or partial |
| Standard interfaces | OIDC or SAML, SQL, S3-compatible API, OpenTelemetry, SMTP? | Proprietary SDK calls spread through every module |
| Pricing curve | Price at 1x, 10x, 100x; which metered dimension grows fastest? | A tier jump on a metric you do not control; "contact sales" just above the entry tier |
| Pricing power | How costly is switching once integrated? | High switching cost with no price cap in the contract |
| Viability | Age, customer base, funding or revenue, open-source fallback, acquisition risk | Early-stage vendor in a critical path with no export |
| Reliability | Status-page history, SLA, regions | No public incident history |
| Security | SOC 2 or ISO 27001 report, SSO and audit log for your team | No report, shared logins only |
| Terms | Data ownership, price-change notice, termination and post-termination export | Vendor may use your data, or deletes it at once on termination |

Pricing power grows with switching cost: the more a vendor is woven into the product, the more
a price rise should be expected and capped in writing. The privacy side of a vendor (DPA,
subprocessors, transfers) belongs to `0x:privacy-compliance`.

Lock-in that is easy to miss:

- **Identity.** Some hosted auth providers do not export password hashes, or only through a
  support request. Without hashes, leaving forces password resets or a lazy migration that
  keeps the old provider alive. Check before adopting.
- **Payments.** Card data can usually be moved between PCI-compliant processors only on
  request, which takes weeks; subscriptions must be recreated on the new side.
- **Logic in a vendor's UI.** Workflows, rules and templates built in a dashboard live outside
  the repo, untested and unversioned. Keep business rules in code.
- **Platform-specific runtime APIs.** Edge or serverless features tied to one host. Keep them at
  the edges of the app.
- **Data gravity.** Egress fees and sheer volume make large datasets slow and costly to move.

## Running a time-boxed spike

A spike answers one question with throwaway code before a commitment.

1. **Write the question and the decision rule first.** "If option A imports our largest
   customer file with our schema in under a minute and handles the failure path, choose A;
   otherwise B." Deciding the rule after seeing results invites rationalization.
2. **Set the box.** Half a day to three days for a solo founder. When the box ends, decide with
   what is known or explicitly buy one more box; never extend silently.
3. **Test the hardest path,** not the hello world: real data shape and volume, auth, the error
   and retry path, webhooks, the migration of existing data.
4. **Run the same test against each option,** including "keep what we have" where it applies.
5. **Record the result** in the decision log in five lines; delete the code or leave it on an
   unmerged branch. Spike code merged as-is becomes production code nobody designed.

Coding agents make parallel spikes cheap: one per option, each in its own worktree
(`0x:ai-coding-agents`).

## Self-hosted open source versus managed

| Cost line | Managed | Self-hosted |
|---|---|---|
| Compute and storage | Included, at a markup | Paid directly |
| Backups and restore tests | Mostly included; still test restores | Build, schedule, test |
| Upgrades and security patches | Done for you, on their schedule | Yours, including major versions |
| High availability, failover | A setting | Design, build and rehearse |
| Monitoring and paging | Partly included | Yours |
| On-call | Vendor's | Yours, at night |

Rules:

- A stateful system (database, queue, search, object store) self-hosted is a commitment to
  backups, restore tests, upgrades, failover and being paged. Managed wins until its bill
  exceeds a meaningful part of an engineer's cost and someone has capacity to run it.
- Stateless tools are cheap to self-host; the case is much weaker for anything holding data.
- Data residency, compliance or air-gapped customers can force self-hosting earlier.
- Check the license and the governance, not just the code. Several widely used projects
  (Elasticsearch, Redis, Terraform) moved to source-available licenses and were forked
  (OpenSearch, Valkey, OpenTofu). Prefer projects governed by a foundation, or have a fork as
  the exit, when the license matters to the business.

## Credits, contracts and renewals

- **Startup credits.** Cloud providers and many vendors run startup programs, often reached
  through accelerators or investors. Credits expire: model the bill at full price before the
  architecture depends on it, and set a reminder 60 days before expiry.
- **Start monthly** while the vendor is unproven. Move to annual prepay once sure; an annual
  discount of about two months is a common rule of thumb, and more is often available.
- **Ask for**: a cap on renewal price increases; overage rates fixed in the contract; ramped
  commitments that grow with usage; the right to reduce seats or tier at renewal; data export
  during the term and for a stated period after termination; SLA credits.
- **Avoid** committed minimums the company may not reach, true-up clauses without a cap, and
  multi-year terms without a price cap or an exit.
- **Leverage**: the vendor's quarter or year end, a competing quote, a growth story, and
  agreeing to be a public customer story.
- **Renewal routine**: auto-renewal notice windows are often 30 to 90 days, so put the notice
  date, not the renewal date, in the calendar. Ninety days before, audit usage (unused seats,
  wrong tier), get one competing quote, and decide.

Keep a vendor register in the repo: vendor, owner, monthly cost, renewal date, notice deadline,
data held, and exit path. It doubles as due diligence material.

## Migrating off a vendor under a hard deadline

Triggers: shutdown, acquisition, sudden price rise, terms change, security incident. Plan to
finish with a third of the time left; the last third goes to stragglers and surprises.

1. **Export everything today,** before any other step, while access is guaranteed. Confirm the
   contractual end date and the post-termination export window in writing.
2. **Inventory every touchpoint**: SDK imports and API calls, environment variables, inbound and
   outbound webhooks, DNS records, scheduled jobs, dashboards and alerts, people and systems
   using the vendor's UI, and data held only there.
3. **Choose the target with a spike** on the hardest path, not the demo.
4. **Put one seam at the call sites** so traffic can switch per tenant behind a flag.
5. **Move state**: idempotent backfill, then dual-write or forward new events during the
   transition; verify with counts and checksums per tenant, not by eye.
6. **Cut over in cohorts**: internal accounts, a small share, then everyone, keeping the old
   path for rollback until verification passes.
7. **Decommission**: remove the SDK, revoke and rotate keys, clean DNS, keep a final archive,
   and cancel after the notice period.

| Domain | Trap | Response |
|---|---|---|
| Auth | Password hashes not exportable | Lazy migration: verify against the old provider at sign-in, rehash locally, force resets for the rest at the deadline |
| Payments | Card migration takes weeks | Request it on day one; move new customers first |
| Email | New provider's DNS and reputation | Add the new DKIM and SPF records early; ramp volume gradually if on dedicated IPs |
| DNS | Long TTLs delay cutover | Lower TTLs a few days before |
| Object storage | Egress fees, silent partial copies | Budget egress; verify object counts and checksums |
| Webhooks | Partners still call the old endpoint | Accept both during transition; log callers of the old one |

If the deadline cannot be met, ask the vendor for an extension (often granted when asked
early), and migrate only what the business cannot run without. Cutover mechanics are in
`0x:ci-cd-release`; database moves in `0x:postgres-database`.

## Ask the user

- **What is an hour of the founder's time worth to the business right now?** It decides most
  build-versus-buy questions. Default: the market rate of a senior engineer, fully loaded.
- **What monthly spend on tools and infrastructure is acceptable at current revenue?** It sets
  how far managed services can go. Default: managed for everything stateful until the bill
  forces a review.
- **Which vendors are trusted with customer data, and are there regions or certifications
  buyers require?** It narrows the vendor list. Default: vendors with a SOC 2 report, data in
  the region of the first market.
- **Can the company commit to annual contracts?** Prepay saves money but spends runway.
  Default: monthly until the vendor has proven itself for a quarter.
- **For a forced migration, what is the true deadline and what can be cut?** Default: the
  vendor's stated end date minus two weeks, with only revenue-critical paths in scope.
