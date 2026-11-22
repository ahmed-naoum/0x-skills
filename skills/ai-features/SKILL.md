---
name: ai-features
description: "Designs LLM-powered product features that are useful, safe and affordable: whether to use a model, prompts and context, RAG, agents and tools, evals, guardrails, cost, latency, streaming UX and data handling. Use when adding an AI assistant, chat or summarization feature, building retrieval or an agent, or fixing wrong answers, prompt injection, LLM cost or slow responses."
---

# AI features in the product

## Stance

An LLM feature is ordinary software with one unreliable, expensive, slow component in the
middle. The work is to make that component's job as small as possible, surround it with code
that validates what goes in and what comes out, and measure it, because it cannot be reasoned
about the way code can. Most failed AI features fail on product shape, missing measurement or
missing limits, not on the model.

1. **Use a model only for the part that needs one.** Rules, lookups, arithmetic and anything
   with legal or financial weight belong in code; the model handles open-ended language. Each
   model step adds latency, cost and a new way to be wrong.
2. **Escalate complexity only on evidence.** Prompt, then context, then retrieval, then tools,
   then an agent, then fine-tuning. Stop at the first that meets the bar; every step up adds
   failure modes that a solo developer must operate.
3. **No eval set, no tuning.** Twenty real cases with pass criteria come before the second
   prompt edit. Without them every fix silently breaks something else and nobody can tell
   whether a change helped.
4. **Context beats wording.** Most wrong answers trace to what was or was not in the window.
   Log the assembled prompt and read it before touching the instructions.
5. **Model output is untrusted input.** Validate it against a schema, encode it before
   rendering, authorize every tool call server-side. A model that has read attacker-controlled
   text is acting for the attacker.
6. **Security lives in code, not in the prompt.** Permissions, tenant filters, approvals and
   egress limits are enforced by the surrounding system. Prompt instructions lower the failure
   rate; they are never the boundary.
7. **Every call has an owner, a budget and a fallback.** Meter per user and tenant from the
   first paying customer, cap spend, set timeouts, and decide what the user sees when the model
   is slow, down, refuses or has nothing to say.
8. **Output is a draft the user controls.** Show sources, allow editing and undo, mark AI
   content, and require approval before anything irreversible. Trust is earned through
   verifiability, not confidence.
9. **Customer data sent to a model is data sent to a vendor.** It needs a contract, a
   subprocessor entry, minimization and a retention period, like any other processor.

## Route

| If the task is … | Read |
|---|---|
| "Should we add AI to this?", choosing between prompt, RAG, tools or fine-tuning, picking a model tier, writing a prompt or structured-output contract, working out why quality is poor, running a local or in-browser model | `references/feature-design.md` |
| Answering from docs, a knowledge base or customers' files; chunking, embeddings, hybrid search, reranking; keeping tenants' data apart in search; stale or deleted documents; citations; "it makes things up when the docs don't say" | `references/retrieval.md` |
| Letting the model call functions or take actions; workflow versus agent; tool design; approvals; long-running agent jobs; code execution; agent memory; consuming MCP servers; sub-agents | `references/agents-tools.md` |
| "I can't tell whether my change helped"; building an eval set; graders and LLM judges; CI for prompts; tracing LLM calls; reviewing production output; using thumbs and edits; A/B testing a model or prompt | `references/evals.md` |
| Prompt injection, jailbreaks, data leaking through the assistant, rendering model output, agent permissions, content moderation, people farming the free tier, a pre-launch red team, labeling AI output | `references/guardrails.md` |
| The LLM bill is too high, responses are too slow, setting timeouts or per-user quotas, cost per customer, prompt caching, batch, routing to cheaper models, provider outages and rate limits, a model being retired | `references/cost-latency.md` |
| Building the chat or assistant UI, streaming with stop and retry, inline AI actions, showing sources or agent progress, error and empty states, rendering streamed markdown | `references/ai-ux.md` |
| "Can we send this customer data to the model?", provider training and retention terms, redacting PII from prompts and logs, how long to keep conversations, admin opt-out, AI questions in a security questionnaire, EU or regional processing | `references/ai-data-privacy.md` |

