# PIM-AI — Agent Development Task List

**Version:** 1.0 | **Audience:** Engineering / Development Team | **Date:** April 2026  
**Integration:** REST API · Direct DB · MCP Tools

---

## Shared Foundation — Required by All Three Agents

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| F-01 | LLM platform evaluation & selection | Benchmark Claude, GPT-4o, Gemini, and open-source models (Llama 3, Mistral). Define selection criteria: tool-calling capability, context window, cost, latency. | AI | High |
| F-02 | Agent orchestration framework setup | Select and configure orchestration layer — LangChain, LlamaIndex, Autogen, or custom. Define agent loop: perceive → plan → act → observe. Set up memory (short-term context + long-term state store). | AI | High |
| F-03 | Tool / function calling schema design | Define standard JSON schema for all agent tools across three agents. Includes input/output contracts, error formats, and retry logic. Shared across REST API, DB, and MCP tool calls. | Backend | High |
| F-04 | MCP server setup & tool registration | Stand up MCP server layer. Register tools for catalog read/write, pricing query, inventory check, and order actions. Expose tool manifest for agent discovery. Define permission scopes per agent type. | Infra | High |
| F-05 | Authentication & agent identity management | Implement service account model for agents (OAuth 2.0 / API keys). Define per-agent permission scopes. Audit log all agent actions with identity, timestamp, and payload. | Infra | High |
| F-06 | Agent action audit & logging service | Build centralised logging service recording every agent decision, tool call, and outcome. Required for debugging, compliance, and HITL review. Store in append-only log. | Backend | High |
| F-07 | Human-in-the-loop (HITL) escalation framework | Define confidence thresholds below which agents must escalate to a human. Build notification + approval UI. Agents pause and await approval before executing irreversible actions. | Frontend | High |
| F-08 | Shared vector database / semantic search layer | Set up vector DB (Pinecone, Weaviate, or pgvector) for semantic product search across all agents. Embed product catalog, descriptions, and attributes. | Infra | Medium |
| F-09 | Agent testing & evaluation harness | Build automated test suite: unit tests per tool, integration tests per workflow, and LLM eval framework (e.g. LangSmith, RAGAS) for response quality. Include regression tests for prompt changes. | AI | Medium |

---

## Agent 1 — Catalog Management Agent

**Summary:** 16 total tasks | 7 High | 6 Medium | 3 Low

**Purpose:** Autonomously manages product records, classifications, tags, image sequencing, and data quality across the catalog. Acts on behalf of catalog managers and merchandisers.

### Data Access & API Layer

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| C-01 | Product catalog read API (REST) | Build REST endpoints for agent to query products by ID, SKU, category, and attribute filters. Return structured JSON with full attribute schema. Support pagination and bulk fetch. | Backend | High |
| C-02 | Product catalog write API (REST) | Build REST endpoints for agent to create, update, and patch product records. Support partial updates (PATCH). Validate schema on write. Emit change events to downstream systems. | Backend | High |
| C-03 | Direct DB read access layer | Create read-only DB views and stored procedures for agent bulk queries — category stats, data completeness scores, missing attribute reports. Use read replica. | Backend | High |

### Agent Tools (MCP / Function Calls)

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| C-04 | Tool: `classify_product` | Takes product attributes + description, returns correct category path (GS1 / eCl@ss / custom). Returns confidence score and top-3 candidates. | AI | High |
| C-05 | Tool: `tag_product` | Analyses product image URL + description, returns suggested attribute tags mapped to schema with confidence scores. Supports batch mode. | AI | High |
| C-06 | Tool: `sequence_images` | Takes product ID + list of image URLs, identifies image types (hero/lifestyle/detail), returns correctly ordered sequence based on category ruleset. Supports marketplace-specific rules. | AI | High |
| C-07 | Tool: `check_data_quality` | Scans a product record or category, returns data completeness score, list of missing required fields, and recommended actions. | Backend | High |
| C-08 | Tool: `bulk_update_products` | Applies updates to multiple products simultaneously. Requires HITL approval above configurable threshold. Returns job ID for async tracking. | Backend | Medium |

