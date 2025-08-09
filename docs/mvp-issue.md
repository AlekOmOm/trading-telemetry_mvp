MVP: ZMQ Side-Car Telemetry Pipeline (trading-telemetry_mvp)

📚 Description/Summary

Deliver an end-to-end, low-latency telemetry loop for a toy trading app:

1. a Streamlit UI (publisher) emits trade events over pyzmq PUSH;
2. a side-car service PULLs, updates Prometheus metrics, and exposes `/metrics`;
3. Prometheus scrapes; Grafana visualizes. Scope targets a minimal, observable path with two independent Python projects and a single infra compose stack.

💭 Proposed Solution

- Repos/structure: create `trading-app/` (publisher) and `metrics-sidecar/` (subscriber), each with its own `pyproject.toml` and hot-reload entrypoints.
- Publisher: Streamlit UI (Buy/Sell, qty default 1). Optional FastAPI `POST /trade/{side}`. Emit JSON per PRD schema `{type, side, qty, ts}` via ZMQ PUSH (`connect`).
- Side-car: ZMQ PULL (`bind`); validate payload; update metrics `trades_total{side}`, `volume_total{side}`, `last_trade_ts_seconds`. FastAPI exposes `GET /metrics` and `GET /health`.
- Infra: `docker-compose.yml` for Prometheus + Grafana; `prometheus.yml` job scraping `metrics-sidecar:8001` every 1s. Provide a minimal Grafana dashboard (totals by side + last trade ts).
- Docs/ops: Document `.env` keys (`WEBAPP_ZMQ_ADDR`, `SIDECAR_ZMQ_BIND`, `HOST`, `PORT`), startup order (side-car before publisher), ports, and run commands.

❗ Dependencies

- Runtime: Python 3.12+, Docker, Docker Compose.
- build: uv (uvicorn run)
- Libraries: streamlit, fastapi, uvicorn, pyzmq, prometheus-client, pydantic.
- Images: Prometheus, Grafana.
- Config/Ports: `SIDECAR_ZMQ_BIND=tcp://0.0.0.0:5555`, `WEBAPP_ZMQ_ADDR=tcp://metrics-sidecar:5555`; side-car HTTP `:8001`; Streamlit default `:8501` (or documented alternative).

✅ Definition of done

- [ ] Two Python projects (`trading-app/`, `metrics-sidecar/`) run independently with hot reload.
- [ ] Publisher sends schema-compliant JSON over ZMQ PUSH; side-car PULL receives and validates.
- [ ] Metrics update correctly: `trades_total{side}+=1`, `volume_total{side}+=qty`, `last_trade_ts_seconds=ts`.
- [ ] `GET /metrics` is scrapeable locally; Prometheus job at ~1s interval collects metrics without errors.
- [ ] Grafana dashboard shows totals by side and last trade timestamp updating within panel refresh ≤5s.
- [ ] Clicking Buy/Sell with qty N reflects in metrics within ≤1s of the next scrape (document scrape interval caveat).
- [ ] README/docs include message schema, metrics contract, startup order, ports, and env var templates.
- [ ] `docker-compose.yml` reliably starts Prometheus + Grafana pointing at `metrics-sidecar`.
