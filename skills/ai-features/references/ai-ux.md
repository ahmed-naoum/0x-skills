# AI interaction and streaming UX

Read this when: designing or building the interface for AI output: choosing between chat,
inline assistance and background automation; streaming with stop and retry; showing sources or
agent progress; rendering model-written markdown; or designing what users see when the model
refuses, times out or has nothing to go on.

## Choosing the interaction pattern

Chat is the default people reach for and often the wrong one: it makes the user do the prompt
writing, hides what the feature can do, and puts the result in a transcript instead of in the
work.

| Pattern | Fits | Costs |
|---|---|---|
| **Background automation**: the product does it without being asked (auto-tag, auto-title, triage, extract fields on upload) | Narrow, frequent task; errors cheap and visible; result lands in an existing field | Needs high precision, a visible "AI" mark, and one-click correction; silent wrong values erode trust in all data |
| **Inline assist**: a button or shortcut on the object ("summarize thread", "draft reply", "fix grammar", suggestions while typing) | The task is known and the context is the thing on screen | One prompt per action to maintain; needs a preview and accept or reject |
| **Generate into a form**: AI fills a structured draft the user reviews | Creating records, setup, onboarding | Review must be quick: highlight what AI filled in |
| **Chat or command box** | Open-ended questions, exploration, tasks nobody can predict, multi-turn refinement | Blank-box problem; long transcripts; hardest to evaluate; highest abuse surface |
| **Agent task**: delegate, watch, review | Multi-step work that takes minutes | Progress, control and review UI (below) |

Decision rules:

- If the top three uses can be named, build them as inline actions first. Add chat when users
  demonstrably need the open-ended remainder.
- Put the output where the work is (in the editor, on the record), not in a side transcript
  the user must copy from.
- Automation level follows error cost: suggest (user accepts), act with undo, act silently.
  Start one level more cautious than seems necessary and loosen with measured acceptance rates.
- If chat is right, never ship an empty box: show three to five example prompts taken from real
  use cases, state the scope in one line, and carry the current page's context automatically.
- AI must be optional on the critical path. The form still works by hand; the model being down
  blocks nobody.

## Streaming

Stream whenever the output takes more than about a second and is read by a person. Do not
stream output that is useless until complete and validated (a JSON object driving UI, a
classification): show a progress state, then the result.

**Transport.** A server route calls the provider and relays events to the browser; the provider
key never reaches the client. Server-sent events or a streamed `fetch` response is sufficient
(one-way, plain HTTP); WebSockets are unnecessary for this. Use a maintained streaming library
for the framework rather than hand-parsing chunks. Check that every proxy and platform layer in
between passes streams without buffering, and that the platform's function time limit exceeds
the longest expected response (`0x:backend-architecture`, `realtime.md`).

**State machine.** Model each response as: `idle → submitted → streaming → done | stopped |
error`. Most streaming bugs are missing transitions.

| Concern | Rule |
|---|---|
| Before the first token | Show an immediate pending state within 100 ms of submit; name the phase if there is one ("Searching docs") |
| Stop | A visible stop control replaces send while streaming. Abort the request client-side and propagate the abort to the provider call so generation and billing stop. Keep the partial text, marked as stopped |
| Double submit | Disable or queue send while a response is in flight; keep the user's draft text if the request fails |
| Mid-stream failure | Keep what arrived, mark it incomplete, offer Retry (replace) and, for long outputs, Continue. Never wipe a half-read answer |
| Truncation at the token limit | Detect the stop reason and say so, with Continue; do not present a cut-off answer as complete |
| Retry | Idempotent on the server: same message ID replaces the failed attempt, no duplicate user message, no repeated side effects |
| Persistence | Save the assistant message server-side when the stream ends or is stopped, including partial text and its status, so a reload shows the same thing |
| Reload or network drop mid-stream | For short answers, show the saved partial plus Retry. For long or agent runs, the work continues server-side as a job and the client re-attaches to its event stream |
| Navigation away | Decide explicitly: abort (cheap, most chats) or continue in the background and notify (long tasks) |

**Reading experience.**

- Auto-scroll only while the user is at the bottom; the moment they scroll up, stop following
  and show a "jump to latest" control. Yanking the viewport while someone reads is the most
  common complaint about streaming UIs.
