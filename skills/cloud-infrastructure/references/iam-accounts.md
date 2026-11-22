# Cloud accounts and IAM

Read this when: creating cloud accounts or projects, granting permissions to people, services or CI, or auditing who can do what. AWS terms lead; GCP and Azure equivalents are given where the model differs.

## Order of work for a new cloud footprint

Do these in sequence; each takes minutes on day one and days after an incident.

1. Create the organization and the top-level account with a company-controlled email (a group alias such as `aws-root@company.com`, not a personal inbox). Losing the mailbox loses the account.
2. Secure the root identity (next section).
3. Set a budget and billing alerts (`cost-control.md`).
4. Turn on single sign-on and create the human roles. Stop using root.
5. Create a separate account or project for production.
6. Turn on the organization-wide audit log and the account-level public-access blocks.
7. Create workload identities (service roles, CI federation) as workloads appear. No long-lived keys.

## The root identity

Root (AWS account root user; on GCP the Workspace or Cloud Identity super admin and the Organization Administrator; on Azure the Global Administrator) can do everything, including closing the account and removing every other control.

| Control | Detail |
|---|---|
| MFA | Phishing-resistant: a passkey or hardware security key. Register **two** authenticators; store the second offline (a safe, a co-founder). SMS is not acceptable here |
| No access keys | The root user must have zero access keys. If one exists, delete it after confirming nothing uses it (the key's last-used data shows this) |
| Password | Long, unique, in the company password manager with access limited to founders |
| Recovery path | Root email is a monitored alias with at least two recipients; phone number is one the company controls; alternate security, billing and operations contacts are set, so provider abuse and compromise notices reach someone |
| Use | Only for the few tasks that require it (changing the support plan, closing the account, some billing and recovery actions). Alert on any root sign-in |
| Member accounts | In an AWS organization, member-account root credentials can be centrally removed so only the management account has a root login to protect. Do this once the organization exists |
| Break-glass test | Twice a year, sign in with the backup authenticator and confirm the recovery email works. An untested recovery path fails when needed |

On Azure, keep two cloud-only emergency Global Administrator accounts excluded from conditional-access policies, with hardware MFA, monitored for any sign-in. On GCP, keep super admin accounts separate from daily accounts and few (two or three), and do not use them for cloud work.

## People: SSO and roles

Rule: no IAM users for humans, no shared logins, no long-lived access keys on laptops. People sign in through an identity provider and assume a role that yields credentials lasting hours.

- **AWS:** IAM Identity Center, connected to the company identity provider (Google Workspace, Microsoft Entra, Okta) or using its built-in directory for a solo founder. Assign **permission sets** per account. CLI access:

```bash
aws configure sso          # once per profile
aws sso login --profile prod-readonly
```

- **GCP:** users are Workspace or Cloud Identity accounts; grant roles to **groups**, never to individuals; `gcloud auth login` yields short-lived credentials. **Azure:** Entra ID users and groups with role assignments at subscription or resource-group scope; use Privileged Identity Management for just-in-time elevation where licensed.

Role set that suits a small team:

| Role | Who | Notes |
|---|---|---|
| Read-only | Everyone, default for production | Daily investigation, cost and logs |
| Developer / power user | Engineers in non-production | Broad, without IAM and organization changes |
| Admin | Founders or the one infrastructure owner, per account | Short session duration (one hour), used deliberately, MFA at the identity provider |
| Billing | Whoever reads the bill | Separate from technical admin |

A solo founder still needs this: two permission sets on one identity (read-only for everyday use, admin when changing things) prevents the stray destructive command in the wrong terminal, and makes adding the second person a five-minute task. Offboarding is then one action at the identity provider. Staff SSO and device policy belong to `0x:web-security`.

## Workloads: one identity per service

Each service, job and pipeline gets its own role with only what it needs. Shared "app role" identities mean one compromised service can read every bucket and secret.

| Where it runs | Identity mechanism | Trap |
|---|---|---|
| ECS / Fargate | **Task role** for the application's own AWS calls; **execution role** for the platform to pull the image and fetch secrets | Putting application permissions on the execution role, or sharing one task role across services |
| Lambda | Execution role, one per function or per tightly related group | A framework's default role shared by every function |
| EC2 | Instance profile | Everything on the host inherits it; require token-based metadata access |
| Kubernetes | Workload identity bound to a ServiceAccount | Falling back to the node role, which every pod on the node can use |
| GCP (Cloud Run, GCE, GKE) | A dedicated service account attached to the resource | Using the default compute service account, which carries a broad Editor role on many projects |
| GitHub Actions and other CI | OIDC federation: the pipeline exchanges its identity token for a short-lived role session | A trust policy that accepts any repository or branch |
| A PaaS or external SaaS that needs cloud access | Federation or a cross-account role with an external ID if supported; otherwise an access key for a dedicated least-privilege user, rotated, stored in the platform's secret store | Reusing a personal or admin key |

Static keys (AWS access keys, GCP service account JSON keys) are the last resort: they leak into repositories, logs and laptops and never expire. Where one is unavoidable, scope it to one purpose, record an owner and a rotation date, and alarm on use from unexpected networks. On GCP, block key creation with an organization policy once nothing needs it.

CI trust policy, scoped to one repository and its production environment:

```json
{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:<org>/<repo>:environment:production"
    }
  }
}
```

A `sub` condition of `repo:<org>/*`, or none at all, lets any repository in the organization (or anyone on the platform) assume the role. Use separate roles for plan (read-only) and apply or deploy (write), with the write role bound to a protected branch or environment. Pipeline hardening is in `0x:ci-cd-release` `pipeline-security.md`.

## Least privilege in practice

Write policies as specific actions on specific resources, with conditions where the service supports them.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::acme-prod-uploads/users/*" },
    { "Effect": "Allow", "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::acme-prod-uploads",
      "Condition": { "StringLike": { "s3:prefix": "users/*" } } }
  ]
}
```

The classic mistake this shows: object actions take the object ARN (`bucket/*`), bucket actions take the bucket ARN. Mixing them produces an access-denied error that looks like a missing permission.

Method that reaches least privilege without weeks of trial and error:

1. Start from what the code calls: list the SDK calls and resources. Not from a managed `FullAccess` policy.
2. If unknown, run the workload in non-production with a broader role and generate a policy from the audit log of what it actually used (IAM Access Analyzer policy generation on AWS; the IAM recommender on GCP), then scope resources by hand.
3. Deploy; read access-denied errors. The error names the action and resource: add exactly that.
4. Re-audit later for unused grants (below).

Permissions that are administrator access in disguise, and must not be granted to applications or CI with a wildcard resource:

- `iam:PassRole` on `*` (lets the holder attach any role, including admin, to a compute resource it controls). Scope it to the specific roles and add a condition on the service it may be passed to.
- Anything that edits policy: `iam:CreatePolicyVersion`, `iam:AttachRolePolicy`, `iam:PutRolePolicy`, `iam:UpdateAssumeRolePolicy`, `iam:CreateAccessKey` for other users.
- `sts:AssumeRole` on `*`; `kms:*` or key-policy edits; `secretsmanager:GetSecretValue` on `*`; `lambda:UpdateFunctionCode` on functions with stronger roles.
- On GCP: the basic roles Owner and Editor, `roles/iam.serviceAccountTokenCreator` and `roles/iam.serviceAccountUser` at project level (impersonation of every service account). Use predefined roles at the resource level, or custom roles.

CI that applies infrastructure necessarily holds broad permissions. Contain it instead of pretending to narrow it: bind it to the protected branch and environment, require review on that path, add a permissions boundary so roles it creates cannot exceed a ceiling, and let organization guardrails cover the catastrophic actions.

Resource-side policies matter as much as identity-side: a bucket policy, key policy or role trust policy with `"Principal": "*"` and no condition is public regardless of how tight the identities are.

## Separate accounts per environment

An account (AWS), project (GCP) or subscription (Azure) is the strongest isolation boundary the cloud offers: separate IAM namespace, quotas, blast radius and bill. IAM policies inside one shared account trying to separate "prod" from "dev" by tags or name prefixes fail eventually.

| Stage | Layout |
|---|---|
| Prototype | One account is acceptable. Create it inside an organization from the start so that adding accounts later needs no migration |
| Launch | Production in its own account. Everything else (staging, dev, experiments) in a second. The organization's management account runs **no workloads** and holds only billing, SSO and guardrails |
| Scale | Add a log-archive or security account receiving the organization audit trail, per-developer or per-team sandboxes with budgets, and separate accounts for regulated data if any |

Consequences to plan for: CI needs a role per account; container images are shared from one registry account by resource policy or pushed per account; DNS zones are delegated per environment (`staging.example.com` as its own zone) so non-production cannot touch production records; Terraform state is separate per account. Costs are otherwise zero: accounts are free.

Do not copy production data into the non-production account unmasked; it then needs production-grade controls.

## Auditing: unused permissions and public exposure

Enable once, at the organization level, at Launch:

| Capability | AWS | GCP | Azure |
|---|---|---|---|
| Audit log of API calls, all regions, to a bucket workloads cannot delete | CloudTrail organization trail | Cloud Audit Logs (admin activity is on by default; enable data access logs selectively) with a sink to a locked bucket | Activity log exported to a storage account or workspace |
| Find resources shared outside the account or publicly | IAM Access Analyzer external access analyzer | Policy Analyzer; Security Command Center findings | Defender for Cloud recommendations |
| Find unused roles, keys and permissions | Access Analyzer unused access findings (billed per analyzed identity); last-accessed data on each role; the credential report for keys and passwords | IAM recommender (role recommendations and insights) | Access reviews; sign-in and audit logs |
| Account-wide public-access block | S3 Block Public Access at account level; block public snapshots and images | Organization policy enforcing public access prevention on storage | Disallow public blob access at the storage-account level |
| Threat detection on the audit stream | GuardDuty | Security Command Center | Defender for Cloud |

Quarterly review, about an hour: every external-access finding is either intended (documented) or removed; every access key older than 90 days is
rotated or deleted; roles unused for 90 days are deleted; humans with admin are still the right humans; no security group is open to the world on
non-web ports (`cloud-networking.md`). Fix public exposure the day it is found; trim unused permissions on a schedule.

When a bucket must be public (static assets), make that one bucket public through a CDN with origin access rather than disabling the account-level block.

## Organization guardrails

Guardrails are deny rules set above the accounts that no account administrator can override: AWS service control policies (and resource control policies), GCP organization policies, Azure Policy at a management group. They limit; they grant nothing. Worth setting at Launch, since they are few and cheap:

| Guardrail | Why |
|---|---|
| Deny use of regions the company does not operate in (exempting global services) | Compromised credentials mine cryptocurrency in an unused region where nobody looks |
| Deny stopping or deleting the audit trail, threat detection and config recording | An attacker's first step |
| Deny leaving the organization; deny changes to account-level public access blocks | Keeps the other guardrails in force |
| Deny creation of IAM users and access keys (with a narrow exception role) | Forces SSO and roles |
| Deny root-user actions in member accounts | Root there should never act |
| GCP: disable service account key creation, restrict policy members to the company's domain, enforce public access prevention, restrict VM external IPs | Same intents in GCP's constraint model |
| Cap expensive resource types (large GPU instances) unless explicitly allowed | Bounds the cost of a compromise |

Traps: AWS service control policies do not apply to the management account, another reason nothing runs there. Test a new guardrail on a sandbox
account or organizational unit first; a region deny without exemptions for global services (IAM, the CDN, DNS, billing, support) breaks consoles and
deployments in confusing ways. Guardrails do not replace least privilege; they bound the damage when it fails.

## Ask the user

- **Who besides the founder can recover the root account if the founder is unreachable?** A bus-factor and governance decision. Default: a second authenticator held by a co-founder or stored offline in a location a named person can access, with the root mailbox reaching two people.
- **Which identity provider do staff already use?** SSO should hang off it. Default: the company's Google Workspace or Microsoft tenant; the cloud's built-in directory for a solo founder.
- **Who is allowed to change production, and should it require a second person's review?** Sets admin role membership and CI protections. Default: founders only, changes through reviewed pull requests, console admin for emergencies.
- **Which regions does the business intend to operate in?** Needed for the region guardrail and residency. Default: the one region in use plus global services.
- **Is there any third party (contractor, agency, SaaS tool) with access to the cloud account today?** Each is an identity to scope or remove. Default: replace shared keys with a role per party, time-limited.
