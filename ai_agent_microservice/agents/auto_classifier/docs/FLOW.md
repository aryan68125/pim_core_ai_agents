# Auto Classifier — End-to-End Flow

Traces a single `POST /classify` request from HTTP arrival to JSON response.

---

## Bird's-Eye View

```
Client
  │
  │  POST /classify
  │  { "product_description": "Samsung T5 SSD 1TB",
  │    "product_manufacturer": "Samsung" }
  ▼
┌─────────────────────────────────────────────┐
│  FastAPI  (routes/classify.py)              │
│  ClassifyRequest → classify_product()       │
└────────────────────┬────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │   LangGraph Graph   │
          │  (6 nodes, below)   │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────────┐
          │  Persist to Postgres    │
          │  classification_results │
          └──────────┬──────────────┘
                     │
                     ▼
              ClassifyResponse → Client
```

---

## LangGraph Workflow Nodes

```
embed ──► search ──► route ──► llm ──► END
                        │              ▲
                        ├──► web_search ┘  (Path B and C only)
                        │
                        └──► (Path C only) save_category ──► END
```

### Node 1 — embed

**File:** `tools/embed_product.py`

Calls `EmbeddingProvider.embed(product_text)` to produce a 1536-dim float vector.

`product_text` = `{product_description} {product_manufacturer}` (concatenated in `classify_product.py`).

### Node 2 — search

**File:** `tools/category_search.py`

Runs a cosine similarity CTE against `web_categories`:

```sql
WITH ranked AS (
    SELECT id, category_id, category_path, level1, level2, level3,
           embedding <=> CAST(:vec AS vector) AS distance
    FROM web_categories
    WHERE embedding IS NOT NULL
    ORDER BY distance
    LIMIT 5
)
SELECT *, 1 - distance AS score FROM ranked
```

Returns top 5 candidates with scores in [0, 1].

### Node 3 — route

Reads `top_score` (best candidate's score) and assigns a path:

| Score | Path |
|-------|------|
| ≥ 0.60 | **A** — high confidence, skip web search |
| 0.35 – 0.59 | **B** — medium confidence, add Wikipedia context |
| < 0.35 | **C** — low confidence, Wikipedia only, generate new category |

### Node 4 — web_search (Path B and C only)

**File:** `tools/web_search.py`

Calls Wikipedia REST API with the product text. Returns up to 500 chars from the best matching article summary. 403 / no-results are handled gracefully (empty string).

### Node 5 — llm

**File:** `workflows/classification_workflow.py` → `llm_node()`

Builds a prompt based on path and calls `pim_core.llm.client.llm_client.complete()`.

| Path | System prompt | User content |
|------|--------------|--------------|
| A | "Pick the best category from the list" | product text + top 5 candidates |
| B | "Use web context + list to pick best" | product text + Wikipedia summary + top 5 |
| C | "Generate a sensible L1 > L2 > L3 path" | product text + Wikipedia summary |

LLM responds with JSON: `{ "category_path": "...", "confidence": 0.0–1.0 }`.

For Paths A and B the code resolves `category_id` by matching `category_path` against the candidate list.

### Node 6 — save_category (Path C only)

Embeds the LLM-generated `category_path`, assigns a random negative `category_id`, and inserts a new row into `web_categories`. This makes the new category discoverable in future searches.

---

## Confidence Thresholds (config.py defaults)

| Variable | Default | Meaning |
|----------|---------|---------|
| `high_confidence_threshold` | `0.60` | Path A cutoff |
| `low_confidence_threshold` | `0.35` | Path B / C boundary |

Calibrated for cross-domain product-description → category-path embedding similarity with `text-embedding-3-small`. Wide gap (0.25) between thresholds prevents fragile single-point routing decisions.
