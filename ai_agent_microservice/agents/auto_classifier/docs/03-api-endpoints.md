# Feature 03 — API Endpoints

All endpoints are served by FastAPI at `http://localhost:8000`. Interactive docs at `/docs`.

All endpoints except `/health` require a JWT bearer token in the `Authorization` header.

---

## Base URL

```
http://localhost:8000
```

---

## Health Check

### `GET /health`

No auth required.

**Response:**
```json
{
  "status": "ok",
  "db": true,
  "redis": true
}
```

`status` is `"ok"` when both `db` and `redis` are reachable. Returns `"degraded"` if either is down.

---

## Classify

### `POST /classify`

Classify a product description against a taxonomy standard.

**Required scope:** `classify:write`

**Request:**
```json
{
  "product_text": "10mm stainless hex bolt M6x20",
  "taxonomy_type": "gs1",
  "top_k": 3,
  "min_confidence": null
}
```

| field | type | default | description |
|---|---|---|---|
| `product_text` | string | required | Product description to classify. 1–4096 chars. |
| `taxonomy_type` | `gs1` \| `eclass` \| `custom` | `"gs1"` | Which taxonomy to classify against |
| `top_k` | int 1–5 | `3` | How many candidate nodes to retrieve from embedding search |
| `min_confidence` | float \| null | `null` | Override the HITL threshold (defaults to `CONFIDENCE_HITL_THRESHOLD` from env) |

**Response:**
```json
{
  "result_id": 42,
  "product_text": "10mm stainless hex bolt M6x20",
  "taxonomy_type": "gs1",
  "stage": "llm_tier2",
  "candidates": [
    {
      "code": "10000265",
      "name": "Bolts/Hex Bolts (Fasteners)",
      "breadcrumb": "Hardware > Fasteners > Bolts > Bolts/Hex Bolts (Fasteners)",
      "score": 0.89
    }
  ],
  "chosen_code": "10000265",
  "chosen_name": "Bolts/Hex Bolts (Fasteners)",
  "confidence": 0.88,
  "requires_review": false,
  "reasoning": "M6x20 stainless hex bolt maps directly to GS1 brick 10000265"
}
```

| field | description |
|---|---|
| `result_id` | DB primary key for this result — use for corrections |
| `stage` | `"embedding"` (Stage 1 exit) or `"llm_tier2"` (LLM was called) |
| `candidates` | All top-k candidates from embedding search with their similarity scores |
| `chosen_code` | Winning taxonomy code, or `null` if no match found |
| `confidence` | Final confidence score 0.0–1.0 |
| `requires_review` | `true` = flagged for human review; `false` = auto-accepted |
| `reasoning` | LLM's explanation (empty if Stage 1 exit) |

---

## Corrections

### `POST /corrections`

Submit a human correction for a flagged result.

**Required scope:** `classify:write`

**Request:**
```json
{
  "result_id": 42,
  "correct_code": "10000264",
  "correct_name": "Screws (Fasteners)",
  "notes": "This is a machine screw, not a hex bolt"
}
```

**Response (201):**
```json
{
  "id": 7,
  "result_id": 42,
  "correct_code": "10000264",
  "correct_name": "Screws (Fasteners)",
  "notes": "This is a machine screw, not a hex bolt",
  "created_at": "2026-04-20T10:30:00Z"
}
```

Submitting a correction also sets `requires_review = false` on the original result and writes a `"correction"` audit event.

---

## Taxonomy

### `GET /taxonomy?taxonomy_type=gs1&page=1&page_size=50`

List taxonomy nodes with pagination.

**Required scope:** `taxonomy:read`

**Query params:**

| param | type | description |
|---|---|---|
| `taxonomy_type` | `gs1` \| `eclass` \| `custom` | Required |
| `page` | int ≥ 1 | Default 1 |
| `page_size` | int 1–500 | Default 50 |

**Response:**
```json
{
  "total": 18500,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": 1,
      "code": "10000265",
      "name": "Bolts/Hex Bolts (Fasteners)",
      "taxonomy_type": "gs1",
      "parent_code": "10000000",
      "breadcrumb": "Hardware > Fasteners > Bolts > Bolts/Hex Bolts (Fasteners)"
    }
  ]
}
```

### `GET /taxonomy/{node_id}`

Fetch a single taxonomy node by its integer ID.

**Required scope:** `taxonomy:read`

Returns the same shape as a single item from the list above. Returns 404 if not found.

---

## Error Responses

| status | meaning |
|---|---|
| 401 Unauthorized | Missing or invalid JWT token |
| 403 Forbidden | Valid token but missing required scope |
| 404 Not Found | Resource not found (taxonomy node, correction target) |
| 422 Unprocessable Entity | Request body failed Pydantic validation |
| 500 Internal Server Error | Unexpected server error |

All errors follow FastAPI's default `{"detail": "..."}` shape.
