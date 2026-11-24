# Hardware resources and limits

Read this when: a host is slow, load is high, memory or disk is running out, a disk is full, or the
task is to choose an instance size or disk type for a workload.

## The first minute on a slow host

Run these in order and read them before forming a theory. `mpstat`, `pidstat`, `iostat` and `sar`
come from the `sysstat` package; install it when the host is built, not during the incident.

```bash
uptime                      # load averages: rising or falling over 1, 5, 15 minutes
sudo dmesg -T | tail -30    # OOM kills, I/O errors, dropped packets, filesystem remounts
vmstat 1 5                  # r, b, si/so, us/sy/id/wa/st in one view; ignore the first line
mpstat -P ALL 1 3           # per-CPU: one core pinned at 100% hides in an average
pidstat 1 3                 # which process uses the CPU
iostat -xz 1 3              # per-device latency, queue and utilization
free -m                     # read "available", not "free"
sar -n DEV 1 3              # network throughput per interface
cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io
df -h; df -i                # space and inodes
```

How to read them:

| Reading | Meaning |
|---|---|
| `vmstat` `r` persistently above the CPU count (`nproc`) | CPU saturation: work is queued for a core |
| `vmstat` `b` above 0 with high `wa` | Tasks blocked on I/O |
| `vmstat` `si`/`so` non-zero for more than a moment | Swapping: memory pressure is now a disk problem |
| `st` above a few percent, sustained | The hypervisor is giving the CPU to someone else, or burst credits ran out |
| `free`: low "free", high "buff/cache", healthy "available" | Normal. Page cache is reclaimable; Linux uses spare memory for it on purpose |
| `free`: "available" under roughly 10% of total | Real memory pressure |
| `iostat` `r_await`/`w_await` in tens of ms on SSD | The device or its provisioned limit is saturated |
| `iostat` `aqu-sz` growing | Requests are queuing |
| `iostat` `%util` near 100 | On a single spindle, saturated; on NVMe and network volumes it only means "always busy", so judge by await and queue instead |
| One CPU at 100% in `mpstat`, others idle | A single-threaded process (a Node event loop, one Postgres query) is the limit; more cores will not help |

Pressure stall information (PSI) is the most direct signal: `some avg10=12.50` in
`/proc/pressure/io` means that over the last 10 seconds at least one task was stalled on I/O 12.5%
of the time. `full` means all non-idle tasks were stalled at once. Sustained `some` above roughly
10% for a resource is worth acting on; treat that threshold as a rule of thumb. With cgroup v2 the
same files exist per service and per container (`cpu.pressure`, `memory.pressure`, `io.pressure`).
If `/proc/pressure` is missing, the kernel has PSI turned off by default; boot with `psi=1` to
enable it.

## High load average: which resource is it

Linux load average counts tasks that are runnable plus tasks in uninterruptible sleep (usually
waiting on disk). A load of 8 on 4 cores is therefore not necessarily a CPU problem. Compare load
with `nproc`, then split it:

| Evidence | Bottleneck | Next step |
|---|---|---|
| `us`+`sy` high, `r` > cores, `wa` low | CPU | `pidstat 1`, `top` (press `1` for per-core, `H` for threads); profile the process |
| `sy` high rather than `us` | Kernel work: syscalls, network, context switches, reclaim | `pidstat -w 1` for context switches; `perf top` |
| `wa` high, `b` > 0, CPU otherwise idle | Disk I/O | `iostat -xz 1`, `sudo iotop -o`, `pidstat -d 1` |
| `si`/`so` non-zero, low "available", memory PSI high | Memory; the I/O wait is swap traffic | `ps aux --sort=-rss \| head`; find the growth, then add memory or fix the leak |
| `st` high | Stolen CPU | See tail latency below |
| Load high, all of the above quiet | Tasks stuck in `D` state on a hung mount (NFS, a detached volume) | `ps -eo state,pid,cmd \| awk '$1=="D"'` |

If CPU, memory and disk all have headroom and a request is still slow, the host is not the problem:
the time goes to a lock, a downstream call or the query plan. Go to `0x:web-performance`.

## USE method: a full sweep

For every resource check Utilization, Saturation and Errors. Saturation and errors are what people
skip, and they are where the answer usually is.

