# Customer success and churn

Read this when: customers are canceling, downgrading or not renewing; designing a cancellation
flow or save offer; building a health score; planning renewal or expansion conversations; running
business reviews for key accounts; winning back former customers or waking dormant ones; or
deciding when to set up customer success.

Measuring churn, cohorts and retention curves → `0x:product-analytics`. This file is about acting.

## Separate involuntary from voluntary churn

| | Involuntary | Voluntary |
|---|---|---|
| What | A payment failed and was never recovered; nobody decided to leave | The customer decided to cancel, not renew, or downgrade |
| Typical causes | Expired or replaced card, insufficient funds, bank or fraud decline, invoice sent to someone who left | Never activated, value below price, missing capability, competitor, champion left, need ended, poor reliability or support |
| Fixed by | Billing mechanics | Onboarding, product, success, pricing |

Split them first. In card-billed self-serve products failed payments are often a large share of
all churn, and they are the cheapest to fix. Involuntary fixes (mechanics → `0x:payments-billing`):

- Provider smart retries and the card networks' automatic card updater switched on.
- Email before a card expires; dunning email with a direct update-payment link behind no login.
- In-app banner on past-due accounts; full access during the retry period.
- B2B annual plans: invoice to accounts payable by bank transfer, with a billing contact who is
  not the champion.
- Review the recovery rate of failed payments monthly.

Finding the causes of voluntary churn:

1. Require a reason in the cancellation flow (below).
2. Within days of a cancellation, the founder emails personally asking for 15 minutes, with no
   pitch. A stated "too expensive" is often a proxy for low use; the conversation finds the real cause.
3. Read the account's usage over the 30 to 90 days before it left: ever activated? When did usage
   drop, and after what?
4. Code each churned account with one primary cause and review monthly by share of revenue lost.

| Cause | Signal | Owner of the fix |
|---|---|---|
| Never activated | No first-value event | Onboarding (`customer-onboarding.md`) |
| Value below price | Light usage, "too expensive" | Product and pricing |
| Missing capability | Named feature, moved to a competitor | Product (`0x:product-discovery`) |
| Champion left | Contact bounces, new admin appears | Success: more than one relationship per account |
| Need ended | Business closed, project finished, seasonal | Pause option; otherwise accept it |
| Reliability or support | Incidents, negative CSAT, open bugs | Engineering and support |

A B2B annual contract is usually lost months before its renewal date; the cancellation is paperwork.

## Health score and outreach before churn

Start with three to five signals the product already records, each scored red, yellow or green.
A weighted 0 to 100 number looks precise and is not.

| Signal | Green | Red |
|---|---|---|
| Core-action frequency against the account's own baseline | Stable or rising | Halved over 30 days |
| Seat activation | Most purchased seats active | A minority active |
| Breadth | Uses the features tied to the outcome they bought | One peripheral feature |
| Relationship | Champion responsive; sponsor known | Champion gone or silent |
| Support | Ordinary tickets | Escalations, negative CSAT, unresolved bug |
| Billing | Current | Past due |

Validate before trusting it: score last year's churned and renewed accounts retroactively. If the
churned ones were not red 60 to 90 days before leaving, change the signals.

| Trigger | Action, as a task with owner and due date |
|---|---|
| Account turns red | Contact within two business days with a specific observation and an offer of help |
| Champion leaves (bounce, job change) | Reach the replacement and the sponsor that week; re-onboard |
| Usage drops right after a release | Check whether the release broke their workflow |
| Renewal within 120 days and not green | Recovery plan (renewals below) |
| Seats or usage near the plan limit | Expansion conversation |

Self-serve triggers fire email and in-app messages; humans step in only above an account-value
threshold. Skip customer-success platforms (Gainsight, ChurnZero, Vitally, Planhat) until Scale; a
SQL query, a CRM field and a weekly review are enough before that.

## Cancellation flow: reasons, pause and save offers

In the product, at most two screens before confirmation:

1. A required reason: five to seven options plus "other" with a text box.
2. One offer matched to that reason, or none.

| Reason | Offer |
|---|---|
| Too expensive | Downgrade to a cheaper plan, or a time-limited discount within policy (`0x:pricing-monetization`) |
| Not using it right now, seasonal | Pause for one to three months: no charge, data kept, reminder before auto-resume |
| Missing feature | Say truthfully whether it is planned; offer a call with the founder; log it |
| Technical problems | Priority support and an offer to fix it together |
| Switching to a competitor | Ask which one; no offer; make export easy |
| Business closed or project over | No offer; easy export; ask permission to stay in touch |

3. Confirmation: the end date, how long data is kept, how to export, how to reactivate; repeat it by email.

- Cancel stays one click from the offer and never requires a call or chat. Several jurisdictions
  require cancellation to be as easy as signup, and obstruction turns into chargebacks and public
  complaints.
