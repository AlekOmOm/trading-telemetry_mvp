Metrics Sidecar (Subscriber)
============================

What it does
- ZeroMQ PULL subscriber that receives trade events from the publisher.
- Updates Prometheus counters/gauges and exposes them on `/metrics`.
- Provides `/health` for a simple readiness check.

How to run
- Ensure `.env` has (defaults shown):
  - `SIDECAR_ZMQ_BIND=tcp://0.0.0.0:5555`
  - `SIDECAR_HTTP_HOST=0.0.0.0`
  - `SIDECAR_HTTP_PORT=8001`
- From the repo root:
  - `uv run -p metrics-sidecar uvicorn metrics_sidecar.web:app --host $SIDECAR_HTTP_HOST --port $SIDECAR_HTTP_PORT --reload`
- Or via the root Makefile:
  - `make apps-up` (attempts to start both apps)

Endpoints
- `GET /metrics`: Prometheus exposition format
- `GET /health`: basic health response including ZMQ bind address

Notes
- Start the sidecar before the publisher to avoid losing early messages (PUSH/PULL is fire-and-forget).
