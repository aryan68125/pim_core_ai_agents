# Databricks Integration Design

**Context:** PIM-AI — Product Description Generator (Content Agent)  
**Principle:** Databricks is the **data + feature + ML layer**, NOT the agent layer.

---

## Core Positioning

Databricks serves as the **data platform and MLOps layer** behind the application stack — it does NOT replace FastAPI, LangGraph, Claude, ARQ/Redis, or FastMCP.

**Logical Flow:**
```
Raw Product Data → Databricks → Feature Tables → Signals → Agent (LangGraph) → LLM (Claude)
```

**Databricks integration flow:**
```
Databricks → Features → Agents → LLM → Actions
```

---

## System Placement

Databricks belongs to:
- **Layer 2 — Feature Computation Layer** (computes reusable features once)
- **Layer 3 — Signal Layer** (computes decision triggers)

From Custonomy architecture:
- Feature Layer = reusable computed data
- Signal Layer = decision triggers

---

## What Databricks is NOT Responsible For

| Component | Responsibility |
|-----------|---------------|
| LangGraph | Agent orchestration |
| FastAPI | API / application layer |
| FastMCP | Tool execution (MCP protocol) |
| Claude API | LLM inference |

These remain inside the existing system.

---

## The Six Realistic Roles Databricks Plays

### 1. Product Data Pipeline (Delta Lake + Delta Live Tables)
Databricks becomes the centralized product data lakehouse.

- Raw product data from PostgreSQL syncs into Bronze layer via CDC (Debezium/Kafka or JDBC)
- Delta Live Tables (DLT) transforms: Bronze → Silver (cleaned, standardized) → Gold (ML-ready)
- Delta Lake provides **ACID transactions, schema evolution, and time travel**
- PostgreSQL remains the operational database; Delta Lake is the analytical and ML data layer

### 2. Batch Description Generation at Scale
When the PIM needs to generate/regenerate thousands of descriptions:
- Distributes LLM API calls across a Spark cluster
- Wraps Claude API calls in Spark UDFs or uses `ai_query()` SQL function
- Applies them across millions of product rows with built-in **fault tolerance, retry logic, rate-limit management**
- Results write directly to Delta tables
- Different from ARQ + Redis (real-time single-product) — Databricks handles bulk batch processing

### 3. Feature Engineering for Prompt Enrichment
Databricks Feature Store precomputes and serves features that enrich `generate_description` prompts.

**Practical feature tables for PIM:**

| Feature Type | Example |
|-------------|---------|
| Category Intelligence | Top keywords, attribute importance |
| SEO Signals | High-ranking keywords per category |
| Content Patterns | Best-performing descriptions |
| Data Quality | Missing fields, completeness score |
| Product Context | Attribute distributions |

Without Databricks: `LLM ← raw product data` (expensive, inconsistent)  
With Databricks: `LLM ← product data + structured features` (efficient, consistent)

### 4. MLflow for LLM Experiment Tracking and Evaluation
- Tracks prompt template versions, LLM parameters (temperature, max tokens, system prompt)
- `mlflow.evaluate()` provides built-in LLM evaluation: toxicity, relevance, readability, plus custom metrics (SEO score, brand voice adherence, keyword inclusion rate)
- **MLflow Tracing** captures the full execution trace of multi-step generation workflows
- Mosaic AI Agent Evaluation adds LLM-as-judge scoring and a Review App for human feedback

### 5. Unity Catalog for Governance and Lineage
- End-to-end lineage tracking: which product data fed which features, which prompt template generated which description, who approved it
- Fine-grained access control — column-level security on sensitive product data (cost prices, supplier info)
- Row-level filtering by region or brand
- Model registry permissions for prompt configurations

### 6. AI Gateway for Centralized LLM Call Management
- Proxies Claude API calls through a unified interface
- Adds **rate limiting, credential isolation**, request/response logging to Delta tables
- Cost tracking per token, access control via Unity Catalog permissions
- Enables A/B testing different models behind a single endpoint name

---

## What Databricks Does vs. Existing Stack

