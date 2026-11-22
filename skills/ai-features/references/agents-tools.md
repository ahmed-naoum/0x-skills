# Agents and tools

Read this when: a model should call functions, query live data or take actions; a task needs
several model steps; deciding between a scripted pipeline and an agent; adding approvals,
sandboxing, long-running execution, memory, MCP servers or sub-agents.

## Workflow or agent

A **workflow** is code that calls the model at fixed points. An **agent** is a loop in which the
model decides the next step. Every degree of freedom given to the model costs predictability,
tokens and test coverage, so grant the least that solves the task.

| Task shape | Build | Why |
|---|---|---|
| One transformation (classify, extract, summarize) | Single call | Nothing to orchestrate |
| Known steps in a known order (extract, then validate, then draft) | Prompt chain in code | Each step is testable; failures are local |
| Input type decides the path | Router: small-model classifier, then a specialized prompt | Cheap, and each branch stays simple |
| Independent subtasks (review ten files) | Parallel calls in code, then merge | Faster; no shared context to corrupt |
| Draft must meet a checkable bar | Generate, check (code or a grader), revise, with a retry cap | Bounded loop with a clear exit |
| Steps cannot be listed in advance; the next action depends on what was found | Agent loop with tools | Only here does model-directed control earn its cost |

Signs that an agent is the wrong choice: the steps can be written as a numbered list; the task
must finish in a couple of seconds; the outcome must be identical every time; nobody can say how
success would be checked. Start with the workflow, and promote one step to an agent when the eval
set shows the fixed path failing on real variety.

A useful middle form: a workflow whose single flexible step is a small agent with two or three
read-only tools (search, fetch record). The outer steps stay deterministic.

## Tool design

The model sees only the name, the description and the schema. Tools designed like internal REST
endpoints fail; tools designed like the buttons a new support hire would be given work.

- **Narrow, task-shaped tools.** `refund_order(order_id, amount_cents, reason)` beats
  `call_api(method, path, body)` and beats `run_sql`. A narrow tool can be authorized, validated,
  logged and approved; a general one is an open door.
- **Few tools.** Accuracy of tool choice falls as the list grows and as tools overlap. Under
  about ten to fifteen per agent is a workable rule of thumb; merge tools that are always called
  together, and split ones the model confuses.
- **Descriptions carry the weight.** Three or four sentences: what it does, when to use it and
  when not to, what each parameter means with an example value, what comes back. Most tool-use
  failures are fixed by rewriting a description, not by changing the model.
- **Unambiguous parameters.** `user_id` not `user`; enums not free strings; accept the
  identifiers the model actually has (a name or email it saw), and resolve them in code.
- **Server-side identity.** Tenant, user and permissions come from the session, never from
  tool arguments. The model must not be able to pass `tenant_id`.
- **Idempotent writes.** The loop will retry after timeouts, and the model will sometimes
  repeat a call. Derive an idempotency key from run ID plus tool-call ID and make the handler
  return the first result on repeats (`0x:api-design`, `idempotency-rate-limits.md`).
- **Typed, instructive errors.** Return errors as tool results the model can act on, not as
  exceptions that kill the run: `{"error":"not_found","message":"No order 8841 for this
  customer. Use search_orders to find the ID."}`. Mark the result as an error in the API's
  tool-result format. Distinguish retryable, fixable-by-model and fatal.
- **Small results.** Return the fields needed, paginated, with a hard size cap and a truncation
  note. One tool that returns a 200 KB JSON blob ruins the rest of the run.
- **Read and write tools are different classes.** Tag each tool as read, reversible write or
  irreversible write; the tag drives approval, logging and the sandbox.

Validate tool input with the same schema on the server even when the API enforces the schema:
the values can still be wrong, out of range or hostile.

## The loop

```ts
for (let step = 0; step < MAX_STEPS; step++) {
  if (signal.aborted || spent > BUDGET) return stop("cancelled_or_budget");
  const res = await callModel(messages, tools, { signal });
  messages.push({ role: "assistant", content: res.content });
  if (res.stop_reason !== "tool_use") return finish(res);
  const results = await runTools(res.content, ctx);   // validate, authorize, approve, execute
  messages.push({ role: "user", content: results });  // one result per tool call, matched by id
}
return stop("step_limit");
```

