Trading App (Publisher)
=======================

What it does

- Streamlit UI to publish trade events over ZeroMQ (PUSH).
- Emits JSON payloads matching the MVP contract: {type, side, qty, ts}.
- Intended to be consumed by the metrics sidecar (PULL) which updates Prometheus.

How to run

- Ensure you have a `.env` with (defaults shown):
  - `WEBAPP_HTTP_HOST=0.0.0.0`
  - `WEBAPP_HTTP_PORT=8501`
  - `WEBAPP_ZMQ_ADDR=tcp://127.0.0.1:5555`
- From the `trading-app/` directory:
  - `uv run trading-app` (console script), or
  - `uv run python app.py` (launcher), or
  - `uv run streamlit run src/trading_app/ui.py --server.address $WEBAPP_HTTP_HOST --server.port $WEBAPP_HTTP_PORT`

Notes

- If no sidecar is running yet, sends may warn due to no subscriber.
