# Plans, packaging and the pricing page

Read this when: deciding how many plans to offer, what goes in each, where limits sit, what the
free plan allows, how customers grow their spend, what an enterprise tier contains, or designing
or reviewing the pricing page.

## Plan count and shape

Default lineup for a self-serve B2B product at Launch:

| Slot | Who it is for | Role |
|---|---|---|
| Free plan or trial | Evaluators, individuals | Entry (`revenue-model.md`) |
| Plan 1 | One person or a very small team | Low-friction first purchase |
| Plan 2, recommended | The core segment: a team using the product for real work | Where most revenue should land |
| Plan 3 | Larger teams needing control: admin, permissions, integrations | The expansion destination |
| Enterprise, "contact us" | Organizations with security, compliance and procurement needs | Anchor and qualification path |

- **At most three self-serve paid plans.** Each extra plan is one more comparison for the buyer
  and one more set of entitlements in code forever. One paid plan plus a trial is fine at
  Prototype; split only when data shows distinct segments.
- **One plan per segment, named for who it serves** (Solo, Team, Business). Metal and gem names
  make the buyer read the feature list to find themselves.
- **Adjacent plans about 2 to 3 times apart in price** (rule of thumb). Narrower gaps push buyers
  to the cheapest plan; wider gaps strand a segment with no plan that fits.
- **Mark one plan as recommended**, the one the core segment should buy. If most new customers
  pick a different plan, the segment assumption or the fences are wrong.
- **Make plans comparable on the same axes**: same value metric, same feature rows in the same
  order, so the difference is visible at a glance.

## The upgrade trigger

Every boundary between plans needs a trigger: an event caused by the customer's success, at which
the next plan is obviously worth it.

| Good trigger | Why it works |
|---|---|
| Team grows past the plan's seat count | Growth means more value; paying more is expected |
| Usage passes the allowance (projects, contacts, credits) | Directly tied to value received |
| They need control: roles, approvals, audit logs | Arrives with organizational size and budget |
| They connect business systems: CRM, SSO, warehouse | The product has become part of operations |

| Bad trigger | Why it fails |
|---|---|
| A core feature locked in a higher plan | Lower-plan customers never reach value, so they churn instead of upgrading |
| A limit that bites before value (two exports, three days of history) | Feels like a trap; trial users leave |
| A limit almost nobody reaches | No upgrades; the lower plan cannibalizes the higher one |

Check with data from Launch: per plan, the share of customers reaching 80 percent of a limit within
three months, and the share of those who upgrade. A limit almost nobody hits, or that almost
everyone hits in week one, is in the wrong place.

## Fencing: which features and limits go where

Place each feature with three questions, in order:

1. **Does it drive activation or the core value?** Put it in every plan, including free. Fencing
   it lowers conversion on every plan below the fence.
2. **Is it valued mainly by a larger or regulated segment?** Fence it in the higher plan: admin
   controls, roles and permissions, SSO, audit logs, advanced integrations, API access at volume,
   retention controls, priority support.
3. **Is it wanted by a minority across segments?** Make it an add-on. A tier feature that few want
   inflates the tier price for everyone else.

- **Limits on the value metric** separate customers of the same kind by size. **Feature gates**
  separate kinds of customer (individual versus organization). Use gates where needs differ, not
  just volume.
- **Do not fence with degraded quality** (slower processing, watermarked exports on paid plans,
  worse output) unless cost truly differs; buyers read it as a deliberately crippled product.
- **Keep fences in one entitlements table** so repackaging is a data change, not a code change
  (`0x:payments-billing`).

## Free plan limits

The free plan must let a user reach the moment the product proves itself, and must end before a
paying customer's normal use.

1. Define activation: the action after which retention jumps (first report sent, first invoice
   paid, first teammate invited). Measuring it → `0x:product-analytics`.
2. Measure the usage needed to reach activation, and a typical paying customer's monthly usage.
3. Place the free limit between the two, closer to activation. If the two overlap, a usage limit
   cannot separate free from paid; gate on seats or a feature instead.
4. Prefer one or two limits that grow with success: projects, records, collaborators, history,
   monthly usage. Each extra limit is another place a free user gets stuck before activation.
5. Build in spread: a "made with" badge, public share pages, invitations. Removing the badge is
   part of what paid plans buy.

Traps:

- **A free plan that covers a small team's whole need.** It becomes the product for most of the
  market. Check the share of free accounts with several active users or heavy usage; if it is
  large, tighten the seat or usage limit for new sign-ups.
- **Variable-cost features free without a hard cap** (AI, SMS, video). Free users then cost money
  with no path to revenue.
- **Tightening limits on existing free users** creates resentment and tickets. Apply new limits to
  new sign-ups, or grandfather existing accounts for a stated period.
- **The limit as a dead end.** At the limit, show which plan removes it, its price and a one-click
  upgrade, and never lose the user's work.

