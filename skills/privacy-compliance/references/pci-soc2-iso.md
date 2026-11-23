# PCI DSS, SOC 2 and ISO 27001

Read this when: the product takes card payments in any form; a buyer, partner or questionnaire
asks for SOC 2, ISO 27001 or "your security certifications"; writing security policies; or
choosing a compliance platform and auditor.

## PCI DSS: keep card data off the servers

PCI DSS applies to anyone who stores, processes or transmits card data, or whose systems can
affect its security. It is enforced by contract through the acquirer or payment provider, not
by statute. The goal for a small company is the smallest possible scope: the card number never
touches its servers, logs or support channels.

| Integration | Card data path | Self-assessment | Effort |
|---|---|---|---|
| Redirect to a provider-hosted page (hosted checkout) | Never on the site | SAQ A | Smallest |
| Provider's fields in iframes embedded in the page (hosted fields, embedded elements) | In the provider's iframe | SAQ A, with the script-security condition below | Small |
| Own form whose values a provider script reads, or a direct post to the provider | Through the page's own DOM | SAQ A-EP | Large: the web server is in scope |
| Card data sent to or through own servers, or stored | On the servers | SAQ D | Avoid; an order of magnitude more requirements |
| Card details taken by phone, email or chat | People and devices in scope | Other SAQs | Do not do it; send a payment link |

Default: hosted checkout or the provider's iframe-based fields, which is also the house default
for payments. Before building a custom card form, confirm with the provider which SAQ the
integration falls under; the provider's dashboard usually states it and pre-fills the
questionnaire.

What remains even at SAQ A:

- Complete the SAQ and attestation of compliance every year, and when the integration changes.
- Use only PCI-compliant providers and keep their attestation on file.
- Secure the accounts that could change the payment integration: provider dashboard, DNS,
  hosting, the repository and CI. Unique accounts with MFA.
- Keep the site that serves the redirect or iframe patched and free of injected scripts; check
  the current SAQ A text for the external vulnerability scan requirement that applies to
  e-commerce pages.
- Never store the card verification code after authorization, in any form, by anyone. Never
  log or screenshot full card numbers; scrub them from support tickets if a customer pastes one.
- Tokens, last four digits, brand and expiry returned by the provider are safe to store.

Merchant level (set by annual transaction volume per card brand) decides whether
self-assessment is enough; small merchants self-assess, the highest-volume level needs an
external assessor's report. A SaaS that touches card data on behalf of its customers is a
"service provider" under PCI, with heavier duties: avoid that architecture, or get advice.

### Payment-page scripts: requirements 6.4.3 and 11.6.1

Card-skimming attacks inject JavaScript into the page that hosts or launches the payment form.
PCI DSS v4 answers with two requirements, mandatory since the end of the v4 transition period:

- **6.4.3**: every script that loads and runs on a payment page is authorized, has its
  integrity assured, and is listed in an inventory with a written business justification.
- **11.6.1**: a change and tamper detection mechanism alerts on unauthorized changes to the
  security-relevant HTTP headers and the script contents of payment pages as received by the
  consumer's browser, at least weekly or at a frequency set by a documented risk analysis.

Who must do what: merchants on SAQ A-EP or D must implement both. For SAQ A, the Council
replaced the two requirements with an eligibility condition that the merchant confirm its site
is not susceptible to script attacks affecting the payment system; redirects are outside the
concern, and for embedded iframes the confirmation rests either on the provider's statement
that its solution protects against such attacks when integrated as documented, or on applying
the same techniques. Read the current SAQ A and the Council's FAQ on that condition before
attesting.

Practical implementation on the page that embeds or links to payment:

1. Minimize: no tag manager, chat widget, analytics, A/B tool or ad pixel on checkout pages.
   Every script removed is one fewer inventory line and attack path.
2. Inventory: a table of each remaining script with source, purpose, owner and how it is
   authorized (code review for first-party, an allowlist entry for third-party).
3. Authorize and constrain: a Content Security Policy on those routes with an explicit
   `script-src` allowlist (nonces or hashes for inline scripts, no wildcards) and `frame-src`
   limited to the payment provider; Subresource Integrity for third-party scripts with stable
   contents. The provider's own loader script usually cannot be pinned with SRI because it
   changes; it is authorized by allowlisting its origin, per the provider's guidance.
