# GDPR, CCPA and privacy fundamentals

Read this when: working out which privacy laws reach the product, building or updating the data
map, picking a lawful basis, deciding controller versus processor, or facing a transfer question,
a DPIA, a representative or DPO question, or a breach notification clock.

## Which laws reach the product

Reach is set by where the people are, not where the company is.

| Law | Reaches the product when | Small-company exemption |
|---|---|---|
| EU GDPR | Established in the EU, or offering goods or services to people in the EU, or monitoring their behavior (Art. 3) | None. No revenue or headcount floor |
| UK GDPR | Same test for people in the UK | None |
| CCPA/CPRA (California) | For-profit, does business in California, and meets one threshold: worldwide annual gross revenue above $25 million adjusted for inflation every other year ($26,625,000 from 2025; check the current figure), or personal information of 100,000+ California consumers or households, or 50%+ of revenue from selling or sharing personal information | Yes: below all thresholds it does not apply |
| Other US state privacy laws | Usually a count of state residents whose data is processed (commonly 100,000, lower in small states; a few have no count at all) | Usually yes; check each state |
| Sector laws (HIPAA, COPPA, GLBA) | By data type and customer, not size | See `sector-consumer-rules.md` |

Signals that the product "targets" the EU: EU languages or currencies, EU shipping, EU customer
logos, ads aimed at EU countries, a `.de` or `.fr` domain. A site that is merely reachable from
the EU is not targeting it. A B2B SaaS with one EU customer is bound by the processor duties
through the DPA it signs with that customer, even where GDPR does not reach it directly.

Working rule for a solo founder: build to GDPR once and treat US state laws as a delta (opt-out of
sale and sharing, Global Privacy Control, a few notice items). GDPR is the stricter structure and
is what B2B buyers' questionnaires ask about. Even below the CCPA thresholds, the FTC and state
attorneys general enforce "unfair or deceptive" practices: doing something the privacy policy
says is not done is the most common way a small US company gets into trouble.

## The data map

The data map is the one artifact every other duty hangs off: the privacy policy, the DPA annex,
request handling, retention, breach scoping and vendor review are all read from it. The GDPR
calls it the record of processing activities (Art. 30). The exemption for organizations under 250
people is narrow (it fails if processing is not occasional), so assume the record is required.

Keep it as a table in the repository (`docs/privacy/data-map.md` or a spreadsheet), one row per
purpose, not per database table:

| Column | Example |
|---|---|
| Purpose | Account and login |
| Data categories | Email, name, password hash, IP, session tokens |
| Data subjects | Customers' end users |
| Role | Controller (own signups) / Processor (customer workspace content) |
| Lawful basis | Contract |
| Systems and vendors | Postgres (EU region), auth provider, email provider |
| Location / transfer mechanism | EU; US vendor under DPF or SCCs |
| Retention | Life of account plus 30 days |
| Access | App, support role |

Build it from the code, not from memory:

1. List tables and columns holding personal data; tag them in the schema (a comment or a `pii`
   naming convention) so the map can be regenerated.
2. List every outbound destination: SDKs in the client bundle, server-side API clients, webhooks,
   log drains, error trackers, analytics, email, support, CRM, LLM providers.
3. Find the shadow copies: logs, error-tracker payloads, analytics event properties, search
   indexes, caches, the warehouse, backups, exported CSVs, spreadsheets and inboxes.
4. Update the map in the same pull request that adds a field, a vendor or a purpose. A map that
   is updated quarterly is wrong for three months at a time.

Personal data is wider than names and emails: IP addresses, device and cookie identifiers, user
IDs, precise location, free-text fields, support transcripts and anything linkable to a person
count. Pseudonymized data (hashed email, internal ID) is still personal data; only data that
cannot be re-linked by anyone is anonymous.

## Collect less

Minimization is the cheapest control: data that is never collected cannot be breached,
requested, transferred or retained too long.

- For each field in a form or event, name the feature that reads it. No reader, no field.
- Do not collect date of birth when an "over 18" checkbox is enough, a full address when a
  country is enough, or a phone number "for later".
- Avoid special categories (health, biometrics, religion, sexual orientation, ethnicity, union
  membership, political views) and government identifiers unless the product is about them: they
  raise the lawful-basis bar, breach consequences and DPIA likelihood.
- Free-text fields and file uploads collect whatever users type. Say what not to enter, and
  treat the contents as potentially sensitive.
- Keep personal data out of URLs, logs, analytics properties and error payloads; scrub at the
  SDK (`beforeSend`-style hooks) and at the logger.
- Truncate or drop IP addresses where only a country is needed. Store derived values (country,
  age band), not the raw input.
- Prefer event properties that describe the action (plan, feature) over ones that describe the
  person.

## Lawful basis

Each purpose needs a lawful basis, chosen before collection and stated in the privacy policy.
Switching later, especially from consent to legitimate interests after a refusal, is not
accepted by regulators.

