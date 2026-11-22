# Evaluations and quality monitoring

Read this when: about to change a prompt, model, tool or retrieval setup; a feature gives wrong
answers and it is unclear whether a change helped; choosing how to grade outputs; setting up
tracing, production review or an online comparison.

## The order of work

1. Collect real cases. 2. Read outputs and name the failure types. 3. Write graders for those
failures. 4. Change one thing. 5. Run the set, compare with the baseline. 6. Ship behind a flag,
watch production signals. 7. Add new failures to the set.

Tuning a prompt before step 1 exists is guessing: each fix for the case in front of the developer
silently breaks others, and nobody sees it.

## Building the eval set

**Start small and real.** 20 to 50 cases are enough to begin; a set that exists beats a perfect
one planned. Grow to a few hundred as failures arrive.

Sources, in order of value:

| Source | Use |
|---|---|
| Production traces (after Launch) | Sample at random for the common case, then oversample thumbs-down, retries, edits, escalations |
| Support tickets, search logs, sales calls | Real phrasing of real needs before the feature exists |
| The founder's own list of "it must handle this" | Requirements as cases |
| Synthetic cases written by a model | Coverage of rare branches only; review every one; never the majority |

Composition that keeps the set honest:

- **Common cases** in proportion to real traffic, so the score predicts user experience.
- **Hard and boundary cases**: ambiguous input, missing data, very long input, other languages,
  typos, two requests in one message.
- **Should-decline cases**: out of scope, unanswerable from the sources, unsafe requests.
  Without these, tuning drifts toward always answering.
- **Adversarial cases**: injection attempts and abuse (`guardrails.md`).
- **Regressions**: every bug fixed becomes a case, like a regression test.

Each case stores: the input exactly as the call site receives it (including context and
retrieved material, or the means to reproduce them), what a good output must and must not
contain, tags (feature, failure type, source) and, where one exists, a reference answer. Write
expectations as checkable criteria ("mentions the 30-day window", "does not promise a refund"),
not as one golden string.

Read outputs before writing graders. Open 50 results, write a one-line note on each failure,
group the notes into five to ten failure types, count them. That list is the roadmap, and each
type becomes a grader. Generic metrics chosen up front ("helpfulness 1 to 5") measure nothing
the product cares about.

Keep the set in the repository (or a versioned store), strip or pseudonymize personal data when
importing from production (`ai-data-privacy.md`), and hold back a slice that is never looked at
while tuning, to detect overfitting to the visible cases.

## Graders

Use the cheapest grader that measures the failure. Most suites mix all four.

| Grader | Good for | Limits |
|---|---|---|
| Code checks: schema valid, enum value, exact or normalized match, regex, contains or excludes, length, cited ID exists, quote occurs in source, numeric tolerance, tool called with expected arguments | Classification, extraction, format, grounding, tool use | Cannot judge meaning or tone |
| Reference comparison (similarity to a gold answer) | Narrow tasks with one right answer | Penalizes correct answers phrased differently; weak signal for open tasks |
| LLM judge with a rubric | Faithfulness to sources, completeness, tone, policy adherence | Must be calibrated (below); costs tokens; drifts with judge model changes |
| Human review | Calibrating judges, new failure discovery, high-stakes domains | Slow and expensive; use on samples |

Rules for LLM judges:

- One criterion per judge, with a binary or three-level verdict (pass, fail, unsure). Numeric
  1 to 10 scales produce noise nobody can interpret.
- Give the judge the input, the output, the relevant sources and the criterion with examples of
  pass and fail. Ask for the reasoning first, then the verdict, as structured output.
- Use a strong model for judging, and where practical a different model from the one being
  judged: models tend to rate their own output favorably. Pin the judge model version; a judge
  change is a measurement change.
- Grade outcomes, not paths: for agents, check the final state (was the right record changed,
  was the forbidden tool never called), not a required sequence of steps, unless the sequence
  itself is the requirement.

For agents and multi-turn features, also record per run: task success, steps, tool errors,
tokens and wall time. A change that keeps success and halves steps is a win the pass rate hides.

## Regression testing changes

- **One change at a time**, against a stored baseline of the current production configuration.
- **Compare per case**, not only the aggregate: list cases that flipped pass to fail and fail to
  pass. A flat total often hides ten fixes and ten new breaks. Read the flips.
