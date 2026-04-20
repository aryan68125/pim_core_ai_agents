# Classification Service — End-to-End Internal Flow

This document traces a single classification request from HTTP arrival to the final JSON response, touching every internal component in order.

---

## Bird's-Eye View

```
Client
  │
  │  POST /classify
  │  { "product_text": "10mm stainless hex bolt M6x20",
  │    "taxonomy_type": "gs1", "top_k": 3 }
  ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI  (main.py)                                     │
│  ├── JWT middleware  →  require_scope("classify:write") │
│  └── ClassifyRouter  →  classify_product()             │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │   Redis Cache check   │  HIT → return immediately
          └───────────┬───────────┘
                      │ MISS
          ┌───────────▼───────────────────────┐
          │  Stage 1 — Embedding Search        │
          │  OpenAI text-embedding-3-small     │
          │  pgvector HNSW cosine similarity   │
          └───────────┬───────────────────────┘
                      │
              score ≥ 0.92?
             /             \
           YES               NO
            │                │
            │    ┌───────────▼───────────────────┐
            │    │  Stage 2 — LLM Tier 2          │
            │    │  Anthropic / OpenAI / Gemini   │
            │    │  picks best from candidates    │
            │    └───────────┬───────────────────┘
            │                │
            └────────┬───────┘
                     │
          ┌──────────▼──────────────┐
          │  confidence ≥ 0.75?      │
          │  YES → auto-accept       │
          │  NO  → flag HITL review  │
          └──────────┬──────────────┘
                     │
          ┌──────────▼──────────────┐
          │  Persist to Postgres     │
          │  classification_results  │
          └──────────┬──────────────┘
                     │
          ┌──────────▼──────────────┐
          │  Write audit record      │
          │  classification_audit    │
          └──────────┬──────────────┘
                     │
          ┌──────────▼──────────────┐
          │  Cache result in Redis   │  (only if not flagged for review)
          └──────────┬──────────────┘
                     │
                     ▼
              JSON response → Client
```

---

## Phase 0 — Taxonomy Pre-loading (one-time setup)

Before any classification request can be served, taxonomy data must be embedded and stored. This is a one-time admin operation, not part of the request path.

```
Admin runs:
  python -m classifier.taxonomy.loader gs1

          ┌──────────────────────────────────────────┐
          │  taxonomy/gs1.py — fetch_gs1_nodes()      │
          │                                           │
          │  1. Download GPC ZIP from GS1 URL         │
          │     (or read local file path)             │
          │  2. Extract XML from ZIP                  │
          │  3. Parse Segment > Family > Class > Brick│
          │  4. Build flat list of brick-level nodes  │
          └──────────────┬───────────────────────────┘
                         │  list[dict]:
                         │  { code, name, breadcrumb, taxonomy_type }
                         ▼
          ┌──────────────────────────────────────────┐
          │  taxonomy/embedder.py — embed_batch()     │
          │                                           │
          │  Calls OpenAI text-embedding-3-small      │
          │  Input: "{name} {breadcrumb}" per node    │
          │  Output: 1536-dim float vector per node   │
          │  Processes in batches of 50               │
          └──────────────┬───────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────────────┐
          │  Postgres: taxonomy_nodes table           │
          │                                           │
          │  UPSERT by (code, taxonomy_type)          │
          │  Stores: code, name, breadcrumb,          │
          │          taxonomy_type, embedding (vector) │
          │                                           │
          │  HNSW index on embedding column           │
          │  (cosine distance, m=16, ef=64)           │
          └──────────────────────────────────────────┘
```

Same pattern runs for **eCl@ss** (`taxonomy/eclass.py`) and **custom YAML** (`taxonomy/custom.py`).

---

## Phase 1 — Request Arrives

```
POST /classify
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "product_text": "10mm stainless hex bolt M6x20",
  "taxonomy_type": "gs1",
  "top_k": 3,
  "min_confidence": null
}
```

**File:** `api/classify.py`

1. FastAPI parses body into `ClassifyRequest`
2. `require_scope("classify:write")` dependency runs:
   - Extracts JWT from `Authorization: Bearer`
   - Decodes with `jwt_secret` + `jwt_algorithm`
   - Checks `"classify:write"` is in token's `scopes` list
   - Returns payload dict (contains `sub` = service account ID)
3. Calls `classify_product()` in `pipeline/classify.py`

---

## Phase 2 — Cache Lookup

**File:** `cache/redis_cache.py`

Cache key is:

```
cls:{taxonomy_type}:{top_k}:{sha256(product_text)}
```

Example: `cls:gs1:3:a3f9c2...`

- **HIT** → deserialize JSON, return `ClassifyResult` immediately. No DB, no embedding, no LLM.
- **MISS** → continue to Stage 1.

Cache TTL is 24 hours (`cache_ttl_seconds = 86400`). Results flagged for human review are **not** cached.

---

## Phase 3 — Stage 1: Embedding Similarity Search

**File:** `pipeline/embedding.py`

```
product_text
     │
     ▼
OpenAI text-embedding-3-small
     │
     ▼  1536-dim vector
     │
     ▼
SELECT id, code, name, breadcrumb,
       1 - (embedding <=> $vec::vector) AS score
FROM taxonomy_nodes
WHERE taxonomy_type = 'gs1'
ORDER BY embedding <=> $vec::vector
LIMIT 3
```