| Concern | Existing Stack | Databricks Role |
|---------|---------------|-----------------|
| HTTP API / application server | FastAPI | Not involved |
| Multi-agent orchestration | LangGraph | Not involved (can evaluate/deploy but not replace) |
| LLM reasoning | Claude API | Can proxy via AI Gateway; Claude quality stays |
| Real-time job queue | ARQ + Redis | Not designed for sub-second task queuing |
| MCP tool protocol | FastMCP | No equivalent |
| Operational product data | PostgreSQL | Not a transactional database |
| Real-time vector search | pgvector | Keep pgvector (co-located with PIM relational data) |
| Product data ETL/pipeline | Limited | **Delta Lake + DLT — major value-add** |
| Batch generation at scale | ARQ (limited) | **Spark-distributed batch inference — major value-add** |
| Feature engineering | Custom code | **Feature Store — major value-add** |
| Prompt/LLM experiment tracking | None | **MLflow — major value-add** |
| LLM output evaluation | None | **Agent Evaluation — major value-add** |
| Data governance & lineage | PostgreSQL RBAC only | **Unity Catalog — major value-add** |
| LLM call logging & cost tracking | Manual/custom | **AI Gateway + Inference Tables — value-add** |

---

## Signal Generation (Trigger Layer)

Databricks computes these decision signals for the Content Agent:
- `missing_description_flag`
- `low_quality_content_flag`
- `seo_gap_flag`

These signals control **agent invocation** (event-driven execution, not full catalog scans).

---

## Content Agent Data Flow

**Step 1 — Databricks (Offline Processing)**
Compute features: keywords, attribute importance, SEO signals, content patterns

**Step 2 — Storage Layer**
Store in: PostgreSQL (feature tables) + Delta tables (Databricks)

**Step 3 — Agent Execution (Online)**
Content Agent workflow:
1. Fetch product data
2. Fetch precomputed features
3. Call `generate_description` tool
4. Use Claude API
5. Store output

**Workflow mapping:**
```
classify → tag → generate description → sequence images
                       ↑
            Databricks enriches this step
```

---

## Reference Architecture

```
┌──────────────────────────────────────────────────────────┐
│              DATABRICKS PLATFORM                          │
│                                                          │
│  Delta Live Tables → Delta Lake (Bronze/Silver/Gold)     │
│  Feature Store (SEO keywords, brand voice configs)       │
│  Databricks Workflows (batch orchestration)              │
│  MLflow (prompt tracking, evaluation, tracing)           │
│  Unity Catalog (governance, lineage, access control)     │
│  AI Gateway (Claude proxy + logging + rate limiting)     │
│  Batch Inference (Spark + Claude for bulk generation)    │
└──────────┬────────────────────────┬──────────────────────┘
           │ Sync product data      │ Serve features /
           │ (CDC)                  │ batch results
           ▼                        ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│ PostgreSQL + pgvector │    │ FastAPI + LangGraph +        │
│ (operational DB,     │◄──►│ Claude API + ARQ/Redis +     │
│  real-time vectors)  │    │ FastMCP (real-time app)      │
└──────────────────────┘    └──────────────────────────────┘
```

---

## When to Use Databricks

**Use Databricks if:**
- Large catalog scale (100K+ products)
- Complex feature computation needed
- Need reusable feature store
- Need ML pipelines

**Avoid Databricks if:**
- Small dataset
- Simple pipelines
- Early-stage MVP

> Note: The ADR prioritizes **low infrastructure complexity** → Databricks is **optional initially**.

---

## Key Design Principles

1. **Process Once, Reuse Everywhere** — Databricks computes features once; all agents reuse them.
2. **No Raw Data Access by Agents** — Agents consume APIs / feature tables only.
3. **Event-Driven Execution** — Signals trigger agents; no full catalog scans.
4. **Separate Offline vs Online Compute** — Databricks handles heavy compute/feature generation; Agents handle decision making + LLM.

---

## Future Evolution Phases

| Phase | What Changes |
|-------|-------------|
| Phase 1 (Current) | Claude API, minimal features, no Databricks required |
| Phase 2 | Introduce feature tables, basic Databricks pipelines |
| Phase 3 | ML models (SEO scoring, quality scoring), fine-tuning |
| Phase 4 | Full feature store, cross-agent shared intelligence |

---

## Official Databricks + LangGraph Integration

Databricks maintains the `databricks-langchain` partner package:
- **`ChatDatabricks`** — chat model wrapper for Databricks Model Serving endpoints
- **`DatabricksEmbeddings`** — embeddings wrapper
- **`DatabricksVectorSearch`** — retriever for Databricks Vector Search
- **`UCFunctionToolkit`** — exposes Unity Catalog functions as LangChain tools

**`databricks-agents`** package handles deployment and evaluation:
- `databricks.agents.deploy()` pushes MLflow-logged agents to Model Serving
- Review App enables human evaluation
- Framework-agnostic — wraps LangGraph agents without replacing orchestration logic

**Pattern:** Define LangGraph `StateGraph` → log with `mlflow.langchain.log_model()` → deploy with `databricks-agents` → evaluate with Mosaic AI Agent Evaluation.
