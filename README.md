# Trading Telemetry MVP

## TL;DR
A minimal, low-latency telemetry loop for a toy trading app. The Streamlit UI (publisher) emits trade events over ZeroMQ (PUSH). A side-car (subscriber) receives them (PULL), updates Prometheus metrics, and exposes `/metrics`. Prometheus scrapes, and Grafana visualizes totals and last trade time. The goal is a small, observable pipeline that’s easy to run and extend.

## Project Layout (MVP)
- `trading-app/`: Streamlit UI + optional FastAPI; sends JSON `{type, side, qty, ts}` via ZMQ PUSH.
- `metrics-sidecar/`: FastAPI server exposing `/metrics`; receives ZMQ PULL and updates counters/gauges.
- `docker-compose.infra.yml`: Prometheus + Grafana stack for local observability.
- `docs/`: Product/design docs (see `docs/MVP.PRD.md`).

## Run the MVP (local)
1) Configure env
- Side-car bind (default): `SIDECAR_ZMQ_BIND=tcp://0.0.0.0:5555`
- App connect: `WEBAPP_ZMQ_ADDR=tcp://localhost:5555`

2) Start infra (Prometheus + Grafana)
- `docker compose -f docker-compose.infra.yml up -d`
- Prometheus scrapes side-car `:8001` every ~1s; Grafana reads from Prometheus.

3) Start services with hot reload
- Side-car: `uvicorn metrics_sidecar.web:app --host 0.0.0.0 --port 8001 --reload`
- App (UI): `streamlit run trading_app/ui.py`

4) Verify
- Click Buy/Sell (qty default 1) in the UI. Within ~1s of the next scrape, metrics update:
  - `trades_total{side} += 1`, `volume_total{side} += qty`, `last_trade_ts_seconds = ts`.
- Check `http://localhost:8001/metrics`, Prometheus UI, and Grafana dashboard.

## MVP Scope
- Two independent Python projects with hot reload.
- Prometheus counters/gauges only (no durability guarantees).
- One simple Grafana dashboard panelizing totals by side and the last trade timestamp.

## Notes
- Start the side-car before the publisher to avoid early message drops.
- All message/metrics contracts and acceptance criteria are in `docs/MVP.PRD.md`.
