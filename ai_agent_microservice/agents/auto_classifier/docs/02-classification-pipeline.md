# Feature 02 — Classification Pipeline

The pipeline classifies a product description against a chosen taxonomy standard using a two-stage approach: fast embedding similarity first, LLM reasoning only when needed.

---

## Pipeline Overview

```
Input: product_text + taxonomy_type + top_k
         │
         ▼
  ┌─────────────┐
  │ Redis Cache │──── HIT ──────────────────────────────► Return cached result
  └──────┬──────┘
         │ MISS
         ▼
  ┌──────────────────────────────────────────────┐
  │  STAGE 1 — Embedding Similarity              │
  │                                              │
  │  Embed product_text with OpenAI              │
  │  Run pgvector HNSW cosine search             │
  │  Get top_k candidates with scores            │
  └───────────────────┬──────────────────────────┘
                      │
             top score ≥ 0.92?
            /                  \
          YES                   NO
           │                    │
           │    ┌───────────────▼───────────────────────┐
           │    │  STAGE 2 — LLM Tier 2                  │
           │    │                                        │
           │    │  Send candidates + product_text to LLM │
           │    │  LLM picks best + returns confidence    │
           │    └───────────────┬───────────────────────┘
           │                    │
           └──────────┬─────────┘
                      │
             confidence ≥ 0.75?
            /                   \
          YES                    NO
           │                     │
     auto-accept           flag for human review
           │                     │
           └──────────┬──────────┘
                      │
              Persist + Audit + Cache
                      │
                      ▼
                   Response
```

---

## Stage 1 — Embedding Similarity

**File:** `src/classifier/pipeline/embedding.py`

The product text is embedded with `text-embedding-3-small` (1536 dimensions). The resulting vector is compared against all pre-embedded taxonomy nodes using pgvector's **cosine distance operator** (`<=>`).

```sql
SELECT id, code, name, breadcrumb,
       1 - (embedding <=> $vec::vector) AS score
FROM taxonomy_nodes
WHERE taxonomy_type = $taxonomy_type
ORDER BY embedding <=> $vec::vector
LIMIT $top_k
```

The HNSW index makes this query fast even across hundreds of thousands of nodes (typically < 10ms).

**Score** ranges from 0 (completely unrelated) to 1 (identical). A score of 0.92+ means the embedding alone is confident enough — the LLM is not called.

---

## Stage 2 — LLM Tier 2

**File:** `src/classifier/pipeline/llm_classify.py`

Only runs when embedding confidence is below 0.92.

The LLM receives:
- The product description
- The top-k candidates from the embedding search, with their codes, names, breadcrumbs, and embedding scores

It returns a structured JSON response:
```json
{
  "code": "10000265",
  "name": "Bolts/Hex Bolts (Fasteners)",
  "confidence": 0.88,
  "reasoning": "Hex bolt M6x20 maps directly to this GS1 brick"
}
```

If no candidate is a good match the LLM returns `"code": null` with `confidence: 0.0`.

The LLM is provider-agnostic — see [05-llm-providers.md](05-llm-providers.md) for switching between Anthropic, OpenAI, Gemini, and Ollama.

---

## Confidence Gate

**File:** `src/classifier/pipeline/classify.py`

```python
effective_threshold = min_confidence (from request) ?? 0.75

requires_review = confidence < effective_threshold or chosen_code is None
```

| confidence | what happens |
|---|---|
| ≥ 0.92 | Stage 1 exit — embedding match accepted, no LLM call |
| 0.75 – 0.91 | Stage 2 ran, auto-accepted |
| < 0.75 | Stage 2 ran, flagged as `requires_review = true` |
| null code | Always flagged for review |

The request can pass a custom `min_confidence` to tighten or loosen the gate per-call.

---

## Orchestrator

**File:** `src/classifier/pipeline/classify.py`

The `classify_product()` function owns the full flow:

1. Cache lookup
2. Stage 1 embedding search
3. Stage 2 LLM (conditional)
4. Confidence gate
5. `INSERT INTO classification_results`
6. `INSERT INTO classification_audit`
7. Redis cache write (if not flagged)
8. Return `ClassifyResult`

---

## Correcting a Result

**File:** `src/classifier/api/corrections.py`

When a human reviewer corrects a flagged result, they `POST /corrections` with the right taxonomy code. This:

1. Inserts a row in `corrections`
2. Sets `classification_results.requires_review = false`
3. Writes a `"correction"` audit event

Corrections feed back as training signal — future taxonomy re-loading + fine-tuning can use the corrections table as ground truth.
