"""
Advanced latency analysis tools for ZMQ publishing benchmarks.
"""

from __future__ import annotations

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from .benchmark import BenchmarkResult, PublishingBenchmark


@dataclass
class LatencyProfile:
    """Detailed latency profile for a benchmark run."""
    timestamp: float
    test_type: str
    config: Dict[str, Any]
    results: BenchmarkResult
    environment: Dict[str, str]


class LatencyAnalyzer:
    """Advanced analysis of publishing latency patterns."""
    
    def __init__(self, zmq_addr: str):
        self.benchmark = PublishingBenchmark(zmq_addr)
        self.profiles: List[LatencyProfile] = []
    
    def profile_latency_under_load(self, max_rate: int = 1000, step: int = 100) -> List[LatencyProfile]:
        """Profile latency characteristics under increasing load."""
        profiles = []
        
        print(f"Profiling latency from 0 to {max_rate} trades/sec (step: {step})")
        
        for rate in range(step, max_rate + 1, step):
            print(f"Testing {rate} trades/sec...")
            
            result = self.benchmark.run_sustained_test(
                duration_seconds=5,
                trades_per_second=rate
            )
            
            profile = LatencyProfile(
                timestamp=time.time(),
                test_type="load_profile",
                config={"rate": rate, "duration": 5},
                results=result,
                environment={"zmq_addr": self.benchmark.client.addr}
            )
            
            profiles.append(profile)
            self.profiles.append(profile)
            
            # Brief pause between tests
            time.sleep(0.5)
        
        return profiles
    
    def analyze_latency_degradation(self, profiles: List[LatencyProfile]) -> Dict[str, Any]:
        """Analyze how latency degrades with increasing load."""
        if not profiles:
            return {}
        
        rates = []
        p50_latencies = []
        p95_latencies = []
        p99_latencies = []
        queue_full_rates = []
        
        for profile in profiles:
            if profile.results.publish_stats:
                stats = profile.results.publish_stats
                rates.append(profile.config["rate"])
                p50_latencies.append(stats.get("p50_us", 0))
                p95_latencies.append(stats.get("p95_us", 0))
                p99_latencies.append(stats.get("p99_us", 0))
                
                # Calculate queue full rate
                total_trades = profile.results.total_trades
                queue_full_rate = (profile.results.queue_full_count / total_trades) * 100 if total_trades > 0 else 0
                queue_full_rates.append(queue_full_rate)
        
        # Find degradation points
        degradation_analysis = {
            "rates": rates,
            "p50_latencies_us": p50_latencies,
            "p95_latencies_us": p95_latencies,
            "p99_latencies_us": p99_latencies,
            "queue_full_rates_pct": queue_full_rates,
        }
        
        # Find where latency starts to degrade significantly
        if len(p95_latencies) >= 2:
            baseline_p95 = p95_latencies[0]
            for i, latency in enumerate(p95_latencies):
                if latency > baseline_p95 * 2:  # 2x degradation
                    degradation_analysis["p95_degradation_rate"] = rates[i]
                    break
        
        # Find where queue saturation begins
        for i, queue_rate in enumerate(queue_full_rates):
            if queue_rate > 1.0:  # 1% queue full rate
                degradation_analysis["queue_saturation_rate"] = rates[i]
                break
        
        return degradation_analysis
    
    def save_profiles(self, filepath: str):
        """Save latency profiles to JSON file."""
        data = []
        for profile in self.profiles:
            profile_dict = asdict(profile)
            # Convert BenchmarkResult to dict
            profile_dict["results"] = asdict(profile.results)
            data.append(profile_dict)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved {len(self.profiles)} profiles to {filepath}")
    
    def load_profiles(self, filepath: str):
        """Load latency profiles from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.profiles = []
        for item in data:
            # Reconstruct BenchmarkResult
            result_data = item["results"]
            result = BenchmarkResult(**result_data)
            
            profile = LatencyProfile(
                timestamp=item["timestamp"],
                test_type=item["test_type"],
                config=item["config"],
                results=result,
                environment=item["environment"]
            )
            self.profiles.append(profile)
        
        print(f"Loaded {len(self.profiles)} profiles from {filepath}")
    
    def print_degradation_analysis(self, analysis: Dict[str, Any]):
        """Print latency degradation analysis."""
        print("\n=== LATENCY DEGRADATION ANALYSIS ===")
        
        if "p95_degradation_rate" in analysis:
            print(f"P95 latency degrades significantly at: {analysis['p95_degradation_rate']} trades/sec")
        
        if "queue_saturation_rate" in analysis:
            print(f"Queue saturation begins at: {analysis['queue_saturation_rate']} trades/sec")
        
        rates = analysis.get("rates", [])
        p95_latencies = analysis.get("p95_latencies_us", [])
        
        if rates and p95_latencies:
            print(f"\nLatency progression:")
            for rate, p95 in zip(rates, p95_latencies):
                queue_full = analysis["queue_full_rates_pct"][rates.index(rate)]
                print(f"  {rate:4d} trades/sec: P95={p95:6.1f}μs, Queue full={queue_full:4.1f}%")
