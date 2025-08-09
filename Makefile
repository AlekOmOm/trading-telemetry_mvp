


.PHONY: infra-up
infra-up:
	@echo "-> starting infra - grafana and prometheus"
	@docker-compose -f docker-compose.infra.yml up -d


.PHONY: open
open:
	@echo "-> opening dashboard"
	@open http://localhost:3000/d/telemetry-mvp/trading-telemetry-mvp?orgId=1&refresh=5s
