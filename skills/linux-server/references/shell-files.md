# Shell, files and permissions

Read this when: working in a shell on a server or in a repo: finding where something lives, fixing
"permission denied" or "command not found", building a pipeline to answer a question, writing a
script that must be safe to rerun, copying files between machines, or mounting and growing volumes.

## Where things live

| Looking for | Look here | Fast way to be sure |
|---|---|---|
| Config of a packaged service | `/etc/<name>/`, drop-ins in `/etc/<name>/conf.d/` or `*.d/` | `dpkg -L <pkg>` / `rpm -ql <pkg>` |
| systemd units | `/etc/systemd/system/` (yours, wins), `/usr/lib/systemd/system/` (packages) | `systemctl cat <unit>` shows file paths and drop-ins |
| Logs | journal first; then `/var/log/<name>/` | `journalctl -u <unit>`; `sudo lsof -p <pid> \| grep -i log` |
| Auth log | journal (`journalctl -u ssh`), `/var/log/auth.log` (Debian family with rsyslog), `/var/log/secure` (RHEL family) | |
| Service state and data | `/var/lib/<name>/` (Postgres, Docker, etc.) | never clean by hand |
| Your app | `/srv/<app>` or `/opt/<app>`; pick one per host and keep it | `systemctl show -p WorkingDirectory,ExecStart <unit>` |
| Admin-installed binaries | `/usr/local/bin` | `command -v <name>`; `type -a <name>` lists every match on PATH |
| Runtime sockets, pid files | `/run/` (tmpfs, gone at reboot) | |
| Scratch | `/tmp` (cleared at boot, may be RAM-backed), `/var/tmp` (survives reboot); `systemd-tmpfiles` also deletes old files in both on many distributions, so neither is storage | `systemd-tmpfiles --cat-config` |
| Live kernel and process state | `/proc/<pid>/`, `/sys/` | `/proc/<pid>/{cwd,exe,environ,limits,fd}` |

Which package owns a file: `dpkg -S /path` or `rpm -qf /path`. Which file a running process actually
opened beats guessing: `sudo ls -l /proc/<pid>/cwd /proc/<pid>/exe` and `sudo lsof -p <pid>`.

Search without crossing into other filesystems or pseudo-filesystems: `sudo find / -xdev -name 'x*'`.
Search config text: `sudo grep -rIn 'listen' /etc/nginx/`.

Edit packaged config through drop-in files (`*.d/` directories, `systemctl edit`) rather than the
shipped file: package upgrades then never prompt about or overwrite the change.

## Permission denied: diagnose before changing anything

Run these three first. They find the cause in most cases, and the cause is usually a parent
directory, not the file.

```bash
namei -l /srv/app/shared/uploads/a.png   # owner and mode of every path component
id appuser                               # uid, groups as configured
sudo -u appuser test -r /srv/app/.env && echo readable   # reproduce as the service user
```

| Symptom | Cause | Fix |
|---|---|---|
| File mode looks right, still denied | A parent directory lacks `x` for that user | Add `x` on the directory for the group, not `chmod -R 777` |
| Cannot delete or rename a file you own | Deleting needs `w`+`x` on the directory, not on the file | Fix the directory mode or owner |
| User was added to a group, still denied | Group membership is read at login | New login session; restart the service |
| `sudo echo x > /etc/file` denied | The redirect runs in the caller's shell | `echo x \| sudo tee /etc/file >/dev/null` |
| Script has `x`, "permission denied" on run | Filesystem mounted `noexec`, or bad interpreter line | `findmnt -T /path`; check the shebang and CRLF line endings |
| Root is denied | Immutable attribute, read-only mount, SELinux/AppArmor, NFS root squash | `lsattr`, `findmnt -T`, `sudo ausearch -m avc -ts recent`, `sudo journalctl -k \| grep -i denied` |
| Works in a shell, denied under systemd | Unit sandboxing (`ProtectSystem`, `ReadOnlyPaths`, `PrivateTmp`) or a different user | `systemctl cat <unit>`; add `ReadWritePaths=` |
| Bind to port 80/443 denied | Ports below 1024 need a capability | `AmbientCapabilities=CAP_NET_BIND_SERVICE` in the unit, or proxy from a high port |
| `ls -l` shows a trailing `+` | An ACL is in effect | `getfacl <path>` |

Modes to use: files `644`, directories `755`, secrets and env files `600` (or `640 root:<appgroup>`),
`~/.ssh` `700` and `authorized_keys` `600`. For a directory several users write to, set the group
and the setgid bit so new files inherit it: `chgrp -R app /srv/app/shared && chmod 2775 /srv/app/shared`.

