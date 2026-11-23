# Packages, updates and provisioning

Read this when: installing a runtime or package on a host, adding a third-party repository, setting
up automatic security updates and reboots, checking what a host exposes before it goes public,
making server setup repeatable, or deciding whether to upgrade a host or replace it.

## Language runtimes

The distribution's `nodejs`, `python3` or `ruby` package is whatever version was current when the
release froze, changes under the app on a release upgrade, and allows one version per host. Use it
for the OS's own tools, not for the app.

| Where | Install the runtime with | Why |
|---|---|---|
| Developer machine, CI | A version manager (mise, fnm, nvm; uv or pyenv for Python) reading a version file in the repo | Several projects, several versions |
| Production in a container | The base image tag | The image is the pin; the host needs no runtime |
| Production directly on a host | One system-wide install of the pinned version: the vendor's package repository or the official binary under `/usr/local` | systemd and cron do not load a version manager's shell setup |

Rules:

- One source of truth for the version, committed: `.nvmrc` or `.node-version` (and `engines` in
  `package.json`), `.python-version`, or the version manager's own file. CI and the Dockerfile read
  or mirror it. "Works locally, fails in production" is often a different major version.
- Use even-numbered Node LTS lines in production, and move before the line's end of life.
- Pin the package manager too (the `packageManager` field in `package.json`), so pnpm's lockfile
  format does not change between machines.
- A version manager installs under the user's home and activates through shell startup files.
  A systemd unit that says `ExecStart=node ...` will not find it, or will find the distro's older
  one. In units use the absolute path of the intended binary and check with
  `sudo -u app /abs/path/node --version`.
- Never `sudo pip install` into the system Python: it overwrites modules the OS's own tools depend
  on. Current Debian and Ubuntu block it with an "externally-managed-environment" error; the answer
  is a virtual environment (`python3 -m venv`, or uv), or `pipx` for command-line tools, not
  `--break-system-packages`.
- Do not `sudo npm install -g` application dependencies. Global installs are for a handful of
  tools at most.
- For `curl ... | sh` installers: download to a file, read it, verify a published checksum where
  one exists, then run it. Never pipe to a root shell from a provisioning script without a pinned
  version, or the same script installs something different next month.

## apt and dnf

Trust order: the distribution's own repositories, then the software vendor's official repository
with a signed key, then anything else only with a reason. Each added repository is a party that
can run code as root on the host at every update.

