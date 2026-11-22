# Data handling for AI features

Read this when: deciding what customer data may be sent to a model provider; reviewing a
provider's retention and training terms; redacting prompts and logs; setting retention for
prompts, outputs and traces; building opt-out, deletion and admin controls; answering a
customer's security questionnaire about AI; or facing a regional processing requirement.

This file covers engineering and product practice. Whether a specific use is lawful, what a
contract must say and which regulations apply (GDPR, sector rules, the EU AI Act) are questions
for `0x:privacy-compliance` and, where stakes are real, a qualified lawyer.

## The model provider is a subprocessor

Sending customer data to a hosted model is the same act as sending it to any other vendor that
processes it: it needs a contract, a place in the subprocessor list, and a purpose the customer
agreed to. What differs is that prompts tend to sweep in far more data than intended (whole
records, whole documents, whole conversations) and that copies multiply: provider logs, the
product's own traces, eval sets, caches, embeddings.

Map every flow before Launch:

| Copy of the data | Where | Who can read it |
|---|---|---|
| Request and response at the provider | Provider's systems, for their retention period | Provider, under their terms |
| Prompt and output in traces | Observability or LLM-tracing vendor | Engineers, that vendor |
| Stored conversations and generated content | Application database | Users, support |
| Embeddings and chunks | Vector index | Application; treat as the source data: embeddings are not anonymization |
| Eval sets and labeled examples | Repository or eval platform | Engineers, CI, that vendor |
| Caches | Redis, CDN, provider-side prompt cache | Application |
| Third-party tools called by an agent | Search, scraping, code sandboxes, MCP servers | Each of those vendors |

Every row is a place a deletion request must reach and a line in the data-flow document.

## What may be sent where

Decide by data class, per provider, and write the result down as a table the code enforces.

