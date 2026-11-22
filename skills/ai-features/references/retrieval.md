# Retrieval over your own data

Read this when: answers must be grounded in documentation, a knowledge base or customers' own
data; building or fixing a RAG pipeline; retrieval returns the wrong passages; or search results
must respect who is allowed to see what.

## Retrieval, long context or a tool call

| Situation | Use | Why |
|---|---|---|
| Corpus fits comfortably in the window (a rule of thumb: up to roughly 100 pages) and is shared by all users | Put it all in the prompt, cached | No pipeline, no retrieval misses. Do the arithmetic first: corpus tokens times the cached-read price times requests. At low traffic the cache expires between requests, and each one then pays full input price and waits for the whole corpus to be read |
| Corpus is large, or differs per user or tenant | Retrieval | Only the relevant slice can enter the window |
| The answer is a fact in a database (order status, usage, balance) | Tool call running a query | Embedding rows of structured data gives stale, approximate answers to exact questions |
| The answer needs an aggregate ("how many", "top five", "total") | Tool call (SQL, analytics API) | Top-k retrieval sees k chunks, never the whole set |
| Live or fast-changing data (inventory, prices, tickets) | Tool call | An index is always behind |
| The user names the document ("summarize this PDF") | Load that document directly | Nothing to search for |
| Open question across many documents, multi-hop | Retrieval exposed as a search tool the model may call several times | One fixed query misses follow-up needs |

Default at Prototype: whole-document context if it fits, otherwise Postgres with `pgvector` and
full-text search in the existing database. Before Launch: hybrid search, the permission filter
with its cross-tenant test, delete propagation and the reconciliation job; add a reranker and a
labeled retrieval set as soon as answers miss. A dedicated vector database is a Scale decision;
index types and tuning belong to `0x:data-stores` (`search.md`).

## The pipeline, with the decisions that matter

```
source -> parse -> chunk (+metadata) -> embed -> index
query  -> [rewrite] -> filter by permission -> hybrid search -> rerank -> assemble -> generate with citations
```

**Chunking.** Split on the document's own structure (headings, sections, list items, table rows,
code blocks), not on a fixed character count. A workable starting size is a few hundred tokens
per chunk with a small overlap; tune on the retrieval eval, not by intuition. Chunks that are too
small lose the context that makes them findable; too large and one embedding blurs several topics
and the window fills with noise.

Every chunk needs enough context to stand alone. A chunk reading "This limit does not apply to
annual plans" is unfindable and unusable. Prepend the document title and heading path to the text
that is embedded and indexed; for higher recall, generate a one- or two-sentence description of
where the chunk sits in its document (a small model with the document cached does this cheaply at
ingestion) and prepend that as well.

**Metadata on every chunk**: tenant ID, source document ID, access-control fields, source URL or
location (page, heading anchor), title, last-modified time, content hash, embedding model version.
The first three are security; the rest make citation, freshness and re-indexing possible.

**Embeddings.** Use one model for documents and queries; if it has separate document and query
modes, use each for its side. Anthropic does not offer its own embedding model (its
documentation points to Voyage AI); pick a dedicated embedding provider, check current options,
and treat it as one more vendor that receives customer text (`ai-data-privacy.md`). Record the
model and version per row: changing the
model means re-embedding everything, because vectors from different models are not comparable.
Check multilingual support if users write in more than one language.

**Query side.** In chat, the latest message alone ("and for the annual plan?") is a bad query.
Rewrite it into a standalone query using the conversation, with a small model, before searching.

**Assembly.** Pass 5 to 20 chunks, each wrapped with its ID and source, ordered by document and
position so adjacent chunks read naturally. Deduplicate near-identical chunks. Merge neighbors
from the same section instead of sending fragments.

## Permissions inside retrieval

The rule: a chunk may enter the prompt only if the requesting user could open its source
document right now. The model cannot be trusted to withhold text it was given, so filtering after
generation, or instructing the model "do not reveal other customers' data", is not a control.

- Apply tenant and access filters **in the search query**, as a mandatory `WHERE` clause or
  filter derived from the server-side session, never from model output or client input.
- With Postgres, enforce it twice: the filter in the query and row-level security on the chunks
  table, so a forgotten filter returns nothing instead of everything. Trap: the table owner,
  superusers and roles with `BYPASSRLS` skip policies, so an application that connects as the
  owner gets no protection unless the table has `FORCE ROW LEVEL SECURITY`. Connect as a
  separate non-owner role and prove it with the test below (`0x:backend-architecture`,
  `multi-tenancy.md`).