- Avoid layout shift: reserve space, do not re-flow earlier content, and batch DOM updates
  (per animation frame or every few tens of milliseconds), not one render per token.
- Accessibility: do not announce every token. Mark the region busy while streaming and announce
  completion once (a polite live region with a short status such as "Answer ready"); make stop
  reachable by keyboard; respect reduced-motion for typing effects (`0x:accessibility`).
- Do not add fake typing delays. Speed is the point.

**Structured results while streaming.** If the UI needs fields, either stream prose first and
fetch the structure in a second small call, or stream a partial object through a library that
parses incomplete JSON and validates the final object against the schema. Never act on a partial
object.

## Failure states

Design these before the happy path is finished; they occur daily at any volume. Each needs
copy, a next action, and a trace ID behind it.

| State | What the user sees | Next action offered |
|---|---|---|
| Empty retrieval: nothing relevant found | "I couldn't find this in [the named sources]." Say what was searched | Rephrase, widen the sources, contact support. Do not let the model answer from general knowledge without saying so |
| Low confidence: weak retrieval score, failed verification, conflicting sources | The answer with a visible caution and the sources, or a clarifying question | Check the sources; refine the question |
| Ambiguous request | One clarifying question with tappable options | Choose an option |
| Refusal or safety stop | A neutral, non-accusing message that this request cannot be helped with here, and what the feature is for | Rephrase, or a human channel. No automatic retry |
| Out of scope | What the assistant can do, with examples | Example prompts |
| Timeout or provider error | Plain statement that the AI service is slow or unavailable; the partial output if any | Retry; the manual path |
| Rate or quota limit | What limit was reached and when it resets | Upgrade or wait |
| Validation failure after retries (structured output) | The feature's non-AI fallback: an empty form, the manual flow | Continue by hand |
| Agent stopped at a step or budget limit | What was completed, what remains | Continue, or take over |

Rules: never show a raw provider error or a stack trace; never show an endless spinner (every
wait has a timeout that lands in one of these states); never lose the user's input on failure;
distinguish "the system failed" from "the system declined" from "nothing was found", because the
user's next move differs. Confidence shown to users must come from a signal in code (retrieval
scores, verification checks, source count), not from the model's self-reported percentage.

## Showing sources

- Cite inline, next to the claim ([1] markers or linked phrases), with a source list below.
  A list of "sources" at the bottom of an answer with no link to specific claims cannot be
  verified claim by claim.
- Each citation opens the exact place: the page and passage, a heading anchor, or a preview
  with the quoted span highlighted. Opening the top of a 60-page PDF is not a citation.
- Show title, origin and date for each source; freshness is part of trust.
- Build links from stored retrieval metadata. Never render a URL the model wrote as a source:
  models invent plausible links.
- Show only sources the model was actually given and (where the pipeline verifies it) actually
  used; hide citations that fail the check instead of showing broken ones.
- Respect permissions at click time as well as retrieval time: the source link goes through the
  product's normal authorization.
- When nothing was retrieved, say so in the UI; an uncited answer in a product that normally
  cites should look different.