### Agent Behaviour & Workflows

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| C-09 | System prompt & persona design | Design catalog agent's system prompt: role, task scope, tone, escalation rules, and constraints (never delete records without approval). Include few-shot examples. | AI | High |
| C-10 | Autonomous data quality patrol workflow | Scheduled agent workflow scanning catalog for data gaps, triggering enrichment or tagging tools, surfacing a daily summary report. | AI | Medium |
| C-11 | New product onboarding workflow | Agent workflow triggered on new product ingestion. Runs: classify → tag → generate description → sequence images → check quality. | AI | Medium |
| C-12 | Conflict detection & resolution logic | Handle cases where agent-suggested classification or tags conflict with existing human-assigned values. Define resolution policy based on confidence threshold. | Backend | Medium |

### UI & Monitoring

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| C-13 | Catalog agent dashboard | UI showing agent activity: tasks completed, products processed, quality scores improved, pending approvals, and error log. | Frontend | Medium |
| C-14 | Agent conversational interface | Chat UI for catalog managers to instruct the agent in natural language (e.g. "Re-classify all Outdoor category products"). | Frontend | Medium |
| C-15 | Change history & rollback | Every agent write action creates a versioned record. UI allows viewing before/after and rolling back changes at product or batch level. | Backend | Low |
| C-16 | Agent performance metrics & reporting | Track KPIs: classification accuracy rate, tagging precision, data quality score delta, average time to onboard a product. | Frontend | Low |

---

## Agent 2 — Procurement / Buying Agent

**Summary:** 17 total tasks | 8 High | 6 Medium | 3 Low

**Purpose:** Autonomously handles catalog queries, product selection, pricing decisions, inventory checks, and purchase order creation on behalf of business procurement teams.

### Data Access & API Layer

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| P-01 | Catalog query API for agents | REST API for structured product search by spec, category, price range, and availability. Optimised for agent consumption — returns ranked results with match scores. | Backend | High |
| P-02 | Real-time pricing API | Endpoint returning current pricing, discount tiers, contract pricing per buyer, and promotional pricing. | Backend | High |
| P-03 | Inventory & availability API | Real-time stock levels, lead times, and warehouse locations per SKU. Triggers substitution logic when stock is insufficient. | Backend | High |
| P-04 | Purchase order creation API | REST endpoint for agent to raise, update, and submit purchase orders. Validates against procurement rules. Returns PO number and status. | Backend | High |

### Agent Tools (MCP / Function Calls)

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| P-05 | Tool: `search_catalog` | Accepts natural language or structured query, returns ranked product matches with full spec comparison. Underpinned by vector search + filter layer. | AI | High |
| P-06 | Tool: `compare_products` | Takes 2–N product IDs, returns structured comparison across selected attributes (price, spec, availability, lead time). | AI | High |
| P-07 | Tool: `check_procurement_rules` | Validates a proposed product selection against procurement policy: approved supplier list, budget thresholds, category restrictions, approval matrix. Returns pass/fail with reason. | Backend | High |
| P-08 | Tool: `raise_purchase_order` | Compiles and submits a PO: supplier, line items, quantities, delivery address, cost centre. Triggers approval workflow if above threshold. | Integration | High |
| P-09 | Tool: `find_substitutes` | When a product is out of stock or discontinued, finds equivalent alternatives by spec similarity. Ranks by price, availability, and compliance. | AI | Medium |

### Agent Behaviour & Workflows

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| P-10 | System prompt & procurement rules encoding | Design procurement agent system prompt: role, decision authority, escalation rules, procurement policy. Constraints: cannot exceed budget without approval, must prefer approved suppliers, must log all decisions. | AI | High |
| P-11 | Autonomous reorder workflow | Scheduled agent workflow monitoring inventory. When stock falls below reorder threshold, finds best-value restock, validates rules, raises PO automatically within pre-approved limits. | AI | Medium |
| P-12 | Procurement request intake workflow | Agent accepts requests in natural language (e.g. "I need 200 units of industrial gloves, medium, by end of month, under £8/unit"). Translates to structured search, finds options, presents recommendation. | AI | Medium |
| P-13 | ERP / procurement system integration | Integrate agent PO output with existing ERP (SAP, Oracle, MS Dynamics) or procurement platforms (Coupa, Jaggaer). Support webhook and API push. | Integration | Medium |

