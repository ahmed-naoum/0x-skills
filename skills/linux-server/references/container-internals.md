# Virtualization and container internals

Read this when: a container is killed, throttled, will not stop cleanly, cannot reach another
container, fills the disk, or behaves differently from the same program on the host; or when
deciding how strongly to isolate code that is not trusted. Commands use Docker; the mechanisms are
the same under Podman, containerd and Kubernetes.

The model that makes the rest obvious: a container is an ordinary host process. Namespaces limit
what it sees (processes, network, mounts, users), cgroups limit what it may use (memory, CPU,
process count), capabilities and seccomp limit what it may ask the kernel, and its root
filesystem is an overlay of image layers plus one writable layer. There is no second kernel.
Every container process is visible in the host's `ps`, and every host tool can look inside.

## App, container or host

```bash
docker ps -a --no-trunc
docker inspect -f '{{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} restarts={{.RestartCount}} {{.State.Error}}' <c>
docker logs --tail 200 -t <c>
docker events --since 1h --until 0s
```

| Evidence | Layer | Next |
|---|---|---|
| Exit 1 or another small code, with an error in `docker logs` | App | Read the log; it is an application bug or bad config |
| Exit 137, `oom=true`, or a "Memory cgroup out of memory" kernel line | Container limit | cgroup section below |
| Exit 137 exactly ten seconds after a stop or deploy | Container: SIGTERM was not handled | PID 1 section below |
| Exit 126 or 127; "no such file or directory" for a file that exists | Image: entrypoint not executable, missing interpreter, CRLF line endings in a script, or a binary linked against a C library the image lacks | `docker run --rm -it --entrypoint sh <image>` |
| "exec format error" | Image built for another CPU architecture | Build for the host's architecture |
| Exit 125 | The engine could not start it: bad flag, port in use, missing volume | The error text; `journalctl -u docker` |
| Several unrelated containers fail at once | Host: disk full, memory exhausted, engine restarted | `df -h`, `free -m`, `journalctl -u docker`, kernel log |
| Same image and config works on another machine | Host or its environment | Compare limits, kernel, mounts, network |
| Works on the host, fails in the container | A difference in the list below | |

What differs inside a container, in the order it bites:

1. `localhost` is the container itself. A service on the host or in another container is not
   there. Use the service name on a shared network, or `host.docker.internal` (on Linux add
   `--add-host=host.docker.internal:host-gateway`) for the host, and make the target listen on an
   address the bridge can reach.
2. Environment: only variables passed explicitly exist.
3. User and file ownership: numeric user IDs are matched against bind-mounted files.
4. Filesystem: only what the image and mounts provide; possibly read-only.
5. Limits: memory and CPU ceilings the host process never had.
6. DNS and outbound network path.
7. The app is PID 1, with different signal behavior.
8. Time zone and locale are whatever the image has, usually UTC and `C`.

Do not start a crashed container with `--rm` while debugging: its logs and writable layer are the
evidence and `--rm` deletes them at exit.

## Looking inside from the host

```bash
docker top <c>                       # its processes, host view
docker stats --no-stream             # memory and CPU against limits
docker exec -it <c> sh               # only if the image has a shell
docker diff <c>                      # files added or changed since the image
docker cp <c>:/app/report.json .     # copy a file out, even from a stopped container

pid=$(docker inspect -f '{{.State.Pid}}' <c>)
sudo nsenter -t "$pid" -n ss -ltnp   # host's ss inside the container's network namespace
sudo nsenter -t "$pid" -n ip addr
sudo ls -la /proc/"$pid"/root/app    # the container's filesystem, through /proc
sudo cat /proc/"$pid"/environ | tr '\0' '\n'
cat /proc/"$pid"/cgroup              # which cgroup holds its limits
```

Minimal and distroless images have no shell, `ps` or `curl`. Do not add them to the production
image. Use `nsenter` with the host's tools as above, or attach a throwaway container to the
target's namespaces:

```bash
docker run --rm -it --pid=container:<c> --network=container:<c> busybox sh
```