| Resource | Utilization | Saturation | Errors |
|---|---|---|---|
| CPU | `mpstat -P ALL 1` | `vmstat` `r` > cores; `/proc/pressure/cpu`; cgroup `nr_throttled` | machine-check lines in `dmesg` |
| Memory | `free -m` available | `si`/`so`; `/proc/pressure/memory`; OOM kills in `dmesg` | `dmesg` allocation failures |
| Disk I/O | `iostat -xz 1` | `aqu-sz`, `await`; `/proc/pressure/io` | `dmesg` I/O errors, filesystem remounted read-only |
| Disk space | `df -h`, `df -i` | n/a | "No space left on device" in logs |
| Network | `sar -n DEV 1` against the instance's limit | drops in `ip -s link`; `nstat -az TcpExtListenOverflows TcpRetransSegs` | errors in `ip -s link` |
| File descriptors | `ls /proc/<pid>/fd \| wc -l` against `/proc/<pid>/limits` | n/a | "Too many open files" |
| Connection tracking | `sysctl net.netfilter.nf_conntrack_count net.netfilter.nf_conntrack_max` | n/a | "nf_conntrack: table full" in `dmesg` |
| Cloud quotas | CPU credit balance, volume burst balance, network allowances in the provider's metrics | credits at zero | provider throttling metrics |

The last row has no Linux command and is the classic invisible limit: a burstable instance or a
burst-credit volume performs well for hours, exhausts its credits and then looks like a slow host
with nothing wrong. Check the provider's credit graphs whenever a slowdown has a clean start time.

## Choosing an instance

Size memory first; it is the resource that fails hard. CPU shortage makes things slow, memory
shortage kills processes.

- **Memory**: add peak resident memory of every process (app workers times their count, database,
  cache, agents), then keep at least 20 to 25% available at peak for page cache and spikes. A
  database on the same host wants most of its data's hot set in memory.
- **CPU**: a Node process uses one core for JavaScript. More vCPUs help only with more processes
  (one worker per core) or other services on the box. Two vCPUs is the practical minimum for a
  production host, so a deploy, a backup or a log shipper does not starve the app.
- **vCPU is not a core everywhere**: on most x86 instance types a vCPU is one hyperthread, so two
  vCPUs are one physical core. On Arm instance types a vCPU is a full core.
- **Architecture**: Arm instances usually cost less for the same work. Before choosing them, check
  that every native dependency and base image has an `arm64` build, and that CI builds the image
  for the architecture it will run on; building under emulation is slow and a wrong-architecture
  image fails with "exec format error".
- **Burstable or shared-CPU types**: right for Prototype and for services that idle most of the
  time. Wrong for anything with steady CPU above the type's baseline and for databases. What
  happens when credits run out depends on the credit mode: in a standard mode the CPU drops to
  the baseline and steal time rises; in an "unlimited" mode the instance keeps bursting and the
  surplus is billed. Some providers launch burstable types in the unlimited mode by default (AWS
  does for its current T families), so the symptom is a larger bill, not a slow host. Check the
  mode and the surplus-credit metric when choosing one.
- **Network**: bandwidth and packet-rate limits scale with instance size and are enforced silently.
  For most web products the bill for outbound traffic matters before the bandwidth limit does;
  check the provider's egress pricing for media-heavy products.
- **Local NVMe on a large cloud (instance store, local SSD, temporary disk)** is fast and is
  erased when the instance stops, is resized or is replaced. Use it for caches and scratch only.
  A VPS's local disk is different: it persists across reboots but lives and dies with that one
  machine, so it still needs snapshots and off-host backups.

| Stage | Starting point | Change when |
|---|---|---|
| Prototype | One small host (2 vCPU, 2 to 4 GB) or a PaaS; burstable is fine | Memory available under 20% at peak, or credits run out |
| Launch | App on 2 to 4 vCPU and 4 to 8 GB, non-burstable; database managed or on its own host | Peak CPU above about 60 to 70% for sustained periods, any swap activity, PSI rising |
| Scale | Several identical app hosts behind a load balancer; sized so losing one is survivable | Capacity planning belongs to `0x:site-reliability` |

Scale up before scaling out: a resize is a reboot, a second host is a load balancer, shared
sessions and a deploy change. Size from measurements at peak, not from averages.

## Choosing a disk