Do not use `chmod -R 777` or `chown -R` on a broad path to make an error go away. It makes secrets
world-readable, makes code writable by the process that serves it (a file-write bug becomes code
execution), breaks sshd (which refuses keys in group-writable homes) and cannot be undone because
the previous modes are lost. Change the one component `namei` showed to be wrong.

Run each service as its own system user with no login shell
(`useradd --system --home /srv/app --shell /usr/sbin/nologin app`). Code is owned by a deploy user
or root and only readable by the service user; the service user owns only the directories it must
write (uploads, cache).

### sudo rules

```bash
sudo visudo -f /etc/sudoers.d/deploy     # validates syntax before saving
# deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart myapp.service, /usr/bin/systemctl status myapp.service
sudo visudo -c && sudo -l -U deploy      # check all files; list what deploy may run
```

- A syntax error in sudoers locks everyone out of sudo. Edit only through `visudo`, and keep a root
  shell open in another session until `sudo -v` works in a new one.
- Files in `/etc/sudoers.d/` whose name contains a dot or ends in `~` are silently ignored.
- Grant exact command lines with absolute paths. A rule that allows an editor, an interpreter, a
  pager, `tee`, `find`, `tar`, `docker` or a script the user can modify is a rule that grants root.
- `sudo` resets the environment and uses its own `secure_path`. "Works as me, command not found
  with sudo" means the binary is in a user-local directory; use the absolute path.
- On Ubuntu 26.04 and later, `sudo` is sudo-rs, which implements a subset of the sudoers language.
  A rule copied from older documentation may not match the same way: confirm each rule with
  `sudo -l -U <user>` and one real run as that user (`man sudoers-rs` lists what is supported).

## Pipelines that answer a question

Build one stage at a time with `| head` on the end; add the next stage when the output looks right.

```bash
# Top client IPs, then status codes per minute, from a combined-format access log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -20
awk '{print substr($4,2,17), $9}' access.log | sort | uniq -c | tail -30

# Sum and p95 of the last field (for example request time)
awk '{s+=$NF} END {print s, s/NR}' access.log
awk '{print $NF}' access.log | sort -n | awk '{a[NR]=$1} END {print a[int(NR*0.95)]}'

# JSON-lines logs: tolerate non-JSON lines, filter, output TSV
jq -R 'fromjson? | select(.level=="error") | [.time,.msg] | @tsv' -r app.log

# Files safely into a command, in parallel
find . -name '*.png' -print0 | xargs -0 -r -n 50 -P 4 optipng -quiet
```

- `uniq` only merges adjacent lines: always `sort` first.
- `LC_ALL=C sort` and `LC_ALL=C grep` are several times faster on large files and sort by bytes.
- `grep -F` for literal strings (no regex surprises from dots and brackets); `-o` to extract;
  `-c` to count; `--line-buffered` when filtering `tail -f` into another pipe.
- Rotated logs: `zgrep`, `zcat -f` (reads compressed and plain alike).
- `xargs` without `-0` splits on spaces and quotes in file names; without `-r` GNU xargs runs the
  command once on empty input.
- Do not parse `ls`. Use globs, or `find ... -print0`.
- `sed -i` is GNU syntax; macOS needs `sed -i ''`. In scripts that run on both, write to a temp file.
- A pipeline's exit status is the last command's unless `set -o pipefail` is on.
- `jq -e` sets the exit code from the result, which makes it usable in `if`.

## Bash scripts that fail safely

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >&2; }

