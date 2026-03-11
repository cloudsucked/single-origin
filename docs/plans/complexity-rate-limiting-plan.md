# Complexity-Based Rate Limiting Plan (v1)

## Goal

Implement origin-generated query complexity scoring so Cloudflare can apply complexity-based rate limiting instead of counting all requests equally.

Reference: https://developers.cloudflare.com/waf/rate-limiting-rules/request-rate/#complexity-based-rate-limiting

## Scope (v1)

Apply complexity scoring to:

- `GET /api/v1/search`
- `POST /api/v1/ai/chat`
- `POST /api/v1/ai/recommend`
- `POST /graphql`

## Contract

Origin returns a numeric complexity score in a response header:

- Header: `X-SO-Complexity-Score`
- Value: integer in range `1..100`
- Fallback: emit safe default score (`10`) if scoring fails

## Scoring Model (v1)

Use deterministic weighted scoring per endpoint:

- `score = clamp(1, 100, base + feature_weights)`

### Search (`/api/v1/search`)

Signal ideas:

- query length bands
- token count
- wildcard/operator count (`*`, `%`, `OR`, `AND`, quotes)
- punctuation/operator density

### AI Chat and Recommend (`/api/v1/ai/chat`, `/api/v1/ai/recommend`)

Signal ideas:

- message count or prompt input size
- estimated token count (all message content)
- max single message length
- payload size

### GraphQL (`/graphql`)

Signal ideas:

- query length
- estimated nesting depth
- field count
- alias count
- argument count
- variables payload size

## Score Bands (for tuning and policy)

- Low: `1-15`
- Medium: `16-40`
- High: `41-70`
- Very High: `71-100`

## Implementation Plan

1. Create scoring service module
   - File: `backend/app/services/complexity.py`
   - Add:
     - `score_search_query(q: str) -> int`
     - `score_ai_payload(payload: dict) -> int`
     - `score_graphql(payload: dict) -> int`
     - shared helpers (`clamp`, token estimator, depth heuristics)

2. Add complexity headers in routes
   - `backend/app/routes/misc.py` (`GET /api/v1/search`)
   - `backend/app/routes/ai.py` (`POST /api/v1/ai/chat`, `POST /api/v1/ai/recommend`)
   - `backend/app/routes/graphql.py` (`POST /graphql`)
   - Ensure all major success/error paths emit score where feasible.

3. Add tests
   - New test file: `backend/tests/test_complexity_scoring.py`
   - Validate:
     - header presence
     - score is integer `1..100`
     - simple payload < complex payload for each endpoint
     - fallback behavior on malformed payloads

4. Calibrate with sample payloads
   - Build a low/medium/high test matrix for search strings, chat/recommend payloads, and graphql queries.
   - Tune weights to separate normal users from expensive/abusive patterns.

5. Cloudflare rule setup
   - Configure complexity-based rate limiting rules for endpoint groups:
     - search
     - ai (chat + recommend)
     - graphql
   - Start in log/simulate mode, then enforce gradually.

6. Rollout
   - Phase A: deploy scoring only and observe distribution
   - Phase B: simulated rate limiting
   - Phase C: enforcement with conservative thresholds
   - Phase D: tune based on observed false positives/negatives

## Documentation Updates

### `README.md`

Add short section:

- complexity scoring is emitted from origin
- covered endpoints
- header name `X-SO-Complexity-Score`

### `docs/specs/single-origin-design.md`

Add subsection:

- Complexity Score Contract
- endpoint coverage
- score range/bands
- intended Cloudflare consumption

### `docs/runbooks/lab-operations.md`

Add verification procedure:

- sample requests for search/chat/recommend/graphql
- check complexity response header exists
- expected score range behavior (simple vs complex)

### `docs/plans/build-single-origin-plan.md`

Add follow-up item for AppSec instrumentation:

- complexity scoring and rate-limiting calibration workflow
