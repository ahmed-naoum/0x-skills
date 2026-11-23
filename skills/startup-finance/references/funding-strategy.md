# Funding strategy and investor communication

Read this when: deciding whether to raise money at all, choosing between bootstrapping, angels,
venture capital, revenue-based financing or grants, planning what to achieve before a round,
preparing a short pitch, or writing the monthly update to investors.

## Venture-scale or bootstrapped niche: decide first

Venture funds return most of their money from a few very large outcomes, so each investment must
plausibly become large enough to return a meaningful part of the fund. That is why venture
capital pushes growth over profit, and why it is the wrong money for a business that could be an
excellent, profitable company of modest size.

| Question | Points to venture | Points to bootstrapping |
|---|---|---|
| Can this reach very large revenue (well beyond 100M a year) in a reachable market? | Yes, with a credible path | A niche that tops out lower |
| Does winning require spending ahead of revenue (network effects, heavy R&D, land grab)? | Yes | Customers can fund growth |
| Can it grow several-fold a year in the early years? | Yes | Steady growth is the realistic shape |
| What does the founder want in five years? | A large outcome, accepting a high chance of nothing | Control, income, freedom to sell at any size |
| Are funded competitors racing for the same customers? | Yes | No, or customers buy slowly anyway |

The arithmetic founders skip:

- After venture rounds, a sale for a modest amount can return little to founders, because
  investors' liquidation preferences are paid first (waterfall in `fundraising-process.md`),
  and investors may resist a sale that does not move their fund.
- Owning all of a business earning a few million a year in profit is often a better personal
  outcome than a small share of a long shot. Compare expected personal outcomes, not
  valuations.
- Once venture money is in, the bootstrapped path mostly closes: the company is now expected to
  grow fast or be sold. Decide before raising, not after.

## Sources of money

| Source | Fits | Cost | Watch |
|---|---|---|---|
| Customers (bootstrapping) | Anything customers pay for early | Slower growth | Annual prepayments, paid pilots and pre-sales are customer funding; lifetime deals buy cash now and support costs forever |
| Friends and family | A small first amount before evidence | Equity or a SAFE; relationships | Only money they can lose entirely; same documents as any investor; securities rules still apply |
| Angels | Pre-seed and seed, often around a lead | Equity, usually through SAFEs in the US, advance subscription agreements in the UK, convertible loans in much of Europe | A few useful angels beat many small checks: each is a cap-table line and a signature at future votes |
| Accelerators | First institutional money plus a network | A fixed stake for a standard check | Read the current standard deal; the network and the demo day are what is bought |
| Seed and venture funds | Venture-scale companies with evidence | Commonly 15 to 25% dilution per round (rule of thumb); board seats from priced rounds | Growth expectations reset the company's pace; each next round needs bigger milestones |
| Bootstrapper-oriented funds | Software with a path to profit | Equity, or shared-earnings agreements repaid from profits | Terms vary widely; read the payout mechanics and any cap |
| Revenue-based financing | Existing recurring revenue and a specific use with payback (ads, inventory) | A fixed multiple of the advance, repaid as a share of monthly revenue | Compute the effective annual cost: a fixed fee repaid quickly is a high interest rate |
| Venture debt | After an equity round, to extend runway | Interest, fees, warrants | Covenants and default triggers; never a substitute for equity in a default-dead company |
| Bank loans | Profitable companies with assets or steady cash flow | Interest; usually a personal guarantee for small companies | A personal guarantee puts the founder's own assets at risk |
| Equity crowdfunding | Consumer products with a community | Equity plus platform fees; many small holders | Regulated offering limits and disclosures; a crowded cap table for later investors |
| Grants and credits | Research-heavy work, regional programs | Time, reporting, restrictions | Below |

Default: bootstrap with customer funding until the evidence for venture scale is real. Raise
when money buys a specific milestone faster and the founder wants the venture path.

## Grants, credits and other non-dilutive money

- **Research grants**: the US SBIR and STTR programs (for US small businesses mostly owned by US
  citizens or residents; reauthorized in April 2026 through September 2031 after a six-month
  lapse, with agencies restarting solicitations at different paces, so check each agency),
  Innovate UK, the EU's EIC Accelerator, and national or regional programs. They
  fund defined research, take months from application to money, restrict spending and require
  reporting. Worth it when the roadmap already contains research a program targets; a poor fit
  when applying would reshape the product around the grant.
- **R&D tax credits**: often the largest non-dilutive source for a software company with an
  engineering payroll (`bookkeeping-tax.md`).
- **Cloud credits**: the major clouds run startup programs in tiers, the larger tiers usually
  requiring an accelerator or investor affiliation. Credits expire, commonly within one or two
  years. Model costs after expiry in the forecast, keep spend alerts on while credits cover it,
  and do not choose a provider or architecture for credits alone: migrating later costs more
  than the credits were worth.
- **Vendor startup programs** (payments, CRM, analytics, developer tools) discount the first
  year. Track when each discount ends; they tend to end together and land as a burn jump.
