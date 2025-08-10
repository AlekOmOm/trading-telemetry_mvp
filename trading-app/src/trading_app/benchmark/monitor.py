"""
Real-time performance monitoring for ZMQ publishing latency.
"""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import deque

from ..features.client import TradingClient


@dataclass
class LatencySnapshot:
    """Point-in-time latency statistics."""
    timestamp: float
    count: int
    min_us: float
    max_us: float
    mean_us: float
    p95_us: float
    p99_us: float


class LatencyMonitor:
    """Real-time latency monitoring with alerting."""
    
    def __init__(self, client: TradingClient, window_seconds: int = 60):
        self.client = client
        self.window_seconds = window_seconds
        self.snapshots: deque = deque(maxlen=1000)  # Keep last 1000 snapshots
        self.alerts: List[str] = []
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Alert thresholds (microseconds)
        self.p95_threshold_us = 1000.0  # 1ms
        self.p99_threshold_us = 5000.0  # 5ms
        self.mean_threshold_us = 500.0  # 0.5ms
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[str], None]] = []
    
    def add_alert_callback(self, callback: Callable[[str], None]):
        """Add callback function for alerts."""
        self.alert_callbacks.append(callback)
    
    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start real-time monitoring in background thread."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        print(f"Started latency monitoring (interval: {interval_seconds}s)")
    
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("Stopped latency monitoring")
    
    def _monitor_loop(self, interval_seconds: float):
        """Main monitoring loop."""
        while self.running:
            try:
                snapshot = self._take_snapshot()
                if snapshot:
                    self.snapshots.append(snapshot)
                    self._check_alerts(snapshot)
                
                time.sleep(interval_seconds)
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(interval_seconds)
    
    def _take_snapshot(self) -> Optional[LatencySnapshot]:
        """Take a latency snapshot."""
        stats = self.client.get_latency_stats()
        if not stats:
            return None
        
        return LatencySnapshot(
            timestamp=time.time(),
            count=stats["count"],
            min_us=stats["min_us"],
            max_us=stats["max_us"],
            mean_us=stats["mean_us"],
            p95_us=stats["p95_us"],
            p99_us=stats["p99_us"]
        )
    
    def _check_alerts(self, snapshot: LatencySnapshot):
        """Check for alert conditions."""
        alerts = []
        
        if snapshot.p95_us > self.p95_threshold_us:
            alerts.append(f"P95 latency high: {snapshot.p95_us:.1f}μs > {self.p95_threshold_us:.1f}μs")
        
        if snapshot.p99_us > self.p99_threshold_us:
            alerts.append(f"P99 latency high: {snapshot.p99_us:.1f}μs > {self.p99_threshold_us:.1f}μs")
        
        if snapshot.mean_us > self.mean_threshold_us:
            alerts.append(f"Mean latency high: {snapshot.mean_us:.1f}μs > {self.mean_threshold_us:.1f}μs")
        
        # Fire alerts
        for alert in alerts:
            self.alerts.append(f"{time.strftime('%H:%M:%S')}: {alert}")
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"Alert callback error: {e}")
    
    def get_current_stats(self) -> Optional[LatencySnapshot]:
        """Get current latency statistics."""
        return self._take_snapshot()
    
    def get_recent_snapshots(self, seconds: int = 60) -> List[LatencySnapshot]:
        """Get snapshots from the last N seconds."""
        cutoff = time.time() - seconds
        return [s for s in self.snapshots if s.timestamp >= cutoff]
    
    def print_current_status(self):
        """Print current latency status."""
        snapshot = self.get_current_stats()
        if not snapshot:
            print("No latency data available")
            return
        
        print(f"\n=== CURRENT LATENCY STATUS ===")
        print(f"Timestamp: {time.strftime('%H:%M:%S', time.localtime(snapshot.timestamp))}")
        print(f"Sample count: {snapshot.count}")
        print(f"Min: {snapshot.min_us:.1f}μs")
        print(f"Mean: {snapshot.mean_us:.1f}μs")
        print(f"P95: {snapshot.p95_us:.1f}μs")
        print(f"P99: {snapshot.p99_us:.1f}μs")
        print(f"Max: {snapshot.max_us:.1f}μs")
        
        # Show recent alerts
        recent_alerts = self.alerts[-5:]  # Last 5 alerts
        if recent_alerts:
            print(f"\n=== RECENT ALERTS ===")
            for alert in recent_alerts:
                print(f"  {alert}")
    
    def print_trend_analysis(self, minutes: int = 5):
        """Print trend analysis for the last N minutes."""
        snapshots = self.get_recent_snapshots(minutes * 60)
        if len(snapshots) < 2:
            print("Insufficient data for trend analysis")
            return
        
        # Calculate trends
        first = snapshots[0]
        last = snapshots[-1]
        
        p95_trend = last.p95_us - first.p95_us
        mean_trend = last.mean_us - first.mean_us
        
        print(f"\n=== TREND ANALYSIS ({minutes} minutes) ===")
        print(f"P95 trend: {p95_trend:+.1f}μs")
        print(f"Mean trend: {mean_trend:+.1f}μs")
        print(f"Samples: {len(snapshots)}")
        
        if abs(p95_trend) > 100:  # Significant change
            direction = "increasing" if p95_trend > 0 else "decreasing"
            print(f"⚠️  P95 latency is {direction} significantly")