Limits every loop needs, each with a designed outcome when it trips:

| Limit | Starting point | On trip |
|---|---|---|
| Steps | 10 to 25 for interactive, higher for background | Return partial work and say what remains |
| Token or cost budget per run | Set from what a run is worth | Same, and record it |
| Wall-clock deadline | Seconds for interactive, minutes to hours for jobs | Checkpoint and stop |
| Repetition | Same tool with same arguments 3 times | Inject a notice or stop; the model is stuck |
| Consecutive tool errors | 3 | Stop and surface the error |

Other rules: handle every stop reason, not only "tool use" and "done" (token limit, refusal and
paused turns all occur); return a result for every tool call in the turn or the next request is
rejected; run independent read calls in parallel and writes in order; keep the context from
growing without bound by dropping or summarizing old tool results; make "done" explicit, for
example a `finish` tool carrying the structured result, so completion is validated instead of
inferred from prose. Trace every step with the run ID (`evals.md`).

## Human approval

Classify by reversibility and blast radius, not by how risky the action sounds.

| Class | Examples | Policy |
|---|---|---|
| Read | Search, fetch a record | Auto, within the user's permissions |
| Reversible, contained write | Draft, label, add a note, create in a draft state | Auto, with an undo and an activity log |
| External or hard-to-reverse | Send email or message, publish, call a customer's webhook | Approve each time, showing the exact content |
| Irreversible or costly | Delete, pay or refund, change permissions, run a migration | Approve each time; consider not offering as a tool at all |

How to build approval so that it holds:

- **Enforce in the tool executor**, in code. A prompt instruction "ask before deleting" is a
  request, and injected text can talk the model out of it.
- **Show the real action**: the exact recipient, amount and body, rendered from the tool
  arguments, not the model's description of what it intends.
- **Bind approval to the arguments.** Store a hash of the tool name and arguments with the
  approval; execute only if the hash matches. Otherwise a later step can swap the payload.
- **Persist and suspend.** Approval may come hours later; the run must be resumable from stored
  state, not held in memory (see durability below).
- **Avoid approval fatigue.** If users approve fifty prompts a day they stop reading. Batch
  ("send these 12 emails"), allow "always allow for this session" only for reversible classes,
  and prefer designing the action as a draft the user sends themselves.
- **Staged effects** give an undo to things that have none: queue the email for five minutes,
  soft-delete, create the refund as pending.

## Model Context Protocol

MCP standardizes how a model-driven application (the host, through clients) connects to servers
that expose tools, resources and prompts. Transports are stdio for local servers and streamable
HTTP for remote ones; remote servers authorize with OAuth.

| Situation | Choice |
|---|---|
| Tools used only by this product's own backend | Plain in-process tool functions; MCP adds a hop and nothing else |
| The same tools must serve several agents or hosts (the product, an IDE, a desktop assistant) | An MCP server |
| Using a vendor's integration (issue tracker, docs, CRM) | Their official MCP server, if one exists, over writing a client |
| Letting customers' agents use the product | An MCP server as a public surface: owned by `0x:api-design` |

Rules when consuming MCP servers:

- A third-party server is third-party code plus third-party prompt text. Tool descriptions and
  results enter the model's context and can carry injected instructions; pin the server version,
  review tool descriptions, and alert when they change.
- Expose an allowlist of tools to the model, not everything the server offers. Every loaded
  tool definition costs tokens on each request and dilutes tool choice.
- Per-user authorization: each end user's token for the remote system, stored server-side and
  scoped to that user. One shared admin token turns every user into an admin through the agent.
- Tool annotations such as "read-only" are hints from the server, not guarantees. Classify
  tools for approval locally.
- Do not combine a server that reads untrusted content with tools that can send data out
  without the controls in `guardrails.md`.

## Long-running tasks

Anything past a request timeout (a rule of thumb: over 30 to 60 seconds) runs as a background
job, not inside an HTTP handler (`0x:backend-architecture`, `background-jobs.md`).

- **State in the database**: a run row (status, step count, spend, owner, tenant) and an
  append-only step log (model response, tool calls, tool results). The message history is
  rebuilt from the log.
- **Checkpoint after every step.** On resume, replay from the log; never re-execute a tool whose
  result is already recorded. A step whose call was recorded without a result is the dangerous
  case: this is where idempotency keys make re-execution safe.