For Kubernetes the equivalent is an ephemeral debug container (`0x:cloud-infrastructure`).

## OOM kills and CPU throttling from cgroup metrics

With cgroup v2 (`stat -fc %T /sys/fs/cgroup` prints `cgroup2fs`) the files are under
`/sys/fs/cgroup/` inside the container, and on the host under the path shown in
`/proc/<pid>/cgroup` (typically `/sys/fs/cgroup/system.slice/docker-<id>.scope/`).

| File | Read it for |
|---|---|
| `memory.max`, `memory.current` | The limit and current use, in bytes; `max` means unlimited |
| `memory.events` | `oom_kill` counts kills in this cgroup; `max` counts times the limit was hit |
| `memory.stat` | `anon` (heap, not reclaimable) versus `file` (page cache, reclaimable) and `shmem` |
| `cpu.max` | `<quota> <period>` in microseconds: `50000 100000` is half a CPU; `max` is unlimited |
| `cpu.stat` | `nr_periods`, `nr_throttled`, `throttled_usec` |
| `memory.pressure`, `cpu.pressure`, `io.pressure` | Stall time for this container alone |

Memory:

- The trustworthy evidence of a kill is `oom_kill` in `memory.events` and the kernel log line.
  Docker's `OOMKilled` flag can miss the case where a child process was killed and the main
  process survived, which shows up as a worker that keeps disappearing.
- A cgroup's memory includes its page cache, but cache is reclaimed before anything is killed.
  Judge from `anon` plus `shmem`, not from the total. Files written to a tmpfs mount or
  `/dev/shm` are `shmem`: they count against the limit and cannot be reclaimed.
- Telling a too-low limit from a leak, and setting the runtime's heap ceiling below the
  container limit: `processes-systemd.md`. Set the heap ceiling explicitly; do not rely on the
  runtime detecting the container limit.
- Set a memory limit on every container from Launch. Without one, a leaking container exhausts
  the host and the kernel chooses the victim, which may be the database.
- Setting `--memory-swap` equal to `--memory` gives the container no swap, so it is killed at the
  limit instead of thrashing the host's disk.

CPU:

- Throttling shows as latency spikes while average CPU looks low. The quota is enforced per
  period (100 ms by default): a process with eight busy threads and a one-CPU quota uses its
  whole allowance in about 12 ms and is frozen for the remaining 88. Compare `nr_throttled` with
  `nr_periods`; more than a few percent of periods throttled on a latency-sensitive service is
  worth fixing.
- Runtimes and libraries that size thread pools and worker counts from the CPU count may see the
  host's CPUs, not the quota. Set worker and pool counts explicitly to match the limit.
- Fixes, in order: match thread and worker counts to the quota; raise the quota; or remove the
  hard CPU limit and use relative weights so the container is only slowed when the host is
  contended. A memory limit must stay; a CPU limit is optional.

Flags: `--memory=512m --cpus=1.5 --pids-limit=256`; in Compose, `mem_limit`, `cpus`,
`pids_limit`.

## Least privilege at run time

```bash
docker run --user 10001:10001 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop=ALL --security-opt no-new-privileges:true \
  --memory=512m --pids-limit=256 <image>
```

Root inside a container is user 0 to the shared kernel (unless user namespaces are remapped).
Any kernel or runtime escape, and any host path mounted in, is then reached as host root. Each
flag removes one step an attacker needs.

| Problem after hardening | Cause | Fix |
|---|---|---|
| "Permission denied" writing to a volume | The volume or bind mount is owned by root | `chown` the host directory to the numeric ID; for named volumes create the directory with that owner in the image so a new volume inherits it |
| "Read-only file system" | The app writes to its own tree: caches, pid files, uploads | `docker diff <c>` on an unhardened run lists every path written; give each a tmpfs or volume |
| Cannot bind port 80 | Low ports are privileged | Listen on a high port and map it; only if that is impossible, `--cap-add=NET_BIND_SERVICE` |
| Orchestrator refuses "run as non-root" | `USER` is a name it cannot verify | Use a numeric user ID |

