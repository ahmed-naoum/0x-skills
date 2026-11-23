# Vendors, DPAs and subprocessors

Read this when: adopting a tool or API that will receive customer or user data; a customer asks
for a DPA, the subprocessor list or where data is stored; setting up the vendor inventory or
trust page; or a vendor outside the EU will handle EU or UK personal data.

## The chain

Three contracts stack, and each must be at least as strict as the one above it:

1. Customer (controller) → the product (processor): the DPA offered to customers.
2. The product → its vendors (subprocessors): each vendor's DPA.
3. Any hop that leaves the EU or UK: a transfer mechanism attached to that DPA.

A promise made in layer 1 that layer 2 cannot honor (EU-only processing while the error tracker
is US-hosted, 24-hour breach notice while a vendor commits to "without undue delay") is the
usual way a small company ends up in breach of its own contract. Read down the chain before
signing anything upward.

## Does this vendor need a DPA

| Vendor relationship | Examples | Paperwork |
|---|---|---|
| Processor: handles personal data only on instructions | Hosting, database, email delivery, error tracking, analytics, support desk, LLM API | DPA required (GDPR Art. 28); listed as a subprocessor if it touches customer data |
| Independent controller: uses the data for its own purposes | Payment networks and parts of a payment provider's service, ad platforms, banks, accountants, law firms | No Art. 28 DPA; disclose in the privacy policy; a controller-to-controller transfer clause if data leaves the EU |
| No personal data | Uptime pings, build tools without customer data | Nothing; still in the inventory |

For US state law, the contract must also bind the vendor as a "service provider" or
"processor" (no selling, no use outside the service, no combining with other data). Most
vendors' DPAs include that language; without it, sending data to the vendor can count as a sale.

How DPAs get signed in practice: most SaaS vendors incorporate the DPA into their terms
automatically, some require accepting it in a dashboard or countersigning a form, and a few
offer one only on a paid or enterprise plan. Check which, do the step, and save a dated PDF copy
of the DPA and subprocessor list as accepted, because vendor pages change. If a vendor will not
provide a DPA, it cannot receive EU or UK personal data.

## Assessing a vendor before sending it data

Scale the effort to the data, not to the vendor's size. Fifteen minutes for most tools.

| Tier | Data it will see | Check |
|---|---|---|
| 1 | Customer content, credentials, payment or sensitive data, production access | Everything below, plus read the SOC 2 Type II or ISO 27001 report summary and exceptions |
| 2 | Names, emails, usage events, support messages | DPA, regions, retention, training use, SSO/MFA, breach notice |
| 3 | No personal data | Terms and account security only |

Questions that decide adoption:

- **Purpose limits.** Does the vendor use the data for its own purposes: advertising, product
  improvement, model training? Look for an opt-out or a contractual exclusion and turn it on.
  "Aggregated and de-identified" carve-outs are normal; training on content is not.
- **Location.** Which regions can be selected, and is the choice per project or per account?
  Where do support staff and sub-vendors access from?
- **Retention and deletion.** Default retention, configurable or not, and whether there is a
  per-user deletion API. A vendor without one becomes a manual step in every deletion request.
- **Security evidence.** A current SOC 2 Type II or ISO 27001 certificate covering the service
  actually bought; MFA and SSO available on the plan to be purchased; encryption at rest and in
  transit; a published breach notification commitment.
- **Its subprocessors.** A public list and a change-notification mechanism to subscribe to.
- **Exit.** Data export format, deletion at termination, and how long deletion takes.
- **Sector needs.** A HIPAA business associate agreement or PCI attestation if those apply; see
  `sector-consumer-rules.md` and `pci-soc2-iso.md`.

Reduce what is sent before assessing harder: pass an internal ID instead of an email, redact
payloads to error trackers, disable autocapture of form inputs. For LLM providers, check
training use, retention windows and zero-retention options; details in `0x:ai-features`
(`ai-data-privacy.md`).

## Vendor inventory

One table, in the repository or a shared sheet. It is the source for the subprocessor list, the
data map's vendor column, the deletion runbook and, later, SOC 2 vendor reviews.

| Column | Purpose |
|---|---|
| Vendor, service, plan | Identity |
| Internal owner | Who answers for it and offboards it |
| Purpose | Why it exists; unowned or purposeless tools get removed |
| Data categories and tier | What it sees |
| Touches customer data: yes or no | Decides subprocessor status |
| Entity and processing location | For the trust page and transfers |
| DPA: date, version, link to saved copy | Proof |
| Transfer mechanism | DPF, SCC module, UK addendum, adequacy, or none needed |
| Security evidence and its date | Report or certificate reviewed |
| Deletion method | API, dashboard or ticket |
| Contract renewal date, notice period, cost | Avoids silent auto-renewals and gives a review trigger |
| Last reviewed | Annual for tier 1 and 2 |

Rules that keep it true: no production secret or SDK is added without a row; the review is tied
to the renewal date; offboarding means export if needed, deletion request and confirmation,
revoked keys and tokens, SDK removed, row marked closed, and customers notified if the vendor
was a listed subprocessor being replaced.

## Transfers to vendors outside the EU or UK

| Vendor situation | Mechanism | To do |
|---|---|---|
| EU or adequate-country entity, data stays there | None | Record it |
| US vendor certified under the Data Privacy Framework | Adequacy for certified recipients | Verify the active listing and that it covers the relevant data type (HR versus non-HR); re-check yearly |
| Any other non-adequate recipient | Standard Contractual Clauses, 2021 version | Confirm the right module is in the vendor's DPA; complete a transfer impact assessment |
| UK personal data to a non-adequate recipient | UK International Data Transfer Addendum to the SCCs, or the IDTA | Usually bundled in the vendor DPA; confirm |
| Swiss data | SCCs with Swiss amendments, or the Swiss-US framework | Usually bundled |

