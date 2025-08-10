#!/usr/bin/env python3
"""
Self-monitoring for the benchmarking system.

This creates a feedback loop where the benchmarking infrastructure monitors itself
through the same metrics pipeline it's testing.
"""

import time
import threading
from typing import Optional
from ..environment import get_trading_app_environment
from ..features.client import TradingClient
from .monitor import LatencyMonitor


def get_metrics_sidecar_addr() -> str:
    """Get the metrics-sidecar ZMQ address for benchmark messages."""
    # Benchmark messages go directly to metrics-sidecar, not through the app bridge
    return "tcp://127.0.0.1:5555"


class BenchmarkSelfMonitor:
    """Self-monitoring system for benchmark infrastructure."""
    
    def __init__(self):
        self.env = get_trading_app_environment()
        # Self-monitor publishes directly to metrics-sidecar (port 5555)
        self.metrics_sidecar_addr = get_metrics_sidecar_addr()
        self.metrics_client = TradingClient(self.metrics_sidecar_addr, enable_benchmarking=True)
        self.monitor = LatencyMonitor(self.metrics_client)
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Setup alert callbacks
        self.monitor.add_alert_callback(self._handle_benchmark_alert)
        
        # Set thresholds for benchmark system health
        self.monitor.p95_threshold_us = 1000.0   # 1ms for P95
        self.monitor.p99_threshold_us = 5000.0   # 5ms for P99
        self.monitor.mean_threshold_us = 500.0   # 0.5ms for mean
    
    def _handle_benchmark_alert(self, alert: str):
        """Handle alerts from the benchmark monitoring system."""
        print(f"🚨 BENCHMARK SYSTEM ALERT: {alert}")
        
        # Publish alert as a benchmark status message
        try:
            alert_msg = {
                "type": "benchmark_status",
                "status": "alert",
                "test_name": "self_monitor",
                "timestamp": time.time(),
                "message": f"Benchmark system alert: {alert}"
            }
            self.metrics_client.publish_json(alert_msg)
        except Exception as e:
            print(f"Failed to publish alert: {e}")
    
    def start_monitoring(self, interval_seconds: float = 5.0):
        """Start self-monitoring of the benchmark system."""
        if self.running:
            return
        
        print("Starting benchmark system self-monitoring...")
        print(f"Monitoring interval: {interval_seconds}s")
        print(f"Publishing alerts to: {self.metrics_sidecar_addr}")
        
        # Publish startup status
        startup_msg = {
            "type": "benchmark_status",
            "status": "started",
            "test_name": "self_monitor",
            "timestamp": time.time(),
            "message": "Benchmark self-monitoring started"
        }
        self.metrics_client.publish_json(startup_msg)
        
        self.monitor.start_monitoring(interval_seconds)
        self.running = True
        
        # Start periodic health reporting
        self.monitor_thread = threading.Thread(
            target=self._health_reporting_loop,
            args=(30.0,),  # Report health every 30 seconds
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop self-monitoring."""
        if not self.running:
            return
        
        print("Stopping benchmark system self-monitoring...")
        
        # Publish shutdown status
        shutdown_msg = {
            "type": "benchmark_status",
            "status": "completed",
            "test_name": "self_monitor",
            "timestamp": time.time(),
            "message": "Benchmark self-monitoring stopped"
        }
        self.metrics_client.publish_json(shutdown_msg)
        
        self.running = False
        self.monitor.stop_monitoring()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
    
    def _health_reporting_loop(self, interval_seconds: float):
        """Periodic health reporting loop."""
        while self.running:
            try:
                # Get current stats
                snapshot = self.monitor.get_current_stats()
                if snapshot:
                    # Publish health status
                    health_msg = {
                        "type": "benchmark_status",
                        "status": "running",
                        "test_name": "self_monitor",
                        "timestamp": time.time(),
                        "message": f"Health: P95={snapshot.p95_us:.1f}μs, samples={snapshot.count}"
                    }
                    self.metrics_client.publish_json(health_msg)
                
                time.sleep(interval_seconds)
            except Exception as e:
                print(f"Health reporting error: {e}")
                time.sleep(interval_seconds)
    
    def get_system_health(self) -> dict:
        """Get current benchmark system health metrics."""
        snapshot = self.monitor.get_current_stats()
        if not snapshot:
            return {"status": "no_data", "message": "No latency data available"}
        
        # Determine health status
        status = "healthy"
        issues = []
        
        if snapshot.p95_us > self.monitor.p95_threshold_us:
            status = "degraded"
            issues.append(f"P95 latency high: {snapshot.p95_us:.1f}μs")
        
        if snapshot.p99_us > self.monitor.p99_threshold_us:
            status = "degraded"
            issues.append(f"P99 latency high: {snapshot.p99_us:.1f}μs")
        
        if snapshot.mean_us > self.monitor.mean_threshold_us:
            status = "degraded"
            issues.append(f"Mean latency high: {snapshot.mean_us:.1f}μs")
        
        return {
            "status": status,
            "timestamp": snapshot.timestamp,
            "sample_count": snapshot.count,
            "latency": {
                "min_us": snapshot.min_us,
                "mean_us": snapshot.mean_us,
                "p95_us": snapshot.p95_us,
                "p99_us": snapshot.p99_us,
                "max_us": snapshot.max_us
            },
            "issues": issues,
            "thresholds": {
                "p95_threshold_us": self.monitor.p95_threshold_us,
                "p99_threshold_us": self.monitor.p99_threshold_us,
                "mean_threshold_us": self.monitor.mean_threshold_us
            }
        }
    
    def print_health_status(self):
        """Print current health status to console."""
        health = self.get_system_health()
        
        print(f"\n=== BENCHMARK SYSTEM HEALTH ===")
        print(f"Status: {health['status'].upper()}")
        
        if health['status'] == 'no_data':
            print(f"Message: {health['message']}")
            return
        
        print(f"Timestamp: {time.strftime('%H:%M:%S', time.localtime(health['timestamp']))}")
        print(f"Sample count: {health['sample_count']}")
        
        latency = health['latency']
        print(f"Latency: min={latency['min_us']:.1f}μs, mean={latency['mean_us']:.1f}μs, "
              f"p95={latency['p95_us']:.1f}μs, p99={latency['p99_us']:.1f}μs, max={latency['max_us']:.1f}μs")
        
        if health['issues']:
            print(f"Issues:")
            for issue in health['issues']:
                print(f"  ⚠️  {issue}")
        else:
            print("✅ All metrics within thresholds")


def main():
    """Run benchmark self-monitoring."""
    monitor = BenchmarkSelfMonitor()
    
    try:
        monitor.start_monitoring(interval_seconds=2.0)
        
        print("\nBenchmark self-monitoring active. Press Ctrl+C to stop.")
        print("This creates a feedback loop - the benchmark system monitors itself!")
        
        while True:
            time.sleep(10)
            monitor.print_health_status()
            
    except KeyboardInterrupt:
        print("\nShutting down benchmark self-monitoring...")
    finally:
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()