Never grant these to an application container, because each is equivalent to root on the host:
`--privileged`; a mount of `/var/run/docker.sock`; `--pid=host`; `--cap-add=SYS_ADMIN`; a bind
mount of `/` or `/etc`. For the same reason, membership of the `docker` group is root access:
treat a deploy user in that group as root when reasoning about sudo rules.

Writing the Dockerfile and Compose file that set these: `0x:cloud-infrastructure`.

## PID 1, signals and zombies

The kernel does not apply default signal actions to PID 1 of a PID namespace. A process that has
not installed a SIGTERM handler ignores SIGTERM when it is PID 1. `docker stop` sends SIGTERM,
waits (10 seconds by default), then sends SIGKILL. The result is deploys that take exactly ten
seconds per container, dropped in-flight requests and exit code 137.

| Cause | Fix |
|---|---|
| Shell-form `CMD node server.js`: `/bin/sh -c` is PID 1 and does not pass signals on | Exec form: `CMD ["node", "server.js"]` |
| `npm start` or another package-manager script as the command | Run the runtime binary directly; the wrapper sits between the signal and the app |
| An entrypoint script that starts the app as a child | End the script with `exec "$@"` so the app replaces the shell |
| The app has no SIGTERM handler | Add one: stop accepting, finish in-flight work, close pools, exit 0 |
| The app spawns subprocesses (headless browsers, shell-outs) and never reaps orphans | Run an init as PID 1: `docker run --init`, or `init: true` in Compose; it forwards signals and reaps zombies |
| Draining takes longer than the grace period | `docker stop -t 30`, `stop_grace_period: 30s` in Compose; keep it above the longest request |

Some servers want a different signal for a graceful stop; set it with `STOPSIGNAL` in the image.

Checks: `time docker stop <c>` returning in about ten seconds means the signal was not handled.
`docker top <c>` should show the app or the init as the first process, not `sh -c` or `npm`.
Processes in state `Z` that accumulate mean nothing is reaping; they eventually exhaust the
process limit.

## Disk used by images, containers and volumes

```bash
docker system df -v                 # images, containers, volumes, build cache
docker ps -a -s                     # writable-layer size per container
docker history --no-trunc <image>   # size of each layer and the instruction that made it
sudo du -sh /var/lib/docker/containers/*/*-json.log | sort -h | tail   # container logs
```

| Reclaim | Command | What is lost |
|---|---|---|
| Stopped containers | `docker container prune` | Their logs and writable layers |
| Build cache | `docker builder prune --filter until=168h` | Nothing; the next build is slower |
| Untagged images | `docker image prune` | Nothing in use |
| All images not used by a container | `docker image prune -a --filter until=168h` | The image a rollback would use, unless it is recent; the next deploy pulls again |
| A runaway container log | `sudo truncate -s 0 "$(docker inspect -f '{{.LogPath}}' <c>)"` | That log |
| Volumes | `docker volume prune` | **Data.** Read the list first |

- A volume counts as unused when no container references it, which includes the database's
  volume after its container was removed (for example by `docker compose down`). Do not run
  `docker system prune --volumes` or `docker volume prune -a` on a host that holds data without
  listing volumes (`docker volume ls`) and confirming each.
- Never delete files under `/var/lib/docker/overlay2` by hand. It corrupts the image store, and
  the usual recovery is wiping all images.
- The lasting fix for logs is a size cap in the engine config (`hardware-resources.md`).
- Files written inside the container layer are slow (copy-on-write) and vanish when the container
  is replaced. Anything that must persist or is written heavily goes to a volume.
- Schedule a weekly prune of old images and build cache with a timer, keeping at least the
  previous release for rollback.

## When a container is not enough isolation

Containers share the host kernel, so the boundary between a container and the host is the whole
system-call interface. That is adequate between services the team wrote and images it chose. It
is not a security boundary against code written to attack it.

