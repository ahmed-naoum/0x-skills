# Security logging, detection and breach response

Read this when: deciding what to audit-log and for how long, building the audit log or an admin tool, wiring alerts on suspicious activity, writing the incident plan, or handling a suspected intrusion. If an intrusion is in progress, go straight to "Containment".

## Three kinds of log

| Kind | Purpose | Lives in |
|---|---|---|
| Application and debug logs | Diagnose behavior | Log platform, short retention: `0x:site-reliability` (`logging-errors.md`) |
| Audit log | A durable business record of who did what to what | The product's database; long retention; queryable; shown to customers |
| Provider logs | Infrastructure and account activity: cloud audit trail, identity provider, source host, database, CDN | Each provider, exported to an archive |

Every security-relevant record answers: who (which identity and which credential), did what, to what, from where, when, and whether it succeeded.

## What to log and how long to keep it

| Area | Events |
|---|---|
| Authentication | Sign-in success and failure with a reason category, sign-out, MFA challenge, MFA enrolled or removed, password changed or reset, email changed, recovery code used, session revoked, sign-in from a new device |
| Access control | Role or permission changed; member invited, joined or removed; ownership transferred; API key or token created or revoked; OAuth app authorized; authorization denied |
| Data | Export and bulk download, share link created, bulk or permanent deletion, import; reads of individual sensitive records where the sector requires it |
| Money | Plan changed, payment method changed, refund issued, payout details changed, coupon created |
| Staff | Every admin action, every read of customer data in admin tools, impersonation start and stop |
| Security settings | Changes to SSO, MFA policy, IP allow-lists, webhook endpoints, custom domains, retention and audit settings |
| System | Deploys (who, which commit), migrations, secret reads from the manager, infrastructure and CI workflow changes, rate-limit trips, webhook signature failures |

All of these from Launch, except the System row beyond deploys, which can wait for Scale.

Fields: `occurred_at` (UTC, server clock), `actor_type` (user, staff, api_key, system), `actor_id`,
`on_behalf_of`, `tenant_id`, `action` (a stable namespaced name such as `member.role_changed`), `target_type`,
`target_id`, `outcome` (success, denied, failed), `ip`, `user_agent`, `request_id`, a credential reference
(session-ID hash or key prefix), `metadata` (before and after of changed fields), `reason`.

Never log: passwords, failed attempts included (a failed password is usually the right password for another account, or one typo from the real one); full tokens, API keys or session IDs (log a prefix or a hash); MFA codes; reset links; card numbers; whole request bodies; `Authorization` and `Cookie` headers. Emit structured JSON so that a newline in user input cannot forge an entry.

Retention (rule of thumb; contracts and sector rules override):

| Log | Searchable | Total |
|---|---|---|
| Audit log | 12 months | 12 to 24 months; longer where a sector rule or contract says so |
| Authentication events | 90 days | 12 months |
| Cloud audit trail, identity-provider and source-host logs | Provider default | 12 months or more in the archive; provider defaults are measured in weeks or months |
| Application and access logs | 14 to 30 days | 30 to 90 days |

Why a year: intrusions are often discovered months after the initial access. When the logs are gone the scope of
the breach is unknown, and unknown usually has to be treated as "everything was accessed". Twelve months with
the latest three immediately available is also what PCI DSS requires and what auditors commonly expect
elsewhere. IP addresses and user agents are personal data under GDPR: state the retention period and purpose,
and do not keep them forever (`0x:privacy-compliance`).

## Append-only audit log

Default at Launch: a table in the main Postgres database, written through one function.

```sql
CREATE TABLE audit_log (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  occurred_at  timestamptz NOT NULL DEFAULT now(),
  tenant_id    uuid,
  actor_type   text NOT NULL,
  actor_id     text,
  on_behalf_of text,
  action       text NOT NULL,
  target_type  text,
  target_id    text,
  outcome      text NOT NULL,
  ip           inet,
  request_id   text,
  metadata     jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX ON audit_log (tenant_id, occurred_at DESC);
CREATE INDEX ON audit_log (actor_id, occurred_at DESC);
GRANT INSERT, SELECT ON audit_log TO app_rw;  -- no UPDATE, DELETE or TRUNCATE
```

