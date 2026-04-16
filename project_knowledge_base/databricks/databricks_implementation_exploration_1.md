# Multi-agent AI systems on Databricks: a complete architecture guide

**Databricks' Mosaic AI Agent Framework is not a replacement for LangGraph or LangChain — it is an enterprise deployment, evaluation, and governance layer that wraps around them.** This distinction is the single most important architectural insight for anyone building multi-agent systems on the platform. The framework provides the ChatAgent interface as a universal contract: you author agents in any Python framework you prefer, then plug them into Databricks' infrastructure for serving, monitoring, and governance. For a PIM platform with three specialized agents, the recommended path is a hybrid approach — LangGraph for orchestration logic, Databricks for everything else — deployed as MLflow models on Model Serving endpoints, with Unity Catalog governing all tools and data.

---

## A. What Mosaic AI Agent Framework actually is

Mosaic AI Agent Framework is Databricks' **end-to-end lifecycle platform** for AI agents, covering authoring, evaluation, deployment, and monitoring. It emerged from Databricks' acquisition of MosaicML and reached General Availability across its core components during late 2024 through 2025.

The framework has five pillars. **Agent authoring** supports building agents using any Python framework — LangGraph, LangChain, OpenAI SDK, CrewAI, AutoGen, or plain Python — as long as they conform to the `ChatAgent` interface. **Agent Evaluation** (via `mlflow.evaluate()` with `model_type="databricks-agent"`) uses LLM-as-judge techniques to assess correctness, groundedness, relevance, and safety. **Agent Deployment** packages agents as MLflow models and serves them on Model Serving endpoints via `databricks.agents.deploy()`. **Agent Monitoring** captures all requests and responses in inference tables for automated quality assessment. The **Review App** provides a built-in chat UI for collecting human feedback.

### The `databricks-agents` Python package

The `databricks-agents` package (`pip install databricks-agents`) is the high-level SDK. Its key functions include:

- **`databricks.agents.deploy(model_name, model_version)`** — Deploys a Unity Catalog-registered model as a serving endpoint, automatically provisioning inference tables, the Review App, and feedback collection
- **`databricks.agents.get_deployments()`** — Lists active agent deployments
- **`databricks.agents.delete_deployment()`** — Removes a deployment
- Integration with `mlflow.evaluate()` for agent-specific evaluation metrics

### How it differs from LangGraph, LangChain, AutoGen

**Mosaic AI Agent Framework operates at a different layer of the stack.** LangGraph provides graph-based orchestration logic (nodes, edges, conditional routing, cycles, state management). LangChain provides tool abstractions and chain primitives. AutoGen and CrewAI provide multi-agent conversation patterns. Mosaic AI Agent Framework provides none of these — instead, it provides the **enterprise infrastructure** around them: deployment, serving, evaluation, monitoring, governance, and access control.

The relationship is complementary: you build your agent with LangGraph, wrap it in MLflow's `ChatAgent` interface, and deploy it through Mosaic AI Agent Framework. The `langchain-databricks` package bridges the ecosystems by providing `ChatDatabricks` (LLM wrapper for Databricks endpoints), `DatabricksVectorSearch` (retriever), `DatabricksEmbeddings`, and `UCFunctionToolkit` (Unity Catalog functions as LangChain tools).

### Agent Evaluation metrics

Mosaic AI Agent Evaluation assesses multiple dimensions automatically. **Retrieval quality** metrics include chunk relevance, document recall, and context sufficiency. **Response quality** metrics include answer correctness (vs. ground truth), relevance to query, groundedness in retrieved context, and safety. **Operational metrics** include token counts, latency, and cost estimates. All results appear in the MLflow experiment UI with per-request scores and aggregate metrics.

### Databricks-native tool calling

The primary native pattern uses **Unity Catalog functions as tools**. SQL or Python functions registered in Unity Catalog become agent tools automatically — the framework reads function metadata (parameters, types, docstrings) and generates JSON schemas for LLM function-calling interfaces. When the LLM requests a tool call, the framework executes the UC function in a sandboxed serverless environment with proper permissions. The AI Playground supports interactive tool-calling with UC functions for prototyping.

---

## B. Four architecture options for multi-agent PIM systems

