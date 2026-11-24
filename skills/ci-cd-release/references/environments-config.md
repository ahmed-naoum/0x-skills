# Environments and configuration

Read this when: adding an environment, wiring per-environment configuration into a deploy, the app
crashed or misbehaved because a variable was missing or wrong, setting up preview environments or
staging data, or chasing a difference between a laptop, CI and production.

## Which environments to run

| Environment | Prototype | Launch | Scale |
|---|---|---|---|
| Local development | yes | yes | yes |
| CI (ephemeral services per run) | yes | yes | yes |
| Preview per pull request | when the platform gives it for free | yes | yes |
| Staging (long-lived) | skip | only for a reason listed under "What staging is for" | yes |
| Production | yes | yes | yes |

Do not create a shared long-lived `dev` environment. Nobody owns it, it drifts within weeks, and
previews plus local development cover its uses.

## Separate everything that holds state or sends something

An environment is separate only if a mistake in it cannot touch production. Share code and
infrastructure definitions; separate the rest:

| Resource | Rule |
|---|---|
| Database | Own instance or branch per environment. A non-production app never holds a production connection string. |
| Secrets | Different value in every environment: session and signing secrets, encryption keys, API keys. A session secret shared with staging lets a staging cookie authenticate in production. |
| Payment provider | Test mode or sandbox keys outside production. Live keys exist only in the production secret store. |
| Email, SMS, push | Sandbox mode, or a recipient allowlist enforced in code (own domain only). Staging emailing real customers is the classic incident. |
| OAuth clients | Separate client per environment with its own redirect URIs. |
| Webhook endpoints | Separate endpoint and signing secret per environment at each provider. |
| Object storage, queues, caches | Separate buckets, queues, key prefixes or instances. A staging worker on the production queue processes real jobs. |
| Cloud access | From Launch: production in its own cloud account or project (`0x:cloud-infrastructure`, `iam-accounts.md`). |
| Domains and cookies | Non-production on a different registrable domain, or cookies scoped to the exact host. A cookie set for `.example.com` by `staging.example.com` is sent to production. |
| Search engines | `X-Robots-Tag: noindex` and access protection on every non-production URL. |
| Analytics and error tracking | Separate project, or an `environment` tag on every event, so test traffic stays out of metrics. |

Name the environment with its own variable, for example `APP_ENV` (`development`, `test`,
`preview`, `staging`, `production`). `NODE_ENV` is not that variable: frameworks and libraries read
it to pick optimized code paths, so it stays `production` in every deployed environment, staging
and previews included. Code that branches on `NODE_ENV === 'production'` to decide whether to
charge cards or send email is wrong in staging.

Make cross-environment mix-ups fail at startup: reject a live payment key when `APP_ENV` is not
`production`, and a test key when it is.

## Validate configuration at startup

Read `process.env` in exactly one module, parse it with a schema, export a typed object, and import
that object everywhere else. A missing variable then fails the deploy at boot instead of failing a
request path three days later.

```ts
// src/env.ts: the only file that reads process.env
import { z } from 'zod';

const schema = z
  .object({
    APP_ENV: z.enum(['development', 'test', 'preview', 'staging', 'production']),
    DATABASE_URL: z.url(),   // Zod 4; Zod 3: z.string().url()
    SESSION_SECRET: z.string().min(32),
    STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
    EMAIL_ENABLED: z.enum(['true', 'false']).transform((v) => v === 'true'),
    PORT: z.coerce.number().int().positive().default(3000),
  })
  .refine((e) => (e.APP_ENV === 'production') === e.STRIPE_SECRET_KEY.startsWith('sk_live_'), {
    message: 'live Stripe key must be used in production and only there',
  });

const parsed = schema.safeParse(process.env);
if (!parsed.success) {
  for (const issue of parsed.error.issues) {
    console.error(`env ${issue.path.join('.')}: ${issue.message}`); // names only, never values
  }
  process.exit(1);
}
export const env = parsed.data;
```

Traps:

- `FOO=` is the empty string, not undefined: `.optional()` accepts it and `.default()` does not
  apply. Require `.min(1)` on strings, or map `''` to `undefined` before parsing.
- `z.coerce.boolean()` turns the string `"false"` into `true`. Parse booleans explicitly as above
  (Zod 4 also has `z.stringbool()`).
- Validation only fails fast if something imports the module at boot. In Next.js, import it from
  `instrumentation.ts` (its `register()` runs once when the server starts, in each runtime: guard
  a Node-only module with `process.env.NEXT_RUNTIME === 'nodejs'`) and from `next.config.ts` so
  the build checks it too. On serverless there is no boot: the build-time check and a post-deploy
  smoke request are the gate.