Uses **pgvector's `<=>` cosine distance operator** with the HNSW index — approximate nearest-neighbour search in sub-millisecond time even across hundreds of thousands of taxonomy nodes.

Returns `top_k` candidates sorted by descending similarity score (score = 1 − cosine distance, range 0–1).

**Exit condition:** If `candidates[0].score >= 0.92` (the embedding threshold), classification exits here.
The top match is accepted as-is. No LLM call is made.

---

## Phase 4 — Stage 2: LLM Tier 2 (if needed)

**File:** `pipeline/llm_classify.py`

Only runs when the top embedding score is below 0.92.

```
System prompt + product_text + candidate list
     │
     ▼
LLMFactory.get("tier2")
     │
     ├─ AnthropicProvider  (claude-sonnet-4-6)
     ├─ OpenAIProvider     (gpt-4o)
     ├─ GeminiProvider     (gemini-1.5-pro)
     └─ OllamaProvider     (any local model)
     │
     ▼
LLM responds with JSON:
{
  "code": "10000265",
  "name": "Bolts/Hex Bolts (Fasteners)",
  "confidence": 0.88,
  "reasoning": "M6x20 stainless hex bolt maps directly to GS1 brick 10000265"
}
```

The active provider is controlled entirely by `LLM_TIER2_PROVIDER` in `.env` — no code changes needed to switch. `LLMFactory.get()` reads the env config at call time and instantiates the correct provider.

---

## Phase 5 — Confidence Gate

**File:** `pipeline/classify.py`

```
confidence = result from Stage 1 or Stage 2

effective_threshold = min_confidence (from request) ?? 0.75

if confidence < effective_threshold or chosen_code is None:
    requires_review = True   ← flagged for human-in-the-loop
else:
    requires_review = False  ← auto-accepted
```

| confidence | outcome |
|---|---|
| ≥ 0.92 | Accepted at embedding stage, no LLM |
| 0.75 – 0.91 | LLM ran, confidence sufficient, auto-accepted |
| < 0.75 | LLM ran but uncertain, flagged for human review |
| no match (null) | Always flagged |

---

## Phase 6 — Persist to Postgres

**File:** `pipeline/classify.py`

Inserts one row into `classification_results`:

| column | value |
|---|---|
| `product_text` | original input text |
| `taxonomy_type` | `gs1` / `eclass` / `custom` |
| `stage` | `embedding` or `llm_tier2` |
| `chosen_code` | winning taxonomy code |
| `chosen_name` | winning taxonomy name |
| `confidence` | 0.0 – 1.0 |
| `requires_review` | true/false |
| `service_account_id` | FK to service_accounts |

---

## Phase 7 — Audit Record

**File:** `core/audit/logger.py`

Appends one row to `classification_audit` (append-only, never updated):

```json
{
  "result_id": 42,
  "event": "classify",
  "payload": {
    "stage": "llm_tier2",
    "confidence": 0.88,
    "requires_review": false,
    "reasoning": "M6x20 stainless hex bolt maps to brick 10000265"
  }
}
```

Every correction also writes a `"correction"` audit event, creating a full history for every result.

---

## Phase 8 — Cache Write and Response

If `requires_review = false`, the serialized `ClassifyResult` is written to Redis with a 24h TTL.

Final response:

```json
{
  "result_id": 42,
  "product_text": "10mm stainless hex bolt M6x20",
  "taxonomy_type": "gs1",
  "stage": "llm_tier2",
  "candidates": [
    { "code": "10000265", "name": "Bolts/Hex Bolts (Fasteners)", "breadcrumb": "Hardware > Fasteners > Bolts > Bolts/Hex Bolts (Fasteners)", "score": 0.89 },
    { "code": "10000264", "name": "Screws (Fasteners)", "breadcrumb": "Hardware > Fasteners > Screws > Screws (Fasteners)", "score": 0.81 },
    { "code": "10000270", "name": "Nuts (Fasteners)", "breadcrumb": "Hardware > Fasteners > Nuts > Nuts (Fasteners)", "score": 0.74 }
  ],
  "chosen_code": "10000265",
  "chosen_name": "Bolts/Hex Bolts (Fasteners)",
  "confidence": 0.88,
  "requires_review": false,
  "reasoning": "M6x20 stainless hex bolt maps directly to GS1 brick 10000265"
}
```

---

## Taxonomy Data Sources

| Standard | Source | Format | How loaded |
|---|---|---|---|
| **GS1 GPC** | gs1.org GPC browser (manual download or URL) | ZIP → XML | `taxonomy/gs1.py` → parses Segment > Family > Class > Brick hierarchy |
| **eCl@ss** | eclass.eu (may require login) | XML | `taxonomy/eclass.py` → parses `ClassificationClass` at level 4 (8-digit codes) |
| **Custom** | Local YAML file (`taxonomy_data/custom.yaml`) | YAML list | `taxonomy/custom.py` → reads and validates list of `{code, name, breadcrumb}` |

All three feed into the same `_upsert_nodes()` function in `taxonomy/loader.py` which embeds in batches of 50 and upserts into `taxonomy_nodes`.

---

## Confidence Threshold Cheat Sheet

| env var | default | meaning |
|---|---|---|
| `CONFIDENCE_EMBEDDING_THRESHOLD` | `0.92` | Skip LLM entirely — embedding match is certain enough |
| `CONFIDENCE_HITL_THRESHOLD` | `0.75` | Below this, flag for human review regardless of stage |

Both are hot-configurable via `.env` with no code changes.
