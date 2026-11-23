# MVP scoping

Read this when: deciding what a first version or a large new feature must include, what to cut,
what to fake or do by hand, how long it should take, and when it is good enough to charge for.

## The scoping procedure

1. Write the one job (from `problem-validation.md`): "When <situation>, <user> wants to <job> so
   they can <outcome>."
2. Choose one user. When user and buyer differ, the MVP serves the user's job; the buyer's needs
   (reports, approvals, administration) are met by hand.
3. Draw the happy path from first contact to the moment the outcome is delivered, as numbered
   steps. It is usually five to ten steps.
4. Put every wished-for feature in one column: on the path (build), needed but off the path
   (fake, do by hand, or buy), later (cut), never.
5. List the assumptions the product rests on and find the riskiest (below). If the path does not
   test it, the scope is wrong whatever its size.
6. Estimate the path. Past about six weeks of work, cut further or test the risk without building.

Commonly cut from a first version, with what replaces it:

| Cut | Replacement until it is needed |
|---|---|
| Roles, permissions, teams | One role; add teammates by hand on request |
| Settings pages | Sensible defaults and "email us to change this" |
| Admin dashboard | Database console or an internal table tool |
| Self-serve import from many sources | The founder imports the customer's data |
| Several integrations | One integration, CSV, or a no-code automation tool |
| Notifications and digests | One transactional email; the rest sent by hand |
| Search, filters, bulk actions | Short lists until data volume needs them |
| Several plans | One plan, or invoices sent by hand |
| Mobile apps, offline, localization | A responsive web app in one language |
| Analytics dashboards for customers | A report generated and emailed by hand |
| Onboarding tours | A call with each new customer |

Do not cut what is cheap now and expensive to retrofit:

- An account or workspace that owns the data, even with one user per account
  (`0x:backend-architecture`).
- Authentication from a maintained provider or library (`0x:auth-identity`).
- Backups that have been restored at least once, and error tracking.
- Correct payment handling if money is taken (`0x:payments-billing`).
- Analytics events on the steps of the happy path (`0x:product-analytics`); without them the
  first users' behavior is lost.
- Terms, a privacy policy and a way to delete an account (`0x:privacy-compliance`).

## Scope around the riskiest assumption

List the assumptions in four categories, then rate each on uncertainty and on damage if wrong.

| Category | Typical assumption | Cheapest test |
|---|---|---|
| Desirability | The ICP has this problem badly enough to switch | Interviews, concierge (`problem-validation.md`) |
| Viability | They will pay enough; they can be reached at an affordable cost | Pre-sale; outreach reply and conversion rates |
| Feasibility | It can be built: data is accessible, a model is accurate enough, an API allows it | A technical spike on real data |
| Usability | Users reach the outcome without help | Prototype test (`0x:ui-ux-design`) |

The riskiest assumption is the one with the highest uncertainty times damage. The MVP exists to
test it; everything else is cut or faked.

- Riskiest is desirability or viability: build nothing yet. Run concierge or a pre-sale.
- Riskiest is feasibility: spike first. Run the hardest technical piece against real customer
  data before building any interface. Extraction or matching that is accurate on demo inputs and
  fails on real documents is the classic lost quarter. For LLM features, this spike is an
  evaluation on real inputs (`0x:ai-features`).
- Riskiest is usability: prototype the core interaction and watch about five users try it.
- Re-rank after each test; the riskiest assumption changes as each one is retired.

## Fake it, do it by hand, or buy it

| Need | At Prototype and Launch | Build it when |
|---|---|---|
| The core outcome, when automating it is the hard part | Concierge: a person produces it, disclosed to the customer | Manual work exceeds about a day a week, or customers wait on it |
| Onboarding and data import | The founder does it on a call | Sign-ups outpace founder hours |
| Internal admin | SQL console or an internal table tool | Non-technical staff or daily support work need it |
| Billing | Hosted checkout or payment links, one plan | Plan or usage logic is a differentiator |
| Auth, email delivery, payments, search, file storage | Buy: a provider or library | Rarely; build versus buy is `0x:engineering-leadership` |
| Integrations | A no-code automation tool or CSV export | Several customers need the same one and the glue keeps breaking |
| Reports for buyers | A script, results sent by email | Customers ask for them more than weekly |
| Content, docs, marketing pages | Markdown files or a hosted CMS | Non-developers edit content often |

- Manual work is research as much as a shortcut: doing the job by hand reveals the real workflow,
  the edge cases and the data, which makes the eventual automation smaller and right.
