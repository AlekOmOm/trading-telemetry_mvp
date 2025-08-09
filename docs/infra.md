# Infra (Prometheus + Grafana)

## TL;DR

- Start with: `docker compose -f docker-compose.infra.yml up -d`.
- Grafana:
  - `http://localhost:3000` (admin/admin).
  - Datasource and dashboard auto-provision.
- Prometheus:
  - `http://localhost:9090`.
  - Scrapes `metrics-sidecar:8001` and `host.docker.internal:8001` every 1s.

## Layout

- `docker-compose.infra.yml`: Brings up Prometheus and Grafana on network `trading-telemetry`.
- `infra/prometheus/prometheus.yml`: Scrape config (1s interval) and targets.
- `infra/grafana/provisioning/`: Auto-provisions datasources and dashboards.
- `infra/grafana/dashboards/trading-telemetry-mvp.json`: Default dashboard (totals and last-trade age).

## Usage

1) Start infra

- `make infra-up`
  - `docker compose -f docker-compose.infra.yml up -d`

2) Ensure side-car is reachable

- If the side-car runs as a container: join network `trading-telemetry` and use service name `metrics-sidecar` on port `8001`.
- If the side-car runs on host: expose `/metrics` at `:8001` (Prometheus also targets `host.docker.internal:8001`).

3) Verify

- Prometheus targets show “UP”.
- Grafana home → Dashboard “Trading Telemetry MVP” renders data when you click Buy/Sell.

## Modifying Dashboard for New Metrics

When you add new Prometheus metrics (e.g., histograms or additional gauges), update the dashboard so it loads at startup.

- Edit JSON: `infra/grafana/dashboards/trading-telemetry-mvp.json`.
- Common queries:
  - Counter by label: `trades_total{side="buy"}`
  - Rate: `rate(trades_total[1m])`
  - Gauge: `last_trade_ts_seconds`
  - Age: `time() - last_trade_ts_seconds`
- Import/export flow:
  1) Open Grafana → Dashboard → Edit panels, confirm queries.
  2) Share → Export → “View JSON” → Download.
  3) Replace the file at `infra/grafana/dashboards/trading-telemetry-mvp.json`.
  4) Recreate Grafana or `docker compose restart grafana` to reload provisioning.
- Adding more dashboards: drop additional `*.json` files into `infra/grafana/dashboards/`.

## Tips & Troubleshooting

- No data? Ensure side-car is running and reachable at `:8001`.
- Slow updates? Scrape interval is 1s; panel refresh is 5s by default.
- Credentials: default admin/admin (consider changing in compose env vars).
