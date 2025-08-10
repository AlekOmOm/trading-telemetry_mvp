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


class TradePublisher:
    """Thin ZMQ PUSH publisher with a single reusable socket."""

    def __init__(self, connect_addr: str) -> None:
        self._addr = connect_addr
        self._ctx = zmq.Context.instance()
        self._sock = self._ctx.socket(zmq.PUSH)
        # Fast fail on send when no peer is available; app handles feedback.
        self._sock.setsockopt(zmq.LINGER, 0)
        self._sock.setsockopt(zmq.SNDTIMEO, 200)  # 200ms send timeout
        self._sock.connect(connect_addr)

    @property
    def addr(self) -> str:
        return self._addr

    def publish_json(self, payload: dict) -> PublishResult:
        encoded = json.dumps(payload, separators=(",", ":"))
        t0 = time.perf_counter()
        try:
            self._sock.send_string(encoded, flags=0)
            return PublishResult(ok=True, elapsed_ms=(time.perf_counter() - t0) * 1000.0)
        except Exception as e:  # zmq.Again on timeout, etc.
            return PublishResult(ok=False, error=str(e))

