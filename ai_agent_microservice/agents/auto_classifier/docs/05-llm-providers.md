# Feature 05 — LLM Providers

The service is provider-agnostic. Switching between Anthropic, OpenAI, Gemini, and Ollama requires only a `.env` change — no code changes.

---

## How the Abstraction Works

**Files:**
- `src/classifier/core/llm/provider.py` — `LLMProvider` ABC
- `src/classifier/core/llm/factory.py` — `LLMFactory.get(tier)`
- `src/classifier/core/llm/anthropic.py` — AnthropicProvider
- `src/classifier/core/llm/openai.py` — OpenAIProvider
- `src/classifier/core/llm/gemini.py` — GeminiProvider
- `src/classifier/core/llm/ollama.py` — OllamaProvider

```
pipeline/llm_classify.py
         │
         │  LLMFactory.get("tier2")
         ▼
    LLMFactory
         │
         │  reads LLM_TIER2_PROVIDER from .env
         ▼
 ┌───────────────────────────────────────┐
 │  "anthropic"  →  AnthropicProvider   │
 │  "openai"     →  OpenAIProvider      │
 │  "gemini"     →  GeminiProvider      │
 │  "ollama"     →  OllamaProvider      │
 └───────────────────────────────────────┘
         │
         │  provider.classify(prompt) → str
         ▼
    JSON response parsed by llm_classify.py
```

All providers implement the same interface:
```python
class LLMProvider(ABC):
    async def classify(self, prompt: str) -> str: ...
    @property
    def model_name(self) -> str: ...
```

---

## Switching Providers

Edit `.env`:

```bash
# Use Anthropic (default)
LLM_TIER2_PROVIDER=anthropic
LLM_TIER2_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...

# Use OpenAI
LLM_TIER2_PROVIDER=openai
LLM_TIER2_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Use Gemini
LLM_TIER2_PROVIDER=gemini
LLM_TIER2_MODEL=gemini-1.5-pro
GOOGLE_API_KEY=AIza...

# Use Ollama (local, no API key)
LLM_TIER2_PROVIDER=ollama
LLM_TIER2_MODEL=llama3
```

Restart the service after changing `.env`. The factory reads config at call time.

---

## Provider Details

### Anthropic (`anthropic.py`)

Uses `anthropic.AsyncAnthropic`. Calls the Messages API. The prompt is sent as a single `user` message. Response is `content[0].text`.

Best models: `claude-sonnet-4-6`, `claude-opus-4-7`

### OpenAI (`openai.py`)

Uses `openai.AsyncOpenAI`. Calls Chat Completions with `response_format={"type": "json_object"}` — forces the model to return valid JSON directly.

Best models: `gpt-4o`, `gpt-4o-mini`

### Gemini (`gemini.py`)

Uses `google.generativeai.GenerativeModel.generate_content_async()`. The API key is configured globally via `genai.configure()`.

Best models: `gemini-1.5-pro`, `gemini-2.0-flash`

### Ollama (`ollama.py`)

Uses `openai.AsyncOpenAI` pointed at `http://localhost:11434/v1` — Ollama exposes an OpenAI-compatible endpoint. No API key required.

Requires Ollama to be running locally: `ollama serve` and `ollama pull llama3`.

Good models for classification: `llama3`, `mistral`, `phi3`

---

## Prompt Design

**File:** `src/classifier/pipeline/llm_classify.py`

The LLM receives:
1. A system prompt describing the task
2. The product description
3. The embedding-ranked candidates with their codes, names, breadcrumbs, and embedding scores

It must respond **only** with this JSON:
```json
{
  "code": "<taxonomy_code>",
  "name": "<taxonomy_name>",
  "confidence": 0.88,
  "reasoning": "<brief explanation>"
}
```

Or if no candidate matches:
```json
{
  "code": null,
  "name": null,
  "confidence": 0.0,
  "reasoning": "<why none match>"
}
```

The service parses the raw string response as JSON. Invalid JSON is handled gracefully — it returns `confidence: 0.0` and triggers human review.

---

## Adding a New Provider

1. Create `src/classifier/core/llm/myprovider.py` implementing `LLMProvider`
2. Add the new name to `LLMProviderName` enum in `config.py`
3. Add a branch in `LLMFactory.get()` in `factory.py`
4. Set `LLM_TIER2_PROVIDER=myprovider` in `.env`
