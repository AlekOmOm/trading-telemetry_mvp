from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Optional

import zmq


@dataclass
class PublishResult:
    ok: bool
    error: Optional[str] = None
    elapsed_ms: Optional[float] = None
    queue_full: bool = False  # ZMQ queue saturation indicator


class TradingClient:
    """Thin ZMQ PUSH publisher with latency benchmarking."""

    def __init__(self, connect_addr: str, enable_benchmarking: bool = False) -> None:
        self._addr = connect_addr
        self._ctx = zmq.Context.instance()
        self._sock = self._ctx.socket(zmq.PUSH)

        # Optimize for low latency
        self._sock.setsockopt(zmq.LINGER, 0)
        self._sock.setsockopt(zmq.SNDTIMEO, 1)  # 1ms timeout - fail fast
        self._sock.setsockopt(zmq.SNDHWM, 100)  # Small send queue
        self._sock.connect(connect_addr)

        # Benchmarking state
        self._benchmarking = enable_benchmarking
        self._publish_times = []
        self._max_samples = 10000

    @property
    def addr(self) -> str:
        return self._addr

    def publish_json(self, payload: dict) -> PublishResult:
        """Publish with precise latency measurement."""
        if self._benchmarking:
            return self._publish_with_benchmark(payload)
        else:
            return self._publish_fast(payload)

    def _publish_fast(self, payload: dict) -> PublishResult:
        """Fast path - minimal overhead."""
        try:
            encoded = json.dumps(payload, separators=(",", ":"))
            self._sock.send_string(encoded, flags=zmq.NOBLOCK)
            return PublishResult(ok=True)
        except zmq.Again:
            return PublishResult(ok=False, error="queue_full", queue_full=True)
        except Exception as e:
            return PublishResult(ok=False, error=str(e))

    def _publish_with_benchmark(self, payload: dict) -> PublishResult:
        """Benchmarking path - measures actual send cost."""
        encoded = json.dumps(payload, separators=(",", ":"))

        t0 = time.perf_counter_ns()  # Nanosecond precision
        try:
            self._sock.send_string(encoded, flags=zmq.NOBLOCK)
            elapsed_ns = time.perf_counter_ns() - t0
            elapsed_ms = elapsed_ns / 1_000_000.0

            # Store sample (ring buffer)
            if len(self._publish_times) >= self._max_samples:
                self._publish_times.pop(0)
            self._publish_times.append(elapsed_ns)

            return PublishResult(ok=True, elapsed_ms=elapsed_ms)

        except zmq.Again:
            elapsed_ns = time.perf_counter_ns() - t0
            return PublishResult(
                ok=False,
                error="queue_full",
                queue_full=True,
                elapsed_ms=elapsed_ns / 1_000_000.0
            )
        except Exception as e:
            return PublishResult(ok=False, error=str(e))

    def get_latency_stats(self) -> dict:
        """Get publishing latency statistics in microseconds."""
        if not self._publish_times:
            return {}

        times_us = [t / 1000.0 for t in self._publish_times]  # Convert to microseconds
        times_us.sort()

        n = len(times_us)
        return {
            "count": n,
            "min_us": times_us[0],
            "max_us": times_us[-1],
            "mean_us": sum(times_us) / n,
            "p50_us": times_us[n // 2],
            "p95_us": times_us[int(n * 0.95)],
            "p99_us": times_us[int(n * 0.99)],
        }
