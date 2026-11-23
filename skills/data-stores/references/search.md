# Search

Read this when: adding or improving product search, autocomplete, faceted filtering or vector
similarity lookup, or when search results are slow, irrelevant, stale or leaking across tenants.

## The ladder

Climb one rung at a time, and only when the current rung is measured as failing.

| Rung | Gives | Stops being enough when |
|---|---|---|
| 1. Trigram index (`pg_trgm`) | Substring and fuzzy match on short fields: names, titles, emails, SKUs | Long text, ranking by relevance |
| 2. Postgres full-text (`tsvector` + GIN) | Word search with stemming, field weights, ranking, phrase and exclusion syntax | Typo tolerance on body text, facets with counts, ranking slow on common terms |
| 3. Both combined | Full-text for recall, trigram for misspellings on the title | Search is a primary product surface and the above is tuned and still short |
| 4. Hosted search engine | Typo tolerance, facets, instant search, synonyms, ranking rules | — |
| Vector search (pgvector) | Similarity by meaning; orthogonal to the ladder, usually combined with rung 2 | See the pgvector section |

Rungs 1 to 3 have no sync problem, no extra system, and permission filters that are ordinary
`WHERE` clauses and joins. That is worth a great deal; do not give it up for features nobody
asked for.

## Postgres full-text and trigram

```sql
ALTER TABLE docs ADD COLUMN search tsvector GENERATED ALWAYS AS (
  setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
  setweight(to_tsvector('english', coalesce(body,  '')), 'B')
) STORED;
CREATE INDEX docs_search_idx ON docs USING gin (search);

SELECT d.id, ts_rank(d.search, q) AS rank
FROM docs d, websearch_to_tsquery('english', $1) AS q
WHERE d.tenant_id = $2 AND d.search @@ q
ORDER BY rank DESC
LIMIT 20;
```

- Use `websearch_to_tsquery` for user input. It accepts quotes, `or` and `-word` and never
  raises a syntax error; `to_tsquery` does on ordinary user text.
- Always pass the configuration name explicitly, in the column and in the query. The one-argument
  forms depend on a session setting, cannot be used in a generated column, and silently
  mismatch.
- `'english'` stems and drops stop words, which is wrong for names, codes and identifiers. Use
  `'simple'` for those fields. For accent-insensitive search, build a configuration with the
  `unaccent` extension.
- Ranking is computed for every matching row before the `LIMIT`. A query for a common word in a
  large tenant ranks hundreds of thousands of rows. This is the usual ceiling of rung 2;
  mitigate by narrowing with filters first, then accept it as the signal to move up.
- Prefix matching for as-you-type needs `to_tsquery('simple', 'repor:*')` built from sanitized
  tokens; full-text has no typo tolerance at all.