### Option 1: Pure Mosaic AI native agents

Build all agents using the `ChatAgent` interface with UC functions as tools. A supervisor agent routes requests to specialized sub-agents deployed as separate Model Serving endpoints using the **agent-as-tool** pattern.

**Pros:** Simplest dependency chain; fully governed by Unity Catalog; deepest integration with Databricks monitoring, evaluation, and Review App; no external framework dependencies. **Cons:** No built-in graph orchestration or state machines; supervisor routing logic must be hand-coded; no support for cyclical agent communication or complex multi-turn inter-agent conversations; agent-to-agent calls traverse HTTP endpoints, adding **10-50ms latency** per hop. **Maturity:** GA for core components; multi-agent orchestration patterns documented but not as mature as LangGraph's graph abstractions.

### Option 2: LangGraph agents on Databricks Model Serving

Author agents entirely in LangGraph, then deploy them via MLflow. Use `mlflow.langchain.log_model()` to package the LangGraph graph, register in Unity Catalog, and deploy to Model Serving.

**Pros:** Full LangGraph expressiveness — cycles, conditional edges, complex state management, `StateGraph` and `MessageGraph`; rich ecosystem of pre-built patterns (`create_react_agent`); `mlflow.langchain.autolog()` provides automatic tracing. **Cons:** LangGraph Platform/Cloud features (LangGraph Studio, hosted persistence) unavailable on Databricks; **statelessness constraint** on Model Serving endpoints means LangGraph's built-in persistence (`MemorySaver`, `SqliteSaver`) needs adaptation; serialization complexity for custom nodes may require falling back to `pyfunc` flavor; all LangGraph dependencies must be properly managed in the serving environment. **Maturity:** Supported and documented; `langchain-databricks` actively maintained.

### Option 3: Hybrid — LangGraph orchestration + Databricks infrastructure (recommended)

This is **the strongest approach for the PIM use case**. Use LangGraph for agent orchestration logic (graph routing, state management, tool execution flow), while leveraging Databricks for everything else:

| Layer | Technology |
|-------|-----------|
| Agent orchestration | LangGraph `StateGraph` |
| LLM access | Databricks Foundation Model APIs / AI Gateway |
| Tool definitions | Unity Catalog functions via `UCFunctionToolkit` |
| Vector search | Databricks Vector Search |
| Feature serving | Online Tables + Feature Serving endpoints |
| Model registry | Unity Catalog Model Registry |
| Deployment | Model Serving via `databricks.agents.deploy()` |
| Evaluation | Mosaic AI Agent Evaluation |
| Monitoring | Inference Tables + Lakehouse Monitoring |
| Governance | Unity Catalog ACLs, lineage, audit |

**Pros:** Best of both worlds — LangGraph's flexible orchestration with Databricks' enterprise infrastructure; full Unity Catalog governance on all tools and data; single platform for data engineering, ML, and agent lifecycle; MLflow tracking and tracing work seamlessly. **Cons:** Two framework ecosystems to manage; slightly more complex dependency management; LangGraph state persistence still requires external solution on Databricks. **Maturity:** Production-ready; this is the pattern Databricks' GenAI Cookbook promotes for complex agent use cases.

### Option 4: Agent Framework with external tools via MCP

Use the Databricks Unity Catalog MCP server to expose agent tools via the Model Context Protocol standard, enabling interoperability with any MCP-compatible client.

**Pros:** Universal tool interoperability — Unity Catalog tools accessible from Claude Desktop, Cursor, VS Code, and any MCP client; positions the PIM tools for future extensibility; aligns with the emerging open standard. **Cons:** MCP integration was released in early 2025 and is still maturing; adds a protocol layer between agents and tools; best suited for extending existing agents to external clients rather than as the primary internal orchestration mechanism. **Maturity:** Early-to-mid maturity; the Unity Catalog MCP server was released on GitHub in early 2025.

---

## C. Delta tables and Feature Store as shared agent state

### Feature Store for structured, entity-keyed features

The **Mosaic AI Feature Store** manages precomputed features as Delta tables registered in Unity Catalog with designated primary keys. The `FeatureEngineeringClient` provides APIs for creating, writing, and reading feature tables. For the PIM platform, this means product features (pricing signals, quality scores, supplier ratings) can be computed once and shared across all three agents.

