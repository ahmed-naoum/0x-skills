# Kubernetes operations

Read this when: the project already runs on Kubernetes or has decided to, and the task is deploying, debugging, securing or upgrading workloads. For whether to adopt Kubernetes at all, read `platform-choice.md` first; the default answer for a solo founder is no.

## Ground rules for a small team on Kubernetes

- Use a managed control plane (GKE, EKS, AKS). Prefer the provider's most managed mode (GKE Autopilot, EKS Auto Mode) unless a workload needs node-level control: nodes, upgrades and autoscaling stop being the team's problem.
- Keep state out of the cluster. Managed Postgres, managed Redis, object storage. Running a database operator is a second job.
- Install few controllers. Each add-on (ingress or gateway controller, cert-manager, external-dns, external-secrets, a GitOps agent, metrics) must be upgraded in step with the cluster. Six is plenty; a service mesh is not on the list until a requirement names it.
- One cluster per environment boundary that matters (production separate from everything else), not one per team or service.

## A Deployment that survives rollouts and node drains

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: web, namespace: app }
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  selector: { matchLabels: { app: web } }
  template:
    metadata: { labels: { app: web } }
    spec:
      terminationGracePeriodSeconds: 45
      automountServiceAccountToken: false
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector: { matchLabels: { app: web } }
      containers:
        - name: web
          image: registry.example.com/web@sha256:<digest>
          ports: [{ containerPort: 3000 }]
          envFrom:
            - configMapRef: { name: web-config }
            - secretRef: { name: web-secrets }
          resources:
            requests: { cpu: 250m, memory: 512Mi }
            limits: { memory: 512Mi }
          startupProbe:
            httpGet: { path: /healthz, port: 3000 }
            periodSeconds: 2
            failureThreshold: 30
          readinessProbe:
            httpGet: { path: /readyz, port: 3000 }
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet: { path: /healthz, port: 3000 }
            periodSeconds: 10
            failureThreshold: 3
          lifecycle:
            preStop:
              exec: { command: ["sleep", "10"] }
          securityContext:
            runAsNonRoot: true
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
            seccompProfile: { type: RuntimeDefault }
```

Why each non-obvious line is there:

- **Three probes with different jobs.** Startup gives a slow boot up to `periodSeconds × failureThreshold` (60 s here) before liveness applies.
  Readiness removes the pod from Service endpoints without restarting it; it may check dependencies. Liveness restarts the container; it must check only
  the process itself. A liveness probe that queries the database turns a database blip into a cluster-wide restart storm.
- **`maxUnavailable: 0`, `maxSurge: 1`** keeps full capacity during rollout. With two replicas, the default 25 percent rounds in ways that can drop to one.
- **`preStop` sleep plus grace period.** Endpoint removal and SIGTERM happen in parallel; without a pause the pod stops listening while load balancers
  still send to it, producing 502s on every deploy. Sleep 5 to 15 s, then the app drains on SIGTERM; `terminationGracePeriodSeconds` must exceed sleep
  plus the longest request. The image needs a `sleep` binary for the exec form; recent Kubernetes versions offer a built-in `preStop: { sleep: {
  seconds: 10 } }` that works in distroless images.
- **Config outside the image.** Non-secret settings in a ConfigMap, secrets in a Secret synced from the cloud's secret manager (External Secrets
  Operator) or encrypted in git (SOPS, Sealed Secrets). Pods do not restart when a ConfigMap or Secret consumed as environment changes: put a checksum
  annotation on the pod template or name the ConfigMap by content hash (Kustomize `configMapGenerator` does this).
- **Image by digest or immutable SHA tag.** `:latest` with the default pull policy makes rollbacks and node replacements nondeterministic.
- **`readOnlyRootFilesystem`** needs an `emptyDir` mounted wherever the app writes (`/tmp`, a framework cache directory).

Add a PodDisruptionBudget for every Deployment with two or more replicas (`minAvailable: 1` or `maxUnavailable: 1`), or a node drain can evict all replicas at once. Do not set a budget that allows zero disruptions (`maxUnavailable: 0`, or `minAvailable` equal to replicas): it blocks node upgrades indefinitely.

Run schema migrations as a Job before the rollout (a pipeline step or a GitOps pre-sync hook), not in an init container that every replica races to execute.

## Debugging a pod

Always start with the same three commands; the answer is in the events more often than in the logs.

```bash
kubectl get pods -n app -o wide
kubectl describe pod <pod> -n app            # read Events at the bottom and Last State
kubectl logs <pod> -n app --previous         # logs of the container that crashed
kubectl get events -n app --sort-by=.lastTimestamp | tail -20
```

| Status | Look at | Common causes and fix |
|---|---|---|
| `Pending`, event `FailedScheduling` | The event text states the reason per node | `Insufficient cpu/memory`: requests exceed any node's free capacity; lower requests or let the node autoscaler add a node (check its max size and cloud quota). `node(s) had untolerated taint` or `didn't match node affinity/selector`: fix selector or toleration. `volume node affinity conflict`: the PersistentVolume is in another zone than any schedulable node. `pod has unbound immediate PersistentVolumeClaims`: no matching StorageClass or provisioning failed; `kubectl describe pvc` |
| `Pending` with no events | Namespace `ResourceQuota`, or no scheduler capacity on a serverless node mode | `kubectl describe quota -n app` |
| `ImagePullBackOff` / `ErrImagePull` | Event text | Wrong tag or digest, missing registry credentials (`imagePullSecrets` or node role lacking pull permission), architecture mismatch (`no matching manifest`) |
| `CreateContainerConfigError` | Event text | Referenced Secret or ConfigMap key does not exist in this namespace |
| `CrashLoopBackOff` | `Last State` exit code and reason, `logs --previous` | Exit 137 with `OOMKilled`: memory limit too low or a leak. Exit 137 without it: killed by liveness probe or grace period. Exit 1: application error at boot, usually missing configuration or unreachable dependency. Exit 127 or 126: wrong command, or file missing or not executable. `exec format error`: wrong architecture |
| `Running` but `0/1` ready | `describe` shows `Readiness probe failed` with the HTTP code or timeout | Wrong path or port, app listening on `127.0.0.1` instead of `0.0.0.0`, dependency check failing, probe timeout shorter than the endpoint's latency under load |
| Ready, but the Service returns nothing | `kubectl get endpointslices -n app -l kubernetes.io/service-name=web` | Empty endpoints: Service selector does not match pod labels, or `targetPort` is wrong. A NetworkPolicy may be dropping traffic |
| `Terminating` forever | `describe` finalizers | A finalizer whose controller is gone, or a node that is unreachable |

