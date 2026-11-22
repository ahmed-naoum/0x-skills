# Security testing and disclosure

Read this when: checking the product's own endpoints for access-control holes, verifying headers, TLS and cookies from outside, running a manual security pass, adding scanners to CI, buying a penetration test, fixing findings, publishing `security.txt` and a disclosure policy, or rehearsing a breach.

## What each method finds

| Method | Finds | Misses | Stage |
|---|---|---|---|
| Two-account access tests | Cross-tenant and privilege flaws, the most common serious class | Everything else | Launch, mandatory |
| External scanners | Header, TLS, cookie and exposure mistakes | Application logic | Launch |
| CI scanners | Secrets, vulnerable dependencies, dangerous code patterns | Authorization and business logic | Prototype for secrets and dependency alerts; Launch for the rest |
| Manual pass with an intercepting proxy | Injection, auth-flow and logic flaws in the features exercised | What nobody thought to try | Launch, per significant release |
| Penetration test | What an experienced outsider finds in a fixed number of days | Anything out of scope or out of time | When a customer or framework asks, or sensitive data is held |
| Disclosure policy | Whatever strangers stumble on | Nothing systematic | Launch |
| Tabletop exercise | Gaps in the response, not in the product | Product flaws | Before Scale, then yearly |

Test only systems the company owns or has written permission to test. Third-party services (payment, auth, hosting platforms) are out of bounds beyond the product's own integration, hosting providers publish rules for testing on their infrastructure, and denial-of-service testing is excluded nearly everywhere.

## Two-account access-control testing

Broken access control is the leading class of serious web vulnerability, and no scanner finds it, because a scanner does not know who should see what.

Fixture: tenant A with an admin (A1) and a low-privilege member (A2); tenant B with a user (B1); and no session at all. Create one object of every type in tenant A. Then, for every endpoint and server action that takes an identifier:

| Actor | Attempt | Expected |
|---|---|---|
| Anonymous | Read, update, delete and list A's objects | 401, or a redirect to sign-in |
| B1, other tenant | The same, using A's IDs | 404 or 403, consistently; no data in the body; nothing changed |
| B1 | Reference A's object from B's own request, such as A's `projectId` in the body of B's create or update | Rejected |
| A2, low privilege | Admin-only operations: invite, change roles, billing, delete the tenant, change its own role | 403 |
| Removed member, revoked key, expired invite | Any call with the old session or token | 401 |

Where the check is usually missing:

- IDs in the body, query string or a header, when only the path parameter is checked.
- Nested routes: `/orgs/B/projects/<A's project>` verifies membership of the organization in the URL but never ties the child to it.
- Bulk, batch, export and download endpoints; presigned-URL generators; direct storage URLs.
- Search, autocomplete, counts and aggregates, which leak names or totals across tenants.
- Realtime channels with guessable names; there the subscription is the read.
- Other methods on the same path (a protected GET beside an unprotected PUT), alternate formats, old API versions.
- Server actions, which are callable directly with any arguments whatever the UI renders.
- State after revocation: a removed member's live session, a downgraded role, a deleted user's API key.

Assert on three things, not on the status alone: the status, that the body contains none of A's data, and that A's object is unchanged afterward. Random IDs are not authorization; identifiers leak through logs, referrers and shared links.

Automate this as an integration suite and keep it exhaustive: generate the route list from the code and fail the build when a route has no entry in the matrix.