Trigram:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX customers_name_trgm ON customers USING gin (name gin_trgm_ops);
-- now indexed: name ILIKE '%acme%'   and   name % 'acmee'  (similarity)
```

Patterns shorter than three characters cannot use the index well; require a minimum length or
fall back to a prefix query. For "closest matches first" use a GiST index with `gist_trgm_ops`
and `ORDER BY name <-> $1 LIMIT 10`. To combine a tenant filter with a GIN index in one index,
add the `btree_gin` extension and index `(tenant_id, search)`.

## Tenant and permission filters

Search is a second read path into the data, and it bypasses whatever authorization the main
query layer has. Every leak described here has shipped in real products.

- **The filter is part of the query, added on the server from the session**, never taken from a
  client parameter and never applied after the engine returns. Post-filtering leaks through
  result counts, facet counts, pagination gaps, suggestions and highlights even when the rows
  themselves are hidden.
- **Every indexed document carries `tenant_id`** and whatever is needed to decide visibility
  (owner, team IDs, visibility level), declared as filterable attributes.
- **One function builds search requests.** No call site talks to the engine directly. That
  function refuses to run without a tenant.
- **Browser-direct search needs a scoped key.** If the frontend queries the engine itself (the
  instant-search pattern), mint a short-lived key on the server with the tenant filter embedded
  and signed: secured API keys in Algolia, scoped search keys in Typesense, tenant tokens in
  Meilisearch. A plain search-only key in a multi-tenant frontend lets any user query every
  tenant. An admin key in the browser is a full breach.
- **Shared index with a filter is the default.** One index per tenant suits a few very large or
  contractually isolated tenants; thousands of small indexes are an operating problem in most
  engines.
- **Row-level permissions:** denormalize the principals allowed to see each document (team IDs,
  not user IDs, to keep updates small) onto the document, and reindex when access changes. When
  the permission model is too dynamic to denormalize, fetch more candidates than needed and
  check each against the database before returning, accepting that counts become approximate
  and facets must be disabled or computed from the checked set.
- **Index only fields the least-privileged searcher may see.** Highlights and snippets quote
  whatever was indexed, including internal notes.
- **Autocomplete, suggestions, facets and vector queries take the same filter.** They are
  separate endpoints and are the ones usually forgotten.

Check: an automated test that creates two tenants with a document containing the same unique
word, searches as each through every search endpoint, and asserts neither sees the other's
document, count or suggestion.

## Choosing an engine

| Option | Fits | Operating burden | Watch for |
|---|---|---|---|
| Postgres (rungs 1–3) | Up to millions of rows per search scope with modest relevance needs | None added | Ranking cost on common terms; facets by `GROUP BY` |
| Meilisearch | Product and content search with typo tolerance and facets, small team | Low; hosted cloud available | Indexing is asynchronous; very large datasets and complex aggregations are not its target |
| Typesense | Same space; fast instant search | Low; hosted cloud available | The index lives in memory, so RAM must exceed index size |
| Algolia | Best-in-class hosted relevance and tooling, no operations | None | Usage-based price grows with records and searches; estimate at 10x volume before committing |
| Elasticsearch / OpenSearch | Tens of millions of documents and up, complex aggregations, custom analyzers, log-style data | High even when managed: shards, heap, mappings, version upgrades | A mapping cannot be changed in place; wrong shard counts are painful to fix |

Decision: if Postgres falls short at Launch, choose a hosted Meilisearch, Typesense or Algolia
by price at projected volume. Choose Elasticsearch or OpenSearch only for a need the others
cannot meet, and managed.

## Keeping the index in sync and rebuilding it

The database is the truth; the index is a projection that can be dropped and rebuilt.

**Sync.** Do not write to the engine from request code after the database write. The second
write fails independently and updates arrive out of order. Instead:

1. In the same transaction as the change, enqueue a job (Postgres-backed queue) or write an
   outbox row containing only the entity type and ID.
2. The worker loads the current row and upserts the document, or deletes the document if the
   row is gone or soft-deleted. Because it always writes current state, the job is idempotent
   and ordering does not matter.
3. Batch: engines index far faster in bulk than one document per request.
4. A reconciliation sweep (hourly or nightly) re-enqueues rows with `updated_at` after the last
   sweep and compares document counts per tenant with the database.

Traps: hard deletes leave nothing for a sweep to find, so deletion must emit its own job;
`ON DELETE CASCADE` removes child rows without any application code running; a renamed parent
(project name shown on every task) requires reindexing its children; bulk updates and
migrations run in SQL bypass application hooks, which is the case for change data capture
(`streams-pipelines.md`) at Scale.

Indexing is asynchronous in most engines. A user who creates an item and searches for it a
second later may not find it; show the new item optimistically or wait for the indexing task on
the paths where it matters.

**Rebuild without downtime.** Needed whenever analyzers, field types or document shape change.

1. Create a new index with a versioned name (`docs_v8`) and the new settings.
2. Start sending live changes to both old and new indexes.
3. Backfill the new index from the database in batches ordered by primary key.
4. Verify: document counts per tenant match, and the golden query set (below) passes.
5. Switch the alias the application reads (`docs`) to the new index in one atomic operation:
   an alias in Elasticsearch, OpenSearch and Typesense; an index swap in Meilisearch.
6. Keep the old index until the next day for rollback, then delete it.

The application always queries through the alias, never the versioned name. Know the full
rebuild time at current size; it is the recovery time if the index is lost.

## Autocomplete, facets and filters

Autocomplete, client side: debounce 150 to 250 ms, cancel the previous request with an
`AbortController`, ignore responses that arrive out of order, start at two characters, show
five to eight suggestions. Server side: target a p95 well under 100 ms (rule of thumb), since
latency is felt on every keystroke. Decide which kind is being built: query suggestions
(completing popular searches, from the search log) or instant results (matching records). In
Postgres, prefix autocomplete on one field is a B-tree index on `lower(name) text_pattern_ops`
with `LIKE 'acm%'`; fuzzy autocomplete is the trigram index.

Facets and filters:

- Declare filterable and facetable attributes explicitly; engines index only what is declared,
  and adding one later triggers a reindex.
- Store dates as numeric timestamps for range filters. Keep identifiers as exact-match fields.
- Facet counts are computed over the filtered result set. In Postgres that is a `GROUP BY` per
  facet over all matches, which is the first thing to become slow.
- Selecting a value inside a facet group should not make its sibling values vanish
  (disjunctive faceting). It costs one extra query per active group; engine client libraries
  do this, hand-rolled code usually does not.
- High-cardinality facets (author among 100,000) need a search-within-facet control, not a list.
- Deep pagination by offset is expensive everywhere. Cap reachable results (for example 1,000)
  and use cursor pagination for exports.

## Embeddings with pgvector

```sql
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE chunks ADD COLUMN embedding vector(1536);   -- must equal the model's dimension
CREATE INDEX chunks_embedding_idx ON chunks
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