| Workload | Isolation |
|---|---|
| Own services, trusted base images | Containers, hardened as above |
| CI jobs for pull requests from outside contributors | Ephemeral VM per job; hosted runners provide this |
| Customer-supplied code, plugins, user scripts, code generated by an LLM and then executed | MicroVM (Firecracker, Kata Containers), a user-space kernel (gVisor), or a sandbox with a much narrower interface (WebAssembly, V8 isolates) |
| Customers' own containers run as a product feature | MicroVM per tenant |

Default for a small team: do not build the sandbox. Run untrusted code on a platform that already
gives each execution its own microVM or isolate, in a separate cloud account or project from
production. Running microVMs oneself needs KVM, which most cloud VMs expose only on bare-metal
or nested-virtualization instance types.

Stronger isolation does not replace the rest. The untrusted code still needs: no credentials in
its environment, no route to the cloud metadata address (`169.254.169.254`) or the private
network, outbound access denied or allow-listed, hard CPU, memory, process and wall-clock limits,
and a filesystem discarded after each run. Missing network controls, not kernel escapes, are how
sandboxes usually leak.

## Container networking

How it is wired: each container has its own network namespace joined by a virtual Ethernet pair
to a bridge on the host (`docker0`, or `br-<id>` per user-defined network). Outbound traffic is
source-NATed to the host's address. A published port is a destination-NAT rule from the host
port to the container's address. On user-defined networks (Compose creates one per project) an
embedded DNS server at `127.0.0.11` resolves container and service names; on the default bridge
there is no name resolution.

Trace "A cannot reach B" in this order:

```bash
docker network inspect <net> -f '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'  # 1. same network?
docker exec <a> getent hosts <b>                         # 2. does the name resolve?
sudo nsenter -t "$(docker inspect -f '{{.State.Pid}}' <b>)" -n ss -ltnp   # 3. is B listening, and on which address?
docker port <b>                                          # 4. host-side mappings, for host-to-container
sudo nsenter -t "$(docker inspect -f '{{.State.Pid}}' <a>)" -n tcpdump -ni eth0 port 5432   # 5. do packets leave A?
```

| Finding | Cause |
|---|---|
| B listens on `127.0.0.1` inside its namespace | The app or dev server binds loopback; it must bind `0.0.0.0` in a container |
| A uses the published host port (`b:15432`) | Between containers use the container port (`b:5432`); published ports exist only on the host |
| Name does not resolve | Different networks, or the default bridge |
| Internal host names fail only in containers | The host uses a local stub resolver, which containers cannot reach, so the engine substitutes other DNS servers; set `dns` in the engine config |
| Small requests work, large responses or TLS handshakes hang | MTU of the bridge exceeds the MTU of the underlying network (VPN, overlay, some clouds); set `mtu` in the engine config |
| Traffic to a VPC, VPN or office range disappears | A Docker network was assigned an overlapping subnet; set `default-address-pools` in the engine config |
| All containers lose networking after a firewall reload | The reload flushed Docker's rules; restart the engine |
| Intermittent connection failures on a busy host | The connection-tracking table used by NAT is full (`processes-systemd.md`) |

Published ports listen on all host addresses and are not filtered by ufw (`ssh-hardening.md`).
`--network host` removes the network namespace altogether: no port mapping, no isolation, and
port conflicts with the host.

## Ask the user

- **How much memory may each container use?** The limit decides which service dies under
  pressure. Default: a limit on every container, sized from observed peak plus about 25%, with
  the database given the most protection.
- **How long can a request or job legitimately run?** It sets the stop grace period and
  therefore deploy time. Default: 30 seconds for web containers.
- **Does the product ever execute code that the team did not write (user scripts, plugins,
  model-generated code)?** If yes, containers are not sufficient isolation. Default: assume no;
  if yes, use a platform sandbox in a separate account.
- **Which volumes hold data that must survive?** Pruning and host replacement depend on the
  answer. Default: treat every named volume as data until confirmed otherwise.
- **Is it acceptable for a rollback to pull the previous image from the registry?** If rollback
  must be instant, image pruning must keep the previous release locally. Default: keep the last
  two releases on the host.
