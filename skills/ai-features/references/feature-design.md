# Designing an LLM feature

Read this when: an AI feature is proposed or being shaped; choosing between a prompt, retrieval,
tools or fine-tuning; picking a model tier; writing the prompt and the call's contract; or a
feature underperforms and the cause is unknown.

## Does this need a model at all

A model call is slower, costlier and less predictable than code, and it can be wrong in ways no
test fully excludes. Use one only where the input or output is open-ended language (or images) and
an occasional wrong answer is survivable or checkable.

| Problem shape | Use | Reason |
|---|---|---|
| Rules can be written down; input is structured | Code, SQL, a regex, a rules table | Exact, free, testable |
| Lookup or filter over known fields | Database query or search | A model adds error, not value |
| Arithmetic, dates, money, aggregates | Code; let the model call it as a tool if language is involved | Models miscalculate at a low but nonzero rate |
| Ranking by behavior (recommendations) | Classical ranking or embeddings similarity | Cheaper and measurable |
| Classify, extract, summarize, rewrite, draft from messy text | LLM | Rules cannot enumerate language |
| Open question answered from documents | LLM with retrieval | See `retrieval.md` |
| Multi-step task with choices that depend on intermediate results | LLM with tools | See `agents-tools.md` |
| Decision with legal, financial or safety weight | Code or a human decides; the model may draft or triage | The error must be attributable and reviewable |

Three tests before building:

1. **Error cost.** What happens when the output is wrong one time in twenty? If the answer is
   "a customer is charged, a record is deleted, advice is acted on", put a deterministic check or a
   human between the model and the effect.
2. **Verifiability.** Can the user tell at a glance whether the output is right (a draft, a
   summary beside its source)? Features where the user cannot check the output need citations,
   validation or a narrower scope.
3. **Hybrid first.** Most good features are code with one model step in the middle: code gathers
   the data, the model does the language part, code validates and applies the result. Shrink the
   model's job until it is the part only a model can do.

At Prototype, build the smallest version by hand: paste ten real inputs into the model with a
draft prompt. If the outputs are not useful there, no architecture will rescue the feature.

## Which approach

Escalate in this order and stop at the first that meets the bar on the eval set (`evals.md`):

