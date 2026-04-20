# agents — Agent Microservices

Each subdirectory is a self-contained FastAPI microservice for one PIM-AI agent.

## Current agents

| Agent | Port | Purpose |
|-------|------|---------|
| `product_description_generator/` | 8002 | Generates SEO-optimised product descriptions from raw PIM records |

## Planned agents (future)

| Agent | Purpose |
|-------|---------|
| `catalog/` | Catalog Management — classifies, tags, sequences images |
| `procurement/` | Procurement/Buying — searches catalog, raises POs |

## Conventions

Every agent directory contains:
- `main.py` — FastAPI app instance
- `tools/` — FastMCP tools (the agent's callable actions)
- `workflows/` — LangGraph StateGraphs (the agent's reasoning loops)
- `prompts/` — Prompt template builders (separated from execution logic)
- `routes/` — FastAPI routers for admin/config endpoints

## Agent identity in the model registry

The agent name string used in `AgentModelRegistry` matches the directory name and the value
of the corresponding `AllAgents` enum entry.

**Register a new agent in `pim_core/utils/all_agents.py` first** before writing any code.

| Directory | Registry key (`AllAgents` enum value) |
|-----------|---------------------------------------|
| `product_description_generator/` | `"product_description_generator"` |
| `catalog/` _(planned)_ | `"catalog"` |
| `procurement/` _(planned)_ | `"procurement"` |
