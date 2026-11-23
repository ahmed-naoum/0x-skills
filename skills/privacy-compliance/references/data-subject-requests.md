# Data-subject requests and retention policy

Read this when: a person asks to see, export, correct, delete or stop the use of their data;
writing the runbook for such requests; or deciding how long each kind of data is kept and what
deletion means for backups, logs and analytics.

The jobs that perform export, deletion and expiry are engineered in `0x:data-stores`
(`data-lifecycle.md`). This file decides what they must do, by when, and what may be kept.

## First triage: whose request is it

| Requester | Role | Action |
|---|---|---|
| Own account holder, lead, newsletter subscriber, site visitor | Controller | Handle it; the clock is running |
| An end user of a B2B customer, asking about data in that customer's workspace | Processor | Do not answer on the merits. Tell the person to contact the customer, forward the request to the customer promptly, and help the customer fulfill it as the DPA requires |
| Someone acting for another person (lawyer, parent, authorized agent, request service) | Depends | Verify the authority as well as the identity |
| A regulator, court or police | Not a data-subject request | See `terms-policies.md`, legal demands |

A request is valid in any form through any channel: a support chat message, a reply to a
marketing email or a social media post all count, with no magic words and no mandatory form.
Train whoever reads the inboxes to route them to `privacy@` the same day.

## Deadlines

| Regime | Acknowledge | Fulfill | Extension |
|---|---|---|---|
| GDPR and UK GDPR | No fixed duty; do it anyway | One month from receipt | Up to two further months for complex or numerous requests; tell the person within the first month, with reasons |
| CCPA (know, delete, correct) | Within 10 business days | 45 calendar days from receipt | One further 45 days, with notice |
| CCPA opt-out of sale or sharing, limit sensitive data | None | As soon as feasible, at most 15 business days | None |
| Other US states | Varies | Commonly 45 days | Commonly 45 more, plus an appeal process the business must offer |

Work to an internal target of 14 days so that one missed handoff does not breach. Requests are
free. A fee or refusal is allowed only for manifestly unfounded or excessive requests, and the
burden of showing that is on the business; the refusal must still be sent on deadline with
reasons and the right to complain. Under GDPR the period generally runs from receipt, or from
the moment identity is confirmed where a verification request was genuinely needed and sent
promptly; do not use verification to stall.

## What each right requires

| Right | Deliver | Limits and traps |
|---|---|---|
| Access | A copy of the person's data plus: purposes, recipients, retention periods, source, transfers, and the existence of automated decisions | Covers every system, including support tickets, logs still held and internal notes. Redact other people's data. Not a right to documents as such, only to the data in them |
| Portability | Data the person provided (including observed activity), in a structured, machine-readable format such as JSON or CSV | Only where the basis is consent or contract; not inferred or derived data |
| Erasure | Delete, or irreversibly anonymize, across live systems and vendors | Exceptions below. Tell recipients the data was disclosed to |
| Rectification | Correct inaccurate data, complete incomplete data, within the same deadline | Opinions and historical records (an invoice as issued) are not "inaccurate"; add a note instead. Propagate to vendors |
| Objection | Stop the processing | Absolute for direct marketing, including profiling for it: stop at once and suppress. For other legitimate-interests processing, stop unless compelling grounds override the person's situation; document the reasoning |
| Restriction | Keep the data but stop using it | Applies while accuracy or an objection is being assessed, or when the person wants data kept for a legal claim instead of deleted. Needs a per-record flag that excludes the row from processing, emails and analytics |
| Automated decisions | Human review of a solely automated decision with legal or similarly significant effect | If the product makes such decisions, design the review path before the first request |
| Withdraw consent | Stop the consent-based processing from now on | Must be as easy as giving it |

Self-service removes most of the work. At Launch, ship in account settings: download my data
(JSON plus files), edit profile, delete account, marketing preferences. A logged-in action is
already authenticated, is logged automatically, and answers the request in minutes. For B2B,
give workspace admins an export and a delete-user function so the customer can answer its own
requests without a support ticket.

## Verifying identity without collecting more

The aim is to match the requester to the data held, using what is already held. Two failures
matter: giving one person's data to another (a breach created by the response), and demanding
so much proof that the right is obstructed.

