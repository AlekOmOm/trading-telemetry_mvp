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

## Phase 1 — `trading-app` Initial Creation (Streamlit)

Goal: Scaffold the Streamlit-based publisher ("trading-app") with a minimal UI (buy/sell + qty), typed payload validation, and a ZeroMQ PUSH that connects to the sidecar’s PULL. Avoid server frameworks here; FastAPI endpoints are optional and out-of-scope for Phase 1.

Tasks

- Project scaffold
  - [x] Create `trading-app/pyproject.toml` (managed by `uv`) with deps: `streamlit`, `pyzmq`, `pydantic` (for validation), `orjson` (optional)
  - [x] Add package `trading_app` with modules: `__init__.py`, `ui.py` (Streamlit app), `zmq_pub.py` (publisher helper), `models.py` (Pydantic `TradeMsg`)
  - [x] Generate and commit `uv.lock`

- Configuration & env
  - [x] Use shared `trading-app/src/environment.py` to load from repo `.env`
  - [ ] Confirm vars: `WEBAPP_HTTP_HOST`, `WEBAPP_HTTP_PORT` (Streamlit), `WEBAPP_ZMQ_ADDR` (e.g., `tcp://127.0.0.1:5555`)
  - [ ] Sensible defaults: host `0.0.0.0`, port `8501`

- Streamlit UI
  - [ ] Build a single-page app with: qty input, Buy and Sell buttons, and a small event log area
  - [ ] On click, construct `TradeMsg {type:"trade", side, qty, ts}` and send via ZMQ PUSH
  - [ ] Show success/error feedback inline (and log to stdout)

- ZMQ integration
  - [ ] Initialize PUSH socket to `WEBAPP_ZMQ_ADDR` (connect)
  - [ ] Reuse one socket per session; add simple retry/backoff on first connect

- Local run integration
  - [ ] Update `Makefile` `apps-up` to run: `uv run streamlit run trading_app/ui.py --server.address $WEBAPP_HTTP_HOST --server.port $WEBAPP_HTTP_PORT`
  - [ ] Optionally add `apps-webapp` target for starting only the publisher
  - [ ] Verify `make apps-up` + `make open` opens the Streamlit UI

- Docs updates
  - [ ] README: confirm Streamlit-first approach; add example “click → metrics” flow description
  - [ ] `docs/infra.md`: reiterate that metrics appear when the sidecar (Phase 2) is running
  - [ ] `docs/uv-guide.md`: add Streamlit dev loop tips

Definition of Done (Phase 1)

- [ ] `make apps-up` starts Streamlit on `WEBAPP_HTTP_HOST:WEBAPP_HTTP_PORT`
- [ ] Clicking Buy/Sell logs an event and sends a ZMQ message without errors
- [ ] With sidecar running, Grafana panels update within ~1s of a click

---

## Phase 2 — `metrics-sidecar`

- [ ] Scaffold sidecar project (`metrics-sidecar`) with `uv`
- [ ] Connect to `WEBAPP_ZMQ_ADDR` as subscriber; parse events
- [ ] Expose Prometheus metrics on `SIDECAR_HTTP_HOST:SIDECAR_HTTP_PORT` (counters, gauges)
- [ ] Align with Grafana dashboard queries; validate panels update
- [ ] add openapi support [openapi fastapi](../api/openapi.fastapi.md)

## Phase 3 - simplification & polish -> clean code

aim: keep modularity, but simplify for minimalism, readability and cleanliness
- remember: clean code is not necessarily less, but always more focused and intentional

- [ ] go through 
  - [ ] trading-app
    - [ ] trading-app/src/trading_app/lib/ui.py
    - [ ] trading-app/src/trading_app/lib/zmq_pub.py
    - [ ] trading-app/src/trading_app/lib/models.py
    - [ ] trading-app/src/trading_app/environment.py
    - [ ] trading-app/src/trading_app/entrypoint.py
    - [ ] trading-app/src/trading_app/app.py
    - [ ] trading-app/pyproject.toml
  - [ ] metrics-sidecar
    - [ ] metrics-sidecar/src/metrics_sidecar/lib/web.py
    - [ ] metrics-sidecar/src/metrics_sidecar/lib/zmq_sub.py
    - [ ] metrics-sidecar/src/metrics_sidecar/lib/metrics.py
    - [ ] metrics-sidecar/src/metrics_sidecar/lib/models.py
    - [ ] metrics-sidecar/src/metrics_sidecar/environment.py
    - [ ] metrics-sidecar/src/metrics_sidecar/entrypoint.py
    - [ ] metrics-sidecar/src/metrics_sidecar/app.py
    - [ ] metrics-sidecar/pyproject.toml

## Phase 4 — `trading-app` UI & Features

- [ ] Add live trade feed UI (SSE or WebSocket)
- [ ] Input validation, schemas, and client-side UX polish
- [ ] Basic auth or API token (if needed)

## Phase 5 — Packaging & Deployment

- [ ] Dockerize apps; add app services to Compose network
