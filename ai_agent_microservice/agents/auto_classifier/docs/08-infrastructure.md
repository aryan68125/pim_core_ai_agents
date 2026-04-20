# Feature 08 — Infrastructure

The service runs entirely in Docker Compose locally. No Kubernetes, no cloud infra required for development.

---

## Services

```
docker-compose.yml
  ├── app       — FastAPI service (built from Dockerfile)
  ├── postgres  — pgvector/pgvector:pg16
  └── redis     — redis:7-alpine
```

---

## Running Locally

```bash
# 1. Clone and enter the directory
cd classification-service

# 2. Copy env file and fill in your API keys
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY or whichever LLM you use

# 3. Start postgres + redis
docker compose up -d postgres redis

# 4. Create a Python venv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 5. Run database migrations
alembic upgrade head

# 6. Load taxonomy data (requires GS1 file or URL in .env)
python -m classifier.taxonomy.loader gs1

# 7. Start the app
uvicorn classifier.main:app --reload --port 8000

# Or start everything including the app in Docker
docker compose up --build
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

| var | required | default | description |
|---|---|---|---|
| `DATABASE_URL` | yes | `postgresql+asyncpg://classifier:classifier@localhost:5432/classifier` | Postgres connection string (asyncpg driver) |
| `REDIS_URL` | yes | `redis://localhost:6379` | Redis connection string |
| `CACHE_TTL_SECONDS` | no | `86400` | Result cache TTL in seconds |
| `LLM_TIER2_PROVIDER` | yes | `anthropic` | LLM provider: `anthropic` \| `openai` \| `gemini` \| `ollama` |
| `LLM_TIER2_MODEL` | yes | `claude-sonnet-4-6` | Model name for the chosen provider |
| `ANTHROPIC_API_KEY` | if using Anthropic | — | Anthropic API key |
| `OPENAI_API_KEY` | if using OpenAI or embeddings | — | OpenAI API key (also used for embedding) |
| `GOOGLE_API_KEY` | if using Gemini | — | Google AI API key |
| `EMBEDDING_MODEL` | no | `text-embedding-3-small` | OpenAI embedding model name |
| `CONFIDENCE_EMBEDDING_THRESHOLD` | no | `0.92` | Skip LLM if top embedding score ≥ this |
| `CONFIDENCE_HITL_THRESHOLD` | no | `0.75` | Flag for human review if confidence < this |
| `JWT_SECRET` | yes | `change-me-in-production` | JWT signing secret — use a long random string in prod |
| `JWT_ALGORITHM` | no | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | no | `60` | Token expiry in minutes |
| `GS1_GPC_URL` | for GS1 loading | — | URL or local file path to GS1 GPC ZIP/XML |
| `ECLASS_DOWNLOAD_URL` | for eCl@ss loading | — | eCl@ss XML download URL |
| `ECLASS_DOWNLOAD_USER` | if eCl@ss needs auth | — | eCl@ss username |
| `ECLASS_DOWNLOAD_PASS` | if eCl@ss needs auth | — | eCl@ss password |
| `LOG_LEVEL` | no | `INFO` | Logging level: `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |

---

## Port Mapping

The local dev environment uses non-standard ports to avoid conflicts with other projects:

| service | container port | host port |
|---|---|---|
| app | 8000 | 8000 |
| postgres | 5432 | 5435 |
| redis | 6379 | 6380 |

Connection strings for local development (outside Docker):
```bash
DATABASE_URL=postgresql+asyncpg://classifier:classifier@localhost:5435/classifier
REDIS_URL=redis://localhost:6380
```

Inside Docker Compose, services talk to each other using service names:
```bash
DATABASE_URL=postgresql+asyncpg://classifier:classifier@postgres:5432/classifier
REDIS_URL=redis://redis:6379
```

---

## Docker Details

**`Dockerfile`** — multi-stage build is not used at MVP; single-stage:
1. `python:3.12-slim` base
2. `COPY pyproject.toml` + `COPY src/`
3. `pip install .` (non-editable, no dev extras)
4. Runs as `USER nobody`
5. `CMD uvicorn classifier.main:app --host 0.0.0.0 --port 8000`

The `.env` file is **not copied** into the image. It is passed at runtime via `env_file: .env` in `docker-compose.yml`.

---

## Healthchecks

Postgres:
```yaml
test: ["CMD-SHELL", "pg_isready -U classifier -d classifier"]
interval: 5s
timeout: 5s
retries: 5
```

Redis:
```yaml
test: ["CMD", "redis-cli", "ping"]
interval: 5s
timeout: 5s
retries: 5
```

The `app` service depends on both `postgres` and `redis` with `condition: service_healthy` — the app won't start until both are ready.

---

## Running Tests

```bash
source .venv/bin/activate

# Unit tests only (no DB/Redis needed)
pytest src/classifier/tests/unit/

# Integration tests (requires running postgres + redis)
TEST_DB_URL=postgresql+asyncpg://classifier:classifier@localhost:5435/classifier \
TEST_REDIS_URL=redis://localhost:6380/1 \
pytest src/classifier/tests/integration/

# All tests
pytest
```

---

## taxonomy_data/ Directory

The `taxonomy_data/` directory is mounted into the Docker container at `/app/taxonomy_data/`:

```
taxonomy_data/
├── gpc_release_i2-2024.zip    ← GS1 GPC (download manually)
├── eclass_12_0_basic.xml      ← eCl@ss (download from eclass.eu)
└── custom.yaml                ← Custom taxonomy (you maintain this)
```

This directory is in `.gitignore` — taxonomy files are not committed to the repo.