- For answers from structured data, show the query or filter that produced the number ("Based
  on 214 orders from March 1 to 31") so it can be checked.

## Edit, regenerate, steer

Accept-or-reject is the weakest interaction. Output is a draft; make reshaping it cheap.

| Control | Detail |
|---|---|
| Edit in place | Output lands in an editable field or the document itself. Track that a human edited it; keep edits when regenerating other parts |
| Regenerate | Keep previous versions reachable (a version switcher); never destroy a version the user may have preferred. Bypass any response cache |
| Quick adjustments | Shorter, longer, more formal, simpler: one-click chips for the top refinements seen in real use |
| Targeted revision | Select a passage and ask for a change to that part only; show the change as a diff the user accepts or rejects |
| Steer before generating | Tone, length, audience or template as explicit controls, remembered per user, instead of prompt-writing |
| Edit and resend the prompt | Editing an earlier message forks the conversation from there |
| Insert, copy, apply | A clear primary action that puts the result into the work; this is also the acceptance signal |
| Undo | Every applied AI change is one undo step |
| Feedback | Thumbs down with optional reason, attached to the trace |

Instrument every one of these: accept, edit distance, regenerate, chip used and undo are the
quality signals the eval loop feeds on (`evals.md`). For changes to existing content, show a diff,
not a replacement: users cannot review what they cannot see changed.

## Agent activity and control

A long silent spinner reads as broken; a wall of raw tool logs reads as noise.

- **Acknowledge immediately**, then show a plan or the first step within a second or two.
- **Show steps as a live list** in the user's vocabulary: "Searching invoices from March",
  "Reading 3 documents", "Drafting the summary". Current step active, completed steps checked,
  details (queries, tool inputs and results) collapsed but available for anyone who wants to
  verify.
- **Do not present raw reasoning as the answer.** If the model's reasoning is shown at all,
  collapse it and separate it visually from results.
- **Stop is always available**, takes effect at the next step boundary within seconds, and
  leaves a clear record: what was done, what was not, and what can be undone.
- **Approvals** interrupt in place with the exact action and its arguments (recipient, amount,
  the text to be sent), a primary approve, and reject or edit. The run waits durably
  (`agents-tools.md`); the user can leave and return.
- **Steer mid-run**: accept a new message while the agent works and apply it at the next step,
  rather than forcing stop and restart.
- **Survive a closed tab**: the run lives on the server; the page re-attaches from the step log;
  notify on completion or when approval is needed.
- **End with a review**: a summary of what changed, each change linked to its object, with undo
  where possible. An activity log of agent actions, marked as done by AI on the user's behalf,
  belongs in the product's history.
- **Show cost or effort** where runs are metered ("used 3 of 20 credits").

## Rendering model output safely

Model output is untrusted content (`guardrails.md` has the security reasoning). In the UI:

- **Markdown**: render with a maintained renderer in its safe configuration: raw HTML disabled,
  or passed through a sanitizer with a strict allowlist. In React, `react-markdown` does not
  render raw HTML unless a raw-HTML plugin is added; do not add it for model output. Never pass
  model output to `dangerouslySetInnerHTML`.
- **Links**: allow `http`, `https` and, if needed, `mailto`; open external links with
  `rel="noopener noreferrer"`; make the destination visible.
- **Images**: do not load arbitrary remote images from model output; allowlist hosts or drop
  them. This closes the main zero-click data-exfiltration channel.
- **Incomplete markdown during streaming**: an unclosed code fence, half a table or a dangling
  link is normal mid-stream. Use a renderer built to tolerate partial input, or close open
  constructs before rendering each frame, so the layout does not flash between states.
  Memoize completed blocks so only the last block re-renders; re-parsing the whole message per
  token makes long answers stutter.
- **Code blocks**: language label, copy button, horizontal scroll, syntax highlighting applied
  lazily (highlighting on every token is expensive). Never execute generated code in the page's
  own origin; previews run in a sandboxed iframe on a separate origin without access to
  cookies or the parent.
- **Math, diagrams, embeds**: each renderer is an attack and breakage surface; enable only what
  the feature needs, with the renderer's strict mode on.
- **Generated UI**: let the model choose among the product's own components by emitting data
  (a component name from an allowlist plus props validated against a schema), and render those.
  Do not render model-written HTML or JSX.
- **Limits**: cap rendered length and nesting; enormous or deeply nested output can freeze the tab.
- **Plain-text sinks** (email subject, notifications, CSV exports): strip markdown and escape for
  the destination format.

## Ask the user

- **Where in the workflow should the AI appear, and what are the top three things users want
  from it?** Decides inline actions versus chat. Default: inline actions for named tasks; chat
  only for the open-ended remainder.
- **Should AI act on its own, or propose and wait?** A trust and risk choice per action.
  Default: propose; the user applies; every applied change can be undone.
- **What should users see when the AI cannot answer?** Handoff to support, a search fallback
  or a plain decline. Default: say what was searched and offer the human channel.
- **Should the model's sources and steps be visible to end users?** Some products prefer a
  clean answer; verification needs the sources. Default: citations always, step details collapsed.
- **Is conversation history kept, and can users delete it?** Product and privacy decision
  (`ai-data-privacy.md`). Default: kept per user, deletable, removed with the account.