- Filter before the top-k cut. Fetching the top 20 globally and then discarding forbidden rows
  leaks nothing but silently returns too few results. Approximate vector indexes do the same
  thing internally: with a `pgvector` HNSW index the `WHERE` clause is applied after the index
  scan, so a small tenant can get three rows back when twenty were asked for. Turn on iterative
  index scans (`hnsw.iterative_scan`, pgvector 0.8 and later), or partition or partially index
  by tenant, and measure filtered recall.
- Document-level sharing that changes often (folders, per-user grants): store the access-control
  list on the chunk and update it when sharing changes, or check candidates against the
  authorization service at query time. A revoked share must take effect on the next query, not
  at the next re-index.
- Caches are part of the path: key any retrieval or answer cache by tenant and by the
  permission set, or one user's cached answer is served to another.
- Never build one shared index for "efficiency" without a tenant column on every row. For
  enterprise customers, a per-tenant index or namespace makes deletion and isolation provable.

Test it: an automated test in which user A asks for content that exists only in tenant B's
documents, asserting zero chunks returned. Run it in CI.

## Parsing

Retrieval quality is capped by parsing quality. Inspect the parsed text of ten real documents
before tuning anything else.

| Source | Approach | Trap |
|---|---|---|
| HTML | Extract main content; drop navigation, footers, cookie banners; keep headings and anchors | Boilerplate repeated on every page dominates search results |
| Markdown, docs sites | Split on headings; keep code blocks whole | Splitting inside a code block or table |
| PDF with text layer | Layout-aware extraction; preserve reading order and page numbers | Multi-column pages read across columns; headers and footers repeated in every chunk; hyphenation |
| Scanned PDF, images | OCR or a vision-capable model to transcribe | Silent garbage text; verify a sample |
| Tables | Keep the table whole as Markdown or HTML with its caption and header row; for big tables, one chunk per row with headers repeated | A row without headers is meaningless numbers |
| Spreadsheets, CSV, database exports | Do not embed; load into tables and expose a query tool | Aggregates over embedded rows are wrong |
| Slides, diagrams | Vision model description plus any text | Meaning lives in layout the text extractor drops |

For complex PDFs (tables, forms, figures), sending the page images or the PDF itself to a
vision-capable model at ingestion gives cleaner text than heuristic extractors, at a per-page
cost; do it once at ingestion, not per query. Keep the original file and the parser version so
documents can be reprocessed when the parser improves.

## Hybrid search and reranking

Vector search finds paraphrases and misses exact tokens: error codes, product names, SKUs, IDs,
rare terms. Keyword search (BM25 or Postgres full-text) does the opposite. Run both and fuse.

- **Fusion**: reciprocal rank fusion needs no score calibration: for each document, sum
  `1 / (k + rank)` over the result lists, with `k` around 60, and sort by the sum.
- **Rerank**: retrieve a wide candidate set (50 to 150), score each candidate against the query
  with a reranking model, keep the best 5 to 20. A reranker reads query and passage together and
  is usually the largest single precision gain. It adds a network hop and a model pass per
  query, with latency that grows with the candidate count; measure it against the budget.
- **Order of investment**: fix parsing and chunk context, add keyword search and fusion, add a
  reranker, then consider query rewriting or multiple query variants. Changing the embedding model
  comes late; it rarely fixes what the earlier steps did not.
- **Metadata filters** (product, version, language, date) cut more noise than any ranking trick
  when the query or the user's context supplies them.

Skip until measured need: knowledge graphs, fine-tuned embedding models, multi-vector indexes.

## Keeping the index fresh

A stale index gives confident answers from deleted or outdated text, and deleted customer data
that still appears in answers is a privacy incident.

- Treat the index as derived data with the source as truth. Store source ID, content hash and
  indexed-at on every chunk.
- **Updates**: on a source change event (webhook, database trigger, queue message), re-parse, and
  re-embed only chunks whose hash changed. Replace a document's chunks in one transaction so
  queries never see half of it.
- **Deletes**: propagate deletion to chunks, embeddings, caches and any stored summaries. Delete
  by source ID; this is why the ID is mandatory metadata. Deleting a tenant must delete its index.
- **Reconciliation**: events get lost. Run a scheduled job that compares source IDs and hashes
  with the index, repairs differences and reports the count. A nonzero count every night means
  the event path is broken.