| Purpose | Usual basis | Notes |
|---|---|---|
| Providing the service, billing, support | Contract | Only what the service the user signed up for actually needs |
| Invoices, tax records, sanctions screening | Legal obligation | Cite the law in the record |
| Security, fraud prevention, debugging, basic product metrics | Legitimate interests | Write a short balancing note: interest, necessity, impact, opt-out |
| B2B sales outreach, marketing to existing customers | Legitimate interests where the e-privacy rules allow | Channel rules in `consent-cookies.md` override |
| Marketing email to non-customers, non-essential cookies, ad targeting | Consent | Opt-in, specific, withdrawable |
| Special-category data | Explicit consent or another Art. 9 condition | In addition to an Art. 6 basis |
| Training models on user content | Not settled; consent or a carefully argued legitimate interest with opt-out | Get advice; see `0x:ai-features` |

Traps: "contract" does not stretch to analytics, ads or product improvement. Consent is the
wrong basis for anything the service cannot run without, because consent must be refusable and
withdrawable without losing the service. Consent bundled into terms acceptance is invalid.
Legitimate interests gives the person a right to object, so an objection path must exist.

## Controller or processor

Decide per data flow, not per company. A B2B SaaS is normally both.

| Flow | Role | Consequence |
|---|---|---|
| Content and end-user data customers put into their workspace | Processor | Act only on the customer's instructions; offer a DPA; forward data-subject requests to the customer; notify the customer of breaches |
| Account owners' login, billing and contact data | Controller | Own privacy policy, own lawful basis, own request handling |
| Website visitors, leads, marketing lists | Controller | Same |
| Product analytics on how customers use the app | Controller, if used for own purposes | Must be permitted by the DPA and disclosed |
| Consumer app users | Controller | All duties fall here |

The test is who decides why and how the data is used. Using customer content for own purposes
(training, benchmarking, advertising) turns a processor into a controller for that use and
breaks most DPAs unless it is carved out explicitly. Vendors are processors when they act only
on instructions (hosting, email delivery) and independent controllers when they use the data for
their own purposes (payment networks for fraud, ad platforms). In CCPA terms the processor
equivalent is a "service provider", and the status depends on specific contract terms being in
place; without them a disclosure can count as a "sale".

## US state duties and Global Privacy Control

When CCPA or a similar state law applies:

- Notice at collection and a privacy policy listing categories collected, sources, purposes,
  and categories disclosed, sold or shared; review at least every 12 months.
- Rights to know, delete, correct, and opt out of sale, sharing (cross-context behavioral
  advertising) and targeted advertising; a right to limit use of sensitive personal information.
- A "Do Not Sell or Share My Personal Information" link, or the combined "Your Privacy Choices"
  link, when any ad pixel or data-sharing arrangement exists. Loading an ad network's pixel that
  uses the data for its own targeting is generally treated as a sale or share.
- Honor Global Privacy Control as a valid opt-out of sale and sharing. California and a growing
  list of states require it, and regulators have enforced it against sites that ignored it.
- No retaliation or worse service for exercising rights; contracts with service providers.
- California's regulations in effect from 2026 add risk assessments, cybersecurity audits and
  automated decision-making duties for covered businesses, phased in over several years by size
  and activity; check which apply once a threshold above is met.

GPC arrives as a request header and a JavaScript property:

```ts
// server: header is "Sec-GPC: 1"
const gpc = request.headers.get("sec-gpc") === "1";
// client
const gpcClient = (navigator as any).globalPrivacyControl === true;
```

When the signal is present, do not load ad or sharing tags for that browser, and if the user is
logged in, persist the opt-out on the account so it applies on other devices. Do not show a
pop-up asking the user to reverse it. The simplest compliant position for a small product is to
do no selling or sharing at all, in which case the link is not needed and GPC has nothing to
switch off; say so in the policy.

## Breach notification

A personal data breach is any accidental or unlawful destruction, loss, alteration, disclosure
of, or access to personal data. A misdirected email and a lost unencrypted laptop both qualify,
not only an attacker. Containment and forensics belong to `0x:web-security`
(`logging-breach-response.md`); the clocks below run in parallel with them.

| Regime | Who is told | Deadline | Threshold |
|---|---|---|---|
| GDPR, controller | The lead supervisory authority if the company has an EU main establishment; without one, each authority whose residents are affected, and the ICO for UK data | 72 hours after becoming aware; give reasons if later, and report in phases if facts are incomplete | Unless unlikely to result in a risk to people |
| GDPR, controller | Affected individuals | Without undue delay | High risk to them; not needed if the data was unintelligible (properly encrypted, key not taken) |
| GDPR, processor | The controller (the customer) | Without undue delay; the DPA usually sets hours | Any breach of their data, no risk threshold |
| US states (all have a statute) | Affected residents; often the attorney general above a headcount; sometimes credit bureaus | "Without unreasonable delay"; a growing number set a fixed outer limit, commonly 30 to 60 days | Defined data elements (name plus SSN, license, financial account, often credentials, medical or biometric data); encryption is usually a safe harbor |
| Contracts | Customers, payment processor, insurer | Whatever was signed, often 24 to 72 hours | Often "suspected" incidents too |

Sequence once a breach is suspected:

1. Write down the time of awareness; the 72 hours run from reasonable certainty that personal
   data was affected, not from the end of the investigation.
