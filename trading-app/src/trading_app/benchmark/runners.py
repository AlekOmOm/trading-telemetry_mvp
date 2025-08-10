#!/usr/bin/env python3
"""
Simple benchmark runners that publish results to metrics-sidecar.
These are designed to be called from Make commands.
"""

import sys
import time
from ..environment import get_trading_app_environment
from ..features.client import TradingClient
from .benchmark import PublishingBenchmark


def get_metrics_sidecar_addr() -> str:
    """Get the metrics-sidecar ZMQ address for benchmark messages."""
    # Benchmark messages go directly to metrics-sidecar, not through the app bridge
    return "tcp://127.0.0.1:5555"


def run_burst_benchmark(num_trades: int = 1000):
    """Run a burst benchmark test."""
    env = get_trading_app_environment()

    # Create separate clients for trading and metrics
    # Benchmark messages go directly to metrics-sidecar (port 5555)
    # Trading messages go through the app bridge (port 5556)
    metrics_sidecar_addr = get_metrics_sidecar_addr()
    metrics_client = TradingClient(metrics_sidecar_addr, enable_benchmarking=False)
    benchmark = PublishingBenchmark(env.APP_ZMQ_ADDR, metrics_client)
    
    print(f"Running burst benchmark: {num_trades} trades")
    print(f"Trading messages to: {env.APP_ZMQ_ADDR}")
    print(f"Benchmark metrics to: {metrics_sidecar_addr}")
    
    # Publish status
    test_name = f"burst_{num_trades}"
    benchmark.publish_status(test_name, "started", f"Starting burst test with {num_trades} trades")
    
    try:
        result = benchmark.run_burst_test(num_trades)
        benchmark.print_results(result)
        
        benchmark.publish_status(test_name, "completed", 
                               f"Completed: {result.trades_per_second:.1f} tps, P95: {result.publish_stats.get('p95_us', 0):.1f}μs")
        
        print(f"✅ Benchmark results published to metrics-sidecar")
        
    except Exception as e:
        benchmark.publish_status(test_name, "failed", str(e))
        print(f"❌ Benchmark failed: {e}")
        sys.exit(1)


def run_sustained_benchmark(duration: int = 30, rate: int = 100):
    """Run a sustained rate benchmark test."""
    env = get_trading_app_environment()

    # Create separate clients for trading and metrics
    # Benchmark messages go directly to metrics-sidecar (port 5555)
    metrics_sidecar_addr = get_metrics_sidecar_addr()
    metrics_client = TradingClient(metrics_sidecar_addr, enable_benchmarking=False)
    benchmark = PublishingBenchmark(env.APP_ZMQ_ADDR, metrics_client)

    print(f"Running sustained benchmark: {duration}s at {rate} trades/sec")
    print(f"Trading messages to: {env.APP_ZMQ_ADDR}")
    print(f"Benchmark metrics to: {metrics_sidecar_addr}")
    
    # Publish status
    test_name = f"sustained_{rate}tps"
    benchmark.publish_status(test_name, "started", f"Starting sustained test: {duration}s at {rate} tps")
    
    try:
        result = benchmark.run_sustained_test(duration, rate)
        benchmark.print_results(result)
        
        benchmark.publish_status(test_name, "completed",
                               f"Completed: {result.trades_per_second:.1f} tps, P95: {result.publish_stats.get('p95_us', 0):.1f}μs")
        
        print(f"✅ Benchmark results published to metrics-sidecar")
        
    except Exception as e:
        benchmark.publish_status(test_name, "failed", str(e))
        print(f"❌ Benchmark failed: {e}")
        sys.exit(1)


def run_comprehensive_benchmark():
    """Run a comprehensive benchmark suite."""
    env = get_trading_app_environment()

    # Create separate clients for trading and metrics
    # Benchmark messages go directly to metrics-sidecar (port 5555)
    metrics_sidecar_addr = get_metrics_sidecar_addr()
    metrics_client = TradingClient(metrics_sidecar_addr, enable_benchmarking=False)
    benchmark = PublishingBenchmark(env.APP_ZMQ_ADDR, metrics_client)

    print("Running comprehensive benchmark suite")
    print(f"Trading messages to: {env.APP_ZMQ_ADDR}")
    print(f"Benchmark metrics to: {metrics_sidecar_addr}")
    
    tests = [
        ("Small Burst", lambda: benchmark.run_burst_test(100)),
        ("Medium Burst", lambda: benchmark.run_burst_test(1000)),
        ("Large Burst", lambda: benchmark.run_burst_test(5000)),
        ("Sustained Low", lambda: benchmark.run_sustained_test(10, 50)),
        ("Sustained Medium", lambda: benchmark.run_sustained_test(10, 200)),
        ("Sustained High", lambda: benchmark.run_sustained_test(10, 500)),
    ]
    
    benchmark.publish_status("comprehensive", "started", "Starting comprehensive benchmark suite")
    
    try:
        for i, (name, test_func) in enumerate(tests, 1):
            print(f"\n{i}. {name}...")
            benchmark.publish_status("comprehensive", "running", f"Running {name}")
            
            result = test_func()
            benchmark.print_results(result)
            
            if i < len(tests):  # Brief pause between tests
                time.sleep(1)
        
        benchmark.publish_status("comprehensive", "completed", "All tests completed successfully")
        print(f"\n✅ Comprehensive benchmark completed - results published to metrics-sidecar")
        
    except Exception as e:
        benchmark.publish_status("comprehensive", "failed", str(e))
        print(f"❌ Comprehensive benchmark failed: {e}")
        sys.exit(1)


def run_latency_profile(max_rate: int = 1000, step: int = 100):
    """Run latency profiling under increasing load."""
    env = get_trading_app_environment()

    # Create separate clients for trading and metrics
    # Benchmark messages go directly to metrics-sidecar (port 5555)
    metrics_sidecar_addr = get_metrics_sidecar_addr()
    metrics_client = TradingClient(metrics_sidecar_addr, enable_benchmarking=False)
    benchmark = PublishingBenchmark(env.APP_ZMQ_ADDR, metrics_client)

    print(f"Running latency profile: 0 to {max_rate} trades/sec (step: {step})")
    print(f"Trading messages to: {env.APP_ZMQ_ADDR}")
    print(f"Benchmark metrics to: {metrics_sidecar_addr}")
    
    benchmark.publish_status("profile", "started", f"Starting latency profile: max_rate={max_rate}, step={step}")
    
    try:
        for rate in range(step, max_rate + 1, step):
            print(f"Testing {rate} trades/sec...")
            benchmark.publish_status("profile", "running", f"Testing {rate} trades/sec")
            
            result = benchmark.run_sustained_test(duration_seconds=5, trades_per_second=rate)
            
            # Brief pause between tests
            time.sleep(0.5)
        
        benchmark.publish_status("profile", "completed", f"Profile completed up to {max_rate} trades/sec")
        print(f"✅ Latency profile completed - results published to metrics-sidecar")
        
    except Exception as e:
        benchmark.publish_status("profile", "failed", str(e))
        print(f"❌ Latency profile failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m trading_app.benchmark.runners <command> [args...]")
        print("Commands:")
        print("  burst [num_trades]")
        print("  sustained [duration] [rate]")
        print("  comprehensive")
        print("  profile [max_rate] [step]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "burst":
        num_trades = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        run_burst_benchmark(num_trades)
    elif command == "sustained":
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        rate = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        run_sustained_benchmark(duration, rate)
    elif command == "comprehensive":
        run_comprehensive_benchmark()
    elif command == "profile":
        max_rate = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        step = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        run_latency_profile(max_rate, step)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