- **Permission changes** are freshness events too and need the shortest lag.
- **Versioned content**: tag chunks with product version or validity dates and filter, or old
  docs outrank current ones. Prefer recency as a tiebreak when sources conflict, and pass dates
  to the model.
- Run ingestion as background jobs with retries and a dead-letter state
  (`0x:backend-architecture`, `background-jobs.md`). Show indexing status in the UI for
  user-uploaded documents: "still processing" beats a wrong answer.

## Grounded answers, citations and declining

Prompt structure that makes the model stay inside the sources:

```text
Answer using only the documents in <documents>. Users act on these answers without checking,
so an unsupported answer is worse than none.
- Support each claim with the ID of the document it comes from, like [doc_3].
- If the documents do not contain the answer, say so, state what is missing, and offer the
  next step (contact support, rephrase). Do not answer from general knowledge.
- If the documents conflict, say so and cite both.
```

Layers, since the prompt alone is not enough:

1. **Before generation**: if retrieval returns nothing, or the best reranker score is under a
   threshold tuned on the eval set, skip the model and show the empty-retrieval state
   (`ai-ux.md`). This is the most reliable way to decline and the cheapest.
2. **In generation**: require citations per claim. Where the provider offers a native citations
   feature that returns the quoted span (Anthropic's API does), use it: a quote can be checked
   against the source in code, a bracket ID only for existence. Check whether it combines with
   schema-constrained output on the same call before designing around both.
3. **After generation**: verify in code that every cited ID was in the provided set and, for
   quoted spans, that the quote occurs in the source. Drop or flag answers with no valid citation.

Citations must resolve to something the user can open: a URL with anchor, or document and page.
Generate links from stored metadata, never from model-written URLs, which are often invented.
Include "unanswerable" questions in the eval set and measure the decline rate on them; without
them, prompt tuning drifts toward always answering.

## Evaluating retrieval separately

End-to-end answer quality hides which half failed. Build a retrieval set: 50 to 200 real
questions, each labeled with the chunk or document IDs that contain the answer. Start from
support tickets and search logs; label by document if chunk labels are too costly, because
document labels survive re-chunking.

| Metric | Question it answers | Use |
|---|---|---|
| Recall@k | Is at least one (or each) needed source in the top k? | The first number to fix; a missing source cannot be recovered downstream |
| Precision@k | How much of the top k is relevant? | Noise cost; drives rerank and k choices |
| MRR or nDCG | How high do relevant sources rank? | Compare rankers |
| Decline accuracy | On unanswerable questions, does the pipeline abstain? | Threshold tuning |

Measure recall at the candidate stage (top 50 to 150) and again after reranking (top 5 to 20):
low candidate recall is a parsing, chunking or search problem; a drop after reranking is a
reranker or cutoff problem. Then measure generation with retrieval held fixed, including a run
with the labeled sources hand-placed, which gives the ceiling for answer quality. Re-run the
retrieval set on every change to parser, chunker, embedding model or ranking.

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Exact names and codes not found | Vector-only search | Add keyword search and fusion |
| Right document, wrong passage | Chunks lack context or are too large | Heading path prefix, contextual descriptions, smaller chunks, rerank |
| Navigation text or legal footer in every result | Boilerplate not stripped | Fix parsing; deduplicate by hash |
| Answers cite an old policy | No versioning or stale index | Validity metadata, reconciliation job |
| Good in testing, poor in chat | Follow-up questions searched verbatim | Query rewriting from history |
| "How many customers ..." answered wrongly | Aggregate over top-k | Route to a SQL tool |
| Another tenant's content appears | Filter missing or applied after search | Mandatory filter plus row-level security; add the cross-tenant test |
| Quality fell after switching embedding model | Mixed vectors in one index | Re-embed all; track model version per row |

## Ask the user

- **Which sources are in scope, and who owns each?** Sources decide parsers, sync method and
  permissions. Default: start with one high-value source (the help center or product docs).
- **Who may see what?** Per-tenant only, or per-user and per-folder inside a tenant? Default:
  mirror the product's existing authorization exactly; never broader.
- **How fresh must answers be?** Minutes, hours or a day sets event-driven versus scheduled
  sync. Default: event-driven for deletes and permission changes, hourly for edits.
- **What should happen when the sources do not cover the question?** Decline, hand off to
  support, or answer from general knowledge with a label. Default: decline and offer a handoff.
- **Must deleted customer documents disappear from answers immediately?** Default: yes, within
  the same request path as the deletion, with a nightly reconciliation as backstop.