A new feature usually needs `feature-design.md` and `evals.md` first, then the file for its
shape (retrieval, agents), then `guardrails.md`, `cost-latency.md` and `ai-ux.md` before Launch.

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Provider | Claude through the Anthropic API, called from the server only | A customer contract demands a specific cloud or region |
| Model per call site | Mid tier for generation and chat; small tier for classification, routing, extraction; largest only for hard agent work | The eval set shows a tier gap, in either direction |
| Model ID | Pinned explicit version in configuration, one entry per call site | Never a floating alias in production |
| Output | Structured output validated with Zod; enums and an explicit "unknown" value | Prose meant for a person to read is streamed as text |
| Prompts | Files in the repository, versioned with model, parameters and tools; version recorded on every trace | |
| Grounding | Whole documents in a cached prompt if they fit; otherwise `pgvector` plus full-text search in Postgres with fusion, then a reranker | A dedicated search system at Scale (`0x:data-stores`) |
| Structured or live data | A narrow tool that runs a query; never embeddings of rows | |
| Orchestration | Fixed workflow in code; one agent with few tools when steps cannot be listed in advance | Sub-agents only when one agent measurably fails |
| Agent actions | Reads and drafts automatic; external, paid or destructive actions need approval bound to the exact arguments | |
| Agent identity | The invoking user's permissions; tenant and user from the session | Never a shared service account |
| Interaction | Inline actions for named tasks; chat only for the open-ended remainder; AI never the only path to a core function | |
| Delivery | Stream to the UI with a stop control; background job for anything beyond a request timeout | |
| Evals | 20 to 50 real cases with code graders first; LLM judges only when calibrated against human labels | |
| Quotas | Per user and tenant, in tokens or cost, checked before the call; hard spend limit in the provider account | |
| Fine-tuning, self-hosting | No | Narrow high-volume task with data, or a contract forbidding third-party processing |
| Customer data | Commercial API terms with no training on inputs; explicit field selection; content traces kept about 30 days in a restricted store | Regulated data: blocked until legal basis and vendor agreements are confirmed |

By stage:

- **Prototype**: prove usefulness on ten real inputs with the strongest model; one call or a
  short chain; a script-based eval; input size caps and a provider spend limit. Skip vector
  databases, agent frameworks, multi-provider fallback, fine-tuning and judges.
- **Launch**: eval set gating prompt and model changes; tracing; per-user metering and quotas;
  timeouts and designed failure states; tenant filters tested in retrieval and tools; safe
  rendering; approvals on consequential actions; injection red-team pass; provider terms,
  subprocessor entry, retention and a tenant-level off switch.
- **Scale**: cost attribution per customer and routing by measured difficulty; online
  comparisons with guardrail metrics; calibrated judges on sampled traffic; cross-provider or
  cross-platform fallback; durable execution for long agents; regional processing where sold.

## Before you call it done

1. Every model call goes through one server-side module; no provider key or direct provider
   call exists in client code (`grep` the client bundle sources for the SDK import and key name).
2. Each call site has a typed input with size caps, an output schema validated in code, an
   explicit `max_tokens`, and handling for invalid output, truncation, refusal, timeout and
   rate limit.
3. An eval set of real cases exists in the repository, includes should-decline and adversarial
   cases, and was run before and after this change with per-case flips reviewed.
4. Prompt, model ID, parameters and tool definitions are versioned in code, and the version is
   on every trace.
5. Retrieval and every tool derive tenant and user from the session; an automated test proves
   user A cannot obtain tenant B's content through the assistant.
6. Model output is never passed to `dangerouslySetInnerHTML`, `eval`, a shell or SQL with
   application credentials; markdown renders with raw HTML off, links restricted to safe
   schemes and remote images blocked or allowlisted.
7. Any run that reads untrusted content cannot both reach private data and send data out
   without approval; a planted-injection test with a canary string passes.
8. Irreversible or external actions are gated in the tool executor, with approval tied to the
   exact arguments; writes carry idempotency keys.
9. Agent loops have step, spend and time limits with a designed result when each trips, and
   can be cancelled.
10. Usage is recorded per user, tenant and feature from the API's token counts; quotas are
    checked before the call; a hard spend limit and an anomaly alert exist.
11. First-token, idle and total timeouts are set; client disconnect aborts the provider call;
    the product works with the provider unavailable.
12. The UI has designed states for empty retrieval, refusal, timeout, quota and partial output;
    stop works; a reload shows the saved result.
13. AI-generated content is labeled, citations link to sources built from stored metadata, and
    each output has a report control tied to its trace.
14. Prompt and output content is kept out of general logs and the error tracker; traces have
    a retention period enforced by a job.
15. The provider is in the subprocessor list under terms reviewed for training and retention;
    a tenant-level switch stops all data reaching the model; deletion reaches conversations,
    embeddings, caches and traces.

## Not this skill

- Anthropic API parameters, model IDs, tool-use syntax, caching and SDK code → `claude-api`
- Using coding agents to build the product itself → `0x:ai-coding-agents`
- Vector indexes and search-engine setup → `0x:data-stores`
- EU AI Act classification and legal transparency duties → `0x:privacy-compliance`
- Exposing your own API to outside agents through MCP → `0x:api-design`
- Pricing AI features and credit packaging → `0x:pricing-monetization`
