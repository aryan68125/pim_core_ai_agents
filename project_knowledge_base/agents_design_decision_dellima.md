# PIM-AI — Service Architecture

## ADR-001 (Revised): Standalone Microservices with Shared Core Package

**Status:** Proposed  
**Date:** April 2026  
**Supersedes:** ADR-001 (FastAPI Modular Monolith)

---

## Decision

Deploy all three PIM-AI agents as **standalone FastAPI applications**, each running in its own Docker container with its own process boundary, port, and deployment pipeline.

Shared foundation concerns (F-01 to F-09) are implemented once inside a **`pim_core` Python package** — an internal pip-installable library that each agent service installs as a dependency. This is code sharing, not service sharing.

---

## Repository Structure

```
pim-ai/
│
├── pim_core/                        # Shared foundation — pip-installable package
│   ├── pyproject.toml
│   ├── llm/                         # LLM provider abstraction (ADR-007)
│   │   └── provider.py              # LLMProvider interface — swap Claude/GPT-4o without touching agent code
│   ├── mcp/                         # FastMCP base config and tool manifest helpers (F-04)
│   ├── auth/                        # OAuth 2.0 service accounts, JWT validation (F-05)
│   ├── audit/                       # structlog + PostgreSQL append-only audit log (F-06)
│   ├── hitl/                        # HITL approval helpers, Redis pub/sub, SSE (F-07)
│   ├── vector/                      # pgvector client, embedding helpers, HNSW index (F-08)
│   └── schemas/                     # Shared Pydantic v2 schemas for all tool contracts (F-03)
│
├── agents/
│   ├── catalog/                     # Agent 1 — Catalog Management (standalone FastAPI app)
│   │   ├── pyproject.toml           # Declares pim_core as a dependency
│   │   ├── main.py                  # FastAPI app instantiation
│   │   ├── router.py                # REST endpoints (C-01, C-02)
│   │   ├── tools/                   # MCP tools: classify_product, tag_product, sequence_images,
│   │   │                            #   check_data_quality, bulk_update_products
│   │   ├── workflows/               # LangGraph state machines: onboarding (C-11), patrol (C-10)
│   │   ├── prompts/                 # System prompt, few-shot examples (C-09)
│   │   └── Dockerfile
│   │
│   ├── content/                     # Agent 3 — Content & Enrichment (standalone FastAPI app)
│   │   ├── pyproject.toml
│   │   ├── main.py
│   │   ├── router.py                # REST endpoints (E-01)
│   │   ├── tools/                   # MCP tools: generate_description, extract_label_data,
│   │   │                            #   enrich_product, enhance_image, translate_content
│   │   ├── workflows/               # LangGraph state machines: supplier onboarding (E-10), patrol (E-11)
│   │   ├── prompts/                 # System prompt, brand voice config (E-09)
│   │   └── Dockerfile
│   │
│   └── procurement/                 # Agent 2 — Procurement & Buying (standalone FastAPI app)
│       ├── pyproject.toml
│       ├── main.py
│       ├── router.py                # REST endpoints (P-01 to P-04)
│       ├── tools/                   # MCP tools: search_catalog, compare_products,
│       │                            #   check_procurement_rules, raise_purchase_order, find_substitutes
│       ├── workflows/               # LangGraph state machines: reorder (P-11), intake (P-12)
│       ├── prompts/                 # System prompt, procurement rules encoding (P-10)
│       └── Dockerfile
│
├── workers/                         # ARQ worker definitions and cron job schedules (ADR-004)
│   ├── catalog_worker.py
│   ├── content_worker.py
│   └── procurement_worker.py
│
├── db/                              # SQLAlchemy models, Alembic migrations, DB view definitions
│   ├── models/
│   ├── views/                       # Read-only views for agent bulk queries (C-03)
│   └── migrations/
│
├── tests/                           # pytest-asyncio test suite; LangSmith eval configs (F-09)
│   ├── catalog/
│   ├── content/
│   └── procurement/
│
├── docker-compose.yml               # Local development: all services + shared infra
└── pyproject.toml                   # Root tooling config (ruff, mypy, pytest)
```