| Situation | Verification |
|---|---|
| Request made while logged in | Sufficient; re-authenticate for export and delete as for any sensitive action |
| Email from the address on the account | Reply with a confirmation link to that same address, or ask them to make the request in-app |
| Email from a different address, or account access lost | Ask for facts only the account holder would know and that are already on file (recent invoice amount, last four card digits, creation month); never accept a spoofable `From` header alone |
| No account (lead, visitor, newsletter) | Confirm control of the email address; for cookie-level data, the requester must supply the identifier, otherwise the data cannot be linked and that is the answer |
| Agent or representative | Signed authority, plus verification of the person directly where allowed |
| Deletion of a paid or high-value account | Add a cooling-off period with a cancel link, since deletion is irreversible and a common account-takeover goal |

Do not ask for government ID by default. It is disproportionate for most accounts, creates new
sensitive data to protect, and regulators have criticized it. If ID is ever justified, check it
and discard it; record only that it was checked. The stricter the consequence, the stronger the
check: disclosing specific records needs more certainty than confirming categories, and an
opt-out needs none. Send exports through an authenticated download link that expires, never as
an email attachment.

## The runbook

Write it once, in the repository, as a checklist per request type. Its backbone is the systems
list from the data map; a request is complete only when every row is ticked.

| System | Access or export | Delete | Notes |
|---|---|---|---|
| Primary database | Export job by user ID | Delete or anonymize job | Cascades and foreign keys decided in advance |
| Object storage | Listing by owner prefix | Delete objects and old versions | Versioned buckets keep deleted objects until lifecycle rules expire them |
| Search index, cache, vector store | Usually derived; mention in the response | Remove documents and embeddings | Reindex does not remove by itself |
| Warehouse and analytics tool | Query by user ID | Tool's person-deletion API, warehouse delete | See the section on analytics below |
| Error tracker, logs | Search by user ID | Vendor deletion API or expiry | Prefer short retention over per-user deletion |
| Email, CRM, support desk, billing provider | Vendor export | Vendor deletion or redaction API | Billing records are retained by law |
| LLM and other API vendors | Normally none retained beyond the vendor's stated window | Vendor process if stored | Check each vendor's retention setting |
| Spreadsheets, inboxes, shared drives | Manual search | Manual | The part that is always forgotten |

Procedure:

1. Log the request (fields below) and compute both the internal and the legal due date.
2. Triage role and right; verify identity.
3. Check for a legal hold or an exception that applies.
4. Run the per-system steps; for deletion, call each subprocessor's deletion mechanism and
   record the confirmation.
5. Reply in plain language: what was done, what was kept and why, how long it will be kept, and
   the right to complain to the regulator. For access, include the explanatory information, not
   only the file.
6. Close the log entry with the date and evidence.

Test the runbook with a seeded test user before the first real request: create data in every
system, run export and delete, then search every system for the user's email and ID.

## What may be kept after a deletion request

Erasure is not absolute. Keep only what an exception covers, isolate it from the live product,
and say so in the reply.

| Kept | Ground |
|---|---|
| Invoices, payment and tax records | Legal obligation; the statutory accounting period of the relevant country, typically several years up to about a decade |
| Evidence needed for an existing or reasonably anticipated legal claim | Establishment or defense of legal claims |
| Fraud, abuse and ban records; security logs for their normal retention | Legitimate interests, kept minimal and time-limited |
| The email on the marketing suppression list | Needed to honor the objection |
| The request log entry itself | Accountability |
| Content the user posted in a shared space (messages to others, team documents) | Other users' rights and the customer's ownership; detach or anonymize the author instead |

Anonymize instead of deleting where rows must survive for integrity or aggregates: replace
identifying columns with nulls or a tombstone value, and sever the link so the row cannot be
re-attached to the person. A hashed email is not anonymous.

## Backups, logs and analytics

- **Backups.** Rewriting backups for each request is not expected. The defensible position:
  the data is deleted from live systems now, is put "beyond use" in backups (not restored for
  any purpose except disaster recovery), expires with the backup rotation, and deletions are
  re-applied after any restore. That last step needs a durable deletion ledger of user IDs and
  dates, stored outside the database being restored, and a restore procedure that replays it.
  Keep backup retention short enough to state a number in the reply: about 30 days is common
  for rolling backups; long-lived archives need a justification.