SET hnsw.ef_search = 100;                               -- default 40; higher = better recall, slower
SELECT id FROM chunks
WHERE tenant_id = $2
ORDER BY embedding <=> $1
LIMIT 10;
```

- The operator must match the index operator class: `<=>` with `vector_cosine_ops`, `<->` with
  `vector_l2_ops`, `<#>` with `vector_ip_ops`. The index is used only for
  `ORDER BY <column> <operator> <value> LIMIT n` in ascending order; ordering by an expression
  such as `1 - (embedding <=> $1)` forces a full scan.
- **Filtering is the main trap.** The approximate index finds nearest neighbors first and the
  `WHERE` clause is applied afterward, so a selective filter can return fewer rows than the
  limit, or none. Options: for scopes of up to tens of thousands of rows, skip the vector index
  and let a B-tree on `tenant_id` narrow to an exact scan, which is fast and has perfect
  recall; enable iterative index scans (`hnsw.iterative_scan`) on pgvector versions that have
  them; partition or build partial indexes for a few large tenants.
- HNSW is the default index: good recall and speed, no training step, slower to build and
  larger in memory. IVFFlat builds faster and smaller but must be created after data is loaded
  and loses recall as data drifts.
- Build the index after bulk loading, with generous `maintenance_work_mem`, and use
  `CREATE INDEX CONCURRENTLY` on a live table. The index should fit in memory; when it does
  not, latency collapses. Half-precision (`halfvec`) storage or lower-dimension embeddings
  halve the footprint.
- Store the embedding model name and version beside each vector. Vectors from different models
  are not comparable; a model change means re-embedding everything into a new column and
  switching, the same pattern as an index rebuild.
- Pure vector search misses exact terms (names, error codes, part numbers). Combine full-text
  and vector results with reciprocal rank fusion for general search.

Chunking, retrieval quality and reranking are in `0x:ai-features` (`retrieval.md`).

## Measuring quality

Log every search: normalized query, tenant, filters, result count, latency, the position of any
clicked result, and whether the next action was a reformulated query. Queries can contain
personal data, so the log gets a retention period (`data-lifecycle.md`).

| Metric | Reading |
|---|---|
| Zero-result rate | Each frequent zero-result query is a missing synonym, a typo-tolerance gap or missing content |
| Click-through rate | Searches with results and no click: ranking or snippet problem |
| Mean position of first click | Rising means the right result is sinking |
| Reformulation rate | The first query failed |
| p95 latency | Per endpoint; autocomplete separately |

Review the top twenty zero-result queries and top twenty no-click queries weekly at Launch; it
is the highest-yield hour in search work. Keep a golden set of 30 to 50 real queries with the
results that must appear in the top three, run it as a test before any relevance change, and add
to it from every complaint.

## Tuning relevance

Change one thing at a time and rerun the golden set. In order of leverage:

1. **Analysis.** The right language analyzer per field; no stemming on names and codes; accent
   folding; how hyphens, dots and camelCase tokenize (searching `wifi` for `Wi-Fi`). Languages
   written without spaces need a dedicated tokenizer. Most "search is broken" reports are
   tokenization.
2. **Searchable fields and their weight.** Title above tags above body. Remove fields that add
   noise.
3. **Typo tolerance.** Allow one typo on medium words and two on long ones (engine defaults are
   sensible); disable it on identifiers, SKUs and emails, where a near match is a wrong match.
4. **Synonyms.** Add from the zero-result log, not from imagination. Prefer one-way synonyms
   (`tv → television`) unless terms are truly interchangeable. Keep the list small and in
   version control.
5. **Ranking rules.** Text relevance first; business signals (popularity, recency) as
   tiebreakers. A strong popularity boost makes every query return the same bestsellers.
6. **Exact matches win.** An exact title or ID match ranks first regardless of other signals.

In Elasticsearch-style engines, analyzer and mapping changes require a rebuild; relevance work
is therefore planned around the rebuild procedure above.

## Ask the user

- **What do people search for, and what should they find?** Ten example queries with the
  expected top result. Without them there is nothing to tune against. Default: derive from logs
  after a week.
- **Is typo tolerance or faceting a requirement at launch?** This decides Postgres versus an
  engine. Default: Postgres search first.
- **Who may see what in results?** Tenant only, or per-document permissions. Default: strict
  tenant isolation plus the same rules as the list views.
- **How fresh must results be after an edit?** Default: a few seconds for the editor's own
  changes, under a minute otherwise.
- **What is the monthly budget for search?** Hosted engines are priced by records, searches or
  memory. Default: stay in Postgres until a requirement forces a cost.
