# prd (mvp): trading-telemetry

## overview

- purpose: demonstrate an end‑to‑end, low‑latency telemetry loop for a toy trading app.
- flow: user clicks **buy/sell** → publisher sends a **pyzmq push** message → side‑car **pulls**, updates **prometheus\_client** metrics → **prometheus** scrapes → **grafana** visualizes.
- outcome: a clear, inspectable data path where each hop is observable.

## goals

### overall project goals

- build a composable telemetry pipeline for trading‑like events with minimal latency and minimal dependencies.
- show how zmq decouples ui/action producers from metrics aggregation and later analytics.
- enable future custom metrics (numpy/pandas) and experimental latency benchmarking (matplotlib) without changing the producer.

### mvp goals

- provide a working publisher (streamlit + fastapi + pyzmq push) and a side‑car subscriber (fastapi + prometheus\_client + pyzmq pull).
- ship one docker‑compose stack for **prometheus + grafana**.
- split codebases into **two python projects** (two `pyproject.toml`) to support independent dev hot‑reload.
- include a minimal grafana dashboard showing: `trades_total{side}`, `volume_total{side}`, and `last_trade_ts_seconds`.
- document the exact message schema and the prometheus metrics contract.

## non‑goals (mvp)

- durability/at‑least‑once semantics (push/pull is fire‑and‑forget). if side‑car is down, messages may be lost.
- matching engine, order book, or real brokerage integration.
- multi‑tenant authn/authz.

## assumptions & constraints

- **assumption:** single side‑car instance (mvp). push/pull round‑robins across multiple pullers; we avoid that by running one.
- **constraint:** side‑car should start before publisher to avoid early message drops (documented in runbook).
- **constraint:** local dev prioritizes simplicity: plain docker for infra; `uvicorn --reload` and `streamlit` for app hot‑reload.

## user requirements

- **buy/sell actions** with quantity input. defaults to `1`.
- **info/trace events**: visible log/notifications that a click emitted a zmq message; side‑car shows a received event.
- **prometheus ingestion**: counters/gauges reflect events within ≤1s after click (scrape interval permitting).
- **grafana visualization**: a simple dashboard panelizing totals per side and last trade timestamp.
- **dev ergonomics**:
  - a single `docker-compose.infra.yml` for prometheus + grafana.
  - two standalone python projects:
    - `trading-app/` (publisher): streamlit ui, optional fastapi endpoints, pyzmq push.
    - `metrics-sidecar/` (subscriber): fastapi serving `/metrics/`, pyzmq pull, prometheus\_client.
  - hot reload in dev: streamlit auto‑reload; fastapi via `uvicorn --reload`.

## tech stack

- **publisher (trading‑app)**
  - streamlit (ui: buy/sell buttons, qty input)
  - fastapi (optional: `/trade/{side}` endpoint for programmatic calls)
  - pyzmq (push socket)
- **side‑car (metrics‑exposer)**
  - fastapi (http server for `/metrics/` and `/health`)
  - prometheus\_client (metrics registry/export)
  - pyzmq (pull socket)
  - *(future)* numpy, pandas (custom metrics), matplotlib (latency plots)
- **observability**
  - prometheus (scrape side‑car)
  - grafana (dashboards)
- **packaging/runtime**
  - two `pyproject.toml`
  - container images with `entrypoint.sh` invoking `web_server.py` (uvicorn) or `streamlit run` as appropriate
  - `.env` managed via a small `environment.py`

## architecture

- components:
  - `trading-app` → streamlit ui issues events → `TradePush` (zmq) sends json.
  - `metrics-sidecar` → `TradePull` receives json → updates prometheus metrics → exposes `/metrics/`.
  - `prometheus` scrapes side‑car.
  - `grafana` reads from prometheus and renders panels.
- deployment shape:
  - apps run as two separate processes/containers; infra (prom+graf) via a separate compose file.

## data flow (numbered)

1. user clicks **buy** with qty q in streamlit.
2. publisher constructs `TradeMsg` and sends over zmq push (`connect`).
3. side‑car pull (`bind`) receives `TradeMsg`, validates, updates counters/gauges.
4. prometheus scrapes `/metrics/` on side‑car.
5. grafana dashboard panels query prometheus and update visuals.

## message schema (contract)

```json
{
  "type": "trade",          // literal
  "side": "buy"|"sell",    // enum
  "qty":  number,            // float >= 0
  "ts":   number             // unix epoch seconds (float)
}
```