```ts
const cases = [
  { name: "read",   run: (c: Client) => c.get(`/api/projects/${aProject.id}`) },
  { name: "update", run: (c: Client) => c.patch(`/api/projects/${aProject.id}`, { name: "x" }) },
  { name: "delete", run: (c: Client) => c.delete(`/api/projects/${aProject.id}`) },
];
for (const actor of [anonymous, userB]) {
  for (const tc of cases) {
    it(`${actor.label} cannot ${tc.name} tenant A's project`, async () => {
      const res = await tc.run(actor.client);
      expect([401, 403, 404]).toContain(res.status);
      expect(await res.text()).not.toContain(aProject.name);
      expect(await loadProject(aProject.id)).toEqual(aProject);
    });
  }
}
```

For manual exploration, two browser profiles and a proxy extension that replays each request with the second account's session do the same job. The authorization design itself: `0x:auth-identity` (`authorization.md`); tenant isolation: `0x:backend-architecture` (`multi-tenancy.md`).

## External checks: headers, TLS, cookies, exposure

| Check | Tool | Pass |
|---|---|---|
| Security headers | A header scanner (securityheaders.com, the HTTP Observatory on MDN) | CSP, HSTS, `nosniff`, framing and referrer policy present. Read the findings, not the letter grade: graders disagree about strict nonce policies |
| CSP quality | Google's CSP Evaluator | No high-severity finding |
| TLS | Qualys SSL Labs, or `testssl.sh` offline | Grade A; no legacy protocol versions; valid chain |
| Cookies | Browser DevTools after sign-in | The session cookie is `Secure`, `HttpOnly`, `SameSite=Lax` or `Strict`, and host-only unless subdomains need it; ideally `__Host-` prefixed |
| Hostnames | Certificate-transparency search for the domain | Every name is known, live and gated |
| Ports | `nmap -Pn -p-` from outside the network | 80 and 443 only |
| Email authentication | SPF, DKIM and DMARC lookup (`0x:email-notifications`, `deliverability.md`) | Aligned, DMARC at enforcement |

```bash
for u in / /api/health /does-not-exist /favicon.ico; do
  echo "== $u"
  curl -sI "https://example.com$u" | grep -iE '^(content-security-policy|strict-transport-security|x-content-type-options|referrer-policy|x-frame-options|set-cookie):'
done
```

Check an API route, an error page, a redirect and a static asset as well as the home page; headers set in page code are usually missing on the others. Run the header check as a smoke test against each deploy, and the full set monthly and after any infrastructure change. TLS and HSTS configuration: `0x:web-networking`; cookie design: `0x:auth-identity` (`sessions-tokens.md`).

## Manual pass with an intercepting proxy

Tools: Burp Suite Community, ZAP or Caido. Use a dedicated browser profile routed through the proxy, against staging or a local build with production-like configuration. Active testing against production creates junk data, sends real email and can take the service down; if production is the only option, restrict the work to manual requests on test tenants.

Method: walk every feature once so that the proxy records each request, then replay and modify. Budget two to four hours per significant release (rule of thumb).

| Area | Try |
|---|---|
| Access control | The two-account matrix through the repeater: swap the session, swap IDs, change the method, add `role` or `tenantId` to bodies, request admin URLs directly |
| Injection | In every parameter: a single quote, `"><img src=x onerror=alert(1)>`, `{{7*7}}`, `$(sleep 5)`, `../../etc/passwd`, and in any URL field a URL to an external catch-all host and to `http://169.254.169.254/`. Watch for errors, delays and reflections |
| Stored XSS | Payloads in names, organization names, filenames and anything displayed later, above all in the admin panel |
| Authentication | Reset flow: token reuse, a token in a response body, a changed `Host` header altering the emailed link. Brute-force limits on sign-in and one-time codes. An old session cookie replayed after sign-out and after a password change. Differences in response or timing that reveal whether an account exists |
| Tokens | Collect twenty and compare them for sequence or timestamps; alter a JWT's algorithm, strip its signature, replay it after expiry |
| Configuration | Malformed JSON and wrong types (do stack traces come back?); `Origin: https://evil.example` (reflected with credentials?); `Cache-Control` on personalized responses, which must be `no-store` or `private` |
| Business logic | Negative and zero quantities, a price in the request, skipped steps, the same request sent twenty times in parallel |
| Files | Upload `.html` and `.svg` containing script and open the served URL; mismatch extension and content type; traversal in the filename; an oversized file |
| Resource limits | Huge bodies, deep JSON nesting, long strings in fields validated by a regex. Any 500 is an unhandled input and a finding |
| Detection | Afterward, look for the session in the audit log and the alerts. What was not recorded is a logging gap |

Use the OWASP Web Security Testing Guide as the exhaustive checklist and the Application Security Verification Standard as the requirements list: its first level is a reasonable target at Launch, its second for products holding sensitive data.

## Scanners in CI

| Layer | Default | Gate |
|---|---|---|
| Secrets | Host secret scanning plus gitleaks | Block on any finding |
| Dependencies | Host dependency alerts; `pnpm audit` or `osv-scanner` | Block on high severity in production dependencies (`supply-chain.md`) |
| Static analysis | Semgrep with community rules, or CodeQL where the plan includes it | Block on new high-confidence findings in changed code |
| Infrastructure as code, Dockerfiles | `trivy config .` or Checkov | Block on high severity |
| Container images | `trivy image` | Block on fixable high and critical |
| Dynamic scan | ZAP baseline (passive) against staging, weekly | Report only |

