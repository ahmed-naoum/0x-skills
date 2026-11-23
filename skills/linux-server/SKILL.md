---
name: linux-server
description: Sets up, hardens, scripts and diagnoses Linux servers, covering CPU, memory and disk bottlenecks, systemd services, SSH and firewalls, patching, container limits and signals, time zones and text encoding. Use when a server is slow, out of memory or the disk is full, a service crashes or does not survive a reboot, setting up a new VPS, writing a bash script, or fixing permission denied and PATH errors.
---

# Linux servers and the machine

## Stance

A server is a small set of finite resources, a process supervisor and a list of who may do what.
Nearly every incident on one is a resource that ran out, a process that was killed or never
started, or a permission that did not match, and each leaves evidence in a known place. Work from
that evidence, change one thing, and leave the host in a state that a script can reproduce.

- **Measure before forming a theory.** Run the one-minute sweep and name the saturated resource
  before changing anything; a restart destroys the evidence and a guess usually tunes the wrong
  thing.
- **Look where the kernel wrote it down.** A process killed by the kernel logs nothing itself.
  Exit status, the kernel log and cgroup counters say why it died; the app log cannot.
- **The host must be rebuildable from the repository.** Every manual fix goes back into the
  provisioning script the same day, because the day the host must be replaced is the day nobody
  remembers what was done to it.
- **Keep a way back in.** Hold a second session open while changing SSH, sudo or firewall rules,
  validate config before reloading, and snapshot before touching a disk. Lockout and data loss
  are the two mistakes that cannot be undone from the same terminal.
- **Fix the one thing that is wrong, with least privilege.** Change the single path component or
  rule that fails. `chmod -R 777`, `--privileged` and broad sudo rules make the error disappear
  by removing the protection.
- **Let systemd supervise.** One unit per service, enabled, restarting, with a memory limit and
  its own user. No `nohup`, `screen` or second process manager: they hide exits and do not
  survive a reboot.
- **Cap everything that grows.** Logs, the journal, container logs, images and each service's
  memory get a limit on the day the host is built, so one runaway fails alone.
- **UTC and UTF-8 inside, conversion at the edges.** Hosts, databases and logs use UTC and
  UTF-8; zones and other encodings exist only where a person or a legacy system is involved.
- **Run as few machines as possible, and tune nothing without a counter.** A self-managed host
  is a standing commitment to patch and watch it; kernel settings change only when a specific
  metric proves the need.

## Route