Add a vendor repository with a key that is trusted for that repository only:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://vendor.example/key.asc | sudo gpg --dearmor -o /etc/apt/keyrings/vendor.gpg
echo "deb [signed-by=/etc/apt/keyrings/vendor.gpg] https://vendor.example/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/vendor.list
sudo apt-get update
```

Do not follow guides that use `apt-key add`: it trusts the key for every repository, and the
command is deprecated and absent from current releases.

| Task | Debian, Ubuntu | RHEL family |
|---|---|---|
| Install without prompts | `sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends <pkg>` | `sudo dnf install -y <pkg>` |
| Which version, from which repo | `apt-cache policy <pkg>` | `dnf info <pkg>`; `dnf repoquery --installed <pkg>` |
| Install an exact version | `apt-get install <pkg>=<version>` | `dnf install <pkg>-<version>` |
| Freeze a package | `sudo apt-mark hold <pkg>`; list with `apt-mark showhold` | `dnf versionlock add <pkg>` (versionlock plugin) |
| What would be upgraded | `apt list --upgradable` | `dnf check-update` |
| Undo a transaction | reinstall the previous version by hand | `dnf history`, `dnf history undo <id>` |
| Finish an interrupted install | `sudo dpkg --configure -a` | `dnf history redo last` or rerun |

- Use `apt-get` in scripts; `apt` is for interactive use and warns that its output is not stable.
- Hold what must only change deliberately: the database server, the container engine, anything
  whose upgrade restarts a stateful service. A held package also stops receiving security fixes,
  so review `apt-mark showhold` on a schedule.
- `apt-get upgrade` never removes packages; `dist-upgrade` (or `apt full-upgrade`) may. Read the
  list before confirming the second on a production host.
- "Could not get lock /var/lib/dpkg/lock-frontend" means another package operation is running,
  usually automatic updates or first-boot setup. Wait (`cloud-init status --wait`, or
  `-o DPkg::Lock::Timeout=120`); do not delete the lock file.
- Do not mix releases (adding a newer release's repository to get one newer package). The
  dependency resolver will eventually replace core libraries. Use the vendor's repository for
  that package or run it in a container.
- Postgres and similar ship one package name per major version, so a routine upgrade never crosses
  a major version; that move is a planned migration (`0x:postgres-database`).

## Security updates and reboots

Automatic security updates are the default from the first day. An unpatched, internet-facing host
is the more likely failure than a bad update.

Debian and Ubuntu:

```bash
sudo apt-get install -y unattended-upgrades needrestart
sudo dpkg-reconfigure -f noninteractive unattended-upgrades   # writes 20auto-upgrades
sudo unattended-upgrade --dry-run --debug                     # proves the config parses and what it would do
```

```text
// /etc/apt/apt.conf.d/52local-unattended   (overrides 50unattended-upgrades)
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:30";
Unattended-Upgrade::Package-Blacklist { "postgresql-"; "docker-ce"; };
```

RHEL family: install `dnf-automatic`, set `apply_updates = yes` and `upgrade_type = security` in
`/etc/dnf/automatic.conf`, and enable `dnf-automatic.timer`.

- A new kernel, C library or TLS library is installed on disk but not in use until the reboot or
  service restart. `/var/run/reboot-required` exists when a reboot is pending (Debian family);
  `sudo dnf needs-restarting -r` on the RHEL family; `sudo needrestart` lists services still
  running old libraries. A host that updates daily and never reboots is not patched.
- Single host: an automatic reboot in the quietest hour costs about a minute and is the right
  trade at Prototype and Launch. It is safe only if every service is enabled and returns by
  itself (`processes-systemd.md`); prove it with one manual reboot.
- Several hosts: stagger reboot times so they are never all down together, and take each out of
  the load balancer first once deploys are automated (`0x:ci-cd-release`).
- Exclude packages whose update restarts a stateful service at a random time: the database, and a
  container engine whose restart stops every container. Patch those by hand in a window, on a
  calendar reminder, at least monthly.
- A remotely exploitable flaw in something exposed (SSH daemon, web server, TLS library, kernel
  network stack) does not wait for the schedule:
  `sudo apt-get update && sudo apt-get install --only-upgrade <pkg>`, then restart or reboot.
- Host updates do not touch container images. A base image is patched only by rebuilding and
  redeploying it (`0x:cloud-infrastructure`, `0x:web-security`).
- Logs: `/var/log/unattended-upgrades/` and `/var/log/apt/history.log` answer "what changed last
  night" when something breaks after an update.

## Audit before exposing a host

Run this before opening a firewall or pointing DNS at a host, and again after installing anything.

```bash
sudo ss -tulnp                                           # every listening TCP and UDP socket
systemctl list-units --type=service --state=running      # what runs
systemctl list-unit-files --type=service --state=enabled # what starts at boot
systemctl --failed                                       # what is broken
apt-mark showmanual | wc -l; apt list --upgradable       # what was chosen; what is unpatched
getent group sudo wheel                                  # who can become root
awk -F: '$7 !~ /(nologin|false)$/ {print $1, $3, $7}' /etc/passwd   # accounts with a shell
sudo sh -c 'ls -la /root/.ssh /home/*/.ssh 2>/dev/null'  # whose keys can log in
systemctl list-timers; sudo ls /etc/cron.d /var/spool/cron/crontabs 2>/dev/null   # scheduled work
```

- In `ss` output, every line whose local address is `0.0.0.0`, `*` or `[::]` is reachable from
  wherever the firewall allows and needs a reason to exist. Lines on `127.0.0.1` or `[::1]` are
  local only.
- Listeners that should almost never be public: Postgres, Redis, other databases and search
  engines, a Node inspector port, metrics and admin endpoints, development servers, a mail
  transfer agent that some package pulled in.
- Verify from outside, because the cloud firewall, the host firewall, bind addresses and Docker's
  own rules combine in ways the host view does not show: from another machine,
  `nmap -Pn -p- <host>` against hosts you own, over IPv4 and IPv6. Only the intended ports
  (typically 22, 80, 443) should answer.
- Stop and disable what is not needed (`sudo systemctl disable --now <unit>`), then purge it.
  Fewer packages means fewer updates and fewer listeners.
- Images from providers and marketplaces come with their own users, keys and agents. Read the
  audit output on a fresh host once; do not assume it is empty.

## Repeatable provisioning

The standard to hold: the host can be destroyed and rebuilt from the repository, without memory or
notes, in under an hour. The only proof is doing it once. A hand-built server works until the day
it has to be replaced in a hurry.

| Stage | Approach |
|---|---|
| Prototype | cloud-init user data for the first boot, plus one idempotent `provision.sh` in the repo |
| Launch | The same, rerun on every change; machine, firewall and volumes created by infrastructure as code (`0x:cloud-infrastructure`) |
| Scale | Configuration management (Ansible) or prebuilt images once there are several hosts or roles |

```yaml
#cloud-config
users:
  - name: admin
    groups: sudo
    shell: /bin/bash
    sudo: "ALL=(ALL) NOPASSWD:ALL"
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... founder@laptop
ssh_pwauth: false
disable_root: true
package_update: true
package_upgrade: true
packages: [ufw, unattended-upgrades]
runcmd:
  - ufw allow OpenSSH
  - ufw --force enable
