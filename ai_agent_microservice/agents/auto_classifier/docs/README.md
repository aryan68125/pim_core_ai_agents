# Classification Service — Docs

| Doc | What it covers |
|-----|----------------|
| [01-taxonomy-loading.md](01-taxonomy-loading.md) | How GS1, eCl@ss, and custom taxonomy data is fetched, embedded, and stored |
| [02-classification-pipeline.md](02-classification-pipeline.md) | The 3-stage classify pipeline: cache → embedding → LLM |
| [03-api-endpoints.md](03-api-endpoints.md) | All HTTP endpoints, request/response shapes, auth |
| [04-auth-and-security.md](04-auth-and-security.md) | JWT service account auth, scopes, token lifecycle |
| [05-llm-providers.md](05-llm-providers.md) | Provider-agnostic LLM layer — switching between Anthropic, OpenAI, Gemini, Ollama |
| [06-caching-and-audit.md](06-caching-and-audit.md) | Redis result cache and append-only audit log |
| [07-database-schema.md](07-database-schema.md) | All 6 tables, their columns, relationships, and indexes |
| [08-infrastructure.md](08-infrastructure.md) | Docker Compose setup, environment variables, running locally |
| [FLOW.md](FLOW.md) | End-to-end internal flow — input request to classified output |