2. Call the cyber insurer before hiring anyone: many policies require their panel counsel and
   forensics firm, and pay for them.
3. Scope from the data map: which categories, how many people, which countries and states,
   which customers are controllers.
4. Decide notification with counsel. Failing to notify a reportable breach is itself an
   infringement that regulators fine; over-notifying a non-reportable event has its own cost. Notify processor-side customers first, since their
   clock starts when they hear.
5. Record every breach, including those not notified, with the facts, effects, decision and
   reasoning. Regulators ask for this register.

A notice to a regulator states the nature of the breach, categories and approximate numbers of
people and records, likely consequences, measures taken, and a contact point. A notice to people
says the same in plain language plus what they should do.

## Transfers and data residency

A transfer happens when personal data from the EU or UK is sent to, or accessible from, a
country without an adequacy decision. Remote access by a US support engineer to an EU database
is a transfer.

| Destination | Mechanism |
|---|---|
| Adequate country (the Commission's list includes the UK, renewed in December 2025 until 2031, Switzerland, Japan, Canada for commercial organizations, and others; check the current list) | None needed |
| US recipient certified under the EU-US Data Privacy Framework | Adequacy applies; check the recipient's active listing on the official DPF site. The EU General Court upheld the framework in September 2025 and an appeal to the Court of Justice is pending, so keep SCCs as the fallback in the contract |
| Anyone else | Standard Contractual Clauses (2021 set, the module matching the roles) plus a transfer impact assessment; for UK data the UK addendum or IDTA |

Vendor-side mechanics are in `vendors-dpas.md`. When a customer asks for "EU data residency",
find out which promise they need, because they differ in cost by an order of magnitude:

1. Storage at rest in the EU: choose EU regions for database, object storage, backups and logs.
   Cheap if done at project creation, a migration afterwards.
2. Processing in the EU: every subprocessor that sees the data (email, error tracking, LLM,
   support desk) must also offer an EU region. This is where most promises quietly fail.
3. No access from outside the EU, or no US-owned provider: needs EU-based staff and EU-owned
   infrastructure. Do not promise it without restructuring.

State on the trust page exactly which of these holds, per data category. Promising "data never
leaves the EU" while error payloads flow to a US-hosted tracker is a misrepresentation.

## DPIA

A data-protection impact assessment is required before processing likely to result in high risk.
Rule of thumb from regulator guidance: two or more of these means do one: scoring or profiling,
automated decisions with legal or similar effect, systematic monitoring, special-category or
highly personal data, large scale, combining datasets, vulnerable people (children, employees,
patients), novel technology (including many AI uses), or processing that blocks access to a
service. National regulators publish lists of always-required cases.

Keep it to a few pages: what is processed and why; why it is necessary and proportionate and what
less intrusive design was rejected; risks to people (not to the company) rated by likelihood and
severity; mitigations and residual risk; sign-off and review date. If residual risk stays high,
the regulator must be consulted before launch. Enterprise customers also ask for help with their
own DPIA; a prepared product description of data flows and safeguards answers most of it.

## EU or UK representative, and DPO

- **Representative (Art. 27).** A company with no EU establishment that is caught by GDPR
  through targeting or monitoring must appoint a representative in a member state where its data
  subjects are, unless processing is occasional, involves no large-scale special-category data
  and is low risk. Ongoing SaaS for EU users is not occasional. Commercial representative
  services exist for a modest annual fee; name the representative in the privacy policy. UK GDPR
  Art. 27 sets the same duty for UK users of a company with no UK establishment; confirm the
  current ICO guidance before appointing, since removing it has been proposed before.
- **DPO (Art. 37).** Mandatory when core activities involve large-scale regular and systematic
  monitoring of people, or large-scale special-category data, or for public bodies. Some member
  states add their own triggers (Germany's is based on the number of staff regularly handling
  personal data). Most early SaaS products do not need one. Do not give anyone the title "DPO"
  casually: the role carries statutory independence and duties once claimed. Publish a
  `privacy@` contact instead.

## Skip until later

- Prototype: a one-page data map and minimization. Nothing else until real users exist.
- Launch: data map, privacy policy, lawful bases, DPAs with vendors, a breach contact list and
  register, GPC handling if any ad tags are present.
- Scale: DPIA process, representative, transfer assessments on file, regional hosting, counsel
  on retainer.
- Do not buy binding corporate rules, a certification seal, or an outsourced DPO to look serious.

## Ask the user

- **Where are the users and customers, now and in the next year?** It decides which laws apply.
  Default: assume EU, UK and California users exist for any public product.
- **Is the product B2B (customers bring other people's data), B2C, or both?** It sets the
  controller and processor split. Default: both roles, as in the table above.
- **Does the product handle health, children's, biometric, financial or location data?** These
  bring sector laws and DPIAs. Default: no, and block such use in the terms if it is not intended.
- **Is any data sold, shared for advertising, or used to train models?** It triggers opt-out
  links, consent and DPA carve-outs. Default: no selling or sharing; no training on customer
  content.
- **Is there cyber insurance and a privacy lawyer to call?** A breach is the wrong moment to
  shop. Default: none; recommend identifying both at Launch.
