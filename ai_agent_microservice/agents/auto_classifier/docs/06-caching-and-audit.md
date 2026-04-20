# Feature 06 — Caching and Audit

---

## Redis Result Cache

**File:** `src/classifier/cache/redis_cache.py`

Classification results are cached in Redis for 24 hours. Identical product text + taxonomy type + top_k combinations are served from cache without hitting the DB, embedding API, or LLM.

### Cache Key

```
cls:{taxonomy_type}:{top_k}:{sha256(product_text)}
```

Example: `cls:gs1:3:a3f9c2d8...`

The SHA-256 hash of the product text keeps the key short and collision-free regardless of text length.

### Cache Behaviour

| condition | cached? |
|---|---|
| `requires_review = false` | Yes, 24h TTL |
| `requires_review = true` | No — result may change after human correction |
| Correction submitted | Cache is NOT invalidated (corrections do not re-classify) |

### TTL

Default: `86400` seconds (24 hours), configurable via `CACHE_TTL_SECONDS`.

### Functions

```python
# Check cache before classifying
result = await get_cached(product_text, taxonomy_type, top_k)

# Write cache after successful classification
await set_cached(product_text, taxonomy_type, top_k, value, ttl=86400)
```

### Redis Config

```bash
REDIS_URL=redis://localhost:6380   # local dev
REDIS_URL=redis://redis:6379       # inside Docker Compose
```

Tests use DB index 1 (`redis://localhost:6380/1`) and flush it between test runs.

---

## Audit Log

**File:** `src/classifier/core/audit/logger.py`

Every classification and every correction writes an append-only record to `classification_audit`. This table is never updated — only inserted into.

### Schema

```sql
classification_audit (
  id         SERIAL PRIMARY KEY,
  result_id  INT REFERENCES classification_results(id),
  event      VARCHAR(50),    -- 'classify' or 'correction'
  payload    JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
)
```

### Classify Event

Written immediately after the `classification_results` row is committed:

```json
{
  "event": "classify",
  "payload": {
    "stage": "llm_tier2",
    "confidence": 0.88,
    "requires_review": false,
    "reasoning": "M6x20 stainless hex bolt maps to brick 10000265"
  }
}
```

### Correction Event

Written when `POST /corrections` is called:

```json
{
  "event": "correction",
  "payload": {
    "correct_code": "10000264",
    "correct_name": "Screws (Fasteners)",
    "notes": "Machine screw, not a hex bolt"
  }
}
```

### Why Append-Only

- Full history of every decision and correction per result
- Can reconstruct how confidence evolved over time
- Corrections table as ground-truth training data for future fine-tuning
- Regulatory / compliance traceability — nothing is ever deleted

### Structured Logging

In addition to the DB audit log, the service uses `structlog` for JSON-structured log output:

```json
{
  "event": "startup complete",
  "timestamp": "2026-04-20T10:57:34Z",
  "level": "info"
}
```

Log level is configurable via `LOG_LEVEL` (default `INFO`). Set to `DEBUG` in development.
