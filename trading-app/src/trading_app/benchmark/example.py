#!/usr/bin/env python3
"""
Example usage of the benchmarking tools.

This script demonstrates how to use the benchmarking components
programmatically in your own applications.
"""

import time
from ..environment import get_trading_app_environment
from .benchmark import PublishingBenchmark
from .analyzer import LatencyAnalyzer
from .monitor import LatencyMonitor
from ..features.client import TradingClient


def example_basic_benchmark():
    """Example: Basic benchmarking."""
    print("=== BASIC BENCHMARK EXAMPLE ===")
    
    env = get_trading_app_environment()
    benchmark = PublishingBenchmark(env.APP_ZMQ_ADDR)
    
    # Run a quick burst test
    result = benchmark.run_burst_test(num_trades=500, qty=1.0)
    benchmark.print_results(result)
    
    # Check if latency is acceptable for trading
    if result.publish_stats:
        p95_us = result.publish_stats.get("p95_us", 0)
        if p95_us > 1000:  # 1ms threshold
            print(f"⚠️  WARNING: P95 latency ({p95_us:.1f}μs) exceeds 1ms threshold")
        else:
            print(f"✅ P95 latency ({p95_us:.1f}μs) is acceptable for trading")


def example_latency_profiling():
    """Example: Latency profiling under load."""
    print("\n=== LATENCY PROFILING EXAMPLE ===")
    
    env = get_trading_app_environment()
    analyzer = LatencyAnalyzer(env.APP_ZMQ_ADDR)
    
    # Profile latency from 100 to 500 trades/sec
    profiles = analyzer.profile_latency_under_load(max_rate=500, step=100)
    
    # Analyze degradation patterns
    analysis = analyzer.analyze_latency_degradation(profiles)
    analyzer.print_degradation_analysis(analysis)
    
    # Save results for later analysis
    analyzer.save_profiles("example_latency_profiles.json")


def example_real_time_monitoring():
    """Example: Real-time monitoring with custom alerts."""
    print("\n=== REAL-TIME MONITORING EXAMPLE ===")
    
    env = get_trading_app_environment()
    client = TradingClient(env.APP_ZMQ_ADDR, enable_benchmarking=True)
    monitor = LatencyMonitor(client)
    
    # Custom alert handler
    def trading_alert(alert: str):
        print(f"🚨 TRADING ALERT: {alert}")
        # In real application, you might:
        # - Log to trading system
        # - Send notification to traders
        # - Trigger circuit breaker
    
    monitor.add_alert_callback(trading_alert)
    
    # Set custom thresholds for trading
    monitor.p95_threshold_us = 500.0   # 0.5ms for P95
    monitor.p99_threshold_us = 2000.0  # 2ms for P99
    monitor.mean_threshold_us = 200.0  # 0.2ms for mean
    
    print("Starting 30-second monitoring demo...")
    monitor.start_monitoring(interval_seconds=2.0)
    
    try:
        # Simulate some trading activity
        for i in range(15):  # 30 seconds total
            # In real app, this would be your actual trading logic
            time.sleep(2)
            
            # Print current status every 10 seconds
            if i % 5 == 0:
                monitor.print_current_status()
    
    finally:
        monitor.stop_monitoring()


def example_integration_with_trading_bot():
    """Example: Integration with trading bot."""
    print("\n=== TRADING BOT INTEGRATION EXAMPLE ===")
    
    env = get_trading_app_environment()
    
    # Create client with benchmarking enabled for development/testing
    # In production, you'd set enable_benchmarking=False for minimal overhead
    client = TradingClient(env.APP_ZMQ_ADDR, enable_benchmarking=True)
    
    # Simulate trading activity
    print("Simulating trading activity...")
    
    for i in range(100):
        # Simulate trade execution
        trade_data = {
            "type": "trade",
            "side": "buy" if i % 2 == 0 else "sell",
            "qty": 1.0,
            "ts": time.time()
        }
        
        # Publish trade (this is what gets benchmarked)
        result = client.publish_json(trade_data)
        
        if not result.ok:
            print(f"Failed to publish trade {i}: {result.error}")
        
        # Small delay to simulate realistic trading pace
        time.sleep(0.01)  # 100 trades/sec
    
    # Get latency statistics
    stats = client.get_latency_stats()
    if stats:
        print(f"\nTrading session latency stats:")
        print(f"  Trades published: {stats['count']}")
        print(f"  Mean latency: {stats['mean_us']:.1f}μs")
        print(f"  P95 latency: {stats['p95_us']:.1f}μs")
        print(f"  P99 latency: {stats['p99_us']:.1f}μs")
        
        # Check if performance is acceptable
        if stats['p95_us'] < 500:  # 0.5ms threshold
            print("✅ Publishing latency is acceptable for high-frequency trading")
        else:
            print("⚠️  Publishing latency may impact trading performance")


def main():
    """Run all examples."""
    print("ZMQ Publishing Latency Benchmarking Examples")
    print("=" * 50)
    
    try:
        example_basic_benchmark()
        time.sleep(1)
        
        example_latency_profiling()
        time.sleep(1)
        
        example_real_time_monitoring()
        time.sleep(1)
        
        example_integration_with_trading_bot()
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Example error: {e}")
    
    print("\n" + "=" * 50)
    print("Examples complete!")


if __name__ == "__main__":
    main()