- A Docker build has no runtime secrets, and `next build` evaluates server modules. Allow a
  build-only skip switch (`SKIP_ENV_VALIDATION=1` set in the Dockerfile's build stage only) and
  confirm the runtime stage does not carry it.
- `NEXT_PUBLIC_*` values are inlined at build time and only when referenced literally
  (`process.env.NEXT_PUBLIC_X`); a dynamic lookup returns undefined in the browser. Validate client
  variables in a separate schema that lists each one explicitly, and keep secrets out of that
  prefix: everything in it ships to every visitor. `@t3-oss/env-nextjs` packages this pattern.
- Never print the parsed object. Log the names of invalid keys only.

Fail fast protects production only when the deploy checks health before shifting traffic: the new
instance exits, the health check fails, the rollout stops and the old version keeps serving
(`deploy-rollback.md`). Without that gate, fail fast turns a missing variable into an outage.

### Adding or changing a variable

The order that prevents "crashed because a variable was missing":

1. Add it to the schema and to the committed `.env.example` (names and dummy values, no secrets).
2. Set the value in every environment's store: local, CI, preview, staging, production.
3. Merge and deploy the code that reads it.
4. Removing: deploy code that no longer reads it, then delete it from the stores.

Know when a changed variable takes effect. Platforms with immutable deployments (Vercel and
similar) apply it only to new deployments: a dashboard edit does nothing until a redeploy. Others
restart the app at once (Heroku config vars, Fly.io secrets), so the edit is an unreviewed
production release at that moment. Rotating a secret is a deploy either way. Rollback differs the
same way: some platforms restore the old release's variables, so a secret rotated since then comes
back as the revoked value; others run old code on current variables. Check which yours does, and
keep variable changes backward compatible for one release, the same as schema changes.

Keep one source of truth per environment (the platform's variable store or a secret manager) and
pull local values from it (`vercel env pull`, the secret manager's CLI) instead of passing `.env`
files around in chat. `.env*` stays in `.gitignore` except `.env.example`. Storage, rotation and
leak response: `0x:web-security` (`secrets.md`).

## Keep local, CI and production close enough to trust

Parity is worth paying for where a difference changes behavior, and not worth it for scale.

| Must match production | How |
|---|---|
| Database engine, major version, extensions | Postgres in a container locally and in CI, same major version, same extensions. Not SQLite, not an in-memory fake. |
| Runtime version | One file (`.nvmrc` or `.node-version`) read by the version manager, CI and the Dockerfile; `engines` in `package.json`. |
| Dependencies | Committed lockfile, `--frozen-lockfile` everywhere. |
| Build mode | End-to-end tests and manual checks before release run the production build, not the dev server. |
| Time zone and locale | Servers run UTC; run tests with `TZ=UTC`. |
| Schema | Every environment reaches its schema by the same migration files. |

| Fine to differ | |
|---|---|
| Instance size, replica count, autoscaling | Scale is tested by load tests, not by parity. |
| Third-party services | Sandboxes or HTTP-level mocks locally and in CI. |
| Data volume | Except when rehearsing a migration (see staging data). |

Differences that cause most "works locally" production bugs, with the check for each:

| Difference | What breaks | Check |
|---|---|---|
| Connection pooler in transaction mode in production, direct connection locally | session state: advisory locks, `SET`, `LISTEN`, some prepared-statement use | run CI or staging through the same pooler mode |
| Several instances in production, one locally | in-memory sessions, caches, rate limits, scheduled jobs running N times | run two instances in staging or locally once; keep state in the database or Redis |
| Reverse proxy and CDN in front | client IP, protocol and host come from forwarded headers; cached responses; body size and timeout limits | test through the real edge in a preview |
| Serverless limits | execution timeout, payload size, no background work after the response, cold starts | test on the platform, not only `next dev` |
| Case-insensitive laptop filesystem | imports that resolve on macOS and fail on Linux | CI on Linux is the check |
| Read replica lag | read-your-own-write bugs | point staging reads at a replica if production does |
| Local `.env` has variables production lacks | undefined at runtime | startup validation |

Local services run from one Compose file with pinned image tags (`0x:cloud-infrastructure`,
`docker-images.md`); CI uses the same tags.

## Preview environment per pull request

A preview is the pull request's build at its own URL with its own database. The application half
comes with most PaaS git integrations. The database half is the work.

| Database approach | Choose when | Trap |
|---|---|---|
| Branching Postgres provider (copy-on-write branch per pull request) | the provider supports it; the default | a branch of the production database contains production data: branch from a seeded or anonymized parent |
| `CREATE DATABASE pr_123` on one shared non-production instance, then migrate and seed | any Postgres | connection limits on the shared instance; cleanup is yours |
| One shared preview database for all pull requests | Prototype only | two pull requests with different migrations break each other |

Lifecycle, as workflow jobs or the provider's integration:

1. On `opened` and `reopened`: create the database, run the full migration chain, run the seed.
2. On `synchronize` (each push): run new migrations. If a migration file that already ran was
   edited, reset the database and reapply; do not hand-patch it.
3. On `closed`: delete the database and the deployment. Add a scheduled sweep that deletes
   previews whose pull request is closed, because the close event is sometimes missed.

```yaml
on:
  pull_request:
    types: [opened, reopened, synchronize, closed]
```

Things that do not work in previews by default, and the fix:

- **OAuth login.** Providers require exact redirect URIs and most do not accept wildcards, so a
  per-pull-request URL is rejected. Give previews a seeded test login or email magic links to a
  sandbox inbox, or route the callback through one fixed preview-auth domain.
- **Inbound webhooks.** Providers cannot reach a new URL per pull request. Test webhook handlers
  with signed fixture payloads in integration tests, or forward from the provider's CLI on demand.
- **Secrets.** Previews run unreviewed code, so they get throwaway credentials only: test-mode
  keys, sandbox email, their own session secret. Scope production variables to the production
  environment in the platform so a preview cannot read them (`pipeline-security.md`).
- **Access.** Turn on the platform's deployment protection or put previews behind login; send
  `noindex`.
- **Cost.** Use auto-suspending databases, cap concurrent previews, and skip previews for
  dependency-bot pull requests.
- **Background workers and cron.** Usually absent in previews. Either run jobs inline in preview
  mode or state plainly that job-driven features are verified elsewhere.

## Staging data

Default: a deterministic seed script, kept in the repository and run by CI, that creates the
accounts and states needed to exercise the product (free and paid accounts, an expired trial, an
account with enough rows to paginate, an admin). It is safe, reproducible and also feeds previews
and local development. Writing fixtures and factories: `0x:code-quality` (`test-data-flaky.md`).

Use a copy of production only when synthetic data cannot answer the question: migration duration
and lock behavior on real table sizes, query plans, or a bug that depends on real data shape. Then:

1. Anonymize before the data leaves the production boundary: restore the backup into a scratch
   database inside production's network, transform there, dump the result. A raw dump on a laptop
   or in staging is already the incident.
2. Work from an allowlist: each column is marked keep, transform or drop, and an unlisted column
   fails the job. A blocklist silently leaks the column added last month.
3. Transform deterministically (same input, same output) so joins and uniqueness survive.

| Data | Treatment |
|---|---|
| Emails | rewrite to `user-<id>@example.com` (a reserved domain that never delivers) |
| Names, phones, addresses, free text, uploaded files | replace with generated values; drop free text and files |
| Password hashes, sessions, API keys, OAuth and push tokens, 2FA secrets | drop or regenerate |
| Payment provider customer and subscription IDs | null or remap: live IDs do not exist in test mode and every call fails |
| Customer-configured webhook URLs and integrations | null, or staging calls customer systems |
| Row counts, foreign keys, distributions, timestamps | keep: this is why the copy was taken |

Keep the outbound guards from the separation table even with anonymized data; they are the second
layer. If only migration timing is in question, table sizes matter and content does not: generate
rows to production scale instead of copying. Anonymized and pseudonymized data are different
things in privacy law; whether a given copy is still personal data: `0x:privacy-compliance`
(`privacy-law.md`).

## What staging is for, and when to skip it

Staging earns its cost only for jobs that previews, flags and a fast rollback cannot do:

| Job | Staging needed? |
|---|---|
| Reviewing a feature before merge | No: preview environment |
| Limiting the blast radius of a risky change | No: feature flag with staff-only targeting, in production |
| Rehearsing a slow or risky migration on production-sized data | Yes, or a one-off restored copy |
| Rehearsing infrastructure changes (proxy, platform, runtime upgrade, Terraform) | Yes |
| Integration with third-party sandboxes that need a stable URL (webhooks, SSO, payment flows) | Yes |
| A stable backend for mobile test builds | Yes |
| Load tests and penetration tests | A short-lived production-shaped environment with seeded data, created for the test; long-lived staging not required |
| Customer or stakeholder acceptance before release, contractual or audit requirements | Yes |

Default for a solo founder through Launch: no long-lived staging. Use previews, flags, automatic
smoke tests and one-command rollback, and restore a scratch copy when a migration needs rehearsal.
Add staging when one of the "Yes" rows becomes a recurring need.

A staging environment that exists must stay trustworthy, or it produces false confidence:

- Every merge to main deploys to staging automatically, with the same artifact that production
  gets next and the same migration step. A staging that is deployed by hand is weeks behind.
- Same infrastructure code as production with smaller numbers, same topology (pooler, proxy,
  at least two instances if production has them).
- Nobody edits it by hand; if it breaks, rebuild it from code and seed.
- Decide what gates production: automatic promotion after smoke tests pass on staging is the
  default; a manual approval only where someone actually looks.

Passing in staging proves the artifact starts and the migration applies. It does not prove
production behavior under real traffic and data, which is what per-release monitoring is for.

## Ask the user

- **Is there a recurring need for a stable pre-production environment** (mobile test builds,
  customer acceptance, partner sandboxes, audits)? Default: no; previews and flags, no staging.
- **May production data be copied anywhere outside production, even anonymized?** Contracts and
  privacy commitments may forbid it. Default: no copies; synthetic seed data only.
- **Which third-party accounts have sandbox or test modes, and who owns them?** Default: create a
  test-mode key or sandbox account per provider before wiring non-production environments.
- **What is an acceptable monthly cost for non-production environments?** Default: auto-suspending
  preview databases, no always-on staging.
- **Who needs to see previews** (only the founder, clients, testers)? Decides the access
  protection. Default: behind the platform's login protection.
