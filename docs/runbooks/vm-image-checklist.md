# VM Image Checklist

Use this list when baking or validating a learner VM image.

## Required Runtime

- Python 3.12+
- Node.js 20+
- npm
- cloudflared (for real lab routing)

### cloudflared ingress rules

The cloudflared configuration must route all four lab hostnames to the same origin container on port 8080. A minimal `config.yml` fragment:

```yaml
tunnel: <TUNNEL_UUID>
credentials-file: /etc/cloudflared/<TUNNEL_UUID>.json
ingress:
  - hostname: www.${SLUG}.sxplab.com
    service: http://localhost:8080
  - hostname: api.${SLUG}.sxplab.com
    service: http://localhost:8080
  - hostname: wholesale.${SLUG}.sxplab.com
    service: http://localhost:8080
  - hostname: iot.${SLUG}.sxplab.com
    service: http://localhost:8080
  - service: http_status:404
```

DNS records for all four hostnames must exist in the lab zone (orange-clouded CNAMEs pointing at the tunnel). The `wholesale.` and `iot.` hostnames carry the same application content — the CML blueprint enforces mTLS at the edge on those two hostnames, so requests without a valid client certificate are rejected before reaching the origin. This is the dependency behind Implement mTLS Task 3 (`wholesale.` hostname enablement) and Task 7 (`iot.` certificate pinning).

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
