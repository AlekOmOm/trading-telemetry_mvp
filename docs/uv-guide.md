# UV Setup Guide (Two Python Projects)

## TL;DR
- Use uv to manage isolated envs and run apps.
- Create two projects: `trading-app/` (publisher) and `metrics-sidecar/` (subscriber).
- Install deps with `uv add`, run with `uv run`, binaries with `uvx`.

## Project Setup
1) Create folders
- `mkdir -p trading-app metrics-sidecar`

2) Initialize pyproject
- In each folder, add a minimal `pyproject.toml`:
```
[project]
name = "trading-app"  # or "metrics-sidecar"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []
```

## Install Dependencies
- trading-app (Streamlit UI + optional FastAPI):
```
cd trading-app
uv add streamlit fastapi uvicorn pyzmq pydantic
uv add --dev pytest ruff black pre-commit
cd -
```
- metrics-sidecar (FastAPI + Prometheus client):
```
cd metrics-sidecar
uv add fastapi uvicorn pyzmq prometheus-client pydantic
uv add --dev pytest ruff black pre-commit
cd -
```
- Lock (optional but recommended): run `uv lock` in each project to produce a lockfile.

## Run (Hot Reload)
- Side-car API (exposes /metrics):
```
cd metrics-sidecar
uv run uvicorn metrics_sidecar.web:app --host 0.0.0.0 --port 8001 --reload
```
- Publisher UI (emits ZMQ PUSH):
```
cd trading-app
uv run streamlit run trading_app/ui.py
```

## Dev Tooling
- Lint/format (per project):
```
uvx ruff check . && uvx black .
```
- Tests:
```
uv run pytest -q
```
- Git hooks:
```
uv run pre-commit install
```

## Env & Config
- Add `.env.example` files documenting:
  - trading-app: `WEBAPP_ZMQ_ADDR=tcp://metrics-sidecar:5555`
  - metrics-sidecar: `SIDECAR_ZMQ_BIND=tcp://0.0.0.0:5555`
- Load env in code (e.g., a small `environment.py`).

## Notes
- Folder names: this guide assumes `metrics-sidecar/` (not “metrics-sidebar”). Adjust paths if you use a different name.
- Join the Docker network `trading-telemetry` to let Prometheus scrape the side-car at `metrics-sidecar:8001`.