- **Logs.** Keep personal data out of logs as a design rule, and set log retention to a short
  fixed period (30 to 90 days is typical for application logs; security and audit logs longer,
  with restricted access). Expiry then does the deleting, and the reply can say so.
- **Product analytics.** Use the tool's person-deletion feature and confirm it also removes
  raw events, not only the profile. In the warehouse, delete or anonymize by user ID across
  event tables; partitioned and append-only tables make this expensive, so key events by a
  pseudonymous ID held in one mapping table and delete the mapping row (then treat what remains
  as anonymous only if nothing else in the events re-identifies the person).
- **Aggregates** that no longer relate to a person need no action.
- **Models and embeddings** built from the person's data: delete embeddings; for trained or
  fine-tuned models there is no settled answer, which is a reason not to train on personal data
  without a plan. See `0x:ai-features` (`ai-data-privacy.md`).

## Retention schedule

Every category in the data map gets a period, a reason, and a deletion mechanism. "As long as
necessary" is not a period. A starting schedule for a SaaS product, to adjust with the user:

| Data | Period | Basis |
|---|---|---|
| Account and content | Life of the account, then 30 days grace | Contract |
| Inactive free accounts | Warn, then delete after 24 months inactivity | Minimization |
| Customer workspace data after cancellation | 30 to 90 days, then delete; per the DPA | Contract |
| Invoices and tax records | Statutory period of the company's and customers' countries | Legal obligation |
| Application logs | 30 to 90 days | Security, debugging |
| Audit and security logs | About 12 months, longer where a framework requires | Security, compliance |
| Support tickets | 2 to 3 years after closure | Service quality, claims |
| Leads who never became customers | 12 to 24 months after last contact | Legitimate interests |
| Job applicants | 6 to 12 months unless consent to keep longer | Claims period |
| Backups | About 30 days rolling | Recovery |
| Consent and request logs | Lifetime of the consent plus the limitation period | Accountability |

Periods here are common practice, not law; limitation periods and bookkeeping rules differ by
country. Enforce each row with a scheduled job or a storage lifecycle rule, and alert when the
job fails, because a schedule nobody runs is evidence against the company.

**Legal hold.** When litigation, a regulator inquiry or a serious dispute is reasonably
anticipated, deletion of relevant data must stop, including scheduled expiry. Implement it as a
flag on the user or tenant that every deletion and retention job checks first, set and released
only on counsel's instruction, with the reason and dates recorded. A deletion request from
someone under hold is answered with a partial refusal citing the legal-claims ground.

## The request log

The log is the proof of timely handling and the first thing a regulator asks for.

| Field | Content |
|---|---|
| ID, date received, channel | Start of the clock |
| Requester and role | Controller request or forwarded to which customer |
| Right invoked, jurisdiction applied | Decides the deadline |
| Verification method and date | Not the evidence itself |
| Due date, extension and its notice date | Deadline control |
| Systems and vendors actioned, with confirmations | Completeness |
| Exceptions applied, data retained | Justification |
| Response date and a copy of the response | Proof |

A spreadsheet or a tagged queue in the support tool is enough until volume reaches several
requests a week. Add a reminder at day 14 and day 25. Keep the log minimal: it must not become
a second copy of the data that was deleted.

## Ask the user

- **How long must financial records be kept where the company is registered?** It sets the
  floor for billing data. Default: keep invoices for the statutory period advised by the
  accountant, isolated from product data.
- **What happens to a customer's data when they cancel?** Decides the grace period and the DPA
  wording. Default: read-only for 30 days, deleted by day 90, export available throughout.
- **Should deleted users' shared content stay, anonymized, or go?** A product decision with
  effects on other users. Default: keep shared content, show the author as "Deleted user".
- **Who answers privacy requests and watches the inbox?** A missed message still starts the
  clock. Default: the founder, with `privacy@` forwarding to the support queue.
- **How long are backups and logs kept today?** The reply to a deletion request must state it.
  Default: 30 days for backups, 30 to 90 days for logs.
