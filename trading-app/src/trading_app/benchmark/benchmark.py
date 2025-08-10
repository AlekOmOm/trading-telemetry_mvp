from __future__ import annotations

import time
import json
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from ..features.client import TradingClient
from ..features.models import TradeMsg


@dataclass
class BenchmarkResult:
    total_trades: int
    duration_seconds: float
    trades_per_second: float
    publish_stats: Dict[str, float]
    queue_full_count: int
    error_count: int


class PublishingBenchmark:
    """Benchmark the actual cost of publishing from the trading bot."""

    def __init__(self, zmq_addr: str, metrics_client: TradingClient = None):
        self.client = TradingClient(zmq_addr, enable_benchmarking=True)
        self.metrics_client = metrics_client  # Separate client for publishing benchmark results
        self.results: List[BenchmarkResult] = []

    def run_burst_test(self, num_trades: int = 1000, qty: float = 1.0) -> BenchmarkResult:
        """Test burst publishing - simulates high-frequency trading."""
        queue_full_count = 0
        error_count = 0

        start_time = time.perf_counter()

        for i in range(num_trades):
            side = "buy" if i % 2 == 0 else "sell"
            msg = TradeMsg(side=side, qty=qty, ts=time.time())

            result = self.client.publish_json(msg.model_dump())

            if result.queue_full:
                queue_full_count += 1
            elif not result.ok:
                error_count += 1

        end_time = time.perf_counter()
        duration = end_time - start_time

        benchmark_result = BenchmarkResult(
            total_trades=num_trades,
            duration_seconds=duration,
            trades_per_second=num_trades / duration,
            publish_stats=self.client.get_latency_stats(),
            queue_full_count=queue_full_count,
            error_count=error_count
        )

        self.results.append(benchmark_result)

        # Publish benchmark result as metrics if metrics client is available
        if self.metrics_client:
            self._publish_benchmark_result("burst", f"burst_{num_trades}", benchmark_result)

        return benchmark_result

    def run_sustained_test(self, duration_seconds: int = 10,
                          trades_per_second: int = 100) -> BenchmarkResult:
        """Test sustained publishing rate."""
        interval = 1.0 / trades_per_second
        trades_sent = 0
        queue_full_count = 0
        error_count = 0

        start_time = time.perf_counter()
        end_time = start_time + duration_seconds

        while time.perf_counter() < end_time:
            side = "buy" if trades_sent % 2 == 0 else "sell"
            msg = TradeMsg(side=side, qty=1.0, ts=time.time())

            result = self.client.publish_json(msg.model_dump())
            trades_sent += 1

            if result.queue_full:
                queue_full_count += 1
            elif not result.ok:
                error_count += 1

            # Rate limiting
            time.sleep(max(0, interval - (result.elapsed_ms or 0) / 1000.0))

        actual_duration = time.perf_counter() - start_time

        benchmark_result = BenchmarkResult(
            total_trades=trades_sent,
            duration_seconds=actual_duration,
            trades_per_second=trades_sent / actual_duration,
            publish_stats=self.client.get_latency_stats(),
            queue_full_count=queue_full_count,
            error_count=error_count
        )

        # Publish benchmark result as metrics if metrics client is available
        if self.metrics_client:
            self._publish_benchmark_result("sustained", f"sustained_{trades_per_second}tps", benchmark_result)

        return benchmark_result

    def print_results(self, result: BenchmarkResult):
        """Print benchmark results."""
        print(f"\n=== Publishing Benchmark Results ===")
        print(f"Total trades: {result.total_trades}")
        print(f"Duration: {result.duration_seconds:.3f}s")
        print(f"Throughput: {result.trades_per_second:.1f} trades/sec")
        print(f"Queue full events: {result.queue_full_count}")
        print(f"Errors: {result.error_count}")

        if result.publish_stats:
            stats = result.publish_stats
            print(f"\n=== Publishing Latency (microseconds) ===")
            print(f"Count: {stats['count']}")
            print(f"Min: {stats['min_us']:.1f}μs")
            print(f"Mean: {stats['mean_us']:.1f}μs")
            print(f"P50: {stats['p50_us']:.1f}μs")
            print(f"P95: {stats['p95_us']:.1f}μs")
            print(f"P99: {stats['p99_us']:.1f}μs")
            print(f"Max: {stats['max_us']:.1f}μs")

    def _publish_benchmark_result(self, test_type: str, test_name: str, result: BenchmarkResult):
        """Publish benchmark result as a metrics message."""
        try:
            benchmark_msg = {
                "type": "benchmark",
                "test_type": test_type,
                "test_name": test_name,
                "timestamp": time.time(),
                "config": {
                    "total_trades": result.total_trades,
                    "duration_seconds": result.duration_seconds
                },
                "total_trades": result.total_trades,
                "duration_seconds": result.duration_seconds,
                "trades_per_second": result.trades_per_second,
                "queue_full_count": result.queue_full_count,
                "error_count": result.error_count,
                "latency_stats": result.publish_stats or {}
            }

            print(f"Publishing benchmark message: {benchmark_msg}")
            publish_result = self.metrics_client.publish_json(benchmark_msg)
            if not publish_result.ok:
                print(f"Failed to publish benchmark metrics: {publish_result.error}")
            else:
                print(f"Successfully published benchmark metrics for {test_type}/{test_name}")

        except Exception as e:
            print(f"Error publishing benchmark metrics: {e}")

    def publish_status(self, test_name: str, status: str, message: str = ""):
        """Publish benchmark status update."""
        if not self.metrics_client:
            return

        try:
            status_msg = {
                "type": "benchmark_status",
                "status": status,
                "test_name": test_name,
                "timestamp": time.time(),
                "message": message
            }

            self.metrics_client.publish_json(status_msg)
        except Exception as e:
            print(f"Error publishing benchmark status: {e}")