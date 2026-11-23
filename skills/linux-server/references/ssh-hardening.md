# SSH access and host hardening

Read this when: a host is about to be reachable from the internet, someone needs shell access
granted or removed, SSH login fails or behaves oddly, a private service must be reached from a
laptop, or access for several people needs to be managed properly.

## Keys, client config, agent and jump hosts

- One key per person per device, generated on that device, with a passphrase:
  `ssh-keygen -t ed25519 -a 100 -C 'name@device'`. Never copy a private key between machines and
  never share one between people. Revoking access is then deleting one line, and the log shows
  who logged in.
- A hardware-backed key (`ssh-keygen -t ed25519-sk`, needs a FIDO2 security key) cannot be copied
  off a compromised laptop. Use it for production access when the user has the hardware.
- Automation gets its own key per purpose, restricted on the server in `authorized_keys`:
  `restrict,command="/usr/local/bin/deploy.sh" ssh-ed25519 AAAA... ci-deploy`. `restrict` turns
  off forwarding and terminals; `command=` pins what the key can run.

```text
# ~/.ssh/config
Host *
    IdentitiesOnly yes
    ServerAliveInterval 60
    AddKeysToAgent yes

Host prod
    HostName 203.0.113.10
    User admin
    IdentityFile ~/.ssh/id_ed25519

Host db-internal
    HostName 10.0.1.5
    User admin
    ProxyJump prod
```

| Symptom | Cause | Fix |
|---|---|---|
| "Too many authentication failures" before the right key is tried | The agent offers every key it holds; the server stops after `MaxAuthTries` | `IdentitiesOnly yes` plus `IdentityFile` per host |
| Key is right, still "Permission denied (publickey)" | Server-side modes: home directory or `~/.ssh` writable by group or others, wrong owner, or the user is not in `AllowUsers` | `chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys; chmod go-w ~`; read the server log |
| "REMOTE HOST IDENTIFICATION HAS CHANGED" | The host was rebuilt or the address reused; or someone is in the middle | If a rebuild explains it, `ssh-keygen -R <host>`. If nothing explains it, stop |
| Works interactively, automation hangs | A host-key prompt | `StrictHostKeyChecking accept-new`; never `no`, which accepts a changed key |
| Session freezes after idling | A NAT or load balancer dropped the idle connection | `ServerAliveInterval 60` |

Debug from both ends: `ssh -vvv host` shows which keys were offered; on the server
`sudo journalctl -u ssh -n 50` (the unit is `sshd` on the RHEL family) gives the reason, which
the client is never told.