- **Append-only by privilege.** The application role may insert and select. It has no `UPDATE`, `DELETE` or `TRUNCATE`, and it does not own the table, since an owner can always grant itself more. Retention is a privileged maintenance job; partition by month once volume justifies it, so that the job drops partitions instead of deleting rows.
- **Same transaction as the action** for successful changes, so that there is never a change without a record, nor a record of a change that rolled back.
- **Outside the transaction for denials and failures.** A denied attempt logged inside the transaction it aborts disappears with the rollback. Write those on a separate connection or after the rollback.
- **No foreign keys to users or tenants.** A cascade would erase history when an account is deleted. Store IDs as plain values, with a display snapshot in `metadata`.
- **Erasure requests**: pseudonymize display fields and keep the event (`0x:privacy-compliance`, `data-subject-requests.md`).
- **Stable action names.** They become a public contract once customers export the log: add, never rename.
- **One entry point**: an `audit(ctx, action, target, metadata)` function, plus a test or lint asserting that every mutation in the admin and settings modules calls it.

Privileges do not stop a database superuser or an attacker holding the owner's credentials, so a copy must leave the database continuously (below). Hash-chaining rows adds tamper evidence; build it only when a regulator or enterprise customer asks, because an off-host copy under object lock gives most of the value with less code.

## Admin actions and impersonation

- Log reads as well as writes in admin tools: viewing a customer, searching by email, exporting. Insider snooping and a compromised staff account both look like reads.
- During impersonation every event carries both identities: `actor` is the staff member, `on_behalf_of` the customer. Never record an impersonated action as if the customer performed it; the session carries an impersonator ID for this purpose.
- Start and stop are events, with a reason and a ticket reference. Impersonation sessions expire on their own (30 to 60 minutes, rule of thumb).
- Customers can see staff access to their account in their own audit log. Enterprise customers usually expect that by contract.
- Staff cannot edit or delete entries. Someone other than the actor samples the staff log monthly; for a solo founder, alerts to oneself on impersonation and exports still catch a compromised staff session.
- Direct database access bypasses all of this and is logged at the database (`accounts-admin-hardening.md`).

## Off-host shipping and cloud alerts

An attacker with root on a host, or admin rights in the cloud account, deletes local logs first. Logs must leave the blast radius as they are produced, to a destination the workload can write to but cannot read back or delete.

| Piece | Setup |
|---|---|
| Hosted log platform | Log drains from the host and application; the simplest option at Launch |
| Write-once object storage | A bucket with versioning and object lock, in a separate account or project whose administrators are not the production credentials |
| Cloud audit trail | Enabled for all regions, delivered to that bucket, with log-file integrity validation on |
| Other providers | Turn on and export the identity-provider audit log, source-host audit log, database logs, CDN and WAF logs, and the secrets manager's access log. Check each default retention |

Alert on these cloud API events, routed to a phone and not to a dashboard:

| Category | Events |
|---|---|
| Root and sign-in | Any root sign-in or root API call; console sign-in without MFA or from a new country |
| Persistence and escalation | User, access key or login profile created; admin policy attached; role trust policy changed; identity provider added |
| Log tampering | Trail stopped, deleted or its selectors changed; log groups deleted; threat detection disabled |
| Data exposure | Bucket policy or ACL made public; public-access block removed; snapshot shared or made public; database made publicly reachable; security group opened to the world on a non-web port |
| Resource abuse | Instances in unused regions; GPU or very large instance types; email-sending limits raised or new sender identities; model-inference usage appearing; spend anomaly |
| Key management | KMS key disabled or scheduled for deletion |
| Enumeration | Bursts of access-denied errors from one principal |

Turn on the cloud's managed threat detection at Launch (GuardDuty on AWS, or the equivalent elsewhere) and page on high-severity findings; it covers most of this list for less effort than writing rules. Deny unused regions by organization policy (`0x:cloud-infrastructure`, `iam-accounts.md`). Decoy credentials are the cheapest tripwire (`secrets.md`).

## Detecting anomalies in the product

At this size a handful of rules beats any model. Start with these as scheduled SQL over the audit log, every 5 to 15 minutes, posting to the alert channel; tune thresholds from a few weeks of data.

| Signal | Starting rule | Likely meaning |
|---|---|---|
| Export or download volume | One actor at several times their own or their tenant's daily norm, or above an absolute cap | Account takeover, insider, scraping |
| Enumeration | One session requesting many distinct object IDs with a high share of 403 and 404 | Probing for missing authorization checks |
| Privilege change | Any grant of owner or admin; a role change followed by an export within a day | Takeover, then escalation |
| New credential | API key, token, OAuth grant, SSH key or MFA device added, especially right after a password reset or from a new device | Persistence |
| Security setting weakened | MFA disabled, SSO enforcement off, email changed, webhook URL changed | Preparation |
| Sign-in | Failure rate per address, network or account; success after many failures; many accounts from one address | Credential stuffing: `0x:auth-identity` (`abuse-defense.md`) |
| Staff | Impersonation or customer-record views above the norm, or outside working hours | Compromised staff account, or snooping |
| Infrastructure | Outbound traffic spike from database or app hosts; long-running dump or copy statements | Exfiltration |

