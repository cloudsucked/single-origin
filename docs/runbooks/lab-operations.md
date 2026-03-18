# Lab Operations Runbook

## Startup

1. Start backend:

```bash
./scripts/start-backend.sh
```

2. Start frontend:

```bash
./scripts/start-frontend.sh
```

3. Verify service status:

```bash
./scripts/status.sh
```

4. Run smoke test:

```bash
./scripts/smoke-test.sh
```

## Common Recovery Paths

- **Backend import/runtime issue**: restart backend and check terminal traceback.
- **Frontend route errors**: run `npm run check` in `frontend/`.
- **Broken learner state/data drift**: run `./scripts/reset-lab.sh`.
- **Need event volume quickly**: run `./scripts/generate-traffic.py`.

## Turnstile Notes

- `ENFORCE_TURNSTILE=false` allows learners to implement validation during the lab.
- `ENFORCE_TURNSTILE=true` enforces token checks for `/login`, `/register`, and `/contact/submit`.
- Backend expects `TURNSTILE_SECRET_KEY` and optionally `TURNSTILE_EXPECTED_HOSTNAME`.

## Seed Credential Logs

- If any `SEED_*_PASSWORD` variable is unset, backend startup logs a warning similar to:

```text
Seed passwords not configured for SEED_DEMO_PASSWORD, SEED_WHOLESALE_PASSWORD, SEED_ADMIN_PASSWORD, SEED_TEST_USERS_PASSWORD. Random passwords will be generated and only password hashes are stored.
```

## Verification Checklist

- `GET /health` returns healthy.
- `GET /api/v1/products` returns seeded catalog.
- `POST /graphql` returns product data.
- Login/register/contact forms render with Turnstile widget placeholders.

## OpenAPI Maintenance

- Runtime schema endpoint: `http://localhost:8000/openapi.json`
- Runtime docs endpoint: `http://localhost:8000/api-docs`

Regenerate the committed artifact after route/schema changes:

```bash
.venv/bin/python scripts/export-openapi.py
```

Check for spec drift:

```bash
.venv/bin/python scripts/export-openapi.py --check
```

## Complexity Score Verification

The app emits `X-SO-Complexity-Score` on query-heavy endpoints used for complexity-based rate limiting.

Quick checks:

```bash
curl -si "http://localhost:8000/api/v1/search?q=coffee" | grep -i x-so-complexity-score
curl -si "http://localhost:8000/api/v1/search?q=coffee%20OR%20espresso%20UNION%20SELECT%20password%20FROM%20users--" | grep -i x-so-complexity-score
curl -si -X POST "http://localhost:8000/api/v1/ai/chat" -H "content-type: application/json" -d '{"model":"brew-assistant-v1","messages":[{"role":"user","content":"Light fruity coffee?"}]}' | grep -i x-so-complexity-score
curl -si -X POST "http://localhost:8000/graphql" -H "content-type: application/json" -d '{"query":"query { products { id name } }"}' | grep -i x-so-complexity-score
```

Expected behavior:

- Header is present for `/api/v1/search`, `/api/v1/ai/chat`, `/api/v1/ai/recommend`, and `/graphql`.
- Score value is an integer between `1` and `100`.
- More complex inputs should return higher scores than simple requests.
