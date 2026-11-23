---
name: privacy-compliance
description: Keeps a web product lawful and sellable by working out which privacy, security-certification, consumer, sector and licensing rules apply and what they require. Use when asked about GDPR or CCPA, a cookie banner, a privacy policy or terms of service, a deletion or export request, a DPA or subprocessor list, SOC 2, ISO 27001, PCI, HIPAA, the EU AI Act, sanctions, a data breach notice, or a GPL or AGPL dependency.
---

# Privacy, legal and compliance

## Stance

Compliance for a small company is three things: knowing which rules actually reach the product,
making public statements that are literally true, and keeping the few records that prove it.
Most enforcement and most lost deals come from a gap between what the company says (policy,
banner, DPA, trust page, questionnaire) and what the code does. Work from the code outward:
establish the facts, then write the documents. This skill gives the mechanism and common
practice; it does not replace a lawyer for the decisions flagged as such, and jurisdiction
details and dates must be confirmed before relying on them.

- **The data map is the root artifact.** The policy, DPA annex, request runbook, retention
  schedule, vendor list and breach scoping are all views of it. Update it in the same change
  that adds a field, a vendor or a purpose.
- **Data not collected carries no duty.** Minimization is cheaper than every control that
  follows; the same goes for trackers not loaded and regulated customers not served.
- **Say only what is true, then keep it true.** A modest accurate statement beats an impressive
  false one: regulators and plaintiffs act on the false one, and auditors test against it.
- **Reach follows the user, not the company.** EU, UK and California rules apply because of
  where people are. Build to GDPR once and treat other regimes as deltas.
- **Consent must be real or avoided.** Either nothing non-essential runs before an equal-choice
  opt-in, or the stack is chosen so that no consent is needed. A decorative banner is worse
  than none.
- **Promises flow down the vendor chain.** Never commit upward (residency, notice periods,
  deletion times) to what the vendors below have not committed to.
- **Certifications are sales instruments.** Start SOC 2 or ISO 27001 when revenue depends on
  it, scope it narrowly, and write policies that describe what is actually done.
- **Deadlines start without warning.** Requests, breaches, takedowns and legal demands run on
  clocks that begin at receipt; have the inbox, the runbook and the lawyer's number before
  they are needed.
- **Know where templates stop.** Policies and DPAs can start from templates; liability terms,
  regulated sectors, breach notifications and any legal demand need counsel.

## Route

| If the task is | Read |
|---|---|
| "Are we GDPR or CCPA compliant?", mapping personal data, choosing a lawful basis, controller or processor, Global Privacy Control, EU data residency, a DPIA, a representative or DPO, or who to notify after a breach and by when | `references/privacy-law.md` |
| "Do we need a cookie banner?", adding analytics, pixels or session replay, wiring consent into tags, auditing trackers, marketing-email permission and unsubscribe, cold email or SMS | `references/consent-cookies.md` |
| A user asks to delete, export, see or correct their data; writing the request runbook; deciding retention periods; what deletion means for backups and logs | `references/data-subject-requests.md` |
| Adopting a tool that will receive user data, a customer asking for a DPA or subprocessor list, building the vendor inventory or trust page, SCCs for a non-EU vendor | `references/vendors-dpas.md` |
| Taking card payments, PCI questionnaires, payment-page scripts, a buyer asking for SOC 2 or ISO 27001, security policies, choosing a compliance platform or auditor | `references/pci-soc2-iso.md` |
| "Does HIPAA, COPPA, the EU AI Act, the Cyber Resilience Act or accessibility law apply?", subscription and cancellation rules, dark patterns, AI disclosure, sanctions and export controls, an accessibility demand letter | `references/sector-consumer-rules.md` |
| Writing or changing terms, a privacy policy or acceptable use policy, recording acceptance, DMCA or DSA takedowns, user-generated content duties, a subpoena or regulator letter | `references/terms-policies.md` |
| "Can I use this GPL or AGPL library?", license checks in CI, attribution notices, fonts and images, API terms and scraping, licensing own code, CLA or DCO, AI-generated code and assets | `references/licenses-ip.md` |

## Defaults at a glance