4. Detect: CSP violation reporting to a monitored endpoint, plus a scheduled synthetic check
   that loads the page in a real browser and compares script sources, hashes and security
   headers against the inventory, alerting on drift. Commercial client-side monitoring services
   do the same.

CSP mechanics are in `0x:web-security` (`browser-security.md`).

## SOC 2 or ISO 27001: when buyers actually require it

Neither is a law. They are sales instruments: evidence that lets a buyer's security team
approve the vendor without auditing it themselves.

| | SOC 2 | ISO 27001 |
|---|---|---|
| What it is | An attestation report by a CPA firm against the AICPA Trust Services Criteria | A certificate from an accredited certification body that an information security management system meets the standard |
| Who asks | US buyers, almost universally | European, UK, APAC and public-sector buyers; global enterprises accept either |
| Scope choice | Security criteria are mandatory; Availability, Confidentiality, Processing Integrity and Privacy are optional | The ISMS scope statement and the Statement of Applicability over the Annex A controls |
| Forms | Type I: design of controls at a date. Type II: operating effectiveness over a period, usually 3 to 12 months | Stage 1 (documentation) and Stage 2 (operation) audits; three-year certificate with annual surveillance audits |
| Output | A long confidential report, shared under NDA | A one-page public certificate |

Decision rules:

- Prototype: do nothing formal. Operate the basics from `0x:web-security` (MFA, least
  privilege, backups, patching) and keep a short security overview page.
- Launch: answer questionnaires honestly from that page; the first mid-market buyers often
  accept a completed questionnaire, a recent penetration test summary and a DPA.
- Start a certification when it gates revenue: rule of thumb, when two or three qualified deals
  name it as a requirement, or one deal is worth more than the first-year cost. The all-in cost
  for a small company (platform, auditor, penetration test, founder time) is typically in the
  tens of thousands of dollars a year, and the time cost is the larger part.
- Ask the buyer what they will accept before committing: "SOC 2 Type II within 12 months" with
  a signed auditor engagement letter, or a Type I now, closes many deals.
- Choose by where the buyers are. US-led: SOC 2. Europe-led: ISO 27001. The controls overlap
  heavily, so the second is cheaper once the first is done.
- Skip Type I if nobody is waiting on it; it is a stepping stone that buyers discount. Take it
  when a deal needs a report within weeks.
- Keep the first scope narrow: the production system and the people who touch it; Security
  criteria only, adding Availability or Confidentiality when buyers ask. The Privacy criteria
  and extra frameworks add work without closing more early deals.

Regulated buyers may ask for something else instead: HIPAA assurances, PCI attestation,
government frameworks. Do not assume SOC 2 covers them.

## The minimal policy set

Auditors test the company against its own policies. A policy that promises more than is done
produces an exception in the report; a short policy that is followed produces none. Write what
is actually done, in a page or two each, with an owner and an annual review date.

| Policy | Must settle |
|---|---|
| Information security (umbrella) | Roles, scope, commitment, exceptions process |
| Access control | SSO and MFA, least privilege, how access is granted, reviewed and removed, and how fast after someone leaves |
| Change management | Pull request, review, automated tests and deploy pipeline; emergency changes |
| Incident response | Severity levels, who decides, notification duties, post-incident review |
| Risk assessment | Method, cadence, register |
| Vendor management | Tiers, checks before adoption, annual review |
| Data classification, retention and disposal | Classes, handling rules, the retention schedule |
| Business continuity and backup | Recovery objectives, backup and restore testing |
| Secure development | Environments separated, secrets handling, dependency and vulnerability management with fix timelines |
| People security and acceptable use | Onboarding, training, device requirements, offboarding |

Avoid commitments that cannot be evidenced: "all changes are reviewed by a second engineer"
when there is one engineer, "quarterly" when annual is what happens, named tools that will be
replaced. Platform templates are a fine starting point only after editing them down to reality.

The solo-founder problem is separation of duties. Workable compensating controls: enforced CI
checks and branch protection on every change, automated deploys with an immutable log, a
periodic after-the-fact review of merged changes by a second person (co-founder, advisor or
contractor) with access limited to that task, and alerts on production access. Agree the
approach with the auditor before the observation window starts.