| Data class | Default |
|---|---|
| Public content, the product's own docs | Any contracted provider |
| Customer business content (documents, tickets, messages) | Providers under a commercial agreement with a data processing agreement, no training on inputs, and a listed subprocessor entry; only for features the customer has enabled |
| Personal data of the customers' end users | As above, minimized to what the task needs; check that the customer's agreement covers AI processing |
| Special categories and regulated data (health, biometrics, children's data, financial account data, government IDs) | Not without a specific legal basis and the matching contract (for US health data, a business associate agreement with the provider and every vendor in the path); otherwise block or redact |
| Secrets (passwords, API keys, tokens), full card numbers | Never. Strip in code before any prompt or log |
| Another tenant's data | Never in the same request context |

Rules that prevent the common mistakes:

- **Consumer chat products are not API terms.** Free or consumer tiers of AI products often
  have different training and retention terms from the commercial API. Use only the commercial
  API or a cloud platform's offering, under the business account, and forbid pasting customer
  data into personal chat accounts in the team's own practices.
- **Each provider is a separate decision.** A fallback provider, an embedding provider, a
  reranker, a speech-to-text service, a tracing vendor: each receives data and needs the same
  terms. A fallback that silently routes customer data to an unlisted vendor is a contract
  breach during an outage.
- **Send the fields the task needs**, selected explicitly, never `JSON.stringify(record)`.
  Summarizing a ticket does not need the customer's address and payment status.
- **Enforce the table in one place**: a single module through which all model calls go, taking
  the data class and tenant settings, applying redaction and choosing allowed providers. Call
  sites that reach the SDK directly bypass every control here.
- **Check the customer's side**: enterprise contracts sometimes forbid AI processing of their
  data, or require notice before a new subprocessor. Read existing agreements before turning a
  feature on for everyone.

## Vendor terms to secure

Read the provider's commercial terms, data processing agreement and data-usage documentation;
do not rely on a summary or on memory, since these terms are revised.

| Term | What to look for | Why |
|---|---|---|
| Training | Inputs and outputs are not used to train models by default, stated in the contract, not only in a blog post or a settings toggle | The first question in every security review |
| Retention | How long requests and responses are kept, for what purposes, and whether a zero-retention arrangement exists and for which endpoints and features | Sets the real deletion timeline |
| Exceptions | What is kept longer: content flagged for policy violations, abuse-monitoring samples, data sent through feedback or opt-in programs | Often longer than the headline number |
| Stateful features | Server-side stored objects (uploaded files, conversation or thread state, batch inputs and results, caches) have their own lifetimes and must be deleted explicitly | Easy to leave behind for good |
| Human review | Whether provider staff may read content, and when | Sensitive-data decisions depend on it |
| Subprocessors and regions | Where the provider processes, and who else is involved | Feeds the product's own disclosures |
| Security attestations | SOC 2 or ISO 27001 reports, breach notification terms | Requested in customer reviews |
| Confidentiality and ownership | The customer keeps rights to inputs and outputs | Standard, but confirm |

Zero-retention arrangements usually need approval from the provider, may exclude features that
store state, and remove the provider's ability to help debug a request. Ask for one when a
customer segment (healthcare, finance, enterprise) requires it, not by reflex.

Obtaining models through a major cloud platform (the hyperscalers' hosted model services) moves
the processing under an existing cloud agreement and region controls, which shortens some
enterprise reviews; feature availability and timing can differ from the provider's direct API.

Keep a dated copy of the terms relied on, and re-check on a schedule and whenever the provider
announces a policy change.

## Redaction and minimization

Order of preference: do not collect; do not send; pseudonymize; redact; then protect what remains.

- **Field selection first.** Building the prompt from an explicit allowlist of fields removes
  more personal data than any detector.
- **Pseudonymize identifiers the model does not need to read.** Replace emails, names, account
  numbers with stable placeholders (`<PERSON_1>`, `<EMAIL_2>`) before the call and map them back
  in the output. The mapping stays server-side, per request. The model still reasons about
  "the same person" without seeing who it is.
- **Pattern detection** for structured identifiers: emails, phone numbers, card numbers (with a
  Luhn check), national ID formats, API key and token patterns. Cheap, reliable for these, and
  run on both prompts and logs.
- **Entity detection** (a named-entity model or library such as Microsoft Presidio, or a small
  local model) for names and addresses in free text. Expect misses and false positives;
  measure on real samples. Redaction reduces exposure; it does not make free text anonymous.
- **Free-text inputs** are where users paste what they should not. For features that do not need
  it, detect card numbers and secrets client-side or at the edge and warn before submit.
- **Logs and traces are the bigger leak.** A prompt containing a customer's document, copied
  into general application logs, an error tracker breadcrumb and a tracing vendor, is three
  uncontrolled copies. Default: log metadata (tokens, model, latency, prompt version, IDs)
  everywhere; store content only in one access-controlled store with redaction applied and a
  retention period; scrub request bodies in the error tracker.
- **Eval sets from production**: pseudonymize on import, record the source trace for deletion,
  and prefer synthetic rewrites of real cases for anything that lives in the repository.
- **Quality trade-off**: over-redaction breaks the task (a reply draft needs the customer's
  name). Decide per feature what the model must see, and test the redacted pipeline on the eval
  set.

## Retention

Set a period for each store, enforce it with a scheduled deletion job, and state it in the
privacy documentation. Durations are a business and legal choice; the pattern below is a
common starting point, not a requirement.

| Store | Typical starting point | Notes |
|---|---|---|
| User-visible conversation history and generated content | Until the user or tenant deletes it, or an admin-set period | It is product data; offer deletion |
| Full prompt and output traces for debugging | Short: on the order of 30 days | Long enough to investigate reports, short enough to limit exposure |
| Trace metadata (tokens, cost, latency, versions) | A year or more | No content; needed for billing and trends |
| Eval cases derived from production | Until removed; reviewed periodically | Pseudonymized; linked to source for deletion |
| Response and retrieval caches | Hours to days | Keyed by tenant; purged on source deletion |
| Embeddings and chunks | Life of the source document | Deleted with the source |
| Provider-side copies | The provider's stated period | Outside direct control; disclose it |
| Abuse and security records | As the security policy says | Narrow content, restricted access |

Mechanics: a `created_at` and tenant ID on every row; partition or index for cheap bulk
deletion; the deletion job reports counts and alerts when it stops running; backups age out on
their own schedule, which is stated (`0x:data-stores`, `data-lifecycle.md`). Legal holds and
regulated retention override these periods; that is a legal determination.

## Customer controls

What customers expect once the buyer is a business, roughly in the order they are asked for:

| Control | Level | Behavior |
|---|---|---|
| Turn AI features off | Tenant (admin), optionally per feature | When off, no data from that tenant reaches any model provider: enforce at the single model-call module, not only by hiding UI. Background jobs and indexing stop as well |
| Per-user opt-out | User | Where the feature processes the user's own content |
| Exclude data | Tenant | Mark workspaces, projects or fields as never sent to AI |
| Delete AI data | User and tenant | Conversations, generated content, memory, embeddings, traces and eval cases derived from them; propagate to caches and provider-side stored objects |
| Retention setting | Tenant | Choose the period for conversation history |
| No training on customer data | Product-wide commitment | State it plainly; if the product ever trains or fine-tunes on customer data, make it explicit opt-in per tenant, because a trained model cannot forget on request |
| Audit log | Tenant admins | Who used AI features and which agent actions ran |
| Region or provider choice | Enterprise plans | See residency below |

Default new enterprise-relevant AI features to admin-controlled, and announce new AI data flows
before enabling them for existing customers: turning on AI processing for all tenants without
notice is how products lose enterprise accounts. A data-subject deletion request must reach
every row of the copies table; test it end to end with a canary record. Using customer data to
improve prompts by reading traces is processing too: cover it in the terms and restrict who may
read content.

## Documenting AI data flows

Security reviewers ask the same questions; answer them once in a maintained document (a page in
the trust or security documentation) and reuse it. Handling the questionnaire process itself:
`0x:sales-support`.

Contents:

1. **Features**: each AI feature, what it does, whether it is on by default, how to disable it.
2. **Data sent**: per feature, the categories of data in prompts, and what is excluded.
3. **Providers**: each model, embedding and AI-tooling vendor, what it receives, region of
   processing, link to its terms; all present in the subprocessor list.
4. **Training**: that customer data is not used to train the provider's or the product's models
   (state only what the contracts support).
5. **Retention**: the retention table above, including the provider-side period.
6. **Isolation**: how tenant separation is enforced in retrieval, caches and agent tools.
7. **Access**: who at the company can read prompts and outputs, under what controls.
8. **Security of AI behavior**: prompt-injection mitigations, output handling, human approval
   for actions, red-team practice (`guardrails.md`).
9. **Human oversight and labeling**: where AI output is marked and where a person decides.
10. **Customer controls** and how deletion works.
11. **Change process**: how customers are told about new providers or features, and the notice
    period the agreement promises.

A simple diagram (customer data → application → redaction → provider → response → stores) with
the retention on each arrow answers half the questionnaire. Keep it true: update it in the same
pull request that adds a provider or a new data flow, and review it when a provider changes
terms.

## Regional processing and residency

Requests take three forms; find out which one is being asked before building anything.

| What the customer means | What satisfies it |
|---|---|
| "Our data is stored in region X" | Application database, files, index, traces and backups in X. Inference may still run elsewhere unless they also mean the next row |
| "Our data is processed only in region X" | Inference in X as well: a regional endpoint or a cloud platform's regional model deployment, plus regional embedding, reranking, tracing and sandbox vendors |
| "Transfers out of our jurisdiction have a lawful mechanism" | Contract terms and transfer mechanisms rather than location: a legal matter for `0x:privacy-compliance` |

Engineering facts that decide feasibility:

- Not every model is offered in every region, new models reach regions at different times, and
  regional or pinned-region routing may be priced differently. Check current availability per
  model before promising.
- "Global" or cross-region routing options on cloud platforms improve capacity by letting the
  request run anywhere; they defeat a processing-location commitment. Choose the routing mode
  deliberately.
- The whole path counts: an EU-pinned model call with traces shipped to a US observability
  vendor is not EU processing. Audit every row of the copies table per region.
- Fallbacks must stay inside the region, or the feature degrades instead of falling back.
- Latency and rate limits differ per region; re-run load and eval checks there.
- Implement as a per-tenant setting that selects endpoint, vendors and stores in the single
  model-call module. Per-region deployments of the whole stack are a Scale decision.
- The strictest demands (no third-party processor at all, air-gapped) lead to self-hosted
  open-weight models (`feature-design.md`); price the operational cost into that deal.

Offer residency when a signed or near-signed customer requires it. Building it speculatively
costs months and constrains every later vendor choice.

## Ask the user

- **Who are the customers and what data will reach the model?** Consumer, small business,
  enterprise, regulated sector; personal or sensitive data. Default: treat all customer content
  as confidential business data containing personal data.
- **What do existing customer contracts and the privacy policy say about AI and subprocessors?**
  They may require notice or consent before launch. Default: add the provider to the
  subprocessor list and notify customers before enabling the feature.
- **Will customer data ever be used to improve the product's models or prompts?** Default: no
  training or fine-tuning on customer data; trace review by restricted staff only, disclosed.
- **How long should prompts and outputs be kept for debugging?** Default: about 30 days of
  redacted content in a restricted store, metadata longer.
- **Do any customers need a specific region, zero retention or a specific cloud?** Default:
  none until a real deal requires it; then scope it to that plan.
- **Is any regulated data in scope (health, children, financial)?** Default: block it from AI
  features until the legal basis and vendor agreements are confirmed by a professional.