| Workload | What it needs | Disk class |
|---|---|---|
| Database, queue, anything that calls fsync per transaction | Random IOPS and low, steady write latency | General-purpose network SSD with enough provisioned IOPS; provisioned-IOPS class when latency must be consistent |
| Logs, backups, media, analytics scans | Sequential throughput (MB/s) | General-purpose SSD; throughput-optimized HDD class for large cold data |
| Build cache, temp files, replicas you can rebuild | Speed, no durability | Local NVMe |
| OS and app code | Little | Smallest general-purpose SSD that leaves room for logs and images |

- Throughput equals IOPS times I/O size, and volumes cap both. Small random I/O hits the IOPS cap;
  large sequential I/O hits the throughput cap. The instance has its own separate storage limits,
  so a fast volume on a small instance is throttled by the instance.
- On volume classes where IOPS scale with size or depend on burst credits, a small volume is also
  a slow volume. Prefer classes where size, IOPS and throughput are set independently.
- Keep data volumes under 70 to 80% full. Postgres needs headroom for WAL, temporary files and
  table or index rebuilds, which can need as much space again as the object being rebuilt.
- Durability: a network volume is replicated within its zone, which protects against a failed disk,
  not against deletion, corruption or losing the zone. Snapshots and off-host backups do. A single
  VPS disk has neither unless backups are enabled and tested.
- Put data on a separate volume from the OS. It can then be snapshotted, grown and moved to a new
  host without touching the system disk, and a log flood cannot fill the database's disk.

## Before a host fills: rotation, alerts, swap

Cap everything that grows without bound on the day the host is built:

```ini
# /etc/systemd/journald.conf.d/size.conf   (then: systemctl restart systemd-journald)
[Journal]
SystemMaxUse=1G
```

```text
# /etc/logrotate.d/myapp   (test with: sudo logrotate -d /etc/logrotate.d/myapp)
/var/log/myapp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

- `copytruncate` is for apps that cannot reopen their log file; it can lose lines written during
  the copy. Simpler and lossless: log to stdout and let journald keep it.
- Docker's default `json-file` log driver has no size limit. Set `max-size` and `max-file` under
  `log-opts` in `/etc/docker/daemon.json`; it applies to containers created afterwards.
- Alerts on every mounted filesystem: ticket at 80% of space or inodes; page when the current rate
  predicts full within 4 hours (inodes: also page at 95%). Thresholds and routing:
  `0x:site-reliability` (`dashboards-alerting.md`).

Swap policy: give app hosts a small swap file (1 to 2 GB) and `vm.swappiness=10`. It converts a
sudden out-of-memory kill into a slowdown that can be noticed and alerted on. Alert on swap-in and
swap-out rate or memory PSI, not on swap used: pages parked in swap do no harm. A host that swaps
continuously needs more memory or a fixed leak, not more swap.

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/60-swap.conf && sudo sysctl --system
```

If `swapon` rejects the file as having holes, create it with `dd` instead of `fallocate`.

## A full disk: free space without losing data

1. `df -h` and `df -i` to see which filesystem and whether it is space or inodes.
2. `sudo du -xh --max-depth=1 / 2>/dev/null | sort -h | tail` and descend into the largest
   directory. `-x` stays on one filesystem. `ncdu -x /` is the interactive equivalent.
3. If `du` adds up to much less than `df` reports, a deleted file is still held open:
   `sudo lsof +L1`. Restart that process, or empty the file through its descriptor with
   `: | sudo tee /proc/<pid>/fd/<n>`.
4. Free space from this list, safest first:

| Safe to reclaim | Command |
|---|---|
| Journal | `sudo journalctl --vacuum-size=500M` |
| Package cache and unused packages, old kernels | `sudo apt-get clean; sudo apt-get autoremove --purge` |
| Rotated, compressed logs | delete old `*.gz` under `/var/log` |
| A live log that grew huge | `sudo truncate -s 0 /var/log/myapp/app.log` (not `rm`: the process keeps the deleted file open and no space returns) |
| Core dumps | `/var/lib/systemd/coredump/`, `/var/crash/` |
| Old releases, build output, package-manager stores | the app's own `releases/`, `~/.npm`, the pnpm store |
| Unused images and build cache | see `container-internals.md` before pruning; volumes hold data |

Do not delete or truncate anything inside a database's data directory. For Postgres that includes
`pg_wal/` (write-ahead log) and `pg_xact/`: they look like disposable logs and removing them
destroys the database. When WAL fills the disk, free space elsewhere or grow the volume so the
database can start, then find why WAL is retained (a failing archive command or an abandoned
replication slot): `0x:postgres-database`.