Creating a feature table follows this pattern: call `fe.create_table()` with primary keys (e.g., `product_id`), optional timestamp keys for point-in-time lookups, and a source DataFrame. Updates use `fe.write_table()` with `mode="merge"` for upserts. All three PIM agents then read from the same governed table.

### Online Tables for real-time agent reads

**Online Tables** are read-optimized copies of Delta tables, automatically synced via Delta Change Data Feed, backed by a low-latency serving layer delivering **5-15ms point lookups**. They support three sync modes: `SNAPSHOT` (one-time), `TRIGGERED` (on-demand refresh), and `CONTINUOUS` (real-time CDC). For the PIM system, an Online Table on `pim.core.product_features` enables all agents to retrieve product attributes at conversation speed.

Feature Serving endpoints expose Online Tables via REST APIs. You create them using the Databricks SDK (`w.serving_endpoints.create()`) with a `FeatureSpec` that defines which features to serve and their lookup keys. Agents query these endpoints with simple HTTP POST requests containing the entity key.

### Mapping to LangGraph StateGraph

The Feature Store maps conceptually to LangGraph's `StateGraph` but at a different granularity. **LangGraph StateGraph provides intra-session, in-memory state** — immediate consistency within a single agent conversation. **Feature Store provides cross-session, cross-agent state** — eventual consistency with durable persistence. For the PIM platform, the recommended pattern combines both:

- LangGraph `StateGraph` manages conversation-level state within each agent session
- Delta tables store durable shared context (agent action logs, computed product attributes, enrichment results)
- Online Tables bridge the gap — any agent can read another agent's persisted outputs at millisecond latency

The practical implementation uses LangGraph nodes that read from Feature Serving endpoints at the start of processing, and write results back to Delta tables at the end, creating a feedback loop across agents.

### When to use Feature Store vs. raw Delta tables

Use **Feature Store** for entity-centric features that agents need at low latency — product risk scores, customer segments, real-time embeddings — where the primary key lookup pattern fits naturally. Use **raw Delta tables** for conversation logs, agent action histories, unstructured context, and append-only audit trails. The hybrid approach is recommended: Feature Store for curated, reusable features; Delta tables for everything else; Online Tables to turn any Delta table into a low-latency lookup store.

---

## D. Unity Catalog as the governance backbone

Unity Catalog provides a unified three-level namespace (`catalog.schema.object`) governing all AI assets in the PIM platform — tools, models, data, and functions.

### UC functions as a tool registry

Agent tools registered as UC functions gain **automatic governance, discoverability, and reusability**. SQL or Python functions at `catalog.schema.function_name` include typed parameters, return types, and docstrings that serve as the tool's API contract. Multiple agents reference the same function, ensuring consistency. The Mosaic AI Agent Framework automatically retrieves function definitions from UC, generates JSON schemas for LLM function-calling, executes functions when the LLM requests tool calls, and returns results — all within a secure, sandboxed serverless environment.

The `UCFunctionToolkit` (from `databricks-langchain`) converts UC functions into LangChain-compatible tools in a single call. Initialize it with a SQL warehouse ID and a list of fully qualified function names, then call `toolkit.get_tools()` to get LangChain `Tool` objects ready for use in LangGraph agents. The toolkit reads function metadata from UC, creates Pydantic schemas from parameter types, and executes functions via the SQL warehouse at invocation time. Equivalent toolkits exist for OpenAI (`unitycatalog-openai`), CrewAI (`unitycatalog-crewai`), and LlamaIndex.

### Permissions and access control

Fine-grained permissions control agent access: `USE CATALOG` and `USE SCHEMA` for namespace access, `EXECUTE` for invoking UC function tools, `SELECT` for underlying table reads. Agents deployed via Model Serving run under a **service principal**, and all tool executions respect that principal's permissions. Row-level security (row filters) and column-level security (column masks) apply even when agents access data through tools. Every permission grant and function execution is fully auditable.

### Model lineage and the UC Model Registry

