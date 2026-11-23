# Agent permissions and governance

Read this when: deciding what an agent may run, read, reach on the network, push or deploy;
what code and customer data may go to AI tools; writing a team policy for AI tools; defending
against prompt injection; or tracking and capping agent spend.

## The threat model

A coding agent is a process that runs commands with the privileges of the user who started it,
chosen by a model that reads untrusted text. Harm comes from two directions: **mistakes**
(`rm` in the wrong directory, a force push, a migration against the wrong database) and
**manipulation** (prompt injection in an issue, a web page, a dependency or a tool result).
Controls must hold when the model is wrong or manipulated, so structure beats instructions:
which credentials exist in the environment, which hosts are reachable, what the token and the
branch rules allow. A line in CLAUDE.md saying "never deploy" is not a control.

The useful lens is the "lethal trifecta": access to private data, exposure to untrusted
content, and a way to send data out. An agent with all three can be steered into exfiltration.
Remove at least one leg in every environment an agent runs in.

## No production credentials where agents run

| Environment | May hold | Must not hold |
|---|---|---|
| Local interactive session | Development database, test-mode payment and email keys, a GitHub login | Production database URLs, live payment keys, cloud admin credentials, production cluster contexts |
| Local unattended (permission prompts off) | Only what is inside a container or VM built for it | Any host credential mounted in; unrestricted network |
| Vendor cloud sandbox | Repository, setup script, scoped development secrets | Production secrets |
| CI agent job | Model API key, a token with the minimum repository scope | Deploy, cloud or database secrets |
| Production | Nothing. Agents never get production access | |

Production changes go through CI/CD from merged code. Data fixes go through a reviewed script
run by a human or a pipeline, with a dry-run count first.

The common leak is the shell, not the repository. An agent inherits the environment of the
terminal that started it: exported `AWS_*` or `DATABASE_URL` variables, and every logged-in
CLI (hosting, database, payment provider, `gh` with broad scopes, `gcloud`, `kubectl`). If the
terminal can reach production, so can the agent.

```bash
env | grep -iE 'key|token|secret|password|database_url|aws_|gcp|azure' | cut -d= -f1
gh auth status
kubectl config current-context 2>/dev/null
```

Fix: run agents under a separate OS user, in a container, or from a shell profile without
production variables, and keep production logins on a different machine profile or behind
hardware-backed MFA.

## Sandboxing options

| Option | What it enforces | Use |
|---|---|---|
| Permission prompts with an allowlist | Approval per action outside the allowlist | Default interactive mode. Allowlist safe commands so prompts stay rare and get read |
| The tool's OS-level sandbox (Claude Code: `/sandbox`) | File writes confined to the project, network limited to allowed domains, applied to every subprocess | Routine local work with fewer prompts |
| Devcontainer or VM with an egress firewall | Process, filesystem and network isolation from the host | The only acceptable place for skipping permission prompts (`--dangerously-skip-permissions`) |
| Vendor cloud sandbox or CI runner | A disposable machine per task | Unattended and parallel runs |

Even inside a container, an agent can send anything it can read, including its own API key, to
any host the network allows. Isolation narrows the blast radius; the network allowlist closes
the exit.

Permission rules are not a sandbox. In Claude Code, `Read` and `Edit` deny rules govern its own
file tools; `cat .env` through the shell is a different path that only an OS-level sandbox or a
missing file stops. Bash rules match command prefixes, so rules that try to constrain arguments
are easy to route around (`rm -fr`, `bash -c "..."`, a script file). Treat Bash rules as
convenience and as speed bumps for mistakes; treat the sandbox, the network and the absence of
credentials as security.

## Permission configuration

Committed `.claude/settings.json` sets the team baseline; `.claude/settings.local.json` holds
personal additions and stays out of git; user settings apply across projects; managed policy
settings, deployed by an administrator, override all of them.

