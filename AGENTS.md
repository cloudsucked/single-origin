# Agents Notes

- On this GitLab server, do not define pipeline jobs using standard `image:` container jobs.
- CI must be implemented via approved Backstage/GitLab CI components (for example `cloudflare/ci/...` includes).
- When adding or updating `.gitlab-ci.yml`, use component includes and component inputs only.

## Application overview

Single Origin is a synthetic specialty-coffee e-commerce app used as the origin in Cloudflare Implement / Operate / Troubleshoot AppSec labs. The canonical spec lives at `docs/specs/single-origin-design.md`. Stack: FastAPI + SvelteKit + SQLite, single container on port 8080, served through `cloudflared`.

### Runtime

- `pytest tests/` from `backend/` runs the backend test suite (currently 34 tests).
- `scripts/export-openapi.py` regenerates `docs/openapi/single-origin.openapi.json`; the `backend-openapi-test` CI job fails if the committed artifact drifts.
- `scripts/reset-lab.sh` drops and re-seeds `single_origin.db`, then restarts the backend. Flags: `--no-restart` (skip the docker/systemd restart in dev shells), `--quiet` (suppress `[ok]` lines).
- `scripts/smoke-test.sh` hits every endpoint the 9 Implement AppSec courses depend on. Flag: `--verbose`. Exits non-zero on the first failure.

### Environment variables

Critical env vars (see `backend/app/config.py`):

- `AI_GATEWAY_ENABLED` — default `false`. When `true`, `/api/v1/ai/chat` and `/api/v1/ai/recommend` proxy to Cloudflare AI Gateway instead of returning the canned lab response.
- `AI_GATEWAY_URL` — gateway URL pattern, e.g. `https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/workers-ai/@cf/meta/llama-3.1-8b-instruct`.
- `AI_GATEWAY_TOKEN` — bearer sent upstream as `cf-aig-authorization: Bearer <token>`.
- `AI_MODEL` — default `@cf/meta/llama-3.1-8b-instruct`. Overrides any client-sent `model` alias so lab aliases like `brew-assistant-v1` work transparently.
- `CHECKOUT_SDK_EXFIL_URL` — default `https://exfil.{SLUG}.sxplab.com/skim`. Controls the fetch target of the `v=1.2.4` compromised variant of `/js/checkout-sdk.js` (Page Shield supply-chain simulation).
- `ENFORCE_TURNSTILE` — when `true`, `/login`, `/register`, `/contact/submit`, and `/checkout/submit` validate `cf-turnstile-response` tokens with Siteverify.
- `LAB_JWT_PRIVATE_KEY` — when set, the app switches from HS256 to RS256 JWT signing and serves a matching JWKS endpoint (for API Shield JWT Validation exercises).
- `SEED_DEMO_PASSWORD`, `SEED_ADMIN_PASSWORD`, `SEED_WHOLESALE_PASSWORD`, `SEED_TEST_USERS_PASSWORD` — seed credentials consumed by `seed_db.py`.

### Key endpoints for lab exercises

Full list in the spec. Highlights:

- `GET /debug/headers` — echoes incoming headers (Implement mTLS Task 8 managed-transform validation).
- `POST /checkout/submit` — form-encoded checkout payload (303 browser / 200 JSON split; Turnstile, Bot Management, Security Analytics).
- `POST /admin` — form-encoded admin login (Bot Management credential stuffing; uses `username` field).
- `POST /api/v2/auth`, `POST /api/mobile/login` — JSON alt-auth endpoints (Traffic Detections custom detection locations).
- `POST /graphql`, `GET /graphql` — real Strawberry schema with self-referential Product→Farm→Origin depth fixture for API Shield Tasks 11–12. GraphiQL on GET.
- `POST /api/v1/ai/chat`, `POST /api/v1/ai/recommend` — OpenAI-compatible; proxy to AI Gateway when `AI_GATEWAY_ENABLED=true`.
- `GET /js/cart.js`, `/js/prefs.js`, `/js/cookie-consent.js`, `/js/so-analytics.js`, `/js/social-pixel.js`, `/js/checkout-sdk.js` — Page Shield Cookie Monitor + Script Monitor fixtures.

### Dependencies of note

`backend/requirements.txt` pins `strawberry-graphql[fastapi]==0.314.3` for the real GraphQL schema. Pydantic 2.12.x is used throughout; Strawberry's FastAPI integration coexists with Pydantic 2 (no v1 compat layer needed).

## Deployment — push to GitHub after every merge to main

The CML `generic-origin` infrastructure template provisions lab VMs by cloning from the **GitHub mirror** (`github` remote), not from GitLab. Changes merged to `main` on GitLab will not appear in new lab pods until they are also pushed to GitHub.

After every merge to `main`, always run:

```bash
git push github main
```

Both remotes are already configured:
- `origin` → `git@gitlab.cfdata.org:cloudflare/sxp/single-origin.git` (source of truth, CI runs here)
- `github` → `git@github.com:cloudsucked/single-origin.git` (read by CML at pod creation time)

**Never push directly to `github` without first merging to `origin/main`.**
If you are unsure whether the GitHub remote is up to date, run `git fetch github && git log github/main..main` to see what is missing.