## Expansion paths

Revenue from existing customers costs the least to win. Every plan needs a way for the bill to grow
without a sales conversation:

| Path | Design rule |
|---|---|
| Seats | Charge for people who create or edit; keep viewers and occasional users free so adoption spreads. Self-serve seat adds with proration; on annual contracts, true up periodically instead of invoicing each change |
| Usage tiers | Graduated pricing (each band of units priced at its own rate) rather than volume pricing (all units at the rate of the band reached), which creates cliffs where using more lowers the bill. Show the next band before the customer reaches it |
| Add-ons | For minority needs: extra storage, extra workspace, AI credits, premium support, more environments. Priced standalone, so nobody must jump a tier for one item |
| Annual prepay | Bigger upfront commitment for a discount (`discounts-price-changes.md`) |
| Plan upgrade | Driven by the triggers above, offered in the product at the point of need |

- A "contact sales" button where a self-serve upgrade would do loses the upgrade. Keep expansion
  self-serve up to the enterprise boundary.
- Net revenue retention (current revenue from a cohort of customers ÷ their revenue a year ago) is
  the expansion health measure; definitions and dashboards → `0x:product-analytics`.

## The enterprise tier

Build it when a deal requires it, not ahead of demand; until then, list it with "contact us".
Typical contents, roughly in the order buyers ask for them:

| Item | Notes |
|---|---|
| SSO (SAML or OIDC) and SCIM provisioning | The most common gate. Putting SSO only in the top tier is common and criticized as a tax on security; a middle path is social and email login everywhere, SAML and SCIM in the top tier |
| Roles, permissions, audit logs | Exportable audit logs with configurable retention |
| Security and compliance documents | Questionnaire answers, DPA, subprocessor list, later SOC 2 or ISO 27001 reports (`0x:privacy-compliance`) |
| SLA | An uptime commitment with service credits as the sole remedy, capped at a share of the fee. Commit only to what monitoring measures and the architecture delivers (`0x:site-reliability`) |
| Support | Named contact, response-time targets, onboarding sessions |
| Commercial terms | Annual or multi-year billing, invoices and purchase orders, payment terms, negotiated contract |
| Data controls | Residency, retention settings, export, deletion at termination |

- **Price enterprise with a minimum annual commitment**, not only per seat. Security reviews,
  procurement and custom terms cost a fixed amount per deal; a minimum recovers it.
- Running enterprise deals → `0x:sales-support`; SSO implementation → `0x:auth-identity`.

## The pricing page

Its job: each visitor finds their plan in seconds and trusts the number.

1. **A headline that frames value**, not the bare word "Pricing"; keep "Pricing" in the page
   title and URL so searchers find the page.
2. **Monthly / annual toggle** with the saving stated in money or months. When the headline price
   is the monthly equivalent of an annual price, say "billed annually" and show the annual total.
3. **Plan cards**: name, one line on who it is for, price with its unit ("per editor per month"),
   the four to six items that differ from the plan before ("Everything in Team, plus"), one
   primary button. The recommended plan is visibly highlighted.
4. **Enterprise card or strip** with "starting at" or "contact us" and what it adds.
5. **Full comparison table** under the cards, grouped by category, for buyers who check details.
6. **A usage calculator** when the bill depends on usage: they enter their volume, see the bill.
7. **FAQ for objections**: what happens at a limit, changing plans, cancellation, refunds,
   currencies, taxes, invoices and purchase orders, nonprofit and education discounts.
8. **Proof**: customer logos or short quotes near the decision point.

Checks:

- Price, currency, billing period, tax treatment and trial terms on the page match checkout
  exactly. A mismatch loses the sale and, for consumers, can break consumer law.
- Every feature row is understandable by a buyer, not internal jargon.
- On a phone, cards stack and the comparison table either scrolls inside its own container or
  turns into per-plan lists.
- No hidden mandatory fee; any setup fee or minimum is visible on the card.
- Display, auto-renewal and cancellation rules → `0x:privacy-compliance`; page copy and conversion
  → `0x:growth-marketing`; visual layout → `0x:ui-ux-design`.

## Ask the user

- **Which segments do you serve, and which matters most?** Decides plan count and the recommended
  plan. Default: one core team segment plus a solo plan.
- **Do you want a free plan, and what may it cost per month?** Decides free limits. Default: no
  free plan for inference-heavy products; a trial instead.
- **Which capabilities would you hold back for larger customers?** Decides fences. Default: admin,
  permissions, SSO, audit logs and priority support in the top plan.
- **Can you support enterprise buyers now (security reviews, contracts, SLA)?** Decides whether
  the tier is real. Default: a "contact us" line with a minimum annual commitment, built per deal.
- **Should viewers and occasional users be free?** Decides the seat definition. Default: yes for
  collaboration products.