The Unity Catalog Model Registry (which replaced the legacy Workspace Model Registry) manages agent models with three-level names like `catalog.pim.catalog_management_agent`. Each `log_model()` call creates a new version automatically. **Named aliases** (`@champion`, `@challenger`) replace the old staging system for deployment routing. For agents, the model artifact captures tools, configuration, and dependencies — `mlflow.models.resources` specifies dependent UC functions, vector search indexes, and serving endpoints, providing full lineage from data through training to serving.

---

## E. MLflow tracing, logging, and the ChatAgent interface

### MLflow Tracing

MLflow Tracing (introduced in MLflow 2.14, significantly enhanced through 2.17+) captures hierarchical execution traces of agent pipelines. Each trace contains a tree of **spans** representing LLM calls, tool executions, retriever lookups, and chain steps, all with inputs, outputs, timestamps, token counts, and latency.

Two instrumentation paths exist. **Automatic tracing** via `mlflow.langchain.autolog()` instruments all LangChain/LangGraph invocations without code changes — every chain step, tool call, and LLM call generates spans automatically. **Manual tracing** via the `@mlflow.trace(span_type="TOOL")` decorator or `mlflow.start_span()` context manager wraps any Python function as a span. Nested decorated functions create parent-child relationships. Traces are viewable in the MLflow experiment UI's Traces tab, showing the full execution tree.

### The ChatAgent interface

`ChatAgent` (from `mlflow.pyfunc`, introduced around MLflow 2.17-2.18) is the **recommended base class for all new agents** on Databricks. It enforces the OpenAI-compatible chat completions schema, defines `predict()` for synchronous responses and `predict_stream()` for streaming (yielding `ChatAgentChunk` objects), and natively handles `tool_calls` in assistant messages and `tool` role messages. Agents implement this class, and `mlflow.models.set_model(agent_instance)` marks the object for code-based model logging.

### Deploying agents as MLflow models

The deployment pipeline follows four steps. **Log** the agent with `mlflow.pyfunc.log_model()` (for custom agents) or `mlflow.langchain.log_model()` (for LangChain/LangGraph agents), specifying `resources` for dependent endpoints and UC functions. **Register** in Unity Catalog with `mlflow.register_model()` using a three-level name. **Deploy** via `databricks.agents.deploy(model_name, model_version)`, which automatically provisions the serving endpoint, Review App, inference tables, and feedback mechanisms. **Monitor** via inference tables and MLflow traces in production.

The Unity Catalog Model Registry is required for `databricks.agents.deploy()` and is recommended over the legacy Workspace Model Registry for all new projects. UC provides cross-workspace scope, full lineage tracking, and governance integration that the workspace registry lacks.

---

## F. Model Serving and the AI Gateway

### Deploying agents to endpoints

Model Serving endpoints host agents behind REST APIs compatible with the OpenAI chat completions format. The `databricks.agents.deploy()` function is the simplest path — pass a UC model name and version, and it handles endpoint creation, scaling configuration, inference table setup, and Review App provisioning. For more control, the Databricks SDK's `w.serving_endpoints.create()` allows explicit configuration of workload size, scale-to-zero behavior, and environment variables (supporting `{{secrets/scope/key}}` syntax for API keys).

Streaming is supported natively when the agent implements `predict_stream()`. Clients consume Server-Sent Events via `w.serving_endpoints.query_stream()` or by setting `stream=True` in the OpenAI SDK.

### Foundation Model APIs and AI Gateway

Databricks provides a **unified interface for all LLM access** through three tiers. **Pay-per-token endpoints** offer instant access to hosted models (Llama 3.x, DBRX, Mixtral) billed per token with no provisioning required — ideal for development. **Provisioned Throughput endpoints** provide dedicated compute with guaranteed tokens-per-second for production workloads, billed per DBU-hour. **External Model endpoints** proxy requests to OpenAI, Anthropic, Google, Amazon Bedrock, Cohere, and AI21 Labs through Databricks, centralizing API key management, enabling unified rate limiting, cost tracking, and governance.

All three tiers expose the same OpenAI-compatible REST API (`/chat/completions`, `/completions`, `/embeddings`). Within agents, you access them via `ChatDatabricks(endpoint="endpoint-name")` from `langchain-databricks`, or through the standard OpenAI SDK by pointing `base_url` at your workspace. The AI Gateway adds guardrails (content filtering, PII detection), usage tracking, and MLflow tracing integration across all tiers.

