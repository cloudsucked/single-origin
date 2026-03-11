# VM Image Checklist

Use this list when baking or validating a learner VM image.

## Required Runtime

- Python 3.12+
- Node.js 20+
- npm
- cloudflared (for real lab routing)

## Required Files

- Repo checked out and readable by learner user.
- `backend/.env` created from `backend/.env.example`.
- `frontend/.env` created from `frontend/.env.example`.

## Dependency Warmup

- Backend venv created and dependencies installed.
- Frontend dependencies installed (`frontend/node_modules`).

## Service Validation

- Start backend and frontend once during image bake.
- Run `./scripts/smoke-test.sh` successfully.

## Reset + Recovery

- Confirm `./scripts/reset-lab.sh` reseeds data and exits 0.
- Confirm `./scripts/generate-traffic.py` executes without crashing.