- **Know the noise.** With 100 pass/fail cases the 95% interval on a pass rate near the middle
  is about plus or minus 10 points (about 18 points with 30 cases; narrower near 0% or 100%);
  a 3-point move on a small set is not a result. Either grow the set, or use the paired view
  (a sign test): among cases where the two versions disagree, is the split clearly lopsided?
  Ten against two is about the weakest split worth believing; six against four is noise.
- **Handle nondeterminism.** Run each case several times (three to five) where outputs vary,
  and report the pass fraction. Setting temperature to 0 does not make outputs repeatable, and
  some models do not accept it. Treat a case that passes two times in three as failing for
  anything safety-related.
- **Tiers in CI**: unit tests without a model on every commit; a smoke set of 10 to 30 cases
  with cheap graders on pull requests that touch prompts, tools, schema, model ID or retrieval
  code; the full set before release and on a schedule. Cache model responses keyed by the full
  request so unchanged cases cost nothing.
- **Gates**: hard-fail on safety and format criteria; treat quality scores as thresholds with a
  margin, reviewed by a person when they drop. Do not block merges on a metric with more noise
  than the change being measured.
- **Model upgrades are changes.** Re-run the full set before moving to a new model version,
  and expect prompts tuned for the old model to need edits (`cost-latency.md`).

Tooling: at Prototype a script that loops over a JSONL file and writes a results table is
enough. Adopt an eval framework or platform (Promptfoo, Braintrust, Langfuse, Inspect and
similar) when the set, the graders or the number of people outgrow the script; the method
matters more than the tool. Ownership in this market moves (in 2026 OpenAI announced the
purchase of Promptfoo and ClickHouse bought Langfuse; both stayed open source), so keep cases
and graders in portable files, and treat any hosted platform that stores prompts and outputs as
a vendor receiving customer data (`ai-data-privacy.md`).

## Tracing

Trace every model call and tool call from Launch on. Without traces, a user report of "it said
something wrong" cannot be investigated.

Use the OpenTelemetry GenAI semantic conventions so traces work with any backend and sit in the
same trace as the HTTP request and database spans (`0x:site-reliability` owns the telemetry
pipeline). The conventions still carry "Development" status, moved to their own repository in
2026, and have renamed attributes before (`gen_ai.system` became `gen_ai.provider.name`). So
prefer a maintained instrumentation library over hand-written names, pin its version, and read
the current specification before building dashboards on an attribute. The core that has held:

| What | Convention |
|---|---|
| Span per model call | Named by operation and model (`chat` plus the model name); `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model` |
| Token usage | `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`; record cache-read and cache-write token counts as well, under the names the current specification gives |
| Outcome | `gen_ai.response.finish_reasons`, `error.type` |
| Tool execution | A child span per tool call (`execute_tool` plus the tool name) with `gen_ai.tool.name` |
| Agent run | A parent span for the whole run; `gen_ai.conversation.id` or the product's run ID on every span |

Add the product's own attributes on every span: prompt version, feature name, tenant ID, user
ID (or a pseudonym), eval-relevant flags (retrieval empty, fallback used, guardrail tripped) and
computed cost. These are what make the traces answer product questions.

Prompt and completion content is sensitive. The conventions treat content capture as opt-in;
decide deliberately: store content in a store with access control, redaction and a retention
period (`ai-data-privacy.md`), not in general-purpose logs that every engineer and vendor reads.
Record time to first token and total duration as separate measurements.

## Reviewing production output

Graders on a fixed set cannot see what users actually send.

- **Sample and read.** A fixed weekly session (a rule of thumb: 30 minutes, 50 traces) by the
  founder finds more than any dashboard. Sample randomly, plus every trace with a negative
  signal, a guardrail trip, a fallback, or an unusually long or costly run.
- **Run cheap graders online** on all or a sample of traffic: format validity, citation
  validity, decline rate, a faithfulness judge on a sample. Chart them per prompt version; a
  step change on deploy day is a regression.
- **Scan for the three bad classes**: wrong (unsupported claims, failed checks), harmful
  (policy violations, unsafe advice for the domain), leaked (other tenants' data, secrets,
  system prompt, personal data that should not appear). Leak detection is partly mechanical:
  search outputs for other tenants' identifiers, key patterns and canary strings.