For the PIM platform, the recommended setup uses **external model endpoints for Claude or GPT-4o** (higher capability for complex reasoning) and **pay-per-token endpoints for Llama 3.x** (cost-effective for routine classification and routing tasks).

---

## G. MCP integration with Databricks

### Unity Catalog MCP server

Databricks released an **official Unity Catalog MCP server** in early 2025, published on GitHub. This server implements the Model Context Protocol standard (created by Anthropic) and exposes Unity Catalog resources as MCP tools. Any MCP-compatible client — Claude Desktop, Cursor, VS Code extensions, or custom applications — can discover and invoke UC functions, list catalogs/schemas/tables, read table metadata, and execute SQL queries through the server.

The architectural significance is substantial: **Unity Catalog becomes a universal, governed tool registry** accessible from any MCP client. Organizations that define PIM tools as UC functions automatically get MCP compatibility. For the PIM platform, this means external applications (e.g., a buyer's desktop AI assistant) can access procurement tools governed by UC permissions without any Databricks-specific integration code.

### MCP and the agent framework

The integration works bidirectionally. **Databricks as MCP server:** The UC MCP server exposes workspace capabilities to external clients. **Databricks agents as MCP clients:** Agents running on Databricks can potentially connect to external MCP servers to access tools beyond the Databricks ecosystem. The MCP layer extends agent capabilities beyond UC functions to any service implementing the MCP standard. As of early 2026, MCP support is functional but still maturing — expect continued improvements in authentication handling, streaming, and client-side tooling.

---

## H. Building the PIM platform: a practical implementation guide

### Step-by-step for three PIM agents from scratch

**Phase 1: Infrastructure setup.** Create a Databricks workspace (Premium or Enterprise tier). Enable Unity Catalog and create the PIM catalog structure: `pim.core` for product data tables, `pim.agents` for agent models and tools. Provision a Serverless SQL Warehouse for UC function execution. Enable Model Serving. Set up external model endpoints for your chosen LLM (Claude or GPT-4o via AI Gateway).

**Phase 2: Data foundation.** Create Delta tables in Unity Catalog — `pim.core.products`, `pim.core.categories`, `pim.core.suppliers`, `pim.core.purchase_orders`, `pim.core.enrichment_queue`. Create Online Tables on the most frequently queried tables for low-latency agent access. Set up a Vector Search index on product descriptions for similarity search.

**Phase 3: Tool development.** Register UC functions for each agent's capabilities. The Catalog Management Agent needs `search_products`, `get_product_by_id`, `update_product`, `list_categories`. The Content & Enrichment Agent needs `generate_description`, `extract_keywords`, `find_similar_products`, `update_enrichment_status`. The Procurement Agent needs `lookup_supplier`, `compare_prices`, `create_purchase_order`, `check_inventory_levels`.

**Phase 4: Agent authoring.** For each agent, define a `ChatAgent` subclass (or a LangGraph `StateGraph`) with the appropriate tools loaded via `UCFunctionToolkit`. Use `ChatDatabricks` as the LLM wrapper. The orchestrator agent routes requests to specialized agents using a classification step.

**Phase 5: Evaluation.** Create evaluation datasets for each agent — DataFrame rows with `request` and `expected_response` columns. Run `mlflow.evaluate()` with `model_type="databricks-agent"` to assess correctness, groundedness, relevance, and safety. Iterate on prompts and tool definitions until metrics meet thresholds.

**Phase 6: Deployment.** Log each agent with `mlflow.pyfunc.log_model()` or `mlflow.langchain.log_model()`, register in Unity Catalog, and deploy via `databricks.agents.deploy()`. Deploy the orchestrator last, configuring it to call the three sub-agent endpoints as tools.

### Recommended stack for starting fresh

- **Python packages:** `databricks-agents`, `mlflow>=2.17`, `langchain-databricks`, `langgraph`, `databricks-sdk`
- **Compute:** Databricks Runtime for ML 14.3+ for development; Serverless Model Serving for agent hosting; Serverless SQL Warehouse for UC function execution
- **LLM access:** External model endpoint for Claude Sonnet (primary reasoning) + pay-per-token Llama 3.1 70B (routing and classification)
- **Orchestration:** LangGraph `StateGraph` for each agent's internal logic; `ChatAgent` wrapper for MLflow compatibility
- **Governance:** Unity Catalog for all tools, models, and data; service principals for production agent deployments
- **CI/CD:** Databricks Asset Bundles (`databricks.yml`) for infrastructure-as-code deployment across dev/staging/prod

### Project structure

```
pim-agents/
├── databricks.yml                    # Asset Bundle config
├── src/agents/
│   ├── catalog_agent.py              # Catalog Management Agent (ChatAgent)
│   ├── content_agent.py              # Content & Enrichment Agent
│   ├── procurement_agent.py          # Procurement/Buying Agent
│   └── orchestrator.py               # Router/supervisor agent
├── src/tools/
│   ├── catalog_tools.sql             # UC function definitions
│   ├── content_tools.sql
│   └── procurement_tools.sql
├── notebooks/
│   ├── 00_setup_infrastructure.py
│   ├── 01_create_tools.py
│   ├── 02_develop_agents.py
│   ├── 03_evaluate_agents.py
│   └── 04_deploy_agents.py
├── tests/eval_datasets/
│   ├── catalog_eval.csv
│   ├── content_eval.csv
│   └── procurement_eval.csv
└── config/agent_config.yml
```

### Key documentation and resources

| Resource | URL |
|----------|-----|
| Mosaic AI Agent Framework | `docs.databricks.com/en/generative-ai/agent-framework/index.html` |
| Agent Evaluation | `docs.databricks.com/en/generative-ai/agent-evaluation/index.html` |
| Deploy agents | `docs.databricks.com/en/generative-ai/agent-framework/deploy-agent.html` |
| Agent tools (UC functions) | `docs.databricks.com/en/generative-ai/agent-framework/create-agent-tools.html` |
| Foundation Model APIs | `docs.databricks.com/en/machine-learning/foundation-models/index.html` |
| External models (AI Gateway) | `docs.databricks.com/en/generative-ai/external-models/index.html` |
| MLflow Tracing | `docs.databricks.com/en/mlflow/mlflow-tracing.html` |
| Feature Store | `docs.databricks.com/en/machine-learning/feature-store/index.html` |
| Online Tables | `docs.databricks.com/en/machine-learning/feature-store/online-tables.html` |
| Unity Catalog | `docs.databricks.com/en/data-governance/unity-catalog/index.html` |
| GenAI Cookbook (GitHub) | `github.com/databricks/genai-cookbook` |
| `databricks-agents` (PyPI) | `pypi.org/project/databricks-agents/` |
| `langchain-databricks` (PyPI) | `pypi.org/project/langchain-databricks/` |
| Unity Catalog AI (GitHub) | `github.com/unitycatalog/unitycatalog` |

---

## Conclusion

The Databricks ecosystem for multi-agent AI systems is mature enough for production PIM deployments in 2025-2026, but the choice of architecture matters significantly. **The hybrid approach — LangGraph for orchestration, Databricks for infrastructure — delivers the strongest combination** of flexible agent logic and enterprise-grade governance. The key insight many teams miss is that Mosaic AI Agent Framework and LangGraph are not competitors; they operate at different layers and combine naturally through the `ChatAgent`/MLflow bridge.

Three factors particularly favor Databricks for this PIM use case. First, **Unity Catalog as a unified tool registry** means all three agents share governed tools with audit trails and access control — critical for a system where the Procurement Agent writes purchase orders. Second, **Online Tables solve the shared state problem** without building custom infrastructure — product features computed by the Content Agent are available to the Catalog Agent at millisecond latency. Third, **the AI Gateway normalizes LLM access** across providers, letting you use Claude for complex reasoning and Llama for cost-effective routing through a single API pattern.

The main gap to watch is MCP maturity. The Unity Catalog MCP server is functional but still evolving. For the initial PIM build, focus on the native UC function pattern and treat MCP as a future extensibility option for integrating external clients. Start with the GenAI Cookbook examples on GitHub, adapt the `create_react_agent` pattern with `UCFunctionToolkit` for each specialized agent, and deploy through `databricks.agents.deploy()` for the fastest path to production.