- **Investor tax reliefs** (UK): SEIS and EIS give UK-taxpaying investors income tax relief and
  capital gains exemptions, so UK angels often invest only in qualifying companies. Apply for
  HMRC advance assurance before signing with investors (optional, but they expect it); after the
  shares are issued, file the compliance statement so HMRC authorizes the compliance
  certificates investors need to claim. Company limits rose in April 2026; check current ones.
  The US counterpart, qualified small business stock, benefits US-taxpaying holders and is in
  `bookkeeping-tax.md`; other countries have their own schemes, which a local adviser names.

## Milestones before each round

Work backwards: what the next round's investors need to see, what reaching it costs, plus a
buffer, is what this round raises. Rule of thumb: raise for 18 to 24 months of runway, planning
to start the next raise with at least six months left.

| Round | What investors look for (direction, not thresholds; the bar moves with the market) |
|---|---|
| Pre-seed | A team that can build and sell it; a sharp insight into a painful problem; a working product or prototype; early users or letters of intent |
| Seed | A launched product; early revenue or strong usage; retention showing the product is kept; a clear target customer |
| Series A | Repeatable acquisition; fast growth from a meaningful revenue base (for SaaS commonly cited in the low millions of ARR); strong retention; acceptable unit economics |
| Series B and later | A scaling go-to-market engine; efficiency (burn multiple); a credible path to leading the market |

- Put the milestones in the 18-month model as numbers with dates (`runway-forecasting.md`), and
  review them in every monthly pack.
- Raising too much at too high a valuation sets a bar the next round must clear. A down round
  triggers anti-dilution adjustments, puts employees' options underwater and hurts morale and
  hiring.
- Six months before raising, ask a few investors who lead the next round what they would need to
  see. Their answers are the milestone list, and the conversations are the first meetings of the
  next raise.
- Milestones that do not need money (pricing changes, retention fixes, a sharper target customer)
  come first: they raise the valuation of every later dollar.

## The two-minute pitch

About 250 to 300 spoken words, rehearsed until it sounds unrehearsed. One structure, three
variants.

1. What it is and for whom, in one sentence a stranger can repeat.
2. The problem, as a concrete example of someone suffering it today.
3. Why now: what changed (technology, regulation, behavior) that makes this possible or urgent.
4. How it works, in one line, then the strongest proof: revenue, growth, retention, a named
   customer outcome.
5. Why this team wins it.
6. The ask.

| Audience | Emphasis | Ask |
|---|---|---|
| Customers | The problem and the outcome in their words; no investors, no market size | A trial, a pilot, a purchase |
| Candidates | Mission, stage, what they would own, why now is the moment to join | A next conversation |
| Investors | Market size built bottom-up, traction, why this becomes large | A meeting or a commitment |

Cut buzzwords, "no competition", top-down market math ("1% of a huge market") and feature lists.
Test: after hearing it once, a listener can restate what the company does and why it is winning.
Write the one-sentence version first; if it does not fit in one sentence, the positioning is not
done yet (`0x:growth-marketing` for positioning).

## The monthly update

Send it every month, on a fixed day after the close, to investors, advisors and warm prospective
investors. It builds the trust that decides follow-on money and bridge rounds, and its history
becomes evidence in the next raise.

```text
Subject: [Company] update, October 2026

TL;DR: one or two sentences, good news and bad.

Numbers (same definitions every month)
- MRR 42.1k (+6% MoM) | Revenue 39.8k | Gross margin 78%
- Net burn 31k (3-month avg 29k) | Cash 612k | Runway 19 months to floor
- Customers 214 (+18 new, -5 churned) | Net MRR retention 101%

Highlights: two or three, with numbers.
Lowlights: two or three, stated plainly, with what is being done.
Asks: specific (an introduction to a named person or role, a candidate, advice on one decision).
Next month: one to three priorities.
```

- Send in bad months too, and put the bad news early. Investors forgive bad months; they do not
  forgive surprises, and the ones who heard early are the ones who help.
- Same metrics and definitions every month, taken from the finance pack. Changing what is
  reported when it looks bad is noticed immediately.
- Specific asks get answered; "let us know if you can help" does not.
- Keep customer names and sensitive details out unless recipients are under confidentiality;
  assume the update will be forwarded.
- Send from a tool or with recipients hidden, keep a sent archive, and track who replies with
  help: those are the people to call first for the next round or a bridge.

Before the first institutional money, the same discipline works as a private monthly note to
the founders and advisors: writing it forces the numbers to be known.

## Ask the user

- **What outcome is wanted in five to ten years: a large exit, a profitable company to own, or
  the freedom to sell at any size?** It decides between venture and bootstrapping. Default:
  bootstrap until the answer and the evidence both point to venture.
- **How much dilution and loss of control is acceptable?** Default: no more than about a quarter
  of the company per round, and founders keep board control through the seed.
- **What would the money buy, by which date?** Without a milestone the raise has no size.
  Default: size to 18 to 24 months to the next round's milestones.
- **Can the founders personally afford a slower, customer-funded path?** Default: check personal
  runway (`runway-forecasting.md`) before choosing.
- **Which jurisdictions do the company and likely investors sit in?** It decides instruments and
  tax reliefs such as SEIS, EIS or qualified small business stock. Default: ask before drafting
  anything.
