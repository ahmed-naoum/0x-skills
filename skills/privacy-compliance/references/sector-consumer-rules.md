# Other rules that may apply: sector, consumer, accessibility, AI and trade regulation

Read this when: the product moves into health, children, finance, education or biometrics;
sells subscriptions to consumers; launches in a new country; ships an AI feature to EU users;
distributes installable software in the EU; receives an accessibility complaint; or needs to
know which countries and customers it may not serve.

Everything here is a trigger map: enough to know a regime applies and what it demands first.
Where a row says the regime applies, bring in a specialist before launch; the dates and
thresholds in these laws move, so confirm current ones.

## Sector triggers

| Regime | Applies when | First consequences | Way to stay out |
|---|---|---|---|
| HIPAA (US) | The company is a covered entity (provider, health plan, clearinghouse) or a business associate handling protected health information on behalf of one | Business associate agreement with each customer and with every vendor touching the data; Security Rule safeguards; breach rules | Do not sell to healthcare providers or plans for patient data; forbid PHI in the terms |
| Consumer health data (US) | Health-related data in a consumer app with no covered entity involved: HIPAA does not apply, but the FTC's health breach rule and state consumer-health laws do, some with private lawsuits | Separate consent for collection and sharing; no ad pixels on health pages | Do not collect health signals |
| COPPA (US) | The service is directed to children under 13, or there is actual knowledge a user is under 13 | Verifiable parental consent before collection; under the amended rule (compliance from April 2026) separate consent before disclosing to third parties for purposes not integral to the service, such as advertising, plus a written retention policy and security program | General-audience positioning, a minimum age in the terms, a neutral age gate where children are plausible, deletion on discovery |
| Children elsewhere | EU digital consent age is 13 to 16 depending on the member state; UK and several US states impose design codes on services likely to be accessed by minors | High-privacy defaults, no profiling or nudging of minors | Same as above; do not market to minors |
| Financial regulation | Holding or moving customer funds, issuing stored value, lending, giving investment advice, insurance distribution | Licensing (money transmission is state by state in the US), KYC and anti-money-laundering programs | Keep out of the flow of funds: let a licensed provider (the payment provider's marketplace product) hold and move money |
| GLBA and consumer reporting (US) | Providing financial products to consumers; supplying data used for credit, employment, insurance or tenancy decisions | Safeguards and privacy notices; consumer-reporting duties on accuracy, disputes and permitted purposes | Do not sell data for eligibility decisions |
| Student data (US) | Selling to schools or processing student records | Acting under the school's control; state laws ban advertising and profiling on student data | Avoid K-12 or accept school contract terms |
| Biometrics | Face, voice or fingerprint templates; Illinois has a private right of action with statutory damages, GDPR treats them as special-category | Written informed consent before capture, a published retention schedule | Use on-device platform biometrics that never send a template to the server |
| Telemarketing and SMS | Marketing texts or automated calls | Prior written consent in the US; see `consent-cookies.md` | Email only |

A B2B product is pulled into a sector regime by its customers: one hospital, bank or school
district as a customer imports their obligations through the contract. Decide deliberately
whether to serve them; if not, say so in the terms and the signup flow.

## Consumer law: renewals, cancellation and price display

These apply to sales to consumers (and in some places to small businesses). They are enforced
by regulators, card networks, app stores and class actions.

| Topic | Rule that holds across major markets | Jurisdiction specifics |
|---|---|---|
| Auto-renewal disclosure | State the price, billing period, that it renews, and how to cancel, clearly and next to the purchase button, before taking payment details | US federal law on online negative-option sales and many state laws; California's is the strictest |
| Consent | An affirmative act specific to the recurring charge; a pre-checked box or terms link is not it | Record it with the terms version |
| Confirmation | Email the terms and cancellation instructions after purchase | Required in the US states with renewal laws and by EU distance-selling rules |
| Free trials and intro prices | Disclose the post-trial price and date at signup; send a reminder before the first charge | Several US states and card network rules require the reminder |
| Annual plans | Send a renewal reminder ahead of the charge (commonly 15 to 45 days) | Required in several US states; expected in the UK |
| Cancellation | Online, in the same medium as signup, without a call, chat queue or retention maze; one save offer at most, with a visible way past it | Germany requires a labeled cancellation button on the site; EU law requires an online withdrawal function for distance contracts from 19 June 2026; the UK's DMCC Act subscription rules are expected to start in 2027 once secondary legislation is made, so check |
| Withdrawal right | EU and UK consumers get 14 days to withdraw from distance contracts | For digital services started immediately, obtain express consent to start and acknowledgment of the effect on the right; without it the consumer can withdraw and be refunded |
| Price display | Show consumers the total price including taxes and mandatory fees from the first screen | EU and UK: VAT-inclusive. US: California and a growing number of states ban drip pricing generally; the FTC's fees rule covers live-event tickets and short-term lodging |
| Order button | Label must make the payment obligation explicit ("Buy now", "Pay and subscribe") | EU requirement; "Continue" or "Start" is not enough |
| Discounts and urgency | A "was" price must be genuine; countdown timers and "only 2 left" must be true | EU: a discount must reference the lowest price of the prior 30 days |
| Reviews and testimonials | No fake, purchased or suppressed reviews; disclose incentives and affiliations | Banned by rule in the US and by EU and UK law |
| Price increases | Advance notice and a chance to cancel before the new price applies | Consent may be required for mid-term increases |

Default cancellation design: a "Cancel subscription" control in account settings, at most one
intermediate screen, cancellation effective at period end with access until then, and a
confirmation email. The card networks also monitor dispute rates, and a hard cancellation flow
converts would-be cancellations into chargebacks. Billing mechanics are in `0x:payments-billing`.

## Dark patterns

Regulators on both sides of the Atlantic treat manipulative design as an unfair practice, and
consent obtained through it as no consent. Audit the consent, pricing and cancellation flows for:

| Pattern | Looks like | Replace with |
|---|---|---|
| Asymmetric choice | Bright "Accept", gray text "decline"; one click to join, six to leave | Equal prominence and equal effort |
| Confirmshaming | "No thanks, I like paying more" | Neutral labels |
| Preselection | Pre-ticked add-ons, upsells or consents | Unticked by default |
| Sneaking | Fees added at the last step; a trial that silently converts | Total price up front; reminder before conversion |
| Obstruction | Cancellation by phone only, forced survey, hidden settings | Self-serve, optional survey after the fact |
| False urgency or scarcity | Resetting timers, invented stock counts | Only real deadlines |
| Nagging | Repeated prompts after a refusal | Remember the refusal |
| Misdirection | Double negatives, trick wording on toggles | Plain statements, on means yes |
| Forced action | Must accept marketing or tracking to use the service | Unbundle |

Test: would the choice distribution change if both options were presented identically? If the
design depends on that difference, it is the pattern.

## Accessibility law

Building accessible interfaces is `0x:accessibility`; this is the legal layer.

| Regime | Reaches | Standard used in practice |
|---|---|---|
| ADA Title III and state laws (US) | Businesses serving the US public; courts differ on web-only businesses, but demand letters and suits are filed in volume, concentrated in a few states, one of which allows statutory damages per violation | WCAG 2.1 AA |
| Public-sector procurement (US Section 508, state and local government rules) | Selling to government or publicly funded bodies | WCAG AA; buyers ask for an Accessibility Conformance Report on the VPAT template |
| European Accessibility Act | Since mid-2025: consumer-facing e-commerce, banking, e-books, telecoms, transport ticketing and certain devices sold in the EU, including by non-EU companies. Micro-enterprises providing services (under 10 people and under a small turnover ceiling) are exempt | EN 301 549, which incorporates WCAG 2.1 AA |
| UK Equality Act, Canadian provincial laws, others | Service providers generally | WCAG AA |

What to have in place at Launch for a consumer product: WCAG 2.2 AA as the stated target (it
contains the 2.1 AA criteria that EN 301 549 and US settlements cite; see `0x:accessibility`); automated checks in CI plus a manual keyboard and screen-reader pass of signup,
checkout and core flows; a public accessibility statement giving the target, known limitations,
a contact route and the date of the last review (the EAA requires information on how the
service meets the requirements); and a tracked backlog. Do not install an overlay widget as the
answer: overlays do not produce conformance, are named in complaints, and the FTC took action against
an overlay vendor in 2025 for claiming otherwise.

**A complaint or demand letter arrives.** 

1. Do not ignore it and do not reply substantively the same day. Preserve the letter and note
   deadlines; send it to a lawyer who handles these (many are template letters from repeat
   filers, and the response strategy differs by state and court).
2. Reproduce each alleged barrier on the named pages with the named assistive technology;
   record what is real.
3. Fix real barriers on the cited flows first, with dated commits, then run a broader audit.
   Prompt remediation strengthens every later position and in some courts can end the claim.
4. Do not publish claims of full compliance in response; update the accessibility statement
   honestly.
5. Counsel decides between contesting and settling. A settlement binds only that claimant, so
   remediation is the only durable defense. For a genuine user complaint without a lawyer,
   answer personally, fix it, and tell them when it is done.

## AI: transparency and the EU AI Act

Disclosure duties that apply to ordinary products with AI features:

- Tell people when they are talking to an AI system unless it is obvious from context. The EU
  AI Act requires it, and several US states have chatbot disclosure laws, some stricter for
  companion, health or sales bots. Default: label every chat or voice agent as AI at the start
  of the interaction and never let it claim to be human.
- Label AI-generated or manipulated images, audio and video that could pass as real
  (deepfakes), and AI-written text published to inform the public on matters of public
  interest unless a human reviewed it and takes editorial responsibility.
- Providers of systems that generate synthetic audio, images, video or text must mark outputs
  as AI-generated in a machine-readable way. A product generating such content on a model API is
  itself such a provider: keep the provenance metadata or watermark the model provider attaches,
  never strip it, and add marking where none exists.
- Emotion recognition or biometric categorization requires telling the people exposed to it.

Classifying a feature under the EU AI Act (reaches providers and deployers whose systems or
outputs are used in the EU):

| Tier | Examples | Duty |
|---|---|---|
| Prohibited | Manipulative or exploitative techniques causing harm, social scoring, untargeted face scraping, emotion inference at work or school, certain biometric categorization | Do not build; in force since early 2025 |
| High-risk | Listed uses: hiring and worker management, education admission and grading, credit scoring and access to essential services, insurance pricing for life and health, biometric identification, critical infrastructure, law enforcement and migration; and AI as a safety component of regulated products | Risk management, data governance, technical documentation, logging, human oversight, accuracy and robustness, conformity assessment, registration; deployers have their own duties |
| Transparency | Chatbots, generative content, emotion recognition | The disclosures above |
| Minimal | Spam filters, recommendations, most productivity features | None specific |

Rules for getting the classification right: classify by intended use, not by the model. A
narrow exemption exists for listed uses that only do preparatory or procedural tasks, but a
system that profiles individuals in a listed area is always high-risk. Building a product on
a model API makes the company the provider of an AI system (not of the general-purpose model,
whose obligations sit with the model developer) and its business customers deployers. All
providers and deployers owe AI literacy measures for staff. The Act applies in stages:
prohibitions and AI literacy since February 2025, transparency duties since August 2026 (a 2026
amending regulation moved output marking to December 2026), and high-risk duties, as amended in
2026, from December 2027 for listed uses and August 2028 for AI in regulated products. Confirm
against the current consolidated text before planning. Write a one-page classification memo per AI feature and
keep it with the data map. Design of AI features is `0x:ai-features`.

## EU Cyber Resilience Act

| Product | Covered? |
|---|---|
| Pure SaaS accessed in a browser | Generally no (other EU security laws address services) |
| Installable software made available commercially in the EU: desktop and mobile apps, CLIs, agents, SDKs, browser extensions, firmware, self-hosted editions | Yes |
| Cloud back end that a covered product needs in order to function | Covered as part of that product |
| Open-source software developed and supplied outside commercial activity | No; organizations that steward open-source projects have a light regime; monetizing the software itself brings it in |

Duties for a manufacturer: security requirements by design and by default, no known exploitable
vulnerabilities at release, a software bill of materials, a vulnerability handling and
coordinated disclosure process, free security updates for a declared support period (at least
five years unless the product's life is shorter), technical documentation, a declaration of
conformity and CE marking; stricter assessment for listed important and critical product
classes. Reporting of actively exploited vulnerabilities and severe incidents through ENISA's
single reporting platform has applied since 11 September 2026: an early warning within 24
hours, a notification within 72 hours, then a final report. The other obligations apply from
11 December 2027. If a downloadable product is sold in the EU, the reporting process is needed
now and the SBOM and vulnerability process before 2027; see `0x:web-security` (`supply-chain.md`).

## Sanctions and export controls

Sanctions are strict liability in the US: intent is not required, and free plans count as
providing a service.

- **Embargoed territories.** The US embargoes a short list of countries and regions outright
  (in 2026: Cuba, Iran, North Korea and the Russian-occupied Crimea, Donetsk and Luhansk
  regions; most Syria sanctions were lifted in 2025, though export controls and listed parties
  remain). EU and UK programs differ: they do not embargo Cuba, and EU law can forbid complying
  with some US Cuba rules. All three restrict Russia and Belarus extensively, including bans on
  supplying certain business software and services. A non-US company meets US rules in practice
  through US payment providers, clouds and dollar payments. The lists change; read the current ones.
- **Listed parties.** No dealings with persons and entities on the sanctions lists (in the US,
  the SDN list), or entities majority-owned by them, anywhere in the world.
- **Controls proportionate to stage.** Launch: block signup and access from embargoed
  territories by IP geolocation and by billing or declared country; exclude them from country
  pickers; state the restriction in the terms. The payment provider screens payers, which does
  not cover free users or discharge the company's own duty. Scale or enterprise sales: screen
  customer and beneficial-owner names against the consolidated lists at onboarding and
  periodically, through a screening API; keep the results.
- **A hit.** Stop service, do not refund or move funds without advice, do not tip off beyond
  what counsel advises, and call a sanctions lawyer; blocked property may have to be reported.
- **Export controls.** Software with encryption is subject to US export rules even when the
  cryptography is standard; most commercial and open-source software qualifies for broad
  exceptions, sometimes with a notification or classification step, and app stores ask about
  it at submission. Advanced computing, surveillance and other dual-use capabilities are
  tightly controlled, and US rules on advanced AI chips and model weights have changed
  repeatedly since 2025: get advice before selling them abroad.

## Ask the user

- **Will any customer be a healthcare provider, bank, school or government body?** Each imports
  a regime. Default: no; prohibit regulated data in the terms until deliberately supported.
- **Are buyers consumers, businesses or both, and in which countries?** Consumer law attaches
  to consumer sales. Default: apply the consumer rules above to all self-serve plans.
- **Could children plausibly use the product?** Decides age gating and design duties. Default:
  adults only, stated in the terms, no child-directed content or marketing.
- **Does any AI feature score, rank or decide about people (hiring, credit, education,
  insurance)?** That is the high-risk line. Default: no; keep a human decision-maker and a
  classification memo.
- **Is anything installable shipped to EU customers?** Triggers the Cyber Resilience Act.
  Default: SaaS only.
- **Is there any reason to serve restricted regions?** Default: block them.
