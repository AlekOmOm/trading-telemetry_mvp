# ZMQ Publishing Latency Benchmarking

This package provides comprehensive tools for measuring and analyzing the latency cost of ZMQ publishing in trading applications. The key insight is to measure the **synchronous cost** of the `socket.send_json()` call, which is what actually blocks the trading bot's execution thread.

**The benchmarking system is fully integrated with our observability infrastructure** - benchmark results are published as metrics to the metrics-sidecar, visualized in Grafana dashboards, and available for historical analysis and alerting through Prometheus.

## Key Features

- **Nanosecond Precision**: Uses `perf_counter_ns()` for accurate sub-microsecond measurements
- **Production Ready**: Fast path with minimal overhead when benchmarking is disabled
- **Queue Saturation Detection**: Identifies when ZMQ queues are full (critical for trading bots)
- **Comprehensive Statistics**: P50, P95, P99 latencies to understand tail behavior
- **Metrics Integration**: Results published to metrics-sidecar for persistence and visualization
- **Grafana Dashboards**: Dedicated dashboard for benchmark visualization and analysis
- **Self-Observable**: The benchmarking system monitors itself through the same pipeline
- **Historical Analysis**: All results stored in Prometheus for trend analysis and alerting

## Quick Start

All benchmarking is done through simple Make commands. Results are automatically published to the metrics-sidecar and visualized in Grafana.

### Basic Benchmarking

```bash
# Quick burst test (1000 trades)
make benchmark-burst

# Large burst test (5000 trades)
make benchmark-burst-large

# Sustained rate test (30s at 200 tps)
make benchmark-sustained

# High-rate sustained test (30s at 500 tps)
make benchmark-sustained-high
```

### Advanced Benchmarking

```bash
# Run comprehensive benchmark suite
make benchmark-comprehensive

# Profile latency under increasing load (up to 1000 tps)
make benchmark-profile

# Start benchmark system self-monitoring
make benchmark-monitor
```

### Visualization

```bash
# Open the benchmark dashboard in Grafana
make benchmark-dashboard

# See all available benchmark commands
make benchmark-help
```

Create a dedicated benchmarking module:

````python path=trading-app/src/trading_app/features/benchmark.py mode=EDIT
from __future__ import annotations

import time
import statistics
import threading
from typing import List, Dict, Any
from dataclasses import dataclass

from .client import TradingClient
from .models import TradeMsg


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
    
    def __init__(self, zmq_addr: str):
        self.client = TradingClient(zmq_addr, enable_benchmarking=True)
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
        
        return BenchmarkResult(
            total_trades=trades_sent,
            duration_seconds=actual_duration,
            trades_per_second=trades_sent / actual_duration,
            publish_stats=self.client.get_latency_stats(),
            queue_full_count=queue_full_count,
            error_count=error_count
        )
    
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
````

Create a benchmark runner script:

````python path=trading-app/src/trading_app/benchmark_runner.py mode=EDIT
#!/usr/bin/env python3
"""
Benchmark the publishing latency of the trading bot.

Usage:
    python -m trading_app.benchmark_runner --burst 1000
    python -m trading_app.benchmark_runner --sustained 10 --rate 500
"""

import argparse
import sys
from trading_app.environment import get_trading_app_environment
from trading_app.features.benchmark import PublishingBenchmark


def main():
    parser = argparse.ArgumentParser(description="Benchmark ZMQ publishing latency")
    parser.add_argument("--burst", type=int, help="Run burst test with N trades")
    parser.add_argument("--sustained", type=int, help="Run sustained test for N seconds")
    parser.add_argument("--rate", type=int, default=100, help="Trades per second for sustained test")
    
    args = parser.parse_args()
    
    if not args.burst and not args.sustained:
        print("Must specify either --burst or --sustained test")
        sys.exit(1)
    
    env = get_trading_app_environment()
    benchmark = PublishingBenchmark(env.APP_ZMQ_ADDR)
    
    print(f"Benchmarking against: {env.APP_ZMQ_ADDR}")
    print("Make sure the metrics-sidecar is running to avoid queue saturation!")
    
    if args.burst:
        print(f"\nRunning burst test: {args.burst} trades...")
        result = benchmark.run_burst_test(args.burst)
        benchmark.print_results(result)
    
    if args.sustained:
        print(f"\nRunning sustained test: {args.sustained}s at {args.rate} trades/sec...")
        result = benchmark.run_sustained_test(args.sustained, args.rate)
        benchmark.print_results(result)


if __name__ == "__main__":
    main()
````

## Key Benefits of This Approach:

1. **Measures Real Cost**: Times the actual `socket.send_string()` call that blocks the trading bot
2. **Nanosecond Precision**: Uses `perf_counter_ns()` for accurate sub-microsecond measurements  
3. **Production Ready**: Fast path with minimal overhead when benchmarking is disabled
4. **Queue Saturation Detection**: Identifies when ZMQ queues are full (critical for trading bots)
5. **Comprehensive Stats**: P50, P95, P99 latencies to understand tail behavior

## Usage:

```bash
# Test burst publishing (simulates order flurry)
python -m trading_app.benchmark_runner --burst 1000

# Test sustained rate (simulates normal trading)  
python -m trading_app.benchmark_runner --sustained 30 --rate 200
```

## Self-Observability

The benchmarking system creates a feedback loop by monitoring itself through the same metrics pipeline it's testing:

```bash
# Start self-monitoring (runs continuously)
make benchmark-monitor
```

This publishes benchmark system health metrics including:
- Publishing latency of the benchmark system itself
- Alert notifications when benchmark performance degrades
- Health status updates and system diagnostics

The self-monitoring data appears in the same Grafana dashboard, allowing you to:
- Monitor the health of your benchmarking infrastructure
- Detect when the benchmark system itself is impacting results
- Set up alerts for benchmark system degradation
- Analyze the overhead of the observability pipeline

## Integration with Observability Stack

### Metrics Published

The benchmark system publishes these metrics to Prometheus:

- `benchmark_tests_total` - Total number of benchmark tests run
- `benchmark_trades_published_total` - Total trades published during benchmarks
- `benchmark_throughput_trades_per_second` - Benchmark throughput
- `benchmark_latency_*_microseconds` - Latency percentiles (min, mean, p50, p95, p99, max)
- `benchmark_queue_full_events_total` - Queue saturation events
- `benchmark_errors_total` - Benchmark errors

### Grafana Dashboard

The dedicated benchmark dashboard (`benchmark-telemetry`) includes:
- Real-time latency metrics (P95, P99) with color-coded thresholds
- Throughput trends over time
- Queue saturation indicators
- Error rate monitoring
- Latency distribution visualization
- Recent benchmark results table

### Historical Analysis

All benchmark results are stored in Prometheus, enabling:
- Long-term trend analysis of publishing performance
- Alerting on benchmark performance degradation
- Correlation with system changes and deployments
- Performance regression detection

This gives you precise measurements of the **synchronous cost** that your trading bot pays for each metrics publish, with full observability and historical tracking.
