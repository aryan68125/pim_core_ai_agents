# Feature 04 — Auth and Security

The service uses **JWT service account tokens**. There are no user accounts — callers are services (e.g. a PIM backend) that hold a long-lived token with a fixed set of scopes.

---

## How It Works

1. An admin creates a `ServiceAccount` row in the DB (name, hashed secret, scopes)
2. A JWT is issued for that account via `create_token()`
3. The caller includes the token in every request: `Authorization: Bearer <token>`
4. The `require_scope(scope)` FastAPI dependency validates the token and checks the scope

---

## JWT Structure

**File:** `src/classifier/core/auth/jwt.py`

Tokens are HS256-signed with `JWT_SECRET`. Payload:

```json
{
  "sub": "12",
  "name": "pim-backend",
  "scopes": ["classify:write", "taxonomy:read"],
  "exp": 1745000000
}
```

| claim | description |
|---|---|
| `sub` | ServiceAccount `id` (integer as string) |
| `name` | Human-readable account name |
| `scopes` | List of permission strings |
| `exp` | Unix timestamp expiry (configurable via `JWT_EXPIRE_MINUTES`) |

---

## Scopes

| scope | endpoints |
|---|---|
| `classify:write` | `POST /classify`, `POST /corrections` |
| `taxonomy:read` | `GET /taxonomy`, `GET /taxonomy/{id}` |

A single token can hold multiple scopes. Add more scopes to the list to grant broader access.

---

## Creating a Token (manual, for dev)

```python
from classifier.core.auth.jwt import create_token

token = create_token(
    account_id="1",
    name="dev-token",
    scopes=["classify:write", "taxonomy:read"],
)
print(token)
```

Use this token in requests:

```bash
curl -X POST http://localhost:8000/classify \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"product_text": "M6 hex bolt", "taxonomy_type": "gs1"}'
```

---

## Environment Variables

| var | description |
|---|---|
| `JWT_SECRET` | Signing secret — change from default in production |
| `JWT_ALGORITHM` | Default `HS256` |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes, default `60` |

---

## Security Notes

- `JWT_SECRET` must be a strong random string in production (e.g. `openssl rand -hex 32`)
- Tokens are stateless — revocation requires secret rotation or a denylist (not yet implemented)
- The service runs as `USER nobody` in Docker — no root privileges
- API keys for LLM providers are never returned in any API response
- `.env` is excluded from Docker image build (only passed via `--env-file` at runtime)
