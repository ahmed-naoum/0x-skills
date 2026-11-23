# Technical debt

Read this when: deciding which shortcuts to take and how to record them, choosing which old
shortcuts to repay, justifying a refactor or migration to whoever controls time or money,
retiring a feature or system, or noticing that small changes keep getting slower.

## Borrow deliberately, with a repayment trigger

Martin Fowler's quadrant separates debt by two questions: deliberate or inadvertent, prudent or
reckless. The only debt worth taking is prudent and deliberate ("ship now and handle the
consequences when X happens"). Inadvertent debt ("now we know how it should have been built")
is normal and gets added to the register when discovered. Reckless debt ("no time for design")
is not a trade-off; it is a cost with no matching benefit.

Shortcuts that are fine at Prototype and Launch, with typical repayment triggers:

| Shortcut | Repay when |
|---|---|
| No application cache | A route's p95 exceeds its budget |
| Admin tasks done with SQL scripts | They take over about an hour a week, or a second person must do them |
| Duplicated logic in two places | A third copy appears, or a bug is fixed in one copy only |
| Polling instead of realtime | Users notice, or polling load shows up in database metrics |
| Slow work done inside the request | Timeouts appear, or p95 exceeds budget |
| Hard-coded configuration | A second customer needs a different value |
| Thin tests on non-critical UI | That area breaks twice |
| One region, no replicas | Measured latency or capacity says so |

Never borrow here, because the interest is unbounded and arrives all at once:

- Authorization and tenant isolation.
- Data integrity: constraints, backups with a tested restore, money in integer minor units.
- Billing correctness.
- Secrets in code or in the repository.
- Formats and IDs exposed to customers or integrations (they are one-way doors).
- Schema changes on live data without a rollback or forward-fix plan.

Record the debt at the moment it is taken, in the same pull request:

```ts
// DEBT(D-014): invoice PDF rendered inside the request.
// Repay when: p95 of POST /invoices > 800 ms, or any timeout in a week. See docs/debt.md
```

A shortcut without a trigger is a TODO that rots. A good trigger is observable: a metric
crossing a number, an event ("before the first enterprise customer"), or a count ("when this
file is changed for the third time for the same reason").

## A visible register

Keep one table in the repository (`docs/debt.md`), or issues with a `debt` label if the team
already lives in an issue tracker. Not both.

| ID | What and where | Interest: what it costs now | Principal: effort to fix | Trigger | Owner | Added |
|---|---|---|---|---|---|---|
| D-014 | Synchronous invoice rendering, `src/billing/invoice.ts` | About two timeouts a week, support replies | 2 days | p95 > 800 ms | Founder | 2026-05-02 |

Rules:

- Keep the active list short, about twenty items. Merge duplicates and delete items nobody
  would ever fix; a register of two hundred items is ignored.
- Review it monthly in fifteen minutes: check triggers, re-rank, pick what goes into the next
  cycle's debt slot.
- When an item is repaid, delete it and add a line to the decision log.
- Cross-check markers in code against the register:

```bash
grep -rhoE "DEBT\(D-[0-9]+\)" src | sort -u
```

The register is also due diligence material: a ranked, owned list of known debt reads as
control; debt the reviewer finds first reads as risk.

## Ranking by interest

Rank by interest, not by ugliness. Interest is how often the team touches the code times how
much the debt slows each touch, plus the chance it fails times the damage when it does.
Principal (the cost to fix) only breaks ties and decides sequencing.

| Kind of debt | Priority | Reason |
|---|---|---|
| Security, data loss, tenant leak, billing error risk | Now, ahead of features | Rare but unbounded damage |
| Taxes every change: slow or flaky CI, slow local setup, painful deploys | High | Paid on every change by everyone |
| Hot code with frequent changes and frequent bugs | High | Paid on every feature in that area |
| Blocks revenue: an enterprise requirement, an integration | Schedule as feature work | It is revenue work |
| Dependency nearing end of support | Before the end date | Security fixes stop |
| Old dependency, no known vulnerability, no blocker | Batch quarterly | Low interest until it blocks something |
| Cold code nobody touches, ugly but working | Leave it | Zero interest |

Find where interest is being paid by combining change frequency with bug fixes:

```bash
# Files changed most often in the last six months
git log --since="6 months ago" --name-only --pretty=format: | grep -v '^$' \
  | sort | uniq -c | sort -rn | head -20
# Files most often touched by commits whose message mentions a fix
git log --since="6 months ago" -i --grep='fix' --name-only --pretty=format: | grep -v '^$' \
  | sort | uniq -c | sort -rn | head -20
```

Large files high on both lists are the hotspots. Repay there first, either inside the feature
that touches the area (leave each touched file a little better, within the pull request's
scope) or in the reserved debt slot (`technical-strategy.md`). Items over a week of work get a
design doc.

## Making the case in business terms

The person deciding cares about money, time, customers and risk, not code quality.

| Engineering symptom | Business framing |
|---|---|
| Changes in the billing module take three times longer than elsewhere | Revenue features ship weeks later; show lead time for that area |
| Flaky tests | Hours a week lost, at a loaded hourly cost |
| Framework version near end of support | Security fixes stop on a known date; security questionnaires ask about it |
| Manual operations | Founder hours a week, plus errors that reach customers |
| Single point of failure | Expected downtime times revenue per hour, plus SLA credits |
| Auth setup cannot do SSO | Named deals blocked, and their annual value |

```markdown
## Proposal: <name>
Cost today: <hours per week, incidents per month, deals blocked, risk with its date>
Investment: <range in engineer-weeks>, in <N> increments, each shippable on its own
Payback: <investment divided by monthly cost> months; risk removed: <...>
Checkpoints: after increment 1, measure <metric>; stop if <abort criterion>
If we do nothing: <what happens, and when>
```

Rule of thumb: payback under about six months in hot code is an easy yes; beyond a year, do it
only if it removes a tail risk or unblocks revenue.

Never ask for "a rewrite". Ask for increments that each deliver value, using the strangler fig
pattern: the new path is built beside the old, traffic moves over piece by piece, and the old
path is deleted. A big-bang rewrite with a feature freeze is the classic way to lose a year and
the customers who were waiting for features. Carrying out the refactor is `0x:code-quality`.

## Retiring features and systems

Every feature keeps costing: tests, dependencies, support questions, security surface, and the
attention of whoever reads the code. Candidates for retirement: features used by a small share
of active accounts with real upkeep, duplicated internal systems, vendors no longer needed, old
API versions and dead feature flags.

1. Measure usage over at least one full billing cycle; some features are used monthly or
   yearly (exports, annual reports).
2. Check commitments: contracts, the pricing page, public docs, API consumers.
3. Decide with the numbers and record the decision.
4. Announce a timeline to affected users with an export or an alternative. Rule of thumb: 30
   to 90 days for paid features, longer for APIs (`0x:api-design` covers API sunsets).
5. Turn it off behind a flag first, and watch errors and support for a cycle.
6. Delete everything: code, tests, flags, scheduled jobs, infrastructure, vendor subscriptions,
   secrets and API keys, docs, and data according to the retention policy.
7. Log what was removed and why.

Traps: removing a feature from the UI while its code, jobs and endpoints keep running (cost and
attack surface stay); deleting data that must be kept for legal or accounting reasons
(retention rules are in `0x:data-stores` and `0x:privacy-compliance`); breaking integrations
without notice. Give every new feature flag a removal date when it is created
(`0x:ci-cd-release`).

## Architecture erosion: notice early, correct small

Erosion is the code drifting from its intended structure one convenient shortcut at a time.
Each step is reasonable; together they make every change touch everything.

| Signal | How to see it |
|---|---|
| Imports reaching into another module's internals | A dependency rule failing in CI |
| Circular dependencies | `npx madge --circular --extensions ts,tsx src/` |
| One file changed in most pull requests | The hotspot command above |
| Small changes touching many files | Files per pull request rising over time |
| Two models of one concept (two `User` or `Plan` types) | Search for duplicate type names |
| Business rules in route handlers or UI components | Review of hot files |
| Lead time and CI duration rising for small changes | Delivery measures (`estimation-planning.md`), CI timings |
| Environment variable sprawl | Count of configuration keys over time |

Correct with small, continuous investments rather than a big restructuring:

- Encode the intended structure as a check that fails CI, so erosion is caught in the pull
  request that causes it. For TypeScript, dependency-cruiser expresses module rules:

```js
// .dependency-cruiser.cjs  - run with: npx depcruise src --config .dependency-cruiser.cjs
module.exports = {
  forbidden: [
    { name: "no-circular", severity: "error", from: {}, to: { circular: true } },
    {
      name: "billing-only-through-its-index",
      severity: "error",
      from: { pathNot: "^src/modules/billing/" },
      to: { path: "^src/modules/billing/", pathNot: "^src/modules/billing/index\\.ts$" },
    },
  ],
};
```

- Give each module one public entry file and import only through it.
- Fix one boundary violation per cycle, in hot code first; leave cold areas alone.
- Put a time budget on CI (for example ten minutes) and treat exceeding it as debt with a
  trigger, because slow CI taxes every change.

## Ask the user

- **How much engineering time per cycle is reserved for debt?** Without a reserved slot debt is
  never repaid. Default: the stage split in `technical-strategy.md`.
- **Which product areas will change most in the next two quarters?** Future change predicts
  interest better than past ugliness. Default: the areas with the most recent commits.
- **Are there dates that turn debt into risk?** A security review, an audit, a framework end of
  support, a large customer onboarding. Default: none known; check dependency support dates.
- **Is there a feature suspected to be unused that feels risky to remove?** It is often the
  cheapest upkeep saving. Default: measure for one billing cycle before deciding.
- **Who must approve a multi-week refactor?** Default: the founder, on the business case above.
