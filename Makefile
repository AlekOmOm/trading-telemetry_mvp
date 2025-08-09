SHELL := /bin/bash

.PHONY: env-setup infra-up apps-up open

env-setup:
	@if [ -f .env ]; then \
		echo ".env already exists. Skipping copy."; \
	else \
		if [ -f .env.sample ]; then \
			cp .env.sample .env && echo "Created .env from .env.sample"; \
		else \
			echo ".env.sample not found" && exit 1; \
		fi; \
	fi

infra-up:
	docker compose -f docker-compose.infra.yml up -d

apps-up:
	@echo "Starting metrics-sidecar (uvicorn) ..."
	@cd metrics-sidecar 2>/dev/null && \
		uv run uvicorn metrics_sidecar.web:app --host "$${SIDECAR_HTTP_HOST:-0.0.0.0}" --port "$$SIDECAR_HTTP_PORT" --reload \
			> ../.metrics-sidecar.out 2>&1 & echo $$! > ../.metrics-sidecar.pid || \
		echo "metrics-sidecar project not found or command failed. Ensure code exists at metrics-sidecar/."
	@sleep 1
	@echo "Starting trading-app (streamlit) ..."
	@cd trading-app 2>/dev/null && \
		uv run streamlit run trading_app/ui.py --server.port "$$WEBAPP_HTTP_PORT" \
			> ../.trading-app.out 2>&1 & echo $$! > ../.trading-app.pid || \
		echo "trading-app project not found or command failed. Ensure code exists at trading-app/."
	@echo "Apps start attempted. PIDs saved to .*.pid if successful."

open:
	@# Open Grafana dashboard and the webapp UI
	@open "http://localhost:3000/d/telemetry-mvp/trading-telemetry-mvp?refresh=5s"
	@open "http://localhost:$${WEBAPP_HTTP_PORT:-8501}"