: "${DEPLOY_ENV:?set DEPLOY_ENV to staging or production}"
```

Quoting rules that prevent nearly every shell bug:

- Quote every expansion: `"$var"`, `"$(cmd)"`, `"$@"`. Unquoted, values are split on whitespace and
  glob-expanded.
- Build command lines as arrays, not strings: `args=(--exclude '*.log' -a); rsync "${args[@]}" src/ dst/`.
- `rm -rf "${dir:?}/"*` aborts if `dir` is empty instead of expanding to `/*`.
- Put `--` before operands that may start with a dash: `rm -- "$file"`.
- Read lines with `while IFS= read -r line; do ...; done < file`. Never `for x in $(cat file)`.
- Use `[[ ... ]]` for tests in Bash; `printf` rather than `echo` for data that may start with `-`.

Where `set -e` does not do what people assume:

| Case | What happens | Do instead |
|---|---|---|
| `local x="$(cmd)"` or `export x="$(cmd)"` | The exit status is `local`'s, always 0 | Declare first, assign on its own line |
| A function called in `if f; then` or `f \|\| true` | `-e` is off for the whole body of `f` | Do not rely on `-e` inside such functions; check explicitly |
| `cmd \| while read ...; do var=...; done` | The loop runs in a subshell; `var` is lost | `while ...; done < <(cmd)` |
| `((count++))` when count is 0 | Returns status 1 and exits the script | `count=$((count + 1))` |
| `grep` finding nothing | Exit 1 kills the script | `grep ... \|\| true` when no match is acceptable |

Run `shellcheck` on every script and in CI; it catches the quoting and `set -e` traps above. Do not
pass secrets as command arguments: they are visible to every user in `ps`. Pass them by environment
or file.

## Environment, PATH and profiles

"Works in my terminal, command not found in cron, systemd, CI or `ssh host cmd`" is one bug: those
contexts do not read the files that set up PATH in an interactive shell.

| Context | What Bash reads | Typical PATH |
|---|---|---|
| Interactive login (ssh session) | `/etc/profile`, then the first of `~/.bash_profile`, `~/.bash_login`, `~/.profile` | full |
| Interactive non-login (new terminal tab) | `~/.bashrc` | full |
| `ssh host 'cmd'` | `~/.bashrc`, which on most distros returns at once when not interactive | system dirs only |
| cron | nothing | `/usr/bin:/bin` |
| systemd service | nothing; no shell is involved | systemd's built-in default |
| `sudo cmd` | nothing; environment reset | `secure_path` from sudoers |

Rules:

- In units, crontabs and scripts, use absolute paths or set `PATH` explicitly at the top. Do not
  source a profile to get a version manager's shims.
- Give a service its environment in the unit: `Environment=NODE_ENV=production` and
  `EnvironmentFile=/etc/myapp/env` (mode `600`, owned by root; systemd reads it before dropping
  privileges). That file is not shell: plain `KEY=value` lines, no `export`, no `$OTHER` expansion.
- A variable set without `export` is invisible to child processes.
- See what a running process really has: `sudo cat /proc/<pid>/environ | tr '\0' '\n'`.
- Reproduce a bare environment before blaming cron:
  `env -i HOME="$HOME" PATH=/usr/bin:/bin bash --noprofile --norc ./job.sh`.
- After installing a binary that shadows another, `hash -r` clears Bash's cached lookup.

## Idempotent scripts

Write each step so it describes the end state, and so a second run changes nothing and exits 0. A
setup script that fails halfway is then fixed by running it again.

| Fails or duplicates on rerun | Converges |
|---|---|
| `mkdir dir` | `mkdir -p dir` |
| `ln -s target link` | `ln -sfn target link` |
| `useradd app` | `id -u app >/dev/null 2>&1 \|\| useradd --system app` |
| `echo 'line' >> file` | `grep -qxF 'line' file \|\| echo 'line' >> file`; better, own a whole file in a `*.d/` directory |
| `cp conf /etc/x.conf` then always restart | `cmp -s conf /etc/x.conf \|\| { install -m 644 conf /etc/x.conf; systemctl reload x; }` |
| `curl -o /usr/local/bin/tool URL` | download to a temp file, verify the checksum, `install -m 755`, skip if the version already matches |
| `systemctl start x` | `systemctl enable --now x` |
| write a file in place | write `file.tmp` in the same directory, then `mv file.tmp file` (atomic rename) |

`apt-get install -y` and `dnf install -y` are already idempotent; set
`DEBIAN_FRONTEND=noninteractive` so a config prompt cannot hang an unattended run. Restart services
only when their config changed: an unconditional restart turns every rerun into an outage.

## Copying and syncing files

```bash
rsync -a --delete -n -v ./build/ deploy@host:/srv/app/releases/new/   # -n: dry run, read the output
rsync -a --delete ./build/ deploy@host:/srv/app/releases/new/
```

- Trailing slash on the source means "the contents of"; without it, the directory itself is
  created inside the destination. With `--delete`, getting this wrong deletes the wrong tree, which
  is why the dry run comes first.
- `-a` keeps modes, times and symlinks. Ownership is kept only when the receiving side runs as
  root; otherwise files belong to the login user, and `--chown=app:app` is silently not applied.
  Simplest: sync as the deploy user into a directory it owns and give the service user read
  access through the group. Setting owners needs root on the receiver
  (`--rsync-path='sudo rsync' --chown=app:app`), and a sudo rule for `rsync` is a rule that
  grants root, because rsync can overwrite any file.
- Add `-H -A -X` for hard links, ACLs and extended attributes (full-system or backup copies), and
  `--numeric-ids` when user names differ between machines.
- `-z` helps over a slow link and hurts on a fast one; `--partial` resumes large files.
- `scp` is fine for one file; `-p` keeps mode and times. For trees use rsync: it resumes, deletes
  and does not follow symlinks into a copy of their targets.
- Switch a release atomically: `ln -sfn releases/new current.tmp && mv -Tf current.tmp current`
  (GNU `mv`; the rename replaces the link in one step, so there is no moment without `current`).
- Do not rsync the data directory of a running database: the copy is inconsistent. Use the
  database's dump or backup tool (`0x:postgres-database`).

## When the script should become a program

Keep Bash for sequencing commands, moving files and wiring environment. Rewrite in the project's
language (TypeScript run with the project's runner, or Python with the standard library) when any
of these is true:

- It manipulates structured data beyond one `jq` expression, or does arithmetic that is not integer.
- It calls an HTTP API with auth, pagination or retries.
- It needs unit tests, or a failure in the middle needs cleanup logic more complex than one `trap`.
- It has passed roughly 100 lines, or has functions that return data through global variables.
- It must run on both macOS and Linux (BSD versus GNU tool flags) or on Windows.
- It runs steps concurrently and must collect their failures.

## Volumes and filesystems

Look before touching: `lsblk -f` (devices, filesystem type, UUID, mount point), `df -hT`, `findmnt`.

Attach a new volume:

```bash
lsblk -f                          # the new device must show an empty FSTYPE
sudo mkfs.ext4 /dev/nvme1n1       # destroys whatever is on it; confirm the device twice
sudo mkdir -p /mnt/data
echo 'UUID=<from blkid> /mnt/data ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
sudo findmnt --verify && sudo systemctl daemon-reload && sudo mount -a && findmnt /mnt/data
```

- Mount by `UUID=`, not `/dev/sdb` or `/dev/nvme1n1`: device names can change between boots.
- `nofail` on every non-root volume. Without it, a missing or slow volume drops the boot into
  emergency mode and the host is unreachable over SSH.
- Always run `findmnt --verify` and `mount -a` after editing fstab and before the next reboot.
  systemd turns fstab into mount units, so run `systemctl daemon-reload` after each edit too, or
  the boot uses the old view.
- Mounting over a non-empty directory hides its contents; they come back when unmounted. The
  reverse trap is worse: if the mount is missing, the service writes into the empty directory on
  the root disk. Add `RequiresMountsFor=/mnt/data` to the unit so it refuses to start instead.

Grow a filesystem (online, no unmount, for ext4 and XFS):

```bash
# 1. Snapshot the volume. 2. Enlarge it in the provider console or API. Then:
sudo growpart /dev/nvme0n1 1            # only if the filesystem sits on a partition
sudo resize2fs /dev/nvme0n1p1           # ext4: takes the device
sudo xfs_growfs /mnt/data               # XFS: takes the mount point
sudo pvresize /dev/nvme0n1p1            # LVM: first let the volume group see the larger disk
sudo lvextend -r -l +100%FREE /dev/vg0/data   # then grow the volume and filesystem together
```

- Shrinking: XFS cannot shrink; ext4 shrinks only unmounted; cloud volumes generally cannot be
  made smaller. To go smaller, create a new volume and copy.
- Never run `fsck` or `xfs_repair` on a mounted filesystem: it corrupts it. For the root
  filesystem, check from a rescue boot or let the boot-time check do it.
- Move a data directory to a new volume in this order: stop the service, `rsync -aHAX old/ new/`,
  mount the new volume at the original path, start, verify, and only then delete the old copy.
- `df -i` shows inode use. A filesystem with free space and no free inodes reports "No space left
  on device"; the cause is millions of small files (sessions, cache entries).

## Ask the user

- **Which user should own and run the app?** It decides every mode and sudo rule. Default: a
  dedicated system user per service with no shell, plus a separate human or deploy user with sudo.
- **May the deploy user restart services without a password?** Needed for unattended deploys, and
  it is a standing privilege. Default: yes, limited to exact `systemctl` commands for that one unit.
- **Is the data on this volume backed up, and when was the last snapshot?** Any resize, `mkfs` or
  move is unrecoverable without one. Default: assume no backup and take a snapshot first.
- **Does this script run only on the server, or also on laptops and CI?** That decides Bash versus
  a real program and whether GNU-only flags are acceptable. Default: assume Linux plus macOS, and
  avoid GNU-only flags or move the logic out of the shell.
- **Is brief downtime acceptable for a disk move or resize?** Growing is online; moving data to a
  new volume is not. Default: schedule moves for a low-traffic window and announce them.
