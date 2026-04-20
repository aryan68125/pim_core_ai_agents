# Feature 07 — Database Schema

Postgres 16 with the `pgvector` extension. All tables use integer primary keys. Migrations managed by Alembic.

---

## Tables

### `taxonomy_nodes`

Stores all taxonomy leaf nodes from GS1, eCl@ss, and custom taxonomy. The `embedding` column is the 1536-dim vector used for similarity search.

```sql
CREATE TABLE taxonomy_nodes (
  id            SERIAL PRIMARY KEY,
  code          VARCHAR(100)  NOT NULL,
  name          TEXT          NOT NULL,
  taxonomy_type taxonomytype  NOT NULL,   -- 'gs1' | 'eclass' | 'custom'
  parent_code   VARCHAR(100),
  breadcrumb    TEXT          NOT NULL DEFAULT '',
  embedding     vector(1536),
  created_at    TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- Unique per (code, taxonomy_type) — same code can exist in different standards
CREATE UNIQUE INDEX uq_taxonomy_code_type ON taxonomy_nodes (code, taxonomy_type);

-- Fast HNSW approximate nearest-neighbour search
CREATE INDEX ix_taxonomy_embedding ON taxonomy_nodes USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

CREATE INDEX ix_taxonomy_type ON taxonomy_nodes (taxonomy_type);
```

Populated by `python -m classifier.taxonomy.loader`.

---

### `classification_results`

One row per classification call. The canonical record of what the system decided.

```sql
CREATE TABLE classification_results (
  id                 SERIAL PRIMARY KEY,
  product_text       TEXT          NOT NULL,
  taxonomy_type      taxonomytype  NOT NULL,
  stage              classificationstage NOT NULL,  -- 'embedding' | 'llm_tier2'
  chosen_code        VARCHAR(100),
  chosen_name        TEXT,
  confidence         FLOAT         NOT NULL DEFAULT 0.0,
  requires_review    BOOLEAN       NOT NULL DEFAULT false,
  service_account_id INT REFERENCES service_accounts(id),
  created_at         TIMESTAMPTZ   NOT NULL DEFAULT now()
);
```

`requires_review = true` means the result is below the confidence threshold and needs a human to submit a correction.

---

### `corrections`

Human-supplied corrections for flagged results. Submitting a correction also sets `classification_results.requires_review = false`.

```sql
CREATE TABLE corrections (
  id           SERIAL PRIMARY KEY,
  result_id    INT  NOT NULL REFERENCES classification_results(id),
  correct_code VARCHAR(100) NOT NULL,
  correct_name TEXT         NOT NULL,
  notes        TEXT,
  created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

---

### `classification_audit`

Append-only event log. Never updated.

```sql
CREATE TABLE classification_audit (
  id         SERIAL PRIMARY KEY,
  result_id  INT         NOT NULL REFERENCES classification_results(id),
  event      VARCHAR(50) NOT NULL,   -- 'classify' | 'correction'
  payload    JSONB       NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

### `taxonomy_loads`

One row per taxonomy load run. Tracks history and node counts.

```sql
CREATE TABLE taxonomy_loads (
  id            SERIAL PRIMARY KEY,
  taxonomy_type taxonomytype NOT NULL,
  node_count    INT          NOT NULL DEFAULT 0,
  status        VARCHAR(20)  NOT NULL DEFAULT 'pending',   -- 'success' | 'error'
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

---

### `service_accounts`

Service account credentials. Scopes stored as a space-delimited string.

```sql
CREATE TABLE service_accounts (
  id             SERIAL PRIMARY KEY,
  name           TEXT    UNIQUE NOT NULL,
  hashed_secret  TEXT    NOT NULL,
  scopes         TEXT    NOT NULL DEFAULT '',  -- e.g. "classify:write taxonomy:read"
  active         BOOLEAN NOT NULL DEFAULT true,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## Enums

```sql
CREATE TYPE taxonomytype AS ENUM ('gs1', 'eclass', 'custom');
CREATE TYPE classificationstage AS ENUM ('embedding', 'llm_tier2');
```

---

## Entity Relationships

```
service_accounts
      │
      │  (FK) service_account_id
      ▼
classification_results
      │
      ├── (FK) result_id ──► corrections
      │
      └── (FK) result_id ──► classification_audit
```

`taxonomy_nodes` is independent — no foreign keys into or from the classification tables.

---

## Migrations

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

The `alembic/env.py` imports `classifier.db.models` to register all models with `Base.metadata` before autogenerate runs.

When adding the `pgvector` extension for the first time, the migration must include:
```python
op.execute("CREATE EXTENSION IF NOT EXISTS vector")
```
This is already present in the initial migration.