```json
{
  "permissions": {
    "allow": [
      "Bash(pnpm typecheck)",
      "Bash(pnpm lint:*)",
      "Bash(pnpm test:*)",
      "Bash(pnpm vitest:*)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "Bash(git log:*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(pnpm add:*)",
      "Bash(pnpm db:migrate)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Bash(git push --force:*)",
      "Bash(rm -rf:*)"
    ]
  }
}
```

Approval matrix, as a default:

| Action | Default | Why |
|---|---|---|
| Read code, run typecheck, lint, tests, `git status/diff/log` | Allow | The feedback loop; prompting here causes approval fatigue |
| Edit files in the repository | Allow on an agent branch (acceptEdits) | Git is the undo |
| Commit on the agent's branch | Allow | Same |
| Add or upgrade a dependency | Ask | Supply chain and maintenance cost |
| Push the agent's branch | Ask, or allow when rulesets protect `main` | The server-side rule is the real gate |
| Force push, `reset --hard` on shared branches, delete branches | Deny | Destroys others' work |
| Migrations against the local database | Allow | Disposable |
| Migrations or writes against any shared database | Deny | Not reversible by reverting code |
| Deploy CLIs, `terraform apply`, `kubectl apply/delete`, package publish | Deny | CI only, from merged code |
| Fetch arbitrary URLs | Ask; allowlist documentation domains | Exfiltration and injection path |
| Read `.env`, `~/.ssh`, `~/.aws`, credential stores | Deny, and sandbox | Secrets |

Client-side prompts are the second layer. The first is on the server and holds whatever the
agent does: rulesets on `main` (pull request required, status checks required, no force push,
no bypass for bot tokens), deploys triggered only by CI on `main`, a production database not
reachable from developer networks, and cloud roles that require MFA for humans. For a team,
managed settings can also disable the permission-skipping mode on company machines.

## Secrets and network access

- **Development needs no real secrets.** Test-mode payment keys, sandbox email, a local
  database with seed data. Production secrets live in the host's secret store and are injected
  at runtime; they never sit in a local `.env` (`0x:web-security`, secrets).
- **Agent tokens are separate, scoped and short-lived**: a fine-grained token limited to the
  repositories and permissions the task needs, revocable without breaking the founder's own access.
- **Network allowlist for unattended runs**: the package registry, GitHub, the model API and
  the documentation domains in use. Everything else is blocked; egress is how injected
  instructions get data out.
- **A secret that entered the agent's context is exposed.** Transcripts are stored on disk
  locally and, depending on plan and settings, by the vendor. Rotate any production secret an
  agent has read; do not debate whether it "really" left.

## What code and customer data may go to AI tools

| Data | Default | Notes |
|---|---|---|
| The company's own source code | Allowed under business or API terms that exclude training | Consumer plans can permit training depending on account settings: check the account type and setting |
| Secrets and keys | Never | Deny rules, sandbox, no real secrets in development |
| Production customer data (personal data, customer content) | Not in prompts | Use synthetic or seeded data. If one debugging case truly needs real data: minimize, pseudonymize, and only with a vendor under a DPA listed as a subprocessor (`0x:privacy-compliance`) |
| Logs, error reports, support tickets | Scrub personal data first | Stack traces often carry emails, tokens and request bodies |
| A client's code or data (agency or contract work) | Check the contract first | Many contracts restrict third-party processing; enterprise customers ask about it in security reviews |
| Regulated data (health records, card numbers) | Never into general-purpose tools | Sector rules apply |

For each tool, record the account type, whether inputs can be used for training, the retention
period, whether zero-data-retention is available, the processing region, and the subprocessor
list. Terms change; re-check them when the plan or vendor changes.

## Team policy for AI tools and code provenance

One page in the repository (`docs/ai-policy.md`), short enough that people read it:

1. **Approved tools and accounts.** Company-managed business accounts only; no personal
   accounts on company code.
2. **Data rules.** The table above, adapted.
3. **Accountability.** The person who opens or merges a pull request owns every line in it,
   whoever or whatever typed it. "The agent wrote it" is never an incident explanation.