- **Cancel** by a flag checked before each model call and each tool call, with the abort signal
  passed into in-flight requests. Cancellation must leave the run in a consistent recorded state.
- **Suspend** for approvals and for waiting on external events by ending the job and
  re-enqueuing on the event; do not hold a worker.
- **Progress** to the UI from the step log (polling or server-sent events), so a page reload
  reattaches (`ai-ux.md`).
- **Concurrency**: one active worker per run (a row lock or lease); two workers on one run
  double every action.
- **Long contexts**: when the history nears the budget, compact it: summarize completed work
  into a state note, keep the task statement and recent steps verbatim.

A durable-execution engine (Temporal, Inngest, Restate and similar) provides replay and
suspension ready-made; adopt one at Scale or when runs last hours. At Launch, a Postgres-backed
queue plus the step log is enough.

## Sandboxing and credentials

Model-written code and shell commands are untrusted code: prompt injection can turn any agent
with code execution into remote code execution.

- Run it in an isolated environment per session: a microVM or container sandbox service, or the
  provider's hosted code-execution tool. Never in the application server's process, container or
  host, and never with `eval` or an unsandboxed child process.
- Default-deny network egress; allowlist the few hosts the task needs. Open egress is the path
  by which secrets and data leave.
- No ambient credentials: no cloud metadata endpoint, no mounted environment files, no deploy
  keys. Inject short-lived tokens scoped to this user, this resource and this task, or keep the
  secret outside the sandbox and proxy the call.
- Set CPU, memory, disk, process and wall-clock limits; use a read-only base image and an
  ephemeral filesystem destroyed at session end.
- The agent acts **as the user**: every tool runs under the invoking user's authorization, so
  the agent can never do what the user could not. A service account with broad rights makes the
  agent a privilege-escalation path.

## Memory across sessions

Start without it. Session history plus the user's existing product data covers most needs, and
persistent memory adds a privacy surface and a poisoning surface.

When it is needed:

- Prefer explicit, structured memory (a preferences record, a notes file per project) written
  through a tool, over automatic embedding of every conversation.
- Scope every memory to user and tenant; apply the same permission filter as retrieval.
- Record provenance: which run wrote it, from what source. Do not write content derived from
  untrusted documents or web pages into memory without user confirmation: a poisoned memory
  re-injects the attack into every future session.
- Make it visible and editable: users can read, correct and delete what is remembered, and
  account deletion removes it (`ai-data-privacy.md`).
- Treat recalled memory as data, not instructions, and date it so stale facts can be discounted.
- Cap size and prune; unbounded memory degrades answers like any bloated context.

## Sub-agents

One agent with good tools is the default. Multiple agents multiply token use several times over,
lose information at each handoff and are far harder to debug.

Split only when a single agent fails on the eval set for a reason splitting fixes:

| Reason | Pattern |
|---|---|
| Context overflows with exploration (search results, file reads) | Sub-agent explores in its own context and returns a short summary |
| Truly independent subtasks at breadth | Orchestrator fans out, workers run in parallel, orchestrator merges |
| Conflicting instructions or very different tool sets | Separate specialist per role |
| Independent check wanted | A reviewer with fresh context and a different prompt |

Do not split tightly coupled work: sub-agents that must agree on shared decisions will diverge.
Give each sub-agent a complete brief (goal, output format, boundaries, what is already known),
since it sees none of the parent's context. Give sub-agents the minimum tools, read-only where
possible, and keep irreversible actions with the orchestrator behind approval.

## Ask the user

- **Which actions may the agent take without asking, and which never?** This is a risk decision.
  Default: reads and drafts automatic; anything sent outside the product, paid, or deleted needs
  approval every time.
- **What is one run worth?** Sets the step, token and time budgets. Default: a conservative cap
  with partial results on trip, raised after seeing real runs.
- **Whose permissions does the agent use?** Default: exactly the invoking user's, never a
  service account.
- **Should the agent remember things between sessions?** Default: no persistent memory until a
  specific need appears, then user-visible and deletable.
- **May the agent run code or browse the open web?** Both widen the attack surface sharply.
  Default: no; add with a sandbox and egress allowlist when a feature requires it.