```bash
docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t https://staging.example.com
```

Wiring rules:

- Pull-request checks fail only on new findings in changed code. A gate that fails on the historical backlog gets disabled within a month; the backlog goes to a scheduled full scan and a tracked list.
- Keep pull-request security checks to a few minutes; move slow scans to a schedule.
- One inbox for findings (the host's code-scanning view or pull-request comments), not five dashboards.
- Triage each finding within its deadline. Exploitable: fix. Real but unreachable: fix when cheap, otherwise document. False positive: suppress inline with the rule ID and a reason, never by disabling the rule globally. A rule that is mostly noise after a month is tuned or removed.
- Scanners are dependencies with access to the pipeline. Pin their actions to a commit SHA and their images or binaries to a version or digest, and run them in jobs that hold no deploy credentials: widely used CI actions, security scanners among them, have been hijacked to steal pipeline secrets.
- The highest-value rules encode the project's own invariants:

```yaml
rules:
  - id: no-sql-raw
    languages: [typescript]
    severity: ERROR
    message: sql.raw() bypasses parameterization; use the sql template tag or an allow-list map.
    pattern: sql.raw(...)
```

Others worth writing: every route handler calls the session helper; no `dangerouslySetInnerHTML` without the sanitizer; no `child_process.exec`. For reviewing a diff with a model, use the `security-review` skill; it complements these gates and does not replace the two-account suite.

## Commissioning a penetration test

When: a customer or framework requires one (commonly yearly), before holding sensitive data at Launch, or after a major change to authentication or architecture. Not before the cheap work above is done, or the day rate buys a report about missing headers.

- **Scope document**: targets (a production-like staging environment with seeded data, plus API documentation); exclusions (third-party services, denial of service, social engineering unless wanted); the time window; contacts and an emergency stop; data-handling rules.
- **Gray-box by default**: give credentials for two tenants and every role, plus documentation. Black-box testing spends the budget on discovery; source access (white-box) yields the most per day where trust allows. Insist that cross-tenant testing is in scope.
- **Allow-list the testers' addresses** in the WAF and rate limiter unless those are the subject; the purchase is a test of the application.
- **Choosing a firm**: named testers with web-application experience, a sample report, a stated methodology, the number of manual person-days, a retest included, and a summary letter that can be shared with customers. A very low price means a rebadged automated scan.
- **Size and timing**: a small SaaS application with an API typically takes one to two tester-weeks (rule of thumb); get two or three quotes. Book weeks ahead, and finish at least a month before the report is needed, to leave time for fixes and the retest.
- **During the test**, watch the product's own logs and alerts. Whether the testers were noticed is a free detection test.

Triage the report by exploitability, not by its labels. For each finding: reproduce it; establish the
preconditions (no account, any account, a specific role, a victim's click, a network position); establish the
impact (cross-tenant data, account takeover, code execution, or information only); check whether it chains with
another finding. Reports tend to inflate hardening items (a missing header, a verbose banner, a flag on a
non-session cookie) and sometimes under-rate chains. Re-rate on the product's own scale, dispute errors during
the draft phase, and record accepted risks with their reasons. The full report is confidential and shared only
under NDA; customers get the summary letter and the retest result.

## Fixing findings

Deadlines run from the day of triage. Rule of thumb, shared with dependency advisories; never promise customers tighter ones than the team can meet.

| Severity | Meaning in the product | Deadline |
|---|---|---|
| Critical | Reachable without an account or by any user: cross-tenant data, account takeover, code execution, payment manipulation; or anything under active exploitation | Mitigated within 24 to 72 hours, fixed within 7 days |
| High | The same impact behind a real precondition | 30 days; aim for 14 |
| Medium | Limited impact, or hard to exploit | 90 days |
| Low, informational | Hardening | Batched quarterly, or accepted in writing |

Procedure for each finding:

1. Reproduce it and write the failing test first, at the level that catches the class: an entry in the access matrix for a missing check, a rendering test with the payload for XSS, a parallel-request test for a race.
2. Fix the class, not the instance. Search for siblings of the pattern, move the check into a shared layer, and add a lint or scanner rule so that it cannot return.
3. Mitigate first when the fix is slow: disable the feature, add an edge rule, tighten validation. A mitigation gets its own ticket with an expiry date.
4. Deploy, then verify in production with the original proof of concept.
5. Search the logs for earlier exploitation of the same flaw. If it was used before it was reported, it is an incident (`logging-breach-response.md`).
6. Have the reporter or tester confirm the fix.
7. Record the finding, root cause, fix commit, test and dates. This record answers audit and questionnaire requests later.

Keep exploitable detail out of public issue trackers and commit messages until the fix is deployed.

## security.txt and a disclosure policy

Serve `https://example.com/.well-known/security.txt` as plain text (in Next.js, the file `public/.well-known/security.txt`):

```text
Contact: mailto:security@example.com
Expires: 2027-11-01T00:00:00Z
Preferred-Languages: en
Canonical: https://example.com/.well-known/security.txt
Policy: https://example.com/security
```

`Contact` and `Expires` are required. Set the expiry less than a year ahead and put the renewal in the calendar; an expired file signals an abandoned process. `security@` reaches at least two people, or pages the founder, and replies automatically with the expected timeline.

The policy page states:

- **Scope**: the domains and applications covered, and the exclusions (third-party services, denial of service, social engineering, physical access, scanner output without a demonstrated impact).
- **Safe harbor**: good-faith research within the rules is authorized and will not be met with legal action. Have counsel read the wording.
- **Rules**: use own accounts; stop at the first sight of other people's data and report; no destruction or degradation; no public disclosure before a fix or an agreed date.
- **What to expect**: acknowledgment within 3 business days and triage within 10 (rule of thumb), status updates, credit if wanted.
- **Rewards**: stated outright, including "none". Ambiguity invites payment demands for trivial findings.

Handling: acknowledge, reproduce, rate, fix on the deadline scale, tell the reporter, credit. Expect mass-mailed
scanner output asking for money: answer once with the policy, pay nothing for non-issues, and still read each
one for a real finding. Never threaten a researcher. A message that demands payment under threat of publication
is extortion, not a report; it goes to the incident plan and counsel.

A paid bug bounty waits until Scale. It needs triage capacity, and opening one draws a flood. Start private, on a platform with managed triage, once penetration tests have stopped finding easy bugs.

## Tabletop exercise

A 60 to 90 minute walk through a breach scenario by the people who would respond. A solo founder runs it with one outside person as facilitator. Hold it yearly, and after major changes to the team or architecture.

Format: the facilitator reveals the scenario in stages (the first signal; new information 15 minutes in;
escalation at an hour; outside pressure the next day). At each stage participants say exactly what they would
do, then open the tool and prove they can: find the control that revokes all sessions, pull the relevant logs
and check their retention, read out the insurer's phone number. The value lies in "show me", not in "we would".

Scenarios; pick the ones the threat model ranks highest:

- A stranger emails a screenshot of another tenant's data.
- A cloud billing alert at night, and instances nobody started.
- The founder's laptop or source-host account is compromised.
- A dependency in the lockfile is reported malicious, having been live for six hours yesterday.
- Customers receive phishing mail sent through the product's email provider.
- An extortion message arrives with a sample of the user table.
- A key vendor announces a breach.

Questions to force at each stage: How do we know it is real? Who leads? What do we shut off, and who has the access to do it? Which logs prove the scope, and do they still exist? What do we tell customers, when, and who writes it? Which legal clock started, and when? Whom do we call? How do we talk if chat and email are compromised? What gets rotated, in what order, and how long does it take?

Output: a list of gaps with owners and dates, an updated plan, and a dated record of the exercise as audit evidence. Typical findings: nobody knows how to revoke all sessions; logs last a week; one person holds the registrar login; no lawyer has been chosen. Pair it with two real drills: rotate one production secret and restore one backup (`0x:site-reliability`, `disaster-recovery.md`).

## Ask the user

- **Does a customer, contract or framework require a penetration test, and by what date?** It sets scope and lead time. Default: not yet; do the two-account suite and scanners first.
- **Is there a staging environment that mirrors production, or must testing touch production?** Active testing on production risks data and uptime. Default: build a seeded staging environment; no active scans on production.
- **What budget exists for an outside test?** Day rates vary widely by region and firm. Default: defer until required, then gray-box at the smallest scope that covers the tenant boundary.
- **Will reporters be paid?** A stated position prevents disputes. Default: no rewards, public thanks, written in the policy.
- **Who reads `security@`, and how fast?** An unanswered report tends to become a public one. Default: the founder plus one other person; acknowledgment within 3 business days.
- **What remediation deadlines have been promised to customers?** Promised deadlines bind; internal ones guide. Default: none promised; adopt the table above internally before offering it externally.
