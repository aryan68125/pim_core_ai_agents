# agents/product_description_generator — Product Description Generator Agent

FastAPI microservice (port 8002) that generates SEO-optimised product descriptions.

## Entry point

`main.py` — mounts all routers and exposes the FastAPI `app`.

## Request flow

```
POST /agents/generate-description       ← accepts a raw PIM export record
  → pim_record_to_product() (pim_core/adapters/pim_adapter.py)
    → generate_description tool (tools/generate_description.py)
      → LangGraph StateGraph (workflows/description_workflow.py)
        → agent_model_registry.get("product_description_generator") → resolve current model
          → llm_client.complete(model=...) → provider → LLM API
```

## Routes

| Route | File | Purpose |
|-------|------|---------|
| `POST /agents/generate-description` | `routes/product_description_generator_api_route.py` | Accepts a raw PIM record, adapts it, then generates |
| `GET  /models/available` | `routes/agent_registry.py` | List all supported models by provider |
| `POST /agents-settings/{name}/model` | `routes/agent_registry.py` | Assign any model to any agent by name |
| `GET  /agents-settings/models` | `routes/agent_registry.py` | View all agent → model assignments + default |
| `DELETE /agents-settings/{name}/model` | `routes/agent_registry.py` | Reset an agent to the default model |

## Agent name

This agent is registered in `AgentModelRegistry` under the key `"product_description_generator"`.