- versioning: mvp sticks to this fixed schema; future changes must be backward‑compatible or gated by `type` variants.

## metrics (prometheus contract)

- counters
  - `trades_total{side}`: increment by `1` per message.
  - `volume_total{side}`: increment by `qty` per message.
- gauges
  - `last_trade_ts_seconds`: set to `ts` of the last received trade.
- *(future)* histograms/summaries for inter‑arrival time and measured end‑to‑end latency.

## http interfaces

- publisher (optional)
  - `POST /trade/{side}` → body/form: `qty: float` → emits zmq message and returns 303 to ui.
- side‑car
  - `GET /metrics/` → prometheus exposition format.
  - `GET /health` → 200 when pull loop is running.

## configuration

- `.env` keys (examples)
  - publisher: `WEBAPP_ZMQ_ADDR=tcp://metrics-sidecar:5555`, `HOST`, `PORT`.
  - side‑car: `SIDECAR_ZMQ_BIND=tcp://0.0.0.0:5555`, `HOST`, `PORT`.
  - prometheus: scrape job targets side‑car `host:port`.
- ports
  - publisher ui: `:8000` (fastapi if used) + streamlit default `:8501` (or unify under fastapi reverse‑proxy in future).
  - side‑car: `:8001` (`/metrics/`).

## deployment & dev setup

- **projects**
  - `trading-app/pyproject.toml` (deps: streamlit, fastapi, uvicorn, pyzmq, pydantic)
  - `metrics-sidecar/pyproject.toml` (deps: fastapi, uvicorn, pyzmq, prometheus-client, pydantic)
- **entrypoint**
  - each image uses `entrypoint.sh` to call `python web_server.py` (fastapi) or `streamlit run ui.py`.
- **compose (infra)**
  - `docker-compose.infra.yml` spins up `prometheus` + `grafana`.
  - prometheus `prometheus.yml` contains a job scraping `metrics-sidecar:8001` every `1s`.
- **dev hot‑reload**
  - run publisher locally via `streamlit run` and optional fastapi via `uvicorn --reload`.
  - run side‑car via `uvicorn --reload`.

## acceptance criteria (mvp)

1. clicking **buy** or **sell** with qty `N` increases `trades_total{side}` by `1` and `volume_total{side}` by `N` within ≤1s of the next scrape.
2. `last_trade_ts_seconds` reflects a timestamp within ±2s of wall time when the click occurred.
3. grafana dashboard shows both totals by side and last trade time updating in real time (panel refresh ≤5s).
4. starting order documented: when side‑car is down, user is informed that events may be dropped; once side‑car is up, new clicks are reflected.
5. two independent `pyproject.toml` projects run with hot reload; changing python files in either project reflects in running dev servers without rebuild.

## risks & mitigations

- **message loss** (push/pull with no subscriber) → mitigate by documenting startup order; *(future)* add a small retry/backoff or switch to dealer/router.
- **clock skew** affecting last‑ts gauge → rely on side‑car receive time for latency panels *(future)*.
- **scrape delay hides immediacy** → set a `1s` scrape interval in dev; clearly annotate in dashboard.

## future (post‑mvp)

- **custom metrics (numpy/pandas)**: rolling windows (e.g., last 1m/5m counts), exponential moving volume, click burstiness; expose as gauges.
- **latency benchmarking**: measure publish→receive (`recv_ts - msg.ts`), build histogram buckets; streamlit page to plot matplotlib latency charts from prometheus exports.
- **distribution**: multiple pullers and rr distribution; compare push/pull vs pub/sub semantics for telemetry broadcast.
- **reliability**: dealer/router with acks; optional disk buffer (nq) for offline scenarios.

## logic skeleton (for clarity)

- premise: if ui emits a well‑typed json message and transport delivers it, then metrics reflect the event since side‑car transforms message→counters.
- assumption: zmq push/pull provides low overhead; prometheus scrape interval is the dominant lag.
- therefore: optimizing scrape + panel refresh yields perceived real‑time behavior without touching ui or transport.
- since: metrics are append‑only counters/gauges, we can layer richer derived metrics later without changing the message schema.

## appendix: fastapi trade endpoint (optional)

```python
@app.post("/trade/{side}")
async def trade(side: str, qty: float = Form(...)):
    assert side in ("buy", "sell")
    await bus.send_trade(side, qty)
    return RedirectResponse("/", status_code=303)
```