- Log hours per manual process each week. Automate the one costing the most hours, not the most
  annoying one.
- Disclose humans in the loop. Customers who believe a process is automated and confidential have
  a legitimate complaint when they learn otherwise, and untrue claims of automation or AI can be
  deceptive marketing.
- Buying adds a vendor and a bill; at this stage it is almost always cheaper than code that must
  be maintained.

## Ship a narrow MVP in weeks, then iterate on usage

Fix the time and let scope flex: decide the appetite (how much time the bet is worth) before
designing, then cut scope to fit rather than moving the date. Rule of thumb: the first real user
is on the product within two to six weeks; past eight weeks, the scope or the plan is wrong.

| Week | Work | Exit condition |
|---|---|---|
| 0 | Spike the riskiest technical piece on real data | Works on real inputs, or the plan changes |
| 1–2 | Happy path end to end, plain but correct, deployed | The founder completes the job on production |
| 3 | Three to five users from validation use it while the founder watches | Each completes the job; every point of help is noted |
| 4+ | Fix what blocked the job; add only what the path needs | Users complete the job unassisted and return unprompted |

- First users come from interviews, design partners and the waitlist, not from a public launch.
  Launching before the job works spends one-time attention on a product that cannot keep it
  (`0x:growth-marketing` for launches).
- The early usage signal that matters: a user completes the job without help and comes back for
  the next instance without a reminder. Sign-ups and first sessions measure curiosity.
- Ship small changes several times a week, each answering a question a user raised.
- Every new request passes the job filter: does it block the happy path for the ICP? If not, it
  waits (`prioritization-roadmaps.md`).

| Symptom | Cause | Fix |
|---|---|---|
| Months in, no real user | Scope too wide; building for imagined users | Cut to the happy path and put it in front of three users this week |
| Users try once, say it is nice, do not return | The MVP does not complete the job, or the pain is mild | Watch a session; if the job completes, revisit the pain evidence |
| Every call adds a feature | No job filter | Score requests against the job and the ICP |
| A clean platform with no product | Generalizing before two concrete cases exist | Hard-code the first case; abstract at the third |
| Polished product nobody wants | Tested feasibility and usability, skipped desirability | Stop building; run concierge or pre-sale with the ICP |

## Define what is good enough to charge for

Charge from the first customer, or at the end of a design partnership at the latest. Paying
customers give honest feedback and real priorities; free users give opinions.

It is good enough to charge when all of these hold:

- It delivers the core job outcome for the ICP reliably, with or without manual help that is part
  of the service.
- It beats the customer's current alternative on the one dimension they care most about, even
  while losing on many others.
- Their data is safe: real authentication, restorable backups, no known data-loss bugs.
- There is a way to pay, a way to cancel, and a support promise the founder can keep (for
  example, a reply within one business day).
- Known limitations are stated before purchase.

Not required: feature parity with incumbents, polish outside the core path, self-serve for
everything, integrations beyond the first.

Label the early phase honestly ("early access", saying what that means), give founding customers
a discount with an end date rather than a free period, and set the price with
`0x:pricing-monetization`.

## Set the quality bar per area

| Area | Bar from the first real user |
|---|---|
| Core job path | Fast, correct, polished, covered by an end-to-end test |
| Data integrity, auth, security, payments | Production grade; never negotiable at any stage |
| Empty, loading and error states on the core path | Decided in the spec (`specs.md`) and built |
| First-run experience | Clear enough to reach the first outcome; hand-holding allowed |
| Secondary features | Functional and plain |
| Settings and rare flows | A stub with a "contact us" link |
| Internal admin | Ugly is fine |
| Marketing site | One page, one promise, one call to action |

Count clicks on stubs and "contact us" links; each is a demand signal for that area and points at
what to build next. Raise an area's bar when it moves onto the core path, when it generates
support load, or when it starts losing deals.

## Ask the user

- **How much time is this bet worth?** The appetite sets the scope. Default: six weeks to the first
  paying user.
- **Which assumption worries the founder most?** It is often the riskiest one. Default:
  desirability, until pre-sales say otherwise.
- **How much manual work per week is acceptable?** Default: up to about a day a week during Launch.
- **Charge from day one?** Default: yes, with a founding-customer discount that ends on a stated
  date.
- **Will the product hold regulated data (health, finance, children's data)?** It raises the bar on
  data handling from the first user (`0x:privacy-compliance`). Default: assume not, and ask before
  storing any such data.
