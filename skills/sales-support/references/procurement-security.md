# Procurement and security questionnaires

Read this when: a prospect sends a security questionnaire or asks for SOC 2, a vendor portal or
supplier form arrives, the buyer's procurement team joins the deal, an RFP lands, or deciding
which enterprise feature (SSO, audit log, data residency) to build next.

## How enterprise buying actually runs

| Track | Owner at the buyer | What they need from you | Typical blocker |
|---|---|---|---|
| Business decision | Champion, economic buyer | Business case, proposal | Priority |
| Security review | Security or third-party-risk team | Questionnaire, reports, pentest | No SOC 2, vague answers |
| Legal | Counsel | Redlines, DPA | Liability, data terms |
| Procurement | Sourcing | Commercial negotiation, sometimes competing bids | Discount demand, supplier policy |
| Supplier onboarding | Procurement operations, accounts payable | Tax forms, bank details, insurance, portal registration | Missing documents |
| Purchase order | Finance | PO issued against the signed contract | Supplier not set up |

Run the tracks in parallel. At qualification ask: "What does your process look like for a new
vendor of this size, and what happened the last time?" Put every track into the mutual close
plan (`discovery-demos.md`). Handled one after another, they multiply the cycle length.

- Procurement is often measured on savings: expect a discount request late, after the business
  already agreed the price. Keep a planned concession (payment terms, a small multi-year discount)
  and let the champion defend the price internally.
- Many organizations let purchases under a spending threshold skip full procurement or go on a
  corporate card. Ask what the threshold is; a first deal under it, then expansion, can save months.
- Risk teams tier vendors by data access. A tool that holds no personal or confidential data gets
  a lighter review; asking for less data (no personal data, read-only scopes) can move you down a tier.
- Budgets follow the fiscal year. A deal that misses the budget-setting window can slip a year.
- Enterprise cycles commonly run several months; plan cash and pipeline coverage for that.

## Security and compliance pack before the first enterprise deal

Build it before it is asked for. Answering a first questionnaire from scratch takes days and
stalls the deal while the buyer's interest cools.

| Item | Content | When |
|---|---|---|
| Security overview, 2 to 4 pages | Hosting provider and regions, architecture diagram, encryption in transit and at rest, tenant isolation, staff access control and MFA, customer SSO, logging and monitoring, backups and tested restores, vulnerability management, secure development (review, CI checks, dependency scanning), incident response, continuity, staff onboarding and offboarding | Launch |
| Policies | Information security, access control, incident response, continuity and recovery, vendor management, retention and deletion, acceptable use | Launch; short and actually followed |
| Subprocessor list and DPA | Owned by `0x:privacy-compliance` | Launch |
| Penetration test | Recent independent test, summary or attestation letter, findings fixed | Before the first enterprise deal |
| Pre-filled standard questionnaire | CAIQ or SIG Lite | Before the first enterprise deal |
| SOC 2 Type II or ISO 27001 | Report shared under NDA; bridge letter covering the gap since the report period | When its absence blocks deals of material value (`0x:privacy-compliance` runs it) |
| Certificate of insurance | Cyber and technology errors and omissions | Before the first enterprise contract |
| Uptime record | Public status page with history | Launch |

- Publish a trust page: public overview plus NDA-gated downloads. Trust-center products exist
  (Vanta, Drata, SafeBase and others); at Launch a page and a shared folder are enough.
- Everything in the pack must be true today, because answers and documents get attached to the
  contract as representations. "Planned, target date Q3" is an acceptable answer; a false "yes" is
  a liability and, after a breach, evidence against you.
- Before SOC 2 exists, a clear overview, real policies, a pentest letter, a pre-filled CAIQ and a
  call between their reviewer and the person who built the system carry many mid-market reviews.
- Underlying controls (MFA everywhere, least-privilege access, logging) → `0x:web-security`.

## Completing a questionnaire from an answer library

Common formats: SIG Lite and SIG Core (Shared Assessments), CAIQ (Cloud Security Alliance),
HECVAT (higher education), VSA, custom spreadsheets of a few dozen to several hundred questions,
and third-party-risk portals.

1. Ask for the questionnaire at qualification, not after the verbal yes. Ask whether the trust
   pack or a completed CAIQ or SIG Lite can replace it; many reviewers accept.
2. Answer from the library: one canonical answer per control, with an evidence link, an owner and
   a last-reviewed date, in a spreadsheet or the trust tool.
3. Answer exactly what is asked, briefly and specifically. Example shape: "Yes. Customer data is
   encrypted at rest by the managed database service and in transit with TLS 1.2 or higher."
   Volunteering extra detail widens scope and invites follow-ups.
4. Use "No" with the compensating control and a dated plan, "Partial" with an explanation, "N/A"
   with the reason. Never a convenient "Yes".
5. The founder or the engineer who knows the system verifies every new or changed answer, then
   it enters the library.
6. Return it within about a week (rule of thumb); speed reads as maturity.
7. Log questions that block or recur; they feed the build decision below.

