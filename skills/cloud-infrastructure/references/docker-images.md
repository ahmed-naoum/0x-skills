# Docker images, Compose and single-server deploys

Read this when: writing, shrinking, speeding up or securing a container image; running the stack locally in containers; or deploying containers to one server with Kamal or Coolify.

## The image an expert ships

Five properties, each checkable:

1. Multi-stage: compilers, dev dependencies and source do not reach the final stage.
2. Runs as a non-root user with no shell tricks needed at start.
3. Starts the server process directly as PID 1 (exec form), so SIGTERM reaches it.
4. Contains no secrets in any layer, and no `.env`, `.git` or local `node_modules` from the build context.
5. Built from a pinned base, tagged with the commit SHA, deployed by digest.

Reference Dockerfile for the house stack (Next.js with `output: "standalone"`, pnpm). Adapt the shape, not the letters:

```dockerfile
# syntax=docker/dockerfile:1
ARG NODE_VERSION=24
FROM node:${NODE_VERSION}-bookworm-slim AS base
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH
RUN corepack enable

FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile

FROM base AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

FROM node:${NODE_VERSION}-bookworm-slim AS run
WORKDIR /app
ENV NODE_ENV=production PORT=3000 HOSTNAME=0.0.0.0
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
```

Notes on the parts people get wrong:

- Match `NODE_VERSION` to the project's `.nvmrc` or `engines`. Corepack is no longer bundled with the newest Node lines; where `corepack` is missing, install the pinned pnpm with `npm install -g pnpm@<version from packageManager>`.
- `.dockerignore` is part of the Dockerfile. Minimum: `node_modules`, `.next`, `.git`, `.env*`, `*.log`, `coverage`, `Dockerfile`, `docker-compose*.yml`. Without it the context upload is slow, `COPY . .` overwrites the installed `node_modules` with the host's, and `.env` lands in a layer.
- For a non-Next Node service: build in one stage, then in the final stage install production dependencies only (`pnpm install --prod --frozen-lockfile`, or `pnpm deploy --prod` in a workspace) and copy `dist`.
- `CMD ["node", "server.js"]`, not `CMD pnpm start` or `npm start`: the shell form and package-manager wrappers sit at PID 1, swallow SIGTERM, and the container is SIGKILLed after the grace period with requests in flight. If the app spawns children or cannot reap zombies, run with an init (`docker run --init`, Compose `init: true`).
- Handle SIGTERM in the app: stop accepting, finish in-flight requests, close the pool, exit. Deploy tools wait a fixed grace period (commonly 10 to 30 s) before SIGKILL.
- Node's heap is not the container's memory: set `--max-old-space-size` to about 75 percent of the container limit in MB, or the kernel OOM-kills (exit 137) before garbage collection gets urgent.
- Framework public variables (`NEXT_PUBLIC_*`) are compiled into the bundle at build time. One image per environment, or runtime-injected public config, is a decision to make deliberately; a staging URL baked into the production image is a common result of not making it. See `0x:ci-cd-release` `environments-config.md`.

Check size and contents:

```bash
docker build -t app:dev . && docker image ls app:dev
docker history --no-trunc app:dev | head -20     # look for secrets and large layers
docker run --rm --entrypoint id app:dev          # must not be uid=0
```

A Node web image built this way lands in the low hundreds of MB; over 1 GB means dev dependencies, build caches or the whole repo got in.

## Secrets and build-time material

`ARG` and `ENV` values persist in image metadata and history; a file copied and deleted in a later layer is still in the earlier layer. Anyone who can pull the image can read both.

| Need | Mechanism |
|---|---|
| Private registry token during install | `RUN --mount=type=secret,id=npmrc,target=/root/.npmrc pnpm install --frozen-lockfile`, built with `docker build --secret id=npmrc,src=$HOME/.npmrc .` |
| Private git dependency | `RUN --mount=type=ssh ...` with `docker build --ssh default .` |
| Runtime secrets (database URL, API keys) | Injected by the platform as environment or mounted files at start; never in the image |
| Build needs a database or API to prerender | Prefer making the build not need it; otherwise pass a build-only, least-privilege credential as a secret mount |

