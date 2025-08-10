from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
from .data_analysis_metrics import TradeAnalyzer


class TradingMetrics:
    """Prometheus metrics for trading telemetry and benchmarking."""

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self._registry = registry
        self.analyzer = TradeAnalyzer()

        # Trading Counters
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

        # Trading Gauges
        self.last_trade_ts_seconds = Gauge(
            "last_trade_ts_seconds",
            "Timestamp of the last trade",
            registry=registry
        )

        # Benchmark Counters
        self.benchmark_tests_total = Counter(
            "benchmark_tests_total",
            "Total number of benchmark tests run",
            ["test_type", "test_name"],
            registry=registry
        )

        self.benchmark_trades_published_total = Counter(
            "benchmark_trades_published_total",
            "Total trades published during benchmarks",
            ["test_type", "test_name"],
            registry=registry
        )

        self.benchmark_errors_total = Counter(
            "benchmark_errors_total",
            "Total benchmark errors",
            ["test_type", "test_name", "error_type"],
            registry=registry
        )

        # Benchmark Gauges
        self.benchmark_last_test_timestamp = Gauge(
            "benchmark_last_test_timestamp",
            "Timestamp of the last benchmark test",
            ["test_type", "test_name"],
            registry=registry
        )

        self.benchmark_throughput_trades_per_second = Gauge(
            "benchmark_throughput_trades_per_second",
            "Benchmark throughput in trades per second",
            ["test_type", "test_name"],
            registry=registry
        )

        self.benchmark_duration_seconds = Gauge(
            "benchmark_duration_seconds",
            "Benchmark test duration in seconds",
            ["test_type", "test_name"],
            registry=registry
        )

        # Benchmark Latency Gauges (in microseconds)
        self.benchmark_latency_min_microseconds = Gauge(
            "benchmark_latency_min_microseconds",
            "Minimum publishing latency in microseconds",
            ["test_type", "test_name"],
            registry=registry
        )

        self.benchmark_latency_mean_microseconds = Gauge(
            "benchmark_latency_mean_microseconds",
            "Mean publishing latency in microseconds",
            ["test_type", "test_name"],
            registry=registry
        )

        self.benchmark_latency_p50_microseconds = Gauge(
            "benchmark_latency_p50_microseconds",
            "P50 publishing latency in microseconds",
            ["test_type", "test_name"],
            registry=registry
        )

        self.benchmark_latency_p95_microseconds = Gauge(
            "benchmark_latency_p95_microseconds",
            "P95 publishing latency in microseconds",
            ["test_type", "test_name"],
            registry=registry
        )

        self.benchmark_latency_p99_microseconds = Gauge(
            "benchmark_latency_p99_microseconds",
            "P99 publishing latency in microseconds",
            ["test_type", "test_name"],
            registry=registry
        )

        self.benchmark_latency_max_microseconds = Gauge(
            "benchmark_latency_max_microseconds",
            "Maximum publishing latency in microseconds",
            ["test_type", "test_name"],
            registry=registry
        )

        # Queue saturation metrics
        self.benchmark_queue_full_events_total = Counter(
            "benchmark_queue_full_events_total",
            "Total queue full events during benchmarks",
            ["test_type", "test_name"],
            registry=registry
        )

        # Data Analysis Gauges (NumPy/Pandas computed)
        self.analysis_mean_qty = Gauge(
            "analysis_mean_qty",
            "Mean trade quantity (NumPy)",
            registry=registry
        )
        
        self.analysis_qty_std = Gauge(
            "analysis_qty_std", 
            "Trade quantity standard deviation (NumPy)",
            registry=registry
        )
        
        self.analysis_buy_volume = Gauge(
            "analysis_buy_volume",
            "Total buy volume (Pandas)",
            registry=registry
        )

    def record_trade(self, side: str, qty: float, ts: float) -> None:
        """Record a trade event in metrics."""
        self.trades_total.labels(side=side).inc()
        self.volume_total.labels(side=side).inc(qty)
        self.last_trade_ts_seconds.set(ts)
        
        # Add to analyzer and update analysis metrics
        self.analyzer.add_trade(side, qty, ts)
        self._update_analysis_metrics()

    def record_benchmark(self, test_type: str, test_name: str, timestamp: float,
                        total_trades: int, duration_seconds: float,
                        trades_per_second: float, queue_full_count: int,
                        error_count: int, latency_stats: dict) -> None:
        """Record a benchmark test result in metrics."""
        labels = {"test_type": test_type, "test_name": test_name}

        # Record test completion
        self.benchmark_tests_total.labels(**labels).inc()
        self.benchmark_last_test_timestamp.labels(**labels).set(timestamp)

        # Record basic metrics
        self.benchmark_trades_published_total.labels(**labels).inc(total_trades)
        self.benchmark_throughput_trades_per_second.labels(**labels).set(trades_per_second)
        self.benchmark_duration_seconds.labels(**labels).set(duration_seconds)

        # Record errors and queue events
        if error_count > 0:
            self.benchmark_errors_total.labels(test_type=test_type, test_name=test_name, error_type="general").inc(error_count)

        if queue_full_count > 0:
            self.benchmark_queue_full_events_total.labels(**labels).inc(queue_full_count)

        # Record latency statistics if available
        if latency_stats:
            if "min_us" in latency_stats:
                self.benchmark_latency_min_microseconds.labels(**labels).set(latency_stats["min_us"])
            if "mean_us" in latency_stats:
                self.benchmark_latency_mean_microseconds.labels(**labels).set(latency_stats["mean_us"])
            if "p50_us" in latency_stats:
                self.benchmark_latency_p50_microseconds.labels(**labels).set(latency_stats["p50_us"])
            if "p95_us" in latency_stats:
                self.benchmark_latency_p95_microseconds.labels(**labels).set(latency_stats["p95_us"])
            if "p99_us" in latency_stats:
                self.benchmark_latency_p99_microseconds.labels(**labels).set(latency_stats["p99_us"])
            if "max_us" in latency_stats:
                self.benchmark_latency_max_microseconds.labels(**labels).set(latency_stats["max_us"])

    def _update_analysis_metrics(self) -> None:
        """Update analysis metrics using NumPy/Pandas."""
        numpy_stats = self.analyzer.get_numpy_stats()
        pandas_stats = self.analyzer.get_pandas_analysis()
        
        self.analysis_mean_qty.set(numpy_stats['mean_qty'])
        self.analysis_qty_std.set(numpy_stats['std_qty'])
        self.analysis_buy_volume.set(pandas_stats['buy_volume'])