- **Alert** on rates, not single events: decline rate, error rate, guardrail trips, cost per
  request, each against its own baseline.
- **Close the loop**: every confirmed failure gets a tag and goes into the eval set.

## User signals

Explicit ratings are sparse (a small share of responses) and skewed toward complaints. Implicit
signals are far more plentiful; instrument both and attach them to the trace ID.

| Signal | Meaning | Caveat |
|---|---|---|
| Thumbs down, with an optional reason | Clear failure candidate | Low volume; always read the reason |
| Regenerate or retry | Output not acceptable | Sometimes curiosity |
| Edit before use, and how large the edit | Draft quality; edit distance is a continuous quality measure | Heavy editing may be personal style |
| Copy, insert, accept, send | Output was useful | Acceptance without reading happens |
| Rephrase of the same question | Misunderstood or unhelpful answer | Needs similarity detection |
| Abandon, or escalate to a human | Feature failed the task | Confirm with the downstream outcome |
| Downstream outcome (ticket resolved, record kept, undo pressed) | The real goal | Lags; needs joining to product data |

Signals are leads, not labels. Review flagged traces, decide what the right output would have
been, and only then add the case with its expectation to the set. Edited outputs are valuable:
the user's final text is a reference answer for free. Keep the set's common-case slice a random
sample so it does not become a museum of only bad days.

## Calibrating an LLM judge

A judge is a classifier and needs its own measurement before its scores are trusted.

1. Have a person with domain knowledge (at this stage, the founder) label 50 to 100 outputs
   pass or fail per criterion, with a one-line reason. Include enough failures: aim for at
   least 20 to 30 of each class.
2. Split the labels: one part to develop the judge prompt (the reasons become its examples), one
   part held out to measure it.
3. Run the judge on the held-out part and compute agreement **per class**: the share of human
   "fail" it catches and the share of human "pass" it agrees with. Raw accuracy misleads when
   90% of outputs pass: a judge that always says "pass" scores 90%.
4. Read the disagreements. Usually the criterion was vague; sharpen the rubric, then re-measure.
   Sometimes the human label was wrong; fix it.
5. Decide how the judge is used from its error profile: a judge that misses failures cannot
   gate releases; one that over-flags can still triage traces for human review.
6. Re-check on fresh labels whenever the judge prompt, the judge model or the product's output
   style changes, and on a schedule.

If two people label, measure their agreement first. Where humans disagree, the criterion is not
defined well enough for any judge.

## Online comparison

Offline evals say a change is not worse on known cases; only production says whether users are
better served. Run an online test for changes that matter (new model, new prompt strategy, new
retrieval) once traffic allows; mechanics of assignment and statistics are in
`0x:product-analytics`.

- Assign by user (or tenant for shared features), sticky, through the feature-flag system;
  record the variant on every trace.
- **Primary metric**: a behavior tied to value: acceptance rate, task completion, resolution
  without escalation, retention of the generated artifact. Not thumbs-up rate alone.
- **Guardrail metrics**, which must not get worse: cost per request, time to first token and
  total latency (p50 and p95), error and fallback rate, decline rate, guardrail trips, negative
  feedback rate. A variant that wins on acceptance and doubles cost is a pricing decision, not a
  winner.
- Decide the stopping rule and minimum sample before starting. With low traffic, prefer a
  staged rollout with guardrail monitoring over an underpowered A/B test, and rely on the
  offline set plus trace review for the quality judgment.
- Shadow mode (run the new version on live inputs without showing its output) gives real-input
  evaluation with zero user risk, at double the token cost; never use it for calls with side
  effects.

## Ask the user

- **What does "good" mean for this feature, in the user's terms?** Graders encode this.
  Default: draft criteria from the first 50 reviewed outputs and have the founder confirm them.
- **Who labels?** Calibration needs a person with domain judgment. Default: the founder, an
  hour up front and 30 minutes weekly.
- **Which failures block a release outright?** Default: any safety, privacy or cross-tenant
  failure blocks; quality scores gate with a margin.
- **May production prompts and outputs be stored and read for review?** This is a privacy and
  contract decision. Default: store with redaction and a short retention, restricted access,
  and say so in the privacy documentation.
- **How much may evals cost per month?** Default: smoke set on relevant pull requests, full set
  before releases, with response caching.
