# Processes, systemd and kernel limits

Read this when: a service died, will not start, does not come back after a reboot, leaks memory or
file descriptors, needs a unit file or a scheduled job, or hits a kernel limit under load.

## Why did it die

Ask systemd first; it recorded how the main process ended.

```bash
systemctl status myapp                      # state, last exit, the last log lines
systemctl show myapp -p Result,ExecMainCode,ExecMainStatus,NRestarts,MemoryPeak
journalctl -u myapp -b -n 200 --no-pager    # this boot; add -b -1 for the previous boot
sudo journalctl -k -b | grep -iE 'killed process|out of memory|segfault|i/o error'
```

| What status shows | Meaning | Where to look next |
|---|---|---|
| `code=exited, status=1` (any small number) | The app chose to exit: uncaught error, bad config | The app's own last log lines |
| `status=127`, or `status=203/EXEC` | Command not found, not executable, bad shebang, wrong architecture | `ExecStart` path, `ls -l`, PATH (see `shell-files.md`) |
| `status=126` | Found but not executable | Mode, `noexec` mount |
| `status=200/CHDIR`, `217/USER`, `226/NAMESPACE` | `WorkingDirectory`, `User`, or a sandbox path does not exist | The unit file |
| `code=killed, signal=KILL` (exit 137 in a shell or container) | SIGKILL: the OOM killer, a stop timeout, or a person | Kernel log for an OOM line; `Result=oom-kill` |
| `signal=TERM` (143) | Asked to stop: a deploy, a reboot, another unit | Journal around that time: `journalctl --since -10min` |
| `signal=SEGV` (139), `signal=ABRT` (134) | Native crash, or the runtime aborted. Node aborts with 134 on "JavaScript heap out of memory" | Core dump (`coredumpctl list`), the line before the abort |
| `Result=timeout` | Start or stop exceeded its timeout | `Type=` mismatch (see below), slow shutdown handler |
| `Result=start-limit-hit` | It crash-looped and systemd gave up | Fix the crash, then `systemctl reset-failed myapp` |

Exit codes above 128 are 128 plus the signal number. A process killed by the kernel writes nothing
to its own log: "it just vanished, no stack trace" is the signature of SIGKILL, and the evidence
is in the kernel log, not the app log.

Signals: send `TERM` and wait; use `KILL` only when that fails, because the process gets no chance
to finish requests, flush or release locks. `HUP` conventionally means reload config. A zombie
(`Z` in `ps`) is already dead and cannot be killed; its parent is not collecting it, so fix or
restart the parent.

```bash
ps -eo pid,ppid,user,state,etime,rss,args --sort=-rss | head -15   # biggest by memory
ps -ef --forest                                                    # who started what
```

## journalctl

| Need | Command |
|---|---|
| Follow a service | `journalctl -u myapp -f` |
| A time window | `journalctl -u myapp --since '2026-11-23 09:00' --until '09:30'`; `--since -2h` |
| Errors only | `journalctl -u myapp -p err` (err and worse; only useful if the app sets priorities) |
| Previous boot, to see what preceded a crash or reboot | `journalctl -b -1 -e` |
| Kernel messages | `journalctl -k` |
| Search | `journalctl -u myapp -g 'timeout\|ECONNRESET'` |
| Raw message for piping to `jq` | `journalctl -u myapp -o cat --no-pager \| jq -R 'fromjson?'` |
| Several units interleaved | `journalctl -u nginx -u myapp --since -10min` |
| Timestamps in UTC | add `--utc -o short-iso` |
| Disk used | `journalctl --disk-usage` |

Traps: without membership of `adm` or `systemd-journal` (or sudo) only the user's own entries are
shown and the output looks empty. Under a log flood journald rate-limits and drops messages
(a "Suppressed N messages" line); the missing lines are not an app bug. If `/var/log/journal/`
does not exist, the journal lives in memory and is lost at reboot; create the directory or set
`Storage=persistent`. Each line of a multi-line stack trace is a separate entry.

## A unit that restarts on crash and starts on boot

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My app
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=20

