# Customer onboarding

Read this when: a business customer has just signed, a new self-serve account needs to reach
value, planning a kickoff or implementation, building an importer from a competitor, training
users, or finding accounts whose onboarding has stalled.

## Touch model by contract value

Onboarding cost has to fit inside the account's economics. The bands below are rules of thumb;
set the real thresholds from the product's acquisition cost and gross margin
(`0x:pricing-monetization`).

| Annual contract value | Model | What the customer gets |
|---|---|---|
| Under a few thousand | Self-serve | In-product checklist, behavior-triggered email, help center, email support |
| Low five figures | Low touch | Self-serve plus one setup call, group onboarding sessions or office hours, import help |
| Above that, or complex | High touch | Named owner, kickoff, written implementation plan, weekly check-ins, admin and user training, assisted migration |

Complexity moves an account up a band whatever its value: integrations with their systems, data
migration, SSO, many seats, or a change to a team's daily process. At Prototype and early Launch
the founder onboards every account personally: it is the fastest way to see where people get
stuck. Automate what repeats once the same steps have been walked through a dozen times.

## First value and the onboarding checklist

Define first value as one observable product event, not a feeling: "first invoice sent", "first
report shared with a colleague", "first sync completed". Track time to first value per account
(measuring activation and funnels → `0x:product-analytics`).

- Three to five steps that lead to the first-value event, in the order that produces it, each an
  action with a deep link. Ten-step checklists get abandoned.
- Defer everything not needed for first value: profile photo, preferences, notification settings.
- Mark steps done automatically from product events, never by the user ticking a box.
- Never show an empty product: provide sample data or a template, clearly labeled and removable.
- Ask for teammate invites at the step where collaboration creates value, not on the first screen.
- Trigger email by what the user has not done yet ("You connected X; next is Y"), not by days
  since signup (lifecycle email → `0x:growth-marketing`; empty states and tours → `0x:ui-ux-design`).

Business accounts have two levels: the admin's setup (SSO, users, integrations, import, billing)
and each user's own first value. An account is onboarded only when a target share of the purchased
seats has reached first value, not when the admin finishes setup.

## Kickoff and implementation plan for larger customers

Hand over internally first. Sales writes a note before kickoff so the customer is never asked
again what sales already learned: why they bought (pains and numbers), agreed success criteria,
every promise made (features, dates, terms), stakeholders and their stance, technical environment
(identity provider, systems to integrate, data sources), risks, contract dates.

Kickoff, 45 to 60 minutes, with their project owner and, for the first ten minutes, their
executive sponsor:

1. Introductions and roles on both sides; their sponsor says why the project matters.
2. Restate the goals and success criteria from the sale; confirm or correct them.
3. Phases, milestones and the go-live date.
4. Their responsibilities, each with a named person: admin, IT and SSO, data export, user list,
   internal announcement.
5. Communication: weekly 30-minute check-in, shared channel, escalation path on both sides.
6. Risks and dependencies.
7. Next steps with dates.

| Phase | Output | Exit criterion |
|---|---|---|
| Setup | Workspace configured, SSO, roles | Admin signs in through their identity provider |
| Data and integrations | Import done, integrations connected | Their data owner validates the data |
| Pilot group | One team doing real work in the product | Pilot team reaches first value |
| Rollout | All purchased seats invited and trained | Target share of seats active |
| Review | Success criteria measured; handover to the success owner | Goals signed off; plan for the year |

- Go-live within weeks, not months (rule of thumb: 30 to 60 days for mid-market), anchored to
  their event: a quarter start, a season, the old tool's contract end. Momentum dies with the
  urgency of the sale.
- A plan without time allocated by the customer's project owner fails. Ask for that time in the
  close plan, before signature (`discovery-demos.md`).
- Change management is theirs, but supply it: an internal announcement template, a "why we are
  switching" FAQ, and the date the old tool is switched off. Without a switch-off date, people
  keep using the old tool and the new one looks unused at renewal.

## Importers that move customers off a competitor

Switching cost is the strongest reason a prospect stays with a competitor they dislike, so a good
importer is a sales tool as much as an onboarding one.