```

- The first line must be exactly `#cloud-config`. A YAML mistake does not stop the boot: the host
  comes up with nothing applied. Check with `cloud-init status --long`, read
  `/var/log/cloud-init-output.log`, and validate with `sudo cloud-init schema --system`.
- User data runs on the first boot only. Later changes go through the script.
- Automation that connects right after creation must wait: `cloud-init status --wait`.
- Any process on the host can read user data from the metadata service, and the provider stores
  it. Put no secrets in it.
- The script covers packages, users, SSH and firewall config, unit files, journald and logrotate
  limits, swap, sysctl settings and the time zone, written to converge (`shell-files.md`). Secrets
  are injected at deploy time (`0x:ci-cd-release`); data is restored from backup.
- Run it remotely as `ssh host 'sudo bash -s' < provision.sh`, on every change, so it is known to
  work on a host that already exists.
- Any fix made by hand on the server goes into the script the same day. Drift is the difference
  between what the script builds and what production is; after a few months of drift the script
  is fiction.

## Patch in place or replace

| Situation | Do |
|---|---|
| Routine security and package updates | Patch in place |
| Stateless app hosts behind a load balancer | Replace: build new, add, drain and delete old |
| OS major-version upgrade | Replace. In-place release upgrades over SSH are the riskiest routine operation on a host |
| Suspected compromise | Replace, always. A host that ran an attacker's code as root cannot be cleaned with confidence; preserve a disk snapshot for investigation first (`0x:web-security`) |
| Nobody knows what was changed by hand | Replace, to get back to a known state |
| Changing CPU architecture or disk layout | Replace |
| Single host holding the only copy of the data | Patch in place, after a snapshot; plan to separate data from the machine |

Replacing is cheap only when three things are already true: data lives on a separate volume or a
managed service, provisioning is scripted, and traffic can be moved with a floating IP, a load
balancer or a DNS record with a short TTL. Sequence for a single host: lower the DNS TTL a day
ahead, build the new host from the script, restore or attach data, test it by address before any
switch, move traffic, keep the old host stopped for a few days, then delete it.

If an in-place release upgrade is unavoidable: snapshot first, run it inside `tmux` or the
provider's console so a dropped SSH session does not kill it midway, and have the rebuild path
ready.

## Operating-system end of life

After end of life a release gets no security fixes, vendor repositories drop it, and it becomes a
finding in any customer security review.

- Find what runs: `cat /etc/os-release`. Record each host's release and end-of-life date in the
  repo, next to the provisioning script.
- Choose long-term-support releases for servers: Ubuntu LTS (even years, `.04`), Debian stable, or
  a RHEL-compatible distribution. Interim Ubuntu releases are supported for months, not years.
- Support lengths differ by distribution and change with paid extended programs. Look up the exact
  date for the release in the distribution's own lifecycle page instead of assuming.
- Start a new host on the newest LTS that has had its first point release; early months of a
  release still shake out package and driver problems.
- Set a reminder six months before end of life. The upgrade is a replacement: build a host on the
  new release from the provisioning script, run the test suite and a restore on it, and cut over.
- The same calendar applies to what sits on top: Node LTS lines, Postgres major versions and the
  container base image each have their own end of life.

## Ask the user

- **When is the quietest hour for an automatic reboot, and is about a minute of downtime then
  acceptable?** Unapplied kernel fixes are the alternative. Default: yes, at night in the main
  customer time zone, expressed in UTC.
- **Should the database be excluded from automatic updates?** Automatic minor updates restart it
  at an unplanned moment. Default: exclude it on a self-run host and patch monthly by hand; a
  managed database handles this itself.
- **Which ports must be public?** Everything else is closed. Default: 80 and 443 to the world, 22
  restricted where a fixed source address exists.
- **Is there budget to run the old and new host side by side for a few days during a
  replacement?** It is what makes replacement safe. Default: yes; the cost is days of one instance.
- **Is there a compliance or customer requirement on patch timelines?** Some contracts set
  deadlines for critical fixes. Default: critical remote flaws the same day, the rest within the
  automatic cycle.