- One save offer per customer per period; repeated discounts teach customers to cancel for them.
- Measure the save rate and whether saved customers are still paying 90 days later. A save that
  churns next month is a deferred loss.
- Pause suits seasonal businesses: they return without re-onboarding.
- Pause and coupon mechanics → `0x:payments-billing`.

## Winning back churned customers

| Segment | Message | When |
|---|---|---|
| Left for a missing feature that has shipped | Founder email: "you asked for X; it is live; your data is still here" | On release |
| Left over price, and pricing has changed | The specific plan that fits | On the change |
| Left over bugs or reliability, now fixed | What changed, honestly, with evidence | Once the fix has held |
| Seasonal or paused | Reminder | Before their season |
| Never activated | Re-onboarding with a setup call | 30 to 90 days after leaving |
| Outside the ideal customer profile | None | Never |

- Keep data for a stated period after cancellation, set in the retention policy
  (`0x:privacy-compliance`), and say so. "Everything is still there" is the strongest argument.
- Offer their old price or a free first month back, not a deep discount that resets expectations.
- Email to former customers needs a lawful basis in their jurisdiction and an opt-out.
- Track reactivations and whether they are still active 90 days later.

## Release announcements that re-engage dormant accounts

- Everyone who asked for a shipped feature gets a personal note (`support-operations.md`).
- Changelog page and in-app announcement for active users; a periodic digest for all; for dormant
  accounts, a "what changed since you last signed in" email limited to changes relevant to how
  they used the product.
- Lead with the problem solved, show it in a screenshot or short clip, deep-link into the feature.
- Do not announce every fix to everyone; fatigue dulls the announcements that matter.
- Writing release notes → `0x:git-collaboration`; lifecycle email → `0x:growth-marketing`.

## Renewal and expansion from account health

Start about 120 days before the end for large annual accounts and 60 to 90 for smaller ones,
always before the customer's non-renewal notice deadline (`proposals-contracts.md`).

| Health at the start | Play |
|---|---|
| Green | Review value delivered against the original goals; propose renewal plus expansion (seats, a higher plan, another team); offer a multi-year price lock in exchange for commitment |
| Yellow | Agree a dated recovery plan first; renew on current terms; expansion later |
| Red | Executive-to-executive call; find the root cause; recovery plan; consider a shorter term or reduced scope over losing the account; concessions only against commitments |

- Expansion triggers: seats at the limit, usage near a plan limit, a new team asking for access,
  the customer hiring in the relevant function, a new use case in tickets.
- A price increase gets the notice the contract requires and a value story (policy →
  `0x:pricing-monetization`).
- The auto-renewal invoice is never the first renewal message on a large account; surprise
  invoices get disputed and canceled.
- Agreeing to fewer seats at renewal usually beats losing the account.

## Business reviews for key accounts

Hold them for the top accounts (for example the top tenth by revenue, or all above a value
threshold), quarterly or twice a year; other accounts get an emailed summary.

- The economic buyer attends, not only users. When the economic buyer stops coming, the account
  is at risk.
- Meet the champion beforehand and agree what they want their boss to hear.
- Content, mostly about them: their goals; outcomes in their numbers (time saved, revenue, errors)
  against the discovery baseline; adoption by team; support summary; recommendations to get more
  value; upcoming changes that matter to them; goals for next period.
- Capture the baseline at kickoff. Without a "before" number, no review can show value.
- Not a roadmap presentation or a sales pitch; expansion follows from demonstrated value.
- Send a written summary with actions and owners within a day.

## Standing up customer success

Start when the founder can no longer hold a real relationship with every account that matters
(rule of thumb: beyond a few dozen high-touch accounts), or when renewals bring surprises.

1. Write the lifecycle and its owners: sales to signature, onboarding to go-live, success for
   health, reviews and renewal. Decide explicitly whether success or sales owns expansion.
2. First hire: a generalist who can onboard, run reviews and handle renewals, often an experienced
   support person or a technical account manager.
3. Segment the book: named owner for high-touch accounts; pooled, automated plays for the rest.
4. Main measure: gross revenue retention of the book; net revenue retention too if success owns
   expansion. Pay a base plus a bonus on that retention, and commission if they carry expansion.
5. Weekly: red and yellow accounts and every renewal in the next 120 days.
6. CRM fields and the health query first; a dedicated platform at Scale.

## Ask the user

- **Which loss hurts more, accounts or revenue?** Sets where effort goes. Default: revenue.
- **What may be offered to keep a customer?** Default: pause, downgrade, one time-limited
  discount within pricing policy.
- **How long is data kept after cancellation?** Default: a stated window from the retention
  policy, shown in the cancellation confirmation.
- **Which accounts count as key accounts?** Default: the top tenth by revenue.
- **Does success carry an expansion target?** Default: no before Scale; success owns renewal.