| If the task is | Read |
|---|---|
| Finding where a config or log lives; "permission denied"; "command not found" or wrong PATH in cron, systemd or over SSH; a grep/awk/jq pipeline; a bash script that must be safe to rerun; rsync or scp; mounting or growing a volume | `references/shell-files.md` |
| The server is slow or load is high; out of memory at host level; the disk is full or about to be; which instance size or disk type to buy; swap, log rotation and disk alerts; steal time and noisy neighbors | `references/hardware-resources.md` |
| A service crashed, will not start or did not come back after reboot; writing a systemd unit or timer; reading journalctl; OOM-killer lines; "too many open files", port exhaustion or conntrack full; ss, lsof, strace, eBPF; TCP sysctls | `references/processes-systemd.md` |
| Installing Node, Python or a package on a host; adding an apt or dnf repository; automatic security updates and reboots; checking what a host exposes; cloud-init or a provisioning script; upgrade in place or rebuild; OS end of life | `references/packages-updates.md` |
| A fresh VPS that must be safe on the internet; SSH keys, config, jump hosts; sshd hardening; ufw or firewalld; tunnels to a private database; fail2ban and auth logs; removing someone's access; SSH certificates or identity-based access | `references/ssh-hardening.md` |
| A container is OOM-killed, throttled, slow to stop or exits 137; works on the host but not in a container; containers cannot reach each other; Docker fills the disk; running non-root and read-only; sandboxing untrusted code | `references/container-internals.md` |
| Timestamps or cron jobs off by an hour or a day; daylight-saving bugs; clock drift, expired-token or certificate-not-yet-valid errors; garbled characters; emoji length, accent or case-insensitive comparison problems | `references/time-encoding.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Run a server at all | No: a PaaS first (`0x:cloud-infrastructure`) | The PaaS limits the product or costs clearly more |
| Distribution | Current Ubuntu LTS or Debian stable | The project or team already uses another |
| Size | Prototype: 2 vCPU, 2 to 4 GB, burstable allowed. Launch: 2 to 4 vCPU, 4 to 8 GB, non-burstable | Measured peak: CPU above 60 to 70%, available memory under 20%, any swapping |
| Scaling | Up before out | Losing one host must be survivable (Scale) |
| Disks | General-purpose network SSD; data on its own volume; under 70 to 80% full | Latency-critical database: provisioned IOPS |
| Swap | 1 to 2 GB swap file, `vm.swappiness=10` | Orchestrator nodes that require none |
| Process supervision | systemd unit: own user, `Restart=always`, `MemoryMax`, `LimitNOFILE`, enabled | The app runs in containers with a restart policy |
| Scheduled jobs | systemd timer in UTC with a timeout and a heartbeat | More than one host: the app's job queue |
| Logs | stdout to journald, capped; Docker logs capped | Shipping to a log service from Launch (`0x:site-reliability`) |
| Access | Key-only SSH as a non-root sudo user, one ed25519 key per device, root login off | Team grows or audit needed: identity-based access |
| Firewall | Provider firewall default-deny plus ufw; public 80 and 443, SSH restricted where possible | |
| Updates | Automatic security updates with a nightly reboot window; database excluded and patched by hand | Several hosts: staggered, behind the load balancer |
| Provisioning | cloud-init plus one idempotent script in the repo | Several hosts or roles: configuration management or images |
| Runtime on a host | One pinned system-wide install, absolute path in the unit | Containers: the base image is the pin |
| Containers | Non-root, read-only root, capabilities dropped, memory limit, init or exec-form command | |
| Kernel and TCP settings | Untouched | A named counter shows the limit being hit |
| Time and text | Host in UTC with time sync; `timestamptz`; IANA zone names; UTF-8, NFC at input | |

By stage: at **Prototype** the PaaS or one small host with key-only SSH, firewall and automatic
updates is enough. At **Launch** add the provisioning script, per-service limits, disk and
heartbeat alerts, tested reboot, separate data volume with snapshots, and off-host logs. At
**Scale** move to replaceable hosts behind a load balancer, identity-based access, and eBPF or
kernel tuning only where measurements call for it.

## Before you call it done

1. The cause is named with evidence (a counter, a log line, an exit status), not inferred from
   the fix appearing to work.
2. `systemctl is-enabled` and `is-active` pass for every service, and the host has been rebooted
   once with everything returning unattended.
3. Killing the service (`systemctl kill -s KILL`) brings it back; stopping it takes less than the
   grace period, not exactly the timeout.
4. `sudo ss -tulnp` shows no listener on a public address without a reason, and a scan from
   outside shows only the intended ports on IPv4 and IPv6.
5. `sudo sshd -T` shows password and root login off, and a login as the admin user was tested
   from a new session before the old one closed.
6. Each service and container has a memory limit, runs as a non-root user, and the runtime's
   heap ceiling sits below the limit.
7. Journal, app logs and container logs are size-capped; `df -h` and `df -i` are under 80%; a
   disk alert and a job heartbeat reach a person.
8. Automatic security updates are on (`unattended-upgrade --dry-run` or the dnf timer), with a
   reboot policy, and no reboot is pending.
9. Every script passes `shellcheck`, uses `set -euo pipefail`, and a second run changes nothing
   and exits 0.
10. Every change made on the host is in the provisioning script or a unit file in the repo; no
    secret is in user data, a unit file, shell history or a command line.
11. Any fstab edit passed `findmnt --verify` and `mount -a`; non-root volumes have `nofail`; a
    snapshot preceded any resize, move or `mkfs`.
12. `timedatectl` shows UTC and a synchronized clock; new timestamp columns are `timestamptz`
    and zones are stored by IANA name.
13. Scheduled jobs have overlap protection, a timeout, and were run once by hand under the same
    environment the scheduler provides.
14. Nothing inside a database data directory or `/var/lib/docker/overlay2` was deleted by hand.

## Not this skill

- Writing Dockerfiles, Compose files or Kubernetes manifests → `0x:cloud-infrastructure`
- DNS, TLS, reverse proxies and anything between the browser and the box → `0x:web-networking`
- Deploy pipelines, releases and rollbacks → `0x:ci-cd-release`
- Postgres tuning, backups and slow queries → `0x:postgres-database`
- Application logs, dashboards, alerts and incident process → `0x:site-reliability`
- A slow page or endpoint when the host has CPU, memory and disk to spare → `0x:web-performance`