---

## Why This Architecture

### What Changed from the Original ADR-001

The original ADR-001 chose a **FastAPI Modular Monolith** — one application, three isolated Python packages — and explicitly deferred microservices to a later phase. That rationale was reasonable at the time, but three requirements justify moving to standalone services **now, during the planning phase**, rather than after implementation:

| Requirement | Monolith limitation | Standalone services |
|---|---|---|
| **Independent deployability** | Redeploying one agent redeploys all three | Each agent has its own pipeline, its own versioning |
| **Fault isolation** | An unhandled exception or runaway LangGraph workflow in one agent router can destabilise the others | Process boundary means failures are contained |
| **Consumption by external systems** | External systems (ERPs, partner APIs) hit the same service running all three agents | Each agent exposes its own base URL, auth scope, and API contract |

### What Stays the Same

The shift to standalone services does **not** change any other ADR. LangGraph, ARQ, pgvector, FastMCP, Claude API, SSE + WebSockets — all unchanged. The only structural change is the deployment boundary.

### How the Shared Foundation is Handled

The `pim_core` package is the direct answer to the shared foundation problem. It implements F-01 through F-09 once. Each agent installs it as a local dependency:

```toml
# agents/catalog/pyproject.toml
[tool.poetry.dependencies]
pim_core = { path = "../../pim_core", develop = true }
```

This means:
- The LLM provider abstraction, pgvector client, audit logger, HITL helpers, and Pydantic schemas are **written once**.
- Each agent service gets its own **connection pool**, **process memory**, and **runtime** — there is no shared state at runtime.
- Upgrading `pim_core` is a dependency bump in each agent's `pyproject.toml`, reviewed and deployed independently per agent.

---

## Resolved Design Decisions

### MCP Server — One Per Agent

Each agent runs its **own FastMCP server**, exposing only the tools that belong to that agent. The LangGraph orchestrator within each agent knows which MCP server to hit because it is colocated in the same service.

There is no cross-agent tool discovery requirement at this stage. If a future workflow requires the Catalog Agent to call a Content Agent tool, that is modelled as an HTTP call between services (not MCP), and documented as a new ADR at that point.

| Agent | MCP tools exposed |
|---|---|
| Catalog | `classify_product`, `tag_product`, `sequence_images`, `check_data_quality`, `bulk_update_products` |
| Content | `generate_description`, `extract_label_data`, `enrich_product`, `enhance_image`, `translate_content` |
| Procurement | `search_catalog`, `compare_products`, `check_procurement_rules`, `raise_purchase_order`, `find_substitutes` |

### Database — Shared PostgreSQL, Isolated Connection Pools

All three agents connect to the **same PostgreSQL instance** (which also runs pgvector for F-08). Each agent service maintains its **own connection pool** (SQLAlchemy 2.0 async engine). This is standard practice for microservice-to-database connectivity and requires no additional infrastructure.

Read-only DB views (C-03) remain in the shared `db/views/` directory and are deployed via Alembic, independent of any agent deployment.

### Auth — JWT Validation in `pim_core`

The JWT validation logic lives in `pim_core/auth/`. All three agents import and apply it identically. JWT issuance remains centralised — either a dedicated identity provider or the same FastAPI dependency injected into each service's startup. No auth microservice is added at this stage.

### HITL Framework — Redis as the Shared Bus

