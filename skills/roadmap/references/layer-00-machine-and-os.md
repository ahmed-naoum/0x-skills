# Layer 0: Machine & OS

Read this when: the user asks what there is to know about machine & os, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

What is my code actually running on?

Competencies: 57 (17 ● / 30 ◐ / 10 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## linux-server

Set up, harden, script and diagnose the Linux machine your code runs on, from CPU, memory and disk limits to systemd, SSH and container internals.

**Shell, files and permissions** (`references/shell-files.md`)

- ● Find files, logs and config using the standard Linux directory layout
- ● Fix permission-denied errors using users, groups, modes and sudo rules
- ● Compose pipes with grep, sed, awk, jq and xargs to answer a question
- ● Write a safe Bash script with strict mode and correct quoting
- ● Manage environment variables, PATH and shell profiles without surprises
- ● Make scripts idempotent so rerunning them is safe
- ◐ Transfer and sync files with rsync and scp, preserving permissions
- ◐ Decide when a shell script should become a real program
- ◐ Mount, resize and check filesystems and volumes without losing data

**Hardware resources and limits** (`references/hardware-resources.md`)

- ● Read live CPU, memory, disk and network usage and name the bottleneck
- ● Tell CPU saturation from I/O wait or memory pressure when load average is high
- ● Choose instance size by CPU architecture, memory and network needs
- ◐ Set log rotation, disk alerts and swap policy before a host fills
- ◐ Diagnose a saturated host with the USE method
- ◐ Choose disk type and size by IOPS, throughput and durability needs
- ◐ Free a full disk safely without deleting database or WAL files
- ○ Benchmark disk IOPS and fsync latency for a database volume
- ○ Diagnose tail latency from CPU steal, NUMA and noisy neighbors

**Processes, systemd and kernel limits** (`references/processes-systemd.md`)

- ● Inspect processes, signals and exit codes to find why a service died
- ● Read and filter service logs with journalctl
- ◐ Write a systemd unit that restarts on crash and starts on boot
- ◐ Inspect open sockets, files and system calls with ss, lsof and strace
- ◐ Read the OOM killer's log and tell a too-low limit from a leak
- ◐ Schedule recurring work with systemd timers or cron, with overlap protection
- ○ Raise file-descriptor, conntrack and ephemeral-port limits before exhaustion
- ○ Tune kernel TCP backlog, buffers and congestion control
- ○ Trace kernel and network latency with eBPF tools

**Packages, updates and provisioning** (`references/packages-updates.md`)

- ● Install language runtimes with version managers, not distro packages
- ◐ Install and pin packages with apt or dnf from trusted repositories
- ◐ Apply kernel and package security updates on a schedule, including reboots
- ◐ Audit what is installed, running and listening before exposing a host
- ◐ Provision a server repeatably with cloud-init or a script, not by hand
- ◐ Decide when to patch a host in place versus replace it
- ◐ Track operating-system end-of-life dates and plan the upgrade

**SSH access and host hardening** (`references/ssh-hardening.md`)

- ● Manage SSH keys, config files, agent and jump hosts safely
- ◐ Create a non-root sudo user and lock root's password on a fresh VPS
- ◐ Harden SSH: keys only, no root login, restricted users
- ◐ Configure a host firewall that allows only the ports in use
- ◐ Use SSH tunnels and port forwarding to reach private services
- ◐ Throttle brute-force attempts and review authentication logs
- ○ Replace long-lived SSH keys with short-lived certificates or identity-based access

**Virtualization and container internals** (`references/container-internals.md`)

- ● Tell whether a fault is in the app, the container or the host
- ● Inspect a running container's processes, network and filesystem from the host
- ◐ Debug OOM-killed or CPU-throttled containers from cgroup metrics
- ◐ Run containers non-root, read-only and with dropped capabilities
- ◐ Handle PID 1, signal forwarding and zombie reaping inside a container
- ◐ Find which image layers and container writes consume disk and prune them safely
- ○ Decide when untrusted code needs a microVM or VM instead of a shared-kernel container
- ○ Trace container networking: bridges, port mapping and DNS between containers

**Time, time zones and text encoding** (`references/time-encoding.md`)

- ● Store timestamps in UTC and convert time zones only at the edges
- ● Store and transmit text as UTF-8 and fix mojibake at its source
- ◐ Run servers in UTC and keep clocks synced with NTP
- ◐ Store time-zone names, not offsets, and keep the zone database current
- ◐ Handle DST and recurring local-time schedules without off-by-one-hour bugs
- ◐ Choose monotonic versus wall-clock time for durations and timeouts
- ○ Write code tolerant of clock skew between machines
- ○ Handle Unicode normalization, grapheme length and case-folding in comparisons
