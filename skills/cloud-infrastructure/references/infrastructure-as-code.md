# Infrastructure as code

Read this when: defining, changing, importing, protecting or scanning cloud resources in Terraform, OpenTofu or Pulumi, or deciding whether to codify something at all. Commands are written as `terraform`; `tofu` accepts the same ones.

## What to codify, and what to leave alone

Infrastructure code is worth its upkeep when it prevents an expensive mistake or makes a rebuild possible. It is overhead when it mirrors a PaaS dashboard that one person touches twice a year.

| Situation | Decision |
|---|---|
| Prototype on a PaaS: one app, one managed database | No Terraform. Use the platform's own config file in the repo (`vercel.json`, `fly.toml`, `render.yaml`) and keep a short `INFRA.md` listing every manual setting, account and DNS record |
| Anything in a hyperscaler account beyond a single bucket | Codify from the first resource. Console-built cloud infrastructure becomes unreproducible within weeks |
| DNS records, IAM roles and policies, networks, databases, buckets, queues, secrets' existence (not values) | Codify at Launch wherever they live: these are the security-relevant and hard-to-recreate parts |
| A second environment is needed | Codify; this is the moment copy-by-clicking starts to drift |
| PaaS project settings, SaaS dashboards (monitoring, auth provider, CDN rules) | Codify when a provider exists and the setting is changed by more than one person or must match across environments; otherwise document |
| One-off experiments | Console, in a sandbox account with a budget, deleted afterwards |
| Application deploys (which image is running) | Not Terraform's job. CI deploys images; Terraform owns the service's shape. Mark the image attribute as ignored (below) or pass it as a variable from the pipeline |