[Service]
User=app
Group=app
WorkingDirectory=/srv/app/current
EnvironmentFile=/etc/myapp/env
ExecStart=/usr/local/bin/node server.js
Restart=always
RestartSec=3
TimeoutStopSec=30
LimitNOFILE=65536
MemoryMax=1G
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/app/shared

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemd-analyze verify /etc/systemd/system/myapp.service
sudo systemctl daemon-reload && sudo systemctl enable --now myapp
```

Decisions and traps:

- `enable` makes it start at boot; `start` runs it now. They are independent, and "did not come
  back after reboot" is most often a unit that was started and never enabled. `enable --now` does
  both. Without an `[Install]` section `enable` does nothing useful.
- `ExecStart` is not a shell: no pipes, `&&`, redirection or `~`. Use an absolute path to the
  binary. If shell features are needed, call a script.
- Run the process in the foreground with the default `Type=simple`. Do not let the app daemonize,
  and do not wrap it in `nohup`, `screen` or a second process manager; systemd then tracks the
  wrong process. Use `Type=notify` only when the app really sends readiness notifications,
  otherwise start times out.
- `Restart=always` for servers. `on-failure` does not restart after exit code 0 or a clean signal,
  which leaves a service down after an unexpected clean exit.
- Restart limits: by default a unit that starts 5 times within 10 seconds is marked failed and
  left down. With a short `RestartSec` a crash loop reaches that in seconds. Set `RestartSec` to a
  few seconds and the limits explicitly as above, and alert on `NRestarts` rising: a service that
  restarts forever looks healthy to systemd.
- Stop behavior: systemd sends SIGTERM, waits `TimeoutStopSec` (default 90 s), then SIGKILL. The
  app must handle SIGTERM by finishing in-flight requests and closing; keep the timeout longer
  than the longest request and shorter than the deploy tolerates.
- Other causes of "works when started by hand, not at boot": it needs a mount
  (`RequiresMountsFor=/mnt/data`), it needs the network or database up (add retry on startup in
  the app; ordering alone does not guarantee the peer accepts connections), or it is a user unit
  (`systemctl --user`) and lingering is off (`loginctl enable-linger <user>`).
- Change packaged units with `sudo systemctl edit <unit>` (a drop-in), never by editing files
  under `/usr/lib/systemd/`.
- `systemd-analyze security myapp` scores the sandbox. The five hardening lines above are the
  cheap majority of the benefit; add `ReadWritePaths` for each directory the app must write.

Prove it: `sudo systemctl kill -s KILL myapp` and watch it return; reboot the host once before
Launch and confirm `systemctl is-active myapp` without logging in to fix anything.

## Sockets, files and system calls

```bash
sudo ss -ltnp                      # listening TCP sockets with owning process
sudo ss -ltnp 'sport = :3000'      # who holds port 3000 ("address already in use")
ss -s                              # socket counts by state
ss -tan state time-wait | wc -l    # sockets in TIME-WAIT
sudo lsof -p <pid> | wc -l         # everything a process has open
sudo lsof -i :5432                 # processes with connections on a port
sudo lsof +L1                      # deleted files still held open
```

- A listener on `127.0.0.1:3000` is unreachable from other hosts and from other containers;
  "connection refused from outside, works with curl on the box" is a bind-address problem. A
  listener on `0.0.0.0` or `*` is reachable by anything the firewall lets through.
- In `ss -ltn`, `Send-Q` is the configured accept backlog and `Recv-Q` the connections waiting to
  be accepted. `Recv-Q` staying near `Send-Q` means the app is not accepting fast enough.

`strace` shows what a process asks the kernel for. It answers "what file is it failing to open"
and "what is it blocked on" when logs do not.

```bash
sudo strace -f -e trace=file -o /tmp/trace.txt <command>   # then grep ENOENT or EACCES
sudo strace -f -p <pid> -e trace=network -tt -T -s 200     # live network calls with durations
sudo strace -c -f -p <pid>                                 # Ctrl-C after 10 s: counts and time per syscall
```

A process blocked in `read(7, ...` is waiting on descriptor 7: `sudo ls -l /proc/<pid>/fd/7` names
the file or socket. `strace` slows the traced process heavily; attach to a busy production process
only for seconds, or use the eBPF tools below.

## OOM kills: too-low limit or leak

```bash
sudo journalctl -k | grep -iE 'out of memory|oom-kill|killed process'
```

The kernel logs which constraint was hit and the victim's memory:

| Log line contains | Meaning |
|---|---|
| `Memory cgroup out of memory` / `constraint=CONSTRAINT_MEMCG` | A cgroup limit was hit: a container's memory limit or a unit's `MemoryMax`. The host may have plenty free |
| `Out of memory:` / `constraint=CONSTRAINT_NONE` | The whole host ran out |
| `Killed process 1234 (node) ... anon-rss:` | The victim and its resident memory at death |

On a host-wide OOM the victim is the process with the highest badness score, roughly the largest,
which is often the database rather than the process that grew. Protect what must survive and make
the expendable killable: `OOMScoreAdjust=-900` on the database unit, a positive value on workers.
Better, give the growing service its own `MemoryMax` so it is killed alone and restarted.

| Evidence | Diagnosis | Action |
|---|---|---|
| Memory rises to a plateau soon after start, kills happen at traffic peaks | Limit too low, or too many workers or concurrent requests for the limit | Raise the limit or lower concurrency; size from the plateau plus headroom |
| Memory climbs steadily for hours or days at constant traffic, drops only on restart | Leak | Heap snapshots or the runtime's profiler; a timed restart is an acceptable stopgap before Scale |
| Kills line up with one job or endpoint | One operation loads too much at once | Stream or paginate it |
| Kills at the same time each day | A scheduled job (backup, report) pushes the host over | Limit that job with its own unit and `MemoryMax` |

Sample to see the shape: `systemctl status` shows current and peak memory for the unit;
`systemd-cgtop -m` ranks units live.

Node specifics: V8 has its own heap ceiling. Set `--max-old-space-size` (in MB) to about 75% of
the unit or container limit, so V8 collects harder and fails with a readable "heap out of memory"
error instead of being SIGKILLed with nothing in the log. Resident memory exceeds the V8 heap
(buffers, native modules), so a leak outside the heap shows in RSS but not in heap statistics.

Some distributions run `systemd-oomd`, which kills whole cgroups under sustained memory pressure
before the kernel does; its decisions are in `journalctl -u systemd-oomd`.

## Scheduled work

| | systemd timer | cron |
|---|---|---|
| Overlap | A running `oneshot` service is not started again | Starts a second copy; wrap with `flock` |
| Missed runs (host was down) | `Persistent=true` runs it at next boot | Skipped silently |
| Logs and exit status | Journal, `systemctl status` | Mailed to a local mailbox nobody reads |
| Environment | The unit's, same as services | Minimal PATH; `%` in the command line means newline unless escaped as `\%` |
| Limits, timeout, user | Unit directives | None |

Default to timers on a systemd host. Cron is acceptable for a one-line job that already exists.

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=Nightly backup
[Service]
Type=oneshot
User=app
ExecStart=/srv/app/bin/backup.sh
TimeoutStartSec=1h
```

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Nightly backup
[Timer]
OnCalendar=*-*-* 03:15:00
RandomizedDelaySec=10m
Persistent=true
[Install]
WantedBy=timers.target
```

```bash
systemd-analyze calendar '*-*-* 03:15:00'        # validates and prints the next run
sudo systemctl daemon-reload && sudo systemctl enable --now backup.timer   # the timer, not the service
systemctl list-timers; sudo systemctl start backup.service                 # see schedule; run once now
```

Cron equivalent with overlap protection, using a lock file the job's user can write:
`15 3 * * * flock -n /tmp/backup.lock /srv/app/bin/backup.sh`.

- `OnCalendar` is in the host's local time zone unless a zone is appended. Keep hosts in UTC
  (`time-encoding.md`) so schedules have no daylight-saving gaps or repeats.
- Give every job a timeout. A hung job with overlap protection blocks every later run silently.
- Detect silence, not only failure: have the job ping a heartbeat monitor on success and alert when
  the ping is missing. A job that never starts raises no error.
- With more than one app host, a host-level timer runs once per host. Run it on one designated
  host or move the schedule into the application's job queue (`0x:backend-architecture`).

## Limits that run out under load

| Limit | Symptom | Check | Raise |
|---|---|---|---|
| File descriptors per process | `EMFILE`, "Too many open files", accept errors | `grep 'open files' /proc/<pid>/limits`; `ls /proc/<pid>/fd \| wc -l` | `LimitNOFILE=65536` in the unit |
| Tasks per unit | "Resource temporarily unavailable" on fork or thread creation | `systemctl status` shows `Tasks: n (limit: m)` | `TasksMax=` in the unit |
| Connection tracking table | Random connection timeouts; `nf_conntrack: table full, dropping packet` in the kernel log | `sysctl net.netfilter.nf_conntrack_count net.netfilter.nf_conntrack_max` | `net.netfilter.nf_conntrack_max` |
| Ephemeral ports | `EADDRNOTAVAIL`, "Cannot assign requested address" on outbound connects | `sysctl net.ipv4.ip_local_port_range`; TIME-WAIT count | Reuse connections first; then widen the range |
| inotify watches | "System limit for number of file watchers reached" (`ENOSPC`) from dev servers and watchers | `sysctl fs.inotify.max_user_watches` | Raise it in `sysctl.d` |
| Memory map areas | Search engines and some databases refuse to start | `sysctl vm.max_map_count` | The value the software documents |

- `/etc/security/limits.conf` and `ulimit` in a profile apply to login sessions only. They do not
  affect systemd services; set `Limit*=` in the unit and verify in `/proc/<pid>/limits`.
- A descriptor count that keeps rising at steady traffic is a leak (unclosed sockets or files).
  Raising the limit only delays the failure; find it with `lsof -p <pid>` grouped by type.
- Ephemeral ports limit connections from one source address to one destination address and port
  (roughly 28,000 with the default range), and closed connections hold their port in TIME-WAIT for
  about a minute. It is hit by a proxy or app that opens a new connection per request to one
  upstream. The fix is keep-alive and connection pools; widening `ip_local_port_range` is second.
  Never enable `tcp_tw_recycle` from old guides; it broke clients behind NAT and was removed.
- Conntrack exists only when stateful firewall or NAT rules are loaded, which includes Docker.

Persist kernel settings in `/etc/sysctl.d/90-<reason>.conf` with a comment saying which symptom
justified them, then `sudo sysctl --system`.

## TCP tuning

Default: change nothing. Modern kernels autotune buffers, and most "sysctl tuning" lists are
copied from another decade. Change one setting when a counter proves the need.

| Evidence | Setting | Notes |
|---|---|---|
| `nstat -az TcpExtListenOverflows TcpExtListenDrops` rising | The app's `listen()` backlog, capped by `net.core.somaxconn` | First ask why accepts are slow: a blocked event loop or too few workers. A bigger queue only lets clients wait longer |
| SYN flood or bursts of new connections dropped | `net.ipv4.tcp_max_syn_backlog`; keep `net.ipv4.tcp_syncookies=1` | Real floods are absorbed upstream (`0x:web-networking`) |
| Idle connections die silently behind a load balancer or NAT | Keep-alive interval below the middlebox idle timeout, set in the client library or pool; system default `net.ipv4.tcp_keepalive_time` is 2 hours | Applies to database and upstream connections held open |
| Slow large transfers over long or lossy paths, served directly to clients | `net.core.default_qdisc=fq` and `net.ipv4.tcp_congestion_control=bbr` | Check `sysctl net.ipv4.tcp_available_congestion_control`. Behind a CDN it only affects the CDN-to-origin hop |
| High-bandwidth transfers between distant hosts capped below link speed | `net.core.rmem_max`, `net.core.wmem_max`, `net.ipv4.tcp_rmem`, `net.ipv4.tcp_wmem` maximums | Rare for web workloads |

Measure before and after with the same counter, and revert what shows no effect.

## eBPF tools

Use them when the USE sweep (`hardware-resources.md`) and the application profiler do not explain
latency. They need root and a host kernel (not available inside most PaaS containers). On Debian
and Ubuntu the `bpfcc-tools` package installs them with a `-bpfcc` suffix; `bpftrace` is separate.

| Question | Tool |
|---|---|
| How long do disk requests take, as a histogram | `biolatency`; per request: `biosnoop` |
| Are threads waiting for a CPU (saturation, throttling) | `runqlat` |
| Which file operations are slow | `ext4slower`, `xfsslower` |
| Who connects where, and how long do connections live | `tcpconnect`, `tcpaccept`, `tcplife` |
| Which connections retransmit | `tcpretrans` |
| Is something spawning short-lived processes that `top` never shows | `execsnoop` |
| Which files are being opened, and which opens fail | `opensnoop -x` |
| Where is CPU time going across the whole host | `profile` (sampling, for flame graphs) |
| What is the process blocked on when off-CPU | `offcputime` |

```bash
sudo bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'   # syscalls by process
```

Overhead is far below `strace`, but tracing very frequent events (scheduler switches, every
packet) on a busy host is still measurable: run for tens of seconds, not hours.

## Ask the user

- **How much memory may this service use before it is killed and restarted?** `MemoryMax` trades
  one service's uptime for the host's. Default: a limit that leaves room for the database and OS,
  with `Restart=always`.
- **How long may a request or job run during shutdown?** It sets `TimeoutStopSec` and how long a
  deploy waits. Default: 30 seconds for web processes, longer for job workers.
- **Is a daily automatic restart acceptable while a leak is investigated?** It hides the leak and
  keeps customers served. Default: yes at Prototype and Launch, with a ticket to fix the cause.
- **If the nightly job fails or does not run, who must know and how fast?** Backups and billing
  jobs need a heartbeat alert; a cache warm-up does not. Default: heartbeat on anything touching
  data or money.
- **Does the scheduled time mean UTC or the business's local time?** A report "at 9 am" for
  customers is a local-time requirement. Default: UTC on the host, local-time logic in the app.