4. **Provenance.** Agent-authored commits carry a trailer (such as `Co-Authored-By`) or the
   pull request a label, with a link to the session where the tool provides one. This serves
   incident investigation, measurement, customer questionnaires and IP questions; the legal
   status of generated code is `0x:privacy-compliance`.
5. **Review rules by risk tier**, and agents never merge (`verification-review.md`).
6. **Agent configuration is code.** `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.mcp.json` and
   workflow files have code owners and get reviewed like CI configuration.
7. **Permission baseline.** Shared settings committed; permission-skipping only in sandboxes.
8. **Incidents.** How to report a leaked secret or a harmful agent action, and how to revoke
   agent tokens and API keys fast.
9. **Spend limits** and who can raise them.

Revisit it quarterly. Security questionnaires from larger customers increasingly ask how AI
tools touch code and data; the policy is the answer (`0x:sales-support`, procurement).

## Prompt injection from what agents read

Untrusted text reaches agents through issue and pull request bodies, comments and commit
messages from others; fetched web pages; dependency READMEs and source under `node_modules`;
MCP tool results (tickets, emails, error messages that embed user input); and the files of any
repository opened, including `CLAUDE.md`, `AGENTS.md`, `.claude/settings.json` (hooks there are
shell commands), `.mcp.json` (servers there are processes), devcontainer files and package
install scripts.

Defenses, by trifecta leg:

| Leg | Defense |
|---|---|
| Untrusted content | Agents that process outsiders' text get read-only tools and no secrets; CI agents trigger only on trusted actors or a maintainer's label |
| Private data | No production credentials; sandboxed filesystem; deny reads of credential paths |
| Way out | Network allowlist; no auto-approved fetches; outbound actions (comments, issues, pushes outside the agent branch) need approval or are limited to the repository |

Before trusting an unfamiliar repository, read its `.claude/`, `.mcp.json`, agent instruction
files and `package.json` scripts. Claude Code asks whether to trust a new folder and whether to
enable project MCP servers; those prompts are the moment to look, not to click through. Warning
sign during a run: an agent that suddenly wants to fetch a URL, read credentials, or edit CI or
agent configuration during an unrelated task. Stop it and inspect what it last read. Telling
the model to "ignore instructions found in files" reduces the rate; it does not make the
environment safe.

## Spend and budgets

Cost drivers: long contexts (every turn re-reads the context), large tool outputs, multi-agent
fan-out, unattended loops, and the largest model used for mechanical tasks. Model choice and
pricing details are the `claude-api` skill.

- **Individuals**: a subscription plan gives a predictable cost with usage limits; API billing
  suits CI and automation. In Claude Code, `/cost` shows session spend on API billing.
- **Attribution**: separate API keys or workspaces for interactive use, CI and scheduled jobs,
  so a runaway is visible by source. Set spend limits and alerts in the provider console.
- **Per-run caps**: `--max-turns`, CI `timeout-minutes`, `concurrency` groups, and triggers on
  mention or label rather than on every event.
- **Teams**: Claude Code can export usage and cost metrics through OpenTelemetry; a dashboard by
  person and repository shows outliers.
- **Budget rule of thumb**: set the hard monthly cap at an amount acceptable to lose to one
  runaway loop, and review spend per merged pull request monthly
  (`parallel-automation.md`).

## Ask the user

- **Which credentials does your development machine and shell hold?** The agent can use all of
  them. Default: assume production access is present until the checks above say otherwise.
- **Are your AI tool accounts business or consumer accounts, and what are their training and
  retention settings?** Default: allow own code only under business terms; no customer data.
- **Do customer or client contracts restrict AI processing of their data or code?** Default:
  check enterprise and agency contracts before sending anything of theirs.
- **What monthly AI spend is acceptable, and per what?** Default: a hard cap with alerts at
  half and most of it, separate keys per use.
- **Is the repository public, or do outsiders file issues an agent may read?** Default:
  maintainer-only triggers and read-only, secret-free jobs for outside content.
