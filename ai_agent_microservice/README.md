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

---

## 1. Python Version and Dependencies

**Python:** 3.13.7 (tested with CPython from Miniconda)

**Core runtime dependencies:**

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.135.3 | REST API framework |
| `uvicorn` | 0.44.0 | ASGI server |
| `pydantic` | 2.13.1 | Data validation and serialisation |
| `pydantic-settings` | 2.13.1 | `.env` file config loading |
| `langgraph` | 1.1.6 | Agent orchestration graph |
| `anthropic` | 0.95.0 | Anthropic Claude SDK |
| `fastmcp` | 3.2.4 | Model Context Protocol tool registration |
| `httpx` | 0.28.1 | Async HTTP client (used by test client) |

**Optional provider packages (install only what you need):**

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
