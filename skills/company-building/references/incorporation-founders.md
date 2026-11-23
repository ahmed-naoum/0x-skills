# Incorporation, founder legal basics, IP protection and the board

Read this when: choosing a company type or country, formalizing a co-founder, building something
while still employed, engaging the first contractor, naming the product, a clone uses the brand or
content, buying insurance, weighing a patent, or forming a board.

This file gives mechanisms and common practice. Company, employment, IP and tax law differ by
country and, in the US, by state. A startup lawyer in the company's jurisdiction should review
formation documents, co-founder terms and anything contested. Equity mechanics, option plans and
the cap table → `0x:startup-finance`. Each mechanism below is labeled with its country; where a US
or UK one is named, the common EU counterpart follows. A founder elsewhere should put the same
question to a local lawyer or accountant.

## Entity and jurisdiction

| Situation | Common default | Why |
|---|---|---|
| Plans to raise from US venture investors | Delaware C corporation | Investors, financing documents and option plans assume it |
| US, bootstrapped, profits paid to owners | LLC in the home state | Pass-through taxation, less formality, one state to deal with |
| Outside the US, local customers, no US venture plans | The home country's standard limited company: UK Ltd; France SAS, or SASU for a single founder; Germany GmbH, or UG to start with little capital; Netherlands BV | Local banking, payroll and tax are simplest, and local investors know the form |
| Outside the US, aiming at US venture capital | Home company now; a US parent ("flip") when a US lead investor asks, or Delaware from day one if that is certain | A later flip costs legal fees and can trigger tax at home; get advice before doing it |
| Testing an idea alone, no hires, no money raised | Simplest local form | Form a company before the first contract with real liability, a co-founder, or outside money |

| Form | What to know |
|---|---|
| UK Ltd | Formed online at Companies House within days; founder vesting lives in the articles and a shareholders' agreement |
| French SAS or SASU | No minimum capital, flexible statutes, filed through the online single window (guichet unique); founder leaver terms go in the shareholders' agreement (pacte d'associés); a paid président joins the employee social-security scheme, with high contributions |
| German GmbH or UG | Notarized formation; GmbH share capital 25,000 euros, at least 12,500 paid in before registration; a UG starts from 1 euro but must retain a quarter of each year's profit until it converts; every share transfer, and any agreement obliging one (founder buybacks included), needs a notary |
| An EU-wide form | None yet. The Commission proposed an optional "EU Inc." company form in March 2026; it is still in the legislative process, so check its status before choosing |

Traps:

- Forming abroad does not move tax residence: a company run from the founder's home country is
  usually taxable there too (place of effective management or a permanent establishment). Take
  home-country tax advice before forming a Delaware, UK or Estonian company from elsewhere.
- US: an LLC cannot issue standard stock options, and most venture funds cannot invest in one for tax
  reasons. Converting later works but costs money. If venture funding is likely within a year or
  two, start as a C corporation.
- US: a C corporation pays corporate tax and owners pay again on dividends; for a profitable lifestyle
  business that double layer matters. Its founders may qualify for the qualified small business
  stock (QSBS) exclusion on a sale. For stock issued after July 4, 2025 the exclusion is 50% after
  three years, 75% after four and 100% after five, capped per holder at the greater of $15 million
  or ten times basis, for companies with gross assets up to $75 million when the stock is issued.
  Some states do not follow it; confirm current figures with a tax advisor.
- A Delaware company operating elsewhere must also register ("foreign qualification") in each state
  where it has employees or an office, and pays that state's fees and taxes.
- Paying personal bills from the company account weakens the liability shield. Separate bank
  account from day one.

Formation sequence for a US C corporation (other forms are analogous):

1. Check the name is free as an entity name and as a trademark (below) before filing.
2. File the charter through a registered agent; adopt bylaws; appoint directors and officers.
3. Issue founder shares at a nominal price with vesting and a company repurchase right on unvested
   shares. Each founder assigns prior work on the product to the company as part of the purchase.
4. File the 83(b) election within 30 days of the share issuance when the shares are subject to
   vesting. The deadline cannot be extended, and missing it can turn each vesting date into taxable
   income. The IRS accepts it online (Form 15620, through an IRS online account) or by mail; keep
   proof of filing and give the company a copy.
5. Get the tax ID, open the bank account, register in the operating state.

Outside the US: the UK counterpart of the 83(b) is a joint section 431 election signed by founder
and company within 14 days of acquiring shares subject to forfeiture or transfer restrictions; it is
kept on file, not sent to HMRC. France and Germany have no matching election; ask a tax advisor how
founder shares with leaver clauses are taxed before signing the shareholders' agreement.

Keep filings current with a shared compliance calendar, one owner per deadline:

