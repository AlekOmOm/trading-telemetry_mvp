SHELL := /bin/bash

.PHONY: env-setup infra-up sidecar-up app-up apps-up apps-stop open

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

sidecar-up:
	@echo "🚀 Starting metrics-sidecar (FastAPI + ZMQ subscriber)..."
	@source .env 2>/dev/null || true; \
	SIDECAR_HOST=$${SIDECAR_HTTP_HOST:-0.0.0.0}; \
	SIDECAR_PORT=$${SIDECAR_HTTP_PORT:-8001}; \
	echo "   → Host: $$SIDECAR_HOST"; \
	echo "   → Port: $$SIDECAR_PORT"; \
	echo "   → Health: http://localhost:$$SIDECAR_PORT/health"; \
	echo "   → Metrics: http://localhost:$$SIDECAR_PORT/metrics"; \
	cd metrics-sidecar 2>/dev/null && \
		PYTHONPATH=src uv run uvicorn metrics_sidecar.web:app --host "$$SIDECAR_HOST" --port "$$SIDECAR_PORT" --reload \
			> ../.metrics-sidecar.out 2>&1 & echo $$! > ../.metrics-sidecar.pid || \
		echo "❌ metrics-sidecar project not found or command failed."

app-up:
	@echo "🎯 Starting trading-app (Streamlit UI)..."
	@source .env 2>/dev/null || true; \
	WEBAPP_HOST=$${WEBAPP_HTTP_HOST:-0.0.0.0}; \
	WEBAPP_PORT=$${WEBAPP_HTTP_PORT:-8501}; \
	echo "   → Host: $$WEBAPP_HOST"; \
	echo "   → Port: $$WEBAPP_PORT"; \
	echo "   → URL: http://localhost:$$WEBAPP_PORT"; \
	cd trading-app 2>/dev/null && \
		uv run trading-app \
			> ../.trading-app.out 2>&1 & echo $$! > ../.trading-app.pid || \
		echo "❌ trading-app project not found or command failed."

apps-up: sidecar-up
	@sleep 2
	@echo ""
	$(MAKE) app-up
	@sleep 1
	@echo ""
	@echo "✅ Apps started! PIDs saved to .*.pid files."
	@echo "📋 Check status with: tail -f .*.out"
	@echo "🛑 Stop with: make apps-stop"

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

open:
	@# Open all four services: Grafana, Trading App, Prometheus, and Metrics Sidecar
	@echo "Opening all services..."
	@open "http://localhost:3000/d/telemetry-mvp/trading-telemetry-mvp?refresh=5s"  # Grafana Dashboard
	@open "http://localhost:9090"                                                   # Prometheus
	@open "http://localhost:$${SIDECAR_HTTP_PORT:-8001}/metrics"                     # Metrics Sidecar Metrics
	@open "http://localhost:$${WEBAPP_HTTP_PORT:-8501}"                             # Trading App (Streamlit)