Verify a new host's key fingerprint against the provider's console output on first connect
(`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the server), at least for production.

Agent forwarding (`ssh -A`, `ForwardAgent yes`): while connected, root on the remote host can use
the forwarded agent to log in anywhere the keys are accepted. Do not use it to hop between hosts;
`ProxyJump` (`ssh -J bastion target`) does the same job and the intermediate host never touches
the key. For `git pull` on a server use a read-only deploy key for that repository instead.

## First ten minutes on a fresh VPS

The order prevents lockout. Keep the original root session open until step 4 has been verified
from a second terminal.

```bash
# 1. As root (or the image's default user): create the admin user and give it the key
adduser --disabled-password --gecos '' admin
usermod -aG sudo admin                        # group is "wheel" on the RHEL family
install -d -m 700 -o admin -g admin /home/admin/.ssh
install -m 600 -o admin -g admin /root/.ssh/authorized_keys /home/admin/.ssh/authorized_keys
echo 'admin ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-admin
chmod 440 /etc/sudoers.d/90-admin && visudo -c

# 2. From a NEW terminal on the laptop: prove the new path works
ssh admin@<host> 'sudo -n true && echo ok'

# 3. Lock root's password, then harden sshd (next section) and reload it
passwd -l root

# 4. From another new terminal: confirm admin still gets in and root does not
ssh admin@<host> true; ssh -o BatchMode=yes root@<host> true   # second must fail
```

Then: firewall (below), automatic updates and the exposure audit (`packages-updates.md`), time
sync and UTC (`time-encoding.md`). Put all of it in the provisioning script rather than typing it.

- `passwd -l` locks the password only. Root can still log in with a key until sshd forbids it,
  and a locked password does not stop key logins for any user. To cut off a user, remove their
  keys or expire the account (`usermod --expiredate 1 <user>`).
- Passwordless sudo for the admin user is the normal choice when login is key-only: the key is
  the credential. If the user wants a second factor for root, give the admin account a strong
  password and drop `NOPASSWD`. Service and deploy users get narrow rules (`shell-files.md`).
- With root locked and passwords off, the provider's web console cannot log in either. Recovery
  is then the provider's rescue mode, which is acceptable; know where that button is before it
  is needed.

## Hardening sshd

```text
# /etc/ssh/sshd_config.d/00-hardening.conf
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AllowUsers admin deploy
MaxAuthTries 3
X11Forwarding no
AllowAgentForwarding no
```

```bash
sudo sshd -t && sudo systemctl reload ssh      # validate first; "sshd" on the RHEL family
sudo sshd -T | grep -Ei '^(permitrootlogin|passwordauthentication|kbdinteractive|allowusers)'
```

- sshd uses the first value it reads for each keyword. Drop-ins are read in name order, and cloud
  images often ship a file such as `50-cloud-init.conf` containing `PasswordAuthentication yes`.
  A hardening file that sorts after it is silently ignored. Name the file to sort first and
  trust only the `sshd -T` output, which prints the effective configuration.
- Confirm the main `sshd_config` has an `Include /etc/ssh/sshd_config.d/*.conf` line; without it
  the drop-in does nothing.
- Reload, not restart, and test from a new terminal before closing the current one. Existing
  sessions survive a reload, which is the safety net.
- `AllowUsers` is exclusive. Forgetting the deploy user locks CI out on the next deploy.
- Disable both `PasswordAuthentication` and `KbdInteractiveAuthentication`; with only the first
  off, PAM can still offer a password prompt.
- Leave ciphers, MACs and key-exchange lists at the defaults of a current OpenSSH. Lists pasted
  from old hardening guides remove newer algorithms and add nothing.
- Moving SSH off port 22 reduces log noise, not risk. Skip it by default. If done: open the new
  port in every firewall first, and note that on distributions where SSH is socket-activated the
  port is set on `ssh.socket`, not only in `sshd_config`.

## Firewall

Two layers, both default-deny for inbound traffic:

1. **The provider's firewall** (security group, cloud firewall). It sits outside the host, cannot
   be broken by a mistake on the host, and is the primary control. Manage it as code.
2. **A host firewall** as the second layer, and the only one on providers that offer none.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH            # before "enable", or the session is cut off
sudo ufw allow 80,443/tcp
sudo ufw enable
sudo ufw status verbose
```

- Restrict SSH to known sources when there is a fixed address or a VPN:
  `sudo ufw allow from 203.0.113.5 to any port 22 proto tcp`, then delete the open rule.
- HTTP/3 needs `443/udp` as well.
- firewalld equivalent: `sudo firewall-cmd --permanent --add-service=https && sudo firewall-cmd --reload`.
  Use one firewall manager per host; mixing ufw, firewalld and hand-written rules produces rule
  sets nobody can reason about.
- **Docker bypasses ufw.** A published port (`-p 5432:5432`) is forwarded by Docker's own NAT
  rules before the ufw input rules are consulted, so the port is public even though
  `ufw status` shows it denied. Publish to loopback (`-p 127.0.0.1:5432:5432`) for anything a
  local proxy or tunnel reaches, do not publish database ports at all, and rely on the provider
  firewall as the outer layer.
- IPv6 is a second front door. Check that the host firewall covers it (`IPV6=yes` in
  `/etc/default/ufw`) and that the provider firewall has matching IPv6 rules.
- Do not drop all ICMP. Path-MTU discovery depends on it; blocking it causes hangs on large
  responses that are hard to trace.
- Outbound filtering is worth its upkeep at Scale or under a compliance requirement, not before.
- Verify from outside with a port scan of the host's addresses (`packages-updates.md`).

## Tunnels and port forwarding

Tunnels let database and admin ports stay closed to the internet while remaining usable.

```bash
# Local forward: laptop port 5433 -> Postgres listening on the server's loopback
ssh -N -o ExitOnForwardFailure=yes -L 5433:127.0.0.1:5432 prod
psql -h 127.0.0.1 -p 5433 -U app appdb

# Through a bastion to a private host; the name is resolved on the bastion's side
ssh -N -L 5433:db.internal:5432 bastion

# Remote forward: server's loopback port 8080 -> dev server on the laptop
ssh -N -R 8080:127.0.0.1:3000 prod

# SOCKS proxy through the host, for a browser or curl --socks5-hostname
ssh -N -D 1080 prod
```

- In `-L local:host:port` the `host:port` is as seen from the SSH server, not from the laptop.
- `-N` opens no shell. `ExitOnForwardFailure=yes` makes a tunnel fail loudly when the local port
  is taken, instead of connecting without the forward and leaving the client talking to
  something else on that port.
- Forwards bind to loopback by default. Do not bind them to `0.0.0.0`; that shares a production
  database with the local network.
- A database client that verifies the TLS host name sees `127.0.0.1`, not the server's name; set
  the expected name in the client rather than disabling verification.
- Connect to production data through a tunnel with a read-only role unless the task is a write.
- A tunnel that must stay up permanently is infrastructure built from a debugging tool. Use a
  private network or a mesh VPN (WireGuard-based) for standing connections.

## Brute-force noise and reading the auth log

With key-only login, password guessing cannot succeed; what remains is log noise and a small
exposure to future SSH daemon bugs. In order of value:

1. Restrict port 22 to known source addresses or a VPN at the provider firewall. The noise stops.
2. Otherwise rate-limit: `sudo ufw limit OpenSSH`, or fail2ban.
3. Current OpenSSH releases also penalize sources that fail repeatedly on their own.

```ini
# /etc/fail2ban/jail.local   (then: systemctl restart fail2ban; fail2ban-client status sshd)
[sshd]
enabled = true
backend = systemd
maxretry = 5
findtime = 10m
bantime = 1h
```

`backend = systemd` matters on distributions that no longer write `/var/log/auth.log`: without it
fail2ban watches a file that does not exist and bans nobody. Unban a locked-out address with
`sudo fail2ban-client set sshd unbanip <ip>`.

Review logins when something feels off and on a schedule (monthly is a reasonable rule of thumb):

```bash
sudo journalctl -u ssh --since -7d | grep -E 'Accepted|Failed|Invalid user' | tail -50
last -a | head -20                     # recent sessions with source address
sudo journalctl _COMM=sudo --since -7d # what was run through sudo
ssh-keygen -lf ~/.ssh/authorized_keys  # fingerprints, to match "Accepted publickey ... SHA256:..."
```

Act on: `Accepted password` when passwords are meant to be off (the config is not in effect);
`Accepted publickey` from an address or at an hour nobody recognizes; a fingerprint not in the
list of issued keys; users, keys or sudoers files nobody added. Any of the last three is a
suspected compromise: `0x:web-security` for response, and replace the host.

A root-level intruder can edit local logs. From Launch, ship auth logs off the host
(`0x:site-reliability`).

Removing someone's access: delete their key from `authorized_keys` of every account on every
host (including shared accounts such as `deploy`), expire or delete their user, end live sessions
(`sudo pkill -KILL -u <user>`), and rotate any secret they could read. Keeping the list of keys
in the provisioning script is what makes this a one-line change.

## Short-lived certificates and identity-based access

Static keys in `authorized_keys` are fine for one to three people and a handful of hosts. Move on
when people join and leave, contractors need temporary access, hosts multiply, or a customer or
auditor asks who accessed production and when.

| Option | How it works | Fits |
|---|---|---|
| Cloud provider session access (session manager, identity-aware proxy, OS login) | Shell through the provider's API, authorized by its IAM with SSO and MFA; port 22 closed entirely; sessions logged | Default when already on a large cloud |
| Mesh VPN with SSH integration, or an access proxy | Identity from the company's SSO; hosts not reachable from the internet at all | Mixed providers, small teams |
| SSH certificate authority | Servers trust one CA key; users get certificates valid for hours | Many hosts, need for standard SSH tooling |

SSH CA mechanics:

```bash
# Sign a user's public key: identity for the log, allowed login name, 8-hour validity
ssh-keygen -s ca_user_key -I alice@laptop -n admin -V +8h id_ed25519.pub
# Server side, in sshd config:  TrustedUserCAKeys /etc/ssh/ca_user_key.pub
```

- Expiry replaces revocation: nothing to remove from hosts when someone leaves.
- The `-n` principal must match the login user (or an `AuthorizedPrincipalsFile` entry), or the
  certificate is rejected with an unhelpful error.
- Host certificates (`ssh-keygen -s ca_host_key -h ...`, `HostCertificate` in sshd, a
  `@cert-authority` line in `known_hosts`) remove first-connection prompts and host-key warnings
  after rebuilds.
- The CA private key opens every host. Hand-signing with a key on a laptop and week-long
  validity recreates the original problem. Use a tool that issues certificates after SSO login
  and keeps the CA key in a KMS or hardware module.
- Certificates depend on correct clocks; a skewed host rejects valid certificates.
- Keep one break-glass path that does not depend on the identity system: the provider's rescue
  console, or a static key stored offline. Test it.

## Ask the user

- **Who needs shell access to production, and from which devices?** Every key is a way in.
  Default: the founder only, one key per device, plus one restricted deploy key for CI.
- **Is there a fixed IP address or VPN from which SSH will always come?** If so, port 22 can be
  closed to everyone else. Default: none; leave 22 open with key-only login and rate limiting.
- **Is a second factor for root wanted (a sudo password or a hardware key)?** It costs friction
  on every session. Default: passwordless sudo with a passphrase-protected key; hardware key
  when the product holds sensitive customer data.
- **Do customers or a compliance program require an access audit trail?** That is the trigger
  for identity-based access. Default: not yet at Prototype; revisit at the first security
  questionnaire.
- **If the laptop is lost, how is access recovered?** Without a second key or the provider
  console, the answer is rescue mode. Default: a second key on a second device or hardware
  token, registered now.
