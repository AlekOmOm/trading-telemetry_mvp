"""
Benchmarking tools for measuring ZMQ publishing latency in trading applications.

This package provides comprehensive tools to measure the actual cost of publishing
metrics from within the trading bot itself, ensuring minimal impact on trading performance.

The benchmarking system is integrated with our observability infrastructure:
- Benchmark results are published as metrics to the metrics-sidecar
- Results are visualized in Grafana dashboards
- Historical analysis and alerting are available through Prometheus

Components:
- PublishingBenchmark: Core benchmarking functionality with metrics publishing
- LatencyAnalyzer: Advanced latency analysis and profiling
- LatencyMonitor: Real-time latency monitoring with alerting

Usage via Make commands:
    make benchmark-burst              # Quick burst test
    make benchmark-sustained          # Sustained rate test
    make benchmark-comprehensive      # Full benchmark suite
    make benchmark-profile            # Latency profiling
    make benchmark-dashboard          # Open Grafana dashboard
"""

from .benchmark import PublishingBenchmark, BenchmarkResult
from .analyzer import LatencyAnalyzer, LatencyProfile
from .monitor import LatencyMonitor, LatencySnapshot

__all__ = [
    "PublishingBenchmark",
    "BenchmarkResult",
    "LatencyAnalyzer",
    "LatencyProfile",
    "LatencyMonitor",
    "LatencySnapshot"
]