Every alert needs an owner and a one-line response; ten actionable alerts are worth more than a hundred ignored ones (`0x:site-reliability`, `dashboards-alerting.md`). Users are the best detectors for their own accounts: notify them of a new sign-in, a new API key, an MFA change, and an email change (sent to the old address).

## The incident plan

Write it now: one or two pages, stored where it survives the incident (printed, in the password manager, and offline), because the wiki may be down or readable by the attacker.

- **Roles.** Incident lead (decides), technical lead (investigates and contains), communications (customers, regulators), scribe (timeline). One person may hold several. A solo founder names an outside second, either a security-experienced peer or a response firm, plus a lawyer.
- **Contacts, with phone numbers.** The team; outside counsel with breach experience; the cyber-insurance hotline
  (call early: policies often require their approved responders and notice before money is spent); a response
  firm; security contacts at the cloud, hosting, auth, payment and registrar providers; security contacts of
  customers owed notification by contract; the data-protection authority's reporting channel.
- **Decisions made in advance.** What counts as a security incident. Anyone on the response may take production offline to contain, without approval. Who decides on customer notification (the lead with counsel). The stance on extortion: by default do not pay, and never decide without counsel, since sanctions law can make payment illegal. Who speaks externally: one voice.
- **Out-of-band channel.** If email or chat may be compromised, the response moves to a pre-agreed alternative: a messaging group on personal devices, or a phone bridge.
- **Clocks.** GDPR requires notifying the supervisory authority within 72 hours of becoming aware of a
  personal-data breach, unless it is unlikely to result in risk; processors notify controllers without undue
  delay; contracts often set shorter windows; other jurisdictions differ (US state laws, for example, each set
  their own triggers, recipients and deadlines). Record the moment of awareness. The law itself:
  `0x:privacy-compliance`, and counsel.
- **Runbooks linked from the plan**, each tried once: revoke all sessions, rotate each secret in the inventory, block an address or network at the edge, disable a user or tenant, switch to maintenance mode, stop outbound email and webhooks, snapshot a host and the database, restore from backup.

General incident mechanics (channels, status page, postmortem) are in `0x:site-reliability` (`incident-response.md`). Security incidents differ in four ways: a small need-to-know group, the assumption that the attacker reads normal channels, evidence preserved before anything is fixed, and legal clocks.

## Containment

Order matters. Steps 2 to 6 overlap in practice, but none is skipped.

1. **Start the timeline.** UTC timestamps for what was observed and what was done, and by whom. Screenshots and exported logs go into one folder.
2. **Scope fast.** Which identities, hosts and credentials are involved? Minutes, not hours. When crown-jewel data is at risk, contain on suspicion.
3. **Preserve evidence before changing anything.** Snapshot disks and the database. Export logs now from every
   system with short retention (PaaS runtime logs can expire within hours or days), along with the cloud audit
   trail and identity-provider logs. On a host, capture the process list, network connections, logged-in users,
   cron entries and `authorized_keys` to a file stored elsewhere. Do not reboot, and do not delete the instance.
4. **Isolate, do not destroy.** Quarantine the host with a network rule that admits only the investigator, and detach it from the load balancer. On a PaaS, roll back to a known-good deploy and disable the affected integration. Suspend a compromised account; do not delete it.
5. **Cut access.** Revoke sessions: every user's if the session secret or the database may be exposed, and staff
   sessions at the identity provider. Then rotate credentials from a clean device, in this order: those the
   attacker is known to have used; those that mint other credentials (cloud admin, identity-provider admin, CI,
   registry and source-host tokens, secrets-manager access); everything readable from the compromised host or
   identity (database passwords, API keys, signing and webhook secrets, OAuth client secrets, and customers'
   third-party tokens, which customers must re-authorize); then the rest.
6. **Hunt persistence while rotating**, or the attacker reads the new secrets. Look for new cloud users, keys, roles and trust policies; OAuth apps and personal tokens; deploy keys and SSH keys; cron jobs and services; new admin rows in the application database; changed webhooks, mail-forwarding rules and DNS records; unexpected commits and CI workflow changes; new MFA devices on staff accounts.
7. **Close the entry point.** A hypothesis about how they got in is the minimum before clean systems go back online; otherwise they return the same way.
8. **Rebuild from known-good.** Redeploy from reviewed source onto fresh infrastructure. A "cleaned" host is not trusted. Restore data from backup only if integrity was affected, and from a backup older than the compromise.
9. **Watch for return** for weeks: the indicators seen, plus the detection rules above at lower thresholds.
10. **Communicate per the plan**: what is known, what is not, what users should do. No speculation, and no reassurance the evidence cannot support.