The HITL approval flow (F-07) works across service boundaries naturally because it uses Redis pub/sub as the communication layer (already in the stack per ADR-004). An agent publishes an approval request to a Redis channel. The SSE stream (consumed by the reviewer's browser) is served by the agent that raised the request. The ARQ worker that resumes the paused job is colocated with that same agent's worker process. No cross-service coordination is required.

### Audit Log — Shared PostgreSQL Table, Written Independently

Each agent writes to the **same** `audit_log` PostgreSQL table using the `pim_core/audit/` logger. Because it is a database write (not a service call), there is no inter-service dependency. The append-only guarantee is enforced at the database constraint level.

---

## Local Development

`docker-compose.yml` brings up all services together for local development:

```yaml
services:
  postgres:         # Shared DB + pgvector
  redis:            # Shared — ARQ queues, HITL pub/sub, caching
  catalog:          # agents/catalog — port 8001
  content:          # agents/content — port 8002
  procurement:      # agents/procurement — port 8003
  catalog_worker:   # ARQ worker for catalog background jobs
  content_worker:   # ARQ worker for content background jobs
  procurement_worker: # ARQ worker for procurement background jobs
```

In production, each service is deployed independently (Kubernetes, ECS, or equivalent). The shared infrastructure (PostgreSQL, Redis) is managed separately.

---

## Trade-offs Accepted

| Trade-off | Mitigation |
|---|---|
| Three deployment pipelines instead of one | Justified by independent deployability requirement. Each pipeline is identical in structure — parameterised by agent name. |
| Three ARQ worker processes instead of one | Each agent's background jobs (patrol, onboarding) run in isolation. A runaway job in one agent does not delay jobs in another. Accepted overhead. |
| `pim_core` version discipline required | A breaking change to `pim_core` must be coordinated across three agent deployments. Mitigated by semantic versioning and a clear compatibility policy: `pim_core` minor versions are backwards-compatible; major versions require coordinated upgrades. |
| More complex local dev setup than a monolith | `docker-compose.yml` abstracts this. A single `docker compose up` starts all services. |

---

## Architecture Principles (Unchanged from Original ADR)

| Principle | What it means in practice |
|---|---|
| **Shared infrastructure, isolated logic** | Foundation services are implemented in `pim_core` (shared code). Agent business logic is isolated in separate services. No agent imports from another agent's package. |
| **Event-driven, not time-driven where possible** | Agent workflows trigger on events (new product ingested, quality score drops, inventory threshold crossed) rather than scanning the full catalog on a timer. |
| **Feature tables, not raw tables** | Agent tools consume REST APIs and pre-computed DB views. No tool queries raw product tables directly. |
| **Confidence-gated escalation** | Every AI decision carries a confidence score. Below the configured threshold, the agent escalates to a human. Thresholds are configurable per tool. |
| **Every action is reversible or approved** | Irreversible actions require HITL approval. All write actions create a versioned history record to enable rollback. |
| **Abstract your LLM provider** | All LLM calls go through `pim_core/llm/provider.py`. The concrete implementation can be swapped without touching agent code. |
| **Treat prompts as deployable artifacts** | System prompts are stored in LangSmith, versioned, and deployed independently of code. |
| **Tier your model usage by cost** | Claude Sonnet for high-throughput, low-complexity tools. Claude Opus for complex reasoning only. |

---

## Build Sequence (Unchanged)

| Phase | Tasks | Key deliverables |
|---|---|---|
| **Phase 1 — Shared Foundation** | F-01 to F-09 | `pim_core` package complete; LLM selected; LangGraph configured; MCP base config; auth and audit log; HITL framework; pgvector seeded |
| **Phase 2 — Agent 1: Catalog** | C-01 to C-16 | Catalog service live; classify, tag, sequence, quality tools; onboarding and patrol workflows; catalog dashboard |
| **Phase 3 — Agent 3: Content** | E-01 to E-15 | Content service live; label extraction; description generation; enrichment; image enhancement; nightly patrol |
| **Phase 4 — Agent 2: Procurement** | P-01 to P-17 | Procurement service live; catalog query; pricing and inventory APIs; PO creation; substitution logic; ERP integration |

---

*PIM-AI · Service Architecture README · April 2026 · Confidential — Engineering Use Only*