Tool choice: Terraform or OpenTofu by default (largest provider and example base; the two remain close enough that the choice is about licensing preference and specific features such as OpenTofu's state encryption). Pulumi when the team strongly prefers writing TypeScript to HCL; everything below about state, plans, protection and review applies unchanged. The cloud's own tool (CloudFormation/CDK, Bicep) is fine if the project already uses it; do not mix two tools over the same resources.

## State, layout and modules

State is the mapping from code to real resources. It contains secrets in plain text (database passwords, generated keys), and losing or corrupting it is the worst routine IaC failure.

```hcl
terraform {
  required_version = "~> 1.10"
  backend "s3" {
    bucket       = "acme-tfstate-prod"
    key          = "network/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}
```

- Remote backend with locking, versioning and encryption, readable only by the infrastructure roles. The S3 backend locks natively with `use_lockfile` in current Terraform and OpenTofu releases; the older DynamoDB lock table is legacy. Turn on bucket versioning: it is the undo for a corrupted state. Pin the provider major version to whatever the project's lock file already uses.
- Commit `.terraform.lock.hcl`. Never commit `*.tfstate`, `*.tfvars` containing secrets, or the `.terraform` directory.
- Keep secrets out of state where possible: let the database manage its own master password in the secret manager, reference secrets by name, and use ephemeral or write-only arguments where the provider offers them.
- The state bucket and CI role are a bootstrap problem: create them with a tiny separate configuration (local state, applied once, then committed or migrated) and document it.

Layout that keeps changes small:

```text
infra/
  modules/            # only what is reused: service, database, network
  envs/
    prod/
      network/        # own state: VPC, subnets, DNS zone
      data/           # own state: database, buckets, queues
      app/            # own state: services, load balancer rules, IAM for apps
    staging/
      ...
```

- **One state per environment per layer.** A plan then touches tens of resources, not hundreds; a mistake in the app layer cannot destroy the database because the database is not in that state. Layers read each other through data sources or remote state outputs, in one direction (app reads data reads network).
- **Directories per environment over workspaces.** Workspaces share one backend config and one code path, and `terraform workspace select` is an easy way to apply to the wrong one. Separate directories make the target visible in the path and in the PR diff, and let production pin a different module version.
- **Write a module on the third copy, not the first.** Early modules guess the wrong abstraction. Keep variables few; a module that exposes every provider argument adds nothing. Pin external modules to a version, and prefer a short local module over a large community one that creates resources nobody reviewed.
- Set `default_tags` on the provider (`environment`, `service`, `managed-by = "terraform"`): cost attribution and drift hunting both depend on them.
- Prefer `for_each` over `count` for anything that may be removed from the middle: `count` identifies by index, so deleting item 0 makes every later item replace.

## Plans in pull requests

The reviewed artifact is the plan, not the HCL. Workflow:

1. On pull request: `terraform fmt -check`, `terraform validate`, lint and scan (below), then `terraform plan -out=tfplan -lock-timeout=60s` with a **read-only** role; post the plan text to the PR.
2. Review the plan (next section).
3. On merge to main: apply **the saved plan** from a job bound to a protected environment, with the write role obtained through OIDC (`iam-accounts.md`). Applying a fresh plan after merge can differ from what was reviewed.
4. One apply at a time per state (locking enforces it; serialize the CI job as well).

Hosted runners (HCP Terraform, Spacelift, env0, Atlantis self-hosted) do this out of the box and are worth it when hand-rolled CI becomes a chore; a GitHub Actions workflow is enough for one or two states. Applying from a laptop is acceptable at Prototype only, and never with a locally stored state.

## Reading a plan

Read the last line first: `Plan: 3 to add, 2 to change, 1 to destroy.` Any nonzero destroy count needs an explanation before anything else is read.

| Symbol | Meaning | Reaction |
|---|---|---|
| `+` | Create | Check names, sizes, public exposure |
| `~` | Update in place | Usually safe; check for restarts (instance class, parameter groups) and for "apply immediately" behavior on databases |
| `-` | Destroy | Stop. Intended? Stateful? |
| `-/+` | Destroy, then create (replacement) | Downtime and data loss for stateful resources. Look for the `# forces replacement` comment on the attribute that caused it |
| `+/-` | Create, then destroy (`create_before_destroy`) | Safer ordering; still new identity, new address |
| `<=` | Data source read | Harmless |

Attributes that commonly force replacement: names and identifiers, availability zone or subnet group, encryption settings, engine or storage type on some databases, instance user data, a load balancer's scheme, and anything derived from a value shown as `(known after apply)` that itself is being replaced: replacements cascade.

List destructive actions mechanically; CI should fail or require an extra approval when this prints anything for a stateful type:

```bash
terraform show -json tfplan \
  | jq -r '.resource_changes[] | select(.change.actions | index("delete")) | .address'
```

Causes of unintended destroys, and the fix for each:

- **Renamed a resource or moved it into a module**: Terraform sees a delete and a create. Add a `moved { from = aws_s3_bucket.a  to = aws_s3_bucket.uploads }` block; the plan then shows a move with no change.
- **Switched `count` to `for_each`, or reordered a list**: addresses changed. Use `moved` blocks per instance.
- **Removed a resource block to "stop managing" it**: that plans a destroy. Use a `removed` block with `lifecycle { destroy = false }`, or `terraform state rm`, to forget without deleting.
- **Provider major upgrade** changed a default or split a resource. Read the upgrade guide; upgrade in its own PR with an expected no-op plan.
- **Drift**: someone changed the resource by hand and the plan reverts it. Decide which side is right before applying.

An empty plan after a refactor is the proof the refactor was safe. Aim for it explicitly.

## Protecting stateful resources

Layer the protections; each covers a gap in the others.

```hcl
resource "aws_db_instance" "main" {
  # ...
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "main-final"
  backup_retention_period   = 14

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [password]
  }
}
```

| Layer | Stops | Does not stop |
|---|---|---|
| `lifecycle { prevent_destroy = true }` | Any plan that would destroy or replace the resource fails | Removing the whole resource block (the guard goes with it), or `state rm` followed by manual deletion |
| Provider-level protection (`deletion_protection` on databases and load balancers, termination protection, bucket `force_destroy = false`, key deletion windows) | Deletion by any tool, including the console, until the flag is turned off in a separate change | In-place changes that lose data |
| Final snapshots, backups, bucket versioning, point-in-time recovery | Makes a mistake recoverable | Nothing; this is the last line |
| Separate state for the data layer, plus an IAM or organization deny on delete actions for production data stores | A bad apply in another layer; a compromised CI role | Changes made in the data layer itself |

Apply these to: databases, buckets holding user data, DNS zones, KMS keys, secrets, static IPs that partners allowlist, and the state bucket itself. Replacing a database is never done through a `-/+` plan: create the new one, migrate, cut over, then remove the old one in a later change. Restore procedures are in `0x:postgres-database` `backup-recovery.md`.

## Importing existing resources and stopping drift

Import with blocks, reviewed like any change:

```hcl
import {
  to = aws_s3_bucket.uploads
  id = "acme-prod-uploads"
}
```

```bash
terraform plan -generate-config-out=generated.tf   # drafts resource blocks for import targets
```

1. Inventory what exists (console, resource explorer or tag editor, billing line items by service).
2. Import in dependency order and in small batches: network, then data, then compute.
3. Clean the generated configuration: remove computed and default-valued arguments, replace literal IDs with references.
4. Iterate until `terraform plan` shows the imports and **no changes**. Any remaining `~` is a difference between code and reality that would be applied; resolve it in code, not by applying.
5. Apply, then delete the `import` blocks.

Importing never modifies the resource; the risk is the first apply after it.

Stopping drift is mostly an access decision: once resources are in code, humans get read-only in production and an audited break-glass admin role (`iam-accounts.md`). Every emergency console change is followed by a PR that brings code in line. Detect the rest with a scheduled plan:

```bash
terraform plan -detailed-exitcode -lock=false   # exit 0 = no changes, 2 = drift or pending changes, 1 = error
```

Run it nightly per state and alert on exit code 2. Use `ignore_changes` only for attributes another system legitimately owns (an autoscaled `desired_count`, an image tag set by the deploy pipeline, a rotated password); each entry is a place where code no longer tells the truth, so comment why.

## Scanning and policy

| Check | Tool | Where |
|---|---|---|
| Syntax, types, references | `terraform validate`, `terraform fmt -check` | Pre-commit and CI |
| Provider-specific mistakes (invalid instance types, deprecated arguments) | TFLint | CI |
| Misconfigurations in code | Trivy (`trivy config .`) or Checkov | CI, failing on high and critical |
| Misconfigurations in the live account, including what was never codified | The cloud's posture service (Security Hub, Security Command Center, Defender for Cloud) or Prowler | Scheduled, weekly at Launch |
| Secrets committed in `.tf` or `.tfvars` | The repository's secret scanner | Pre-commit and CI |

Scanner output is noisy. Triage rule: fix immediately anything that makes data reachable or readable by the public (open security groups on non-web ports, public buckets, public snapshots, unauthenticated endpoints), wildcard IAM, and disabled encryption or logging on data stores. Suppress the rest explicitly, inline with a reason, so the gate stays meaningful; a scan nobody can pass gets switched off.

**Policy as code** is the next step when more than a couple of people write infrastructure, or an auditor asks how rules are enforced: write the team's own non-negotiables as tests against the plan JSON (OPA with Conftest, Checkov custom policies, or the hosted runner's policy engine) and require them in CI. Start with five or fewer, such as: no security group open to the world except 80/443 on load balancers; no storage bucket without the public-access block; every resource carries the required tags; no database without deletion protection and backups; no IAM policy with `Action: "*"` on `Resource: "*"`. Policy in CI checks proposed changes; organization guardrails (`iam-accounts.md`) stop the action whatever tool attempts it; scheduled drift detection and posture scans catch what bypassed both. All three are needed at Scale; the scanner defaults plus guardrails are enough at Launch.