Traps: deleting the compromised instance and the evidence with it; rotating only the one key that was noticed; stating "no evidence of access" when there were no logs that could contain such evidence; coordinating over a compromised channel; forgetting that sessions, refresh tokens and API keys survive a password reset; restoring a backup that already contains the backdoor.

## Reconstructing what was accessed

- **Build one timeline** from all sources, normalized to UTC and joined on credential ID (access key ID, session hash, API key prefix), IP address, user agent and request ID.
- **Pivot until the set closes.** Start from one known-bad indicator: all activity from that address → every identity it touched → every address those identities used → repeat. Then look earlier, because the first event found is rarely the initial access. Search for the precursor: failed sign-ins, scanning, a phishing timestamp, a dependency install.
- **Know what each source can prove.**

| Source | Shows | Blind to |
|---|---|---|
| CDN and load-balancer access logs | Every HTTP request: path, status, bytes sent | POST bodies; which rows were returned |
| Application audit log | Semantic actions per identity | Anything done outside the application |
| Database logs | Connections; statements if auditing was on | Reads, when statement auditing was off |
| Cloud audit trail | Management API calls by credential | Object-level reads, unless data events were enabled beforehand |
| Identity provider | Sign-ins, token grants, admin changes | Activity inside downstream tools |
| Source host | Clones, token use, workflow runs, settings changes | Events past its retention |
| Host | Auth log, process and network captures | Anything the attacker edited: shell history and file times are not trustworthy |

```bash
aws cloudtrail lookup-events --max-results 50 \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIAEXAMPLEKEYID
```

`lookup-events` covers management events from the last 90 days; older and data-level events come from the archived trail.

- **Classify every data set three ways**: confirmed accessed; possibly accessed (reachable, and no log can exclude it); confirmed not accessed (the logs are complete and show nothing). Regulators and customers need exactly this, and "possibly" generally has to be treated as affected; counsel decides.
- **Estimate volume** from response byte counts and request counts per endpoint. For a stolen database credential without statement logs, assume everything that role could read.
- **Record the gaps**: expired retention, logging the attacker disabled, sampling.
- **Protect the evidence**: work on copies, hash the originals (`sha256sum`), note who handled what. Bring in a response firm when crown-jewel data is involved, the attacker held root or cloud admin, there is extortion, or the insurer requires it.

## Customer-facing audit logs

Build at the first enterprise deal that asks, or at Scale. With `tenant_id` and stable action names in place since Launch, it is a view, an export and an API over the existing table.

- **Scope**: the tenant's own events, including staff access to their account shown as vendor support. Internal-only metadata stays hidden.
- **Access**: tenant admins only; viewing and exporting the log are themselves logged; the tenant filter comes from the session, never from a parameter.
- **Functions**: filter by actor, action, target and date; CSV and JSON export as an asynchronous job; a cursor-paginated API; streaming to the customer's SIEM by webhook or bucket delivery on the enterprise tier.
- **Contract**: a documented, versioned event schema; UTC ISO 8601 timestamps; a stated retention period per plan; entries immutable for customer admins too.
- **Packaging**: the full log and streaming usually sit in the enterprise plan; a basic security-activity page (recent sign-ins, active sessions) belongs in every plan.

## Ask the user

- **Is there cyber insurance, and what is its incident hotline?** The policy may dictate which responders and lawyers can be used. Default: none; uninsured response costs fall on the company.
- **Who is the second person in an incident, and which lawyer handles a breach?** A solo founder cannot investigate, communicate and decide at once. Default: nobody named yet; choose both before launch.
- **Do customer contracts set notification deadlines or log-retention periods?** They override the defaults here. Default: none set; plan for the 72-hour authority deadline where GDPR applies, and keep 12 months of audit log.
- **Must reads of individual records be logged (health, financial or similarly sensitive data)?** It multiplies log volume and design work. Default: log exports and admin reads only.
- **Is there budget for a hosted log platform and managed threat detection?** Both are usage-priced. Default: yes at Launch for the audit-trail archive and threat detection; a full SIEM waits for Scale.
- **May the service be taken offline to contain an intrusion?** It trades availability for containment. Default: yes, and anyone on the response may do it.