## Platform and auditor

A compliance automation platform (Vanta, Drata, Secureframe, Sprinto and others) connects to
the cloud account, identity provider, code host, HR system and device management, tests
controls continuously, collects evidence, hosts policies and gives the auditor a workspace.
For a small team it replaces most of the manual evidence work; it does not make the company
compliant by being installed.

Choosing the platform: check that it integrates with the stack actually used (a PaaS and a
managed Postgres are less well covered than the big clouds, which means manual evidence);
check which frameworks are included in the price; check renewal pricing, which often rises
after the first year; and ask how evidence can be exported if leaving.

Choosing the auditor: it must be independent of the platform (a licensed CPA firm for SOC 2,
an accredited certification body for ISO 27001, which cannot also be the consultant who built
the ISMS). Prefer a firm that works inside the chosen platform, will name the people doing the
fieldwork, and whose reports buyers' security teams recognize. Very cheap, very fast reports
are noticed by experienced reviewers and can cost more in lost credibility than they save. Ask
for a sample report and the expected number of evidence requests.

## Getting to Type II or certification

1. Scope and gap assessment: system description, criteria or Annex A applicability, missing
   controls. One to two weeks with a platform.
2. Remediate: SSO and MFA everywhere; device encryption, screen lock and patching verified by
   a management tool; branch protection and required reviews; logging and alerting; backups
   with a tested restore; vulnerability scanning with tracked fixes; onboarding and
   offboarding checklists; background checks where lawful; security training; a penetration
   test; vendor reviews; a risk assessment; an incident response tabletop.
3. Stabilize before starting the clock. Every lapse inside a Type II observation window is
   reportable, so begin the window only when the automated tests are green and the manual
   cadences have each run once.
4. Observation window: three months is the usual first window, moving to twelve-month periods
   afterwards so reports are continuous. ISO needs the ISMS operating with at least one
   internal audit and one management review before Stage 2.
5. Fieldwork: the auditor samples populations (all hires, all departures, all changes, all
   incidents in the window) and asks for evidence for each sample.
6. Report or certificate, then the same thing every year. Buyers ask for a bridge letter
   covering the gap between report periods.

Exceptions in a report are not fatal. Buyers read the exception and the management response;
a few honest exceptions with fixes read better than a suspiciously clean report from an
unknown firm.

## The cadence that keeps it true

| Activity | Frequency | Evidence |
|---|---|---|
| Access review: every system in scope, every account and privilege | Quarterly | Signed-off list and the removals made |
| Offboarding | Within the policy's stated time of departure | Ticket with timestamps |
| Vulnerability scans and dependency updates | Continuous, with fix deadlines by severity | Scanner and pull request history |
| Backup restore test | At least annually | Test record with timings |
| Vendor review | Annually for vendors handling sensitive data | Updated inventory, reports reviewed |
| Risk assessment | Annually and on major change | Updated register with owners and treatments |
| Policy review and approval | Annually | Version history |
| Penetration test | Annually | Report and remediation tickets |
| Incident response exercise | Annually | Notes and actions |
| Security training | At hire and annually | Completion records |
| ISO only: internal audit and management review | Annually | Reports and minutes |

Put each row in the calendar with an owner on the day the policies are signed. Missing a
quarterly access review is the single most common Type II exception at small companies. Answering
buyers' questionnaires from this material is covered in `0x:sales-support`.

## Ask the user

- **Has a named buyer asked for SOC 2 or ISO 27001, and what would they accept in the
  meantime?** It decides whether to start and which form. Default: do not start until deals
  require it; offer a questionnaire, penetration test summary and trust page.
- **Where are most target customers: US or Europe?** Picks the framework. Default: SOC 2 for
  US-led sales, ISO 27001 for Europe-led.
- **How do customers pay, and does any flow take card numbers outside the provider's hosted
  fields?** Sets PCI scope. Default: hosted checkout or provider iframes only, SAQ A.
- **Is there a second person who can review changes and access?** Separation of duties shapes
  the control design. Default: automated controls plus a periodic independent review.
- **What budget and founder time can go to compliance this year?** It is a recurring annual
  cost, not a project. Default: narrowest scope, one framework, a platform plus a mid-market
  auditor.