AI drafting from the library is fine for speed, but every answer is checked by someone who knows
it is true: a wrong answer is a misrepresentation, not a typo. Review the library quarterly and
after any architecture or vendor change. When the reviewer returns findings with remediation
requests, agree only dates that can be met and add them to the obligation register
(`proposals-contracts.md`).

## Which enterprise requirement to build next

Keep a blocker log: requirement, deal, annual value, stage, hard blocker or preference, whether a
competitor has it, date. Rank by blocked value times the probability that building it actually
closes the deal, against cost. Test whether a blocker is real: "If we had SAML SSO by June, would
you sign at this price?" and ask for a conditional order form or a fee. A question in a
questionnaire is a preference until a buyer says it blocks signature.

| Requirement | Commonly demanded by | Notes |
|---|---|---|
| SSO (SAML or OIDC) | Mid-market and up | Usually the first; place it in a higher plan (`0x:pricing-monetization`); build → `0x:auth-identity` |
| Roles and permissions | Teams beyond a handful of users | → `0x:auth-identity` |
| Audit log | Security reviews | Append-only, exportable, admin-visible |
| SOC 2 Type II | Enterprise security teams | Months of observation; start before the deal that needs it |
| SCIM provisioning | Large organizations with an identity provider | → `0x:auth-identity` |
| Data residency | EU enterprise and public sector | Expensive: a separate deployment to run forever |
| Contractual SLA with credits | Enterprise legal | Only once uptime is measured (`0x:site-reliability`) |

Do not build for one prospect unless they pay for it or it is on the path for the whole segment.
Moving upmarket is a strategy decision; one large logo can bend the roadmap for a year.

## Vendor portals, tax and insurance forms

Large buyers onboard suppliers through procurement systems (SAP Ariba, Coupa, Jaggaer, Oracle and
others). Registration is the prerequisite for a PO and for payment, so start it the day the deal
reaches contracting, in parallel with legal.

Keep a vendor kit in one folder, current:

| Item | Notes |
|---|---|
| Legal entity name, registration number, address | Exactly as on the contract and invoices |
| Tax forms | US buyers: Form W-9 for a US entity, Form W-8BEN-E for a non-US entity (with any treaty claim); VAT number for EU buyers |
| Bank details | On letterhead or a bank-issued letter |
| Certificate of insurance | General liability, technology errors and omissions, cyber; buyers often set minimum limits and ask to be named as additional insured, which the broker can issue |
| Security pack | As above |
| Attestations | Supplier code of conduct, anti-bribery, sanctions, modern-slavery statements: read them and sign only what is true |
| Contacts | Sales, billing, security, legal |

- Business email compromise targets supplier bank details. Never change bank details on the
  strength of an email in either direction; confirm by phone on a known number, and tell buyers
  you will never change them by email.
- Some supplier networks charge for premium supplier accounts; the free tier is normally enough
  to receive POs and submit invoices. Check before accepting a paid plan.
- Get insurance quotes before the first enterprise contract. If the buyer's minimums exceed what
  is affordable, negotiate the requirement in the contract (`proposals-contracts.md`).
- One owner and one inbox for portals: they send renewal requests for expiring documents, and the
  certificate of insurance renews every policy year.

## Deciding whether to answer an RFP

An RFP the vendor first hears about at publication was often written around an incumbent or a
preferred vendor, and a response costs days to weeks.

| Question | If the answer is no |
|---|---|
| Did we know the buyer or the project before it was issued? | Strong reason to decline |
| Do we meet every mandatory requirement? | Decline |
| Can we ask questions in the clarification window and get real answers? | Lower odds |
| Does the contract value repay the effort at a realistic win rate? | Decline |
| Do we fit the scoring (price weight, references, certifications)? | Decline, or partner with a vendor who fits |

If the answer is go:

- Submit clarification questions within the window; the answers reveal which requirements are soft.
- Follow the structure, format and deadline exactly. Late or non-compliant responses are often
  excluded unread. Public-sector processes forbid contact outside official channels.
- Answer every requirement in a compliance matrix (Yes, Partial, Roadmap, No), honestly.
- Open with an executive summary about their outcomes, not the company history.
- Reuse the answer library; spend the effort on the summary and the differentiating requirements.
- Price in their template, within pricing policy. Ask for a debrief afterward, win or lose.

Declining politely, with a reason and an offer of a smaller pilot or a conversation before the
next cycle, often earns the early involvement that wins the next one.

## Ask the user

- **Which assurance exists: SOC 2, ISO 27001, a pentest?** Decides what can be sent today.
  Default: a pentest and real policies before the first enterprise deal; SOC 2 when it blocks
  material revenue.
- **What customer data, especially personal data, does the product hold?** Sets the review tier.
  Default: assume personal data and prepare accordingly.
- **What insurance is in place and at what limits?** Default: get a broker quote for cyber and
  technology errors and omissions before signing enterprise terms.
- **Where is the legal entity, and what is its tax status?** Decides the tax forms. Default: ask an
  accountant before signing a W-8BEN-E treaty claim.
- **Move upmarket, or stay self-serve?** Decides whether SSO, audit logs and SOC 2 are worth
  building. Default: build only against logged, confirmed blockers.
