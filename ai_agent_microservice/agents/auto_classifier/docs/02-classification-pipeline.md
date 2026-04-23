# 02 — Classification Pipeline

The pipeline is a 6-node LangGraph `StateGraph` in `workflows/classification_workflow.py`. All state passes through a `ClassificationState` TypedDict.

---

## State Shape

```python
class ClassificationState(TypedDict):
    product_text: str          # "{description} {manufacturer}"
    session: AsyncSession      # DB session passed through graph
    embedding: list[float] | None
    candidates: list[dict]     # top 5 from pgvector search
    top_score: float
    web_context: str | None    # Wikipedia summary (Paths B/C)
    path: str | None           # "A", "B", or "C"
    category_path: str | None  # final answer
    category_id: int | None
    confidence: float
    method: str                # "A", "B", or "C" — which path was used
    error: str | None
```

---

## Path A — High Confidence (score ≥ 0.60)

```
embed → search → route → llm → END
```

1. Embed product text
2. Find top 5 categories by cosine similarity
3. `top_score ≥ 0.55` → route to Path A
4. LLM picks best from the 5 candidates
5. `category_id` resolved from candidate list by exact `category_path` match

**Prompt:** "You are a product classifier. Pick the single best category from the list."

---

## Path B — Medium Confidence (0.35 ≤ score < 0.60)

```
embed → search → route → web_search → llm → END
```

1–3. Same as Path A
4. Wikipedia searched for product context (up to 500 chars)
5. LLM picks best using web context + 5 candidates
6. `category_id` resolved same as Path A

**Prompt:** "Use the web context and the category list to pick the best match."

---

## Path C — Low Confidence (score < 0.35)

```
embed → search → route → web_search → llm → save_category → END
```

1–4. Same as Path B (web context gathered)
5. LLM generates a **new** `L1 > L2 > L3` category path freely (no candidate list)
6. New category is embedded and saved to `web_categories` with a negative `category_id`

**Prompt:** "Generate the most appropriate L1 > L2 > L3 category path."

---

## LLM Response Format

All three paths expect the same JSON shape:

```json
{
  "category_path": "Electronics > Storage Devices > External Solid State Drives",
  "confidence": 0.85
}
```

The `llm_node` strips markdown code fences before parsing (`removeprefix("```json")`).

---

## Error Handling

- `embed_node` failure → sets `error`, downstream nodes skip gracefully
- `web_search_node` failure → sets `web_context = ""`, pipeline continues
- `llm_node` failure → sets `category_path = None`, `confidence = 0.0`, `error` message