## Rebuilding an environment from code

The claim "we can rebuild from Terraform" is false until it has been done. What is usually missing:

- **Bootstrap**: organization, accounts, state bucket, CI federation. Document the order or script it.
- **Manual steps nobody wrote down**: domain registration and delegation of name servers, DNS validation for certificates, email sending approval and domain verification, quota increases, marketplace subscriptions, third-party OAuth app credentials, webhook endpoints registered with providers.
- **Secret values**: code creates the secret's container, not its content. Keep a list of every secret, its source and who can reissue it.
- **Ordering across states**: network, then data, then app; plus resources that need two applies or a wait (certificate validation, DNS propagation).
- **Global names**: bucket names and some identifiers are globally unique and may be held for a while after deletion; parameterize by environment and account.
- **Data**: restoring the database and object storage is a separate, timed procedure.

Rehearse at Launch and then twice a year: stand up a complete throwaway environment in a fresh account or project from an empty state, deploy the application, run the smoke tests, record how long it took and every manual step hit, fix the code, then destroy it. The same code path gives ephemeral preview or load-test environments later. Recovery objectives and disaster-recovery planning belong to `0x:site-reliability`.

## Ask the user

- **Is it acceptable for production changes to be made in the console in an emergency?** Decides how strict read-only access is. Default: yes through a break-glass role, with a follow-up PR within a day.
- **Who must approve a production infrastructure change?** Solo founders cannot have a second reviewer; the substitute is a plan posted to a PR and a deliberate merge. Default: plan on PR, apply on merge to main, manual approval step for production.
- **Which resources would be unrecoverable or contract-breaking if deleted?** These get every protection layer. Default: databases, user-data buckets, DNS zones, encryption keys, allowlisted IPs.
- **How long may a full rebuild of production take?** Sets how much rehearsal and automation are worth. Default: within one working day at Launch.
- **Terraform or OpenTofu?** A licensing and ecosystem preference, not a technical necessity for internal use. Default: keep what the project uses; for greenfield, either, chosen once and used everywhere.