| Option | When | Cost |
|---|---|---|
| CSV import with column mapping | Any source that exports CSV; build this first | Low and generic |
| Direct API importer for a named competitor | One or two competitors account for most switching deals | Medium; their API changes must be tracked |
| White-glove migration run by you | High-value accounts with messy data | Time per account; charge for it or use it as a negotiated concession |

Requirements for any importer:

- **Dry run first**: parse and validate, then show a preview with counts and a per-row error
  report before writing anything.
- **Idempotent and re-runnable**: upsert by the source system's ID stored on each record, so a
  rerun after fixing errors never duplicates.
- **Lossless**: keep source IDs, timestamps, authors, relations, attachments and comments; map
  unknown fields to custom fields or notes rather than dropping them.
- **Background job** with progress, partial-failure handling and an email on completion (jobs and
  uploads → `0x:backend-architecture`).
- **Accept the competitor's export as it is**; asking the customer to reshape a spreadsheet loses
  the switch.
- **Use the customer's own credentials** (OAuth or an API key they provide), respect the source's
  rate limits, and delete the credentials when the import finishes.
- **Cutover support**: bulk import, parallel running, a final delta import, then switch-off.
- **Reconcile with their data owner**: record counts and sums (amounts, quantities) match before
  the import is declared done.

Importing a customer's own data with their credentials is normally the customer's right. Do not
scrape the competitor or use undocumented access, and read the competitor's API terms. Personal
data in imports falls under the DPA (`0x:privacy-compliance`). Choose which competitor to support
from discovery notes: build for the one whose name comes with "migration" most often.

## Training users

| Audience | Format | Notes |
|---|---|---|
| Admins | Live session, recorded; admin guide | Setup, roles, SSO, billing, export |
| End users | Short task videos (a few minutes, one task each), written guides with screenshots, in-product hints | "How to approve an invoice", not "Product overview" |
| Large organizations | Train the trainer: teach their champions and give them the materials | Scales without the founder in every room |
| Pooled customers | Recurring office hours, open questions | Cheaper than one-to-one; shows where docs fail |

- Train each role on its two or three daily tasks, not the whole product.
- Train just before people need it, at rollout, not weeks earlier.
- Videos go stale with every interface change. Record tasks whose screens are stable, keep the
  script as text, and add "re-record affected videos" to the release checklist. Written guides
  with screenshots are cheaper to keep current; make them the primary format.
- Send the recording and the guide after every session, and track who attended.
- Questions asked in training and office hours are the best list of help-center gaps
  (`support-operations.md`).

## Tracking milestones and chasing stalled accounts

Record milestone dates per account in the CRM or a table fed by product events: signed, kickoff
held, admin setup done, data imported or integration connected, first value reached, target seat
activation reached, go-live, success criteria reviewed. Pipe product events into the CRM so the
account owner sees progress without asking engineering.

| Signal | Action | Owner |
|---|---|---|
| Self-serve: no first-value event in the first few days | Behavior email; personal email for accounts above a size threshold | Automated, founder |
| High touch: no milestone progress in 7 days | Check in with their project owner; offer a working session | Onboarding owner |
| No progress in 14 days, or a missed milestone date | Escalate to their executive sponsor with the plan and the blocker | Founder |
| Seat activation below target at day 30 | Find inactive teams; targeted training; ask the admin about rollout | Onboarding owner |
| Their project owner has left | Find the new owner that week; re-kickoff if needed | Account owner |

- Thresholds above are starting points; adjust to the product's normal pace.
- Seat activation in the first two to three months predicts the renewal: unused seats get cut or
  the contract canceled (`success-churn.md`).
- Escalate with facts and an offer, not blame: "Two of four steps are done; the import is waiting
  on the export from your old system. Shall we do it together on Thursday?"
- At go-live, hand the account to whoever owns success with a short note: goals, status, risks,
  contacts.

## Ask the user

- **What contract values separate self-serve, low touch and high touch?** Default: the founder
  onboards every account until about twenty, then bands by annual value.
- **Charge an implementation fee?** Default: yes for high touch, shown on the order form even when
  discounted.
- **Which competitor do switchers come from?** Default: CSV import first; an API importer for the
  competitor named most in discovery.
- **What is the first-value event?** Default: the first action that produces the outcome the
  customer bought.
- **Who owns onboarding after the founder?** Default: the founder until the first support or
  success hire.