Check: `docker history --no-trunc <image>` shows no token-shaped strings, and a scan for secrets in the image (Trivy's secret scanner) is clean. Secret storage and rotation belong to `0x:web-security`.

## Build speed: layer order and cache

A layer is rebuilt when its instruction or any file it copies changes, and every layer after it is rebuilt too. Order from least to most frequently changing: base and OS packages, then lockfile and dependency install, then source, then build.

- Copy only `package.json` and the lockfile before installing. Copying the source first reinstalls dependencies on every commit.
- Use cache mounts for package-manager stores (`--mount=type=cache`), so a lockfile change downloads only the difference.
- In a monorepo, copy only the manifests the target needs (or prune with the workspace tool) before install; otherwise any package's change invalidates the install layer.
- CI runners start with an empty cache. Export and import it: with `docker/build-push-action`, `cache-from: type=gha` and `cache-to: type=gha,mode=max`, or a registry cache (`type=registry,ref=<repo>:buildcache`). `mode=max` caches intermediate stages, which is where the dependency layer lives.
- Combine `apt-get update` and `apt-get install` in one `RUN` and remove `/var/lib/apt/lists/*` in the same instruction; a separate `update` layer goes stale in cache and installs fail later.

Targets (rule of thumb): a cached rebuild after a source-only change under two minutes; a cold build under ten. Pipeline structure belongs to `0x:ci-cd-release`.

## Base image choice and patching

| Base | Use when | Trap |
|---|---|---|
| Debian slim (`-bookworm-slim` and successors) | Default. glibc, a shell for debugging, native modules work | More packages than strictly needed, so more CVE noise |
| Distroless (`gcr.io/distroless/...`, use a `nonroot` tag) or Chainguard-style minimal images | Launch onward when scan noise or attack surface matters | No shell, no package manager: debugging needs an ephemeral debug container; health checks cannot use `curl` |
| Alpine | Static binaries (Go, Rust) or when size dominates | musl libc: prebuilt native Node modules may be missing or slower, some DNS and locale behavior differs. Not the default for Node or Python |
| `scratch` | Fully static Go or Rust binary | Must add CA certificates and time zone data, and set a numeric `USER` |

Patching is a schedule, not an event:

- Pin the base by version tag at least; by digest (`FROM node:24-bookworm-slim@sha256:...`) for reproducibility, with Renovate or Dependabot opening the PRs that bump it. A digest pin with no bot means never patched.
- Rebuild and redeploy at least weekly even with no code change, so OS package fixes arrive. A scheduled CI run that builds with `--pull` does it.
- Scan in CI with Trivy or Grype. Fail on critical and high vulnerabilities that have a fix available; do not fail on unfixable ones, or the gate gets disabled within a month.

## Health checks and resource limits

Every container needs both, wherever it runs.

Health endpoint: a cheap `GET /healthz` that returns 200 when the process can serve. Do not make liveness depend on the database: when the database blips, every instance fails its check at once, the orchestrator restarts them all, and a short outage becomes a long one. A separate readiness check may include dependencies.

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
```

The Dockerfile `HEALTHCHECK` is used by Docker and Compose. Kubernetes ignores it and ECS reads the check from the task definition, so define it there too.

Limits: a container with no memory limit can take the host down; one with a limit and a leak restarts alone. Set a memory limit on everything, sized
from observed peak plus about 25 percent headroom, and a CPU limit or share on anything that can spin. Exit code 137 with `OOMKilled: true` in `docker
inspect` means the limit was hit. Cgroup mechanics are in `0x:linux-server` `container-internals.md`.

## Local stack with Compose

Goal: `docker compose up` gives a new machine the same Postgres, Redis and mail catcher as everyone else, in one command. Default split: backing services in Compose, the app itself run natively with `pnpm dev` (fastest reload, best debugger). Put the app in Compose too only when it needs system libraries that are painful to install on the host.

```yaml
services:
  db:
    image: postgres:17
    environment:
      POSTGRES_PASSWORD: dev
    ports: ["127.0.0.1:5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 10
  app:
    build: .
    init: true
    env_file: .env
    ports: ["127.0.0.1:3000:3000"]
    depends_on:
      db:
        condition: service_healthy
    deploy:
      resources:
        limits: { memory: 1g, cpus: "1.0" }
volumes:
  pgdata:
```

- Match the production major version of every backing service (the `postgres:17` above is a placeholder for whatever production runs).
- `depends_on` without `condition: service_healthy` only orders container start; the app still races the database.
- Bind published ports to `127.0.0.1`. Docker's port publishing writes its own firewall rules and bypasses `ufw`; `"5432:5432"` on a server with a public IP exposes the database to the internet.
- Inside the Compose network, services reach each other by service name (`db:5432`), not `localhost`.
- Bind-mounting source on macOS and Windows is slow for large trees; use Compose `develop.watch` to sync, or keep the app native. Never bind-mount over `node_modules`: host and container architectures differ.
- `docker compose down -v` deletes the named volumes, and with them the dev database. Seed scripts make that harmless.
- Dev containers (`.devcontainer/devcontainer.json` pointing at the Compose file) are worth adding when onboarding more than one contributor or when using cloud workspaces; for a solo founder, Compose for services is enough.

## Tags and registry

- Tag every build with the full git SHA. Add a human tag (`v1.4.2`, `main`) only as an alias. Mutable tags (`latest`, `prod`) must never be what a deploy references: two servers pulling at different times run different code, and rollback has no target.
- Deploy by digest (`repo@sha256:...`) or by SHA tag with tag immutability enabled in the registry.
- Build once, promote the same image through staging to production; rebuilding per environment ships something untested.
- Retention: registries bill per GB and grow without bound. Rules that are safe: expire untagged images after a few days; keep the most recent N (for example 30) SHA-tagged images; never expire release tags. Make sure N covers the rollback window, including the image currently running, before enabling the rule.
- Keep the registry in the same cloud and region as the runtime to avoid pull latency and transfer fees, and give the runtime pull-only credentials.

## Multi-arch and ARM64

ARM64 instances (AWS Graviton, Ampere-based offerings on other clouds, ARM VPS plans) are typically cheaper per vCPU with equal or better throughput for Node, Go, Java, Python and Postgres; treat a saving in the region of 20 percent as a rule of thumb and benchmark the real workload. Managed databases and caches switch with one setting and are the easiest win.

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t registry.example.com/app:$GIT_SHA --push .
```

- `exec format error` (or `no matching manifest for linux/amd64`) at container start means the image architecture does not match the host. The usual cause: built on an Apple Silicon laptop, deployed to x86. Build in CI, with `--platform` explicit.
- Cross-building under QEMU emulation is several times slower. Build each architecture on a native runner (GitHub offers hosted ARM64 runners) and merge the manifests, or build only the one architecture production uses.
- Check every native dependency and sidecar publishes ARM64 builds before switching: image libraries, headless browsers, database drivers with native bindings, monitoring agents.
- If production is ARM64 and developers are on Apple Silicon, dev and production match with no emulation at all.

## One server with Kamal or Coolify

| Tool | Shape | Pick when |
|---|---|---|
| Kamal | CLI run from a laptop or CI; config in the repo (`config/deploy.yml`); SSHes in, pulls the image, boots the new container beside the old one, switches its proxy after the health check passes | Config in git, no web UI wanted, more than one server later |
| Coolify | Self-hosted PaaS with a web UI on the server; git-push deploys, managed databases with backups, built-in reverse proxy and certificates | A Heroku-like panel is wanted, several small apps on one box |
| Plain Compose on the server | `docker compose pull && docker compose up -d` | Internal tools where a few seconds of downtime per deploy is acceptable |

Zero-downtime on one host needs four things, whichever tool: a reverse proxy that owns ports 80 and 443; the new container started alongside the old;
traffic switched only after the new one passes its health check; the old one drained on SIGTERM before removal. Kamal's proxy does this by default and
expects a health endpoint (by default `GET /up` returning 200, configurable). In Coolify, configure a health check on the application; without one, a
rolling update cannot know when to switch.

Sequence for a first Kamal deploy: fresh server with SSH key access and nothing on ports 80/443; DNS A record pointing at it; registry credentials and app secrets supplied through Kamal's secrets file from the environment or a password manager, not committed; `kamal setup` once; `kamal deploy` thereafter; `kamal rollback <version>` to return to a previous image that is still on the host.

What single-server deploys do not give, and what to do about each:

- **The server is the single point of failure.** Accept it at Prototype and early Launch with a rehearsed rebuild: provisioning script, config in git, restore from backup timed end to end.
- **A database on the same box dies with it.** Either use a managed database, or ship continuous backups off the server (WAL archiving or frequent dumps to object storage) and test a restore. See `0x:postgres-database` `backup-recovery.md`.
- **Schema migrations are not rolled back with the image.** Old and new containers overlap during the switch, so every migration must be compatible with the previous release. See `0x:postgres-database` `migrations.md`.
- **Nobody patches it.** Enable unattended security updates and reboot on a schedule; host hardening is in `0x:linux-server`.
- **Disk fills with old images and logs.** Schedule `docker image prune -af --filter "until=168h"` and cap container log size (`max-size`, `max-file` for the `json-file` driver).

## Ask the user

- **Is a few seconds of downtime per deploy acceptable right now?** Decides plain Compose versus a proxy-switching tool. Default: no once there are paying users; use Kamal or the platform's rolling deploy.
- **Does the same image need to run in staging and production with different public configuration?** Decides build-time versus runtime public variables. Default: build once and inject public config at runtime where the framework allows; otherwise build per environment and say so.
- **Where does the database live for a single-server setup?** On-box is cheapest and carries the restore risk. Default: managed Postgres in the same region or metro.
- **x86 or ARM for production?** Affects price and build setup. Default: ARM64 when every dependency supports it, otherwise x86; one architecture only.
- **How far back must a rollback reach?** Sets registry retention. Default: the last 30 images or 30 days, whichever keeps more.
