from __future__ import annotations

from typing import Literal, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator


class TradeMsg(BaseModel):
    type: Literal["trade"] = "trade"
    side: Literal["buy", "sell"]
    qty: float = Field(ge=0)
    ts: float  # unix epoch seconds (float)

    @field_validator("qty")
    @classmethod
    def _qty_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("qty must be >= 0")
        return v


class BenchmarkMsg(BaseModel):
    """Message containing benchmark results for metrics collection."""
    type: Literal["benchmark"] = "benchmark"
    test_type: Literal["burst", "sustained", "profile"]
    test_name: str
    timestamp: float  # unix epoch seconds

    # Test configuration
    config: Dict[str, Any]  # e.g., {"num_trades": 1000, "rate": 100}

    # Results
    total_trades: int
    duration_seconds: float
    trades_per_second: float
    queue_full_count: int = 0
    error_count: int = 0

    # Latency statistics (in microseconds)
    latency_stats: Dict[str, float] = Field(default_factory=dict)
    # Expected keys: count, min_us, max_us, mean_us, p50_us, p95_us, p99_us


class BenchmarkStatusMsg(BaseModel):
    """Message for benchmark monitoring status updates."""
    type: Literal["benchmark_status"] = "benchmark_status"
    status: Literal["started", "running", "completed", "failed"]
    test_name: str
    timestamp: float
    message: str = ""


# Union type for all message types
TelemetryMsg = Union[TradeMsg, BenchmarkMsg, BenchmarkStatusMsg]
