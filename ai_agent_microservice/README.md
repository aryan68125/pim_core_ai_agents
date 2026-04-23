# PIM AI Agent Microservice

A production-ready FastAPI microservice that powers AI agents for a Product Information Management (PIM) system. Agents generate SEO-optimised product content using any major LLM provider — Anthropic Claude, OpenAI GPT, or Google Gemini — switchable at runtime without restarting the service.

---

## Table of Contents

1. [Python Version and Dependencies](#1-python-version-and-dependencies)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Running the Project](#4-running-the-project)
5. [API Reference](#5-api-reference)
6. [Directory Structure](#6-directory-structure)
7. [Phase 1 — Content Agent (Product Description Generator)](#7-phase-1--content-agent-product-description-generator)
8. [Phase 2 — Multi-LLM Provider Layer](#8-phase-2--multi-llm-provider-layer)
9. [Architecture Diagram](#9-architecture-diagram)
10. [Theory and References](#10-theory-and-references)
11. [Running Tests](#11-running-tests)
12. [Knowledge Graph (graphify)](#12-knowledge-graph-graphify)
13. [Shared vs Agent-Specific Code](#13-shared-vs-agent-specific-code)
14. [Deep Dive — LangGraph, FastMCP, and How Everything Works Together](#14-deep-dive--langgraph-fastmcp-and-how-everything-works-together)
15. [Deep Dive — The LLM Provider Layer (base, providers, client, factory, registry)](#15-deep-dive--the-llm-provider-layer-pim_corellm)
16. [Deep Dive — Prompts, Routes, Tools, and Workflows](#16-deep-dive--prompts-routes-tools-and-workflows)
17. [Logging Architecture (CloudWatch + Provider Pattern)](#17-logging-architecture-cloudwatch--provider-pattern)

---

## 1. Python Version and Dependencies

**Python:** 3.13.7 (tested with CPython from Miniconda)

---

### Tech Stack by Layer

| Layer | Technology | Role |
|---|---|---|
| **Web Framework** | FastAPI | REST API — route definitions, request/response handling, automatic OpenAPI docs |
| **Web Framework** | Uvicorn | ASGI server — runs the FastAPI app in production and development |
| **Web Framework** | Starlette | ASGI toolkit underlying FastAPI — middleware, routing, request lifecycle |
| **AI / LLM Provider** | Anthropic Claude SDK | SDK for Claude models (Sonnet, Opus, Haiku) |
| **AI / LLM Provider** | OpenAI SDK | SDK for GPT-4o, o1, o3, o4 models |
| **AI / LLM Provider** | Google Generative AI SDK | SDK for Gemini models |
| **Agent Orchestration** | LangGraph | StateGraph-based agent workflow — each agent is a directed computation graph |
| **Agent Orchestration** | LangChain Core | Base abstractions (messages, runnables) used by LangGraph |
| **Data Validation & Config** | Pydantic | Runtime type validation for all request/response models and internal data schemas |
| **Data Validation & Config** | Pydantic-Settings | Loads and validates environment variables from `.env` at startup |
| **MCP Protocol** | FastMCP | Registers agent tools as Model Context Protocol endpoints — lets external AI agents call this service |
| **Security** | PyJWT | JWT encoding and decoding — used for service-to-service authentication |
| **HTTP Client** | HTTPX | Async HTTP client — used by FastAPI test client and internal HTTP calls |
| **Testing** | pytest | Test runner |
| **Testing** | pytest-asyncio | Async test support for FastAPI async routes |
| **Testing** | pytest-cov | Test coverage reporting |

---

### All Dependencies

**Core runtime dependencies:**

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.136.0 | REST API framework |
| `uvicorn` | 0.44.0 | ASGI server |
| `starlette` | 1.0.0 | ASGI toolkit underlying FastAPI |
| `pydantic` | 2.13.1 | Data validation and serialisation |
| `pydantic-settings` | 2.13.1 | `.env` file config loading |
| `langgraph` | 1.1.8 | Agent orchestration graph |
| `langchain-core` | 1.3.0 | Base abstractions used by LangGraph |
| `anthropic` | 0.96.0 | Anthropic Claude SDK |
| `openai` | 2.32.0 | OpenAI GPT SDK |
| `google-generativeai` | 0.8.6 | Google Gemini SDK |
| `fastmcp` | 3.2.4 | Model Context Protocol tool registration |
| `PyJWT` | — | JWT encoding / decoding for service-to-service auth |
| `httpx` | 0.28.1 | Async HTTP client (used by test client and internal calls) |
| `python-dotenv` | — | `.env` file parsing |

**Optional provider packages — install only what you need:**

```bash
pip install openai              # for GPT-4o, o1, o3, o4 models
pip install google-generativeai  # for Gemini models
```

**Test dependencies:**

| Package | Purpose |
|---|---|
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Coverage reporting |

---

## 2. Installation

### Step 1 — Clone the repository

```bash
git clone <repo-url>
cd pim_core_ai_agents/ai_agent_microservice
```

### Step 2 — Create a virtual environment

```bash
python3.13 -m venv venv
```

### Step 3 — Activate the virtual environment

```bash
# Linux / macOS
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Create your `.env` file

Copy the template and fill in your API key:

```bash
cp .env .env.local  # optional backup
```

Edit `.env`:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-your-real-key-here

# Optional — only needed for GPT models
OPENAI_API_KEY=

# Optional — only needed for Gemini models
GOOGLE_API_KEY=

# App settings (defaults are fine)
ENVIRONMENT=development
LOG_LEVEL=INFO
CLAUDE_MODEL=claude-sonnet-4-6
```

---

## 3. Configuration

All configuration is loaded from `.env` at startup via `pim_core/config.py` using `pydantic-settings`.

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key. Get one at console.anthropic.com |
| `OPENAI_API_KEY` | No | `None` | OpenAI API key. Required only when you switch an agent to a GPT model |
| `GOOGLE_API_KEY` | No | `None` | Google API key. Required only when you switch an agent to a Gemini model |
| `ENVIRONMENT` | No | `development` | Runtime environment label |
| `LOG_LEVEL` | No | `INFO` | Python logging level |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-6` | Default model used when no model is explicitly assigned to an agent |

---

## 4. Running the Project

Run from inside the `ai_agent_microservice/` directory:

```bash
venv/bin/python -m uvicorn agents.product_description_generator.main:app --reload --port 8001
```

The `--reload` flag enables hot-reloading during development — the server restarts automatically when you change a source file. Remove it for production.

Once the server is running, visit:

- **Interactive API docs (Swagger UI):** `http://localhost:8001/docs`
- **Alternative docs (ReDoc):** `http://localhost:8001/redoc`

---

## 5. API Reference

### Health Check

```
GET /health
```

Response:
```json
{ "status": "ok", "agent": "content" }
```

---

---

---

### Generate a description directly from a PIM record

```
POST /agents/generate-description
Content-Type: application/json
```

Accepts a product record **exactly as exported from the PIM system** — no field mapping required by the caller. The adapter layer handles the conversion internally.

The `pim_record` accepts exactly **13 fields** — all optional (empty string, empty array, or null are all valid). Any additional keys in the JSON payload are silently ignored.

Request body:

```json
{
  "pim_record": {
    "productID": 705517,
    "productName": "MACSTUDIO E25 M4M/64/1TB",
    "coordGroupDescription": "APPLE DESKTOP SYSTEMS",
    "ipManufacturer": "APPLE",
    "productDescription": "MACSTUDIO E25 M4M/64/1TB",
    "copy1": "Apple Mac Studio with M4 Max chip — the most powerful desktop for pro workflows.",
    "posDescription": "MACSTUDIO E25 M4M/64/1TB",
    "warranty": "1 year",
    "vendorStyle": "15098309",
    "webManufacturer": "Apple Inc",
    "suggestedWebcategory": "Computers<br />Desktop Computers",
    "productType": "Hardware",
    "categorySpecificAttributes": []
  },
  "channel": "ecommerce",
  "brand_voice": {
    "tone": "professional",
    "keywords": ["Mac Studio", "M4 Max", "workstation"],
    "locale": "en-GB"
  }
}
```

`brand_voice` is optional.

**Field mapping applied by the adapter:**

| PIM field | Maps to | Notes |
|---|---|---|
| `productID` | `Product.id` | Cast to string |
| `productName` | `Product.name` | |
| `coordGroupDescription` | `Product.category` | Trailing spaces stripped |
| `ipManufacturer` | `Product.attributes.brand` | Empty string → `None` |
| `copy1` | `existing_description` | 1st priority |
| `productDescription` | `existing_description` | 2nd priority fallback |
| `posDescription` | `existing_description` | 3rd priority fallback |
| `warranty` | `additional["warranty"]` | Omitted if empty |
| `vendorStyle` | `additional["vendor_part_number"]` | Omitted if empty |
| `webManufacturer` | `additional["web_manufacturer"]` | Omitted if empty |
| `suggestedWebcategory` | `additional["web_category"]` | Omitted if empty |
| `productType` | `additional["product_type"]` | Omitted if empty |
| `categorySpecificAttributes` | `additional["category_attributes"]` | JSON-serialised; omitted when `[]` |

`existing_description` is set to the first of `copy1`, `productDescription`, `posDescription` that is non-empty **and** different from the product name (to avoid sending the LLM a description that just repeats the name).

Returns a `DescriptionResult` — same schema as shown above.

---

---

### List all available models

```
GET /models/available
```

Returns the full catalogue of models supported by the provider layer, grouped by provider.

```json
{
  "anthropic": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
  "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o1-mini", "o3-mini", "o4-mini"],
  "google": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
}
```

---

### Assign a model to any agent

```
POST /agents-settings/{agent_name}/model
Content-Type: application/json
```

```json
{ "model": "gpt-4o" }
```

Takes effect immediately — no restart required. Any agent registered under `agent_name` in the registry will use the new model on its next LLM call.

| HTTP status | Meaning |
|---|---|
| 200 | Model assigned |
| 400 | Model prefix not recognised by any provider |

Response:

```json
{ "agent": "content", "model": "gpt-4o" }
```

---

### View all agent model assignments

```
GET /agents-settings/models
```

Returns every agent that has been explicitly assigned a model, plus the default fallback from `.env`.

```json
{
  "registry": {
    "content": "gpt-4o",
    "catalog": "gemini-2.0-flash"
  },
  "default_model": "claude-sonnet-4-6"
}
```

Agents not listed in `registry` automatically use `default_model`.

---

### Reset an agent to the default model

```
DELETE /agents-settings/{agent_name}/model
```

Removes the explicit assignment. The agent reverts to `default_model` from `.env`.

```json
{ "agent": "content", "model": "claude-sonnet-4-6" }
```

---

### Example: Switch to GPT-4o then generate

```bash
# 1. Switch model for the product_description_generator agent
curl -X POST http://localhost:8002/agents/product_description_generator/model \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o"}'

# 2. Generate description (now uses GPT-4o)
curl -X POST http://localhost:8001/agents/generate-description \
  -H "Content-Type: application/json" \
  -d '{
    "pim_record": {
      "productID": 1,
      "productName": "Standing Desk",
      "coordGroupDescription": "Furniture"
    },
    "channel": "wholesale"
  }'
```

### Example: Generate directly from PIM export data

```bash
curl -X POST http://localhost:8001/agents/generate-description \
  -H "Content-Type: application/json" \
  -d '{
    "pim_record": {
      "productID": 705511,
      "shortSku": "968909",
      "productName": "2-BAY NASYNC DH2300",
      "coordGroupDescription": "SMB NETWORK/NAS DRV ENCL",
      "ipManufacturer": "UGREEN",
      "warranty": "1 year",
      "vendorStyle": "95432"
    },
    "channel": "ecommerce"
  }'
```

---

## 6. Directory Structure

```
ai_agent_microservice/
│
├── .env                          # API keys and app settings (not committed)
├── pytest.ini                    # Test runner config
├── requirements.txt              # All Python dependencies
├── CONTEXT.md                    # Root-level orientation for AI and humans
│
├── pim_core/                     # Shared infrastructure — never imports from agents/
│   ├── config.py                 # Settings singleton — loads .env via pydantic-settings
│   ├── schemas/
│   │   ├── product.py            # Pydantic models: Product, BrandVoice, DescriptionResult
│   │   └── pim_product.py        # PIMProductRecord — 13 selected PIM fields (extra="ignore")
│   ├── adapters/
│   │   └── pim_adapter.py        # pim_record_to_product() — PIM → Product mapping
│   ├── utils/
│   │   ├── all_available_models.py  # Enums: AllAvailableModelsAnthropic/OpenAI/Google
│   │   └── all_agents.py            # Enum: AllAgents — register agents here first
│   ├── db/
│   │   ├── agent_model_db.py     # SQLite helpers: load_all / upsert / delete
│   │   └── agent_models.db       # SQLite database file (auto-created, not committed)
│   └── llm/
│       ├── client.py             # Provider-agnostic LLMClient — the public interface
│       ├── factory.py            # Routes model names to provider instances (factory pattern)
│       ├── registry.py           # AgentModelRegistry — agent-to-model runtime map
│       └── providers/
│           ├── base.py           # BaseLLMProvider ABC — defines the contract
│           ├── anthropic_provider.py   # Anthropic Claude implementation
│           ├── openai_provider.py      # OpenAI GPT implementation (lazy import)
│           └── google_provider.py      # Google Gemini implementation (lazy import)
│
├── agents/
│   └── product_description_generator/  # Product Description Generator Agent
│       ├── main.py               # FastAPI app — mounts all routers
│       ├── routes/
│       │   ├── product_description_generator_api_route.py  # POST /agents/generate-description — raw PIM record ingestion
│       │   └── agent_registry.py # GET /models/available · POST|GET|DELETE /agents-settings/* — global registry API
│       ├── workflows/
│       │   └── description_workflow.py  # LangGraph StateGraph — orchestrates the LLM call
│       ├── tools/
│       │   └── generate_description.py  # FastMCP tool — invokes the graph, returns DescriptionResult
│       └── prompts/
│           └── brand_voice.py    # Prompt builders — system prompt + user message from BrandVoice
│
└── tests/
    ├── conftest.py               # Shared pytest fixtures
    ├── test_config.py            # Settings loading tests
    ├── test_schemas.py           # Pydantic schema validation tests
    ├── test_llm_client.py        # LLMClient delegation tests
    ├── test_llm_factory.py       # Provider routing and caching tests
    ├── test_llm_registry.py      # AgentModelRegistry behaviour tests
    └── product_description_generator/
        ├── test_brand_voice.py              # Prompt builder output tests
        ├── test_description_workflow.py     # LangGraph graph node tests
        ├── test_generate_description_tool.py # MCP tool integration tests
        └── test_main.py                     # FastAPI endpoint tests
```

### What each file is responsible for and why it exists

**`pim_core/config.py`**
Loads all environment variables at startup into a single `Settings` object. Every part of the application imports `settings` from here instead of calling `os.getenv()` directly. This gives one place to change, validate, and document all configuration.

**`pim_core/schemas/product.py`**
Defines the data contracts the entire system speaks. `Product` is what comes in from the PIM system. `BrandVoice` controls how the copy sounds. `DescriptionResult` is what the agent returns. Using Pydantic models here means FastAPI validates request bodies automatically and any invalid input is rejected before the LLM is ever called.

**`pim_core/llm/client.py`**
The only way any agent touches an LLM. It accepts a `model` name and delegates to the right provider. Agents never import providers directly — only `LLMClient`. This means you can change how providers work without touching agent code.

**`pim_core/llm/factory.py`**
Reads the model name prefix and returns the matching provider instance. Instances are cached in a module-level dict so each provider SDK is initialised only once per process. This is the factory pattern — callers ask for what they want by name, not by constructing it themselves.

**`pim_core/llm/registry.py`**
An in-memory map of `agent_name → model_name` backed by SQLite. When the operator calls `POST /agents-settings/{name}/model`, the registry is updated and persisted. When the agent's workflow runs, it reads from the registry to find its current model. If no model has been set for an agent, it falls back to `settings.claude_model`. This is what makes model switching possible at runtime without restart.

**`pim_core/llm/providers/base.py`**
The abstract interface that all providers must satisfy. If a new provider is written (e.g. Mistral, Cohere), it must implement `complete()` with this exact signature. This enforces the contract so `LLMClient` can call any provider the same way.

**`pim_core/llm/providers/anthropic_provider.py`**
Wraps `anthropic.AsyncAnthropic`. Reads `ANTHROPIC_API_KEY` from settings. Always imported — Claude is the default and always required.

**`pim_core/llm/providers/openai_provider.py`**
Wraps `openai.AsyncOpenAI`. Uses lazy imports — the `openai` package is not imported at startup. It is only imported when an agent is first switched to a GPT model. This means the service starts fine even if `openai` is not installed.

**`pim_core/llm/providers/google_provider.py`**
Wraps `google.generativeai`. Same lazy import pattern as OpenAI. Converts the shared message format into Gemini's format (role must be `"user"` or `"model"`, content goes in a `parts` array).

**`agents/product_description_generator/main.py`**
The FastAPI application entry point for the Product Description Generator. Mounts the PIM ingest router (`POST /agents/generate-description`) and the agent registry router. Thin — all logic lives in the tool and workflow layers below.

**`agents/product_description_generator/workflows/description_workflow.py`**
A LangGraph `StateGraph` with a single node: `generate_node`. This node reads the current model from the registry, builds the prompt, calls the LLM via `LLMClient`, and parses the JSON response. Errors are caught inside the node and stored in `state["error"]` rather than being raised — this keeps the graph always terminating cleanly.

**`agents/product_description_generator/tools/generate_description.py`**
A FastMCP tool that is the public entry point invoked by the FastAPI endpoint. It initialises the graph state, runs the graph with `ainvoke()`, checks for errors, and assembles the final `DescriptionResult`.

**`agents/product_description_generator/prompts/brand_voice.py`**
Pure functions that build the system prompt and user message from a `BrandVoice` and `Product`. No LLM calls here — just string assembly. Kept separate so prompts can be read, tested, and iterated on without touching the workflow.

---

## 7. Phase 1 — Content Agent (Product Description Generator)

### Goal

Build the Content Agent: a FastAPI microservice that accepts a product and brand voice configuration, runs a LangGraph orchestration graph, calls Claude, and returns a structured JSON description result.

### What was built

**Shared schemas (`pim_core/schemas/product.py`)**

Three Pydantic models define the data contract:
- `Product` — the product coming in from the PIM system (id, sku, name, category, attributes)
- `BrandVoice` — how the generated copy should sound (tone, keywords to include, words to avoid, length limits, locale)
- `DescriptionResult` — the structured output (title, description, seo_keywords, word_count, model_used)

**Prompt builders (`agents/product_description_generator/prompts/brand_voice.py`)**

Two pure functions:
- `get_system_prompt(brand_voice)` — builds the LLM system prompt. Tells the model it is a product copywriter, sets tone, length constraints, locale, and instructs it to respond only with valid JSON in a specific format.
- `get_user_message(product, channel)` — builds the user turn. Formats product attributes into a readable block and includes the target channel.

Keeping prompts in their own module means they can be iterated without touching the orchestration graph.

**LangGraph workflow (`agents/product_description_generator/workflows/description_workflow.py`)**

A `StateGraph` with one node (`generate_node`) and one edge to `END`. The state is a `TypedDict` carrying: product, channel, brand_voice, title, description, seo_keywords, and error.

`generate_node` does:
1. Reads the system prompt and user message from the prompt builders
2. Calls `llm_client.complete()` with the assembled messages
3. Parses the JSON response from the LLM
4. Returns the parsed fields, or sets `error` in the state if parsing fails

Errors are caught inside the node rather than raising mid-graph. This ensures the graph always reaches `END` cleanly — the caller checks `state["error"]` after the graph finishes.

**FastMCP tool (`agents/product_description_generator/tools/generate_description.py`)**

Wraps the graph in a FastMCP `@mcp.tool()` decorated function. Initialises the state dict, calls `description_graph.ainvoke(state)`, raises `ValueError` if `state["error"]` is set, otherwise assembles and returns `DescriptionResult`.

**FastAPI app (`agents/product_description_generator/main.py`)**

Exposes one endpoint:
- `GET /health` — liveness check

The `POST /agents/generate-description` endpoint is mounted via the PIM ingest router.

**Tests written in Phase 1 (34 tests):**
- `test_brand_voice.py` — 10 tests covering prompt builder output
- `test_description_workflow.py` — 4 tests covering graph node behaviour
- `test_generate_description_tool.py` — 4 tests covering tool integration
- `test_main.py` — 4 tests covering HTTP endpoints
- `test_config.py` — 3 tests covering settings
- `test_schemas.py` — 6 tests covering Pydantic models
- `test_llm_client.py` — 3 tests covering LLM client delegation

---

## 8. Phase 2 — Multi-LLM Provider Layer

### Goal

Remove the hard dependency on Claude. Let operators switch any agent to OpenAI GPT or Google Gemini at runtime via a REST API call, without restarting the service.

### Requirements

- One agent has exactly one model assigned at a time
- Multiple agents can share the same model
- The model assignment is changed via `POST /agents-settings/{agent_name}/model`
- Switching takes effect on the next generate call, no restart required
- The service must start even if OpenAI or Google packages are not installed

### What was built

**`BaseLLMProvider` ABC (`pim_core/llm/providers/base.py`)**

An abstract base class with one abstract method: `complete(model, system, messages, max_tokens)`. This is the contract every provider must satisfy. By programming against this interface, `LLMClient` can call any provider identically.

**Three concrete providers**

`AnthropicProvider` wraps `anthropic.AsyncAnthropic`. It is always available (Anthropic is a hard dependency). Reads API key from `settings.anthropic_api_key`.

`OpenAIProvider` wraps `openai.AsyncOpenAI`. Uses lazy imports — `openai` is only imported inside `__init__`, which is only called when a GPT model is first requested. If the `openai` package is not installed, a clear `ImportError` with a `pip install` instruction is raised at that point. OpenAI's chat format requires the system prompt as the first message in the messages list, so the provider prepends it automatically.

`GoogleProvider` wraps `google.generativeai`. Same lazy import pattern. Gemini's API uses a different message format (`role` must be `"user"` or `"model"`, content goes in a `parts` array), so the provider converts the shared format before calling the SDK.

**Factory (`pim_core/llm/factory.py`)**

`get_provider(model_name)` routes by prefix:
- `claude-*` → `AnthropicProvider`
- `gpt-*`, `o1-*`, `o3-*`, `o4-*` → `OpenAIProvider`
- `gemini-*` → `GoogleProvider`
- anything else → `ValueError` with a clear message listing supported prefixes

Provider instances are cached in a module-level `_instances` dict. Each SDK client is created once and reused on every subsequent call. This avoids creating a new HTTP connection pool on every request.

**Registry (`pim_core/llm/registry.py`)**

`AgentModelRegistry` is a module-level singleton that holds a `dict[str, str]` mapping agent names to model names. It has four methods:
- `set(agent, model)` — assign a model to an agent
- `get(agent)` — return the assigned model, or fall back to `settings.claude_model`
- `all()` — snapshot of all current assignments
- `remove(agent)` — clear assignment (reverts to default)

The `get()` method imports `settings` lazily (inside the method body) to avoid circular imports at module load time.

**Refactored `LLMClient` (`pim_core/llm/client.py`)**

The client now delegates to the factory instead of constructing an `AsyncAnthropic` directly. It accepts an optional `model` parameter. If no model is passed, it falls back to `settings.claude_model`. This makes it provider-agnostic.

**Workflow update (`agents/product_description_generator/workflows/description_workflow.py`)**

`generate_node` calls `agent_model_registry.get(AllAgents.PRODUCT_DESCRIPTION_GENERATOR.value)` to discover its current model before calling the LLM. This is the line that connects the runtime registry to the LLM call.

**Agent registry router (`agents/product_description_generator/routes/agent_registry.py`)**

Four endpoints covering the full lifecycle:
- `GET /models/available` — returns all supported models from the `AllAvailableModels*` enums
- `POST /agents-settings/{name}/model` — validates the model exists in an enum, then writes to registry + SQLite
- `GET /agents-settings/models` — returns all current assignments and the default fallback
- `DELETE /agents-settings/{name}/model` — removes an assignment, reverting that agent to the default

**Tests written in Phase 2 (10 new tests, 48 total):**
- `test_llm_factory.py` — 5 tests: Anthropic routing, OpenAI routing, Google routing, instance caching, unknown prefix error
- `test_llm_registry.py` — 5 tests: default fallback, set/get, multiple agents, all() snapshot, remove reverts to default

---

## 9. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        HTTP Client / cURL                        │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
  POST /agents/generate-description   POST /agents-settings/{name}/model
                                      GET  /agents-settings/models
  GET  /health                        GET  /models/available
                │                               │
                │        agents/product_description_generator/main.py │
                │        (FastAPI application)  │
                │                               │
                ▼                               ▼
  tools/generate_description.py    routes/agent_registry.py
  (FastMCP tool)                   (APIRouter)
        │                                │
        │                                │ validates model in enum
        │                                ▼
        │                         pim_core/llm/factory.py
        │                         get_provider(model)
        │                                │
        │                                ▼
        │                         pim_core/llm/registry.py + SQLite
        │                         agent_model_registry.set(...)
        │
        ▼
  workflows/description_workflow.py
  (LangGraph StateGraph)
        │
        ├── prompts/brand_voice.py
        │   get_system_prompt(brand_voice)
        │   get_user_message(product, channel)
        │
        ├── pim_core/llm/registry.py
        │   agent_model_registry.get("content")
        │              │
        │              │ returns model name (or default claude model)
        │              ▼
        └── pim_core/llm/client.py
            LLMClient.complete(model=..., system=..., messages=...)
                       │
                       ▼
            pim_core/llm/factory.py
            get_provider(model_name)
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
  AnthropicProvider  OpenAIProvider  GoogleProvider
  (claude-*)         (gpt-*, o1-*)   (gemini-*)
          │            │            │
          ▼            ▼            ▼
  Anthropic SDK    OpenAI SDK    Google GenAI SDK
  (AsyncAnthropic) (AsyncOpenAI) (GenerativeModel)
          │            │            │
          └────────────┴────────────┘
                       │
                       ▼
              raw text response
                       │
                       ▼
  json.loads() → {title, description, seo_keywords}
                       │
                       ▼
              DescriptionResult
              {product_id, channel, title,
               description, seo_keywords,
               word_count, model_used}
                       │
                       ▼
              HTTP 200 JSON response


Shared data models (pim_core/schemas/product.py):

  ┌─────────────┐    ┌────────────┐    ┌──────────────────┐
  │   Product   │    │ BrandVoice │    │ DescriptionResult│
  │─────────────│    │────────────│    │──────────────────│
  │ id          │    │ tone       │    │ product_id       │
  │ sku         │    │ keywords   │    │ channel          │
  │ name        │    │ avoid_words│    │ title            │
  │ category    │    │ max_title  │    │ description      │
  │ attributes  │    │ max_desc   │    │ seo_keywords     │
  │ image_urls  │    │ locale     │    │ word_count       │
  └─────────────┘    └────────────┘    │ model_used       │
                                       └──────────────────┘

Configuration (.env → pim_core/config.py → Settings singleton):

  ANTHROPIC_API_KEY ──► AnthropicProvider.__init__()
  OPENAI_API_KEY    ──► OpenAIProvider.__init__()   (checked lazily)
  GOOGLE_API_KEY    ──► GoogleProvider.__init__()   (checked lazily)
  CLAUDE_MODEL      ──► AgentModelRegistry.get() fallback
  LOG_PROVIDER      ──► LogProviderFactory.get_handler()  (cloudwatch | gcp | azure)


Cross-Cutting: Structured Logging (every component emits JSON log lines)

  FastAPI Middleware
  └── generates request_id (UUID per request)
  └── injects into Python contextvars — available to all downstream code
                │
                ▼
  Any component: Agent / Workflow / LLMClient / Registry / Routes
                │
                │  StructuredLogger.info() / .error() / .warning() / .debug()
                ▼
  pim_core/logging/logger.py  ← StructuredLogger (single entry point)
  └── attaches: level, timestamp, request_id, class, method, message
  └── python-json-logger → formats as JSON line
                │
                ▼
  pim_core/logging/factory.py  ← LogProviderFactory
  reads LOG_PROVIDER from .env
                │
      ┌─────────┼──────────┐
      │         │          │
      ▼         ▼          ▼
  cloudwatch   gcp       azure
      │         │          │
      ▼         ▼          ▼
  CloudWatch  GCP Cloud  Azure
  LogProvider Logging    Monitor
  (watchtower)(google-   (azure-monitor-
              cloud-     opentelemetry)
              logging)
      │         │          │
      └─────────┴──────────┘
                │
                ▼
     Cloud Log Aggregation Backend
     └── SQL-like queries (CloudWatch Insights / GCP Log Explorer / Azure Monitor)
     └── Metric filters + Alarms on ERROR rate
     └── Retention policy → cost control
```

---

## 10. Theory and References

### Design Patterns

**Strategy Pattern**

The core of the multi-LLM layer. `BaseLLMProvider` defines the interface (the strategy). Each provider (`AnthropicProvider`, `OpenAIProvider`, `GoogleProvider`) is a concrete strategy. `LLMClient` is the context — it holds no provider directly, it asks the factory for one. Swapping providers does not change any caller code.

> Reference: [Refactoring Guru — Strategy Pattern](https://refactoring.guru/design-patterns/strategy)

**Factory Pattern**

`get_provider(model_name)` in `factory.py` is a factory function. Callers say what they want (a model name) and the factory decides which class to instantiate. Callers never call `AnthropicProvider()` themselves. This is the Factory Method pattern applied as a plain function.

> Reference: [Refactoring Guru — Factory Method](https://refactoring.guru/design-patterns/factory-method)

**Singleton Pattern**

Three module-level singletons exist in this codebase:
- `settings` in `pim_core/config.py` — one config object per process
- `llm_client` in `pim_core/llm/client.py` — one client per process
- `agent_model_registry` in `pim_core/llm/registry.py` — one registry per process

Python modules are cached after first import, so a module-level variable is effectively a singleton.

> Reference: [Refactoring Guru — Singleton Pattern](https://refactoring.guru/design-patterns/singleton)

**Agent Pattern (Perceive → Plan → Act)**

Although Phase 1 has a single-node graph, the LangGraph `StateGraph` is already structured for the agent loop pattern. State flows through nodes; nodes perceive the current state, decide what to do, and produce new state. Future agents can add planning and tool-use nodes without changing the outer structure.

> Reference: [LangGraph — Concepts](https://langchain-ai.github.io/langgraph/concepts/)
> Reference: [ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2022)](https://arxiv.org/abs/2210.03629)

---

### Concurrency Model

FastAPI is built on Starlette and runs in an async event loop (via `asyncio`). All LLM calls use `async/await` throughout:
- `LLMClient.complete()` is `async`
- All provider `complete()` methods are `async`
- The LangGraph graph is invoked with `ainvoke()` (the async version of `invoke()`)
- The FastAPI endpoint uses `async def`

This means a single worker process can handle many concurrent requests without blocking — while one request waits for a Claude API response, the event loop handles other requests.

> Reference: [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
> Reference: [FastAPI — Async and Await](https://fastapi.tiangolo.com/async/)

---

### Prompt Engineering

The system prompt in `brand_voice.py` follows structured prompt design:
- **Role framing** — "You are a professional product copywriter specialising in e-commerce content" sets the model's persona before any instruction
- **Explicit output format** — the prompt instructs the model to respond only with valid JSON in a specific schema, making parsing reliable
- **Constraint injection** — tone, length limits, locale, keyword inclusions, and word exclusions are injected into the prompt from the `BrandVoice` config at runtime

> Reference: [Anthropic — Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
> Reference: [OpenAI — Prompt Engineering Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)

---

### Testing Strategy

**Where to patch in Python tests**

A critical subtlety in the test suite: when a module does `from pim_core.llm.factory import get_provider`, Python creates a local name binding in that module's namespace. Patching `pim_core.llm.factory.get_provider` does not affect that local binding. You must patch the name where it is used: `agents.product_description_generator.routes.agent_registry.get_provider`.

This is documented in the Python standard library under "Where to Patch":

> Reference: [Python docs — unittest.mock: Where to Patch](https://docs.python.org/3/library/unittest.mock.html#where-to-patch)

**Test isolation**

All LLM calls are mocked in tests using `unittest.mock`. No test makes a real API call. Provider constructors that check API keys are bypassed using `patch.object(ProviderClass, "__init__", return_value=None)` so tests focus on routing logic, not credentials.

> Reference: [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/en/latest/)

---

### Lazy Imports

`OpenAIProvider` and `GoogleProvider` import their SDKs inside `__init__` rather than at module top-level. This is intentional:
- The `openai` and `google-generativeai` packages are not in `requirements.txt` as hard dependencies
- The service starts and runs Claude-only without them installed
- The import error (if the package is missing) is raised at the moment a user first tries to switch to that provider — with a clear `pip install` message — not at server startup

> Reference: [Python docs — Import system](https://docs.python.org/3/reference/import.html)

---

### Pydantic Settings

`pydantic-settings` extends Pydantic to read configuration from environment variables and `.env` files. Fields are declared as typed class attributes. Required fields (no default) cause an immediate startup failure with a clear validation error if missing. Optional fields (typed as `T | None = None`) silently default to `None`.

> Reference: [pydantic-settings documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

## 11. Running Tests

From inside `ai_agent_microservice/`:

```bash
# Run all 48 tests
venv/bin/python -m pytest -v

# Run only Content Agent tests
venv/bin/python -m pytest tests/product_description_generator/ -v

# Run only LLM layer tests
venv/bin/python -m pytest tests/test_llm_factory.py tests/test_llm_registry.py tests/test_llm_client.py -v

# Run with coverage report
venv/bin/python -m pytest --cov=. --cov-report=term-missing
```

Expected output: **82 passed**.

No real API calls are made during tests. All LLM interactions are mocked.

---

## 12. Knowledge Graph (graphify)

The project uses [graphify](https://github.com/safishamsi/graphify) to maintain a navigable knowledge graph of the entire codebase, documentation, and knowledge base. The graph lives in `graphify-out/` at the project root (one level above `ai_agent_microservice/`).

### What it produces

| Output file | What it is |
|---|---|
| `graphify-out/graph.html` | Interactive graph — open in any browser, no server needed |
| `graphify-out/graph.json` | Raw graph data for programmatic querying |
| `graphify-out/GRAPH_REPORT.md` | Audit report: god nodes, surprising connections, suggested questions |

### Installation

graphify is a separate Python tool installed globally (not inside the project venv):

```bash
pip install graphifyy
```

Verify it installed correctly:

```bash
python3 -c "import graphify; print('ok')"
```

### Build the graph for the first time

Run from the **project root** (`pim_core_ai_agents/`), not from inside `ai_agent_microservice/`:

```bash
cd ..                  # move to pim_core_ai_agents/ if you're inside ai_agent_microservice/
/graphify .            # or: claude --skill graphify .
```

This scans all 65+ files (Python source, Markdown docs, PDFs, SVG diagrams), runs AST extraction on code files, and runs semantic extraction (via Claude) on documents. Outputs are written to `graphify-out/`.

### Update the graph after making changes

After editing files or adding new files:

```bash
/graphify . --update
```

graphify compares the current project state against its stored manifest and only re-extracts files that changed:

| Change type | Re-extraction needed | LLM call? |
|---|---|---|
| Python file modified | AST only | No |
| `.md` / `.txt` / `.pdf` added or changed | Semantic extraction | Yes (costs tokens) |
| File deleted | Ghost nodes pruned automatically | No |
| No changes since last run | Exits immediately with "Nothing to update" | No |

The manifest and extraction cache are stored in `graphify-out/`. Do not delete this folder between runs — it is what makes incremental updates fast and cheap.

### Full rebuild from scratch

Only needed if the graph has become significantly out of date or corrupted:

```bash
rm -rf graphify-out/
/graphify .
```

### Querying the graph

Once built, you can ask questions about the codebase directly:

```bash
/graphify query "how does model switching work"
/graphify query "what connects BrandVoice to the LLM call"
/graphify path "AgentModelRegistry" "AnthropicProvider"
/graphify explain "get_provider"
```

### Current graph stats

The graph as of the last run covers:

- **367 nodes** — code symbols, documentation concepts, design decisions, business signals
- **516 edges** — 66% extracted directly from source, 34% inferred by Claude
- **14 meaningful communities** — Content Agent Runtime, LLM Provider Layer, Model Config & Registry, Prompt Engineering, Agent Development Roadmap, Customer & Business Signals, and more
- **Top god nodes:** `BrandVoice` (20 edges), `Product` (19), `AgentModelRegistry` (17), `get_provider()` (12)

---

## 13. Shared vs Agent-Specific Code

> **Maintainer note:** Update this section every time a new agent is added or a new shared module is introduced in `pim_core/`.

Understanding what is shared and what is agent-specific is critical when adding new agents (Catalog, Procurement, etc.). The rule is simple: **if it lives in `pim_core/`, it belongs to everyone. If it lives in `agents/<name>/`, it belongs to that agent alone.**

---

### Shared — any agent can use this (`pim_core/`)

`pim_core/` is the shared foundation. No individual agent owns any file inside it. When you build a new agent, import from here — never from another agent's directory.

| File | What it provides |
|---|---|
| `pim_core/config.py` | `settings` singleton — API keys, default model name, environment, log level |
| `pim_core/schemas/product.py` | `Product`, `ProductAttributes`, `BrandVoice`, `DescriptionResult` — shared data contracts |
| `pim_core/schemas/pim_product.py` | `PIMProductRecord` — 13 fields selected for description generation. `extra = "ignore"` silently drops any unrecognised keys in the raw payload |
| `pim_core/adapters/pim_adapter.py` | `pim_record_to_product()` — adapter that maps a raw `PIMProductRecord` → normalised `Product` (strips trailing spaces, filters empty images, skips redundant descriptions) |
| `pim_core/utils/all_available_models.py` | `AllAvailableModelsAnthropic`, `AllAvailableModelsOpenAI`, `AllAvailableModelsGoogle` enums — single source of truth for every supported model name |
| `pim_core/utils/all_agents.py` | `AllAgents` enum — register every agent here before building it; used everywhere instead of bare string literals |
| `pim_core/db/agent_model_db.py` | SQLite persistence layer — `load_all()`, `upsert()`, `delete()` for agent → model assignments |
| `pim_core/llm/client.py` | `llm_client` — provider-agnostic async LLM caller. One line to call any LLM |
| `pim_core/llm/factory.py` | `get_provider(model_name)` — routes model name prefix to the correct provider instance |
| `pim_core/llm/registry.py` | `agent_model_registry` — runtime map of which LLM each agent is currently using |
| `pim_core/llm/providers/base.py` | `BaseLLMProvider` ABC — the interface every provider must implement |
| `pim_core/llm/providers/anthropic_provider.py` | Anthropic Claude provider (`claude-*` models) |
| `pim_core/llm/providers/openai_provider.py` | OpenAI provider (`gpt-*`, `o1-*`, `o3-*`, `o4-*` models) |
| `pim_core/llm/providers/google_provider.py` | Google Gemini provider (`gemini-*` models) |

---

### Product Description Generator only (`agents/product_description_generator/`)

Everything inside `agents/product_description_generator/` is exclusively owned by the Content Agent. No other agent should import from here.

| File | Why it is specific to this agent |
|---|---|
| `agents/product_description_generator/main.py` | This agent's own FastAPI application and HTTP server |
| `agents/product_description_generator/routes/product_description_generator_api_route.py` | `POST /agents/generate-description` — accepts a raw PIM record, runs the shared adapter, then calls the same generation pipeline |
| `agents/product_description_generator/routes/agent_registry.py` | `GET /models/available` · `POST/GET/DELETE /agents-settings/*` — global model assignment and registry view |
| `agents/product_description_generator/tools/generate_description.py` | The `generate_description` FastMCP tool — content-specific logic |
| `agents/product_description_generator/workflows/description_workflow.py` | LangGraph `StateGraph` wired for product description generation |
| `agents/product_description_generator/prompts/brand_voice.py` | Prompt builders using `BrandVoice` — specific to product copywriting |

---

### Visual map

```
pim_core/                          ← SHARED — used by ALL agents
├── config.py                          Settings singleton
├── schemas/
│   ├── product.py                     Product, BrandVoice, DescriptionResult
│   └── pim_product.py                 PIMProductRecord (raw PIM export schema)
├── adapters/
│   └── pim_adapter.py                 pim_record_to_product() adapter
├── utils/
│   ├── all_available_models.py        AllAvailableModelsAnthropic/OpenAI/Google enums
│   └── all_agents.py                  AllAgents enum — register agents here first
├── db/
│   └── agent_model_db.py              SQLite persistence for agent→model assignments
└── llm/
    ├── client.py                      LLMClient (provider-agnostic)
    ├── factory.py                     get_provider() factory
    ├── registry.py                    AgentModelRegistry
    └── providers/
        ├── base.py                    BaseLLMProvider ABC
        ├── anthropic_provider.py      Claude
        ├── openai_provider.py         GPT
        └── google_provider.py         Gemini

agents/
├── product_description_generator/ ← PRODUCT DESCRIPTION GENERATOR only
│   ├── main.py
│   ├── routes/
│   │   ├── product_description_generator_api_route.py  POST /agents/generate-description
│   │   └── agent_registry.py          GET /models/available · POST|GET|DELETE /agents-settings/*
│   ├── tools/generate_description.py
│   ├── workflows/description_workflow.py
│   └── prompts/brand_voice.py
│
├── catalog/                       ← PLANNED — will import from pim_core/ only
└── procurement/                   ← PLANNED — will import from pim_core/ only
```

---

### Rule for adding a new agent

When building `agents/catalog/` or `agents/procurement/`:

1. Add the agent to `pim_core/utils/all_agents.py` — add a new entry to `AllAgents` enum first
2. Create `agents/<name>/main.py` — its own FastAPI app, mount the PIM route router and `agent_registry_router`
3. Create `agents/<name>/workflows/`, `tools/`, `prompts/` — agent-specific logic only
4. Use `AllAgents.<NAME>.value` everywhere as the registry key — never a bare string
5. Import `llm_client`, `agent_model_registry`, `get_provider`, and all schemas from `pim_core/` — never from `agents/product_description_generator/`
6. Assign a model via `POST /agents-settings/<name>/model` — no per-agent config route needed
7. Add new shared schemas to `pim_core/schemas/` if multiple agents will need them
8. Update this section of the README

---

## 14. Deep Dive — LangGraph, FastMCP, and How Everything Works Together

> This section is for developers who are new to agent frameworks. It explains every layer of the system from scratch, using analogies from data engineering where helpful.

---

### The big picture — what problem are we solving?

A product description generator sounds simple: take product data, send it to an LLM, get text back. You could do that in 10 lines of Python. So why does this project have workflows, tools, graphs, state, providers, and registries?

**Because the naive 10-line version breaks down fast:**

| Problem | What breaks in the naive version |
|---|---|
| You want to switch from Claude to GPT | Hard-coded `anthropic.Anthropic()` everywhere |
| You want to run 100 requests at once | Blocking `requests.post()` blocks the whole process |
| The LLM returns malformed JSON | Unhandled exception crashes the request |
| You want to add a "retry with better prompt" step | No structure to add steps to |
| You want to know which model generated each result | No tracking |
| A second agent needs to call the same LLM | Copy-paste the LLM code everywhere |

Each layer in this project solves one of these problems. Understanding why each layer exists makes the architecture obvious.

---

### Layer 1 — FastAPI: receiving the HTTP request

FastAPI is a Python web framework for building REST APIs. If you have used Flask or Django, FastAPI is similar but with two key additions:
- **Automatic data validation** via Pydantic — if the request body is malformed, FastAPI rejects it before your code even runs
- **Async support** — requests don't block each other (explained below)

When you hit `POST /agents/generate-description`, FastAPI:
1. Reads the raw JSON body
2. Validates it against `PIMIngestRequest` (a Pydantic model)
3. If valid, calls the route handler function
4. If invalid, returns a 422 error automatically — no code needed

```python
# routes/product_description_generator_api_route.py
@router.post("/generate-description", response_model=DescriptionResult)
async def generate_description_from_pim(request: PIMIngestRequest):
    product = pim_record_to_product(request.pim_record)  # step 1: adapt
    return await generate_description(                    # step 2: generate
        product=product,
        channel=request.channel,
        brand_voice=request.brand_voice,
    )
```

There is no business logic here. The route handler does two things: adapt the raw input into a clean `Product`, and call the FastMCP tool.

---

### Layer 2 — Pydantic: data contracts

Pydantic is a Python library for defining and validating data structures using type hints.

Think of a Pydantic model like a database schema — it defines exactly what shape the data must have:

```python
class PIMProductRecord(BaseModel):
    productID: int = 0          # must be an integer, defaults to 0
    productName: str = ""       # must be a string, defaults to empty
    categorySpecificAttributes: list[Any] = []  # must be a list

    model_config = {"extra": "ignore"}  # unknown fields are silently dropped
```

When FastAPI receives a request, it passes the raw JSON to Pydantic. Pydantic:
- Coerces types where safe (`"705517"` → `705517` if the field is `int`)
- Rejects the request with a clear error if a required field is the wrong type
- Drops fields not in the model (because `extra = "ignore"`)

This means **your actual business logic never sees invalid data**. The validation happens at the boundary.

> **Data engineering analogy:** Pydantic is like a schema-enforced Kafka topic or a Delta table with enforced schema. Data that doesn't match the schema is rejected at the door.

---

### Layer 3 — The Adapter: translating raw PIM data into a clean Product

The PIM system exports data in its own format — field names like `coordGroupDescription`, `ipManufacturer`, `copy1`. The LLM pipeline uses a clean, normalised `Product` schema.

`pim_adapter.py` is the translation layer between them:

```python
def pim_record_to_product(record: PIMProductRecord) -> Product:
    return Product(
        id=str(record.productID),
        name=record.productName.strip(),
        category=record.coordGroupDescription.strip(),  # strip trailing spaces
        attributes=ProductAttributes(
            brand=record.ipManufacturer.strip() or None,
            additional={...}
        ),
        existing_description=_pick_best_description(record),
    )
```

This pattern is called the **Adapter Pattern**. The adapter converts one interface into another without changing either side. The PIM system doesn't know about `Product`. The LLM pipeline doesn't know about `coordGroupDescription`. The adapter is the only place that knows both.

> **Data engineering analogy:** This is exactly what a staging layer does in a data warehouse — raw source data → normalised model. The adapter is the transformation step.

---

### Layer 4 — FastMCP: what is MCP and why is it here?

**MCP (Model Context Protocol)** is an open standard created by Anthropic that defines how LLMs connect to external tools. Think of it as a USB standard — any LLM that speaks MCP can use any tool that exposes MCP, without custom integration code.

**FastMCP** is a Python library that makes it easy to build MCP servers. You decorate a function with `@mcp.tool()` and FastMCP handles the protocol details.

```python
# tools/generate_description.py
mcp = FastMCP("Content Agent")

@mcp.tool()
async def generate_description(
    product: Product,
    channel: str,
    brand_voice: BrandVoice | None = None,
) -> DescriptionResult:
    """Generate an SEO-optimised title and description for a product."""
    ...
```

**Why use FastMCP here instead of just calling a function directly?**

In this project, the route handler does call the tool as a regular Python function. But using `@mcp.tool()` gives you:

1. **Self-documentation** — the tool's docstring and type hints become the schema that any MCP client can discover automatically
2. **Future compatibility** — if you want to expose this tool to a Claude agent that can call it by name (e.g. `use_mcp_tool("generate_description", {...})`), the server is already built
3. **Separation of concerns** — the tool is the "what" (generate a description), the route is the "how the request arrived" (HTTP). They stay independent

> **Interview answer:** "FastMCP registers the `generate_description` function as an MCP-compliant tool. This means the same function can be called by a FastAPI HTTP handler today, and by a Claude agent using the Model Context Protocol in the future, without any changes to the tool itself."

---

### Layer 5 — LangGraph: what is a StateGraph and why use it?

LangGraph is a library for building agent workflows as **directed graphs**. Before explaining LangGraph, let's understand why a plain function call isn't enough.

#### The problem with plain function calls

If you were writing a simple pipeline in Python, you might write:

```python
def generate(product, channel, brand_voice):
    prompt = build_prompt(product, channel, brand_voice)
    raw = call_llm(prompt)
    result = parse_json(raw)
    return result
```

This works for a single step. But what if you want to:
- **Retry** if the LLM returns invalid JSON?
- **Add a review step** that checks the description before returning it?
- **Branch** — generate a short description for mobile and a long one for desktop?
- **Run steps in parallel** — generate title and description simultaneously?

With plain functions, adding any of these requires rewriting the control flow. LangGraph solves this by making the workflow **explicit and composable**.

#### What is a graph?

A graph is a data structure with **nodes** (things) and **edges** (connections between things). You already use graphs constantly in data engineering — a DAG (Directed Acyclic Graph) in Airflow, dbt, or Spark is a graph.

LangGraph's `StateGraph` works the same way:
- **Nodes** are functions that do work
- **Edges** are the connections that say "after this node, go to that node"
- **State** is a shared dictionary that flows through every node

#### The StateGraph in this project

```python
# workflows/description_workflow.py

class DescriptionState(TypedDict):
    product: Product
    channel: str
    brand_voice: BrandVoice
    title: str
    description: str
    seo_keywords: list[str]
    error: str | None

graph_builder = StateGraph(DescriptionState)
graph_builder.add_node("generate", generate_node)
graph_builder.set_entry_point("generate")
graph_builder.add_edge("generate", END)
description_graph = graph_builder.compile()
```

**Breaking this down line by line:**

`StateGraph(DescriptionState)` — creates a new graph where every node shares the same `DescriptionState` TypedDict. Think of the state as a row in a table that every node can read and write.

`add_node("generate", generate_node)` — registers a node named `"generate"` that runs the `generate_node` function when reached.

`set_entry_point("generate")` — the graph starts at this node.

`add_edge("generate", END)` — after `"generate"` finishes, the graph ends. `END` is a LangGraph constant.

`compile()` — converts the builder into a runnable graph object. This validates that all edges connect to real nodes, the entry point exists, etc.

#### The node function

```python
async def generate_node(state: DescriptionState) -> dict:
    model = agent_model_registry.get(AllAgents.PRODUCT_DESCRIPTION_GENERATOR.value)
    system = get_system_prompt(state["brand_voice"])
    user_msg = get_user_message(state["product"], state["channel"])

    raw_text = await llm_client.complete(
        model=model,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=1200,
    )

    try:
        parsed = json.loads(_extract_json(raw_text))
        return {
            "title": parsed["title"],
            "description": parsed["description"],
            "seo_keywords": parsed.get("seo_keywords", []),
            "error": None,
        }
    except (json.JSONDecodeError, KeyError) as e:
        return {"error": f"Failed to parse LLM response: {e}"}
```

**Key things to notice:**

1. The node receives the **full state** and returns only the **fields it changes**. LangGraph merges the returned dict back into the state automatically.

2. **Errors go into state, not exceptions.** If parsing fails, the node returns `{"error": "..."}` instead of raising. This ensures the graph always reaches `END` cleanly. The caller checks `state["error"]` afterwards.

3. The node is `async` — it can be awaited and won't block other requests while waiting for the LLM.

#### How ainvoke works

```python
# In the FastMCP tool:
result_state = await description_graph.ainvoke(state)
```

`ainvoke` is the async version of `invoke`. It:
1. Creates a copy of the initial state
2. Runs the entry point node
3. Follows edges to the next node (or `END`)
4. Returns the final state

The `a` prefix (`ainvoke`, `astream`, `aget`) consistently means "async" across LangGraph and LangChain.

> **Data engineering analogy:** A LangGraph StateGraph is like an Airflow DAG. Tasks are nodes. Dependencies are edges. The state dict is like XCom — shared data passed between tasks. The difference is LangGraph is designed for LLM workflows and can branch, retry, and loop based on what the LLM returns.

---

### Layer 6 — The LLM abstraction: Client, Factory, Registry, Providers

This is the most architecturally interesting part of the codebase. Let's trace what happens when `generate_node` calls `llm_client.complete(model="gpt-4o", ...)`.

#### Step 1: LLMClient.complete()

```python
# pim_core/llm/client.py
class LLMClient:
    async def complete(self, model, system, messages, max_tokens=1024):
        provider = get_provider(model)          # ask factory for the right provider
        return await provider.complete(         # call it
            model=model,
            system=system,
            messages=messages,
            max_tokens=max_tokens,
        )
```

`LLMClient` knows nothing about Anthropic, OpenAI, or Google. It just asks the factory for a provider and calls it. This is the **Strategy Pattern** — the strategy (which LLM to use) is injected at runtime.

#### Step 2: get_provider() — the Factory

```python
# pim_core/llm/factory.py
_ANTHROPIC_MODELS = frozenset(m.value for m in AllAvailableModelsAnthropic)
_OPENAI_MODELS = frozenset(m.value for m in AllAvailableModelsOpenAI)
_GOOGLE_MODELS = frozenset(m.value for m in AllAvailableModelsGoogle)
_instances: dict[str, BaseLLMProvider] = {}

def get_provider(model_name: str) -> BaseLLMProvider:
    if model_name in _instances:
        return _instances[model_name]          # return cached instance

    if model_name in _ANTHROPIC_MODELS:
        provider = AnthropicProvider()
    elif model_name in _OPENAI_MODELS:
        provider = OpenAIProvider()
    elif model_name in _GOOGLE_MODELS:
        provider = GoogleProvider()
    else:
        raise ValueError(f"No provider found for model '{model_name}'")

    _instances[model_name] = provider          # cache it
    return provider
```

The factory:
- Decides **which class to instantiate** based on the model name
- **Caches instances** so the SDK client is created once per process (not once per request)
- Raises a clear error for unknown models

This is the **Factory Pattern** — callers never write `AnthropicProvider()` themselves.

#### Step 3: The providers — BaseLLMProvider ABC

```python
# pim_core/llm/providers/base.py
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    @abstractmethod
    async def complete(self, model, system, messages, max_tokens) -> str:
        ...
```

`ABC` (Abstract Base Class) means you cannot instantiate `BaseLLMProvider` directly — it only defines the contract. Every concrete provider must implement `complete()` with exactly this signature.

**Why this matters:** `LLMClient` is typed to accept `BaseLLMProvider`. It calls `provider.complete(...)`. It does not care which concrete class it gets. This is **polymorphism** — different classes share a common interface, and the caller doesn't need to know which one it has.

#### Step 4: AgentModelRegistry

```python
# pim_core/llm/registry.py
class AgentModelRegistry:
    def __init__(self):
        self._registry = agent_model_db.load_all()  # load from SQLite on startup

    def get(self, agent_name: str) -> str:
        if agent_name in self._registry:
            return self._registry[agent_name]        # explicit assignment
        return settings.claude_model                 # fallback to default

    def set(self, agent_name: str, model_name: str) -> None:
        self._registry[agent_name] = model_name
        agent_model_db.upsert(agent_name, model_name)  # persist to SQLite

agent_model_registry = AgentModelRegistry()  # module-level singleton
```

The registry is the bridge between the HTTP config API and the LLM call inside the workflow:

```
POST /agents-settings/product_description_generator/model {"model": "gpt-4o"}
  → agent_model_registry.set("product_description_generator", "gpt-4o")
    → SQLite write

Next LLM call in generate_node:
  → agent_model_registry.get("product_description_generator")
  → returns "gpt-4o"
  → llm_client.complete(model="gpt-4o", ...)
  → OpenAIProvider.complete(...)
  → OpenAI API
```

**SQLite persistence** means the assignment survives server restarts. Without it, every restart would reset all agents to the default Claude model.

---

### The complete data flow — step by step

Here is every step from HTTP request to HTTP response, with the file responsible for each:

```
1.  HTTP POST /agents/generate-description
    │   Raw JSON body arrives
    │
2.  routes/product_description_generator_api_route.py
    │   FastAPI validates body against PIMIngestRequest (Pydantic)
    │   Invalid? → 422 error returned immediately
    │
3.  pim_core/adapters/pim_adapter.py
    │   pim_record_to_product(record)
    │   Translates 13 PIM fields → clean Product schema
    │   Strips whitespace, picks best existing_description
    │
4.  tools/generate_description.py  (FastMCP tool)
    │   Initialises DescriptionState TypedDict with product, channel, brand_voice
    │
5.  workflows/description_workflow.py  (LangGraph)
    │   description_graph.ainvoke(state)
    │   Enters "generate" node
    │
6.  generate_node — step A: resolve model
    │   agent_model_registry.get("product_description_generator")
    │   → returns "gpt-4o" (or default "claude-sonnet-4-6")
    │
7.  generate_node — step B: build prompts
    │   prompts/brand_voice.py
    │   get_system_prompt(brand_voice) → system instruction string
    │   get_user_message(product, channel) → user turn string
    │
8.  generate_node — step C: call the LLM
    │   pim_core/llm/client.py
    │   llm_client.complete(model="gpt-4o", system=..., messages=[...])
    │
9.  pim_core/llm/factory.py
    │   get_provider("gpt-4o") → OpenAIProvider (cached)
    │
10. pim_core/llm/providers/openai_provider.py
    │   openai.AsyncOpenAI.chat.completions.create(...)
    │   Async HTTP call to OpenAI API
    │   Awaits response (event loop handles other requests meanwhile)
    │
11. Raw text response returns up the call stack to generate_node
    │
12. generate_node — step D: parse response
    │   _extract_json(raw_text) strips markdown code fences if present
    │   json.loads(cleaned) → {"title": ..., "description": ..., "seo_keywords": [...]}
    │   Returns updated state fields
    │   If parsing fails → returns {"error": "Failed to parse LLM response: ..."}
    │
13. LangGraph follows edge "generate" → END
    │   ainvoke() returns final state dict
    │
14. tools/generate_description.py
    │   Checks state["error"] — if set, raises ValueError
    │   Assembles DescriptionResult from state fields
    │   Reads model_used from registry (what model was actually used)
    │
15. routes/product_description_generator_api_route.py
    │   Returns DescriptionResult
    │   FastAPI serialises to JSON
    │
16. HTTP 200 response
    {
      "product_id": "705517",
      "channel": "ecommerce",
      "title": "Apple Mac Studio M4 Max — 64GB RAM, 1TB SSD",
      "description": "Experience unparalleled desktop performance...",
      "seo_keywords": ["mac studio", "m4 max", "desktop workstation"],
      "word_count": 38,
      "model_used": "gpt-4o"
    }
```

---

### Why async/await? (for data engineers)

If you have written data pipelines, you are familiar with waiting — waiting for a database query, waiting for an API call, waiting for a file to upload. In traditional code, while you wait, the CPU sits idle.

`async/await` in Python solves this by using a **single-threaded event loop**. Instead of blocking the entire program while waiting for the OpenAI API to respond, the event loop pauses that coroutine and runs something else — like handling the next incoming HTTP request.

```python
# This does NOT block — while OpenAI responds, FastAPI handles other requests
raw_text = await llm_client.complete(...)
```

For an LLM service that makes network calls for every request, this is critical. Without async, a server with one worker could only handle one request at a time. With async, it can handle hundreds simultaneously because most of the time is spent waiting for network I/O, not doing CPU work.

> **Real-world impact:** A single uvicorn worker with async handlers can typically serve 50–200 concurrent LLM requests before bottlenecking on CPU, versus 1 request at a time with blocking (synchronous) code.

---

### Why separate prompts, tools, and workflows?

This is a design choice that pays off in maintenance:

| Layer | Changes when... | Who changes it |
|---|---|---|
| `prompts/brand_voice.py` | You want different copy style, add constraints, change output format | Copywriter / prompt engineer |
| `tools/generate_description.py` | You add a new parameter or change the return schema | Backend developer |
| `workflows/description_workflow.py` | You add a retry step, a review node, parallel steps | Agent developer |
| `pim_core/llm/` | You add a new provider (Mistral, Cohere) | Infrastructure |

Each layer can change independently without touching the others. A prompt engineer can iterate on the system prompt without touching the LangGraph code. A developer can add a new LLM provider without touching the workflow.

> **Interview answer:** "We applied separation of concerns — each file has one reason to change. The prompt builders are pure functions that can be tested in isolation. The workflow is where orchestration logic lives. The tools are the public interface. The LLM layer is the infrastructure. Changing one doesn't require changing the others."

---

### Key terms for interviews

| Term | What it means in this project |
|---|---|
| **Agent** | A software system that perceives input, reasons about it (via LLM), and produces structured output |
| **MCP (Model Context Protocol)** | Open standard for connecting LLMs to external tools and data sources |
| **FastMCP** | Python library for building MCP-compliant tool servers |
| **LangGraph StateGraph** | A workflow defined as a directed graph where shared state flows through nodes |
| **Node** | A function in a LangGraph graph — receives state, does work, returns updated state |
| **Edge** | A connection between nodes — defines which node runs next |
| **State (TypedDict)** | The shared data dictionary that every node reads from and writes to |
| **ainvoke** | Async invocation of a LangGraph graph — returns the final state |
| **Strategy Pattern** | `LLMClient` calls whatever provider the factory gives it — doesn't know which one |
| **Factory Pattern** | `get_provider()` decides which class to instantiate based on the model name |
| **Singleton** | Module-level variables (`settings`, `llm_client`, `agent_model_registry`) — one per process |
| **Adapter Pattern** | `pim_record_to_product()` translates one data format into another |
| **Lazy import** | OpenAI and Google SDKs are only imported when first needed, not at startup |
| **Registry** | `AgentModelRegistry` — the runtime map of which LLM each agent uses, backed by SQLite |

---

## 16. Deep Dive — Prompts, Routes, Tools, and Workflows

> This section covers the five files that make up the Product Description Generator agent: `brand_voice.py`, `agent_registry.py`, `product_description_generator_api_route.py`, `generate_description.py`, and `description_workflow.py`.

---

### Q1 — `prompts/brand_voice.py`

**File:** [agents/product_description_generator/prompts/brand_voice.py](agents/product_description_generator/prompts/brand_voice.py)

There are two pure functions here. Neither calls the LLM. Neither has side effects. They take data in and return strings out — the strings sent to the LLM as the system prompt and user message.

---

#### `get_system_prompt(brand_voice: BrandVoice) -> str`

**Purpose:** Build the LLM *system prompt* — the invisible instruction layer that sets the model's role, rules, and output format before any conversation begins.

Think of the system prompt like a job briefing given to an employee before they start work. It tells them who they are, what they must produce, the rules they must follow, and the exact format expected.

**How it builds the string:**

```python
def get_system_prompt(brand_voice: BrandVoice) -> str:
    # Step 1: optional keyword instruction — only added if list is non-empty
    keyword_line = ""
    if brand_voice.keywords:
        keyword_line = (
            f"\n- Include these SEO keywords naturally: {', '.join(brand_voice.keywords)}"
        )
    # e.g. "\n- Include these SEO keywords naturally: M4 Max, workstation"

    # Step 2: optional word-avoidance — only added if list is non-empty
    avoid_line = ""
    if brand_voice.avoid_words:
        avoid_line = f"\n- Avoid these words: {', '.join(brand_voice.avoid_words)}"
    # e.g. "\n- Avoid these words: cheap, budget"

    # Step 3: f-string assembles everything
    return f"""You are a professional product copywriter specialising in e-commerce content.
...
Rules:
- Tone: {brand_voice.tone}
- Title: maximum {brand_voice.max_title_length} characters
- Description: maximum {brand_voice.max_description_length} characters
- Locale: {brand_voice.locale}{keyword_line}{avoid_line}

Respond ONLY with valid JSON in this exact format.
Do not wrap it in code fences. Do not add any text before or after the JSON.
{{
  "title": "<product title>",
  "description": "<product description>",
  "seo_keywords": ["keyword1", "keyword2", "keyword3"]
}}"""
```

**Why are `keyword_line` and `avoid_line` conditional?**

If `brand_voice.keywords` is `[]` and you formatted the line unconditionally, you would send:
```
- Include these SEO keywords naturally: 
```
An empty instruction. The LLM would either ignore it or produce unpredictable output. Conditional assembly means the line only appears when it has content.

**What a real rendered system prompt looks like:**

```
You are a professional product copywriter specialising in e-commerce content.

Your task is to generate an SEO-optimised product title and description.

Rules:
- Tone: professional
- Title: maximum 80 characters
- Description: maximum 500 characters
- Locale: en-GB
- Include these SEO keywords naturally: Mac Studio, M4 Max, workstation
- Avoid these words: cheap

Respond ONLY with valid JSON in this exact format.
Do not wrap it in code fences. Do not add any text before or after the JSON.
{
  "title": "<product title>",
  "description": "<product description>",
  "seo_keywords": ["keyword1", "keyword2", "keyword3"]
}
```

**Why instruct the LLM to return only JSON?**

Because `generate_node` parses the response with `json.loads()`. Any conversational text before or after the JSON — "Sure! Here is the description:" — breaks parsing. The `_FENCE_RE` regex in `description_workflow.py` handles the remaining cases where the LLM wraps the JSON in code fences despite this instruction.

---

#### `get_user_message(product: Product, channel: str) -> str`

**Purpose:** Build the *user turn* message — the actual product data the LLM reads and writes copy for. If the system prompt is the job briefing, the user message is the specific task: "write copy for *this* product".

**How it builds the string:**

```python
def get_user_message(product: Product, channel: str) -> str:
    attr_lines: list[str] = []

    # Step 1: add known structured attributes, only if non-empty
    if product.attributes.brand:
        attr_lines.append(f"Brand: {product.attributes.brand}")
    if product.attributes.color:
        attr_lines.append(f"Colour: {product.attributes.color}")
    # ... size, material, weight, dimensions ...

    # Step 2: add everything from the 'additional' dict
    # warranty, vendor_part_number, web_category, product_type etc. all land here
    for key, value in product.attributes.additional.items():
        attr_lines.append(f"{key}: {value}")

    # Step 3: join into a block or use fallback
    attr_block = "\n".join(attr_lines) if attr_lines else "No additional attributes"

    # Step 4: assemble into the final message
    return f"""Product to describe:
Name: {product.name}
Category: {product.category}
Channel: {channel}

Attributes:
{attr_block}

Existing description (for context, do not copy verbatim):
{product.existing_description or 'None'}"""
```

**What a real rendered user message looks like:**

```
Product to describe:
Name: MACSTUDIO E25 M4M/64/1TB
Category: APPLE DESKTOP SYSTEMS
Channel: ecommerce

Attributes:
Brand: APPLE
warranty: 1 year
vendor_part_number: 15098309
web_manufacturer: Apple Inc
web_category: Computers<br />Desktop Computers
product_type: Hardware

Existing description (for context, do not copy verbatim):
Apple Mac Studio with M4 Max chip, 64GB RAM, 1TB SSD.
```

**Why iterate `product.attributes.additional`?**

The `additional` dict holds all extra PIM fields that don't have a dedicated attribute on `ProductAttributes` — `warranty`, `vendor_part_number`, `web_manufacturer`, `web_category`, `product_type`, `category_attributes`. All of them are valuable context for generating accurate copy.

**Why "for context, do not copy verbatim"?**

The existing description from the PIM system seeds the LLM with context about the product without forcing it to plagiarise a potentially poor or truncated description. "Do not copy verbatim" prevents the LLM from lazily returning the same text.

---

### Q2 — `routes/agent_registry.py` — How do `get_all_agent_models` and `reset_agent_model` work with the registry?

**File:** [agents/product_description_generator/routes/agent_registry.py](agents/product_description_generator/routes/agent_registry.py)

---

#### `GET /agents-settings/models` — `get_all_agent_models`

```python
@router.get("/agents-settings/models", response_model=AllAgentModelsResponse)
async def get_all_agent_models() -> AllAgentModelsResponse:
    return AllAgentModelsResponse(
        registry=agent_model_registry.all(),
        default_model=settings.claude_model,
    )
```

This looks like just two lines — no database query, no external call. That is because the data was already loaded into RAM at server startup. Here is the full lifecycle:

```
Server process starts
       │
       │  Python imports registry.py for the first time
       │
       ▼
AgentModelRegistry.__init__() runs  (once per process lifetime)
       │
       ├── agent_model_db.load_all()
       │        │
       │        │  SQLite: SELECT agent_name, model_name FROM agent_models
       │        │
       │        ▼
       │   {"product_description_generator": "gpt-4o",
       │    "catalog": "gemini-2.0-flash"}
       │
       └── self._registry = {"product_description_generator": "gpt-4o",
                              "catalog": "gemini-2.0-flash"}
                              ← lives in RAM for the entire process lifetime
                              ← no further SQLite reads on the hot path


GET /agents-settings/models arrives
       │
       ▼
get_all_agent_models()
       │
       ├── agent_model_registry.all()
       │        │
       │        └── return dict(self._registry)   ← snapshot copy, not a reference
       │             {"product_description_generator": "gpt-4o",
       │              "catalog": "gemini-2.0-flash"}
       │
       ├── settings.claude_model  →  "claude-sonnet-4-6"  (from .env)
       │
       └── AllAgentModelsResponse(
               registry={"product_description_generator": "gpt-4o",
                         "catalog": "gemini-2.0-flash"},
               default_model="claude-sonnet-4-6"
           )
       │
       ▼
HTTP 200:
{
  "registry": {
    "product_description_generator": "gpt-4o",
    "catalog": "gemini-2.0-flash"
  },
  "default_model": "claude-sonnet-4-6"
}
```

**Why is `procurement` not in the registry?**

Because no one called `POST /agents-settings/procurement/model`. The registry only holds agents that were explicitly assigned a model. Every other agent falls back to `default_model` when `registry.get()` is called.

**Why does `all()` return `dict(self._registry)` instead of `self._registry` directly?**

Returning `self._registry` would give the caller a reference to the live internal dict. The caller could accidentally mutate it. Returning `dict(...)` gives a shallow copy — a snapshot of the current state that the caller cannot accidentally corrupt.

---

#### `DELETE /agents-settings/{agent_name}/model` — `reset_agent_model`

```python
@router.delete("/agents-settings/{agent_name}/model", response_model=AgentModelResponse)
async def reset_agent_model(agent_name: str) -> AgentModelResponse:
    agent_model_registry.remove(agent_name)
    return AgentModelResponse(agent=agent_name, model=settings.claude_model)
```

`agent_model_registry.remove(agent_name)` does two things:

```python
def remove(self, agent_name: str) -> None:
    self._registry.pop(agent_name, None)    # 1. remove from in-memory dict
    agent_model_db.delete(agent_name)       # 2. remove from SQLite
```

```
State BEFORE reset:
  self._registry = {"product_description_generator": "gpt-4o"}
  SQLite:
    ┌──────────────────────────────────┬───────────┐
    │ agent_name                       │ model_name│
    ├──────────────────────────────────┼───────────┤
    │ product_description_generator    │ gpt-4o    │
    └──────────────────────────────────┴───────────┘


DELETE /agents-settings/product_description_generator/model
       │
       ▼
agent_model_registry.remove("product_description_generator")
       │
       ├── self._registry.pop("product_description_generator", None)
       │   Before: {"product_description_generator": "gpt-4o"}
       │   After:  {}
       │   (second argument None = silently do nothing if key not found)
       │
       └── agent_model_db.delete("product_description_generator")
               │
               ▼
           DELETE FROM agent_models
           WHERE agent_name = 'product_description_generator'
               │
               ▼
           SQLite table now empty for that agent


State AFTER reset:
  self._registry = {}
  SQLite: row deleted — survives server restart


HTTP 200:
{ "agent": "product_description_generator", "model": "claude-sonnet-4-6" }
                                                       ↑ settings.claude_model


Next LLM call after reset:
       │
       ▼
agent_model_registry.get("product_description_generator")
       │
       ├── "product_description_generator" in self._registry?   NO
       │
       └── return settings.claude_model  →  "claude-sonnet-4-6"
```

**What happens if you reset an agent that was never assigned?**

`self._registry.pop(agent_name, None)` — the `, None` default silently does nothing if the key is absent. `agent_model_db.delete(agent_name)` runs a `DELETE WHERE` that matches zero rows — also harmless. The response still returns 200.

---

### Q3 — `tools/generate_description.py`

**File:** [agents/product_description_generator/tools/generate_description.py](agents/product_description_generator/tools/generate_description.py)

---

#### What is `FastMCP("Content Agent")`?

**MCP (Model Context Protocol)** is an open standard created by Anthropic. It defines a universal protocol for connecting LLMs to external tools — similar to how USB is a standard for connecting devices to computers. Any LLM that speaks MCP can use any tool that exposes MCP, without custom integration code for each pair.

**FastMCP** is a Python library that makes building MCP servers easy. Instead of writing protocol boilerplate, you decorate your function.

```python
mcp = FastMCP("Content Agent")
```

This creates a named MCP server. `"Content Agent"` is the server's identity — how an MCP client (such as a Claude agent or an MCP inspector) will refer to this server and the tools it provides.

The `mcp` object does not affect how the FastAPI route calls `generate_description`. The route calls it as a plain Python function. The decorator's value is forward-looking: if you later want a Claude agent to discover and call this tool via the MCP protocol directly (without HTTP), the server is already built — you just expose the transport.

---

#### What is `@mcp.tool()` and why is it here?

```python
@mcp.tool()
async def generate_description(
    product: Product,
    channel: str,
    brand_voice: BrandVoice | None = None,
) -> DescriptionResult:
    ...
```

`@mcp.tool()` registers the function with the MCP server. FastMCP reads:

| What FastMCP reads | What it becomes |
|---|---|
| Function name `generate_description` | Tool name — used by a Claude agent to call it |
| Docstring | Tool description — what an agent reads to decide when to use this tool |
| Type hints (`product: Product`, etc.) | JSON Schema — parameter definitions |
| Return type `-> DescriptionResult` | Output schema |

**Why use `@mcp.tool()` instead of a plain function?**

1. **Future compatibility** — if you want a Claude agent to call this tool via MCP transport instead of HTTP, no code changes are needed
2. **Self-documentation** — the tool schema is machine-readable; any MCP client can call `list_tools()` and discover `generate_description` automatically
3. **Separation of concerns** — the tool is the "what" (generate a description); the HTTP route is the "how the request arrived"; they stay independent

---

#### Full walkthrough of `generate_description`

**Step 1 — Apply default brand voice**

```python
if brand_voice is None:
    brand_voice = BrandVoice()
```

`BrandVoice()` with no arguments applies all defaults: tone=`"professional"`, locale=`"en-GB"`, max lengths, empty keywords and avoid lists. Callers don't have to send `brand_voice` at all.

**Step 2 — Initialise the LangGraph state**

```python
state = {
    "product":      product,
    "channel":      channel,
    "brand_voice":  brand_voice,
    "title":        "",       # generate_node will fill this
    "description":  "",       # generate_node will fill this
    "seo_keywords": [],       # generate_node will fill this
    "error":        None,     # generate_node sets this on parse failure
}
```

All fields must exist at initialisation — including the empty output fields — because LangGraph validates the state shape when `ainvoke()` is called.

**Step 3 — Run the LangGraph**

```python
result_state = await description_graph.ainvoke(state)
```

`await` suspends this coroutine and returns control to the FastAPI event loop while the LLM call happens. The graph runs `generate_node`, which calls the LLM, parses the JSON response, fills the output fields (or sets `error`), and returns the final state dict.

**Step 4 — Check for errors**

```python
if result_state.get("error"):
    raise ValueError(result_state["error"])
```

`generate_node` never raises exceptions — it catches all errors internally and stores them in `state["error"]`. This line surfaces the error as a Python exception. The route handler catches it and returns HTTP 422.

**Step 5 — Assemble and return `DescriptionResult`**

```python
return DescriptionResult(
    product_id=product.id,
    channel=channel,
    title=result_state["title"],
    description=result_state["description"],
    seo_keywords=result_state["seo_keywords"],
    word_count=len(result_state["description"].split()),   # computed in code, not by LLM
    model_used=agent_model_registry.get(AllAgents.PRODUCT_DESCRIPTION_GENERATOR.value),
)
```

**Why compute `word_count` in Python instead of asking the LLM?**

Asking an LLM to count its own words accurately is unreliable. A simple `len(text.split())` is exact, deterministic, and free. Always compute objective metrics in code.

**Why read `model_used` from the registry at the end?**

The registry is the single source of truth. Reading it here guarantees `model_used` reflects the model that was actually called during this invocation, even if the model was changed by another concurrent request.

---

### Q4 — `workflows/description_workflow.py`

**File:** [agents/product_description_generator/workflows/description_workflow.py](agents/product_description_generator/workflows/description_workflow.py)

---

#### `_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)`

This is a precompiled **regular expression** that detects and extracts JSON wrapped in markdown code fences.

**Why it exists:**

The system prompt instructs the LLM: *"Respond ONLY with valid JSON. Do not wrap it in code fences."* LLMs are probabilistic — they don't always follow instructions. Claude sometimes returns:

````
```json
{
  "title": "Apple Mac Studio M4 Max",
  "description": "Experience unparalleled performance...",
  "seo_keywords": ["mac studio", "m4 max"]
}
```
````

Calling `json.loads()` on that string fails because of the backtick wrapper. `_FENCE_RE` strips them as a safety net.

**Anatomy of the pattern:**

```
r"```(?:json)?\s*(\{.*?\})\s*```"
    ^^^                      ^^^
     │   ^^^^^^^^ ^^^^^^^^    │
     │       │        │       └── closing triple backtick
     │       │        └── capture group: the JSON object {…}
     │       └── optional "json" language tag + whitespace
     └── opening triple backtick
```

| Part | What it matches |
|---|---|
| ` ``` ` | Opening code fence |
| `(?:json)?` | Optional `json` language tag — `(?:...)` is non-capturing so it is not included in `.group(1)` |
| `\s*` | Zero or more whitespace characters including newlines |
| `(\{.*?\})` | Capture group — a JSON object from `{` to `}`. `.*?` is *non-greedy*: stops at the first `}` rather than the last |
| `\s*` | Trailing whitespace |
| ` ``` ` | Closing code fence |
| `re.DOTALL` | Makes `.` match newlines — required because JSON spans multiple lines |

**How `_extract_json` uses it:**

```python
def _extract_json(raw: str) -> str:
    stripped = raw.strip()
    match = _FENCE_RE.search(stripped)
    if match:
        return match.group(1).strip()   # JSON from inside the fences
    return stripped                     # no fences — plain JSON, return as-is
```

Two cases handled cleanly:
1. LLM returns plain JSON → no match → return as-is
2. LLM returns fenced JSON → match → return just the object inside

**Why precompile with `re.compile()`?**

`re.compile()` parses the regex pattern once at module import time. If you used `re.search(pattern, text)` inside the function, Python would re-parse the pattern on every call. Since `_extract_json` runs on every LLM response, precompiling avoids this repeated work.

---

#### `generate_node(state: DescriptionState) -> dict`

This is the single node in the LangGraph. It receives the full current state, does the LLM call, and returns a dict of only the fields it changes.

```python
async def generate_node(state: DescriptionState) -> dict:
    # Step 1: which model is this agent currently using?
    model = agent_model_registry.get(AllAgents.PRODUCT_DESCRIPTION_GENERATOR.value)

    # Step 2: build prompts from state
    system_prompt = get_system_prompt(state["brand_voice"])
    user_message  = get_user_message(state["product"], state["channel"])

    # Step 3: log what we are about to do
    logger.info("Calling LLM model '%s' for product %s on channel %s",
                model, state["product"].id, state["channel"])

    try:
        # Step 4: call the LLM (async — non-blocking)
        raw_text = await llm_client.complete(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            model=model,
            max_tokens=1200,
        )

        # Step 5: strip code fences if present, then parse JSON
        parsed = json.loads(_extract_json(raw_text))

        # Step 6: return only the fields that changed
        return {
            "title":        parsed["title"],
            "description":  parsed["description"],
            "seo_keywords": parsed.get("seo_keywords", []),
            "error":        None,
        }

    except (json.JSONDecodeError, KeyError) as exc:
        # Step 7: store error in state — do NOT raise
        logger.error("LLM parse failed for product %s: %s", state["product"].id, exc)
        return {"error": f"Failed to parse LLM response: {exc}"}
```

**Why return only changed fields?**

LangGraph merges the returned dict into the existing state. Returning `{"title": "...", "description": "..."}` updates only those two fields; `product`, `channel`, `brand_voice` remain unchanged without you having to explicitly pass them through. You never need to copy unchanged state fields.

**Why catch `KeyError`?**

If the LLM returns valid JSON but without the expected keys:
```json
{"heading": "Apple Mac Studio", "body": "..."}
```
`parsed["title"]` raises `KeyError`. Catching it alongside `JSONDecodeError` means the caller gets a clean error message rather than an unhandled exception.

**Why never raise inside a node?**

Raising an exception inside a LangGraph node causes `ainvoke()` to propagate it all the way to the caller as an unhandled exception, which FastAPI turns into an HTTP 500. By catching all expected errors and storing them in `state["error"]`, the graph always reaches `END` cleanly. The caller (the tool) checks `state["error"]` and decides how to surface the error as an HTTP response.

---

#### `build_description_graph()` — Why wrap construction in a function?

```python
def build_description_graph():
    graph: StateGraph = StateGraph(DescriptionState)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("generate")
    graph.add_edge("generate", END)
    return graph.compile()
```

The graph construction is a function — not bare module-level statements — for **testability**. Any test can call `build_description_graph()` to get a fresh, independent graph instance. If the graph were built directly at module level as bare statements, there would be no way to get a clean graph in tests.

**What `graph.compile()` does:**

Compilation converts the mutable `StateGraph` builder into a locked, runnable `CompiledGraph`. During compilation LangGraph:
- Validates every node referenced in edges exists
- Validates the entry point is a registered node
- Builds internal routing tables
- Returns an object with `invoke()`, `ainvoke()`, `astream()` etc.

After `compile()` the graph structure is frozen. Only the data (the state dict) changes at runtime.

---

#### `description_graph = build_description_graph()`

```python
description_graph = build_description_graph()
```

This line runs **once** when Python first imports `description_workflow`. The compiled graph is stored as a module-level singleton.

**Where is `description_graph` used?**

Imported and used in exactly one place:

```python
# tools/generate_description.py — line 5
from agents.product_description_generator.workflows.description_workflow import description_graph

# ...line 45:
result_state = await description_graph.ainvoke(state)
```

The compiled graph is safe to call concurrently — each `ainvoke()` call operates on its own copy of the state, so multiple simultaneous HTTP requests do not interfere with each other.

---

### Q5 — How all five files work together: the complete flow

```
  HTTP Client
      │
      │  POST /agents/generate-description
      │  { "pim_record": { "productID": 705517, ... },
      │    "channel": "ecommerce",
      │    "brand_voice": { "tone": "professional", "keywords": ["M4 Max"] } }
      │
      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  product_description_generator_api_route.py                              │
│                                                                          │
│  FastAPI validates body against GenerateFromPIMRequest (Pydantic)        │
│  Invalid → 422 automatically                                             │
│                                                                          │
│  pim_record_to_product(request.pim_record)   ← pim_adapter.py           │
│  → Product(id="705517", name="MACSTUDIO ...", category="APPLE DESKTOP    │
│            SYSTEMS", attributes=ProductAttributes(brand="APPLE", ...))   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ generate_description(product, channel, brand_voice)
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  tools/generate_description.py   (@mcp.tool)                             │
│                                                                          │
│  brand_voice = brand_voice or BrandVoice()   ← apply defaults           │
│                                                                          │
│  state = { "product": Product(...), "channel": "ecommerce",              │
│            "brand_voice": BrandVoice(...),                               │
│            "title": "", "description": "", "seo_keywords": [],           │
│            "error": None }                                               │
│                                                                          │
│  await description_graph.ainvoke(state)   ───────────────────────────►  │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  description_workflow.py   (LangGraph StateGraph)                        │
│                                                                          │
│  ┌─────────┐                                                             │
│  │  START  │                                                             │
│  └────┬────┘                                                             │
│       │ entry point                                                      │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  generate_node(state)                                             │   │
│  │                                                                   │   │
│  │  A. registry.get("product_description_generator") → "gpt-4o"     │   │
│  │        └── pim_core/llm/registry.py                               │   │
│  │                                                                   │   │
│  │  B. get_system_prompt(brand_voice) ← prompts/brand_voice.py      │   │
│  │     → "You are a professional product copywriter..."              │   │
│  │                                                                   │   │
│  │  C. get_user_message(product, "ecommerce") ← brand_voice.py      │   │
│  │     → "Product to describe:\nName: MACSTUDIO..."                  │   │
│  │                                                                   │   │
│  │  D. llm_client.complete(model="gpt-4o", system=..., messages=[..]│   │
│  │        └── pim_core/llm/client.py                                 │   │
│  │              └── factory.get_provider("gpt-4o")                   │   │
│  │                    └── OpenAIProvider.complete(...)                │   │
│  │                          └── OpenAI API HTTP call (awaited)        │   │
│  │                                                                   │   │
│  │  E. _extract_json(raw_text) — strip code fences if present        │   │
│  │     json.loads(cleaned)                                            │   │
│  │     → {"title": "...", "description": "...", "seo_keywords": [...]}│   │
│  │                                                                   │   │
│  │  returns { "title": "Apple Mac Studio M4 Max — 64GB RAM, 1TB SSD",│   │
│  │            "description": "Experience unparalleled performance...",│   │
│  │            "seo_keywords": ["mac studio", "m4 max", "workstation"],│   │
│  │            "error": None }                                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│       │ edge: "generate" → END                                           │
│       ▼                                                                  │
│  ┌─────────┐                                                             │
│  │   END   │                                                             │
│  └─────────┘                                                             │
│                                                                          │
│  ainvoke() returns final state dict                                      │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  tools/generate_description.py  (back in generate_description)           │
│                                                                          │
│  result_state["error"] is None  → continue                              │
│                                                                          │
│  return DescriptionResult(                                               │
│    product_id  = "705517",                                               │
│    channel     = "ecommerce",                                            │
│    title       = "Apple Mac Studio M4 Max — 64GB RAM, 1TB SSD",         │
│    description = "Experience unparalleled desktop performance...",       │
│    seo_keywords= ["mac studio", "m4 max", "workstation"],                │
│    word_count  = 6,                  ← computed by Python, not LLM      │
│    model_used  = "gpt-4o"            ← read from registry               │
│  )                                                                       │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  product_description_generator_api_route.py                              │
│  FastAPI serialises DescriptionResult to JSON                            │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
HTTP 200:
{
  "product_id":    "705517",
  "channel":       "ecommerce",
  "title":         "Apple Mac Studio M4 Max — 64GB RAM, 1TB SSD",
  "description":   "Experience unparalleled desktop performance...",
  "seo_keywords":  ["mac studio", "m4 max", "workstation"],
  "word_count":    6,
  "model_used":    "gpt-4o"
}
```

---

### Responsibility map — which file owns what

```
What needs doing               Who does it
─────────────────────────────────────────────────────────────────────────
Receive HTTP request           product_description_generator_api_route.py
Validate request body          FastAPI + Pydantic (automatic)
Convert PIM fields → Product   pim_core/adapters/pim_adapter.py
Build system prompt            prompts/brand_voice.py
Build user message             prompts/brand_voice.py
Orchestrate the workflow       workflows/description_workflow.py
Decide which LLM to use        pim_core/llm/registry.py
Call the LLM                   pim_core/llm/client.py + factory.py
Strip code fences from LLM     _extract_json() in description_workflow.py
Parse LLM JSON response        generate_node() in description_workflow.py
Assemble final result          tools/generate_description.py
Expose as MCP tool             tools/generate_description.py (@mcp.tool)
Manage agent-to-model map      pim_core/llm/registry.py + agent_model_db
List available models          routes/agent_registry.py
Assign model to agent          routes/agent_registry.py
Reset agent to default         routes/agent_registry.py
```

---

### Error handling map — what breaks where and how it surfaces

```
Error location                  How caught                      HTTP status
─────────────────────────────────────────────────────────────────────────────
Invalid request body            FastAPI + Pydantic automatic    422
PIM record cannot be adapted    try/except in api route         400
LLM returns invalid JSON        try/except in generate_node     state["error"]
  surfaced in tool              if result_state.get("error")    ValueError raised
  caught in api route           except ValueError               422
LLM API key missing             provider __init__ raises        500 (unhandled — ops issue)
Unknown model requested         factory raises ValueError       400 (caught in set_agent_model)
```

> **Interview answer:** "Each layer catches only what it can meaningfully handle. The workflow node catches JSON parse errors because it owns the response format. The route handler catches adapter errors because it owns HTTP status codes. The factory catches unknown model names because it owns the model catalogue. No layer handles another layer's errors — that is the single-responsibility principle in practice."

---

## 15. Deep Dive — The LLM Provider Layer (`pim_core/llm/`)

> This section answers every question about how `base.py`, the three providers, `client.py`, `factory.py`, and `registry.py` work together. Read this section alongside the actual source files.

---

### Q1 — How do all these files work together?

Think of it as a chain of responsibility. Each file has one job, and they hand off to each other:

```
                         ┌──────────────────────────────────────────────────────┐
                         │  generate_node  (workflows/description_workflow.py)  │
                         │  "I need to call the LLM. Which model should I use?" │
                         └────────────────────────┬─────────────────────────────┘
                                                  │ calls
                                                  ▼
                         ┌──────────────────────────────────────────────────────┐
                         │  agent_model_registry.get("product_description_      │
                         │  generator")   →   "gpt-4o"       (registry.py)      │
                         └────────────────────────┬─────────────────────────────┘
                                                  │ model name resolved
                                                  ▼
                         ┌──────────────────────────────────────────────────────┐
                         │  llm_client.complete(model="gpt-4o", ...)  (client.py)│
                         │  "I don't know about providers. I'll ask the factory."│
                         └────────────────────────┬─────────────────────────────┘
                                                  │ calls
                                                  ▼
                         ┌──────────────────────────────────────────────────────┐
                         │  get_provider("gpt-4o")           (factory.py)       │
                         │  "gpt-4o is in _OPENAI_MODELS → return OpenAIProvider"│
                         └────────────────────────┬─────────────────────────────┘
                                                  │ returns
                                                  ▼
                         ┌──────────────────────────────────────────────────────┐
                         │  OpenAIProvider.complete(...)  (openai_provider.py)  │
                         │  Extends BaseLLMProvider  (base.py)                  │
                         │  Makes real HTTP call to OpenAI API                  │
                         └────────────────────────┬─────────────────────────────┘
                                                  │ returns
                                                  ▼
                                          raw text string
```

**File responsibilities at a glance:**

| File | Single responsibility |
|---|---|
| `base.py` | Defines the contract — what every provider MUST implement |
| `anthropic_provider.py` | Implements that contract using the Anthropic SDK |
| `openai_provider.py` | Implements that contract using the OpenAI SDK |
| `google_provider.py` | Implements that contract using the Google Gemini SDK |
| `factory.py` | Decides which provider class to use based on the model name |
| `client.py` | The only file the rest of the codebase ever talks to |
| `registry.py` | Stores which model each agent is currently assigned to |

---

### Q2 — What is `BaseLLMProvider`? What is `ABC`? What is `abstractmethod`? What does `complete()` do?

**File:** [pim_core/llm/providers/base.py](pim_core/llm/providers/base.py)

```python
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM provider implementations."""

    @abstractmethod
    async def complete(
        self,
        model: str,
        system: str,
        messages: list[dict],
        max_tokens: int = 1024,
    ) -> str:
        """Call the LLM and return the response text."""
```

**What is `ABC` (Abstract Base Class)?**

`ABC` is a Python class from the `abc` module. When you inherit from it, Python treats your class as an *abstract* class — a class that defines a blueprint but cannot be used directly.

Think of `ABC` like a job description. It says "any provider we hire must be able to do these things". But the job description itself is not a worker — you can't call it directly.

```python
# This would raise: TypeError: Can't instantiate abstract class BaseLLMProvider
# with abstract method complete
provider = BaseLLMProvider()   # NOT allowed

# This is allowed — concrete subclass with complete() implemented
provider = AnthropicProvider() # OK — it implements complete()
```

**What is `@abstractmethod`?**

`@abstractmethod` is a decorator that marks a method as "must be overridden by every subclass". If you forget to implement it, Python raises a `TypeError` at instantiation time — not at the call site. This is a compile-time safety net.

```python
class BadProvider(BaseLLMProvider):
    pass  # forgot to implement complete()

bad = BadProvider()
# TypeError: Can't instantiate abstract class BadProvider with abstract method complete
```

**What does `complete()` do?**

`complete()` is the single method that every provider must implement. It is the *contract*. The signature defines:

| Parameter | Type | What it carries |
|---|---|---|
| `model` | `str` | Which exact model to use — e.g. `"gpt-4o"`, `"claude-sonnet-4-6"` |
| `system` | `str` | The system prompt — instructions to the LLM about its role, output format, constraints |
| `messages` | `list[dict]` | The conversation turns — `[{"role": "user", "content": "..."}]` |
| `max_tokens` | `int` | Hard cap on response length (defaults to 1024) |
| **returns** | `str` | The raw text the LLM produced |

Every provider maps these four universal parameters to whatever format its own SDK expects. The callers never need to know these differences exist.

**Why does this pattern matter for interviews?**

This is the **Open/Closed Principle** from SOLID:
- *Open* for extension — you can add `MistralProvider` without touching any existing code
- *Closed* for modification — adding a new provider never breaks existing callers

---

### Q3 — `OpenAIProvider` deep dive

**File:** [pim_core/llm/providers/openai_provider.py](pim_core/llm/providers/openai_provider.py)

#### `self._client = AsyncOpenAI(api_key=settings.openai_api_key)`

```python
from openai import AsyncOpenAI
self._client = AsyncOpenAI(api_key=settings.openai_api_key)
```

`AsyncOpenAI` is the async version of the OpenAI Python SDK client. Under the hood it creates:
- An HTTP session (using `httpx` internally)
- Authentication headers with your API key
- Connection pooling (reuses TCP connections instead of creating new ones per request)

By storing it as `self._client`, the connection pool is created **once** when the provider is first initialised (which happens when the factory first creates the provider instance) and reused for every subsequent call. This is why the factory caches provider instances — so we don't create a new connection pool per request.

#### `all_messages = [{"role": "system", "content": system}] + messages`

```python
all_messages = [{"role": "system", "content": system}] + messages
```

OpenAI's Chat Completions API requires all instructions, including the system prompt, to be in a single flat `messages` list in this format:

```json
[
  {"role": "system",    "content": "You are a product copywriter..."},
  {"role": "user",      "content": "Generate a description for: MacBook Pro..."},
  {"role": "assistant", "content": "Here is the description: ..."},
  {"role": "user",      "content": "Make it shorter."}
]
```

`system` is the string returned by `get_system_prompt(brand_voice)` in [prompts/brand_voice.py](agents/product_description_generator/prompts/brand_voice.py). It is built dynamically from the `BrandVoice` configuration — tone, keywords to include, words to avoid, locale, length limits.

The `+` operator on two Python lists concatenates them:
```python
[{"role": "system", "content": system}] + messages
# result: [system_message, user_message_1, user_message_2, ...]
```

So `all_messages` is a new list with the system message prepended to whatever `messages` the caller passed in.

#### `response = await self._client.chat.completions.create(...)`

```python
response = await self._client.chat.completions.create(
    model=model,
    messages=all_messages,
    max_tokens=max_tokens,
)
```

Breaking this down:

| Part | What it is |
|---|---|
| `await` | This is an async call — the event loop is released while waiting for OpenAI's server to respond. Other requests can be handled meanwhile. |
| `self._client` | The `AsyncOpenAI` instance created in `__init__` |
| `.chat` | Accesses the "chat" section of the OpenAI API (as opposed to embeddings, images, etc.) |
| `.completions` | Accesses the "completions" endpoint within chat |
| `.create(...)` | Sends the HTTP POST request to `https://api.openai.com/v1/chat/completions` |
| `model=model` | Which exact GPT model to use — e.g. `"gpt-4o"` |
| `messages=all_messages` | The full conversation history including system message |
| `max_tokens=max_tokens` | Maximum length of the response in tokens |

The `await` is critical. Without it you'd get a coroutine object, not the actual response. With it, Python suspends this coroutine, lets the event loop work on other things, and resumes here when OpenAI replies.

#### `response.choices[0].message.content`

```python
return response.choices[0].message.content
```

OpenAI returns a response object structured like this (simplified):

```python
ChatCompletion(
    choices=[
        Choice(
            index=0,
            message=ChatCompletionMessage(
                role="assistant",
                content='{"title": "...", "description": "...", "seo_keywords": [...]}'
            ),
            finish_reason="stop"
        )
        # OpenAI can return multiple choices if n > 1 (we don't set n, so always 1)
    ],
    model="gpt-4o",
    usage=CompletionUsage(prompt_tokens=..., completion_tokens=..., total_tokens=...)
)
```

- `response.choices` — a list of completions (we always get exactly one since we don't set `n`)
- `[0]` — take the first (and only) choice
- `.message` — the assistant's message object
- `.content` — the text string the model wrote

The result is the raw text string — e.g. the JSON that the LLM produced. It goes back up to `generate_node` which then runs `json.loads()` on it.

---

### Q4 — `GoogleProvider` deep dive

**File:** [pim_core/llm/providers/google_provider.py](pim_core/llm/providers/google_provider.py)

#### Message format conversion

```python
gemini_messages = [
    {
        "role": "user" if m["role"] == "user" else "model",
        "parts": [m["content"]],
    }
    for m in messages
]
```

This is a **list comprehension** — a compact for-loop that builds a new list by transforming each element. The long-form equivalent is:

```python
gemini_messages = []
for m in messages:
    if m["role"] == "user":
        role = "user"
    else:
        role = "model"          # Gemini uses "model", not "assistant"
    gemini_messages.append({
        "role": role,
        "parts": [m["content"]] # Gemini uses "parts" (list), not "content" (string)
    })
```

**Why the conversion is necessary:**

Different LLM providers use different conventions for the same concept:

| Convention | OpenAI | Anthropic | Google Gemini |
|---|---|---|---|
| AI role name | `"assistant"` | `"assistant"` | `"model"` |
| Message body key | `"content"` (string) | `"content"` (string) | `"parts"` (list) |
| System prompt | First message with `"system"` role | Separate `system=` parameter | `system_instruction=` on the model |

Our shared format uses `{"role": "user" | "assistant", "content": "..."}`. The GoogleProvider translates this into Gemini's format before making the API call.

**Note:** The system prompt is handled separately — it is passed to `GenerativeModel(system_instruction=system)` when creating the client, not injected into the messages list like OpenAI does.

#### `generate_content_async`

```python
response = await client.generate_content_async(
    gemini_messages,
    generation_config=self._genai.GenerationConfig(
        max_output_tokens=max_tokens,
    ),
)
```

| Part | What it is |
|---|---|
| `await` | Async call — event loop released while Gemini's API responds |
| `client` | A `GenerativeModel` instance for the specific Gemini model requested |
| `.generate_content_async(...)` | Gemini's equivalent of OpenAI's `chat.completions.create()` |
| `gemini_messages` | The converted message list |
| `generation_config=GenerationConfig(...)` | Gemini's way of passing generation parameters |
| `max_output_tokens=max_tokens` | Gemini uses `max_output_tokens`, OpenAI uses `max_tokens` — different SDK, different name |

`response.text` at the end is Gemini's equivalent of `response.choices[0].message.content` — it returns the generated text directly.

---

### Q5 — `AnthropicProvider` deep dive

**File:** [pim_core/llm/providers/anthropic_provider.py](pim_core/llm/providers/anthropic_provider.py)

```python
response = await self._client.messages.create(
    model=model,
    max_tokens=max_tokens,
    system=system,
    messages=messages,
)
```

Anthropic's SDK is the cleanest of the three because its API design separates the system prompt from the conversation messages as a dedicated `system=` parameter — instead of requiring you to prepend it to the messages list like OpenAI does.

| Parameter | What it carries |
|---|---|
| `model` | e.g. `"claude-sonnet-4-6"` |
| `max_tokens` | Hard cap on response length |
| `system` | The system prompt — passed as a separate parameter, not in `messages` |
| `messages` | Just the conversation turns — `[{"role": "user", "content": "..."}]` |

The response structure:

```python
# Anthropic returns:
Message(
    content=[
        ContentBlock(type="text", text='{"title": "...", "description": "..."}')
    ],
    model="claude-sonnet-4-6",
    usage=Usage(input_tokens=..., output_tokens=...)
)

# We extract:
response.content[0].text   # the text string
```

Unlike OpenAI's `response.choices[0].message.content`, Anthropic uses `response.content[0].text`. Different names, same idea — the generated text string.

**Side-by-side comparison of all three providers:**

```python
# OpenAI
all_messages = [{"role": "system", "content": system}] + messages
response = await client.chat.completions.create(model=model, messages=all_messages, max_tokens=max_tokens)
return response.choices[0].message.content

# Google
client = GenerativeModel(model_name=model, system_instruction=system)
gemini_msgs = [{"role": ..., "parts": [m["content"]]} for m in messages]
response = await client.generate_content_async(gemini_msgs, generation_config=GenerationConfig(max_output_tokens=max_tokens))
return response.text

# Anthropic
response = await client.messages.create(model=model, max_tokens=max_tokens, system=system, messages=messages)
return response.content[0].text
```

All three do the same thing. The providers are what hide these differences from the rest of the codebase.

---

### Q6 — `LLMClient` deep dive

**File:** [pim_core/llm/client.py](pim_core/llm/client.py)

```python
class LLMClient:
    async def complete(
        self,
        system: str,
        messages: list[dict],
        model: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        from pim_core.config import settings
        model_name = model or settings.claude_model
        provider = get_provider(model_name)
        return await provider.complete(
            model=model_name,
            system=system,
            messages=messages,
            max_tokens=max_tokens,
        )

llm_client = LLMClient()  # module-level singleton
```

**What is `LLMClient`?**

`LLMClient` is the **single public interface** for making LLM calls anywhere in the codebase. No agent, workflow, or tool should ever import a provider directly. Every LLM call goes through `llm_client.complete()`.

Think of it like a database connection pool — the rest of your application doesn't care if the database is Postgres or MySQL; it just calls `db.execute(...)`. `LLMClient` is that unified interface for LLM calls.

**Why is `complete` async?**

Because every provider's `complete()` is async (they all make network calls). To call an async function you must either `await` it (inside another async function) or run it in an event loop. `LLMClient.complete()` is declared `async` so callers can `await llm_client.complete(...)`.

**How does it tie to `base.py`?**

```
LLMClient.complete()
    │
    │  calls get_provider(model_name)
    │  factory returns a BaseLLMProvider subclass instance
    │          │
    │          │  e.g. OpenAIProvider (which inherits BaseLLMProvider)
    │
    ▼
provider.complete(model, system, messages, max_tokens)
    │
    │  This works regardless of which concrete class provider is
    │  because all subclasses implement complete() with the same signature
    │  — guaranteed by @abstractmethod in base.py
    │
    ▼
returns: str (the LLM response text)
```

`provider.complete(...)` works here because Python's polymorphism guarantees that whatever object `get_provider()` returns, it will have a `complete()` method with this exact signature. The `@abstractmethod` decorator in `base.py` enforces this guarantee at class construction time.

**Why call `provider.complete(...)` instead of calling the SDK directly?**

Because `LLMClient` doesn't know (and shouldn't know) which provider it has. It just calls the contract method. This is the **Strategy Pattern**:

```
Without the pattern:                    With the pattern:
┌─────────────────────────────┐         ┌────────────────────────┐
│ if model.startswith("gpt"): │         │ provider = get_provider│
│   openai_call(...)          │         │ provider.complete(...)  │
│ elif model.startswith("cl"  │         └────────────────────────┘
│   anthropic_call(...)       │
│ elif model.startswith("gem" │         Adding Mistral:
│   gemini_call(...)          │         • Add MistralProvider file
│ elif model.startswith("mis" │         • Add to factory
│   mistral_call(...)         │         • Nothing else changes
└─────────────────────────────┘
                                         vs.
Adding Mistral:                         
• Add new elif branch everywhere        
  this if-block appears                 
```

---

### Q7 — `factory.py` deep dive

**File:** [pim_core/llm/factory.py](pim_core/llm/factory.py)

#### `_instances: dict[str, BaseLLMProvider] = {}`

```python
_instances: dict[str, BaseLLMProvider] = {}
```

This is a **module-level dictionary** that caches provider instances. The keys are provider names (`"anthropic"`, `"openai"`, `"google"`), the values are the actual provider objects.

**Why is this necessary?**

Provider `__init__` methods do expensive work:
- Check API keys
- Import SDK packages (which themselves do initialization)
- Create HTTP clients and connection pools

If we created a new provider on every LLM call, we would pay this cost thousands of times. With the cache, we pay it once — the first time that provider is used — and reuse the same instance forever.

```python
def get_provider(model_name: str) -> BaseLLMProvider:
    if model_name in _ANTHROPIC_MODELS:
        key = "anthropic"
        if key not in _instances:             # ← only create once
            from pim_core.llm.providers.anthropic_provider import AnthropicProvider
            _instances[key] = AnthropicProvider()
        return _instances[key]                # ← always return the cached one
```

This is the **Singleton Pattern** applied per-provider. After the first request for any Anthropic model, `_instances["anthropic"]` exists and is reused forever.

#### `frozenset` and `_ANTHROPIC_MODELS`

```python
_ANTHROPIC_MODELS: frozenset[str] = frozenset(m.value for m in AllAvailableModelsAnthropic)
```

Breaking this down piece by piece:

**`m.value for m in AllAvailableModelsAnthropic`** — this is a generator expression that extracts the string values from the enum:

```python
# AllAvailableModelsAnthropic is an Enum defined like:
class AllAvailableModelsAnthropic(str, Enum):
    CLAUDE_OPUS = "claude-opus-4-6"
    CLAUDE_SONNET = "claude-sonnet-4-6"
    CLAUDE_HAIKU = "claude-haiku-4-5-20251001"

# m.value for m in AllAvailableModelsAnthropic yields:
# "claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"
```

**`frozenset(...)`** — wraps those strings in a frozen (immutable) set.

Why `frozenset` specifically?

| Property | Why it matters here |
|---|---|
| **Set** (not list) | `in` check is O(1) — instant lookup regardless of size. A list `in` check is O(n). |
| **Frozen** (immutable) | The valid model names should never change at runtime. `frozenset` enforces this — you cannot add/remove elements accidentally. |
| **Immutable** | Can be used as a dictionary key or stored in other sets safely. |

```python
# O(1) lookup — works the same with 3 models or 300 models
if model_name in _ANTHROPIC_MODELS:   # instant
    ...
```

#### `all_models = sorted(_ANTHROPIC_MODELS | _OPENAI_MODELS | _GOOGLE_MODELS)`

```python
all_models = sorted(_ANTHROPIC_MODELS | _OPENAI_MODELS | _GOOGLE_MODELS)
```

The `|` operator between two sets returns their **union** — a new set containing all elements from both, with no duplicates:

```python
{"a", "b"} | {"b", "c"} | {"d"}  →  {"a", "b", "c", "d"}
```

`sorted(...)` converts the set to a sorted list (sets have no ordering) so the error message lists models in alphabetical order — helpful for reading:

```
ValueError: No provider found for model 'unknown-xyz'.
Supported models: claude-haiku-4-5-20251001, claude-opus-4-6, claude-sonnet-4-6,
gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash, gpt-4-turbo, gpt-4o, ...
```

#### Why does `_ANTHROPIC_MODELS` start with `_`?

The leading underscore is a **Python convention** for "this is module-private". It is not enforced by the language (unlike Java's `private` keyword), but it signals to other developers:

> "Do not import `_ANTHROPIC_MODELS` from outside this module. It's an implementation detail. Use `get_provider()` instead."

Linters and IDEs respect this convention and will warn you if you import a name starting with `_` from outside its module.

---

### Q8 — `AgentModelRegistry` deep dive

**File:** [pim_core/llm/registry.py](pim_core/llm/registry.py)

#### What is a registry in general?

A **registry** is a central lookup table that maps names to things. Real-world registries you already know:

| Real-world registry | Maps | To |
|---|---|---|
| DNS registry | Domain name (`google.com`) | IP address (`142.250.80.46`) |
| Docker image registry | Image name (`nginx:latest`) | Image binary |
| Windows Registry | Software name | Configuration values |
| Service registry (Consul, etcd) | Service name (`user-service`) | IP:port of running instance |

In Python, a registry is typically just a dictionary wrapped in a class with lookup and mutation methods.

#### What is `AgentModelRegistry`?

```python
class AgentModelRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, str] = agent_model_db.load_all()

    def set(self, agent_name: str, model_name: str) -> None:
        self._registry[agent_name] = model_name
        agent_model_db.upsert(agent_name, model_name)   # write to SQLite

    def get(self, agent_name: str) -> str:
        if agent_name in self._registry:
            return self._registry[agent_name]            # explicit assignment
        from pim_core.config import settings
        return settings.claude_model                     # fallback to default

    def all(self) -> dict[str, str]:
        return dict(self._registry)                      # snapshot copy

    def remove(self, agent_name: str) -> None:
        self._registry.pop(agent_name, None)
        agent_model_db.delete(agent_name)                # remove from SQLite

agent_model_registry = AgentModelRegistry()   # module-level singleton
```

`AgentModelRegistry` maps **agent names** to **model names** at runtime:

```
"product_description_generator"  →  "gpt-4o"
"catalog"                        →  "gemini-2.0-flash"
"procurement"                    →  (not set → falls back to "claude-sonnet-4-6")
```

**Two layers of storage:**

```
┌──────────────────────────────────────────────────┐
│  In-memory dict: self._registry                  │
│  { "product_description_generator": "gpt-4o" }   │  ← fast O(1) lookups per request
└──────────────────────────────┬───────────────────┘
                               │ written to on every set() / remove()
                               ▼
┌──────────────────────────────────────────────────┐
│  SQLite database: agent_models.db                │  ← survives server restarts
│  Table: agent_models                             │
│  ┌────────────────────────────┬──────────────┐   │
│  │ agent_name                 │ model_name   │   │
│  ├────────────────────────────┼──────────────┤   │
│  │ product_description_genera │ gpt-4o       │   │
│  │ catalog                    │ gemini-2.0-f │   │
│  └────────────────────────────┴──────────────┘   │
└──────────────────────────────────────────────────┘
```

On startup, `__init__` calls `agent_model_db.load_all()` which reads SQLite and pre-populates `self._registry`. After that every `get()` is purely in-memory — no database query on the hot path.

**The fallback chain for `get()`:**

```
agent_model_registry.get("product_description_generator")
  │
  ├── Is "product_description_generator" in self._registry?
  │     YES → return "gpt-4o"
  │     NO  → return settings.claude_model  (e.g. "claude-sonnet-4-6")
```

This means every agent works out of the box with Claude as the default, and any agent can be upgraded to GPT or Gemini without touching code.

---

### Q9 — How does this design make the code modular? (with diagrams)

#### Adding a new provider (Mistral, Cohere, etc.)

You only touch **two files**. Everything else stays the same.

**Step 1 — Add the model names to the enum** ([pim_core/utils/all_available_models.py](pim_core/utils/all_available_models.py)):

```python
class AllAvailableModelsMistral(str, Enum):
    MISTRAL_LARGE = "mistral-large-latest"
    MISTRAL_SMALL = "mistral-small-latest"
```

**Step 2 — Create the provider** (new file: `pim_core/llm/providers/mistral_provider.py`):

```python
from pim_core.llm.providers.base import BaseLLMProvider

class MistralProvider(BaseLLMProvider):
    def __init__(self) -> None:
        try:
            from mistralai import Mistral
        except ImportError as exc:
            raise ImportError("pip install mistralai") from exc
        from pim_core.config import settings
        self._client = Mistral(api_key=settings.mistral_api_key)

    async def complete(self, model: str, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        # Mistral uses the same OpenAI-compatible format
        all_messages = [{"role": "system", "content": system}] + messages
        response = await self._client.chat.complete_async(
            model=model,
            messages=all_messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
```

**Step 3 — Register in the factory** ([pim_core/llm/factory.py](pim_core/llm/factory.py), add ~6 lines):

```python
from pim_core.utils.all_available_models import AllAvailableModelsMistral
_MISTRAL_MODELS: frozenset[str] = frozenset(m.value for m in AllAvailableModelsMistral)

def get_provider(model_name: str) -> BaseLLMProvider:
    # ... existing anthropic, openai, google blocks ...

    if model_name in _MISTRAL_MODELS:        # ← add this block
        key = "mistral"
        if key not in _instances:
            from pim_core.llm.providers.mistral_provider import MistralProvider
            _instances[key] = MistralProvider()
        return _instances[key]
```

Nothing else changes. The `LLMClient`, the registry, the workflow, the routes — all untouched. Any agent can now be assigned a Mistral model via `POST /agents-settings/{name}/model`.

```
Before adding Mistral:        After adding Mistral:
                              
LLMClient                     LLMClient
    │                             │
    ▼                             ▼
factory.py                    factory.py
    │                             │
    ├── AnthropicProvider          ├── AnthropicProvider
    ├── OpenAIProvider             ├── OpenAIProvider
    └── GoogleProvider             ├── GoogleProvider
                                  └── MistralProvider  ← new, nothing else touched
```

---

#### Swapping providers at runtime (without restart)

This is the core feature. Here is the full flow when an operator calls the API:

```
Operator                  FastAPI                  Registry           Next generate call
   │                         │                        │                      │
   │  POST /agents-settings  │                        │                      │
   │  /product_description_  │                        │                      │
   │  generator/model        │                        │                      │
   │  {"model": "gpt-4o"}    │                        │                      │
   │────────────────────────►│                        │                      │
   │                         │                        │                      │
   │                         │  validate "gpt-4o"     │                      │
   │                         │  in _OPENAI_MODELS ✓   │                      │
   │                         │                        │                      │
   │                         │  registry.set(         │                      │
   │                         │   "product_desc...",   │                      │
   │                         │   "gpt-4o")            │                      │
   │                         │───────────────────────►│                      │
   │                         │                        │                      │
   │                         │                        │ _registry["product_  │
   │                         │                        │ desc..."] = "gpt-4o" │
   │                         │                        │                      │
   │                         │                        │ SQLite.upsert(...)   │
   │                         │                        │                      │
   │◄────────────────────────│                        │                      │
   │  200 OK                 │                        │                      │
   │  {"agent": "product_    │                        │                      │
   │   description_gen...",  │                        │                      │
   │   "model": "gpt-4o"}    │                        │                      │
   │                         │                        │                      │
   │                         │                        │  registry.get(       │
   │                         │                        │  "product_desc...")  │
   │                         │                        │◄─────────────────────│
   │                         │                        │                      │
   │                         │                        │ returns "gpt-4o"     │
   │                         │                        │─────────────────────►│
   │                         │                        │                      │
   │                         │                        │  factory.get_provider│
   │                         │                        │  ("gpt-4o")          │
   │                         │                        │  → OpenAIProvider    │
   │                         │                        │                      │
   │                         │                        │  OpenAI API called   │
```

**Key insight:** The registry is read on every LLM call (step 6 in `generate_node`). There is no caching of the model name inside the workflow. So the next call after `registry.set(...)` uses the new model immediately.

---

#### Writing tests with a mock provider

Because `BaseLLMProvider` defines the contract, you can write a `MockProvider` in tests that:
- Extends `BaseLLMProvider`
- Implements `complete()` to return a hardcoded string
- Never makes any real network calls

```python
# In a test file:
from pim_core.llm.providers.base import BaseLLMProvider

class MockProvider(BaseLLMProvider):
    def __init__(self, response_text: str):
        self._response = response_text

    async def complete(self, model, system, messages, max_tokens=1024) -> str:
        return self._response  # always returns this, no API call
```

**Using it in a test:**

```python
from unittest.mock import patch

FAKE_LLM_RESPONSE = '{"title": "Test Title", "description": "Test desc", "seo_keywords": []}'

with patch(
    "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
    new=AsyncMock(return_value=FAKE_LLM_RESPONSE),
):
    result = await generate_description(product=..., channel="ecommerce")
    assert result.title == "Test Title"
```

**Why this works:**

```
Normal execution:                 Test execution:
                                  
llm_client.complete(...)          llm_client.complete(...)  ← patched
    │                                 │
    ▼                                 ▼
get_provider(model_name)          AsyncMock()  ← returns FAKE_LLM_RESPONSE
    │                                 │
    ▼                                 ▼
AnthropicProvider.complete()      FAKE_LLM_RESPONSE string
    │                                 │
    ▼                                 ▼
Real HTTP call to Claude          No network call — instant, deterministic
```

The patch replaces `llm_client.complete` at the exact import location where the workflow uses it. Everything above the patch (route handler, adapter, tool) and below the patch (JSON parsing, DescriptionResult assembly) runs for real — only the actual LLM call is faked.

---

### The full modularity map

```
                    ┌─────────────────────────────────────┐
                    │         base.py                     │
                    │   BaseLLMProvider (ABC)              │
                    │   + complete() [abstract]            │
                    └────┬──────────┬────────────┬────────┘
                         │          │            │
              implements │          │            │ implements
                         │          │            │
               ┌─────────┴──┐  ┌───┴──────┐ ┌──┴──────────┐
               │ Anthropic  │  │  OpenAI  │ │   Google    │
               │ Provider   │  │ Provider │ │  Provider   │
               └─────────┬──┘  └───┬──────┘ └──┬──────────┘
                         │         │            │
                         └────┬────┘────────────┘
                              │
                      instantiates
                              │
               ┌──────────────▼──────────────────┐
               │         factory.py               │
               │   get_provider(model_name)        │
               │   _instances = {}  (cache)        │
               │   _ANTHROPIC_MODELS (frozenset)   │
               │   _OPENAI_MODELS    (frozenset)   │
               │   _GOOGLE_MODELS    (frozenset)   │
               └──────────────┬──────────────────┘
                              │
                         used by
                              │
               ┌──────────────▼──────────────────┐
               │         client.py               │
               │   LLMClient.complete()           │
               │   llm_client (singleton)         │
               └──────────────┬──────────────────┘
                              │
                         used by
                              │
               ┌──────────────▼──────────────────┐
               │     description_workflow.py      │
               │   generate_node()               │
               │   reads model from registry →   │
               │   calls llm_client.complete()    │
               └──────────────────────────────────┘
                              │
                     model resolved by
                              │
               ┌──────────────▼──────────────────┐
               │         registry.py             │
               │   AgentModelRegistry             │
               │   _registry = {}  (in-memory)    │
               │   agent_model_db  (SQLite)       │
               │   agent_model_registry (singleton│
               └──────────────────────────────────┘
                              ▲
                    written by │
                              │
               ┌──────────────┴──────────────────┐
               │       agent_registry.py          │
               │   POST /agents-settings/*/model  │
               │   DELETE /agents-settings/*/model│
               │   GET /agents-settings/models    │
               └─────────────────────────────────┘
```

**Three things that prove the design is modular:**

1. **Add Mistral** → create one file + add one block in `factory.py`. Zero other changes.
2. **Swap from Claude to GPT** → one `POST` API call. Zero code changes. Zero restarts.
3. **Test the workflow** → patch `llm_client.complete`. Test runs in milliseconds, no API key needed, no network.

> **Interview summary:** "The LLM provider layer uses three design patterns together. `BaseLLMProvider` ABC defines the contract (Strategy Pattern). `get_provider()` decides which implementation to instantiate (Factory Pattern). `agent_model_registry` holds the runtime assignment of which model each agent currently uses. The result is that you can add providers, swap models, and write tests — all without touching existing code. This is the Open/Closed Principle from SOLID: open for extension, closed for modification."

---

## 17. Logging Architecture (CloudWatch + Provider Pattern)

### Overview

Logging is a cross-cutting concern — every component in the microservice (routes, agent, workflow, LLM client, registry) emits structured log lines. The logging layer is built using the **same provider-agnostic pattern as the LLM layer**, so switching from AWS CloudWatch to GCP Cloud Logging or Azure Monitor requires changing a single environment variable and zero application code.

---

### How It Works

**Step 1 — Request arrives, middleware generates `request_id` and loads `company_id`**

Every incoming HTTP request is assigned a UUID (`request_id`) by a FastAPI middleware. The `company_id` from the authenticated request is also injected into the same Python `contextvar`. Both propagate automatically to every function call downstream — no manual passing required.

**Step 2 — Components emit logs through `StructuredLogger`**

No component imports `watchtower`, `google-cloud-logging`, or any vendor SDK directly. Every component calls `StructuredLogger.info()`, `.debug()`, `.warning()`, or `.error()`. `StructuredLogger` is the **single entry point** for all logging — identical to how `LLMClient` is the single entry point for all LLM calls.

**Step 3 — `python-json-logger` formats each line as JSON**

```json
{
  "level":      "ERROR",
  "timestamp":  "2026-04-23T09:25:33.882Z",
  "request_id": "req-a1b2c3",
  "class":      "LLMClient",
  "method":     "generate",
  "message":    "Anthropic API call failed — AuthenticationError: invalid API key"
}
```

**Step 4 — `LogProviderFactory` resolves the correct handler for this company**

`LogProviderFactory.get_handler(company_id)` checks its in-memory cache for a handler already created for that company. If found, it is returned instantly. If not, the factory reads `company_log_provider_config` from the database for that `company_id`, creates the appropriate provider handler, caches it, and returns it. If the company has no row in the table, the factory falls back to the global `LOG_PROVIDER` from `.env`.

**Step 5 — The handler ships the JSON line to the company's configured cloud backend**

Each company's logs land in their own isolated log group on their own cloud platform. Company 12 (CloudWatch) never sees Company 33's logs (GCP), and vice versa.

**Step 6 — Cloud backend stores, indexes, and makes logs queryable**

CloudWatch Logs Insights, GCP Log Explorer, or Azure Monitor each provide SQL-like querying on the JSON fields.

---

### Provider Layer Architecture

```
BaseLogProvider          (pim_core/logging/base.py)
  ├── get_handler() → logging.Handler   abstract
  └── get_log_group() → str             abstract
        │
        ├── CloudWatchLogProvider      (pim_core/logging/providers/cloudwatch.py)
        │   └── watchtower.CloudWatchLogHandler
        │   └── ships to: AWS CloudWatch Log Group
        │
        ├── GCPCloudLoggingProvider    (pim_core/logging/providers/gcp.py)
        │   └── google.cloud.logging.handlers.CloudLoggingHandler
        │   └── ships to: GCP Cloud Logging
        │
        └── AzureMonitorLogProvider    (pim_core/logging/providers/azure.py)
            └── azure.monitor.opentelemetry AzureLogHandler
            └── ships to: Azure Monitor / Log Analytics Workspace

LogProviderFactory       (pim_core/logging/factory.py)
  ├── _cache: dict[company_id → handler_instance]
  ├── get_handler(company_id) → logging.Handler
  │     ├── cache hit  → return cached handler instantly
  │     ├── cache miss → read company_log_provider_config from DB
  │     │                 → create provider → cache → return
  │     └── no DB row  → fall back to LOG_PROVIDER from .env
  └── refresh(company_id)  ← called when operator updates via API

StructuredLogger         (pim_core/logging/logger.py)
  └── Single entry point — application code only ever touches this
  └── Attaches request_id from contextvar on every log record
```

---

### Parallel With the LLM Provider Layer

| LLM Layer | Logging Layer |
|---|---|
| `BaseLLMProvider` | `BaseLogProvider` |
| `AnthropicProvider` | `CloudWatchLogProvider` |
| `OpenAIProvider` | `GCPCloudLoggingProvider` |
| `GoogleProvider` | `AzureMonitorLogProvider` |
| `LLMProviderFactory` | `LogProviderFactory` |
| `LLMClient` | `StructuredLogger` |
| `CLAUDE_MODEL=claude-sonnet-4-6` | `LOG_PROVIDER=cloudwatch` |

Any developer already familiar with the LLM provider layer understands the logging layer immediately — same patterns, same structure.

The second parallel goes deeper — just as `AgentModelRegistry` lets an operator assign a different LLM model per agent via API, `LogProviderFactory` (backed by `company_log_provider_config`) lets an operator assign a different cloud log provider per company via API. The mechanism is identical:

| `AgentModelRegistry` | `LogProviderFactory` |
|---|---|
| Reads model assignments from SQLite on startup | Reads provider config from `company_log_provider_config` on startup |
| `{agent_name: model_string}` in-memory cache | `{company_id: handler_instance}` in-memory cache |
| Falls back to `CLAUDE_MODEL` env var | Falls back to `LOG_PROVIDER` env var |
| Updated via `POST /agents-settings/{name}/model` | Updated via `POST /log-settings/{company_id}/provider` |
| Cache entry refreshed on each `set` call | Cache entry refreshed on each `set` call |
| Zero DB cost per LLM call after first load | Zero DB cost per log line after first load |

---

### Per-Company Log Provider Routing

The `company_log_provider_config` database table drives which cloud backend receives each company's logs at runtime. This is how it all connects:

```
Operator calls:
  POST /log-settings/12/provider
  { "log_provider": "cloudwatch", "log_group_name": "/pim-ai/company-12",
    "region": "eu-west-1", "credentials_secret_ref": "arn:aws:secretsmanager:..." }
        │
        ▼
  Write row to company_log_provider_config WHERE company_id=12
        │
        ▼
  LogProviderFactory.refresh(company_id=12)
  └── fetches credentials from AWS Secrets Manager using credentials_secret_ref
  └── creates CloudWatchLogProvider(log_group="/pim-ai/company-12", region="eu-west-1")
  └── stores handler in _cache[12]

─────────────────────────────────────────────────────
Next request arrives for company_id=12:
─────────────────────────────────────────────────────
  Middleware injects company_id=12 into contextvar
        │
        ▼
  StructuredLogger.info("LLM call completed...")
        │
        ▼
  LogProviderFactory.get_handler(company_id=12)
  └── cache hit → returns CloudWatchLogProvider handler instantly
        │
        ▼
  Log line → AWS CloudWatch /pim-ai/company-12

─────────────────────────────────────────────────────
Simultaneously, request for company_id=33:
─────────────────────────────────────────────────────
  LogProviderFactory.get_handler(company_id=33)
  └── cache hit → returns GCPCloudLoggingProvider handler
        │
        ▼
  Log line → GCP Cloud Logging (company 33's project)

─────────────────────────────────────────────────────
Request for company_id=99 (no DB row — new company):
─────────────────────────────────────────────────────
  LogProviderFactory.get_handler(company_id=99)
  └── no cache, no DB row → falls back to LOG_PROVIDER from .env
        │
        ▼
  Log line → default cloud backend (e.g. CloudWatch)
```

**The result:** Each company's logs land in their own isolated log group on their own cloud platform. A company on AWS never shares a log group with a company on GCP. Compliance, billing, and access control all stay cleanly separated per customer.

**The `company_log_provider_config` table schema** is documented in `project_task_list/db_schema_design_proposal/database_schema_design_proposal.xlsx`.

---

### Log Schemas — Five Distinct Levels

The logging system uses five distinct schemas. The first four (`ERROR`, `INFO`, `WARNING`, `DEBUG`) are standard Python log levels filtered by `LOG_LEVEL` in `.env`. The fifth (`AUDIT`) is a separate event that is **always emitted regardless of `LOG_LEVEL`** — it captures business-critical data that must never be accidentally silenced in production.

---

#### ERROR — emitted from `except` blocks only

Carries the exception message exactly as raised. Only fires when something has gone wrong and was caught by a `try/except` block.

```json
{
  "level":      "ERROR",
  "timestamp":  "2026-04-23T09:25:33.882Z",
  "request_id": "req-a1b2c3",
  "class":      "LLMClient",
  "method":     "generate",
  "message":    "Anthropic API call failed — AuthenticationError: invalid API key"
}
```

---

#### INFO — emitted on successful method exit

Confirms that a method completed without error. Includes the key outcome so you can see what happened without reading the full debug payload.

```json
{
  "level":      "INFO",
  "timestamp":  "2026-04-23T09:25:35.562Z",
  "request_id": "req-a1b2c3",
  "class":      "LLMClient",
  "method":     "generate",
  "message":    "LLM call completed successfully — model=claude-sonnet-4-6, latency_ms=1680"
}
```

---

#### WARNING — emitted when something worked but looks suspicious

Fires when execution continued but a potential problem was detected — empty fields, slow responses, fallbacks triggered, missing config. Does not mean failure; means "watch this".

```json
{
  "level":      "WARNING",
  "timestamp":  "2026-04-23T09:25:33.001Z",
  "request_id": "req-d4e5f6",
  "class":      "BrandVoicePromptBuilder",
  "method":     "build_prompt",
  "message":    "productName is empty — LLM will have limited context for productID=705517"
}
```

---

#### DEBUG — emitted for verbose technical detail (dev/staging only)

Captures internal state — raw payloads, token counts, parsed values — useful for diagnosing issues in development. Disabled in production by setting `LOG_LEVEL=INFO`.

```json
{
  "level":        "DEBUG",
  "timestamp":    "2026-04-23T09:25:33.445Z",
  "request_id":   "req-a1b2c3",
  "class":        "LLMClient",
  "method":       "generate",
  "message":      "Raw LLM payload dispatched",
  "payload_tokens": 412,
  "model":        "claude-sonnet-4-6"
}
```

---

#### AUDIT — always emitted, never filtered

This is a separate structured event that records the business outcome of every agent action. It is emitted through a dedicated `AuditLogger` (not `StructuredLogger`) so it bypasses `LOG_LEVEL` and is always captured, even in production with `LOG_LEVEL=ERROR`. Inspired by the audit log design proposed by Smit Patel.

```json
{
  "level":      "AUDIT",
  "timestamp":  "2026-04-23T09:25:35.562Z",
  "request_id": "req-a1b2c3",
  "company_id": 12,
  "agent_id":   1,
  "action":     "generate",
  "status":     "success",
  "latency_ms": 1680,
  "llm_model":  "claude-sonnet-4-6",
  "output_quality": {
    "schema_valid":          true,
    "title_length_ok":       true,
    "description_length_ok": true,
    "keywords_hit_rate":     0.85,
    "finish_reason":         "end_turn"
  },
  "created_at": "2026-04-23T09:25:33.882Z"
}
```

**`output_quality` — why these five fields and not a single accuracy float:**

True model accuracy requires ground truth — a known correct answer to compare the LLM output against. At runtime for a generative task, ground truth does not exist. Instead, `output_quality` records **proxy signals that are fully measurable at runtime** and together give a reliable picture of whether the model followed its instructions:

| Field | Type | How measured | What it tells you |
|---|---|---|---|
| `schema_valid` | boolean | Did `json.loads()` succeed on the response? | Whether the model followed the JSON output format instruction |
| `title_length_ok` | boolean | `len(title) <= brand_voice.max_title_length` | Whether the title constraint was respected |
| `description_length_ok` | boolean | `len(description) <= brand_voice.max_description_length` | Whether the description constraint was respected |
| `keywords_hit_rate` | float 0–1 | `keywords_found / total_keywords` from `brand_voice.keywords` | % of required brand keywords the model included in the output |
| `finish_reason` | string | Returned by the LLM SDK (`end_turn`, `max_tokens`, `stop`) | Whether the model completed naturally or was cut off by the token limit |

A `keywords_hit_rate` of `1.0` and `finish_reason = "end_turn"` with all boolean fields `true` means the model performed perfectly against measurable constraints. Any deviation is immediately visible in CloudWatch Logs Insights:

```sql
-- Find responses where the model was cut off by token limit
fields timestamp, request_id, llm_model, output_quality.finish_reason
| filter level = "AUDIT" and output_quality.finish_reason = "max_tokens"

-- Find responses where required keywords were missed
fields timestamp, company_id, output_quality.keywords_hit_rate
| filter level = "AUDIT" and output_quality.keywords_hit_rate < 1.0
| sort output_quality.keywords_hit_rate asc

-- Average keyword hit rate per LLM model — compare model quality
fields llm_model, output_quality.keywords_hit_rate
| filter level = "AUDIT"
| stats avg(output_quality.keywords_hit_rate) as avg_keyword_score by llm_model
| sort avg_keyword_score desc
```

**Why AUDIT is separate from DEBUG:**

| | DEBUG | AUDIT |
|---|---|---|
| Purpose | Technical diagnosis | Business audit trail + output quality tracking |
| Production? | Usually disabled (`LOG_LEVEL=INFO`) | Always on — never filtered |
| Who reads it | Engineers debugging issues | Product, compliance, billing, QA |
| Fields | Raw payloads, token counts | company_id, action, status, latency, output_quality |

---

### Why CloudWatch

AWS CloudWatch is the chosen backend because the microservice is deployed on AWS. It requires zero additional infrastructure — logs flow from stdout to CloudWatch automatically via the `watchtower` handler.

**Pros:**

| Benefit | Detail |
|---|---|
| Zero infrastructure | No log server to run or maintain |
| Native AWS integration | Alarms, dashboards, metric filters built in |
| CloudWatch Logs Insights | SQL-like queries directly on JSON log fields |
| Retention policies | Auto-delete after N days — directly controls storage cost |
| Works on EC2, ECS, Lambda | Same setup across all AWS compute options |

**Cons:**

| Limitation | Detail |
|---|---|
| Cost grows with volume | Charged per GB ingested + stored + queried |
| Vendor lock-in | Tied to AWS — reason this layer uses a provider pattern |
| Insights learning curve | CloudWatch Insights query syntax is not standard SQL |
| Cold query latency | Large log groups can be slow to query |

---

### CloudWatch Logs Insights — Example Queries

```sql
-- Trace one full request end-to-end (all 5 levels)
fields level, timestamp, class, method, message
| filter request_id = "req-a1b2c3"
| sort timestamp asc

-- All errors in the last hour
fields timestamp, request_id, class, method, message
| filter level = "ERROR"
| sort timestamp desc
| limit 50

-- Find the most error-prone component
fields class
| filter level = "ERROR"
| stats count() as error_count by class
| sort error_count desc

-- Warnings about suspicious inputs or slow responses
fields timestamp, request_id, message
| filter level = "WARNING"
| sort timestamp desc

-- Audit: all actions for a specific company
fields timestamp, request_id, action, status, latency_ms, llm_model
| filter level = "AUDIT" and company_id = 12
| sort timestamp desc

-- Audit: average latency per agent action
fields action, latency_ms
| filter level = "AUDIT"
| stats avg(latency_ms) as avg_ms, count() as calls by action
| sort avg_ms desc

-- Audit: failure rate per company
fields company_id, status
| filter level = "AUDIT"
| stats count() as total,
        sum(status = "failed") as failures by company_id
| sort failures desc
```

---

### Adding a New Log Provider (e.g. Datadog)

1. Create `pim_core/logging/providers/datadog.py` — extend `BaseLogProvider`, implement `get_handler()`
2. Add `"datadog"` case to `LogProviderFactory`
3. Set `LOG_PROVIDER=datadog` in `.env`

Zero changes to `StructuredLogger`, zero changes to any agent or workflow. This is the **Open/Closed Principle** — open for extension, closed for modification.

---

### Design Patterns

| Pattern | Where Applied |
|---|---|
| **Strategy** | `BaseLogProvider` + concrete providers — swap log backend at runtime |
| **Factory** | `LogProviderFactory` — instantiates the correct provider from config |
| **Adapter** | Each provider adapts its vendor SDK to the same `get_handler()` interface |
| **Singleton** | `StructuredLogger` — one shared logger instance across the entire app |
| **Context Variable** | `request_id` propagated via Python `contextvars` — no manual passing through call chains |

> **Summary:** The logging layer is a direct structural mirror of the LLM provider layer. `BaseLogProvider` defines the contract, concrete providers adapt vendor SDKs to that contract, `LogProviderFactory` routes based on config, and `StructuredLogger` is the only surface the rest of the application touches. Adding a new cloud platform means adding one file and one line in the factory — nothing else changes.

---

### Implementation Plan

**Goal:** 100% logging coverage — every method and function wrapped in `try/except`, all exceptions handled and logged, `INFO` on success, `AUDIT` on every agent action, `WARNING` on suspicious state.

This plan is **implementation-only** — no architectural changes. The provider layer design above is the target state.

---

#### Phase 1 — Logging Infrastructure (no application code changes)

Build the logging layer itself before touching any existing code.

| Task | File to create | What it does |
|---|---|---|
| Abstract base | `pim_core/logging/base.py` | `BaseLogProvider` ABC with `get_handler()` and `get_log_group()` |
| CloudWatch provider | `pim_core/logging/providers/cloudwatch.py` | `CloudWatchLogProvider` using `watchtower` |
| GCP provider (stub) | `pim_core/logging/providers/gcp.py` | `GCPCloudLoggingProvider` — stub, ready for future wiring |
| Azure provider (stub) | `pim_core/logging/providers/azure.py` | `AzureMonitorLogProvider` — stub, ready for future wiring |
| Factory | `pim_core/logging/factory.py` | `LogProviderFactory.get_handler(LOG_PROVIDER)` |
| Structured logger | `pim_core/logging/logger.py` | `StructuredLogger` singleton — attaches `request_id` from contextvar |
| Audit logger | `pim_core/logging/audit.py` | `AuditLogger` — separate emitter, bypasses `LOG_LEVEL`, always fires |
| Request middleware | `pim_core/logging/middleware.py` | FastAPI middleware — generates UUID `request_id` per request, injects into contextvar |
| Config update | `pim_core/config.py` | Add `LOG_PROVIDER` and `LOG_LEVEL` to `Settings` |
| Env update | `.env` | Add `LOG_PROVIDER=cloudwatch`, `LOG_LEVEL=INFO` |

---

#### Phase 2 — Try/Except Coverage (100% method coverage)

Current state (from codebase audit): only 6 try/except blocks exist. Every file below needs coverage added.

**`pim_core/llm/client.py` — `LLMClient`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `complete()` | `Exception` (base — catches all provider errors) | `ERROR`: exception message | `INFO`: model, latency_ms |

**`pim_core/llm/factory.py` — `LLMProviderFactory`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `get_provider()` | `ValueError` (unknown model prefix) | `ERROR`: unknown model name | `DEBUG`: provider resolved |

**`pim_core/llm/registry.py` — `AgentModelRegistry`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `load()` | `Exception` (SQLite file missing / corrupt) | `ERROR`: db path, exception | `INFO`: registry loaded, N entries |
| `get()` | `KeyError` | `WARNING`: agent not found, returning default | `DEBUG`: model returned |
| `set()` | `Exception` (SQLite write failure) | `ERROR`: exception message | `INFO`: model assigned |

**`pim_core/llm/providers/anthropic_provider.py` — `AnthropicProvider`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `complete()` | `anthropic.APIError`, `Exception` | `ERROR`: status code, message | `DEBUG`: tokens used, latency |

**`pim_core/llm/providers/openai_provider.py` — `OpenAIProvider`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `complete()` | `openai.APIError`, `Exception` | `ERROR`: status code, message | `DEBUG`: tokens used, latency |

**`pim_core/llm/providers/google_provider.py` — `GoogleProvider`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `complete()` | `google.api_core.exceptions.GoogleAPIError`, `Exception` | `ERROR`: exception message | `DEBUG`: tokens used, latency |

**`agents/product_description_generator/workflows/description_workflow.py`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `generate_node()` | `JSONDecodeError`, `KeyError` (already exists — expand) | `ERROR`: exception + raw LLM output snippet | `INFO`: title length, description length |
| `build_state()` (if exists) | `Exception` | `ERROR`: exception message | `DEBUG`: state keys populated |

**`agents/product_description_generator/prompts/brand_voice.py`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `get_system_prompt()` | `Exception` | `ERROR`: exception message | `DEBUG`: prompt token estimate |
| `get_user_message()` | `Exception` | `ERROR`: exception message | `DEBUG`: product fields used |

**`agents/product_description_generator/tools/generate_description.py`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `generate_description()` | `Exception` | `ERROR`: exception message | `INFO`: tool invocation completed |

**`agents/product_description_generator/routes/product_description_generator_api_route.py`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `generate_description_from_pim()` | `Exception` (PIM adapt), `ValueError` (already exists — add logging) | `ERROR`: exception + request summary | `INFO`: HTTP 200 dispatched |

**`agents/product_description_generator/routes/agent_registry.py`**

| Method | Exception to catch | Log on except | Log on success |
|---|---|---|---|
| `set_agent_model()` | `ValueError` (already exists — add logging) | `ERROR`: invalid model name | `INFO`: model assignment recorded |
| `get_agent_model()` | `Exception` | `ERROR`: exception message | `INFO`: model returned |
| `list_models()` | `Exception` | `ERROR`: exception message | `INFO`: N models returned |
| `reset_agent_model()` | `Exception` | `ERROR`: exception message | `INFO`: reset to default |

---

#### Phase 3 — AUDIT Event Emission

Every agent action that completes (success or failure) must emit one AUDIT event. The AUDIT event is emitted at the end of the request lifecycle — after the workflow resolves and the result is available for quality scoring.

**Where to emit:**

| Location | Trigger | Core fields |
|---|---|---|
| `generate_description_from_pim()` in API route | After workflow resolves | `company_id`, `agent_id`, `action=generate`, `status`, `latency_ms`, `llm_model` |
| `generate_description()` MCP tool | After tool resolves | Same fields |

**How `output_quality` is computed before emitting:**

The `output_quality` block is computed inline at the emit site using the `DescriptionResult` returned by the workflow and the `BrandVoice` config from the request. No external calls are needed — all five fields are derived from data already in memory:

| Field | Source |
|---|---|
| `schema_valid` | `True` if workflow returned a `DescriptionResult` without raising `JSONDecodeError` |
| `title_length_ok` | `len(result.title) <= request.brand_voice.max_title_length` |
| `description_length_ok` | `len(result.description) <= request.brand_voice.max_description_length` |
| `keywords_hit_rate` | `sum(1 for kw in brand_voice.keywords if kw.lower() in result.description.lower()) / len(brand_voice.keywords)` — returns `1.0` if keyword list is empty |
| `finish_reason` | Passed through from `LLMClient.complete()` response metadata |

**Status mapping:**

| Condition | `status` value |
|---|---|
| Workflow returned `DescriptionResult` with no error | `success` |
| Workflow returned error state (JSON parse failed, etc.) | `failed` |
| Request escalated to human-in-the-loop review | `escalated` |

---

#### Phase 4 — Middleware Wiring

Wire the `RequestIdMiddleware` into the FastAPI app startup so every request gets a `request_id` before hitting any route.

| Task | File | Change |
|---|---|---|
| Register middleware | `agents/product_description_generator/main.py` | `app.add_middleware(RequestIdMiddleware)` |
| Initialise logger | `main.py` startup | `StructuredLogger.initialise(LogProviderFactory.get_handler())` |

---

#### Coverage Checklist

- [ ] `pim_core/logging/` — all 6 files created (base, 3 providers, factory, logger, audit, middleware)
- [ ] `pim_core/config.py` — `LOG_PROVIDER`, `LOG_LEVEL` added
- [ ] `LLMClient.complete()` — try/except + INFO/ERROR
- [ ] `LLMProviderFactory.get_provider()` — try/except + ERROR/DEBUG
- [ ] `AgentModelRegistry.load()` — try/except + INFO/ERROR
- [ ] `AgentModelRegistry.get()` — try/except + WARNING/DEBUG
- [ ] `AgentModelRegistry.set()` — try/except + INFO/ERROR
- [ ] `AnthropicProvider.complete()` — try/except + DEBUG/ERROR
- [ ] `OpenAIProvider.complete()` — try/except + DEBUG/ERROR
- [ ] `GoogleProvider.complete()` — try/except + DEBUG/ERROR
- [ ] `description_workflow.generate_node()` — expand existing try/except + INFO/ERROR
- [ ] `brand_voice.get_system_prompt()` — try/except + DEBUG/ERROR
- [ ] `brand_voice.get_user_message()` — try/except + DEBUG/ERROR
- [ ] `generate_description tool` — try/except + INFO/ERROR
- [ ] `api_route.generate_description_from_pim()` — expand existing + INFO/ERROR + AUDIT emit
- [ ] `agent_registry` all 4 route handlers — try/except + INFO/ERROR
- [ ] `main.py` — middleware registered, logger initialised
