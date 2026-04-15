# PIM-AI — Project Overview

## What is this project?

**PIM-AI** (Product Information Management — AI) is an AI-powered platform built on top of a PIM system. It automates catalog management, procurement, and content enrichment workflows using multi-agent AI architecture.

The broader customer intelligence platform is called **Custonomy** — a signal-driven, supervisor-orchestrated, feature-store-backed decision platform designed to optimize customer revenue, retention, and engagement.

---

## Core Principle

> "Process once, decide many times"
> "Agents consume feature tables, not raw data"

Every agent in the system reads from a shared feature layer and signal layer — never directly from raw enterprise tables (orders, campaign logs, customer master, etc.).

---

## Two Distinct Platforms in this Project

### 1. PIM-AI (Product Intelligence)
Focuses on managing, enriching, and publishing product catalog data. Has 3 agents and 8 AI-powered features. Target audience: catalog managers, content teams, merchandisers, procurement teams.

### 2. Custonomy (Customer Intelligence)
Focuses on customer revenue recovery, retention, campaign optimization, and experience. Has a multi-supervisor, multi-child-agent architecture. Target audience: marketing teams, CRM managers, business analysts.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Agent orchestration | LangGraph |
| API layer | FastAPI |
| LLM | Claude API (Anthropic) |
| Real-time task queue | ARQ + Redis |
| Tool protocol | FastMCP (MCP) |
| Operational database | PostgreSQL + pgvector |
| Data/ML infrastructure | Databricks (optional, for scale) |
| Vector search | pgvector (co-located with PostgreSQL) |

---

## Human-in-the-Loop Model

Every final recommendation or irreversible agent action goes through:
1. User review
2. Approval / modification / rejection
3. Downstream activation

Agents escalate to humans when confidence is below threshold or when actions exceed configured limits.

---

## Key Documents in This Knowledge Base

| File | Contents |
|------|----------|
| [pim-ai-core-features.md](pim-ai-core-features.md) | 8 PIM-AI product features |
| [customer-features-and-signals.md](customer-features-and-signals.md) | 15 customer metrics with formulas |
| [business-features.md](business-features.md) | 7 business-level metrics with formulas |
| [multi-agent-architecture.md](multi-agent-architecture.md) | Custonomy 8-layer architecture |
| [agent-development-tasks.md](agent-development-tasks.md) | Dev task list for 3 PIM-AI agents |
| [databricks-integration.md](databricks-integration.md) | Databricks role in the architecture |
