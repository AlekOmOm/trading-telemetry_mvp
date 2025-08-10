SHELL := /bin/bash

.PHONY: env-setup infra-up sidecar-up app-up apps-up apps-stop sidecar-dev app-dev apps-dev open \
        benchmark-burst benchmark-burst-large benchmark-sustained benchmark-sustained-high \
        benchmark-comprehensive benchmark-profile benchmark-dashboard benchmark-monitor benchmark-test benchmark-help

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
sidecar-up:
	@echo "Starting metrics-sidecar"
	@cd metrics-sidecar && uv run run-metrics-sidecar

trading-app-up:
	@echo "Starting trading-app"
	@cd trading-app && uv run run-trading-app

apps-up:
	@echo "Starting both applications in separate terminals..."
	@osascript -e 'tell application "Terminal" to do script "cd \"$(PWD)\" && make sidecar-up"'
	@sleep 1
	@osascript -e 'tell application "Terminal" to do script "cd \"$(PWD)\" && make trading-app-up"'
	@echo "terminals started"
	@make open

# ------------------------------------------------------------
# Open all services

open:
	@# Open all four services: Grafana, Trading App, Prometheus, and Metrics Sidecar
	@echo "Opening all services..."
	@open "http://localhost:3000/d/telemetry-mvp/trading-telemetry-mvp?refresh=5s"  # Grafana Dashboard
	@open "http://localhost:9090"                                                   # Prometheus
	@open "http://localhost:$(SIDECAR_PORT)/metrics"                     			# Metrics Sidecar Metrics
	@open "http://localhost:$(WEBAPP_PORT)"                             			# Trading App (Streamlit)

# ------------------------------------------------------------
# Benchmarking
# ------------------------------------------------------------

benchmark-burst:
	@echo "Running burst benchmark (1000 trades)..."
	@cd trading-app && uv run python -m trading_app.benchmark.runners burst 1000

benchmark-burst-large:
	@echo "Running large burst benchmark (5000 trades)..."
	@cd trading-app && uv run python -m trading_app.benchmark.runners burst 5000

benchmark-sustained:
	@echo "Running sustained benchmark (30s at 200 tps)..."
	@cd trading-app && uv run python -m trading_app.benchmark.runners sustained 30 200

benchmark-sustained-high:
	@echo "Running high-rate sustained benchmark (30s at 500 tps)..."
	@cd trading-app && uv run python -m trading_app.benchmark.runners sustained 30 500

benchmark-comprehensive:
	@echo "Running comprehensive benchmark suite..."
	@cd trading-app && uv run python -m trading_app.benchmark.runners comprehensive

benchmark-profile:
	@echo "Running latency profile (up to 1000 tps)..."
	@cd trading-app && uv run python -m trading_app.benchmark.runners profile 1000 100

benchmark-dashboard:
	@echo "Opening benchmark dashboard..."
	@open "http://localhost:3000/d/benchmark-telemetry/benchmark-telemetry?refresh=5s"

benchmark-monitor:
	@echo "Starting benchmark system self-monitoring..."
	@cd trading-app && uv run python -m trading_app.benchmark.self_monitor

benchmark-test:
	@echo "Testing benchmark metrics publishing..."
	@cd trading-app && uv run python -m trading_app.benchmark.test_metrics

benchmark-help:
	@echo "Available benchmark commands:"
	@echo "  benchmark-burst         - Quick burst test (1000 trades)"
	@echo "  benchmark-burst-large   - Large burst test (5000 trades)"
	@echo "  benchmark-sustained     - Sustained rate test (30s at 200 tps)"
	@echo "  benchmark-sustained-high- High rate test (30s at 500 tps)"
	@echo "  benchmark-comprehensive - Full benchmark suite"
	@echo "  benchmark-profile       - Latency profiling under load"
	@echo "  benchmark-dashboard     - Open benchmark dashboard"
	@echo "  benchmark-monitor       - Start benchmark system self-monitoring"
	@echo "  benchmark-test          - Test benchmark metrics publishing"

