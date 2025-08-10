from __future__ import annotations

from prometheus_client import Counter, Gauge, CollectorRegistry


class TradingMetrics:
    """Prometheus metrics for trading telemetry."""

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self._registry = registry
        
        # Counters
        self.trades_total = Counter(
            "trades_total",
            "Total number of trades",
            ["side"],
            registry=registry
        )
        
        self.volume_total = Counter(
            "volume_total", 
            "Total trading volume",
            ["side"],
            registry=registry
        )
        
        # Gauges
        self.last_trade_ts_seconds = Gauge(
            "last_trade_ts_seconds",
            "Timestamp of the last trade",
            registry=registry
        )

    def record_trade(self, side: str, qty: float, ts: float) -> None:
        """Record a trade event in metrics."""
        self.trades_total.labels(side=side).inc()
        self.volume_total.labels(side=side).inc(qty)
        self.last_trade_ts_seconds.set(ts)