### UI & Monitoring

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| P-14 | Procurement agent conversational interface | Chat-based UI for procurement users to interact with the agent. Users describe needs; agent searches, compares, and recommends. One-click approval to raise PO. | Frontend | Medium |
| P-15 | Approval & escalation UI | Procurement managers review agent-raised POs above threshold. UI shows agent reasoning, product comparison, and procurement rule check result. | Frontend | Medium |
| P-16 | Spend analytics dashboard | Visualise agent-driven procurement activity: spend by category, supplier, cost centre, and time period. Track savings identified. | Frontend | Low |
| P-17 | Agent decision explainability log | Every product recommendation and PO raised includes structured rationale: why this product, what alternatives were considered, which rules were applied. | Backend | Low |

---

## Agent 3 — Content & Enrichment Agent

**Summary:** 15 total tasks | 7 High | 5 Medium | 3 Low

**Purpose:** Autonomously generates product descriptions, extracts data from labels and packaging, and enriches sparse product records — acting on behalf of content, marketing, and catalog teams.

### Data Access & API Layer

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| E-01 | Product read/write API for content agent | REST API for agent to read product records (attributes, existing descriptions, images) and write generated content back. Supports field-level writes. | Backend | High |
| E-02 | External data sources integration | Build connectors to public enrichment sources: Open Food Facts, GS1 registry, manufacturer websites, and open product databases. Includes rate limiting, caching, and source attribution. | Integration | High |
| E-03 | Image ingestion & processing pipeline | Pipeline to accept product images (URL or upload), run quality assessment, pass to enhancement model, and store enhanced versions. | Infra | High |

### Agent Tools (MCP / Function Calls)

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| E-04 | Tool: `generate_description` | Takes product attributes, category, and target channel. Returns SEO-optimised title and description. Supports tone/style config per brand. Includes keyword injection from category SEO rules. | AI | High |
| E-05 | Tool: `extract_label_data` | Accepts product image URL. Runs OCR + AI extraction to return structured data: ingredients, nutritional values, allergens, certifications, and claims with confidence scores. | AI | High |
| E-06 | Tool: `enrich_product` | Takes product ID, identifies missing required fields, queries external sources and LLM knowledge, returns enrichment suggestions with source attribution. | AI | High |
| E-07 | Tool: `enhance_image` | Accepts image URL, returns enhanced version URL. Applies sharpening, background removal, and colour correction. Supports batch processing. Returns before/after metadata. | AI | High |
| E-08 | Tool: `translate_content` | Translates generated descriptions and extracted data into target languages. Maintains technical accuracy for spec fields. Supports brand tone guidelines per locale. | AI | Medium |

### Agent Behaviour & Workflows

| ID | Task | Description | Type | Priority |
|----|------|-------------|------|----------|
| E-09 | System prompt & brand voice design | Design content agent system prompt: role, content quality standards, SEO rules, brand voice constraints, and escalation criteria. Include few-shot examples of good vs. poor descriptions per category. | AI | High |
| E-10 | New supplier onboarding workflow | Agent workflow triggered when new supplier products are ingested: reads label images → extracts data → fills gaps via enrichment → generates descriptions → enhances images → outputs publish-ready records. | AI | Medium |

---

## Task Type Legend

| Type | Colour | Meaning |
|------|--------|---------|
| Backend | Blue | Server-side API / data layer |
| Frontend | Yellow | UI / dashboard |
| AI / LLM | Purple | Prompt, model, agent logic |
| Infrastructure | Green | DevOps, databases, queues |
| Integration | Pink | External system connectors |

## Priority Legend

| Priority | Meaning |
|----------|---------|
| High | Must be done first — blocks other tasks |
| Medium | Important but not blocking |
| Low | Nice to have / analytics |
