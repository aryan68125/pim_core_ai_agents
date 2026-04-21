# 03 — API Endpoints

All endpoints served by FastAPI at `http://localhost:8003`. Interactive docs at `/docs`.

---

## POST /classify

**File:** `routes/classify.py`

Classify a product into the Web Category Hierarchy.

### Request

```json
{
  "product_description": "Samsung T5 Portable SSD 1TB USB 3.1 Gen 2 External Solid State Drive",
  "product_manufacturer": "Samsung"
}
```

| Field | Type | Required |
|-------|------|----------|
| `product_description` | string | yes |
| `product_manufacturer` | string | no |

### Response

```json
{
  "category_path": "Electronics > Storage Devices > External Solid State Drives",
  "level1": "Electronics",
  "level2": "Storage Devices",
  "level3": "External Solid State Drives",
  "confidence": 0.85,
  "method": "A",
  "model_used": "gpt-4o"
}
```

| Field | Description |
|-------|-------------|
| `category_path` | Full `L1 > L2 > L3` path |
| `level1/2/3` | Split levels (split on `>`) |
| `confidence` | LLM-reported confidence 0–1 |
| `method` | `"A"`, `"B"`, or `"C"` — which path was used |
| `model_used` | LLM model name |

### Example curl

```bash
curl -X POST http://localhost:8003/classify \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Samsung T5 Portable SSD 1TB USB 3.1 Gen 2",
    "product_manufacturer": "Samsung"
  }'
```

---

## GET /health

**File:** `routes/health.py`

Returns DB connectivity status.

### Response (healthy)

```json
{ "status": "ok", "db": "ok" }
```

### Response (DB unreachable)

```json
{ "status": "degraded", "db": "error" }
```

HTTP 200 in both cases.