1. A better prompt with examples.
2. More of the right context placed in the prompt (the user's record, the relevant document).
3. Retrieval, when the knowledge does not fit or changes per query.
4. Tools, when the model needs live data or must take an action.
5. A multi-step workflow or agent, when one call cannot hold the task.
6. Fine-tuning, last (see below).

Each step adds moving parts and failure modes. Skipping steps is the most common waste: teams build
a vector pipeline for 40 pages of docs that fit in one cached prompt.

## Model tier

Providers ship three rough tiers: small and fast, mid, and largest. Model IDs, prices and context
limits change; read them from the `claude-api` skill, not from memory.

| Task | Start with | Move when |
|---|---|---|
| Classification, routing, extraction of clear fields, short rewrites, moderation | Small | Eval failures cluster on nuance or long inputs |
| Summaries, RAG answers, drafting, most chat, tool use with a few tools | Mid | Quality bar unmet after prompt and context work |
| Long multi-step agents, hard reasoning, code generation, ambiguous high-stakes judgment | Largest | Never by default for high-volume paths |

Rules that settle most choices:

- Prototype on the strongest model to learn whether the task is possible at all, then step down
  with the eval set as the judge. Starting small confuses "the model cannot" with "the prompt is bad".
- Pick per call site, not per product. One feature often has a small-model classifier in front of
  a mid-model generator.
- Output tokens dominate latency; input tokens usually dominate cost in RAG and agents. A smaller
  model fixes latency; trimming or caching context fixes cost (`cost-latency.md`).
- Extended reasoning ("thinking") buys quality on multi-step problems and costs latency and
  output tokens. Leave it off for classification and extraction; measure before enabling.
- Keep the model ID in configuration per call site so a tier change is a one-line diff that the
  eval run can gate.

## The prompt

Write the prompt as a brief for a capable new colleague who knows nothing about the product.

Order that works for most calls:

1. **Role and situation**: who the model is acting as, for whom, inside which product.
2. **Task**: what to produce and what a good result is for; the purpose lets the model handle
   cases the rules did not foresee.
3. **Rules and constraints**: scope, tone, length, what to do when information is missing.
4. **Examples**: three to five, covering the hard and boundary cases, not five easy ones.
   Examples outweigh instructions: a rule contradicted by an example loses.
5. **Output format**: schema or exact shape, kept with the other stable parts so it stays in
   the cached prefix.
6. **Reference material**: documents, records, retrieved chunks, each in its own delimited block.
7. **The specific request**, last.

Practices that change results:

- Delimit every kind of content with XML-style tags (`<document>`, `<user_message>`,
  `<examples>`). The model then distinguishes instructions from data, and the code can swap parts.
- State what to do, with the reason, instead of piling up prohibitions. "Answer only from the
  documents, because users act on these answers without checking" generalizes; ten "do not" lines
  do not.
- Give an explicit way out: what to output when the input is empty, off-topic, or insufficient.
  Without one the model invents an answer to satisfy the format.
- Put stable content (instructions, examples, shared documents) first and per-request content
  last. This also makes the prefix cacheable.
- Put system-level instructions in the system prompt and user-supplied text in the user turn.
  Never interpolate user text into the system prompt: that hands the user the instruction channel.
- For long documents, place them before the question and ask the model to quote the relevant
  passages before answering; this usually raises accuracy on long inputs (confirm on the eval
  set).
- Avoid shouting (capitals, "CRITICAL"). Current models follow plain instructions; overemphasis
  makes them over-apply one rule at the expense of the rest.
- Do not lean on temperature 0 for repeatable output: results still vary run to run, and some
  current models reject non-default sampling parameters. Get consistency from examples, a
  schema and validation in code.

## The call's contract

Treat each call site as a function with a typed signature, and write the signature first.

- **Inputs**: a typed object, validated, with size limits per field (truncate or reject; never
  pass unbounded user text or documents).
- **Output**: a schema. Get it through the provider's structured-output feature or a forced tool
  call, then validate with the same schema in code. Model output is untrusted even when it parses.
- **Failures**: enumerate them and decide each.

```ts
const Triage = z.object({
  category: z.enum(["billing", "bug", "how_to", "other"]),
  urgency: z.enum(["low", "normal", "high"]),
  summary: z.string().max(280),
});

const res = await client.messages.create({
  model: MODELS.triage, max_tokens: 512, system: TRIAGE_PROMPT,
  tools: [{ name: "record_triage", description: "Record the triage result.",
            input_schema: z.toJSONSchema(Triage) as Anthropic.Tool.InputSchema }], // Zod 4
  tool_choice: { type: "tool", name: "record_triage" }, // not combinable with extended thinking
  messages: [{ role: "user", content: `<ticket>${ticket}</ticket>` }],
});
const block = res.content.find((b) => b.type === "tool_use");
const parsed = Triage.safeParse(block?.input);
```

The Anthropic TypeScript SDK also ships Zod helpers for native structured output (the schema is
passed as the output format and a parsed result comes back); take the current syntax from
`claude-api`. Schema-constrained output guarantees the shape but supports only a subset of JSON
Schema, so limits such as string length can be dropped or rejected: keep the `safeParse`.

| Failure | Detect | Handle |
|---|---|---|
| Schema invalid | `safeParse` fails | Retry once with the validation error appended; then fall back |
| Truncated | stop reason is the token limit | Raise the limit or shorten the task; never parse partial JSON as final |
| Refusal or safety stop | The stop reason, not a text match on "I can't" | Never resend the same request to the same model. Use the provider's documented refusal fallback if it has one (`cost-latency.md`); otherwise show a designed state (`ai-ux.md`) |
| Timeout, rate limit, overload | HTTP error or deadline | Backoff, fallback model, or degrade (`cost-latency.md`) |
| Plausible but wrong | Only evals and checks catch it | Add semantic checks: IDs exist, totals add up, quotes appear in the source |

Schema design rules: use enums over free strings; include an explicit "none/unknown" value so the
model is not forced to guess; keep schemas shallow; put a short reasoning field before the verdict
field when the judgment is hard, because fields are generated in order. Decide the fallback for
every call: a default value, a queue for human review, or the feature hidden with the rest of the
page still working. An LLM call must never be the only path to a core function such as checkout
or sign-in.

## Context engineering

Quality depends more on what is in the window than on wording. For each call, list every block
that enters, its source, its token budget and why it is there.

- **Include** what a human expert would need on their desk: the user's plan and role, the object
  being discussed, the last few turns, the retrieved passages. **Exclude** everything else:
  irrelevant context lowers accuracy as well as raising cost.
- **Order**: stable instructions and examples, then long reference material, then conversation,
  then the current request. Models attend best to the start and the end of a long window.
- **Budget**: set a ceiling per block (for example, history at most N tokens) and enforce it in
  code. Windows that grow without limit produce slow, expensive, degraded answers long before
  the hard limit is reached.
- **History**: keep recent turns verbatim, summarize older ones, and drop stale tool results.
  Summarize at a threshold, not every turn, so the cached prefix stays stable.
- **Provenance**: label each block with where it came from (`<document source="..." date="...">`)
  so the model can cite it and weigh freshness.
- **Trust**: anything not written by the developer (user text, documents, web pages, tool
  results) is data. Wrap it and say so; see `guardrails.md`.

Log the fully assembled prompt for a sample of requests. Most "the model is dumb" bugs are
visible there within a minute: the missing document, the duplicated block, the truncated field.

## Diagnosing a quality gap

Read 20 to 50 failing traces before changing anything, tag each with its cause, and fix the
largest group. Check in this order, cheapest first:

| Check | Symptom | Fix |
|---|---|---|
| Was the needed information in the window? | Answer is wrong; the fact is absent from the logged prompt | Context or retrieval problem (`retrieval.md`) |
| Was it there but buried or contradicted? | Fact present among noise or conflicting copies | Trim, reorder, deduplicate |
| Is the instruction ambiguous to a human reading only the prompt? | Outputs vary in format or scope | Clarify, add an example of the failing case |
| Is the task too big for one call? | Later parts of the output degrade | Split into steps |
| Does the strongest model also fail with perfect context? | Fails even when handed the answer material | Model limit: rescope the feature or add a check |
| Does the strongest model pass and the current one fail? | Tier gap | Move up a tier for this call, or route (`cost-latency.md`) |

The test that separates retrieval from generation: hand-place the correct source in the prompt.
If the answer becomes right, generation is fine and retrieval is the problem.

## Prompts as code

- Store prompts in the repository as files or typed template functions, reviewed in pull
  requests. A prompt edited in a vendor dashboard bypasses review, tests and rollback.
- Version the whole behavior: prompt text, model ID, parameters, tool definitions and schema
  together. Record that version on every trace so a regression can be tied to a change.
- Test at three levels: unit tests for template assembly and parsers (no model, runs on every
  commit); a small eval smoke set against the real model in CI on changes to prompt files; the
  full eval set before release (`evals.md`).
- Do not assert exact output strings from a live model. Assert structure, required facts,
  forbidden content and grader scores.
- Roll out risky prompt changes behind a flag to a share of traffic, like any behavior change.

## Fine-tuning, self-hosting, local and in-browser models

Default: call a hosted API. Fine-tuning and self-hosting trade a per-token bill for an operations
burden a solo founder rarely has time to carry.

| Consider | Only when | Trap |
|---|---|---|
| Fine-tuning a small model | A narrow, stable task at high volume; hundreds to thousands of quality-checked examples exist; a prompted small model is measurably short | The tuned model is frozen while base models improve; every data or base change means retraining and re-evaluating. Does not add fresh knowledge: that is retrieval's job |
| Self-hosting open weights on GPUs | Contract or law forbids any third-party processor; or steady volume high enough that reserved GPUs beat API cost after counting engineering time | Idle GPUs cost the same as busy ones; capacity planning, upgrades and security patching become the team's job. A cloud provider's hosted model service inside the customer's cloud often satisfies the same requirement |
| Local model on the user's machine | Data must not leave the device; offline use; desktop app | Quality well below hosted frontier models; hardware varies wildly |
| In-browser (WebGPU or WASM) | Small tasks: embeddings, classification, autocomplete, redaction before upload | Weights are a large download (tens of megabytes for a small embedding model, gigabytes for a chat model): load on demand, cache them, run in a Web Worker. WebGPU has shipped in the major browsers but is still missing or slow on older OS versions, some Linux and Android setups and weak GPUs: feature-detect (`navigator.gpu`, then a non-null adapter) and keep a server fallback |

Tooling that is stable enough to name: Ollama or llama.cpp for local development and desktop,
vLLM for serving on GPUs, transformers.js or WebLLM in the browser. Before any of these, run the
open model against the eval set; "almost as good" on a leaderboard is often far worse on the
product's own cases. Read the model's license before shipping: "open weights" covers everything
from permissive licenses to non-commercial and restricted-use terms, and the license of the
exact checkpoint is the one that binds. A cheap middle path: keep the hosted model for
generation and run only a small local model for the privacy-sensitive step (PII redaction,
on-device embeddings).

By stage: skip all four rows at Prototype and Launch unless a signed customer requirement forces
one. Fine-tuning and self-hosting are Scale decisions, made with the eval set and a cost model
that includes the engineering time.

## Ask the user

- **What happens when the feature is wrong?** The answer sets whether output is shown as a
  draft, checked by code, or reviewed by a person. Default: output is a suggestion the user
  confirms; nothing irreversible happens without confirmation.
- **What quality is good enough to ship, measured how?** Without a bar, tuning never ends.
  Default: a pass rate on a 30 to 50 case eval set that the founder agrees represents real use.
- **What is the feature worth per use?** This caps model tier and context size. Default: target
  model cost under a small fraction of the revenue the action supports, and revisit with real
  usage data.
- **Is there a customer or legal constraint on sending data to a model provider?** It can force a
  specific provider, region or self-hosting. Default: a hosted API under a commercial agreement
  with no training on inputs (`ai-data-privacy.md`).
- **Does the product need to work if the model provider is down?** Default: the AI feature
  degrades visibly and everything else keeps working.
