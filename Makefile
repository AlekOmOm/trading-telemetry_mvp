SHELL := /bin/bash

.PHONY: env-setup infra-up sidecar-up app-up apps-up apps-stop sidecar-dev app-dev apps-dev open

-include .env

SIDECAR_HOST := $${SIDECAR_HTTP_HOST:-0.0.0.0}
SIDECAR_PORT := $${SIDECAR_HTTP_PORT:-8001}
WEBAPP_HOST := $${WEBAPP_HTTP_HOST:-0.0.0.0}
WEBAPP_PORT := $${WEBAPP_HTTP_PORT:-8501}

# ------------------------------------------------------------
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

logs:
	@docker compose -f docker-compose.infra.yml logs -f

# ------------------------------------------------------------
# Apps
# ------------------------------------------------------------
apps-stop:
	@echo "🛑 Stopping applications..."
	@if [ -f .metrics-sidecar.pid ]; then \
		PID=$$(cat .metrics-sidecar.pid) && kill $$PID 2>/dev/null && echo "   → Stopped metrics-sidecar (PID: $$PID)" || echo "   → metrics-sidecar already stopped"; \
		rm -f .metrics-sidecar.pid; \
	fi
	@if [ -f .trading-app.pid ]; then \
		PID=$$(cat .trading-app.pid) && kill $$PID 2>/dev/null && echo "   → Stopped trading-app (PID: $$PID)" || echo "   → trading-app already stopped"; \
		rm -f .trading-app.pid; \
	fi
	@echo "✅ Apps stopped."

sidecar-up:
	@echo "Starting metrics-sidecar"
	@cd metrics-sidecar && uv run run-metrics-sidecar

trading-app-up:
	@echo "Starting trading-app"
	@cd trading-app && uv run run-trading-app

apps-up:
	@echo "Starting both applications in separate terminals..."
	@osascript -e 'tell application "Terminal" to do script "cd \"$(PWD)\" && make sidecar-dev"'
	@osascript -e 'tell application "Terminal" to do script "cd \"$(PWD)\" && make trading-app-dev"'
	@echo "terminals started"
	@make open


open:
	@# Open all four services: Grafana, Trading App, Prometheus, and Metrics Sidecar
	@echo "Opening all services..."
	@open "http://localhost:3000/d/telemetry-mvp/trading-telemetry-mvp?refresh=5s"  # Grafana Dashboard
	@open "http://localhost:9090"                                                   # Prometheus
	@open "http://localhost:$(SIDECAR_PORT)/metrics"                     # Metrics Sidecar Metrics
	@open "http://localhost:$(WEBAPP_PORT)"                             # Trading App (Streamlit)
