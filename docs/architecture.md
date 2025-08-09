# Architecture Overview

This document describes the current MVP architecture and how the two Python apps and the observability stack fit together.

## Components

- Trading App (publisher)
  - UI: Streamlit single-page app with quantity input and Buy/Sell buttons.
  - Transport: ZeroMQ PUSH socket (connect) sending JSON trade events.
  - Package: `trading_app` under `trading-app/src/`.
  - Entrypoints: console scripts `trading-app` and `webapp`.

- Metrics Sidecar (subscriber)
  - Server: FastAPI app exposing `/metrics` and `/health`.
  - Transport: ZeroMQ PULL socket (bind) receiving trade events.
  - Metrics: `prometheus_client` counters/gauges updated on receive.
  - Package: `metrics_sidecar` under `metrics-sidecar/src/`.

- Observability
  - Prometheus scrapes the sidecar `/metrics` (dev scrape interval ~1s).
  - Grafana visualizes totals by side and last-trade timestamp.

## Data Flow

1. User clicks Buy/Sell with qty in the Streamlit UI.
2. UI constructs a `TradeMsg` and publishes via ZMQ PUSH to `WEBAPP_ZMQ_ADDR`.
3. Sidecar ZMQ PULL (bound at `SIDECAR_ZMQ_BIND`) receives, validates, and updates:
   - `trades_total{side}`
   - `volume_total{side}`
   - `last_trade_ts_seconds`
4. Prometheus scrapes `/metrics` on the sidecar.
5. Grafana dashboard shows live totals and last trade time.

## Message Schema

```json
{
  "type": "trade",
  "side": "buy" | "sell",
  "qty":  number,   // float >= 0
  "ts":   number    // unix epoch seconds (float)
}
```

Modeled by `trading_app.models.TradeMsg` and `metrics_sidecar.models.TradeMsg`.

## Project Layout

- `trading-app/`
  - `src/trading_app/ui.py`: Streamlit UI (main page)
  - `src/trading_app/zmq_pub.py`: Reusable ZMQ PUSH publisher
  - `src/trading_app/models.py`: Pydantic `TradeMsg`
  - `src/trading_app/environment.py`: Env loader (`get_trading_app_environment()`)
  - `src/trading_app/launcher.py`: Launches `streamlit run` with host/port from env
  - `src/trading_app/app.py`: `main()` wrapper for console script use
  - Console scripts (`pyproject.toml`): `trading-app`, `webapp`

- `metrics-sidecar/`
  - `src/metrics_sidecar/web.py`: FastAPI app (exposes `/metrics`, `/health`)
  - `src/metrics_sidecar/zmq_sub.py`: ZMQ PULL subscriber
  - `src/metrics_sidecar/metrics.py`: Prometheus counters/gauges
  - `src/metrics_sidecar/models.py`: Pydantic `TradeMsg`
  - `src/metrics_sidecar/environment.py`: Env loader (`get_sidecar_environment()`)

## Configuration

- Publisher env (with defaults):
  - `WEBAPP_ZMQ_ADDR=tcp://127.0.0.1:5555`
  - `WEBAPP_HTTP_HOST=0.0.0.0`
  - `WEBAPP_HTTP_PORT=8501`

- Sidecar env (with defaults):
  - `SIDECAR_ZMQ_BIND=tcp://0.0.0.0:5555`
  - `SIDECAR_HTTP_HOST=0.0.0.0`
  - `SIDECAR_HTTP_PORT=8001`

Both apps load `.env` from the repo root if present, without overwriting existing env vars.

## Run Commands

- Publisher (from repo root):
  - `uv run -p trading-app webapp` (console script), or
  - `make apps-up` (starts both apps if present)

- Sidecar (from repo root):
  - `uv run -p metrics-sidecar uvicorn metrics_sidecar.web:app --host $SIDECAR_HTTP_HOST --port $SIDECAR_HTTP_PORT --reload`

## Notes

- Start the sidecar before the publisher in dev to avoid early message drops (PUSH with no PULL peer may drop).
- Prometheus scrape interval drives UI-to-metrics visibility; default is ~1s in the provided infra compose.