Emergency helpers: ext4 reserves 5% of blocks for root, so root can still write when users cannot;
on a large data volume lower it with `sudo tune2fs -m 1 <device>`. Growing the volume online
(see `shell-files.md`) is often faster and safer than deciding what to delete under pressure.

For inode exhaustion, find the directory with millions of entries:
`sudo find / -xdev -type f | cut -d/ -f2-4 | sort | uniq -c | sort -rn | head`.

## Benchmarking a database volume

Benchmark only to answer a question: does this volume deliver what was provisioned, and is fsync
fast enough for the commit rate. Use `fio` on the real volume, in a scratch directory, never on a
raw device that holds data.

```bash
mkdir -p /mnt/data/fio && cd /mnt/data/fio

# Commit latency: sequential 8k writes with a data sync after each, like a WAL
fio --name=wal --rw=write --bs=8k --size=1G --ioengine=sync --fdatasync=1 \
    --runtime=60 --time_based

# Random mixed IOPS, cache bypassed
fio --name=rand --rw=randrw --rwmixread=70 --bs=8k --size=4G --ioengine=libaio --direct=1 \
    --iodepth=32 --numjobs=4 --runtime=300 --time_based --group_reporting
```

- Read the sync latency percentiles from the first test, not the mean. Each committing transaction
  waits for one sync, so p99 sync latency bounds p99 commit latency. As a rule of thumb, low
  single-digit milliseconds is normal for network SSD and well under one for local NVMe; tens of
  milliseconds means the volume will limit write throughput.
- Without `--direct=1` (or a file larger than RAM) the second test measures the page cache.
- Run long enough to outlast burst credits; a cloud volume's first minutes can be far faster than
  its sustained rate. Compare the sustained IOPS with what was provisioned.
- `pg_test_fsync`, shipped with Postgres, answers the commit-latency question directly.
- A benchmark competes with production I/O. Run it before the volume goes live.

## Tail latency from the platform

When medians are fine and p99 is bad, and the application profile is clean, check the layer below.

| Suspect | Evidence | Fix |
|---|---|---|
| CPU steal | `st` in `vmstat`/`mpstat` above a few percent during the slow periods | Move off burstable or shared-CPU types to dedicated vCPUs; on clouds where a stop and start reschedules the instance, that also moves it off a noisy host (a reboot does not) |
| Exhausted burst credits | Slowdown with a sharp start; credit balance at zero in provider metrics | Larger or non-burstable type; provisioned IOPS |
| Disk neighbor or volume limit | `await` rises while the host's own IOPS do not | Provisioned-IOPS class, or check the instance-level storage cap |
| Network allowance exceeded | Drops with no interface errors; provider counters in `ethtool -S <iface>` (on AWS, the `*_allowance_exceeded` counters) | Larger instance; fewer, longer-lived connections |
| cgroup CPU throttling | `nr_throttled` rising in the container's `cpu.stat` | See `container-internals.md` |
| Transparent huge pages | Latency spikes with `sy` time in compaction; common with databases and Redis; `cat /sys/kernel/mm/transparent_hugepage/enabled` shows `[always]` | Set `madvise` or `never`, whichever that database's documentation asks for (Redis warns at startup when it is `always`); persist it with a boot parameter or a unit |
| NUMA imbalance | Only on multi-socket sizes: `lscpu \| grep -i numa` shows more than one node, `numastat` shows one node exhausted | Instance size that fits one node, or `numactl --interleave=all` for the database |

NUMA does not apply to small instances with a single node; do not spend time on it there.

## Ask the user

- **What is the monthly budget for this host, and is a few minutes of downtime for a resize
  acceptable?** It decides between resizing now and tuning first. Default: resize one step up when
  memory or CPU is the proven bottleneck; it is cheaper than a day of tuning.
- **Which data on this machine cannot be recreated?** That decides the disk class, the snapshot
  schedule and what must never be on local NVMe. Default: treat the database and uploads as
  irreplaceable, everything else as rebuildable.
- **How long must logs be kept?** Retention sets disk size and may be a legal or contractual
  matter. Default: 14 days on the host, longer only in a log service (`0x:site-reliability`).
- **Is traffic steady or spiky, and what is the expected peak?** Burstable types suit spiky, low
  average load only. Default: non-burstable from Launch onward.
- **Who is paged when a disk is predicted full within 4 hours?** An alert nobody receives is no alert. Default: the
  founder's phone through the existing alerting channel.
