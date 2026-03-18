# Single Origin

This repository contains the implementation workspace for the Single Origin AppSec lab origin server.

## MVP Scaffold Status

Phases 0-6 are scaffolded with an end-to-end lab baseline:

- `frontend/` SvelteKit app with core route surfaces and editable Turnstile form templates.
- `backend/` FastAPI app with seeded SQLite data, broad API surface, GraphQL endpoint, and Turnstile Siteverify helper.
- `scripts/` VM-friendly helper scripts to run frontend and backend with hot reload.
- `infra/` optional Docker Compose file for internal reproducibility.
- `docs/runbooks/` lab operations and VM image validation checklists.
- `.gitlab-ci.yml` lightweight CI for frontend checks and backend smoke tests.

## Frontend Data Flow

The frontend now uses real backend calls for key surfaces:

- Home: health + featured products
- Shop and product detail: catalog and review data
- Account: profile, orders, subscriptions
- Wholesale: inventory, orders, invoices
- Search: API-backed query results
- Checkout and Assistant: interactive API calls from the page

## Complexity Scoring for Rate Limiting

The origin emits `X-SO-Complexity-Score` response headers (range `1..100`) for selected query-heavy endpoints so Cloudflare complexity-based rate limiting can enforce request cost, not just request count.

Covered endpoints:

- `GET /api/v1/search`
- `POST /api/v1/ai/chat`
- `POST /api/v1/ai/recommend`
- `POST /graphql`

## Canonical Spec

- `docs/specs/single-origin-design.md` — source requirements/specification copied from the contentpipeline project.

## OpenAPI Spec

- Runtime OpenAPI JSON: `GET /openapi.json`
- Runtime Swagger UI: `GET /api-docs` (redirects to `/docs`)
- Committed artifact: `docs/openapi/single-origin.openapi.json`

Regenerate the committed OpenAPI artifact:

```bash
.venv/bin/python scripts/export-openapi.py
```

Validate that the committed spec matches the generated backend schema:

```bash
.venv/bin/python scripts/export-openapi.py --check
```

CI also enforces this with `backend/tests/test_openapi_artifact.py`.

## Build Plan

- `docs/plans/build-single-origin-plan.md` — MVP-first implementation plan with VM-native learner runtime.

## Run Locally (VM-Native)

1. Start backend in terminal 1:

```bash
./scripts/start-backend.sh
```

2. Start frontend in terminal 2:

```bash
./scripts/start-frontend.sh
```

3. Open `http://localhost:5173`.

4. Validate backend quickly:

```bash
./scripts/smoke-test.sh
```

5. Optional traffic warmup:

```bash
./scripts/generate-traffic.py
```

## Environment

- Frontend: copy `frontend/.env.example` to `frontend/.env` and set:
  - `PUBLIC_API_BASE_URL`
  - `PUBLIC_TURNSTILE_SITEKEY`
- Backend: copy `backend/.env.example` to `backend/.env` and set:
  - `TURNSTILE_SECRET_KEY`
  - `TURNSTILE_EXPECTED_HOSTNAME`
  - `ENFORCE_TURNSTILE` (`false` by default for learner exercises)
  - Optional seeded login passwords: `SEED_DEMO_PASSWORD`, `SEED_WHOLESALE_PASSWORD`, `SEED_ADMIN_PASSWORD`, `SEED_TEST_USERS_PASSWORD`

If `TURNSTILE_SECRET_KEY` is empty, Turnstile validation endpoints fail with a clear configuration error.
If seed password variables are unset, random passwords are generated at startup and only password hashes are persisted.

## Reset and Recovery

- Reset lab data to baseline:

```bash
./scripts/reset-lab.sh
```

- Full operations runbook: `docs/runbooks/lab-operations.md`