SCC modules: one is controller to controller, two is controller to processor, three is
processor to processor (the product, as its customers' processor, sending to its own
subprocessor), four is processor to controller. A B2B product typically relies on module two
for its own controller data and module three for customer data; well-drafted vendor DPAs
include both.

The transfer impact assessment is a short memo per non-adequate destination: what data, which
law in the destination could compel access, how likely that is for this data, and the
supplementary measures (encryption with keys held in the EU, pseudonymization before sending,
minimization). For US vendors, the framework's safeguards apply to SCC transfers as well, which
shortens the memo. Keep SCCs in place as a fallback even when the vendor is DPF-certified,
since the two earlier EU-US arrangements were struck down (2015 and 2020) and the current one
is under appeal at the Court of Justice.

Choosing an EU region does not by itself remove the transfer question if the vendor's staff or
its own sub-vendors can access the data from outside the EU. The vendor's DPA says whether they
can.

## The DPA offered to customers

Publish one before the first enterprise prospect asks: a self-serve document, incorporated into
the terms by reference so it applies without signature, with a countersigned PDF available on
request. Negotiating from the product's own paper is far cheaper than reviewing each customer's.

Contents and the position to take:

| Clause | Sensible position | What to resist in customer paper |
|---|---|---|
| Scope and instructions | Process only to provide the service as described in the agreement | Open-ended "any instruction" at no cost |
| Annex: processing details | Subject matter, duration, data categories, data subjects, drawn from the data map | Blank or vague annexes |
| Annex: security measures | The controls actually operated, described at a level that survives change | Named products, specific key lengths or promises not yet true |
| Subprocessors | General authorization, public list, advance notice of additions (30 days is a common commitment, shorter is easier to live with), right to object on reasonable data-protection grounds, remedy is terminating the affected service | Prior written consent for each new subprocessor: it gives every customer a veto over the stack |
| Breach notice | Without undue delay after becoming aware, with a stated outer bound of 48 to 72 hours | 24 hours, or notice of "suspected" incidents |
| Audits | Provide the SOC 2 or ISO report and answer a reasonable questionnaire once a year; on-site only where a regulator requires or after a breach, at the customer's cost | Unlimited on-site audits |
| Assistance | Help with data-subject requests and DPIAs, through product features first | Unpaid unlimited consulting |
| Deletion or return | Export available during the term; deletion within a stated period after termination (30 to 90 days), backups by rotation | Immediate certified destruction including backups |
| Transfers | SCCs and UK addendum incorporated by reference, effective only where needed | Bans on any processing outside one country that the stack cannot meet |
| Liability | Subject to the main agreement's cap | Uncapped liability for data protection: the most expensive clause in the document |

The security annex and the liability clause are where a template stops being enough; have a
lawyer review the first version and any customer redline that touches them. Contract
negotiation tactics belong to `0x:sales-support`.

## Subprocessor changes

The DPA creates an operational duty: customers must hear about a new subprocessor before it
receives their data.

1. Decide to add the vendor; complete the assessment and its DPA.
2. Update the public list with the vendor, purpose, location and an effective date that is the
   notice period in the future.
3. Notify: an email to a subscriber list (a "subscribe to updates" form on the trust page) or
   to account admins. A changelog nobody is told about does not meet a notice clause.
4. Wait out the period; handle objections case by case (explain, offer a configuration that
   avoids the vendor, or allow termination of the affected service).
5. Only then route customer data to the vendor.

Plan vendor changes with this delay in mind; an emergency replacement (a vendor outage or
breach) is usually permitted with prompt after-the-fact notice if the DPA says so, so write
that exception in.

## Trust page

A `/trust` or `/security` page answers most first-round procurement questions and reduces
questionnaire work. Keep it factual and current:

- Subprocessor table: vendor, purpose, data categories, processing location, date added.
- Where customer data is hosted (cloud provider and region) and where backups live.
- Which residency promise is made, in the precise sense described in `privacy-law.md`.
- Links to the DPA, privacy policy, terms and security overview; certifications held and how
  to request reports under NDA.
- Contacts: `privacy@`, `security@`, and a vulnerability disclosure route.
- A way to subscribe to subprocessor updates, and a "last updated" date.

Every statement on the page is a representation customers and regulators can hold the company
to. Generate the subprocessor table from the vendor inventory so the two cannot drift, and do
not list aspirations ("SOC 2 in progress" is acceptable only with a real engagement behind it).

## Ask the user

- **Which tools currently receive customer or user data?** The inventory starts from the truth,
  including tools signed up for on a personal card. Default: derive from the codebase's SDKs and
  environment variables, then ask what else exists.
- **Do customers need EU-only processing, or is disclosure of locations enough?** It constrains
  every vendor choice. Default: EU region for primary storage where available, US subprocessors
  disclosed with a transfer mechanism.
- **What notice period for new subprocessors can the company live with?** Longer notice slows
  every stack change. Default: 14 to 30 days, with an emergency exception.
- **Has a lawyer reviewed the customer DPA?** The liability and security annex wording carries
  real exposure. Default: publish from a reputable template, flag those two parts for review
  before the first negotiated deal.
- **Who owns vendor reviews and renewals?** Without an owner the inventory rots. Default: the
  founder, reviewed at each renewal date.