To get a shell in a distroless or crashing pod: `kubectl debug -it <pod> -n app --image=busybox --target=web`. To test the app without the Service path: `kubectl port-forward pod/<pod> 3000:3000 -n app`. Fix the manifest in git, not with `kubectl edit`: under GitOps a hand edit is reverted, and without it the next deploy silently undoes it.

## Requests, limits and autoscaling

Requests decide scheduling and the node bill; limits decide what happens under pressure.

| Setting | Rule | Reason |
|---|---|---|
| Memory request | Observed steady peak plus about 20 percent | Scheduler packs by requests; too low and nodes overcommit and evict |
| Memory limit | Equal to the request | Memory is not compressible; a limit above the request invites node-level OOM that kills arbitrary pods |
| CPU request | Typical usage at normal load (a p90 over a week is a reasonable start) | Guarantees a share under contention and is the denominator for CPU-based autoscaling |
| CPU limit | Usually omit for latency-sensitive services | A limit throttles the container within each scheduling period even when the node is idle, showing as unexplained tail latency. Set one for batch or untrusted workloads, or where a policy requires it |

Every container needs requests; a namespace `LimitRange` supplies defaults for those that forget. Size from data: `kubectl top pod --containers`, the metrics backend, or the Vertical Pod Autoscaler in recommendation-only mode.

Horizontal autoscaling:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: web, namespace: app }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: web }
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 65 } }
```

- Utilization is a percentage of the **request**. No CPU request means the autoscaler reports unknown and does nothing.
- Remove `replicas` from the Deployment manifest once an autoscaler owns it, or each apply resets the count.
- `maxReplicas` is a spend cap and a database-connection cap: `maxReplicas × pool size` must stay under what the database or pooler accepts.
- Queue workers scale on backlog, not CPU: use KEDA or an external metric.
- Do not run the Vertical Pod Autoscaler in auto mode on the same resource metric a horizontal autoscaler uses; they fight.
- Pod autoscaling without node autoscaling (Cluster Autoscaler, Karpenter, or the managed node mode) just produces Pending pods. Set a node maximum as well.

Scaling policy and capacity planning beyond the mechanics belong to `0x:site-reliability`.

## Traffic in: Gateway API, ingress and certificates

- New clusters: use **Gateway API** (`Gateway` plus `HTTPRoute`) with the cloud's managed implementation or a maintained controller (Envoy Gateway, Cilium, Traefik, NGINX Gateway Fabric). It separates the infrastructure object (Gateway, owned by whoever runs the cluster) from routes (owned by the app) and is where new development goes.
- Existing clusters on the `Ingress` API: it remains supported; migrate when convenient. Check the status of the specific controller, though: the community `ingress-nginx` controller has been retired by the Kubernetes project, so a cluster running it needs a migration plan to another controller or to Gateway API rather than further investment.
- Expose one Gateway or ingress controller behind one cloud load balancer, and route by host and path. A `Service` of type `LoadBalancer` per app creates one billed load balancer each.
- Certificates: cert-manager with an ACME `ClusterIssuer` issues and renews automatically for both Ingress and Gateway resources. HTTP-01 works for
  public hostnames; wildcards and private hostnames need DNS-01 with scoped DNS API credentials. Use the staging ACME endpoint while testing to avoid
  production rate limits. A cloud-managed certificate on the load balancer is simpler when the provider's gateway supports it.
- external-dns can create DNS records from routes; scope its credentials to one zone.

Load-balancer behavior, TLS settings and DNS are covered in `0x:web-networking`.

## GitOps and manifests

Model: a git repository holds the desired state; an in-cluster agent (Argo CD or Flux) pulls and applies it. CI builds the image and opens or pushes a commit changing the image digest; it holds no cluster credentials. Rollback is `git revert`.

| Choice | Default | Flip when |
|---|---|---|
| Plain manifests with Kustomize overlays vs own Helm chart | Kustomize for the team's own services: the diff in a PR is the change | Many near-identical services justify one shared chart |
| Third-party software | The vendor's Helm chart, version pinned, values file in git | n/a |
| GitOps agent vs `kubectl apply` or `helm upgrade` from CI | An agent at Scale or with more than one cluster | Launch with one cluster: CI running `helm upgrade --install --atomic --wait` (rolls back automatically on failure) is acceptable and simpler |

Make changes reviewable: render in CI (`kustomize build` or `helm template`) and show the diff against the cluster (`kubectl diff -f -`, or the agent's diff) in the pull request. Template changes are unreadable without the rendered output. Validate rendered manifests against the target version's schemas (kubeconform) before merge.

Traps: never commit plain Secrets (base64 is encoding, not encryption); enable pruning only after confirming the agent's scope, or it deletes resources it does not find in git; turn on self-heal so manual edits are reverted, and tell everyone with cluster access that it is on.

## Isolation

Namespaces are a naming and policy scope, not a security boundary on their own. Three layers make them one:

1. **Network policy.** By default every pod can reach every other pod. Apply a default-deny ingress policy per namespace, then allow specific flows. Policies do nothing unless the cluster's network plugin enforces them (check the provider's setting). When denying egress as well, allow DNS to the cluster resolver first or everything fails with name-resolution errors.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-ingress, namespace: app }
spec:
  podSelector: {}
  policyTypes: ["Ingress"]
```

