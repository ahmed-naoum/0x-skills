# Cloud networking

Read this when: designing or debugging private networking in a cloud account: VPCs, subnets, firewall rules, NAT and egress, private access to a database or admin tool, peering and private links. AWS terms are used; GCP and Azure equivalents are noted where the model differs.

## The target shape

One sentence describes a correct small-product network: **one public entry point (a load balancer or gateway), application instances with no public inbound, a database reachable only from the application's security group, and humans reaching private things through an identity-checked tunnel.** Everything below is how to get there and how to debug it.

On a PaaS at Prototype, the equivalent is three checks, and no VPC work: the database does not accept connections from `0.0.0.0/0` (use the platform's private network, or an IP allowlist plus TLS plus a strong credential when private networking is unavailable); admin panels and dashboards are behind authentication; no service port other than 80/443 is published.

## Keeping databases and admin surfaces private

| Surface | Rule | Check |
|---|---|---|
| Postgres, Redis, search, queues | No public IP, or public access disabled; inbound only from the application's security group | From a laptop off the VPN: `nc -vz -w 5 <db-host> 5432` must time out |
| Redis and search engines especially | Never public: many deployments have no authentication by default and are scanned for constantly | Same check on 6379, 9200 |
| Admin panel, internal dashboards, metrics UIs, queue UIs, database GUIs | Behind an identity-aware proxy or VPN, with application authentication as well | Request from an unauthenticated browser returns the identity provider's login, not the tool |
| SSH (22), RDP (3389) | Not open to `0.0.0.0/0`. Prefer no inbound at all (session manager or tunnel) | List security groups for rules with source `0.0.0.0/0` or `::/0` on any port other than 80/443 |
| Cloud metadata endpoint | Require the token-based version (IMDSv2 on AWS) with hop limit 1 for non-container hosts | Instance metadata options show tokens required |
| Managed services with "allow all cloud services" style toggles | Off; it means every customer of that cloud | Review the database firewall settings |

```bash
aws ec2 describe-security-groups \
  --filters Name=ip-permission.cidr,Values=0.0.0.0/0 \
  --query 'SecurityGroups[].[GroupId,GroupName]' --output table
# Repeat with Name=ip-permission.ipv6-cidr,Values=::/0 and in every region in use, then read each
# listed group's rules: only 80/443 on the load balancer's group may be open to the world.
```

"Private" is necessary and not sufficient: keep TLS and credentials on private connections too. Admin-panel hardening itself is in `0x:web-security`.

## VPC design

Decide the address plan once; it is painful to change.

- **Do not use the default VPC for production.** Its subnets are all public and auto-assign public IPs.
- **CIDR:** a `/16` per VPC from `10.0.0.0/8`, a different one per environment and region (`10.10.0.0/16` production, `10.20.0.0/16` staging).
  Non-overlapping ranges are what make later peering, VPN and private-link options possible. Avoid ranges likely to collide: `10.0.0.0/16` and
  `172.31.0.0/16` (cloud defaults), `172.17.0.0/16` (Docker's default bridge), `192.168.0.0/16` (home and office networks, which matters the day a VPN
  is added).
- **Subnets:** three tiers across two or three availability zones.

| Tier | Route to internet | Holds | Size |
|---|---|---|---|
| Public | Internet gateway | Load balancer, NAT gateway. Nothing else | `/24` each |
| Private (application) | Outbound only, through NAT | Containers, functions in the VPC, workers | `/20` each; generous, because every task, pod and function interface takes an address |
| Isolated (data) | None | Database, cache | `/24` each |

  The provider reserves a few addresses in every subnet (five on AWS). Kubernetes with a VPC-native network plugin consumes one address per pod and exhausts small subnets quickly. Two zones are the minimum managed databases and load balancers accept; three cost more NAT and cross-zone traffic and are a Scale choice.
- **Security groups are the main control.** They are stateful (return traffic is automatic) and allow-only. Reference other security groups as the source, not CIDR ranges: `db-sg` allows 5432 from `app-sg`; `app-sg` allows the app port from `lb-sg`; `lb-sg` allows 443 from the internet. One group per role, not per instance.
- **Network ACLs:** leave at the default allow-all unless a compliance rule demands them. They are stateless, so a deny on ephemeral ports (1024 to 65535) breaks return traffic in ways that are slow to diagnose.
- **GCP differences:** a VPC is global and subnets are regional; firewall rules attach to the network and target instances by tag or service account. Use service-account-based rules as the equivalent of security-group references. Azure uses network security groups on subnets or interfaces, with application security groups as the reference mechanism.

### NAT and private endpoints

A NAT gateway is the usual first surprise on a small bill: it has an hourly charge per gateway whether used or not, plus a per-GB processing charge on every byte in both directions, on top of normal egress. Image pulls, object-storage traffic and log shipping through NAT are the typical volume.

| Situation | Choice |
|---|---|
| Production, availability matters | One NAT gateway per zone; a single one is a cross-zone dependency and adds cross-zone transfer fees. AWS's regional NAT gateway mode does the per-zone placement as one resource and is still billed per zone it is active in |
| Staging, dev, cost-sensitive Launch | One NAT gateway total, or a small NAT instance |
| Tasks need outbound only and nothing more | Public subnet, public IP on the task, security group with **no inbound rules** except from the load balancer. Simpler and cheaper than NAT; acceptable when a policy does not forbid public IPs. Note that public IPv4 addresses are themselves billed hourly on AWS |
| Heavy traffic to object storage or the provider's key-value store | Gateway endpoints (free on AWS for S3 and DynamoDB): add them in every VPC |
| Heavy traffic to registry, logs, secrets or other provider APIs | Interface endpoints: each has an hourly charge per zone plus per-GB, cheaper per GB than NAT. Add only where the volume justifies the fixed fee |
| Functions that only call the database | Put them in the VPC with no NAT; they then cannot reach the internet or provider APIs without endpoints |

## Reaching private resources as a human

Order of preference:

1. **The cloud's session service: no inbound port, access tied to IAM, sessions logged.** AWS Systems Manager Session Manager, GCP Identity-Aware Proxy TCP forwarding, Azure Bastion.

```bash
# Postgres on a private host, through any SSM-managed instance in the VPC that can reach it.
# Needs the Session Manager plugin on the laptop; afterwards the database answers on localhost:5432.
aws ssm start-session --target <instance-id> \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{"host":["<db-endpoint>"],"portNumber":["5432"],"localPortNumber":["5432"]}'

# GCP: SSH with no public IP on the VM
gcloud compute ssh <vm> --tunnel-through-iap
```

Keep certificate verification on through a tunnel: with libpq clients, `host=<db-endpoint> hostaddr=127.0.0.1` connects to the local port and still checks the certificate against the real name. Do not lower `sslmode` to make the tunnel work.

2. **A mesh VPN with identity** (Tailscale or similar, WireGuard underneath): one small node in the VPC advertises the subnets; access rules are per user and tied to SSO. Good default for a small team that also needs staging sites and internal tools.
3. **An identity-aware proxy for web tools** (Cloudflare Access, the cloud's IAP, an OAuth proxy on the load balancer): puts single sign-on in front of an admin panel or dashboard without a VPN client.
4. **A classic SSH bastion**: only when the above are unavailable. If used: a dedicated minimal host, key or certificate auth only, source restricted to known IPs, no agent forwarding (use `ssh -J`), patched automatically, logs shipped off the box.

Rules for all of them: per-person identity (no shared key), access revocable in one place, production database access logged and read-only by default, and no long-lived tunnel left running from a developer laptop.

## One public entry point

All inbound traffic enters through one load balancer or gateway; instances and tasks have no public inbound path.

- Route many services through one load balancer with host- and path-based rules. Each additional load balancer is a fixed monthly fee and another certificate and firewall surface.
- The application security group allows the app port **only from the load balancer's security group**. Test: `curl` to an instance's own address from outside must time out.
- If a CDN or WAF fronts the load balancer, lock the origin to it, or attackers bypass the protection by hitting the origin directly: restrict the load balancer's security group to the CDN's published ranges or managed prefix list, and additionally verify a secret header or mutual TLS from the CDN.
- Health checks come from the load balancer; the app's security group must allow them, and the health path must not redirect to HTTPS or require auth. A healthy app marked unhealthy is this, most of the time.
- Terminate TLS at the load balancer with a managed certificate. Listener rules, timeouts, connection draining and proxy headers are covered in `0x:web-networking` `proxies-load-balancers.md`.

## Debugging a blocked connection

Read the symptom first; it halves the search.

| Symptom | Meaning | Look at |
|---|---|---|
| Hangs, then times out | Packets dropped silently | Security group, network ACL, route table, or the target has no path back |
| `Connection refused` immediately | Reached a host; nothing listening on that port, or a host firewall rejected it | Process bound to `127.0.0.1` instead of `0.0.0.0`, wrong port, service down |
| Name does not resolve, or resolves to a private address from outside | DNS | Private hosted zone not associated with the VPC; resolving a private endpoint from a laptop |
| TLS or authentication error | Network is fine | Certificate name, credentials, database host-based auth |
| Works from one subnet or zone, not another | Per-subnet route table or ACL difference | Compare route tables |

Walk the path in order, source to destination and back:

1. **DNS:** `dig +short <host>` from the source. Is it the address expected (private inside the VPC)?
2. **Reachability:** `nc -vz -w 5 <host> <port>` from the actual source (exec into the container or task; a laptop proves nothing about the VPC).
3. **Source egress:** does the source's security group allow outbound to that port (default yes, often tightened)? Is there a route: local for in-VPC, NAT for internet, peering or gateway entry for another network?
4. **Destination ingress:** does the destination's security group allow that port from the source's security group or CIDR? Referencing a security group does not work across VPCs unless peered in the same region; across other boundaries use CIDRs.
5. **Return path:** security groups are stateful, ACLs are not. For peering, VPN and transit, the **other side's route table** needs a route back; a one-way route produces a timeout.
6. **ACLs**, only if they were ever changed from default.
7. **Host level:** is the process listening on the right interface (`ss -ltnp`), and is a host firewall in the way?

Tools that answer without guessing: the provider's path analyzer (AWS Reachability Analyzer, GCP Connectivity Tests, Azure Network Watcher) names the blocking component; VPC flow logs show `REJECT` records for security-group and ACL drops (no record at all means the packet never arrived: routing or DNS).

Recurring causes: a function or task placed in the wrong subnets; a function in a VPC without NAT trying to reach a public API; the database's
security group still referencing a deleted or old application group; a managed database set to public resolving differently inside and outside;
overlapping CIDRs between peered networks; MTU problems over VPN showing as small requests working and large ones hanging. General tooling is in
`0x:web-networking` `network-debugging.md`.

## Egress: static IPs and allowlists

Two different needs:

**A partner must allowlist the product's outbound IP** (payment processor, bank API, enterprise customer's firewall, a managed database's IP
allowlist). Give outbound traffic stable addresses: a NAT gateway with reserved static IPs (one per zone; give the partner all of them), or on GCP
Cloud NAT with reserved addresses. On a PaaS, static outbound IPs are a paid feature, shared across customers on some platforms (which weakens the
allowlist to "anyone on this platform"), or unavailable; the fallback is a small fixed-IP forward proxy that only the app can use. Functions need to
be attached to the VPC to egress through the NAT. Record the addresses in IaC so they are never released by accident: a released address cannot be
recovered and every partner must be updated.

**The product must restrict where its own workloads can connect** (containing a compromised dependency or SSRF). Security groups filter by IP, not by
domain, and SaaS APIs change IPs, so domain allowlists need a filtering layer: the cloud's network firewall with domain rules, an explicit forward
proxy with an allowlist, or FQDN policies in a Kubernetes network plugin that supports them. This is a Scale or compliance-driven control. The cheap
parts apply from Launch: block the metadata endpoint from application code paths that fetch user-supplied URLs (SSRF defenses are in
`0x:web-security`), deny outbound from the data tier entirely, and remove outbound-anywhere from workloads that only talk to the database.

## Private connections between networks and services

| Mechanism | Use when | Constraints |
|---|---|---|
| VPC peering | Two networks of the same owner, or one trusted partner, need broad connectivity | CIDRs must not overlap. Not transitive: A-B and B-C do not connect A to C. Routes and security groups are needed on both sides |
| Transit gateway or hub network | More than three or four networks | Hourly and per-GB fees; a Scale tool |
| Private link (AWS PrivateLink, GCP Private Service Connect, Azure Private Link) | Consuming one service privately: a SaaS database, a vendor API, or exposing one service to a customer's network | One direction, one service. Works with overlapping CIDRs. Hourly per endpoint per zone plus per-GB. SaaS providers usually reserve it for higher plans |
| Site-to-site VPN | Connecting to an office, another cloud, or a customer's data center | Throughput limits, MTU issues, both ends need non-overlapping ranges |
| Mesh VPN | A few hosts across providers need to talk | Depends on a third-party control plane unless self-hosted |

Decision rule for a hosted database or SaaS outside the VPC: at Prototype and Launch, a public endpoint restricted by IP allowlist (the static egress
IPs above), enforced TLS with certificate verification, and a strong rotated credential is acceptable. Move to a private link when a customer contract
or compliance framework requires that data not traverse the public internet, or when the provider's allowlist cannot be made narrow. Prefer private
link over peering with a vendor: peering exposes the whole network range in both directions and depends on address plans not colliding.

Enterprise customers asking to "connect privately to our VPC" mean private link from their network to the product's service: an endpoint service behind a network load balancer, with per-customer acceptance. Price it as an enterprise feature; each one is ongoing operational surface.

## Ask the user

- **Does any customer contract or compliance commitment say data must not cross the public internet, or name private connectivity?** Decides private link versus allowlisted public endpoints. Default: allowlist plus TLS until a contract says otherwise.
- **Does any partner or customer need to allowlist the product's outbound IP addresses?** Decides whether NAT with static IPs is needed at all. Default: no; skip NAT where tasks can use public subnets with no inbound.
- **Who needs direct access to the production database, and how often?** Sizes the access path. Default: nobody routinely; break-glass through the session service with logging, read-only role.
- **Is production availability worth the extra cost of per-zone NAT and three zones?** A money-versus-risk call. Default: two zones, one NAT gateway per zone in production, a single one elsewhere.
- **Are there existing networks (office, another cloud, an acquired product) this must eventually connect to?** Determines the CIDR plan. Default: choose unusual, non-overlapping `/16` ranges anyway.