- US: annual report and franchise tax in the state of incorporation; for Delaware corporations, due
  by March 1. Delaware's default calculation produces an alarming bill for companies with many
  authorized shares; recalculating with the assumed par value capital method usually cuts it sharply.
  Annual reports in each state of registration; registered agent renewal.
- Income tax returns everywhere, even with no revenue.
- UK: a confirmation statement every year and annual accounts at Companies House. Since 18 November
  2025 every new director and person with significant control must verify their identity there
  (existing ones over the following year, tied to the confirmation statement); failing to is an
  offense.
- France: approve the annual accounts within six months of year-end and file them with the
  commercial court registry. Germany: publish annual accounts through the company register
  (Unternehmensregister).
- Beneficial ownership: US-formed companies and US persons owe no federal Corporate Transparency Act
  report (exempt since 2025, made permanent by an August 2026 FinCEN rule); foreign companies
  registered in a US state still file, and some states have their own rules (New York for LLCs).
  EU countries keep registers every company files with at formation and on each change (France's
  RBE, Germany's Transparenzregister); the UK keeps its PSC register. Check what applies at
  formation and whenever ownership changes.

Missed filings cost good standing. A company not in good standing struggles to close a round, sign
some contracts or be acquired, and in time can have its charter voided (Delaware) or be struck off
the register (UK).

## Co-founder agreement

Sign before significant shared work. The equity documents are the legally operative part: in the
US a stock purchase agreement with vesting; in the UK and most of Europe a shareholders' agreement
with leaver clauses (a pacte d'associés in France; in Germany notarized where it obliges GmbH share
transfers). A co-founder agreement records the rest and is drafted alongside them.

| Topic | Decide | Default |
|---|---|---|
| Split | Percentages by expected future contribution, not by who had the idea | Close to equal among full-time founders, never 50/50 without a tie-break |
| Vesting | Schedule and cliff | 4 years, 1-year cliff, for every founder including the CEO |
| Roles | Who owns which domain | One owner per domain: product, engineering, sales, operations |
| Decision rights | Who decides within a domain; how cross-domain disputes end | Domain owner decides; CEO breaks ties; equity, fundraising, sale or shutdown need all founders |
| Commitment | Full-time from when; outside work; salary | Full-time from a stated date; equal salaries until the board decides otherwise |
| Leaving | Vested and unvested shares, titles, board seats | Unvested repurchased at cost; vested kept; departing founder resigns all offices |
| Bad leaver | Whether cause lets the company buy back vested shares cheaply | Common in Europe, rarer in the US; define cause narrowly (fraud, material breach, competing); courts in several European countries strike down buyback prices far below fair value, so a local lawyer sets the price |
| Acceleration | Vesting on acquisition | Double trigger: acquisition plus termination without cause |
| Death or disability | Repurchase rights and how they are funded | Company may repurchase at fair value; consider key-person insurance |
| Disputes | Steps before litigation | Structured conversation, then mediation, then arbitration or court |

With a 50/50 split, any disagreement can deadlock both the board and the shareholders. Give one
founder a casting vote or one more share, or appoint a mutually trusted third director early.
Negotiating a departure → `founder-effectiveness.md`.

## Building while employed

Read the employment contract before writing a line. Look for invention assignment (often covering
anything "related to the business" or made "during employment"), outside-activity clauses,
non-compete and non-solicit clauses, and confidentiality.

- Use only personal equipment, accounts, time and networks. Code on an employer laptop or
  repository, or written in work hours, gives the employer a claim.
- Never use the employer's code, data, customer lists or confidential information.
- California Labor Code section 2870 limits assignment of inventions made entirely on the
  employee's own time without employer resources, except those relating to the employer's business
  or research or resulting from work for the employer. Several other states have similar statutes.
- UK: patentable inventions made in the course of normal duties belong to the employer (Patents Act
  1977 section 39), and contract terms taking more than that are unenforceable for those inventions
  (section 42); copyright in work made in the course of employment belongs to the employer.
  Germany and France: software written in the course of the job belongs to the employer by statute,
  and German law lets the employer claim an employee's service inventions against compensation.
  Elsewhere, ask a local lawyer whether side projects are covered.
- If the idea is adjacent to the employer's business, get a written release first, or leave first.
- Non-competes: enforceability varies widely. In the US it is state law (California voids most).
  Germany and France enforce a post-employment non-compete only if the employer pays compensation
  for its duration (in Germany at least half of the last pay); UK courts enforce only narrow,
  reasonable ones. Non-solicits of colleagues and customers are enforced more often: do not recruit
  coworkers while still employed.
- Keep a dated record of where and when the work was created. Investor due diligence asks.

## IP assignment

The company, not the people, must own everything the product is built from. Due diligence for a
round or an acquisition checks every contributor, and a gap found then is expensive to fix.

| Contributor | Document | Key point |
|---|---|---|
| Founders | IP assignment at the share purchase | Covers work done before incorporation |
| Employees | Proprietary information and inventions assignment (PIIA, the US name), signed before day one; elsewhere the same clauses sit in the employment contract | Lists excluded prior inventions; includes confidentiality |
| Contractors, agencies | Contractor agreement with an explicit assignment | Without one the contractor keeps copyright: in the US "work made for hire" generally does not cover contractor software; in the UK an assignment must be in writing, signed by the contractor |
| Advisors | Advisor agreement with assignment of their work product | Most often forgotten |
| Dependencies | License inventory | → `0x:privacy-compliance` |

- US: use present-tense wording ("hereby assigns"). A promise to assign later can lose to a present
  assignment someone else holds.
- Germany: copyright itself cannot be transferred, so the contract grants exclusive usage rights,
  unlimited in time and place, for every listed use. France: an assignment of author's rights must
  list each right with its scope, purpose, territory and duration; what is not listed stays with the
  author. Use a local template, not a translated US one.
- Where moral rights exist (much of Europe), add a waiver or a covenant not to assert them, as far
  as local law allows.
- Contractors reusing their own libraries grant a perpetual, irrevocable license to those parts.
- US agreements with employees and contractors include the Defend Trade Secrets Act whistleblower
  immunity notice; without it the company loses exemplary damages and attorney fees against them.
- A past contributor never signed? Get a confirmatory assignment now, while relations are good.

## Standard templates

Keep a small set of reviewed templates with e-signature; do not draft per hire. Law-firm startup
libraries and incorporation services give reasonable starting points; have a lawyer adapt them once.

| Template | Must contain | Notes |
|---|---|---|
| Mutual NDA | Definition, exclusions, permitted use, term | Rarely needed; investors generally will not sign one |
| Contractor agreement | Scope, fees and payment terms, IP assignment, confidentiality, independent-contractor terms, termination, governing law | One statement of work per engagement |
| Offer letter | Title, pay, start date, at-will or notice terms, equity "subject to board approval", contingencies | Outside the US usually a full employment contract → `hiring.md` |
| PIIA | Assignment, prior-invention list, confidentiality, return of property | Signed before any access |
| Advisor agreement | Duties, equity with vesting, assignment, confidentiality | Small grant vesting monthly over one to two years is common |

## Trademark: clear and register

Clear the name before spending on the brand. Renaming after launch costs the domain, search
rankings, design work and customer recognition.

1. Knockout search: national trademark databases (USPTO, EUIPO, WIPO's global database), app
   stores, domains, social handles, and the web for unregistered use in the same field.
2. Prefer distinctive marks. Invented or arbitrary words register easily; descriptive names
   ("Fast Invoice") are hard to register and to defend.
3. File in the classes that cover the product: usually class 9 (downloadable software) and 42
   (SaaS, hosted software), plus classes for services sold, such as 35 or 41.
4. File in each market where the product sells. In the US an intent-to-use application can be filed
   before launch; EU and UK filings need no prior use. One EU trade mark (EUIPO) covers every member
   state; the UK needs its own filing. A filing abroad within six months can claim the first
   filing's date (Paris Convention priority), and the Madrid system extends one application to many
   countries.
5. Use "TM" until registration and the registered symbol only where registered; implying a
   registration that does not exist is an offense in some countries, the UK among them.

Use a trademark attorney for a full search once real money goes into the brand. Examination takes
many months, and fees are charged per class.

## Enforcing against clones

Collect evidence first: dated screenshots, archived copies, the copier's WHOIS, DNS and host, and
proof of the original (repository history, publication dates).

| Infringement | Route | Notes |
|---|---|---|
| Copied text, images, code or docs | Copyright takedown to the host or platform: in the US a DMCA notice to the host's designated agent; in the EU the host's notice-and-action channel | US: a counter-notice restores the content after 10 to 14 business days unless the claimant sues |
| Name or logo on a site, app or account | Platform trademark complaint; registrar and host abuse reports | Much faster with a registration |
| Confusingly similar domain | UDRP complaint for generic TLDs: identical or confusingly similar, no legitimate interest, registered and used in bad faith; URS for quick suspension on newer TLDs; country-code domains (.uk, .fr, .de) follow their registry's own procedure or the courts | Transfer or cancellation only, no damages |
| Phishing or payment clone | Abuse reports to host, registrar, CDN and browser safe-browsing services at once | A security incident too → `0x:web-security` |
| A real business copying | Lawyer's cease-and-desist letter, then litigation if worth it | Overreaching letters that claim rights in ideas can backfire in public |

In the US, register copyright in key works (docs, site content, a code snapshot) early: registration
is required before suing over a US work, and statutory damages and attorney fees are available only
if registration came before the infringement or within three months of publication. The EU and UK
have no copyright registration; keep dated proof of authorship instead (repository history, a dated
deposit). In the EU, the Digital Services Act obliges hosting providers to run a notice-and-action
process for illegal content; use the host's own form so the notice counts.

## Insurance

| Policy | Covers | Buy when |
|---|---|---|
| Technology errors and omissions | Claims that the product failed and caused a customer loss | First B2B contract, or a contract requires it |
| Cyber | Breach response, forensics, notification, extortion, business interruption, third-party claims | Customer personal data or payment flows; often bundled with tech E&O |
| Directors and officers (D&O) | Claims against directors and officers over management decisions | Outside investors or independent directors; investors often require it |
| General liability | Injury, property damage, some advertising claims | Office, events, or a contract lists it |
| Workers' compensation (US), employer's liability (UK) | Workplace injury | US: mandatory with employees in nearly every state (Texas lets most employers opt out); UK: compulsory with employees; Germany and France: statutory accident insurance through payroll contributions, no separate policy |
| Employment practices liability | Discrimination, harassment, wrongful-termination claims | First employees |

- Enterprise contracts name minimum limits; buy to match before signing.
- Names differ by country: tech E&O is professional indemnity in the UK and responsabilité civile
  professionnelle in France. Ask a local broker which policies are compulsory for the sector.
- Most of these policies are claims-made: they respond to claims made during the policy period for
  acts after a retroactive date. Keep coverage continuous and notify the insurer of a possible
  claim as soon as it appears.
- Cyber applications ask about MFA, backups and patching. Answer accurately; a misstatement can void
  coverage exactly when it is needed.

## Patents and trade secrets

For most web software companies, patents are not worth their cost at Prototype or Launch: each one
costs a large sum over several years, software patents face eligibility limits in the US and
exclusions in Europe, and enforcement is beyond a small company's budget. Consider them for a
genuine technical method (hardware, novel algorithms with a measurable technical effect, deep tech)
or where investors in the sector expect a portfolio.

- Public disclosure (launch, blog post, demo, open-sourcing) destroys novelty immediately in most
  countries, including at the European Patent Office; the US gives the inventor's own disclosure a
  one-year grace period. If patents may matter, file first: a US provisional application, or a first
  national or European filing, holds the date for 12 months while filing elsewhere.
- Trade secrets (models, data pipelines, pricing logic, know-how) cost nothing to create but exist
  only while protected by reasonable measures (a condition under both US law and the EU Trade
  Secrets Directive): access control, confidentiality terms, marking,
  clean offboarding. Code shipped to a browser or app is not secret.
- Publishing a technical description defensively stops others from patenting it.

## Board

| Stage | Composition | Practice |
|---|---|---|
| Prototype, Launch, no priced round | Founders only, often one or two directors | Written consents (US) or written resolutions (UK) for formal acts: share issues, option grants, officers, bank resolutions |
| First priced round | Founders plus investor seats set by the financing documents | Quarterly meetings, minutes, D&O insurance |
| Later | Add an independent director; keep an odd number | Audit and compensation committees at Scale |

- Send the pre-read several days ahead: metrics against plan, what went well and badly, cash and
  runway, and the asks (decisions or help) stated at the top. The meeting discusses the asks; it
  does not replay the deck.
- Deliver bad news before the meeting, by phone. Never let the board learn it in the room.
- Formal acts (option grants, valuation approvals, officer changes) need a resolution or written
  consent; record decisions in minutes.
- At later stages, close with an executive session without management.
- An advisory board has no authority and no fiduciary duty; it is a set of advisor relationships.
- Outside the US and UK the organs differ: a French SAS has a président and whatever board its
  statutes create; a German GmbH has managing directors bound by shareholder instructions, often
  with an advisory board (Beirat). The pre-read practice carries over; which acts need a formal
  resolution is set by local law and the statutes.

## Ask the user

- In which country do you live and run the company day to day? Tax residence and the available
  forms follow from it; default to forming there, with local advice before forming anywhere else.
- Do you plan to raise venture capital in the next two years, and from which country? It decides C
  corporation versus LLC or a local company; default to the local standard company unless US
  venture money is likely.
- Are you employed now, and what does the contract say about inventions and outside work? It decides
  whether the IP is clean; default to assuming the clauses apply until a lawyer says otherwise.
- How do you and your co-founder split decisions, and what happens to equity if one leaves in year
  one? Defaults: domain owners decide, the CEO breaks ties, 4-year vesting with a 1-year cliff.
- Has anyone contributed code, design or content without a signed assignment? Default: get
  confirmatory assignments now.
- Where do you sell, and how much brand spend is planned this year? It sets where and when to file
  trademarks; default to the home market and the largest customer market, before launch.
- Do customer contracts require insurance, and what data do you hold? Default: tech E&O plus cyber
  at the first B2B contract.