2. **Pod security.** Label namespaces for Pod Security Admission: `pod-security.kubernetes.io/enforce: baseline` at minimum, `restricted` for application namespaces (requires the `securityContext` shown in the Deployment above). Roll out with the `warn` and `audit` labels first to see what would be rejected.
3. **Identity and RBAC.** One ServiceAccount per workload; `automountServiceAccountToken: false` unless the pod calls the Kubernetes API; cloud
   permissions through workload identity (EKS Pod Identity or IRSA, GKE Workload Identity Federation, AKS Workload Identity), never node-wide roles or
   static keys in Secrets. No `cluster-admin` for CI or apps; namespace-scoped Roles. Enable encryption of Secrets at rest with the provider's key
   service.

For tenants that are mutually untrusted (customer code, for example), namespaces with policies are not enough: use separate node pools with sandboxed runtimes, or separate clusters.

## Upgrades

Kubernetes ships about three minor releases a year and each is supported upstream for roughly a year; managed providers force-upgrade or charge extended-support fees after that. Plan an upgrade every four to six months; staying current is cheaper than a multi-version catch-up.

Sequence:

1. Read the release notes for removed APIs and behavior changes. Scan manifests and live objects for deprecated API versions (pluto or kubent), and check the provider's upgrade-readiness report.
2. Check each add-on's compatibility matrix (gateway or ingress controller, cert-manager, CNI, CSI drivers, autoscaler, GitOps agent) and upgrade add-ons that must move first.
3. Upgrade a non-production cluster and run the deploy pipeline against it.
4. Upgrade the control plane one minor version at a time; skipping minors is not supported.
5. Upgrade nodes: surge upgrade in place, or create a new node pool on the new version, cordon and drain the old one, then delete it (safer, and easy to reverse until the old pool is gone). Nodes may lag the control plane by a limited number of minors but never lead it.
6. Watch error rate and pod restarts during drains; pause on regression.

Zero-downtime drains depend on work done earlier: at least two replicas spread across nodes, a PodDisruptionBudget that permits one eviction, readiness probes, and graceful shutdown. A drain that hangs is almost always a budget that allows zero disruptions or a pod with no controller. Control-plane upgrades cannot be rolled back; the staging cluster is the rehearsal.

## Ask the user

- **Who owns cluster upgrades, and when was the last one?** If nobody, the cluster is a liability; default to proposing the most managed node mode or a move to a managed container service.
- **Is any workload stateful inside the cluster?** Changes drain, backup and upgrade risk. Default: plan to move state to managed services.
- **What is the maximum monthly spend the cluster may reach under autoscaling?** Sets node-pool and `maxReplicas` caps. Default: twice current steady-state node count.
- **Do workloads from different customers or trust levels share the cluster?** Decides whether namespaces suffice. Default: one trust level; namespaces with default-deny policies.
- **Is a deploy that briefly drops requests acceptable?** If not, the preStop, budget and probe work above is mandatory before the next node upgrade. Default: not acceptable at Launch and beyond.
