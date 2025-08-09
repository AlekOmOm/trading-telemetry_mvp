# Trading Telemetry MVP — TODO Roadmap

A living checklist to track phased delivery. Use small, verifiable tasks with clear DoD. Update as we learn.

## Phase 0 — Setup (DONE)

- [x] Infra up and running (Prometheus + Grafana provisioning)
- [x] Makefile commands created (`env-setup`, `infra-up`, `apps-up`, `open`)
- [x] Architecture skeleton established (apps + infra layout)
- [x] Core docs created (`README`, `AGENTS.md`, `docs/infra.md`, `docs/uv-guide.md`)
- [x] Root `.gitignore` in place (keep `uv.lock`, ignore `.env`)
- [x] Root `.env` and `.env.sample` added
- [x] `uv` usage documented and aligned

Definition of Done (Phase 0)
- [x] `make infra-up` brings up Prometheus + Grafana with a default dashboard
- [x] `make open` opens Grafana and the webapp placeholder

---

## Phase 1 — Webapp Initial Creation

Goal: Scaffold the trading webapp ("trading-app") with a minimal but production-lean shape: config, HTTP server, basic UI placeholder, health endpoints, and a publish path for trade events to ZeroMQ for the metrics sidecar. Keep it lean; real features come next phases.

Tasks

- Project scaffold
  - [ ] Create `trading-app/pyproject.toml` (managed by `uv`) with deps: `fastapi`, `uvicorn[standard]`, `pydantic`, `jinja2`, `python-multipart` (if forms), `prometheus-client` (basic process metrics), `pyzmq`, `orjson` (optional)
  - [ ] Add package `trading_app` with modules: `__init__.py`, `ui.py` (FastAPI app factory), `routes.py` (HTTP endpoints), `zmq_pub.py` (publisher helper), `main.py` (CLI entry)
  - [ ] Add `__main__.py` or `console_scripts` entrypoint `trading-app=trading_app.main:main`
  - [ ] Generate and commit `uv.lock`

- Configuration & env
  - [ ] Use shared `trading-app/src/environment.py` to load from repo `.env`
  - [ ] Define/confirm vars: `WEBAPP_HTTP_HOST`, `WEBAPP_HTTP_PORT`, `WEBAPP_ZMQ_ADDR`
  - [ ] Provide sane defaults (e.g., `0.0.0.0:8000` and `tcp://127.0.0.1:5555`)

- HTTP server & routes
  - [ ] FastAPI app with middleware for request ID and logging
  - [ ] Endpoints: `GET /healthz`, `GET /readyz`, `GET /` (placeholder page), `POST /trade` (accept trade payload, basic validation)
  - [ ] Add CORS config (dev-friendly, restricted by env)

- UI placeholder
  - [ ] Jinja2 template at `templates/index.html` with a minimal page (“Trading Telemetry MVP”)
  - [ ] Simple HTML form or curl examples to send a demo trade to `POST /trade`

- ZMQ integration (publish-only stub)
  - [ ] Initialize ZeroMQ publisher on `WEBAPP_ZMQ_ADDR` (lazy connect, retry on failure)
  - [ ] On `POST /trade`, publish a normalized event for the sidecar to consume
  - [ ] Include basic schema: `symbol`, `price`, `qty`, `side`, `ts`

- Metrics & logging
  - [ ] Expose basic process metrics via `prometheus_client` at `/metrics` (optional in Phase 1; sidecar owns trade metrics)
  - [ ] Structured logging to stdout with context (request id, route, status)

- Local run integration
  - [ ] Update `Makefile` `apps-up` to run the webapp via `uv run` (with reload in dev)
  - [ ] Add `apps-down` to stop dev processes (if using a supervisor) or document Ctrl+C
  - [ ] Verify `make apps-up` + `make open` workflow

- Docs updates
  - [ ] README: add “Webapp” section with run instructions and example curl
  - [ ] `docs/infra.md`: note that trade metrics appear once sidecar is added (Phase 2)
  - [ ] `docs/uv-guide.md`: add typical dev loop (`uv run`, reload)

Definition of Done (Phase 1)
- [ ] `make apps-up` starts the webapp on `WEBAPP_HTTP_HOST:WEBAPP_HTTP_PORT`
- [ ] `GET /healthz` returns 200; `GET /` renders placeholder page
- [ ] `POST /trade` accepts a valid payload and publishes to ZMQ without errors
- [ ] Optional: `/metrics` exposes basic process metrics

---

## Phase 2 — Metrics Sidecar

- [ ] Scaffold sidecar project (`metrics-sidecar`) with `uv`
- [ ] Connect to `WEBAPP_ZMQ_ADDR` as subscriber; parse events
- [ ] Expose Prometheus metrics on `SIDECAR_HTTP_HOST:SIDECAR_HTTP_PORT` (counters, gauges)
- [ ] Align with Grafana dashboard queries; validate panels update

## Phase 3 — Webapp UI & Features

- [ ] Add live trade feed UI (SSE or WebSocket)
- [ ] Input validation, schemas, and client-side UX polish
- [ ] Basic auth or API token (if needed)

## Phase 4 — Packaging & Deployment (Optional)

- [ ] Dockerize apps; add app services to Compose network
- [ ] CI checks (lint, type-check, tests) and release tagging
- [ ] Production configs and secrets handling