| Area | Prototype | Launch | Scale |
|---|---|---|---|
| Data map | One page; collect the minimum | Complete, in the repository, updated per change | Reviewed on a cadence; DPIAs for risky features |
| Privacy policy and terms | Policy if any personal data is collected | Policy generated from the data map; clickwrap terms with versioned acceptance records; lawyer review of terms | Negotiable contract set; counsel on retainer |
| Tracking | Cookieless analytics, no ad pixels, no banner | Same; if ads are added, a blocking opt-in banner for EU and UK, GPC and an opt-out link for the US | Consent platform if programmatic ads or many tags |
| Marketing email | Double opt-in list | Unticked checkbox, one-click unsubscribe, permanent suppression list | Country-specific rules for outreach |
| Data requests | Manual | Self-serve export and delete in settings, a `privacy@` inbox, runbook and log, 14-day internal target | Automated across systems and vendors |
| Retention | None formal | Written schedule enforced by jobs; backups about 30 days; legal-hold flag | Audited |
| Vendors | Prefer vendors with a DPA and region choice | Inventory, saved DPAs, public subprocessor list, own DPA published | Annual reviews, notice workflow for changes |
| Payments | Hosted checkout or provider iframes | SAQ A filed yearly, quarterly ASV scan passing; no third-party scripts on checkout pages | Script inventory and tamper monitoring formalized |
| Certifications | None | Security overview and honest questionnaires | SOC 2 (US buyers) or ISO 27001 (European buyers) when deals require it |
| Regulated sectors | Stay out | Prohibit regulated data in the terms unless deliberately supported | Enter with specialist counsel |
| Sanctions | None | Geo-block embargoed regions; restriction in the terms | Name screening for enterprise customers |
| Licenses | Permissive dependencies only | CI allowlist, third-party notices for the browser bundle, asset register | SBOM per release |
| Own code | Proprietary | Proprietary; Apache-2.0 for SDKs | CLA before accepting outside contributions to anything dual-licensed |

Other standing defaults: no selling or sharing of personal data; no training on customer
content; EU region for primary storage when EU customers are expected, with the residency
promise stated precisely; AI chat interfaces labeled as AI; cancellation online in as few
steps as signup.

## Before you call it done

1. The data map lists every purpose, data category, system, vendor, location, lawful basis and
   retention period touched by the change, and was updated in the same pull request.
2. Every statement in the privacy policy, DPA, trust page and banner text is true of the code
   as deployed; absolutes ("never", "anonymous", "EU only") were checked literally.
3. In a fresh browser profile set to an EU location, no non-essential third-party request or
   storage write occurs before opt-in or after "Reject all"; an automated test asserts it.
4. The banner offers reject with the same prominence and click count as accept, has no
   pre-ticked options, and can be reopened from the footer; withdrawal stops the tags.
5. A request with `Sec-GPC: 1` results in no sale or sharing tags, and the opt-out persists on
   the account when logged in.
6. Marketing email has a recorded consent or soft opt-in basis, a working one-click
   unsubscribe, and a suppression list that survives re-imports and account deletion.
7. A seeded test user can be exported and deleted across every system in the runbook; a search
   for its email and ID afterwards finds only the documented retained records.
8. Each retention period has a job or lifecycle rule enforcing it, that job checks the
   legal-hold flag, and deletions are replayed after a backup restore.
9. Every vendor receiving personal data has a row in the inventory, a saved DPA, a transfer
   mechanism where needed, and appears on the public subprocessor list before receiving
   customer data.
10. Terms acceptance is an affirmative act at signup and stores user, document, version,
    timestamp and IP; every published version is retrievable.
11. Card numbers never reach the servers, logs or support tools; checkout pages load only
    inventoried scripts; the correct SAQ is on file and its required ASV scans pass.
12. Subscription checkout shows price, period, renewal and cancellation next to the button,
    and cancellation works online without contacting support.
13. CI fails on a dependency license outside the allowlist; distributed artifacts include
    third-party notices; fonts, images and data have licenses on file.
14. Items needing a professional (liability terms, regulated-sector entry, breach
    notification, legal demands, a high-risk AI classification) were flagged to the user as
    such, not decided silently.
15. Time-sensitive legal facts used (deadlines, thresholds, application dates, adequacy
    status) were confirmed as current or stated as needing confirmation.

## Not this skill

- Engineering the export, deletion and retention jobs → `0x:data-stores`
- Technical security controls and breach containment → `0x:web-security`
- Making the interface itself accessible → `0x:accessibility`
- Incorporation, founder agreements and employment contracts → `0x:company-building`
- Negotiating customer contracts and answering security questionnaires → `0x:sales-support`
- Sales tax and VAT handling → `0x:payments-billing`
