# Feature 01 — Taxonomy Loading

Taxonomy loading is a one-time (or scheduled) admin operation that populates the `taxonomy_nodes` table with embedded vectors for all three supported standards.

---

## What It Does

1. Downloads or reads raw taxonomy data (GS1 ZIP, eCl@ss XML, or custom YAML)
2. Parses the hierarchy into flat leaf-level nodes
3. Calls the OpenAI embedding API to generate a 1536-dim vector per node
4. Upserts nodes into Postgres — new nodes are inserted, existing nodes are updated in place

---

## Running the Loader

```bash
# Load all three taxonomies
python -m classifier.taxonomy.loader

# Load a specific taxonomy only
python -m classifier.taxonomy.loader gs1
python -m classifier.taxonomy.loader eclass
python -m classifier.taxonomy.loader custom
```

---

## GS1 GPC

**File:** `src/classifier/taxonomy/gs1.py`

GS1 GPC (Global Product Classification) organises all physical products into a four-level hierarchy:

```
Segment  (e.g. "Food/Beverage/Tobacco")
  └── Family  (e.g. "Fruit and Vegetables")
        └── Class  (e.g. "Vegetables")
              └── Brick  ← leaf, this is what we store
```

Only **Brick** level nodes are stored. Each brick maps to a unique 8-digit code (e.g. `10001002`).

**Breadcrumb stored:** `Segment > Family > Class > Brick name`

**How to get the file:**

GS1 blocks automated downloads. Options:

1. **Local file (recommended):** Download the GPC release ZIP from [gs1.org/services/gpc/browser](https://www.gs1.org/services/gpc/browser), save to `taxonomy_data/`, then set:
   ```
   GS1_GPC_URL=taxonomy_data/gpc_release_i2-2024.zip
   ```

2. **Direct URL:** Set `GS1_GPC_URL` to the ZIP URL. The loader adds browser-like headers; success depends on GS1's current access policy.

The loader automatically detects and extracts ZIP files — no manual unzipping needed.

---

## eCl@ss

**File:** `src/classifier/taxonomy/eclass.py`

eCl@ss is the European standard for industrial product classification. It uses 8-digit codes at the most granular level (level 4).

**How to get the file:**

Download the eCl@ss BASIC XML from [eclass.eu](https://eclass.eu/). Free registration may be required. Set:

```
ECLASS_DOWNLOAD_URL=https://...
ECLASS_DOWNLOAD_USER=your_username    # leave blank if no auth needed
ECLASS_DOWNLOAD_PASS=your_password
```

The loader only stores level-4 (8-digit) classes.

---

## Custom Taxonomy

**File:** `src/classifier/taxonomy/custom.py`

Drop a YAML file at `taxonomy_data/custom.yaml` with this structure:

```yaml
- code: "ELEC-001"
  name: "Resistors"
  parent_code: "ELEC"
  breadcrumb: "Electronics > Passive Components > Resistors"

- code: "ELEC-002"
  name: "Capacitors"
  parent_code: "ELEC"
  breadcrumb: "Electronics > Passive Components > Capacitors"
```

All fields except `code` and `name` are optional. `breadcrumb` defaults to `name` if omitted.

---

## Embedding

**File:** `src/classifier/taxonomy/embedder.py`

Each node is embedded as: `"{name} {breadcrumb}"`

This gives the embedding model both the short label and the full path context, which improves similarity matching for ambiguous product descriptions.

- Model: `text-embedding-3-small` (1536 dims) — configurable via `EMBEDDING_MODEL`
- Batch size: 50 nodes per API call
- The loader commits every batch to Postgres — safe to interrupt and re-run

---

## Storage

All nodes land in the `taxonomy_nodes` table:

| column | description |
|---|---|
| `code` | taxonomy code (unique per type) |
| `name` | human-readable label |
| `taxonomy_type` | `gs1`, `eclass`, or `custom` |
| `parent_code` | parent code for hierarchy display |
| `breadcrumb` | full path string |
| `embedding` | `vector(1536)` — used for similarity search |

A **HNSW index** (m=16, ef_construction=64, cosine ops) on the `embedding` column enables fast approximate nearest-neighbour queries at classification time.

---

## Load History

Every completed load is recorded in `taxonomy_loads`:

| column | description |
|---|---|
| `taxonomy_type` | which standard was loaded |
| `node_count` | how many nodes were processed |
| `status` | `success` or `error` |
| `created_at` | timestamp |
