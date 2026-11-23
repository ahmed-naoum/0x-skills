# Terms, privacy policy and platform duties

Read this when: writing or updating terms of service, a privacy policy or an acceptable use
policy; building the acceptance flow; changing terms for existing users; hosting user content
and receiving takedown notices; or a subpoena, police request, regulator letter or legal threat
arrives.

## The document set by stage

| Stage | Publish | Source |
|---|---|---|
| Prototype | Privacy policy if any personal data is collected (a waitlist email counts) | Template, edited to the real data flows |
| Launch | Terms of service, privacy policy, cookie information if applicable, acceptable use rules, refund and cancellation terms, DPA for B2B, legally required company details | Template or generator for the frame; lawyer review of the terms before meaningful revenue |
| Scale | Negotiable master agreement and order form, SLA, security overview, subprocessor page, copyright and content policies if hosting user content | Lawyer-drafted |

Several countries require an imprint: company name, address, contact and registration details
on the site (Germany's is the strictest). EU consumer sellers must show identity and contact
details before purchase.

## Privacy policy: written from the data map

The policy is a public statement of fact. Regulators rarely punish a missing clause; they punish
statements that are false. Generate it from the data map in `privacy-law.md` and update both in
the same change.

Required content, covering GDPR and the US state laws together:

| Item | Detail |
|---|---|
| Who | Legal entity, contact, EU or UK representative and DPO if any |
| What and from where | Categories of data, and sources when not collected from the person |
| Why and on what basis | Each purpose with its lawful basis; the legitimate interest named |
| Who receives it | Categories of recipients, with a link to the subprocessor list; whether anything is sold or shared for advertising |
| Where | International transfers and the mechanism |
| How long | Retention periods or the criteria, per category |
| Rights and how to use them | Access, deletion, correction, portability, objection, withdrawal of consent, opt-out of sale and sharing, appeal, complaint to a regulator, no retaliation |
| Other | Automated decision-making, whether providing data is required, children, how changes are announced, effective date |

Rules that prevent the usual failures:

- No absolutes that are not literally true: "we never share your data" (there are vendors),
  "bank-level security", "anonymous" for pseudonymous data, "we delete everything immediately".
- A template policy describing practices the product does not have is as wrong as one that
  omits practices it does have. Delete every paragraph that does not apply.
- For a B2B product, state that for customer workspace data the customer is the controller and
  its policy governs; the product's policy covers account holders and site visitors.
- A new tracker, vendor category or purpose is a policy change. Add a policy check to the pull
  request template for any change touching data collection.
- Date and archive every version.
- Plain language, layered: a short summary on top, detail below. A policy is also read by
  enterprise reviewers; precision sells.

## Terms of service: the clauses that carry weight

| Clause | Sensible starting position |
|---|---|
| Who contracts, eligibility | The legal entity; minimum age; authority to bind an organization |
| The service and changes to it | Right to modify features; no promise of specific future features |
| Fees, renewal, taxes, refunds | Mirrors the checkout disclosures in `sector-consumer-rules.md` |
| Customer data and IP | Customer owns its content; a license limited to operating the service; the company owns the software and feedback; say explicitly whether content is used to train models |
| Acceptable use | Incorporates the AUP; right to suspend for violations |
| Confidentiality and data protection | Incorporates the DPA |
| Warranty disclaimer | Service provided as is, to the extent the law allows; in the US the disclaimer must be conspicuous |
| Limitation of liability | No indirect or consequential damages; total liability capped at fees paid in the preceding 12 months (a small fixed amount for free plans) |
| Indemnity | Customer indemnifies for its content and misuse; B2B buyers will ask for an IP indemnity in return |
| Term, termination, effect | Either side may end; data export window; survival of key clauses |
| Governing law and disputes | Home jurisdiction and courts; arbitration and class waiver is a US-specific choice with its own risks, for a lawyer to decide |
| Changes to the terms | Notice mechanism as described below |

Limits on what terms can do:

- Consumer protection law overrides the contract. EU and UK consumers keep their home-country
  mandatory rights and courts whatever the terms say; unfair terms are void; liability for
  death, personal injury, fraud and (in many countries) gross negligence or intent cannot be
  excluded. A US-style cap written in capitals does not travel unchanged.
- B2B terms are mostly enforced as written, which is why enterprise buyers negotiate the cap,
  the data-breach carve-outs and the indemnities. Decide the fallback positions in advance.
- A liability cap protects only if the terms were validly accepted.

## Acceptance: make it enforceable and provable

| Method | Enforceability |
|---|---|
| Clickwrap: an unticked checkbox, or a clear statement directly at the signup button ("By creating an account you agree to the Terms and Privacy Policy") with visible links | Regularly upheld |
| Sign-in wrap with small gray text far from the button | Litigated; outcomes depend on the design |
| Browsewrap: a footer link and "by using this site you agree" | Regularly rejected |

Do not ask for "agreement" to the privacy policy as consent to processing: link it as a notice.
Acceptance of terms and consent to marketing or tracking are separate controls.

Record for every acceptance:

```sql
create table terms_acceptance (
  user_id      uuid        not null references users(id),
  document     text        not null,            -- 'terms' | 'dpa' | 'aup'
  version      text        not null,            -- dated version identifier
  accepted_at  timestamptz not null default now(),
  ip           inet,
  user_agent   text,
  primary key (user_id, document, version)
);
```

Keep every published version retrievable by its identifier (a file per version in the
repository, served at a stable URL), and keep a screenshot or the component version of the
signup screen as it looked. In a dispute the questions are which text, shown how, accepted when.
For organizations, record which user accepted and that they affirmed authority; for enterprise
deals the signed order form governs and should say it overrides the online terms.

## Changing terms

| Change | Process |
|---|---|
| Typos, clarifications, a new feature's description | Update, bump the version, changelog entry |
| Material: pricing, liability, dispute resolution, new uses of data, reduced rights | Advance notice by email and in-app (30 days is the common commitment), a summary of what changed, and affirmative re-acceptance at next login for the significant ones; a right to cancel before the change applies |
| Anything applied to an existing paid term | Usually takes effect at renewal unless the customer agrees |
| New use of data already collected | Not fixable by a policy edit: US regulators treat retroactive changes as deceptive without affirmative consent, and GDPR requires a compatible purpose or new consent |

A clause saying terms may change at any time with continued use as acceptance is weak in the US
and often void against EU consumers. Negotiated B2B contracts change only by written amendment.

## What to template and when to pay a lawyer

| Do it from a template or generator | Pay a lawyer |
|---|---|
| Privacy policy for a standard SaaS (driven by the data map) | Terms before material revenue or the first enterprise deal |
| Cookie information, accessibility statement, AUP | Liability, indemnity, arbitration and governing-law choices |
| Customer DPA from a recognized standard form | A customer's redlines on liability or data protection |
| Subprocessor list, security overview | Anything regulated: health, finance, children, marketplaces holding funds |
| DMCA policy and designated-agent registration | Any legal demand, regulator contact, lawsuit threat or breach notification |
| | Consumer subscriptions sold in several countries; user-generated content at scale |

A fixed-fee review of a template-based set is the efficient purchase: arrive with the data map,
the pricing and renewal model, the countries served, and the three risks that matter most. Do
not copy a competitor's terms: they encode another company's risks and jurisdiction, and are
copyrighted.

## Acceptable use policy and enforcement

List prohibited conduct concretely for the product: illegal content, infringement, malware and
attacks, spam and unsolicited bulk messaging, scraping or load beyond limits, circumventing
limits or reselling without permission, harassment, sexual content involving minors, regulated
data the service is not built for, and use to build a competing model or product if that is the
position. Reserve the right to remove content and suspend accounts.

Enforcement that holds up: a graduated ladder (warning, feature restriction, suspension,
termination) with immediate action reserved for severe harm; a written reason given to the user
for each action; an appeal route to a human; an internal log of report, evidence, decision and
decider; consistent treatment of similar cases; a data export window on termination unless the
content itself is unlawful. Abuse detection mechanics are in `0x:auth-identity`
(`abuse-defense.md`).

## Takedowns and duties for user-generated content

Hosting content that users post brings notice-handling duties from the first upload.

**US copyright (DMCA safe harbor).** Protection from liability for users' infringement depends
on formalities: designate an agent with the Copyright Office (online, small fee, periodic
renewal) and publish the same contact on the site; adopt and apply a repeat-infringer policy;
remove or disable access expeditiously on a notice that contains the required elements
(identification of the work and the material, contact details, good-faith and accuracy
statements, signature); notify the uploader; on a valid counter-notice, restore the material
after 10 and within 14 business days unless the claimant files suit. Log everything. Do not
adjudicate fair use informally: follow the procedure.

**EU Digital Services Act.** Applies to any intermediary offering services to EU users,
whatever its size or location:

| Tier | Duties |
|---|---|
| All intermediaries, including hosting | A single point of contact for authorities and for users; an EU legal representative if not established in the EU; terms that describe moderation rules and tools; act on orders from authorities |
| Hosting services | An easy electronic notice mechanism for illegal content; timely, diligent decisions; a statement of reasons to the affected user for each restriction; report suspected serious crimes threatening life or safety |
| Online platforms (content disseminated to the public) | Internal complaint handling, out-of-court dispute options, trusted flaggers, measures against repeat misuse, ad and recommender transparency, no dark patterns, protections for minors, transparency reports. Micro and small enterprises (under 50 staff and a low turnover ceiling) are exempt from this tier, not from the two above |
| Marketplaces | Trader identification and traceability |
| Very large platforms | Not a small-company concern |

**Other regimes to check when hosting content.** The UK Online Safety Act applies to
user-to-user and search services with UK users regardless of size: illegal-content and
children's risk assessments, proportionate safety measures, reporting and complaints routes.
US providers that become aware of child sexual abuse material must report it to the national
clearinghouse and preserve it; never review such material beyond what the report requires. EU
rules allow authorities to order removal of terrorist content within one hour. Several
countries have their own notice regimes for defamation and privacy.

Minimum build for any product with public user content: a report button on each item, an
intake queue with timestamps, the decision log, templated reasons, an appeal link, a published
policy, and a `legal@` or `abuse@` contact that is monitored.

## Legal demands, subpoenas and regulator letters

Sequence, the same for every type:

1. Do not delete or alter anything related. Suspend relevant retention jobs (legal hold; see
   `data-subject-requests.md`).
2. Record receipt: date, channel, sender, deadline. Do not reply substantively yet, and do not
   ignore it. Deadlines in court and regulator documents are real.
3. Verify authenticity out of band (call the court or agency through a number found
   independently). Fake law-enforcement requests are a known way to obtain user data.
4. Send it to counsel. Counsel checks jurisdiction and validity, objects to or narrows
   overbroad requests, and drafts the response.
5. Disclose the minimum that the instrument compels, through a secure channel, and log it.
6. Notify the affected user or customer before disclosure unless legally prohibited; DPAs
   usually require telling the customer.

| Document | What it is | Note |
|---|---|---|
| Lawyer's demand or cease-and-desist letter | A private claim, not an order | No duty to comply; do not admit or apologize in writing; counsel answers |
| Civil subpoena | Compels records or testimony | Can be objected to or narrowed; US law restricts disclosing the contents of users' communications to civil litigants |
| Law-enforcement request | Varies from informal to a warrant | Require the proper legal process for the data type; content generally needs a warrant in the US. Foreign authorities normally must use formal cross-border channels. Emergency requests involving risk to life may be honored after verification |
| Preservation request | Keep specified data for a period | Preserve; it does not authorize disclosure |
| Regulator inquiry | Questions or an audit from a data protection, consumer or sector authority | Calendar the deadline, engage counsel immediately, answer accurately and narrowly, one point of contact, ask for an extension early if needed |
| Gag or confidentiality order | Prohibits telling the user | Follow it; counsel may challenge it |

Publish a short law-enforcement guideline once requests recur: what process is required for
which data and where to send it. Enterprise customers ask how demands are handled; the answer
is this procedure.

## Ask the user

- **Are customers consumers, businesses or both, and in which countries?** It decides how far
  US-style disclaimers and caps hold. Default: write for both, with a consumer-rights saving
  clause, and get the terms reviewed.
- **Which legal entity contracts, and under which governing law?** Default: the operating
  company and its home jurisdiction.
- **Can users post content that others see?** It triggers the takedown and DSA duties.
  Default: if yes, build the report-and-decide loop before public launch.
- **Is customer content ever used for training or product improvement?** The terms, policy and
  DPA must agree. Default: no, stated explicitly.
- **Is there a lawyer who has reviewed the terms, and one to call when a demand arrives?**
  Default: template now, fixed-fee review before the first enterprise contract or paid
  consumer launch.
