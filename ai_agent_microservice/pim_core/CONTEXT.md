# pim_core — Shared Infrastructure

Shared code used by all agents. Nothing in here is specific to any one agent.

## Modules

| Module | Purpose |
|--------|---------|
| `config.py` | pydantic-settings `Settings` singleton — reads env vars |
| `llm/` | Provider-agnostic LLM abstraction layer |
| `schemas/product.py` | `Product`, `ProductAttributes`, `BrandVoice`, `DescriptionResult` — normalised data contracts |
| `schemas/pim_product.py` | `PIMProductRecord` — 13 fields selected for description generation. `extra = "ignore"` silently drops any additional keys in the raw payload |
| `adapters/pim_adapter.py` | `pim_record_to_product()` — maps a raw `PIMProductRecord` to the normalised `Product` schema. Picks the most informative non-redundant description from `copy1`, `productDescription`, `posDescription` in that priority order |
| `utils/all_available_models.py` | `AllAvailableModelsAnthropic`, `AllAvailableModelsOpenAI`, `AllAvailableModelsGoogle` — enums that are the single source of truth for every supported model name. `factory.py` and `agent_registry.py` derive their logic from these |
| `utils/all_agents.py` | `AllAgents` — enum of every registered agent. **Register a new agent here first** before writing any agent code. Used everywhere instead of bare string literals |
| `db/agent_model_db.py` | SQLite persistence — `load_all()`, `upsert()`, `delete()` for agent→model assignments. The registry loads from here on startup; writes go here immediately |

## PIMProductRecord accepted fields

| Field | Type | Maps to |
|-------|------|---------|
| `productID` | `int` | `Product.id` |
| `productName` | `str` | `Product.name` |
| `coordGroupDescription` | `str` | `Product.category` |
| `ipManufacturer` | `str` | `Product.attributes.brand` |
| `copy1` | `str` | `existing_description` (1st priority) |
| `productDescription` | `str` | `existing_description` (2nd priority) |
| `posDescription` | `str` | `existing_description` (3rd priority) |
| `warranty` | `str` | `additional["warranty"]` |
| `vendorStyle` | `str` | `additional["vendor_part_number"]` |
| `webManufacturer` | `str` | `additional["web_manufacturer"]` |
| `suggestedWebcategory` | `str` | `additional["web_category"]` |
| `productType` | `str` | `additional["product_type"]` |
| `categorySpecificAttributes` | `list` | `additional["category_attributes"]` (JSON-serialised, only when non-empty) |

## Key rule

Never import from `agents/` here. This package is consumed by agents, not the other way around.
