#!/usr/bin/env python3
"""
Test script to verify benchmark metrics are being published correctly.
"""

import time
import requests
from ..features.client import TradingClient


def test_benchmark_metrics_publishing():
    """Test that benchmark metrics are published and appear in /metrics endpoint."""
    
    print("Testing benchmark metrics publishing...")
    
    # Create client to publish directly to metrics-sidecar
    metrics_client = TradingClient("tcp://127.0.0.1:5555", enable_benchmarking=False)
    
    # Create a test benchmark message
    test_msg = {
        "type": "benchmark",
        "test_type": "burst",
        "test_name": "test_metrics_publishing",
        "timestamp": time.time(),
        "config": {"num_trades": 100},
        "total_trades": 100,
        "duration_seconds": 0.5,
        "trades_per_second": 200.0,
        "queue_full_count": 0,
        "error_count": 0,
        "latency_stats": {
            "count": 100,
            "min_us": 10.5,
            "mean_us": 25.3,
            "p50_us": 23.1,
            "p95_us": 45.7,
            "p99_us": 67.2,
            "max_us": 89.4
        }
    }
    
    print(f"Publishing test benchmark message: {test_msg}")
    
    # Publish the message
    result = metrics_client.publish_json(test_msg)
    if not result.ok:
        print(f"❌ Failed to publish test message: {result.error}")
        return False
    
    print("✅ Test message published successfully")
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Check if metrics appear in /metrics endpoint
    try:
        response = requests.get("http://localhost:8001/metrics", timeout=5)
        if response.status_code != 200:
            print(f"❌ Failed to fetch /metrics endpoint: {response.status_code}")
            return False
        
        metrics_text = response.text
        print(f"Fetched metrics from /metrics endpoint ({len(metrics_text)} chars)")
        
        # Check for benchmark metrics
        benchmark_metrics = [
            "benchmark_tests_total",
            "benchmark_latency_p95_microseconds",
            "benchmark_throughput_trades_per_second"
        ]
        
        found_metrics = []
        missing_metrics = []
        
        for metric in benchmark_metrics:
            if metric in metrics_text:
                found_metrics.append(metric)
                print(f"✅ Found metric: {metric}")
            else:
                missing_metrics.append(metric)
                print(f"❌ Missing metric: {metric}")
        
        if missing_metrics:
            print(f"\n❌ Missing {len(missing_metrics)} benchmark metrics")
            print("Available metrics:")
            for line in metrics_text.split('\n'):
                if line.startswith('# HELP') or line.startswith('# TYPE'):
                    print(f"  {line}")
            return False
        else:
            print(f"\n✅ All {len(found_metrics)} benchmark metrics found!")
            return True
            
    except requests.RequestException as e:
        print(f"❌ Failed to connect to metrics endpoint: {e}")
        return False


def test_status_message():
    """Test publishing a benchmark status message."""
    
    print("\nTesting benchmark status message...")
    
    metrics_client = TradingClient("tcp://127.0.0.1:5555", enable_benchmarking=False)
    
    status_msg = {
        "type": "benchmark_status",
        "status": "started",
        "test_name": "test_status",
        "timestamp": time.time(),
        "message": "Test status message"
    }
    
    print(f"Publishing test status message: {status_msg}")
    
    result = metrics_client.publish_json(status_msg)
    if not result.ok:
        print(f"❌ Failed to publish status message: {result.error}")
        return False
    
    print("✅ Status message published successfully")
    return True


if __name__ == "__main__":
    print("Benchmark Metrics Publishing Test")
    print("=" * 40)
    
    print("Make sure the metrics-sidecar is running on localhost:8001")
    print("Run: make sidecar-up")
    print()
    
    # Test benchmark metrics
    benchmark_success = test_benchmark_metrics_publishing()
    
    # Test status messages  
    status_success = test_status_message()
    
    print("\n" + "=" * 40)
    if benchmark_success and status_success:
        print("✅ All tests passed! Benchmark metrics are working correctly.")
    else:
        print("❌ Some tests failed. Check the metrics-sidecar logs for details.")
        print("Troubleshooting:")
        print("1. Ensure metrics-sidecar is running: make sidecar-up")
        print("2. Check metrics-sidecar logs for error messages")
        print("3. Verify ZMQ port 5555 is accessible")
