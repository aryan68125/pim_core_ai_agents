# tests — Test Suite

pytest suite mirroring the source tree. All async tests run automatically (asyncio_mode=auto in pytest.ini).

## Structure

| Path | Covers |
|------|--------|
| `conftest.py` | Shared fixtures: `sample_product`, `sample_brand_voice`; sets `ANTHROPIC_API_KEY` env var |
| `test_config.py` | `pim_core/config.py` |
| `test_schemas.py` | `pim_core/schemas/product.py` |
| `test_pim_adapter.py` | `pim_core/adapters/pim_adapter.py` |
| `test_llm_client.py` | `pim_core/llm/client.py` |
| `test_llm_factory.py` | `pim_core/llm/factory.py` |
| `test_llm_registry.py` | `pim_core/llm/registry.py` |
| `product_description_generator/test_brand_voice.py` | `agents/product_description_generator/prompts/brand_voice.py` |
| `product_description_generator/test_description_workflow.py` | `agents/product_description_generator/workflows/description_workflow.py` |
| `product_description_generator/test_generate_description_tool.py` | `agents/product_description_generator/tools/generate_description.py` |
| `product_description_generator/test_agent_registry.py` | `agents/product_description_generator/routes/agent_registry.py` |
| `product_description_generator/test_product_description_generator_api_route.py` | `agents/product_description_generator/routes/product_description_generator_api_route.py` |
| `product_description_generator/test_main.py` | `agents/product_description_generator/main.py` (integration) |

## Running

```bash
# Full suite
venv/bin/python -m pytest tests/ -v

# Single file
venv/bin/python -m pytest tests/product_description_generator/test_description_workflow.py -v
```

## LLM calls

All LLM calls are mocked. Tests never hit real APIs.
The mock path is always: `agents.product_description_generator.workflows.description_workflow.llm_client.complete`

## Database isolation

Agent registry tests patch `pim_core.db.agent_model_db.upsert` and `.delete` so they never
write to the real `agent_models.db`. Running pytest does not alter any manually-set
agent → model assignments.
