# Single Origin Build Plan (MVP-First)

This plan translates the canonical requirements in `docs/specs/single-origin-design.md` into an implementation sequence optimized for lab delivery.

## Delivery Approach

- Build a thin, end-to-end MVP first (all key routes + flows present, minimal business depth).
- Run the learner lab on a VM-native setup so students can directly edit frontend and backend.
- Keep containerization as a secondary packaging path for internal reproducibility, not the primary learner runtime.

## Runtime Model for Labs

- Provision one VM per learner/pod with source code pre-baked.
- Run frontend and backend as separate local services with hot reload.
- Include `cloudflared` in the VM image and route hostnames through Cloudflare.
- Preinstall dependencies and provide helper scripts (`start`, `restart`, `status`, `logs`).

## Phase 0: Repository Scaffold

- `frontend/` (SvelteKit)
- `backend/` (FastAPI + Strawberry)
- `scripts/` (lab helper scripts)
- `infra/` (optional container + deployment assets)
- `docs/` (specs, runbooks, learner troubleshooting)

Exit criteria:
- Fresh VM boots and can run both services with one command.

## Phase 1: Core Backend MVP

- SQLite models + seed data for products, users, carts, orders, subscriptions.
- JWT auth basics (`/api/v1/auth/login`, `/register`, `/refresh`, JWKS endpoint).
- Core API routes with stable schemas and dummy-safe business behavior.
- OpenAPI exposure at `/openapi.json` and `/api-docs`.

Exit criteria:
- API routes respond with expected status codes and shape.
- Seed users from spec can authenticate.

## Phase 2: Core Frontend MVP

- SSR pages: home, shop, product detail, guides, login, register, contact, search.
- SPA pages: checkout, account, subscribe, wholesale, assistant, admin.
- Form flows connected to backend endpoints.

Exit criteria:
- Learner can navigate key pages and submit forms.

## Phase 3: Turnstile-Ready Lab Surface

- Login/register/contact forms present in editable source.
- Backend handlers for those forms structured so learners can add Siteverify checks.
- Environment-variable wiring for Turnstile secret key.
- Clear separation of frontend widget insertion points and backend verification points.

Exit criteria:
- Learner can complete Turnstile tasks end-to-end by editing app code.

## Phase 4: AppSec Coverage Features

- Third-party script simulation and outbound connection simulation for Page Shield.
- Upload endpoint and intentional unsanitized inputs for WAF/Traffic Detections labs.
- AI endpoints for Firewall for AI, GraphQL schema depth for API Shield.
- Origin complexity score emission for search/ai/graphql endpoints to support complexity-based rate limiting calibration.
- Sensitive-data response fixtures and BOLA-prone object ID patterns per spec.

Exit criteria:
- Each AppSec lab has the required exercise surface available.

## Phase 5: Traffic + Observability

- Add a traffic generator profile for legitimate + attack-like patterns.
- Add local service logs and health checks for quick learner debugging.
- Document common failure paths and quick resets.

Exit criteria:
- Security events are visible early in the lab without manual warm-up.

## Phase 6: Hardening for Lab Operations

- VM image bake pipeline with versioned release notes.
- Smoke test script to verify routes, auth, and key lab prerequisites.
- Fast reset path to baseline state between learners/runs.

Exit criteria:
- Reproducible VM image with deterministic learner experience.

## Risks and Controls

- Risk: Student edits break the app mid-lab.
  - Control: Include reset scripts and known-good branch/tag restore steps.
- Risk: Turnstile confusion between widget-only and actual validation.
  - Control: Built-in lab checks that fail when Siteverify is missing.
- Risk: Container-first runtime slows iteration.
  - Control: Default to VM-native services for learner path.

## Immediate Next Build Slice

1. Scaffold `frontend/` + `backend/` + shared run scripts.
2. Implement login/register/contact paths with minimal UI and handlers.
3. Add environment plumbing for Turnstile keys and verification helper stub.
4. Validate edit-refresh-test loop on a VM image prototype.
